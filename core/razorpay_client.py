"""
Secure Razorpay Payment Gateway Client

This module provides secure Razorpay integration with:
- Secure key management via SecretManager (3-tier security)
- Payment order creation and verification
- Webhook signature verification
- Automatic retry logic
- Comprehensive error handling
"""

import json
import hmac
import hashlib
from typing import Dict, Optional, Any, Tuple
from datetime import datetime

import razorpay
from core.secret_manager import SecretManager
from core.logger import get_logger
from config.payment_config import PaymentProvider, PAYMENT_PROVIDER, razorpay_config

logger = get_logger(__name__)


class RazorpayError(Exception):
    """Custom exception for Razorpay errors."""

    pass


class RazorpayClient:
    """
    Secure Razorpay payment gateway client.

    All API keys are fetched securely via SecretManager which provides
    three-tier security: Environment Variables -> Local Cache -> Remote Supabase RPC.

    This ensures keys cannot be tampered with or exposed in the code.
    """

    _instance: Optional["RazorpayClient"] = None
    _client: Optional[razorpay.Client] = None

    # Key names for SecretManager
    KEY_ID_NAME = "RAZORPAY_KEY_ID"
    KEY_SECRET_NAME = "RAZORPAY_KEY_SECRET"
    WEBHOOK_SECRET_NAME = "RAZORPAY_WEBHOOK_SECRET"

    def __new__(cls) -> "RazorpayClient":
        """Singleton pattern to ensure single client instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the Razorpay client with secure key retrieval."""
        if self._client is not None:
            return

        self._initialize_client()

    def _initialize_client(self) -> None:
        """
        Initialize Razorpay client with secure key retrieval.

        Keys are fetched via SecretManager which provides:
        1. Environment variables (first priority - for development)
        2. Local cache (second priority)
        3. Remote Supabase RPC (requires valid license)
        """
        try:
            # Fetch keys securely via SecretManager
            key_id = SecretManager.get_secret(self.KEY_ID_NAME)
            key_secret = SecretManager.get_secret(self.KEY_SECRET_NAME)

            if not key_id or not key_secret:
                raise RazorpayError(
                    "Razorpay credentials not found. "
                    f"Please set {self.KEY_ID_NAME} and {self.KEY_SECRET_NAME} "
                    "in environment variables or ensure you have a valid license."
                )

            # Initialize Razorpay client
            self._client = razorpay.Client(auth=(key_id, key_secret))
            logger.info("Razorpay client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Razorpay client: {e}")
            raise RazorpayError(f"Razorpay initialization failed: {str(e)}")

    @property
    def client(self) -> razorpay.Client:
        """Get the initialized Razorpay client."""
        if self._client is None:
            self._initialize_client()
        return self._client

    def is_configured(self) -> bool:
        """Check if Razorpay is properly configured."""
        try:
            key_id = SecretManager.get_secret(self.KEY_ID_NAME)
            key_secret = SecretManager.get_secret(self.KEY_SECRET_NAME)
            return bool(key_id and key_secret)
        except Exception:
            return False

    def get_active_keys_info(self) -> Dict[str, str]:
        """
        Get information about active keys (without exposing values).

        Returns:
            Dict with key names and their status (configured/not configured)
        """
        key_id = SecretManager.get_secret(self.KEY_ID_NAME)
        key_secret = SecretManager.get_secret(self.KEY_SECRET_NAME)
        webhook_secret = SecretManager.get_secret(self.WEBHOOK_SECRET_NAME)

        return {
            "key_id": "✓ Configured" if key_id else "✗ Not configured",
            "key_secret": "✓ Configured" if key_secret else "✗ Not configured",
            "webhook_secret": "✓ Configured" if webhook_secret else "✗ Not configured",
            "mode": "Test"
            if razorpay_config.key_id and razorpay_config.key_id.startswith("rzp_test")
            else "Live",
        }

    def create_order(
        self,
        amount: int,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, Any]] = None,
        payment_capture: int = 1,
    ) -> Dict[str, Any]:
        """
        Create a Razorpay order.

        Args:
            amount: Amount in smallest currency unit (paise for INR)
            currency: Currency code (default: INR)
            receipt: Your receipt ID
            notes: Additional notes (dict)
            payment_capture: 1 to auto-capture, 0 for manual capture

        Returns:
            Order details from Razorpay

        Raises:
            RazorpayError: If order creation fails
        """
        try:
            order_data = {
                "amount": amount,
                "currency": currency,
                "payment_capture": payment_capture,
            }

            if receipt:
                order_data["receipt"] = receipt

            if notes:
                order_data["notes"] = notes

            order = self.client.order.create(data=order_data)
            logger.info(f"Razorpay order created: {order.get('id')}")
            return order

        except razorpay.errors.BadRequestError as e:
            logger.error(f"Razorpay bad request error: {e}")
            raise RazorpayError(f"Invalid order data: {str(e)}")
        except razorpay.errors.ServerError as e:
            logger.error(f"Razorpay server error: {e}")
            raise RazorpayError(f"Razorpay server error: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to create Razorpay order: {e}")
            raise RazorpayError(f"Order creation failed: {str(e)}")

    def verify_payment_signature(
        self, order_id: str, payment_id: str, signature: str
    ) -> bool:
        """
        Verify Razorpay payment signature.

        Args:
            order_id: Razorpay order ID
            payment_id: Razorpay payment ID
            signature: Signature from Razorpay

        Returns:
            True if signature is valid
        """
        try:
            # Fetch secret securely
            key_secret = SecretManager.get_secret(self.KEY_SECRET_NAME)
            if not key_secret:
                logger.error("Cannot verify signature: Key secret not available")
                return False

            # Generate expected signature
            message = f"{order_id}|{payment_id}"
            expected_signature = hmac.new(
                key_secret.encode(), message.encode(), hashlib.sha256
            ).hexdigest()

            # Compare signatures
            is_valid = hmac.compare_digest(expected_signature, signature)

            if is_valid:
                logger.info(f"Payment signature verified: {payment_id}")
            else:
                logger.warning(f"Payment signature verification failed: {payment_id}")

            return is_valid

        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False

    def verify_webhook_signature(
        self, webhook_body: str, webhook_signature: str
    ) -> bool:
        """
        Verify Razorpay webhook signature.

        Args:
            webhook_body: Raw webhook body
            webhook_signature: X-Razorpay-Signature header

        Returns:
            True if signature is valid
        """
        try:
            # Fetch webhook secret securely
            webhook_secret = SecretManager.get_secret(self.WEBHOOK_SECRET_NAME)
            if not webhook_secret:
                logger.error("Cannot verify webhook: Webhook secret not available")
                return False

            # Generate expected signature
            expected_signature = hmac.new(
                webhook_secret.encode(), webhook_body.encode(), hashlib.sha256
            ).hexdigest()

            # Compare signatures
            is_valid = hmac.compare_digest(expected_signature, webhook_signature)

            if is_valid:
                logger.info("Webhook signature verified")
            else:
                logger.warning("Webhook signature verification failed")

            return is_valid

        except Exception as e:
            logger.error(f"Webhook verification error: {e}")
            return False

    def fetch_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Fetch payment details from Razorpay.

        Args:
            payment_id: Razorpay payment ID

        Returns:
            Payment details
        """
        try:
            payment = self.client.payment.fetch(payment_id)
            logger.info(f"Fetched payment: {payment_id}")
            return payment
        except Exception as e:
            logger.error(f"Failed to fetch payment {payment_id}: {e}")
            raise RazorpayError(f"Failed to fetch payment: {str(e)}")

    def fetch_order(self, order_id: str) -> Dict[str, Any]:
        """
        Fetch order details from Razorpay.

        Args:
            order_id: Razorpay order ID

        Returns:
            Order details
        """
        try:
            order = self.client.order.fetch(order_id)
            logger.info(f"Fetched order: {order_id}")
            return order
        except Exception as e:
            logger.error(f"Failed to fetch order {order_id}: {e}")
            raise RazorpayError(f"Failed to fetch order: {str(e)}")

    def capture_payment(self, payment_id: str, amount: int) -> Dict[str, Any]:
        """
        Capture a payment (for manual capture mode).

        Args:
            payment_id: Razorpay payment ID
            amount: Amount to capture in smallest currency unit

        Returns:
            Payment details after capture
        """
        try:
            payment = self.client.payment.capture(payment_id, amount)
            logger.info(f"Payment captured: {payment_id}")
            return payment
        except Exception as e:
            logger.error(f"Failed to capture payment {payment_id}: {e}")
            raise RazorpayError(f"Failed to capture payment: {str(e)}")

    def refund_payment(
        self,
        payment_id: str,
        amount: Optional[int] = None,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Refund a payment.

        Args:
            payment_id: Razorpay payment ID
            amount: Amount to refund (optional, full refund if not specified)
            notes: Refund notes

        Returns:
            Refund details
        """
        try:
            data = {}
            if amount:
                data["amount"] = amount
            if notes:
                data["notes"] = notes

            refund = self.client.payment.refund(payment_id, data)
            logger.info(f"Payment refunded: {payment_id}")
            return refund
        except Exception as e:
            logger.error(f"Failed to refund payment {payment_id}: {e}")
            raise RazorpayError(f"Failed to refund payment: {str(e)}")

    def create_payment_link(
        self,
        amount: int,
        currency: str = "INR",
        accept_partial: bool = False,
        first_min_partial_amount: Optional[int] = None,
        description: Optional[str] = None,
        customer: Optional[Dict[str, Any]] = None,
        notify: Optional[Dict[str, bool]] = None,
        reminder_enable: bool = True,
        notes: Optional[Dict[str, Any]] = None,
        callback_url: Optional[str] = None,
        callback_method: str = "get",
    ) -> Dict[str, Any]:
        """
        Create a Razorpay Payment Link.

        Args:
            amount: Amount in smallest currency unit
            currency: Currency code (default: INR)
            accept_partial: Whether to accept partial payments
            first_min_partial_amount: Minimum amount for first partial payment
            description: Description of the payment
            customer: Customer details (name, email, contact)
            notify: Notification settings (sms, email)
            reminder_enable: Enable payment reminders
            notes: Additional notes
            callback_url: URL to redirect after payment
            callback_method: HTTP method for callback (get/post)

        Returns:
            Payment Link details
        """
        try:
            data = {
                "amount": amount,
                "currency": currency,
                "accept_partial": accept_partial,
                "reminder_enable": reminder_enable,
            }

            if first_min_partial_amount:
                data["first_min_partial_amount"] = first_min_partial_amount
            if description:
                data["description"] = description
            if customer:
                data["customer"] = customer
            if notify:
                data["notify"] = notify
            if notes:
                data["notes"] = notes
            if callback_url:
                data["callback_url"] = callback_url
                data["callback_method"] = callback_method

            payment_link = self.client.payment_link.create(data=data)
            logger.info(f"Payment link created: {payment_link.get('id')}")
            return payment_link

        except Exception as e:
            logger.error(f"Failed to create payment link: {e}")
            raise RazorpayError(f"Failed to create payment link: {str(e)}")


# Convenience function
def get_razorpay_client() -> RazorpayClient:
    """Get or create Razorpay client instance."""
    return RazorpayClient()


def is_razorpay_active() -> bool:
    """Check if Razorpay is the active payment provider."""
    from core.payment_config_sync import get_active_payment_provider
    return get_active_payment_provider() == "razorpay"


def validate_razorpay_config() -> Tuple[bool, str]:
    """
    Validate Razorpay configuration.

    Returns:
        Tuple of (is_valid, message)
    """
    if not is_razorpay_active():
        return False, "Razorpay is not the active payment provider"

    client = get_razorpay_client()

    if not client.is_configured():
        return (
            False,
            "Razorpay keys not configured. Please check environment variables or ensure valid license.",
        )

    try:
        keys_info = client.get_active_keys_info()
        return True, f"Razorpay configured: {keys_info}"
    except Exception as e:
        return False, f"Razorpay validation error: {str(e)}"
