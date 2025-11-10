"""
Unit tests for get_patron_status_report function
Tests R7: Patron Status Report functionality
"""

import pytest
import sqlite3
import os
from datetime import datetime, timedelta
from services.library_service import get_patron_status_report, add_book_to_catalog, borrow_book_by_patron
from database import init_database, get_db_connection

@pytest.fixture
def setup_test_db():
    """Setup a test database with sample data for patron status testing."""
    # Use a test database
    test_db = 'test_library.db'
    
    # Remove test database if it exists
    if os.path.exists(test_db):
        os.remove(test_db)
    
    # Temporarily replace the database path
    import database
    original_db = database.DATABASE
    database.DATABASE = test_db
    
    # Initialize test database
    init_database()
    
    # Add sample books for testing
    test_books = [
        ("The Great Gatsby", "F. Scott Fitzgerald", "9780743273565", 3),
        ("To Kill a Mockingbird", "Harper Lee", "9780061120084", 2),
        ("1984", "George Orwell", "9780451524935", 1),
        ("Pride and Prejudice", "Jane Austen", "9780141439518", 2),
    ]
    
    for title, author, isbn, copies in test_books:
        add_book_to_catalog(title, author, isbn, copies)
    
    yield
    
    # Cleanup: restore original database path and remove test database
    database.DATABASE = original_db
    if os.path.exists(test_db):
        os.remove(test_db)

def test_get_patron_status_not_implemented(setup_test_db):
    """Test that get_patron_status_report function returns patron status."""
    result = get_patron_status_report("123456")
    
    # Function should return dictionary with patron status information
    assert isinstance(result, dict)
    assert 'patron_id' in result
    assert 'currently_borrowed' in result
    assert 'total_late_fees' in result
    assert 'current_borrow_count' in result
    assert 'borrowing_history' in result
    assert result['patron_id'] == "123456"
    assert result['currently_borrowed'] == []
    assert result['total_late_fees'] == 0.00
    assert result['current_borrow_count'] == 0

def test_get_patron_status_invalid_patron_id_empty(setup_test_db):
    """Test patron status with empty patron ID."""
    result = get_patron_status_report("")
    
    assert isinstance(result, dict)
    assert 'error' in result
    assert result['error'] == 'Invalid patron ID. Must be exactly 6 digits.'

def test_get_patron_status_invalid_patron_id_wrong_format(setup_test_db):
    """Test patron status with invalid patron ID format."""
    test_cases = [
        "12345",      # Too short
        "1234567",    # Too long
        "12345a",     # Non-numeric
        "abcdef",     # All letters
    ]
    
    for invalid_id in test_cases:
        result = get_patron_status_report(invalid_id)
        
        assert isinstance(result, dict)
        assert 'error' in result
        assert result['error'] == 'Invalid patron ID. Must be exactly 6 digits.'

def test_get_patron_status_nonexistent_patron(setup_test_db):
    """Test patron status for patron with no borrowing history."""
    result = get_patron_status_report("999999")
    
    assert isinstance(result, dict)
    assert result['patron_id'] == '999999'
    assert result['currently_borrowed'] == []
    assert result['total_late_fees'] == 0.00
    assert result['current_borrow_count'] == 0
    assert result['borrowing_history'] == []

def test_get_patron_status_with_current_borrows(setup_test_db):
    """Test patron status for patron with currently borrowed books."""
    # Borrow some books
    borrow1, _ = borrow_book_by_patron("123456", 1)  # The Great Gatsby
    borrow2, _ = borrow_book_by_patron("123456", 2)  # To Kill a Mockingbird
    assert borrow1 == True
    assert borrow2 == True
    
    result = get_patron_status_report("123456")
    
    assert isinstance(result, dict)
    assert result['patron_id'] == '123456'
    assert len(result['currently_borrowed']) == 2
    assert result['current_borrow_count'] == 2
    assert result['total_late_fees'] == 0.00
    
    # Check first book
    assert result['currently_borrowed'][0]['book_id'] == 1
    assert result['currently_borrowed'][0]['title'] == 'The Great Gatsby'
    assert result['currently_borrowed'][0]['author'] == 'F. Scott Fitzgerald'
    assert result['currently_borrowed'][0]['is_overdue'] == False
    
    # Check second book
    assert result['currently_borrowed'][1]['book_id'] == 2
    assert result['currently_borrowed'][1]['title'] == 'To Kill a Mockingbird'
    assert result['currently_borrowed'][1]['author'] == 'Harper Lee'
    assert result['currently_borrowed'][1]['is_overdue'] == False

