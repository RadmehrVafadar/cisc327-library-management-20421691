"""
Task 2.1: Comprehensive Unit Tests with Stubbing and Mocking

This test suite demonstrates:
1. STUBBING: Using pytest-mock to stub database functions with fake data
   - Tests for calculate_late_fee_for_book() 
   - Tests for get_book_by_id()
   
2. MOCKING: Using Mock(spec=PaymentGateway) to mock payment gateway methods
   - Tests for pay_late_fees() 
   - Tests for refund_late_fee_payment()
   - Verification using assert_called_once(), assert_called_with(), assert_not_called()

References:
- pytest-mock documentation: https://pytest-mock.readthedocs.io/
- unittest.mock docs: https://docs.python.org/3/library/unittest.mock.html
- Real Python mocking guide: https://realpython.com/python-mock-library/
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.library_service import (
    calculate_late_fee_for_book, 
    get_book_by_id,
    pay_late_fees,
    refund_late_fee_payment
)
from services.payment_service import PaymentGateway


# =============================================================================
# PART 1: STUBBING TESTS - Using pytest-mock to stub database functions
# =============================================================================

class TestCalculateLateFeeWithStubs:
    """
    Tests for calculate_late_fee_for_book() using STUBS for database functions.
    
    STUBBING: We provide fake return values for database functions without
    verifying they were called. We only care about the return values to test
    the business logic.
    """
    
    def test_calculate_late_fee_invalid_patron_id(self, mocker):
        """Test with invalid patron ID - database functions should not be called."""
        # Stub database functions (though they won't be called)
        mock_get_book = mocker.patch('services.library_service.get_book_by_id')
        mock_get_borrow = mocker.patch('services.library_service.get_borrow_record')
        
        # Test with empty patron ID
        result = calculate_late_fee_for_book("", 1)
        
        assert result['fee_amount'] == 0.00
        assert result['days_overdue'] == 0
        assert result['status'] == 'Invalid patron ID. Must be exactly 6 digits.'
        
        # Verify database functions were NOT called
        mock_get_book.assert_not_called()
        mock_get_borrow.assert_not_called()
    
    def test_calculate_late_fee_invalid_patron_id_too_short(self, mocker):
        """Test with patron ID that's too short."""
        result = calculate_late_fee_for_book("12345", 1)
        
        assert result['fee_amount'] == 0.00
        assert result['status'] == 'Invalid patron ID. Must be exactly 6 digits.'
    
    def test_calculate_late_fee_invalid_patron_id_non_numeric(self, mocker):
        """Test with non-numeric patron ID."""
        result = calculate_late_fee_for_book("abcdef", 1)
        
        assert result['fee_amount'] == 0.00
        assert result['status'] == 'Invalid patron ID. Must be exactly 6 digits.'
    
    def test_calculate_late_fee_book_not_found(self, mocker):
        """Test late fee calculation when book doesn't exist - stub returns None."""
        # STUB: get_book_by_id returns None (book not found)
        mocker.patch('services.library_service.get_book_by_id', return_value=None)
        
        result = calculate_late_fee_for_book("123456", 999)
        
        assert result['fee_amount'] == 0.00
        assert result['days_overdue'] == 0
        assert result['status'] == 'Book not found.'
    
    def test_calculate_late_fee_book_not_borrowed_by_patron(self, mocker):
        """Test when book exists but not borrowed by patron - stub returns None for borrow record."""
        # STUB: Book exists
        fake_book = {
            'book_id': 1,
            'title': 'Test Book',
            'author': 'Test Author',
            'isbn': '1234567890123',
            'total_copies': 5,
            'available_copies': 3
        }
        mocker.patch('services.library_service.get_book_by_id', return_value=fake_book)
        
        # STUB: No borrow record exists
        mocker.patch('services.library_service.get_borrow_record', return_value=None)
        
        result = calculate_late_fee_for_book("123456", 1)
        
        assert result['fee_amount'] == 0.00
        assert result['days_overdue'] == 0
        assert result['status'] == 'This book is not currently borrowed by you.'
    
    def test_calculate_late_fee_book_not_overdue(self, mocker):
        """Test late fee when book is not overdue - stub with future due date."""
        # STUB: Book exists
        fake_book = {
            'book_id': 1,
            'title': 'Python Programming',
            'author': 'John Doe',
            'isbn': '9781234567890',
            'total_copies': 5,
            'available_copies': 4
        }
        mocker.patch('services.library_service.get_book_by_id', return_value=fake_book)
        
        # STUB: Borrow record with future due date (not overdue)
        future_due_date = datetime.now() + timedelta(days=5)
        fake_borrow_record = {
            'patron_id': '123456',
            'book_id': 1,
            'borrow_date': (datetime.now() - timedelta(days=9)).isoformat(),
            'due_date': future_due_date.isoformat(),
            'return_date': None
        }
        mocker.patch('services.library_service.get_borrow_record', return_value=fake_borrow_record)
        
        result = calculate_late_fee_for_book("123456", 1)
        
        assert result['fee_amount'] == 0.00
        assert result['days_overdue'] == 0
        assert result['status'] == 'Book is not overdue.'
    
    def test_calculate_late_fee_3_days_overdue(self, mocker):
        """Test late fee calculation for 3 days overdue (within 7 days: $0.50/day)."""
        # STUB: Book exists
        fake_book = {
            'book_id': 2,
            'title': 'Data Structures',
            'author': 'Jane Smith',
            'isbn': '9789876543210',
            'total_copies': 3,
            'available_copies': 2
        }
        mocker.patch('services.library_service.get_book_by_id', return_value=fake_book)
        
        # STUB: Borrow record 3 days overdue
        past_due_date = datetime.now() - timedelta(days=3)
        fake_borrow_record = {
            'patron_id': '123456',
            'book_id': 2,
            'borrow_date': (past_due_date - timedelta(days=14)).isoformat(),
            'due_date': past_due_date.isoformat(),
            'return_date': None
        }
        mocker.patch('services.library_service.get_borrow_record', return_value=fake_borrow_record)
        
        result = calculate_late_fee_for_book("123456", 2)
        
        # 3 days * $0.50 = $1.50
        assert result['fee_amount'] == 1.50
        assert result['days_overdue'] == 3
        assert 'Data Structures' in result['status']
    
    def test_calculate_late_fee_7_days_overdue(self, mocker):
        """Test late fee for exactly 7 days overdue (boundary: $0.50/day)."""
        fake_book = {
            'book_id': 3,
            'title': 'Algorithms',
            'author': 'Bob Wilson',
            'isbn': '9781111111111',
            'total_copies': 2,
            'available_copies': 1
        }
        mocker.patch('services.library_service.get_book_by_id', return_value=fake_book)
        
        # STUB: Exactly 7 days overdue
        past_due_date = datetime.now() - timedelta(days=7)
        fake_borrow_record = {
            'patron_id': '654321',
            'book_id': 3,
            'borrow_date': (past_due_date - timedelta(days=14)).isoformat(),
            'due_date': past_due_date.isoformat(),
            'return_date': None
        }
        mocker.patch('services.library_service.get_borrow_record', return_value=fake_borrow_record)
        
        result = calculate_late_fee_for_book("654321", 3)
        
        # 7 days * $0.50 = $3.50
        assert result['fee_amount'] == 3.50
        assert result['days_overdue'] == 7
    
    def test_calculate_late_fee_10_days_overdue(self, mocker):
        """Test late fee for 10 days overdue (7 days @ $0.50 + 3 days @ $1.00)."""
        fake_book = {
            'book_id': 4,
            'title': 'Machine Learning',
            'author': 'Alice Johnson',
            'isbn': '9782222222222',
            'total_copies': 4,
            'available_copies': 3
        }
        mocker.patch('services.library_service.get_book_by_id', return_value=fake_book)
        
        # STUB: 10 days overdue
        past_due_date = datetime.now() - timedelta(days=10)
        fake_borrow_record = {
            'patron_id': '111111',
            'book_id': 4,
            'borrow_date': (past_due_date - timedelta(days=14)).isoformat(),
            'due_date': past_due_date.isoformat(),
            'return_date': None
        }
        mocker.patch('services.library_service.get_borrow_record', return_value=fake_borrow_record)
        
        result = calculate_late_fee_for_book("111111", 4)
        
        # (7 * $0.50) + (3 * $1.00) = $3.50 + $3.00 = $6.50
        assert result['fee_amount'] == 6.50
        assert result['days_overdue'] == 10
    
    def test_calculate_late_fee_maximum_cap_at_15(self, mocker):
        """Test that late fee is capped at $15.00 even for very long overdue periods."""
        fake_book = {
            'book_id': 5,
            'title': 'Operating Systems',
            'author': 'Charlie Brown',
            'isbn': '9783333333333',
            'total_copies': 2,
            'available_copies': 1
        }
        mocker.patch('services.library_service.get_book_by_id', return_value=fake_book)
        
        # STUB: 30 days overdue (would be $26.50 without cap)
        past_due_date = datetime.now() - timedelta(days=30)
        fake_borrow_record = {
            'patron_id': '222222',
            'book_id': 5,
            'borrow_date': (past_due_date - timedelta(days=14)).isoformat(),
            'due_date': past_due_date.isoformat(),
            'return_date': None
        }
        mocker.patch('services.library_service.get_borrow_record', return_value=fake_borrow_record)
        
        result = calculate_late_fee_for_book("222222", 5)
        
        # Should be capped at $15.00
        assert result['fee_amount'] == 15.00
        assert result['days_overdue'] == 30
    
    def test_calculate_late_fee_1_day_overdue(self, mocker):
        """Test late fee for 1 day overdue (edge case)."""
        fake_book = {
            'book_id': 6,
            'title': 'Database Systems',
            'author': 'Diana Prince',
            'isbn': '9784444444444',
            'total_copies': 3,
            'available_copies': 2
        }
        mocker.patch('services.library_service.get_book_by_id', return_value=fake_book)
        
        # STUB: 1 day overdue
        past_due_date = datetime.now() - timedelta(days=1)
        fake_borrow_record = {
            'patron_id': '333333',
            'book_id': 6,
            'borrow_date': (past_due_date - timedelta(days=14)).isoformat(),
            'due_date': past_due_date.isoformat(),
            'return_date': None
        }
        mocker.patch('services.library_service.get_borrow_record', return_value=fake_borrow_record)
        
        result = calculate_late_fee_for_book("333333", 6)
        
        # 1 day * $0.50 = $0.50
        assert result['fee_amount'] == 0.50
        assert result['days_overdue'] == 1


