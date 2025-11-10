"""
Unit tests for add_book_to_catalog function
Tests R1: Add Book To Catalog functionality
"""

import pytest
import sqlite3
import os
from services.library_service import add_book_to_catalog
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

def test_add_book_valid_input(setup_test_db):
    """Test adding a book with valid input."""
    success, message = add_book_to_catalog("Test Book", "Test Author", "1234567890123", 5)
    
    assert success == True
    assert "successfully added" in message.lower()
    assert "Test Book" in message

def test_add_book_empty_title(setup_test_db):
    """Test adding a book with empty title."""
    success, message = add_book_to_catalog("", "Test Author", "1234567890123", 5)
    
    assert success == False
    assert "title is required" in message.lower()

def test_add_book_whitespace_title(setup_test_db):
    """Test adding a book with whitespace-only title."""
    success, message = add_book_to_catalog("   ", "Test Author", "1234567890123", 5)
    
    assert success == False
    assert "title is required" in message.lower()

def test_add_book_title_too_long(setup_test_db):
    """Test adding a book with title exceeding 200 characters."""
    long_title = "A" * 201  # 201 characters
    success, message = add_book_to_catalog(long_title, "Test Author", "1234567890123", 5)
    
    assert success == False
    assert "200 characters" in message

def test_add_book_empty_author(setup_test_db):
    """Test adding a book with empty author."""
    success, message = add_book_to_catalog("Test Book", "", "1234567890123", 5)
    
    assert success == False
    assert "author is required" in message.lower()

def test_add_book_whitespace_author(setup_test_db):
    """Test adding a book with whitespace-only author."""
    success, message = add_book_to_catalog("Test Book", "   ", "1234567890123", 5)
    
    assert success == False
    assert "author is required" in message.lower()

def test_add_book_author_too_long(setup_test_db):
    """Test adding a book with author exceeding 100 characters."""
    long_author = "A" * 101  # 101 characters
    success, message = add_book_to_catalog("Test Book", long_author, "1234567890123", 5)
    
    assert success == False
    assert "100 characters" in message

def test_add_book_isbn_too_short(setup_test_db):
    """Test adding a book with ISBN too short."""
    success, message = add_book_to_catalog("Test Book", "Test Author", "123456789", 5)
    
    assert success == False
    assert "13 digits" in message

def test_add_book_isbn_too_long(setup_test_db):
    """Test adding a book with ISBN too long."""
    success, message = add_book_to_catalog("Test Book", "Test Author", "12345678901234", 5)
    
    assert success == False
    assert "13 digits" in message

def test_add_book_negative_copies(setup_test_db):
    """Test adding a book with negative total copies."""
    success, message = add_book_to_catalog("Test Book", "Test Author", "1234567890123", -1)
    
    assert success == False
    assert "positive integer" in message

def test_add_book_zero_copies(setup_test_db):
    """Test adding a book with zero total copies."""
    success, message = add_book_to_catalog("Test Book", "Test Author", "1234567890123", 0)
    
    assert success == False
    assert "positive integer" in message

def test_add_book_duplicate_isbn(setup_test_db):
    """Test adding a book with duplicate ISBN."""
    # First add a book
    success1, message1 = add_book_to_catalog("First Book", "First Author", "1234567890123", 3)
    assert success1 == True
    
    # Try to add another book with the same ISBN
    success2, message2 = add_book_to_catalog("Second Book", "Second Author", "1234567890123", 2)
    
    assert success2 == False
    assert "already exists" in message2.lower()

def test_add_book_title_author_trimming(setup_test_db):
    """Test that title and author are properly trimmed of whitespace."""
    success, message = add_book_to_catalog("  Test Book  ", "  Test Author  ", "1234567890123", 5)
    
    assert success == True
    
    # Verify the book was added with trimmed values by checking the database
    import database
    conn = database.get_db_connection()
    book = conn.execute('SELECT * FROM books WHERE isbn = ?', ("1234567890123",)).fetchone()
    conn.close()
    
    assert book is not None
    assert book['title'] == "Test Book"
    assert book['author'] == "Test Author"

def test_add_book_boundary_title_length(setup_test_db):
    """Test adding a book with title exactly 200 characters."""
    title_200_chars = "A" * 200  # Exactly 200 characters
    success, message = add_book_to_catalog(title_200_chars, "Test Author", "1234567890123", 5)
    
    assert success == True
    assert "successfully added" in message.lower()

def test_add_book_boundary_author_length(setup_test_db):
    """Test adding a book with author exactly 100 characters."""
    author_100_chars = "A" * 100  # Exactly 100 characters
    success, message = add_book_to_catalog("Test Book", author_100_chars, "1234567890123", 5)
    
    assert success == True
    assert "successfully added" in message.lower()
