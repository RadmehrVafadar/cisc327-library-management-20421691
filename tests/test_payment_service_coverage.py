"""
Task 2.2: Code Coverage Tests for PaymentGateway
Tests that execute actual PaymentGateway code (not mocked) to increase coverage.
"""

import pytest
import time
from services.payment_service import PaymentGateway


class TestPaymentGatewayActualExecution:
    """
    Tests that execute the actual PaymentGateway implementation.
    These tests increase code coverage by running the real methods.
    """
    
    def test_payment_gateway_initialization(self):
        """Test PaymentGateway initialization with default API key."""
        gateway = PaymentGateway()
        
        assert gateway.api_key == "test_key_12345"
        assert gateway.base_url == "https://api.payment-gateway.example.com"
    
    def test_payment_gateway_initialization_custom_key(self):
        """Test PaymentGateway initialization with custom API key."""
        gateway = PaymentGateway(api_key="custom_key_999")
        
        assert gateway.api_key == "custom_key_999"
        assert gateway.base_url == "https://api.payment-gateway.example.com"
    
    def test_process_payment_successful(self):
        """Test successful payment processing with valid inputs."""
        gateway = PaymentGateway()
        
        success, txn_id, message = gateway.process_payment(
            patron_id="123456",
            amount=10.50,
            description="Late fees"
        )
        
        assert success is True
        assert txn_id.startswith("txn_123456_")
        assert "Payment of $10.50 processed successfully" in message
    
    def test_process_payment_invalid_amount_zero(self):
        """Test payment processing with zero amount."""
        gateway = PaymentGateway()
        
        success, txn_id, message = gateway.process_payment(
            patron_id="123456",
            amount=0,
            description="Test"
        )
        
        assert success is False
        assert txn_id == ""
        assert "Invalid amount: must be greater than 0" in message
    
    def test_process_payment_invalid_amount_negative(self):
        """Test payment processing with negative amount."""
        gateway = PaymentGateway()
        
        success, txn_id, message = gateway.process_payment(
            patron_id="123456",
            amount=-5.00,
            description="Test"
        )
        
        assert success is False
        assert txn_id == ""
        assert "Invalid amount: must be greater than 0" in message
    
    def test_process_payment_amount_exceeds_limit(self):
        """Test payment processing with amount exceeding $1000 limit."""
        gateway = PaymentGateway()
        
        success, txn_id, message = gateway.process_payment(
            patron_id="123456",
            amount=1500.00,
            description="Test"
        )
        
        assert success is False
        assert txn_id == ""
        assert "Payment declined: amount exceeds limit" in message
    
    def test_process_payment_invalid_patron_id_too_short(self):
        """Test payment processing with invalid patron ID (too short)."""
        gateway = PaymentGateway()
        
        success, txn_id, message = gateway.process_payment(
            patron_id="12345",
            amount=10.00,
            description="Test"
        )
        
        assert success is False
        assert txn_id == ""
        assert "Invalid patron ID format" in message
    
    def test_process_payment_invalid_patron_id_too_long(self):
        """Test payment processing with invalid patron ID (too long)."""
        gateway = PaymentGateway()
        
        success, txn_id, message = gateway.process_payment(
            patron_id="1234567",
            amount=10.00,
            description="Test"
        )
        
        assert success is False
        assert txn_id == ""
        assert "Invalid patron ID format" in message
    
    def test_process_payment_with_description(self):
        """Test payment processing includes description in transaction."""
        gateway = PaymentGateway()
        
        success, txn_id, message = gateway.process_payment(
            patron_id="654321",
            amount=15.00,
            description="Late fees for 'Python Programming'"
        )
        
        assert success is True
        assert txn_id.startswith("txn_654321_")
        assert "$15.00" in message
    
    def test_refund_payment_successful(self):
        """Test successful refund processing."""
        gateway = PaymentGateway()
        
        success, message = gateway.refund_payment(
            transaction_id="txn_123456_1699999999",
            amount=10.50
        )
        
        assert success is True
        assert "Refund of $10.50 processed successfully" in message
        assert "Refund ID:" in message
    
    def test_refund_payment_invalid_transaction_id_format(self):
        """Test refund with invalid transaction ID format."""
        gateway = PaymentGateway()
        
        success, message = gateway.refund_payment(
            transaction_id="invalid_123",
            amount=5.00
        )
        
        assert success is False
        assert "Invalid transaction ID" in message
    
    def test_refund_payment_empty_transaction_id(self):
        """Test refund with empty transaction ID."""
        gateway = PaymentGateway()
        
        success, message = gateway.refund_payment(
            transaction_id="",
            amount=5.00
        )
        
        assert success is False
        assert "Invalid transaction ID" in message
    
    def test_refund_payment_invalid_amount_zero(self):
        """Test refund with zero amount."""
        gateway = PaymentGateway()
        
        success, message = gateway.refund_payment(
            transaction_id="txn_123456_1699999999",
            amount=0
        )
        
        assert success is False
        assert "Invalid refund amount" in message
    
    def test_refund_payment_invalid_amount_negative(self):
        """Test refund with negative amount."""
        gateway = PaymentGateway()
        
        success, message = gateway.refund_payment(
            transaction_id="txn_123456_1699999999",
            amount=-10.00
        )
        
        assert success is False
        assert "Invalid refund amount" in message
    
    def test_refund_payment_valid_transaction_id_format(self):
        """Test refund with valid transaction ID starting with txn_."""
        gateway = PaymentGateway()
        
        success, message = gateway.refund_payment(
            transaction_id="txn_999999_1234567890",
            amount=7.50
        )
        
        assert success is True
        assert "Refund of $7.50" in message
    
    def test_verify_payment_status_valid_transaction(self):
        """Test payment status verification with valid transaction ID."""
        gateway = PaymentGateway()
        
        result = gateway.verify_payment_status("txn_123456_1699999999")
        
        assert result["transaction_id"] == "txn_123456_1699999999"
        assert result["status"] == "completed"
        assert result["amount"] == 10.50
        assert "timestamp" in result
    
    def test_verify_payment_status_invalid_transaction_id_format(self):
        """Test payment status verification with invalid transaction ID."""
        gateway = PaymentGateway()
        
        result = gateway.verify_payment_status("invalid_123")
        
        assert result["status"] == "not_found"
        assert result["message"] == "Transaction not found"
    
    def test_verify_payment_status_empty_transaction_id(self):
        """Test payment status verification with empty transaction ID."""
        gateway = PaymentGateway()
        
        result = gateway.verify_payment_status("")
        
        assert result["status"] == "not_found"
        assert result["message"] == "Transaction not found"
    
    def test_process_payment_transaction_id_uniqueness(self):
        """Test that transaction IDs are unique (include timestamp)."""
        gateway = PaymentGateway()
        
        success1, txn_id1, _ = gateway.process_payment("111111", 5.00, "Test 1")
        time.sleep(1.1)  # Wait to ensure different timestamp
        success2, txn_id2, _ = gateway.process_payment("111111", 5.00, "Test 2")
        
        assert success1 is True
        assert success2 is True
        assert txn_id1 != txn_id2  # Different timestamps = different IDs
    
    def test_process_payment_boundary_amount_one_cent(self):
        """Test payment processing with smallest valid amount ($0.01)."""
        gateway = PaymentGateway()
        
        success, txn_id, message = gateway.process_payment(
            patron_id="999999",
            amount=0.01,
            description="Minimum payment"
        )
        
        assert success is True
        assert txn_id.startswith("txn_999999_")
        assert "$0.01" in message
    
    def test_process_payment_boundary_amount_max_allowed(self):
        """Test payment processing with maximum allowed amount ($1000)."""
        gateway = PaymentGateway()
        
        success, txn_id, message = gateway.process_payment(
            patron_id="888888",
            amount=1000.00,
            description="Maximum payment"
        )
        
        assert success is True
        assert txn_id.startswith("txn_888888_")
        assert "$1000.00" in message
    
    def test_refund_payment_boundary_amount(self):
        """Test refund with minimum valid amount."""
        gateway = PaymentGateway()
        
        success, message = gateway.refund_payment(
            transaction_id="txn_777777_1234567890",
            amount=0.01
        )
        
        assert success is True
        assert "$0.01" in message


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