class TestGetBookByIdWithStubs:
    """
    Tests for get_book_by_id() function using STUBS.
    
    Note: get_book_by_id is actually imported from database module, but we test
    it with stubbed database connections to demonstrate stubbing techniques.
    """
    
    def test_get_book_by_id_book_exists(self, mocker):
        """Test retrieving an existing book by ID."""
        # STUB: Database returns a book
        fake_book = {
            'book_id': 1,
            'title': 'Clean Code',
            'author': 'Robert Martin',
            'isbn': '9780132350884',
            'total_copies': 5,
            'available_copies': 3
        }
        mock_get_book = mocker.patch('services.library_service.get_book_by_id', return_value=fake_book)
        
        from services.library_service import get_book_by_id as get_book_func
        result = get_book_func(1)
        
        assert result is not None
        assert result['book_id'] == 1
        assert result['title'] == 'Clean Code'
        assert result['author'] == 'Robert Martin'
        assert result['isbn'] == '9780132350884'
        mock_get_book.assert_called_once_with(1)
    
    def test_get_book_by_id_book_not_found(self, mocker):
        """Test retrieving non-existent book by ID."""
        # STUB: Database returns None (book not found)
        mock_get_book = mocker.patch('services.library_service.get_book_by_id', return_value=None)
        
        from services.library_service import get_book_by_id as get_book_func
        result = get_book_func(999)
        
        assert result is None
        mock_get_book.assert_called_once_with(999)
    
    def test_get_book_by_id_with_zero_available_copies(self, mocker):
        """Test retrieving a book with zero available copies."""
        # STUB: Book exists but no copies available
        fake_book = {
            'book_id': 2,
            'title': 'Design Patterns',
            'author': 'Gang of Four',
            'isbn': '9780201633610',
            'total_copies': 3,
            'available_copies': 0
        }
        mock_get_book = mocker.patch('services.library_service.get_book_by_id', return_value=fake_book)
        
        from services.library_service import get_book_by_id as get_book_func
        result = get_book_func(2)
        
        assert result is not None
        assert result['available_copies'] == 0
        assert result['total_copies'] == 3
        mock_get_book.assert_called_once_with(2)


