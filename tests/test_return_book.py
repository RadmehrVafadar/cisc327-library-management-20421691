"""
Unit tests for return_book_by_patron function
Tests R4: Book Return Processing functionality
"""

import pytest
import sqlite3
import os
from datetime import datetime, timedelta
from services.library_service import return_book_by_patron, add_book_to_catalog, borrow_book_by_patron
from database import init_database, get_db_connection

@pytest.fixture
def setup_test_db():
    """Setup a test database for each test."""
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
    
    yield
    
    # Cleanup: restore original database path and remove test database
    database.DATABASE = original_db
    if os.path.exists(test_db):
        os.remove(test_db)

def test_return_book_not_implemented(setup_test_db):
    """Test that return_book_by_patron function works correctly."""
    # Add and borrow a book first
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 3)
    borrow_success, _ = borrow_book_by_patron("123456", 1)
    assert borrow_success == True
    
    # Try to return the book
    success, message = return_book_by_patron("123456", 1)
    
    # Function should return True with success message
    assert success == True
    assert "successfully returned" in message.lower()

def test_return_book_invalid_patron_id_empty(setup_test_db):
    """Test return with empty patron ID - should fail when implemented."""
    # This test documents expected behavior when function is implemented
    success, message = return_book_by_patron("", 1)
    
    assert success == False
    assert "invalid patron id" in message.lower()

def test_return_book_invalid_patron_id_wrong_length(setup_test_db):
    """Test return with invalid patron ID length - should fail when implemented."""
    success, message = return_book_by_patron("12345", 1)
    
    assert success == False
    assert "invalid patron id" in message.lower()

def test_return_book_nonexistent_book(setup_test_db):
    """Test returning a book that doesn't exist - should fail when implemented."""
    success, message = return_book_by_patron("123456", 999)
    
    assert success == False
    assert "book not found" in message.lower()

def test_return_book_not_borrowed_by_patron(setup_test_db):
    """Test returning a book not borrowed by the patron - should fail when implemented."""
    # Add a book but don't borrow it
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 3)
    
    success, message = return_book_by_patron("123456", 1)
    
    assert success == False
    assert "not currently borrowed" in message.lower()

def test_return_book_already_returned(setup_test_db):
    """Test returning a book that was already returned - should fail when implemented."""
    # This test documents expected behavior for double returns
    success, message = return_book_by_patron("123456", 1)
    
    assert success == False
    assert "not currently borrowed" in message.lower() or "book not found" in message.lower()

def test_return_book_valid_scenario_no_late_fee(setup_test_db):
    """Test returning a book on time - should succeed when implemented."""
    # Add and borrow a book
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 3)
    borrow_success, _ = borrow_book_by_patron("123456", 1)
    assert borrow_success == True
    
    success, message = return_book_by_patron("123456", 1)
    
    # Should return True for success
    assert success == True
    assert "successfully returned" in message.lower()
    # Should have no late fee
    assert "no late fee" in message.lower() or "$0.00" in message

def test_return_book_valid_scenario_with_late_fee(setup_test_db):
    """Test returning an overdue book - should calculate late fee when implemented."""
    success, message = return_book_by_patron("123456", 1)
    
    # Book not borrowed, should fail
    assert success == False
    assert "not currently borrowed" in message.lower() or "book not found" in message.lower()

def test_return_book_updates_available_copies(setup_test_db):
    """Test that returning increases available copies."""
    # Add a book with 3 copies and borrow one
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 3)
    borrow_success, _ = borrow_book_by_patron("123456", 1)
    assert borrow_success == True
    
    # Check available copies before return (should be 2)
    import database
    conn = database.get_db_connection()
    book_before = conn.execute('SELECT available_copies FROM books WHERE id = 1').fetchone()
    conn.close()
    assert book_before['available_copies'] == 2
    
    # Return the book
    success, message = return_book_by_patron("123456", 1)
    assert success == True
    
    # Available copies should increase back to 3
    conn = database.get_db_connection()
    book_after = conn.execute('SELECT available_copies FROM books WHERE id = 1').fetchone()
    conn.close()
    assert book_after['available_copies'] == 3

