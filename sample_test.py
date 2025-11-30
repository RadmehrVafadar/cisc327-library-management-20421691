import pytest
import os
from library_service import (
    add_book_to_catalog
)
from database import init_database

@pytest.fixture
def setup_test_db():
    """Setup a test database for each test."""
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

def test_add_book_valid_input(setup_test_db):
    """Test adding a book with valid input."""
    success, message = add_book_to_catalog("Test Book", "Test Author", "1234567890123", 5)
    
    assert success == True
    assert "successfully added" in message.lower()

def test_add_book_invalid_isbn_too_short(setup_test_db):
    """Test adding a book with ISBN too short."""
    success, message = add_book_to_catalog("Test Book", "Test Author", "123456789", 5)
    
    assert success == False
    assert "13 digits" in message



# Add more test methods for each function and edge case. You can keep all your test in a separate folder named `tests`.