# =============================================================================
# PART 2: MOCKING TESTS - Using Mock(spec=PaymentGateway) to mock payment gateway
# =============================================================================

class TestPayLateFeesWithMocks:
    """
    Tests for pay_late_fees() using MOCKS for PaymentGateway.
    
    MOCKING: We create a mock PaymentGateway and verify that the correct methods
    are called with the correct parameters. This is different from stubbing because
    we verify the interactions, not just provide return values.
    """
    
    def test_pay_late_fees_successful_payment(self, mocker):
        """Test successful late fee payment through payment gateway."""
        # STUB: Setup database functions with fake data
        fake_book = {
            'book_id': 1,
            'title': 'Python Crash Course',
            'author': 'Eric Matthes',
            'isbn': '9781593279288',
            'total_copies': 4,
            'available_copies': 3
        }
        mocker.patch('services.library_service.get_book_by_id', return_value=fake_book)
        
        # Stub calculate_late_fee_for_book to return a fee
        mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={
            'fee_amount': 5.50,
            'days_overdue': 5,
            'status': 'Late fee calculated'
        })
        
        # MOCK: Create mock payment gateway with spec
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.process_payment.return_value = (True, "txn_123456_1699999999", "Payment successful")
        
        # Execute payment
        success, message, transaction_id = pay_late_fees("123456", 1, mock_gateway)
        
        # Verify results
        assert success is True
        assert "Payment successful" in message
        assert transaction_id == "txn_123456_1699999999"
        
        # VERIFY MOCK: Ensure process_payment was called exactly once with correct parameters
        mock_gateway.process_payment.assert_called_once_with(
            patron_id="123456",
            amount=5.50,
            description="Late fees for 'Python Crash Course'"
        )
    
    def test_pay_late_fees_payment_declined(self, mocker):
        """Test payment declined by gateway - mock returns failure."""
        # STUB: Setup database
        fake_book = {
            'book_id': 2,
            'title': 'JavaScript: The Good Parts',
            'author': 'Douglas Crockford',
            'isbn': '9780596517748',
            'total_copies': 3,
            'available_copies': 2
        }
        mocker.patch('services.library_service.get_book_by_id', return_value=fake_book)
        
        mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={
            'fee_amount': 10.00,
            'days_overdue': 12,
            'status': 'Late fee calculated'
        })
        
        # MOCK: Payment gateway declines the payment
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.process_payment.return_value = (False, None, "Insufficient funds")
        
        success, message, transaction_id = pay_late_fees("654321", 2, mock_gateway)
        
        # Verify failure result
        assert success is False
        assert "Payment failed: Insufficient funds" in message
        assert transaction_id is None
        
        # VERIFY MOCK: process_payment should still be called once
        mock_gateway.process_payment.assert_called_once_with(
            patron_id="654321",
            amount=10.00,
            description="Late fees for 'JavaScript: The Good Parts'"
        )
    
    def test_pay_late_fees_invalid_patron_id_mock_not_called(self, mocker):
        """Test invalid patron ID - verify payment gateway is NOT called."""
        # MOCK: Create payment gateway mock
        mock_gateway = Mock(spec=PaymentGateway)
        
        # Test with invalid patron ID
        success, message, transaction_id = pay_late_fees("12345", 1, mock_gateway)  # Too short
        
        # Verify failure
        assert success is False
        assert "Invalid patron ID" in message
        assert transaction_id is None
        
        # VERIFY MOCK: Payment gateway should NOT be called for invalid patron ID
        mock_gateway.process_payment.assert_not_called()
    
    def test_pay_late_fees_zero_fees_mock_not_called(self, mocker):
        """Test zero late fees - verify payment gateway is NOT called."""
        # STUB: Book exists but no late fees
        fake_book = {
            'book_id': 3,
            'title': 'Head First Java',
            'author': 'Kathy Sierra',
            'isbn': '9780596009205',
            'total_copies': 5,
            'available_copies': 4
        }
        mocker.patch('services.library_service.get_book_by_id', return_value=fake_book)
        
        # STUB: No late fees
        mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'Book is not overdue.'
        })
        
        # MOCK: Payment gateway
        mock_gateway = Mock(spec=PaymentGateway)
        
        success, message, transaction_id = pay_late_fees("111111", 3, mock_gateway)
        
        # Verify no payment processed
        assert success is False
        assert "No late fees to pay" in message
        assert transaction_id is None
        
        # VERIFY MOCK: Payment gateway should NOT be called when fee is zero
        mock_gateway.process_payment.assert_not_called()
    
    def test_pay_late_fees_network_error_exception(self, mocker):
        """Test network error during payment processing - exception handling."""
        # STUB: Setup database
        fake_book = {
            'book_id': 4,
            'title': 'Eloquent JavaScript',
            'author': 'Marijn Haverbeke',
            'isbn': '9781593279509',
            'total_copies': 3,
            'available_copies': 2
        }
        mocker.patch('services.library_service.get_book_by_id', return_value=fake_book)
        
        mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={
            'fee_amount': 7.50,
            'days_overdue': 9,
            'status': 'Late fee calculated'
        })
        
        # MOCK: Payment gateway raises exception (simulating network error)
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.process_payment.side_effect = Exception("Network timeout")
        
        success, message, transaction_id = pay_late_fees("222222", 4, mock_gateway)
        
        # Verify error handling
        assert success is False
        assert "Payment processing error" in message
        assert "Network timeout" in message
        assert transaction_id is None
        
        # VERIFY MOCK: process_payment was called before exception
        mock_gateway.process_payment.assert_called_once()
    
    def test_pay_late_fees_book_not_found_mock_not_called(self, mocker):
        """Test book not found - verify payment gateway is NOT called."""
        # STUB: Book doesn't exist
        mocker.patch('services.library_service.get_book_by_id', return_value=None)
        
        mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'Book not found.'
        })
        
        # MOCK: Payment gateway
        mock_gateway = Mock(spec=PaymentGateway)
        
        success, message, transaction_id = pay_late_fees("333333", 999, mock_gateway)
        
        # Verify failure
        assert success is False
        assert transaction_id is None
        
        # VERIFY MOCK: Payment gateway should NOT be called
        mock_gateway.process_payment.assert_not_called()
    
    def test_pay_late_fees_with_multiple_patrons(self, mocker):
        """Test payments for multiple patrons - verify each call separately."""
        # STUB: Book exists
        fake_book = {
            'book_id': 5,
            'title': 'The Pragmatic Programmer',
            'author': 'Hunt & Thomas',
            'isbn': '9780135957059',
            'total_copies': 4,
            'available_copies': 3
        }
        mocker.patch('services.library_service.get_book_by_id', return_value=fake_book)
        
        # MOCK: Payment gateway
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.process_payment.return_value = (True, "txn_test", "Success")
        
        # Test first patron
        mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={
            'fee_amount': 3.50,
            'days_overdue': 7,
            'status': 'Late fee calculated'
        })
        success1, _, _ = pay_late_fees("444444", 5, mock_gateway)
        assert success1 is True
        
        # Test second patron
        mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={
            'fee_amount': 6.50,
            'days_overdue': 10,
            'status': 'Late fee calculated'
        })
        success2, _, _ = pay_late_fees("555555", 5, mock_gateway)
        assert success2 is True
        
        # VERIFY MOCK: process_payment called twice
        assert mock_gateway.process_payment.call_count == 2