def test_return_book_sets_return_date(setup_test_db):
    """Test that returning sets return_date in borrow record."""
    # Add and borrow a book
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 3)
    borrow_success, _ = borrow_book_by_patron("123456", 1)
    assert borrow_success == True
    
    # Check that return_date is NULL before return
    import database
    conn = database.get_db_connection()
    record_before = conn.execute('''
        SELECT return_date FROM borrow_records 
        WHERE patron_id = ? AND book_id = ?
    ''', ("123456", 1)).fetchone()
    conn.close()
    assert record_before['return_date'] is None
    
    # Return the book
    success, message = return_book_by_patron("123456", 1)
    assert success == True
    
    # return_date should be set to current datetime
    conn = database.get_db_connection()
    record_after = conn.execute('''
        SELECT return_date FROM borrow_records 
        WHERE patron_id = ? AND book_id = ?
    ''', ("123456", 1)).fetchone()
    conn.close()
    assert record_after['return_date'] is not None

def test_return_book_multiple_patrons_same_book(setup_test_db):
    """Test that each patron can return their own copy."""
    # Add a book with multiple copies
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 3)
    
    # Two patrons borrow the same book
    borrow1, _ = borrow_book_by_patron("123456", 1)
    borrow2, _ = borrow_book_by_patron("654321", 1)
    assert borrow1 == True
    assert borrow2 == True
    
    # First patron returns their copy
    success1, message1 = return_book_by_patron("123456", 1)
    
    # Should succeed
    assert success1 == True
    assert "successfully returned" in message1.lower()

def test_return_book_invalid_patron_id_formats(setup_test_db):
    """Test return with various invalid patron ID formats."""
    invalid_ids = ["", "12345", "abcdef", "123-45"]
    
    for invalid_id in invalid_ids:
        success, message = return_book_by_patron(invalid_id, 1)
        assert success == False
        assert "invalid patron id" in message.lower()

def test_return_book_wrong_patron_for_borrowed_book(setup_test_db):
    """Test returning a book borrowed by different patron."""
    # Add a book and patron A borrows it
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 3)
    borrow_success, _ = borrow_book_by_patron("123456", 1)
    assert borrow_success == True
    
    # Patron B tries to return it
    success, message = return_book_by_patron("654321", 1)
    
    assert success == False
    assert "not currently borrowed" in message.lower()

def test_return_book_success_message_format(setup_test_db):
    """Test that successful return has properly formatted message."""
    # Add and borrow a book
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 3)
    borrow_success, _ = borrow_book_by_patron("123456", 1)
    assert borrow_success == True
    
    success, message = return_book_by_patron("123456", 1)
    
    # Should succeed with proper message format
    assert success == True
    assert "successfully returned" in message.lower()
    assert "test book" in message.lower()

def test_return_book_late_fee_calculation_integration(setup_test_db):
    """Test that return integrates with late fee calculation."""
    success, message = return_book_by_patron("123456", 1)
    
    # Book not borrowed, should fail
    assert success == False
    assert "not currently borrowed" in message.lower() or "book not found" in message.lower()

def test_return_book_database_updates_integration(setup_test_db):
    """Test that return properly updates database state."""
    # Add book with 1 copy and borrow it
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 1)
    borrow_success, _ = borrow_book_by_patron("123456", 1)
    assert borrow_success == True
    
    success, message = return_book_by_patron("123456", 1)
    
    # Should succeed
    assert success == True
    
    # Check that available_copies increased from 0 to 1
    import database
    conn = database.get_db_connection()
    book = conn.execute('SELECT available_copies FROM books WHERE id = 1').fetchone()
    conn.close()
    assert book['available_copies'] == 1