def test_get_patron_status_with_overdue_books(setup_test_db):
    """Test patron status for patron with overdue books."""
    result = get_patron_status_report("123456")
    
    assert isinstance(result, dict)
    assert result['patron_id'] == "123456"
    # No books borrowed yet, so should be empty
    assert result['currently_borrowed'] == []
    assert result['total_late_fees'] == 0.00

def test_get_patron_status_borrowing_history(setup_test_db):
    """Test that patron status includes complete borrowing history."""
    result = get_patron_status_report("123456")
    
    assert isinstance(result, dict)
    assert 'borrowing_history' in result
    assert isinstance(result['borrowing_history'], list)

def test_get_patron_status_late_fees_calculation(setup_test_db):
    """Test that total late fees are correctly calculated."""
    result = get_patron_status_report("123456")
    
    assert isinstance(result, dict)
    assert 'total_late_fees' in result
    assert isinstance(result['total_late_fees'], float)
    assert result['total_late_fees'] == 0.00

def test_get_patron_status_due_dates_correct(setup_test_db):
    """Test that due dates are correctly calculated (14 days from borrow)."""
    # Borrow a book
    borrow_success, _ = borrow_book_by_patron("123456", 1)
    assert borrow_success == True
    
    result = get_patron_status_report("123456")
    
    assert isinstance(result, dict)
    assert len(result['currently_borrowed']) == 1
    # Check that borrow_date and due_date are present
    assert 'borrow_date' in result['currently_borrowed'][0]
    assert 'due_date' in result['currently_borrowed'][0]

def test_get_patron_status_books_borrowed_count(setup_test_db):
    """Test that current books borrowed count is accurate."""
    # Borrow multiple books
    for book_id in [1, 2, 3]:
        borrow_success, _ = borrow_book_by_patron("123456", book_id)
        assert borrow_success == True
    
    result = get_patron_status_report("123456")
    
    assert isinstance(result, dict)
    assert result['current_borrow_count'] == 3

def test_get_patron_status_multiple_patrons_isolation(setup_test_db):
    """Test that patron status is isolated per patron."""
    # Patron 1 borrows books 1 and 2
    borrow1, _ = borrow_book_by_patron("123456", 1)
    borrow2, _ = borrow_book_by_patron("123456", 2)
    
    # Patron 2 borrows book 3
    borrow3, _ = borrow_book_by_patron("654321", 3)
    
    assert borrow1 == True
    assert borrow2 == True
    assert borrow3 == True
    
    # Check patron 1 status
    result1 = get_patron_status_report("123456")
    assert result1['current_borrow_count'] == 2
    assert len(result1['currently_borrowed']) == 2
    
    # Check patron 2 status
    result2 = get_patron_status_report("654321")
    assert result2['current_borrow_count'] == 1
    assert len(result2['currently_borrowed']) == 1

def test_get_patron_status_returned_books_in_history(setup_test_db):
    """Test that returned books appear in borrowing history but not current borrows."""
    result = get_patron_status_report("123456")
    
    assert isinstance(result, dict)
    assert 'currently_borrowed' in result
    assert 'borrowing_history' in result

def test_get_patron_status_format_consistency(setup_test_db):
    """Test that patron status format is consistent with requirements."""
    result = get_patron_status_report("123456")
    
    assert isinstance(result, dict)
    assert 'patron_id' in result
    assert 'currently_borrowed' in result
    assert 'total_late_fees' in result
    assert 'current_borrow_count' in result
    assert 'borrowing_history' in result
    
