"""
Admin UI Package

Contains admin dashboard components for managing the application.
"""

from ui.admin.payment_gateway_admin import (
    PaymentGatewayAdminDialog,
    open_payment_gateway_admin,
)

__all__ = [
    "PaymentGatewayAdminDialog",
    "open_payment_gateway_admin",
]
