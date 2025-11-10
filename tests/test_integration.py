"""
Integration tests for library system
Tests that multiple functions work together correctly
"""

import pytest
import os
from datetime import datetime, timedelta
from services.library_service import (
    add_book_to_catalog, borrow_book_by_patron, 
    return_book_by_patron, search_books_in_catalog,
    get_patron_status_report
)
from database import init_database, get_db_connection

@pytest.fixture
def setup_test_db():
    """Setup test database"""
    test_db = 'test_library.db'
    
    if os.path.exists(test_db):
        os.remove(test_db)
    
    import database
    original_db = database.DATABASE
    database.DATABASE = test_db
    
    init_database()
    
    yield
    
    database.DATABASE = original_db
    if os.path.exists(test_db):
        os.remove(test_db)

def test_complete_borrow_return_cycle(setup_test_db):
    """Test complete cycle: add book, borrow, return"""
    # Add book
    success, msg = add_book_to_catalog("Python Basics", "John Doe", "9781234567890", 2)
    assert success == True
    
    # Borrow book
    success, msg = borrow_book_by_patron("123456", 1)
    assert success == True
    assert "Python Basics" in msg
    
    # Check available copies decreased
    import database
    conn = database.get_db_connection()
    book = conn.execute('SELECT available_copies FROM books WHERE id = 1').fetchone()
    conn.close()
    assert book['available_copies'] == 1
    
    # Return book
    success, msg = return_book_by_patron("123456", 1)
    assert success == True
    assert "Python Basics" in msg
    
    # Check available copies increased
    conn = database.get_db_connection()
    book = conn.execute('SELECT available_copies FROM books WHERE id = 1').fetchone()
    conn.close()
    assert book['available_copies'] == 2

def test_search_and_borrow(setup_test_db):
    """Test searching for a book and then borrowing it"""
    # Add multiple books
    add_book_to_catalog("Python Programming", "Alice Smith", "9781111111111", 3)
    add_book_to_catalog("Java Programming", "Bob Jones", "9782222222222", 2)
    add_book_to_catalog("Python Advanced", "Charlie Brown", "9783333333333", 1)
    
    # Search for Python books
    results = search_books_in_catalog("Python", "title")
    assert len(results) == 2
    
    # Borrow first Python book found
    book_id = results[0]['id']
    success, msg = borrow_book_by_patron("555555", book_id)
    assert success == True

def test_patron_status_with_multiple_books(setup_test_db):
    """Test patron status report with multiple borrowed books"""
    # Add books
    add_book_to_catalog("Book One", "Author A", "9781111111111", 3)
    add_book_to_catalog("Book Two", "Author B", "9782222222222", 2)
    
    # Patron borrows two books
    borrow_book_by_patron("888888", 1)
    borrow_book_by_patron("888888", 2)
    
    # Get patron status
    status = get_patron_status_report("888888")
    
    assert status['current_borrow_count'] == 2
    assert len(status['currently_borrowed']) == 2
    assert status['total_late_fees'] == 0.0

def test_borrowing_limit_enforcement(setup_test_db):
    """Test that borrowing limit is enforced at 5 books"""
    # Add 6 books
    for i in range(6):
        isbn = f"978{i:010d}"
        add_book_to_catalog(f"Book {i+1}", "Test Author", isbn, 1)
    
    # Borrow 5 books successfully
    for i in range(1, 6):
        success, msg = borrow_book_by_patron("999999", i)
        assert success == True
    
    # 6th borrow should fail
    success, msg = borrow_book_by_patron("999999", 6)
    assert success == False
    assert "maximum" in msg.lower() or "limit" in msg.lower()

def test_search_case_insensitive(setup_test_db):
    """Test that search is case insensitive"""
    add_book_to_catalog("The Great Gatsby", "F. Scott Fitzgerald", "9780743273565", 2)
    
    # Search with different cases
    results1 = search_books_in_catalog("gatsby", "title")
    results2 = search_books_in_catalog("GATSBY", "title")
    results3 = search_books_in_catalog("GaTsBY", "title")
    
    assert len(results1) == 1
    assert len(results2) == 1
    assert len(results3) == 1