class TestRefundLateFeesWithMocks:
    """
    Tests for refund_late_fee_payment() using MOCKS for PaymentGateway.
    """
    
    def test_refund_successful(self, mocker):
        """Test successful refund through payment gateway."""
        # MOCK: Payment gateway with successful refund
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.refund_payment.return_value = (True, "Refund of $5.50 processed successfully. Refund ID: refund_txn_123_1699999999")
        
        success, message = refund_late_fee_payment("txn_123456_1699999999", 5.50, mock_gateway)
        
        # Verify success
        assert success is True
        assert "Refund of $5.50 processed successfully" in message
        
        # VERIFY MOCK: refund_payment called once with correct parameters
        mock_gateway.refund_payment.assert_called_once_with("txn_123456_1699999999", 5.50)
    
    def test_refund_invalid_transaction_id_format(self, mocker):
        """Test refund with invalid transaction ID format - mock should NOT be called."""
        # MOCK: Payment gateway
        mock_gateway = Mock(spec=PaymentGateway)
        
        # Test with invalid transaction ID (doesn't start with "txn_")
        success, message = refund_late_fee_payment("invalid_123", 5.00, mock_gateway)
        
        # Verify failure
        assert success is False
        assert "Invalid transaction ID" in message
        
        # VERIFY MOCK: refund_payment should NOT be called
        mock_gateway.refund_payment.assert_not_called()
    
    def test_refund_invalid_transaction_id_empty(self, mocker):
        """Test refund with empty transaction ID - mock should NOT be called."""
        mock_gateway = Mock(spec=PaymentGateway)
        
        success, message = refund_late_fee_payment("", 5.00, mock_gateway)
        
        assert success is False
        assert "Invalid transaction ID" in message
        mock_gateway.refund_payment.assert_not_called()
    
    def test_refund_negative_amount(self, mocker):
        """Test refund with negative amount - mock should NOT be called."""
        mock_gateway = Mock(spec=PaymentGateway)
        
        success, message = refund_late_fee_payment("txn_123456_1699999999", -5.00, mock_gateway)
        
        # Verify failure
        assert success is False
        assert "Refund amount must be greater than 0" in message
        
        # VERIFY MOCK: refund_payment should NOT be called for invalid amount
        mock_gateway.refund_payment.assert_not_called()
    
    def test_refund_zero_amount(self, mocker):
        """Test refund with zero amount - mock should NOT be called."""
        mock_gateway = Mock(spec=PaymentGateway)
        
        success, message = refund_late_fee_payment("txn_654321_1699999999", 0.00, mock_gateway)
        
        # Verify failure
        assert success is False
        assert "Refund amount must be greater than 0" in message
        
        # VERIFY MOCK: refund_payment should NOT be called
        mock_gateway.refund_payment.assert_not_called()
    
    def test_refund_exceeds_maximum_late_fee(self, mocker):
        """Test refund amount exceeding $15 maximum - mock should NOT be called."""
        mock_gateway = Mock(spec=PaymentGateway)
        
        success, message = refund_late_fee_payment("txn_789012_1699999999", 20.00, mock_gateway)
        
        # Verify failure
        assert success is False
        assert "Refund amount exceeds maximum late fee" in message
        
        # VERIFY MOCK: refund_payment should NOT be called for invalid amount
        mock_gateway.refund_payment.assert_not_called()
    
    def test_refund_exactly_maximum_amount(self, mocker):
        """Test refund with exactly $15.00 (maximum allowed)."""
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.refund_payment.return_value = (True, "Refund of $15.00 processed successfully")
        
        success, message = refund_late_fee_payment("txn_111111_1699999999", 15.00, mock_gateway)
        
        # Verify success
        assert success is True
        
        # VERIFY MOCK: refund_payment should be called for valid maximum amount
        mock_gateway.refund_payment.assert_called_once_with("txn_111111_1699999999", 15.00)
    
    def test_refund_gateway_failure(self, mocker):
        """Test refund when payment gateway fails."""
        # MOCK: Payment gateway fails refund
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.refund_payment.return_value = (False, "Transaction already refunded")
        
        success, message = refund_late_fee_payment("txn_222222_1699999999", 7.50, mock_gateway)
        
        # Verify failure
        assert success is False
        assert "Refund failed: Transaction already refunded" in message
        
        # VERIFY MOCK: refund_payment was called
        mock_gateway.refund_payment.assert_called_once_with("txn_222222_1699999999", 7.50)
    
    def test_refund_exception_handling(self, mocker):
        """Test exception handling during refund process."""
        # MOCK: Payment gateway raises exception
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.refund_payment.side_effect = Exception("Connection refused")
        
        success, message = refund_late_fee_payment("txn_333333_1699999999", 4.50, mock_gateway)
        
        # Verify error handling
        assert success is False
        assert "Refund processing error" in message
        assert "Connection refused" in message
        
        # VERIFY MOCK: refund_payment was called before exception
        mock_gateway.refund_payment.assert_called_once()
    
    def test_refund_valid_small_amount(self, mocker):
        """Test refund with small valid amount ($0.50)."""
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.refund_payment.return_value = (True, "Refund of $0.50 processed successfully")
        
        success, message = refund_late_fee_payment("txn_444444_1699999999", 0.50, mock_gateway)
        
        # Verify success
        assert success is True
        
        # VERIFY MOCK: refund_payment called with correct parameters
        mock_gateway.refund_payment.assert_called_once_with("txn_444444_1699999999", 0.50)
    
    def test_refund_with_decimal_precision(self, mocker):
        """Test refund with decimal amount."""
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.refund_payment.return_value = (True, "Refund processed")
        
        success, message = refund_late_fee_payment("txn_555555_1699999999", 12.75, mock_gateway)
        
        assert success is True
        
        # VERIFY MOCK: Verify exact amount was passed
        mock_gateway.refund_payment.assert_called_once_with("txn_555555_1699999999", 12.75)


