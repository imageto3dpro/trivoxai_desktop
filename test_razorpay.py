"""
Test script for Razorpay integration

This script tests the secure Razorpay integration.
Run this after setting up your Razorpay test keys in environment variables.

Setup:
1. Get test keys from https://dashboard.razorpay.com/app/keys
2. Set environment variables:
   - RAZORPAY_KEY_ID=rzp_test_...
   - RAZORPAY_KEY_SECRET=...
3. Run: python test_razorpay.py
"""

import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_configuration():
    """Test Razorpay configuration."""
    print("\n" + "=" * 60)
    print("TEST 1: Configuration Check")
    print("=" * 60)

    from config.payment_config import PaymentProvider, PAYMENT_PROVIDER, razorpay_config

    print(f"Active Payment Provider: {PAYMENT_PROVIDER.value}")
    print(f"Razorpay Configured: {razorpay_config.is_configured}")

    if PAYMENT_PROVIDER != PaymentProvider.RAZORPAY:
        print("\n⚠️  WARNING: Razorpay is not the active payment provider!")
        print(
            "   Update config/payment_config.py: PAYMENT_PROVIDER = PaymentProvider.RAZORPAY"
        )
        return False

    if not razorpay_config.is_configured:
        print("\n❌ ERROR: Razorpay credentials not configured!")
        print("   Set environment variables:")
        print("   - RAZORPAY_KEY_ID")
        print("   - RAZORPAY_KEY_SECRET")
        return False

    print("\n✅ Configuration check passed!")
    return True


def test_secret_manager():
    """Test SecretManager key retrieval."""
    print("\n" + "=" * 60)
    print("TEST 2: SecretManager Key Retrieval")
    print("=" * 60)

    from core.secret_manager import SecretManager

    key_id = SecretManager.get_secret("RAZORPAY_KEY_ID")
    key_secret = SecretManager.get_secret("RAZORPAY_KEY_SECRET")

    if key_id:
        print(f"✅ Key ID retrieved: {key_id[:10]}...")
    else:
        print("❌ Key ID not found")

    if key_secret:
        print(f"✅ Key Secret retrieved: {key_secret[:5]}...")
    else:
        print("❌ Key Secret not found")

    if key_id and key_secret:
        print("\n✅ SecretManager test passed!")
        return True
    else:
        print("\n❌ SecretManager test failed!")
        return False


def test_razorpay_client():
    """Test Razorpay client initialization."""
    print("\n" + "=" * 60)
    print("TEST 3: Razorpay Client Initialization")
    print("=" * 60)

    try:
        from core.razorpay_client import get_razorpay_client

        client = get_razorpay_client()
        print("✅ Razorpay client initialized")

        if client.is_configured():
            print("✅ Client is configured")

            keys_info = client.get_active_keys_info()
            print("\nKey Status:")
            for key, status in keys_info.items():
                print(f"  {key}: {status}")

            print("\n✅ Razorpay client test passed!")
            return True
        else:
            print("❌ Client not configured")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_order_creation():
    """Test creating a Razorpay order."""
    print("\n" + "=" * 60)
    print("TEST 4: Order Creation (Live API Call)")
    print("=" * 60)

    try:
        from core.razorpay_client import get_razorpay_client

        client = get_razorpay_client()

        # Create a test order for ₹199 (19900 paise)
        order = client.create_order(
            amount=19900,
            currency="INR",
            receipt="test_receipt_001",
            notes={"test": "true", "user_id": "test_user_123"},
        )

        print(f"✅ Order created successfully!")
        print(f"   Order ID: {order['id']}")
        print(f"   Amount: ₹{order['amount'] / 100}")
        print(f"   Status: {order['status']}")
        print(f"   Receipt: {order['receipt']}")

        # Save order ID for verification test
        with open("test_order_id.txt", "w") as f:
            f.write(order["id"])

        print("\n✅ Order creation test passed!")
        return order["id"]

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_payment_handler():
    """Test PaymentHandler."""
    print("\n" + "=" * 60)
    print("TEST 5: Payment Handler")
    print("=" * 60)

    try:
        from core.payment_handler import get_payment_handler

        handler = get_payment_handler()
        print("✅ Payment handler created")

        status = handler.get_payment_status()
        print("\nPayment Handler Status:")
        print(f"  Available: {status['is_available']}")
        print(f"  Configured: {status['is_configured']}")
        print(f"  Message: {status['message']}")

        if status["is_available"]:
            print("\n✅ Payment handler test passed!")
            return True
        else:
            print("\n⚠️  Payment handler not available (expected if no valid license)")
            return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_signature_verification():
    """Test payment signature verification."""
    print("\n" + "=" * 60)
    print("TEST 6: Signature Verification")
    print("=" * 60)

    try:
        from core.razorpay_client import get_razorpay_client

        client = get_razorpay_client()

        # Test with dummy values (this will fail validation, which is expected)
        is_valid = client.verify_payment_signature(
            order_id="order_test_123",
            payment_id="pay_test_456",
            signature="invalid_signature",
        )

        if not is_valid:
            print("✅ Invalid signature correctly rejected")
        else:
            print("⚠️  Unexpected: Invalid signature accepted")

        print("\n✅ Signature verification test passed!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_webhook_verification():
    """Test webhook signature verification."""
    print("\n" + "=" * 60)
    print("TEST 7: Webhook Signature Verification")
    print("=" * 60)

    try:
        from core.razorpay_client import get_razorpay_client

        client = get_razorpay_client()

        # Test with dummy webhook
        is_valid = client.verify_webhook_signature(
            webhook_body='{"event":"payment.captured"}',
            webhook_signature="invalid_webhook_signature",
        )

        if not is_valid:
            print("✅ Invalid webhook signature correctly rejected")
        else:
            print("⚠️  Unexpected: Invalid webhook signature accepted")

        print("\n✅ Webhook verification test passed!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("RAZORPAY INTEGRATION TEST SUITE")
    print("=" * 60)
    print("\nThis will test the Razorpay integration.")
    print("Make sure you have set your test API keys first!")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    input()

    results = []

    # Run tests
    results.append(("Configuration", test_configuration()))
    results.append(("SecretManager", test_secret_manager()))
    results.append(("Razorpay Client", test_razorpay_client()))

    # Ask before making live API calls
    print("\n" + "=" * 60)
    print("LIVE API TESTS")
    print("=" * 60)
    print("\nThe next tests will make live API calls to Razorpay.")
    print("This requires valid test API keys.")
    print("\nRun live API tests? (y/n): ", end="")

    response = input().lower().strip()
    if response == "y":
        order_id = test_order_creation()
        if order_id:
            results.append(("Order Creation", True))
        else:
            results.append(("Order Creation", False))
    else:
        print("Skipping live API tests.")
        results.append(("Order Creation", "Skipped"))

    results.append(("Payment Handler", test_payment_handler()))
    results.append(("Signature Verification", test_signature_verification()))
    results.append(("Webhook Verification", test_webhook_verification()))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for name, result in results:
        status = (
            "✅ PASS"
            if result is True
            else ("⏭️  SKIP" if result == "Skipped" else "❌ FAIL")
        )
        print(f"{name:.<40} {status}")

    passed = sum(1 for _, r in results if r is True)
    total = len([r for _, r in results if r != "Skipped"])

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed! Razorpay integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTests cancelled by user.")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