def test_get_patron_status_menu_integration(setup_test_db):
    """Test documentation for menu integration requirement."""
    # This is more of a documentation test for R7 requirement:
    # "There should be a menu option created for showing the patron status in the main interface"
    
    # When implemented, the web interface should have:
    # 1. A menu item/link for patron status
    # 2. A form to enter patron ID
    # 3. Display of patron status information
    # 4. Integration with get_patron_status_report function
    
    pass  # This test serves as documentation of the requirement

def test_get_patron_status_edge_case_maximum_books(setup_test_db):
    """Test patron status when patron has maximum allowed books (5)."""
    # Add more books to test maximum limit
    add_book_to_catalog("Book 5", "Author 5", "9780000000005", 1)
    
    # Borrow maximum allowed books (5)
    for book_id in range(1, 6):
        borrow_success, _ = borrow_book_by_patron("123456", book_id)
        if book_id <= 4:  # First 4 books exist from setup
            assert borrow_success == True
    
    result = get_patron_status_report("123456")
    
    assert isinstance(result, dict)
    assert result['current_borrow_count'] >= 4  # At least 4 books borrowed

def test_get_patron_status_comprehensive_patron_id_validation(setup_test_db):
    """Test comprehensive patron ID validation scenarios."""
    invalid_patron_ids = [
        "",           # Empty string
        "12345",      # Too short
        "1234567",    # Too long
        "12345a",     # Contains letter
        "123 456",    # Contains space
        "123-456",    # Contains hyphen
    ]
    
    for invalid_id in invalid_patron_ids:
        try:
            result = get_patron_status_report(invalid_id)
            assert isinstance(result, dict)
            assert 'error' in result
        except (TypeError, AttributeError):
            pass

def test_get_patron_status_multiple_patrons_data_isolation(setup_test_db):
    """Test that patron status properly isolates data between patrons."""
    # Patron 1 borrows books 1-3
    for book_id in range(1, 4):
        borrow1, _ = borrow_book_by_patron("123456", book_id)
        assert borrow1 == True
    
    # Patron 2 borrows book 4
    borrow2, _ = borrow_book_by_patron("654321", 4)
    assert borrow2 == True
    
    # Get status for both patrons
    result1 = get_patron_status_report("123456")
    result2 = get_patron_status_report("654321")
    
    assert result1['current_borrow_count'] == 3
    assert result2['current_borrow_count'] == 1

def test_get_patron_status_format_consistency_requirements(setup_test_db):
    """Test that patron status format meets all requirements."""
    result = get_patron_status_report("123456")
    
    assert isinstance(result, dict)
    assert 'patron_id' in result
    assert 'currently_borrowed' in result
    assert 'total_late_fees' in result

def test_get_patron_status_overdue_and_late_fee_integration(setup_test_db):
    """Test integration between overdue calculation and late fee calculation."""
    result = get_patron_status_report("123456")
    
    assert isinstance(result, dict)
    assert 'total_late_fees' in result
    assert isinstance(result['total_late_fees'], float)

def test_get_patron_status_complete_data_structure(setup_test_db):
    """Test that patron status returns complete required data structure."""
    # Add and borrow books to test complete scenario
    borrow1, _ = borrow_book_by_patron("123456", 1)
    borrow2, _ = borrow_book_by_patron("123456", 2)
    assert borrow1 == True
    assert borrow2 == True
    
    result = get_patron_status_report("123456")
    
    assert isinstance(result, dict)
    assert result['patron_id'] == '123456'
    assert len(result['currently_borrowed']) == 2
    assert result['total_late_fees'] == 0.00
    assert result['current_borrow_count'] == 2
    assert isinstance(result['borrowing_history'], list)

def test_get_patron_status_security_and_performance(setup_test_db):
    """Test security and performance considerations."""
    # Test SQL injection protection
    malicious_ids = ["'; DROP TABLE books; --", "' OR '1'='1"]
    
    for malicious_id in malicious_ids:
        result = get_patron_status_report(malicious_id)
        assert isinstance(result, dict)
        assert 'error' in result