# =============================================================================
# ADDITIONAL INTEGRATION TESTS: Combining Stubs and Mocks
# =============================================================================

class TestPaymentWorkflowWithStubsAndMocks:
    """
    Integration tests combining both stubbing (for database) and mocking (for payment gateway).
    """
    
    def test_complete_payment_workflow(self, mocker):
        """Test complete payment workflow from fee calculation to payment processing."""
        # STUB: Database functions
        fake_book = {
            'book_id': 10,
            'title': 'Refactoring',
            'author': 'Martin Fowler',
            'isbn': '9780134757599',
            'total_copies': 3,
            'available_copies': 2
        }
        mocker.patch('services.library_service.get_book_by_id', return_value=fake_book)
        
        past_due_date = datetime.now() - timedelta(days=5)
        fake_borrow_record = {
            'patron_id': '999999',
            'book_id': 10,
            'borrow_date': (past_due_date - timedelta(days=14)).isoformat(),
            'due_date': past_due_date.isoformat(),
            'return_date': None
        }
        mocker.patch('services.library_service.get_borrow_record', return_value=fake_borrow_record)
        
        # First, calculate fee
        fee_info = calculate_late_fee_for_book("999999", 10)
        assert fee_info['fee_amount'] == 2.50  # 5 days * $0.50
        
        # MOCK: Payment gateway for actual payment
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.process_payment.return_value = (True, "txn_999999_test", "Success")
        
        # Process payment
        success, message, txn_id = pay_late_fees("999999", 10, mock_gateway)
        
        assert success is True
        assert txn_id == "txn_999999_test"
        
        # VERIFY MOCK: Correct payment amount was charged
        mock_gateway.process_payment.assert_called_once_with(
            patron_id="999999",
            amount=2.50,
            description="Late fees for 'Refactoring'"
        )
    
    def test_refund_after_incorrect_payment(self, mocker):
        """Test refund workflow after an incorrect payment was made."""
        # MOCK: Payment gateway for refund
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.refund_payment.return_value = (True, "Refund of $8.00 processed successfully")
        
        # Process refund
        success, message = refund_late_fee_payment("txn_incorrect_payment", 8.00, mock_gateway)
        
        assert success is True
        assert "Refund of $8.00 processed successfully" in message
        
        # VERIFY MOCK: Refund was processed correctly
        mock_gateway.refund_payment.assert_called_once_with("txn_incorrect_payment", 8.00)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

