"""
Gumroad Payment Provider Implementation

Best for: Quick start without business registration
Requirements: No GST/PAN needed
Fees: 10% per transaction

All sales are persisted to Supabase `gumroad_sales` table.
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import httpx

from core.providers.base import (
    BasePaymentProvider,
    Subscription,
    PaymentResult,
    License,
    SubscriptionStatus,
)
from config.payment_config import gumroad_config, pricing_config, payment_settings


def _get_supabase():
    """Lazy import to avoid circular imports."""
    try:
        from core.supabase_client import get_supabase_client
        return get_supabase_client()
    except Exception:
        return None


class GumroadProvider(BasePaymentProvider):
    """
    Gumroad payment provider implementation.

    Gumroad acts as the merchant of record, handling all tax compliance.
    Perfect for starting without business registration.

    All sales data is stored in Supabase `gumroad_sales` table.
    """

    BASE_URL = "https://api.gumroad.com/v2"

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config or {})
        self.access_token = (
            os.getenv("GUMROAD_ACCESS_TOKEN") or gumroad_config.access_token
        )
        self.client = httpx.AsyncClient(base_url=self.BASE_URL)

    # ═════════════════════════════════════════════════════════════════
    # Supabase Helpers
    # ═════════════════════════════════════════════════════════════════

    def _save_sale_to_db(self, sale_data: Dict) -> bool:
        """Insert or update a sale record in Supabase."""
        sb = _get_supabase()
        if not sb:
            return False
        try:
            sb.table("gumroad_sales").upsert(
                sale_data, on_conflict="sale_id"
            ).execute()
            return True
        except Exception as e:
            print(f"[GumroadProvider] Error saving sale to DB: {e}")
            return False

    def _update_sale_status(self, sale_id: str, status: str, extra: Dict = None) -> bool:
        """Update the status of an existing sale in Supabase."""
        sb = _get_supabase()
        if not sb:
            return False
        try:
            update_data = {"status": status, "updated_at": datetime.utcnow().isoformat()}
            if extra:
                update_data.update(extra)
            sb.table("gumroad_sales").update(update_data).eq("sale_id", sale_id).execute()
            return True
        except Exception as e:
            print(f"[GumroadProvider] Error updating sale status: {e}")
            return False

    def _save_license_to_db(self, license_key: str, plan_id: str, email: str = "") -> bool:
        """Upsert a license into the `licenses` table."""
        sb = _get_supabase()
        if not sb:
            return False
        try:
            sb.table("licenses").upsert({
                "license_key": license_key,
                "status": "active",
                "plan": plan_id,
                "email": email,
                "activated_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            }, on_conflict="license_key").execute()
            return True
        except Exception as e:
            print(f"[GumroadProvider] Error saving license: {e}")
            return False

    def _deactivate_license_in_db(self, sale_id: str) -> Optional[str]:
        """Find license key by sale_id in gumroad_sales, then deactivate it."""
        sb = _get_supabase()
        if not sb:
            return None
        try:
            result = sb.table("gumroad_sales").select("license_key").eq("sale_id", sale_id).limit(1).execute()
            if result.data and result.data[0].get("license_key"):
                lic_key = result.data[0]["license_key"]
                sb.table("licenses").update({"status": "inactive"}).eq("license_key", lic_key).execute()
                return lic_key
        except Exception as e:
            print(f"[GumroadProvider] Error deactivating license: {e}")
        return None

    # ═════════════════════════════════════════════════════════════════
    # API Methods
    # ═════════════════════════════════════════════════════════════════

    async def _make_request(
        self, method: str, endpoint: str, data: Dict = None
    ) -> Dict:
        """Make authenticated request to Gumroad API."""
        headers = {"Authorization": f"Bearer {self.access_token}"}

        if method == "GET":
            response = await self.client.get(endpoint, headers=headers, params=data)
        else:
            response = await self.client.post(endpoint, headers=headers, data=data)

        response.raise_for_status()
        return response.json()

    async def create_subscription(
        self,
        user_id: str,
        plan_id: str,
        customer_email: str,
        customer_name: Optional[str] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> PaymentResult:
        """
        Create a Gumroad subscription.

        Note: Gumroad uses product-based subscriptions.
        Customer purchases a product that grants access.
        """
        try:
            # Map plan_id to Gumroad product
            product_mapping = {
                "starter": gumroad_config.product_ids.get("starter_monthly"),
                "pro": gumroad_config.product_ids.get("pro_monthly"),
                "enterprise": gumroad_config.product_ids.get("enterprise_monthly"),
            }

            product_id = product_mapping.get(plan_id)
            if not product_id:
                return PaymentResult(
                    success=False, message=f"Product not configured for plan: {plan_id}"
                )

            # Generate unique license key
            license_key = self.generate_license_key(user_id, plan_id)

            # Create Gumroad offer code for this customer (optional)
            # Or redirect to product page with custom params
            product_url = f"https://gumroad.com/l/{product_id}"

            # Add custom parameters for tracking
            checkout_url = f"{product_url}?email={customer_email}&ref={user_id}"

            return PaymentResult(
                success=True,
                message="Redirect to Gumroad checkout",
                payment_url=checkout_url,
                metadata={
                    "license_key": license_key,
                    "product_id": product_id,
                    "plan_id": plan_id,
                },
            )

        except Exception as e:
            return PaymentResult(
                success=False, message=f"Failed to create subscription: {str(e)}"
            )

    async def cancel_subscription(self, subscription_id: str) -> PaymentResult:
        """
        Cancel a Gumroad subscription.

        In Gumroad, users cancel from their library or via customer portal.
        We track the cancellation via webhook.
        """
        return PaymentResult(
            success=True,
            message="User must cancel from Gumroad library. Webhook will update status.",
            metadata={"subscription_id": subscription_id},
        )

    async def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription details from Gumroad."""
        try:
            result = await self._make_request("GET", f"/sales/{subscription_id}")

            sale = result.get("sale", {})
            if not sale:
                return None

            is_subscription = sale.get("is_subscription", False)
            is_cancelled = sale.get("subscription_cancelled_at") is not None

            if is_cancelled:
                status = SubscriptionStatus.CANCELLED
            elif is_subscription:
                status = SubscriptionStatus.ACTIVE
            else:
                status = SubscriptionStatus.ACTIVE

            created_at = datetime.fromisoformat(
                sale.get("created_at", "").replace("Z", "+00:00")
            )

            return Subscription(
                id=subscription_id,
                user_id=sale.get("custom_fields", {}).get("user_id", ""),
                plan_id=self._map_product_to_plan(sale.get("product_id", "")),
                status=status,
                current_period_start=created_at,
                current_period_end=created_at + timedelta(days=30),
                metadata=sale,
            )

        except Exception:
            return None

    async def purchase_credits(
        self,
        user_id: str,
        credit_pack_id: str,
        customer_email: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> PaymentResult:
        """Purchase a credit pack via Gumroad."""
        product_mapping = {
            "small": gumroad_config.product_ids.get("credits_small"),
            "medium": gumroad_config.product_ids.get("credits_medium"),
            "large": gumroad_config.product_ids.get("credits_large"),
        }

        product_id = product_mapping.get(credit_pack_id)
        if not product_id:
            return PaymentResult(
                success=False,
                message=f"Product not configured for credit pack: {credit_pack_id}",
            )

        credits = pricing_config.credit_packs.get(credit_pack_id, {}).get("credits", 0)

        product_url = f"https://gumroad.com/l/{product_id}"
        checkout_url = f"{product_url}?email={customer_email}&ref={user_id}"

        return PaymentResult(
            success=True,
            message="Redirect to Gumroad checkout for credits",
            payment_url=checkout_url,
            metadata={
                "credits": credits,
                "credit_pack_id": credit_pack_id,
            },
        )

    async def verify_webhook(self, payload: str, signature: str) -> bool:
        """
        Verify Gumroad webhook signature.

        Gumroad uses basic verification via signature in headers.
        """
        expected_secret = payment_settings.webhook_secret
        if expected_secret:
            return signature == expected_secret
        return True

    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Gumroad webhook events.

        Key events:
        - sale: New purchase
        - refund: Refund issued
        - subscription_cancelled: Subscription cancelled
        - subscription_restarted: Subscription restarted
        """
        event_type = payload.get("action")

        if event_type == "sale":
            return await self._handle_sale(payload)
        elif event_type == "refund":
            return await self._handle_refund(payload)
        elif event_type == "subscription_cancelled":
            return await self._handle_subscription_cancelled(payload)
        elif event_type == "subscription_restarted":
            return await self._handle_subscription_restarted(payload)

        return {"status": "ignored", "event": event_type}

    # ═════════════════════════════════════════════════════════════════
    # Webhook Handlers — Persist to Supabase
    # ═════════════════════════════════════════════════════════════════

    async def _handle_sale(self, payload: Dict) -> Dict[str, Any]:
        """Handle new sale event — persist to Supabase."""
        sale = payload.get("sale", payload)  # Gumroad may nest or flatten
        sale_id = sale.get("id") or sale.get("sale_id", "")
        product_id = sale.get("product_id", "")
        product_name = sale.get("product_name", "")
        email = sale.get("email", "")
        buyer_name = sale.get("full_name", "")
        price = sale.get("price", 0)
        currency = sale.get("currency", "usd")
        quantity = sale.get("quantity", 1)
        is_subscription = sale.get("is_subscription", False)
        subscription_id = sale.get("subscription_id", "")
        custom_fields = sale.get("custom_fields", {})
        user_id = custom_fields.get("user_id", email)
        ip = sale.get("ip_address", "")

        # Map product to plan
        plan_id = self._map_product_to_plan(product_id)

        # Generate license
        license_key = self.generate_license_key(user_id, plan_id)

        # Determine credits based on product
        credits = self._get_credits_for_product(product_id)

        # 1. Save sale record to Supabase
        sale_record = {
            "sale_id": sale_id,
            "product_id": product_id,
            "product_name": product_name,
            "plan_id": plan_id,
            "license_key": license_key,
            "buyer_email": email,
            "buyer_name": buyer_name,
            "price": float(price) / 100 if isinstance(price, int) and price > 1000 else float(price),
            "currency": currency.upper(),
            "quantity": int(quantity),
            "is_subscription": is_subscription,
            "subscription_id": subscription_id or None,
            "status": "active",
            "credits_granted": credits,
            "ip_address": ip or None,
            "gumroad_payload": payload,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        self._save_sale_to_db(sale_record)

        # 2. Upsert license into licenses table
        self._save_license_to_db(license_key, plan_id, email)

        return {
            "status": "success",
            "event": "sale",
            "license_key": license_key,
            "user_id": user_id,
            "plan_id": plan_id,
            "credits": credits,
        }

    async def _handle_refund(self, payload: Dict) -> Dict[str, Any]:
        """Handle refund event — update status in Supabase."""
        sale = payload.get("sale", payload)
        sale_id = sale.get("id") or sale.get("sale_id", "")

        # Update sale status to refunded
        self._update_sale_status(sale_id, "refunded", {
            "refunded_at": datetime.utcnow().isoformat(),
        })

        # Deactivate the associated license
        lic_key = self._deactivate_license_in_db(sale_id)

        return {
            "status": "success",
            "event": "refund",
            "license_deactivated": lic_key or "not_found",
        }

    async def _handle_subscription_cancelled(self, payload: Dict) -> Dict[str, Any]:
        """Handle subscription cancellation — update in Supabase."""
        sale = payload.get("sale", payload)
        sale_id = sale.get("id") or sale.get("sale_id", "")

        self._update_sale_status(sale_id, "cancelled", {
            "cancelled_at": datetime.utcnow().isoformat(),
        })

        return {
            "status": "success",
            "event": "subscription_cancelled",
            "sale_id": sale_id,
        }

    async def _handle_subscription_restarted(self, payload: Dict) -> Dict[str, Any]:
        """Handle subscription restart — reactivate in Supabase."""
        sale = payload.get("sale", payload)
        sale_id = sale.get("id") or sale.get("sale_id", "")

        self._update_sale_status(sale_id, "active", {
            "cancelled_at": None,
        })

        # Re-activate the license
        sb = _get_supabase()
        if sb:
            try:
                result = sb.table("gumroad_sales").select("license_key").eq("sale_id", sale_id).limit(1).execute()
                if result.data and result.data[0].get("license_key"):
                    lic_key = result.data[0]["license_key"]
                    sb.table("licenses").update({
                        "status": "active",
                        "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                    }).eq("license_key", lic_key).execute()
            except Exception:
                pass

        return {
            "status": "success",
            "event": "subscription_restarted",
            "sale_id": sale_id,
        }

    # ═════════════════════════════════════════════════════════════════
    # License Management — DB-backed
    # ═════════════════════════════════════════════════════════════════

    def generate_license_key(self, user_id: str, plan_id: str) -> str:
        """Generate a unique license key."""
        prefix = payment_settings.license_key_prefix
        unique_string = f"{user_id}:{plan_id}:{secrets.token_hex(16)}"
        hash_part = hashlib.sha256(unique_string.encode()).hexdigest()[:24].upper()
        return f"{prefix}-{hash_part[:4]}-{hash_part[4:8]}-{hash_part[8:12]}-{hash_part[12:16]}"

    async def validate_license(self, license_key: str) -> Optional[License]:
        """Validate a license key against the Supabase `licenses` table."""
        # Check for admin/master licenses first (hardcoded)
        admin_licenses = {
            "I3D-ADMIN-LIFETIME-2026": License(
                key="I3D-ADMIN-LIFETIME-2026",
                user_id="admin",
                plan_id="lifetime",
                credits=999999,
                created_at=datetime.utcnow(),
                expires_at=None,
                is_active=True,
                metadata={"type": "admin", "description": "Admin lifetime license"},
            ),
            "I3D-MASTER-UNLIMITED": License(
                key="I3D-MASTER-UNLIMITED",
                user_id="master",
                plan_id="unlimited",
                credits=999999,
                created_at=datetime.utcnow(),
                expires_at=None,
                is_active=True,
                metadata={"type": "master", "description": "Master unlimited license"},
            ),
        }

        license_key_upper = license_key.upper()
        if license_key_upper in admin_licenses:
            return admin_licenses[license_key_upper]

        # Query Supabase licenses table
        sb = _get_supabase()
        if sb:
            try:
                result = sb.table("licenses").select("*").eq("license_key", license_key).limit(1).execute()
                if result.data:
                    row = result.data[0]
                    if row.get("status") != "active":
                        return None
                    # Check expiry
                    expires_at = None
                    if row.get("expires_at"):
                        expires_at = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
                        if expires_at < datetime.utcnow().replace(tzinfo=expires_at.tzinfo):
                            return None

                    # Get credits from gumroad_sales
                    credits = 0
                    sale_result = sb.table("gumroad_sales").select("credits_granted").eq("license_key", license_key).limit(1).execute()
                    if sale_result.data:
                        credits = sale_result.data[0].get("credits_granted", 0)

                    return License(
                        key=license_key,
                        user_id=row.get("email", ""),
                        plan_id=row.get("plan", "starter"),
                        credits=credits,
                        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else datetime.utcnow(),
                        expires_at=expires_at,
                        is_active=True,
                        metadata={"source": "supabase"},
                    )
            except Exception as e:
                print(f"[GumroadProvider] License validation error: {e}")

        return None

    async def get_customer_portal_url(self, customer_id: str) -> Optional[str]:
        """
        Get Gumroad customer library URL.

        Customers manage subscriptions from their Gumroad library.
        """
        return "https://app.gumroad.com/library"

    def _map_product_to_plan(self, product_id: str) -> str:
        """Map Gumroad product ID to internal plan ID."""
        reverse_mapping = {
            gumroad_config.product_ids.get("starter_monthly"): "starter",
            gumroad_config.product_ids.get("pro_monthly"): "pro",
            gumroad_config.product_ids.get("enterprise_monthly"): "enterprise",
            gumroad_config.product_ids.get("credits_small"): "credits_small",
            gumroad_config.product_ids.get("credits_medium"): "credits_medium",
            gumroad_config.product_ids.get("credits_large"): "credits_large",
        }
        return reverse_mapping.get(product_id, "unknown")

    def _get_credits_for_product(self, product_id: str) -> int:
        """Get credit amount for a product."""
        plan_id = self._map_product_to_plan(product_id)

        plan = pricing_config.plans.get(plan_id)
        if plan:
            return plan.get("credits_per_month", 0)

        credit_pack = pricing_config.credit_packs.get(plan_id)
        if credit_pack:
            return credit_pack.get("credits", 0)

        return 0

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
