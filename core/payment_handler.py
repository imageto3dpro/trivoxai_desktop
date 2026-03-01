"""
Payment Handler for Credit Purchases

This module handles payment processing for credit purchases using the secure
Razorpay integration. It provides:
- Order creation for credit packs
- Payment verification
- Automatic credit addition on successful payment
- Webhook handling
"""

import webbrowser
from typing import Dict, Optional, Any, Callable
from datetime import datetime

from PySide6.QtCore import QTimer, QObject, Signal

from core.razorpay_client import (
    get_razorpay_client,
    RazorpayClient,
    RazorpayError,
    is_razorpay_active,
    validate_razorpay_config,
)
from core.credit_manager import CREDIT_PACKS, get_user_balance, add_credits
from core.payment_config_sync import get_credit_packs
from core.logger import get_logger
from core.supabase_client import get_supabase

logger = get_logger(__name__)


class PaymentStatus:
    """Payment status constants."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentHandler(QObject):
    """
    Handler for payment operations with Razorpay.

    This class manages the entire payment flow:
    1. Create order/payment link
    2. Open payment page
    3. Poll for payment status
    4. Verify payment and add credits
    """

    # Signals
    payment_started = Signal(str)  # order_id
    payment_completed = Signal(str, int)  # order_id, credits_added
    payment_failed = Signal(str, str)  # order_id, error_message
    payment_status_changed = Signal(str, str)  # order_id, status

    def __init__(self, parent=None):
        """Initialize payment handler."""
        super().__init__(parent)
        self.razorpay_client: Optional[RazorpayClient] = None
        self._active_orders: Dict[str, Dict[str, Any]] = {}
        self._poll_timer: Optional[QTimer] = None
        self._init_razorpay()

    def _init_razorpay(self) -> bool:
        """Initialize Razorpay client."""
        if not is_razorpay_active():
            logger.info("Razorpay is not the active payment provider")
            return False

        is_valid, message = validate_razorpay_config()
        if not is_valid:
            logger.error(f"Razorpay configuration invalid: {message}")
            return False

        try:
            self.razorpay_client = get_razorpay_client()
            logger.info("PaymentHandler: Razorpay client initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Razorpay: {e}")
            return False

    def is_available(self) -> bool:
        """Check if payment handler is available."""
        return self.razorpay_client is not None and self.razorpay_client.is_configured()

    def get_payment_status(self) -> Dict[str, Any]:
        """Get current payment handler status."""
        is_valid, message = validate_razorpay_config()

        if self.razorpay_client:
            keys_info = self.razorpay_client.get_active_keys_info()
        else:
            keys_info = {}

        return {
            "is_available": self.is_available(),
            "is_configured": is_valid,
            "message": message,
            "keys_info": keys_info,
            "active_orders": len(self._active_orders),
        }

    def create_order_for_pack(
        self,
        pack_id: str,
        user_id: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a Razorpay order for a credit pack.

        Args:
            pack_id: Credit pack ID (e.g., "credits_small")
            user_id: User ID
            email: User email (optional)
            phone: User phone (optional)

        Returns:
            Order details or None if failed
        """
        if not self.is_available():
            logger.error("Payment handler not available")
            return None

        pack_info = get_credit_packs().get(pack_id) or CREDIT_PACKS.get(pack_id)
        if not pack_info:
            logger.error(f"Invalid pack ID: {pack_id}")
            return None

        # Convert price to paise (smallest currency unit)
        amount_paise = int(pack_info["price"] * 100)

        # Create receipt ID
        receipt = f"credits_{pack_id}_{user_id}_{int(datetime.now().timestamp())}"

        # Customer info
        customer = {}
        if email:
            customer["email"] = email
        if phone:
            customer["contact"] = phone

        # Notes for tracking
        notes = {
            "pack_id": pack_id,
            "user_id": user_id,
            "credits": pack_info["credits"],
            "pack_name": pack_info["name"],
        }

        try:
            order = self.razorpay_client.create_order(
                amount=amount_paise,
                currency="INR",
                receipt=receipt,
                notes=notes,
                payment_capture=1,  # Auto-capture
            )

            # Store order info
            self._active_orders[order["id"]] = {
                "pack_id": pack_id,
                "user_id": user_id,
                "credits": pack_info["credits"],
                "amount": pack_info["price"],
                "created_at": datetime.now(),
                "status": PaymentStatus.PENDING,
            }

            logger.info(f"Order created: {order['id']} for pack {pack_id}")
            self.payment_started.emit(order["id"])

            return order

        except RazorpayError as e:
            logger.error(f"Failed to create order: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating order: {e}")
            return None

    def open_payment_page(self, order_id: str) -> bool:
        """
        Open Razorpay checkout page for an order.

        Args:
            order_id: Razorpay order ID

        Returns:
            True if page opened successfully
        """
        order_info = self._active_orders.get(order_id)
        if not order_info:
            logger.error(f"Order not found: {order_id}")
            return False

        # Build checkout URL
        # For Razorpay, we can use the standard checkout or a payment link
        # Here we use a simple payment link approach
        checkout_url = (
            f"https://checkout.razorpay.com/v1/checkout.js?order_id={order_id}"
        )

        try:
            webbrowser.open(checkout_url)
            logger.info(f"Opened payment page for order: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to open payment page: {e}")
            return False

    def create_and_open_payment(
        self,
        pack_id: str,
        user_id: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create order and open payment page in one step.

        Args:
            pack_id: Credit pack ID
            user_id: User ID
            email: User email (optional)
            phone: User phone (optional)

        Returns:
            Order ID if successful, None otherwise
        """
        # Create order
        order = self.create_order_for_pack(pack_id, user_id, email, phone)
        if not order:
            return None

        order_id = order["id"]

        # Open payment page using Payment Link approach (simpler)
        pack_info = get_credit_packs().get(pack_id) or CREDIT_PACKS.get(pack_id)
        if pack_info and pack_info.get("razorpay_id"):
            # Use existing Payment Link
            razorpay_link_id = pack_info["razorpay_id"]
            payment_url = f"https://rzp.io/l/{razorpay_link_id}"
            if user_id:
                payment_url += f"?notes[user_id]={user_id}"

            try:
                webbrowser.open(payment_url)
                logger.info(f"Opened Payment Link: {payment_url}")
                return order_id
            except Exception as e:
                logger.error(f"Failed to open payment link: {e}")

        # Fallback: try to open standard checkout
        if self.open_payment_page(order_id):
            return order_id

        return None

    def verify_payment(self, payment_id: str, order_id: str, signature: str) -> bool:
        """
        Verify a payment signature.

        Args:
            payment_id: Razorpay payment ID
            order_id: Razorpay order ID
            signature: Payment signature

        Returns:
            True if payment is valid
        """
        if not self.razorpay_client:
            logger.error("Razorpay client not initialized")
            return False

        try:
            is_valid = self.razorpay_client.verify_payment_signature(
                order_id, payment_id, signature
            )

            if is_valid:
                logger.info(f"Payment verified: {payment_id}")
                return True
            else:
                logger.warning(f"Payment verification failed: {payment_id}")
                return False

        except Exception as e:
            logger.error(f"Payment verification error: {e}")
            return False

    def process_successful_payment(self, order_id: str, payment_id: str) -> bool:
        """
        Process a successful payment and add credits.

        Args:
            order_id: Razorpay order ID
            payment_id: Razorpay payment ID

        Returns:
            True if credits were added successfully
        """
        order_info = self._active_orders.get(order_id)
        if not order_info:
            logger.error(f"Order not found in active orders: {order_id}")
            return False

        user_id = order_info["user_id"]
        credits = order_info["credits"]
        pack_id = order_info["pack_id"]

        try:
            # Add credits to user's account
            success = add_credits(
                user_id=user_id,
                amount=credits,
                source="razorpay_purchase",
                description=f"Purchased {pack_id} via Razorpay (Payment: {payment_id})",
                reference_id=payment_id,
            )

            if success:
                order_info["status"] = PaymentStatus.SUCCESS
                logger.info(f"Credits added: {credits} to user {user_id}")
                self.payment_completed.emit(order_id, credits)
                return True
            else:
                order_info["status"] = PaymentStatus.FAILED
                logger.error(f"Failed to add credits for order: {order_id}")
                self.payment_failed.emit(order_id, "Failed to add credits")
                return False

        except Exception as e:
            order_info["status"] = PaymentStatus.FAILED
            logger.error(f"Error processing payment: {e}")
            self.payment_failed.emit(order_id, str(e))
            return False

    def start_payment_polling(
        self,
        user_id: str,
        expected_credits: int,
        timeout_minutes: int = 5,
        callback: Optional[Callable] = None,
    ):
        """
        Start polling for payment completion.

        Args:
            user_id: User ID to check
            expected_credits: Expected credit amount
            timeout_minutes: Polling timeout in minutes
            callback: Optional callback function(success, credits_added)
        """
        if self._poll_timer and self._poll_timer.isActive():
            self._poll_timer.stop()

        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(
            lambda: self._check_payment_status(user_id, expected_credits, callback)
        )
        self._poll_timer.start(5000)  # Check every 5 seconds

        self._poll_count = 0
        self._poll_max = (timeout_minutes * 60) // 5  # Convert to poll intervals
        self._poll_initial_balance = 0

        # Get initial balance
        try:
            balance_info = get_user_balance(user_id)
            self._poll_initial_balance = balance_info.get("credits_balance", 0)
            logger.info(
                f"Started polling for user {user_id}, initial balance: {self._poll_initial_balance}"
            )
        except Exception as e:
            logger.error(f"Failed to get initial balance: {e}")

    def _check_payment_status(
        self, user_id: str, expected_credits: int, callback: Optional[Callable]
    ):
        """Check if payment has been processed and credits added."""
        self._poll_count += 1

        try:
            balance_info = get_user_balance(user_id)
            new_balance = balance_info.get("credits_balance", 0)

            if new_balance > self._poll_initial_balance:
                # Credits added!
                self._poll_timer.stop()
                added = new_balance - self._poll_initial_balance

                logger.info(f"Credits added: {added}, new balance: {new_balance}")

                if callback:
                    callback(True, added)
                return

        except Exception as e:
            logger.debug(f"Balance check error (may be temporary): {e}")

        # Check timeout
        if self._poll_count >= self._poll_max:
            self._poll_timer.stop()
            logger.warning(f"Payment polling timed out for user {user_id}")
            if callback:
                callback(False, 0)

    def stop_polling(self):
        """Stop payment polling."""
        if self._poll_timer and self._poll_timer.isActive():
            self._poll_timer.stop()
            logger.info("Payment polling stopped")

    def verify_webhook(self, webhook_body: str, webhook_signature: str) -> bool:
        """
        Verify webhook signature from Razorpay.

        Args:
            webhook_body: Raw webhook body
            webhook_signature: X-Razorpay-Signature header

        Returns:
            True if signature is valid
        """
        if not self.razorpay_client:
            return False

        return self.razorpay_client.verify_webhook_signature(
            webhook_body, webhook_signature
        )

    def handle_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """
        Handle Razorpay webhook event.

        Args:
            webhook_data: Webhook payload

        Returns:
            True if handled successfully
        """
        event = webhook_data.get("event")
        payload = webhook_data.get("payload", {})

        logger.info(f"Processing webhook event: {event}")

        if event == "payment.captured":
            payment = payload.get("payment", {}).get("entity", {})
            payment_id = payment.get("id")
            order_id = payment.get("order_id")
            notes = payment.get("notes", {})

            if order_id and notes.get("pack_id"):
                # This is a credit pack purchase
                success = self.process_successful_payment(order_id, payment_id)
                return success

        elif event == "order.paid":
            order = payload.get("order", {}).get("entity", {})
            order_id = order.get("id")
            notes = order.get("notes", {})

            if notes.get("pack_id"):
                # Order paid, process credits
                payments = order.get("payments", [])
                if payments:
                    payment_id = payments[0].get("id")
                    success = self.process_successful_payment(order_id, payment_id)
                    return success

        return True


# Global instance
_payment_handler: Optional[PaymentHandler] = None


def get_payment_handler() -> PaymentHandler:
    """Get or create payment handler instance."""
    global _payment_handler
    if _payment_handler is None:
        _payment_handler = PaymentHandler()
    return _payment_handler
