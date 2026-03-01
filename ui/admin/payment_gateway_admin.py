"""
Payment Gateway Admin Dashboard

Admin panel for managing payment providers with secure key configuration.
Allows admin to:
- Switch between payment providers (Gumroad, Razorpay, etc.)
- Configure secure API keys via environment or Supabase
- Test payment gateway connectivity
- View gateway status and configuration
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QComboBox,
    QLineEdit,
    QTextEdit,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QTabWidget,
    QSplitter,
    QFrame,
    QScrollArea,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor

from core.admin_manager import PaymentGatewayManager
from core.razorpay_client import get_razorpay_client, validate_razorpay_config
from config.payment_config import PaymentProvider, PAYMENT_PROVIDER


class PaymentGatewayAdminDialog(QDialog):
    """
    Admin dialog for managing payment gateways.
    Provides secure configuration and provider switching.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.gateway_manager = PaymentGatewayManager()
        self.setWindowTitle("Payment Gateway Admin")
        self.setMinimumSize(900, 700)
        self.setModal(True)

        self._setup_ui()
        self._load_gateways()

    def _setup_ui(self):
        """Setup the admin UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("💳 Payment Gateway Configuration")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #e2e8f0;")
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel(
            "Manage payment providers and configure secure API keys. "
            "Keys are stored securely and cannot be tampered with."
        )
        subtitle.setStyleSheet("color: #94a3b8; font-size: 13px;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Create tabs
        self.tabs = QTabWidget()

        # Tab 1: Gateway Management
        self.tab_gateways = self._create_gateways_tab()
        self.tabs.addTab(self.tab_gateways, "🔄 Gateway Status")

        # Tab 2: Secure Configuration
        self.tab_config = self._create_config_tab()
        self.tabs.addTab(self.tab_config, "🔐 Secure Keys")

        # Tab 3: Test & Validate
        self.tab_test = self._create_test_tab()
        self.tabs.addTab(self.tab_test, "🧪 Test Connection")

        # Tab 4: Documentation
        self.tab_docs = self._create_docs_tab()
        self.tabs.addTab(self.tab_docs, "📖 Documentation")

        layout.addWidget(self.tabs)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _create_gateways_tab(self) -> QWidget:
        """Create gateway management tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        # Current Active Gateway
        active_group = QGroupBox("Current Active Gateway")
        active_layout = QVBoxLayout(active_group)

        self.active_gateway_label = QLabel("Loading...")
        self.active_gateway_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #4ade80;"
        )
        active_layout.addWidget(self.active_gateway_label)

        # Gateway selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Switch to:"))

        self.gateway_selector = QComboBox()
        self.gateway_selector.setMinimumWidth(200)
        selector_layout.addWidget(self.gateway_selector)

        self.switch_btn = QPushButton("🔄 Switch Gateway")
        self.switch_btn.setObjectName("primaryButton")
        self.switch_btn.clicked.connect(self._switch_gateway)
        selector_layout.addWidget(self.switch_btn)

        selector_layout.addStretch()
        active_layout.addLayout(selector_layout)

        layout.addWidget(active_group)

        # Gateway table
        table_group = QGroupBox("Available Gateways")
        table_layout = QVBoxLayout(table_group)

        self.gateway_table = QTableWidget()
        self.gateway_table.setColumnCount(5)
        self.gateway_table.setHorizontalHeaderLabels(
            ["Gateway", "Status", "Currency", "Fee", "Actions"]
        )
        self.gateway_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.gateway_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.gateway_table.setAlternatingRowColors(True)

        table_layout.addWidget(self.gateway_table)
        layout.addWidget(table_group)

        return widget

    def _create_config_tab(self) -> QWidget:
        """Create secure configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        # Security notice
        notice = QLabel(
            "🔒 SECURITY NOTICE:\n\n"
            "API keys are stored using three-tier security:\n"
            "1. Environment Variables (development)\n"
            "2. Local Cache (runtime)\n"
            "3. Supabase RPC (production - requires valid license)\n\n"
            "Keys are never hardcoded in source code and cannot be tampered with."
        )
        notice.setStyleSheet(
            "background-color: #1e3a5f; padding: 15px; border-radius: 8px; "
            "color: #94a3b8; font-size: 12px;"
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)

        # Environment variables section
        env_group = QGroupBox("Environment Variables (Development)")
        env_layout = QVBoxLayout(env_group)

        env_info = QLabel(
            "Set these in your .env file or system environment:\n\n"
            "RAZORPAY_KEY_ID=rzp_test_...\n"
            "RAZORPAY_KEY_SECRET=...\n"
            "RAZORPAY_WEBHOOK_SECRET=...\n\n"
            "GUMROAD_ACCESS_TOKEN=...\n"
            "STRIPE_SECRET_KEY=sk_...\n"
            "PAYPAL_CLIENT_ID=..."
        )
        env_info.setStyleSheet("font-family: monospace; color: #64748b;")
        env_info.setWordWrap(True)
        env_layout.addWidget(env_info)

        # Check env button
        self.check_env_btn = QPushButton("🔍 Check Environment Variables")
        self.check_env_btn.clicked.connect(self._check_env_vars)
        env_layout.addWidget(self.check_env_btn)

        layout.addWidget(env_group)

        # Supabase RPC section
        supabase_group = QGroupBox("Supabase RPC (Production)")
        supabase_layout = QVBoxLayout(supabase_group)

        supabase_info = QLabel(
            "In production, keys are fetched securely from Supabase via RPC.\n"
            "Requires a valid license. Keys are encrypted in transit and at rest."
        )
        supabase_info.setStyleSheet("color: #64748b;")
        supabase_info.setWordWrap(True)
        supabase_layout.addWidget(supabase_info)

        # Test Supabase connection
        self.test_supabase_btn = QPushButton("🔗 Test Supabase Connection")
        self.test_supabase_btn.clicked.connect(self._test_supabase_connection)
        supabase_layout.addWidget(self.test_supabase_btn)

        layout.addWidget(supabase_group)

        # Key status display
        self.key_status_text = QTextEdit()
        self.key_status_text.setReadOnly(True)
        self.key_status_text.setPlaceholderText("Key status will appear here...")
        self.key_status_text.setMaximumHeight(150)
        layout.addWidget(QLabel("Current Key Status:"))
        layout.addWidget(self.key_status_text)

        layout.addStretch()
        return widget

    def _create_test_tab(self) -> QWidget:
        """Create test connection tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        # Test Razorpay section
        razorpay_group = QGroupBox("Test Razorpay Integration")
        razorpay_layout = QVBoxLayout(razorpay_group)

        self.test_razorpay_btn = QPushButton("🧪 Test Razorpay Configuration")
        self.test_razorpay_btn.setObjectName("primaryButton")
        self.test_razorpay_btn.clicked.connect(self._test_razorpay)
        razorpay_layout.addWidget(self.test_razorpay_btn)

        self.razorpay_result = QTextEdit()
        self.razorpay_result.setReadOnly(True)
        self.razorpay_result.setPlaceholderText(
            "Razorpay test results will appear here..."
        )
        razorpay_layout.addWidget(self.razorpay_result)

        layout.addWidget(razorpay_group)

        # Test Gumroad section
        gumroad_group = QGroupBox("Test Gumroad Integration")
        gumroad_layout = QVBoxLayout(gumroad_group)

        self.test_gumroad_btn = QPushButton("🧪 Test Gumroad Configuration")
        self.test_gumroad_btn.clicked.connect(self._test_gumroad)
        gumroad_layout.addWidget(self.test_gumroad_btn)

        self.gumroad_result = QTextEdit()
        self.gumroad_result.setReadOnly(True)
        self.gumroad_result.setPlaceholderText(
            "Gumroad test results will appear here..."
        )
        gumroad_layout.addWidget(self.gumroad_result)

        layout.addWidget(gumroad_group)

        layout.addStretch()
        return widget

    def _create_docs_tab(self) -> QWidget:
        """Create documentation tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        docs_text = QTextEdit()
        docs_text.setReadOnly(True)
        docs_text.setHtml("""
        <h2>Payment Gateway Configuration Guide</h2>
        
        <h3>🔐 Security Architecture</h3>
        <p>All payment gateway API keys are stored securely using a three-tier system:</p>
        <ol>
            <li><b>Environment Variables</b> - For development and testing</li>
            <li><b>Local Cache</b> - Runtime caching after first fetch</li>
            <li><b>Supabase RPC</b> - Production secure storage (requires valid license)</li>
        </ol>
        
        <h3>⚙️ Configuration Steps</h3>
        
        <h4>For Development:</h4>
        <ol>
            <li>Create a <code>.env</code> file in project root</li>
            <li>Add your test API keys (see .env.example for template)</li>
            <li>Restart the application</li>
        </ol>
        
        <h4>For Production:</h4>
        <ol>
            <li>Set up Supabase <code>get_app_config</code> RPC function</li>
            <li>Store keys securely in Supabase (encrypted)</li>
            <li>Users fetch keys via RPC (requires valid license)</li>
        </ol>
        
        <h3>🔄 Switching Gateways</h3>
        <p>Admin can switch payment providers:</p>
        <ol>
            <li>Go to "Gateway Status" tab</li>
            <li>Select desired gateway from dropdown</li>
            <li>Click "Switch Gateway"</li>
            <li>Ensure API keys are configured for the new gateway</li>
        </ol>
        
        <h3>✅ Testing</h3>
        <p>Always test in test/sandbox mode first:</p>
        <ul>
            <li>Razorpay: Use keys starting with <code>rzp_test_</code></li>
            <li>Stripe: Use test keys (sk_test_...)</li>
            <li>PayPal: Use sandbox mode</li>
        </ul>
        
        <h3>📞 Support</h3>
        <p>For issues with payment configuration:</p>
        <ul>
            <li>Check logs in application directory</li>
            <li>Verify API keys are correct</li>
            <li>Ensure webhook URLs are configured</li>
        </ul>
        """)

        layout.addWidget(docs_text)
        return widget

    def _load_gateways(self):
        """Load gateway data from manager."""
        try:
            # Get active gateway
            active = self.gateway_manager.get_active_gateway()
            self.active_gateway_label.setText(f"🟢 {active.upper()}")

            # Get all gateways
            gateways = self.gateway_manager.get_gateways()

            # Update table
            self.gateway_table.setRowCount(len(gateways))
            self.gateway_selector.clear()

            for i, gateway in enumerate(gateways):
                name = gateway.get("gateway_name", "unknown")
                is_enabled = gateway.get("is_enabled", False)
                currency = gateway.get("currency", "USD")
                fee = gateway.get("fee_percent", 0)

                # Name
                self.gateway_table.setItem(i, 0, QTableWidgetItem(name.upper()))

                # Status
                status_item = QTableWidgetItem(
                    "✅ Enabled" if is_enabled else "❌ Disabled"
                )
                status_item.setForeground(
                    QColor("#4ade80" if is_enabled else "#ef4444")
                )
                self.gateway_table.setItem(i, 1, status_item)

                # Currency
                self.gateway_table.setItem(i, 2, QTableWidgetItem(currency))

                # Fee
                self.gateway_table.setItem(i, 3, QTableWidgetItem(f"{fee}%"))

                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 0, 5, 0)

                toggle_btn = QPushButton("Disable" if is_enabled else "Enable")
                toggle_btn.clicked.connect(
                    lambda checked, n=name, e=is_enabled: self._toggle_gateway(n, not e)
                )
                actions_layout.addWidget(toggle_btn)

                self.gateway_table.setCellWidget(i, 4, actions_widget)

                # Add to selector
                self.gateway_selector.addItem(name.upper(), name)

            # Select current active gateway in selector
            for i in range(self.gateway_selector.count()):
                if self.gateway_selector.itemData(i) == active:
                    self.gateway_selector.setCurrentIndex(i)
                    break

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load gateways: {e}")

    def _toggle_gateway(self, gateway_name: str, enabled: bool):
        """Toggle gateway enabled status."""
        try:
            success = self.gateway_manager.toggle_gateway(gateway_name, enabled)
            if success:
                self._load_gateways()
                QMessageBox.information(
                    self,
                    "Success",
                    f"Gateway '{gateway_name}' {'enabled' if enabled else 'disabled'} successfully.",
                )
            else:
                QMessageBox.warning(self, "Error", "Failed to toggle gateway.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to toggle gateway: {e}")

    def _switch_gateway(self):
        """Switch to selected gateway."""
        selected = self.gateway_selector.currentData()
        if not selected:
            return

        # Disable all other gateways first
        try:
            gateways = self.gateway_manager.get_gateways()
            for gateway in gateways:
                name = gateway.get("gateway_name")
                if name != selected:
                    self.gateway_manager.toggle_gateway(name, False)

            # Enable selected
            self.gateway_manager.toggle_gateway(selected, True)

            self._load_gateways()

            QMessageBox.information(
                self,
                "Gateway Switched",
                f"Payment gateway switched to: {selected.upper()}\n\n"
                f"Make sure API keys are configured for this gateway.",
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to switch gateway: {e}")

    def _check_env_vars(self):
        """Check environment variables."""
        env_vars = {
            "RAZORPAY_KEY_ID": os.getenv("RAZORPAY_KEY_ID", "Not set"),
            "RAZORPAY_KEY_SECRET": os.getenv("RAZORPAY_KEY_SECRET", "Not set"),
            "RAZORPAY_WEBHOOK_SECRET": os.getenv("RAZORPAY_WEBHOOK_SECRET", "Not set"),
            "GUMROAD_ACCESS_TOKEN": os.getenv("GUMROAD_ACCESS_TOKEN", "Not set"),
            "STRIPE_SECRET_KEY": os.getenv("STRIPE_SECRET_KEY", "Not set"),
        }

        status_text = "Environment Variables Status:\n\n"
        for var, value in env_vars.items():
            is_set = value != "Not set"
            status = "✅ Set" if is_set else "❌ Not set"
            display_value = value[:20] + "..." if is_set and len(value) > 20 else value
            status_text += f"{var}:\n  {status}"
            if is_set:
                status_text += f" ({display_value})"
            status_text += "\n\n"

        self.key_status_text.setText(status_text)

    def _test_supabase_connection(self):
        """Test Supabase connection for secure key retrieval."""
        try:
            from core.secret_manager import SecretManager

            # Try to fetch a test key
            test_key = SecretManager.get_secret("RAZORPAY_KEY_ID")

            if test_key:
                self.key_status_text.setText(
                    "✅ Supabase connection successful!\n\n"
                    f"Key fetched: {test_key[:15]}...\n"
                    "Keys are being retrieved securely via SecretManager."
                )
            else:
                self.key_status_text.setText(
                    "⚠️ No key found in Supabase.\n\n"
                    "This could mean:\n"
                    "1. Keys not stored in Supabase yet\n"
                    "2. No valid license (required for RPC access)\n"
                    "3. RPC function not set up\n\n"
                    "For development, set keys in environment variables."
                )
        except Exception as e:
            self.key_status_text.setText(f"❌ Supabase connection failed:\n{str(e)}")

    def _test_razorpay(self):
        """Test Razorpay configuration."""
        try:
            self.razorpay_result.setText("Testing Razorpay configuration...\n")

            is_valid, message = validate_razorpay_config()

            if is_valid:
                client = get_razorpay_client()
                keys_info = client.get_active_keys_info()

                result_text = "✅ Razorpay Configuration Valid!\n\n"
                result_text += "Key Status:\n"
                for key, status in keys_info.items():
                    result_text += f"  • {key}: {status}\n"

                result_text += "\n"
                result_text += f"Active Provider: {PAYMENT_PROVIDER.value}\n"
                result_text += (
                    f"Mode: {'Test' if keys_info.get('mode') == 'Test' else 'Live'}\n\n"
                )
                result_text += "Ready to accept payments!"

                self.razorpay_result.setText(result_text)
            else:
                self.razorpay_result.setText(
                    f"❌ Razorpay Configuration Invalid:\n\n{message}\n\n"
                    f"Please check:\n"
                    f"1. RAZORPAY_KEY_ID is set\n"
                    f"2. RAZORPAY_KEY_SECRET is set\n"
                    f"3. Payment provider is set to RAZORPAY in config"
                )
        except Exception as e:
            self.razorpay_result.setText(f"❌ Razorpay test failed:\n{str(e)}")

    def _test_gumroad(self):
        """Test Gumroad configuration."""
        try:
            self.gumroad_result.setText("Testing Gumroad configuration...\n")

            token = os.getenv("GUMROAD_ACCESS_TOKEN")

            if token:
                self.gumroad_result.setText(
                    f"✅ Gumroad token configured\n\n"
                    f"Token: {token[:10]}...\n\n"
                    f"Note: Full API testing requires implementing Gumroad client."
                )
            else:
                self.gumroad_result.setText(
                    "❌ Gumroad token not found\n\n"
                    "Set GUMROAD_ACCESS_TOKEN in environment variables."
                )
        except Exception as e:
            self.gumroad_result.setText(f"❌ Gumroad test failed:\n{str(e)}")


# Convenience function
def open_payment_gateway_admin(parent=None):
    """Open the payment gateway admin dialog."""
    dialog = PaymentGatewayAdminDialog(parent)
    return dialog.exec()
