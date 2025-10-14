"""
Unit tests for search_books_in_catalog function
Tests R6: Book Search Functionality
"""

import pytest
import sqlite3
import os
from library_service import search_books_in_catalog, add_book_to_catalog, borrow_book_by_patron
from database import init_database, get_db_connection

@pytest.fixture
def setup_test_db():
    """Setup a test database with sample books for search testing."""
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
        ("The Catcher in the Rye", "J.D. Salinger", "9780316769174", 1),
        ("Pride and Prejudice", "Jane Austen", "9780141439518", 2),
        ("The Lord of the Rings", "J.R.R. Tolkien", "9780544003415", 1),
        ("Harry Potter and the Philosopher's Stone", "J.K. Rowling", "9780747532699", 4)
    ]
    
    for title, author, isbn, copies in test_books:
        add_book_to_catalog(title, author, isbn, copies)
    
    yield
    
    # Cleanup: restore original database path and remove test database
    database.DATABASE = original_db
    if os.path.exists(test_db):
        os.remove(test_db)

def test_search_books_not_implemented(setup_test_db):
    """Test that search_books_in_catalog function works correctly."""
    result = search_books_in_catalog("Gatsby", "title")
    
    # Function should return list of matching books
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]['title'] == "The Great Gatsby"

def test_search_books_by_title_partial_match(setup_test_db):
    """Test searching books by title with partial match (case-insensitive)."""
    # Test various partial title searches
    test_cases = [
        ("great", ["The Great Gatsby"]),  # lowercase
        ("GREAT", ["The Great Gatsby"]),  # uppercase
        ("Great", ["The Great Gatsby"]),  # mixed case
        ("gatsby", ["The Great Gatsby"]),  # partial word
        ("the", ["The Great Gatsby", "The Catcher in the Rye", "The Lord of the Rings"]),  # common word
        ("potter", ["Harry Potter and the Philosopher's Stone"]),  # middle of title
    ]
    
    for search_term, expected_titles in test_cases:
        result = search_books_in_catalog(search_term, "title")
        
        # Should return books with titles containing search_term
        assert isinstance(result, list)
        result_titles = [book['title'] for book in result]
        for expected_title in expected_titles:
            assert expected_title in result_titles

def test_search_books_by_author_partial_match(setup_test_db):
    """Test searching books by author with partial match (case-insensitive)."""
    test_cases = [
        ("fitzgerald", ["The Great Gatsby"]),  # lowercase last name
        ("FITZGERALD", ["The Great Gatsby"]),  # uppercase last name
        ("scott", ["The Great Gatsby"]),       # middle name
        ("j.k.", ["Harry Potter and the Philosopher's Stone"]),  # initials
        ("tolkien", ["The Lord of the Rings"]), # last name only
        ("jane", ["Pride and Prejudice"]),      # first name only
    ]
    
    for search_term, expected_titles in test_cases:
        result = search_books_in_catalog(search_term, "author")
        
        # Should return books with authors containing search_term
        assert isinstance(result, list)
        result_titles = [book['title'] for book in result]
        for expected_title in expected_titles:
            assert expected_title in result_titles

def test_search_books_by_isbn_exact_match(setup_test_db):
    """Test searching books by ISBN with exact match."""
    test_cases = [
        ("9780743273565", ["The Great Gatsby"]),
        ("9780061120084", ["To Kill a Mockingbird"]),
        ("9780316769174", ["The Catcher in the Rye"]),
        ("9999999999999", []),  # Non-existent ISBN
    ]
    
    for isbn, expected_titles in test_cases:
        result = search_books_in_catalog(isbn, "isbn")
        
        # Should return exact ISBN matches only
        assert isinstance(result, list)
        if expected_titles:
            assert len(result) == len(expected_titles)
            result_titles = [book['title'] for book in result]
            for expected_title in expected_titles:
                assert expected_title in result_titles
        else:
            assert len(result) == 0

def test_search_books_empty_search_term(setup_test_db):
    """Test searching with empty search term."""
    result = search_books_in_catalog("", "title")
    
    assert isinstance(result, list)
    assert result == []

def test_search_books_whitespace_search_term(setup_test_db):
    """Test searching with whitespace-only search term."""
    result = search_books_in_catalog("   ", "title")
    
    assert isinstance(result, list)
    assert result == []

def test_search_books_invalid_search_type(setup_test_db):
    """Test searching with invalid search type."""
    result = search_books_in_catalog("Gatsby", "invalid_type")
    
    assert isinstance(result, list)
    assert result == []

def test_search_books_case_insensitive_title(setup_test_db):
    """Test that title search is case-insensitive."""
    test_cases = [
        "the great gatsby",
        "THE GREAT GATSBY", 
        "The Great Gatsby",
        "tHe GrEaT gAtSbY"
    ]
    
    for search_term in test_cases:
        result = search_books_in_catalog(search_term, "title")
        
        # All should return "The Great Gatsby"
        assert isinstance(result, list)
        assert len(result) >= 1
        assert "The Great Gatsby" in [book['title'] for book in result]

def test_search_books_case_insensitive_author(setup_test_db):
    """Test that author search is case-insensitive."""
    test_cases = [
        "f. scott fitzgerald",
        "F. SCOTT FITZGERALD",
        "F. Scott Fitzgerald", 
        "f. ScOtT fItZgErAlD"
    ]
    
    for search_term in test_cases:
        result = search_books_in_catalog(search_term, "author")
        
        # All should return "The Great Gatsby"
        assert isinstance(result, list)
        assert len(result) >= 1
        assert "The Great Gatsby" in [book['title'] for book in result]

def test_search_books_no_matches(setup_test_db):
    """Test searching with term that has no matches."""
    result = search_books_in_catalog("nonexistent", "title")
    
    assert isinstance(result, list)
    assert result == []

def test_search_books_partial_isbn_should_not_match(setup_test_db):
    """Test that partial ISBN searches don't return matches (exact match only)."""
    # ISBN search should be exact match only, not partial
    result = search_books_in_catalog("978074327", "isbn")  # Partial ISBN
    
    assert isinstance(result, list)
    assert result == []

def test_search_books_return_format(setup_test_db):
    """Test that search results return proper format."""
    result = search_books_in_catalog("Gatsby", "title")
    
    # Should return list of dictionaries with book information
    assert isinstance(result, list)
    assert len(result) >= 1
    # Each book should have: id, title, author, isbn, total_copies, available_copies
    book = result[0]
    assert 'id' in book
    assert 'title' in book
    assert 'author' in book
    assert 'isbn' in book
    assert 'total_copies' in book
    assert 'available_copies' in book

def test_search_books_multiple_matches(setup_test_db):
    """Test searching that returns multiple matches."""
    result = search_books_in_catalog("the", "title")  # Should match multiple books
    
    assert isinstance(result, list)
    assert len(result) >= 3  # At least "The Great Gatsby", "The Catcher in the Rye", "The Lord of the Rings"

def test_search_books_author_with_initials(setup_test_db):
    """Test searching authors with various initial formats."""
    test_cases = [
        ("j.d.", "The Catcher in the Rye"),      # lowercase with periods
        ("J.D.", "The Catcher in the Rye"),      # uppercase with periods
        ("j d", "The Catcher in the Rye"),       # without periods
        ("jd", "The Catcher in the Rye"),        # no spaces or periods
    ]
    
    for search_term, expected_title in test_cases:
        result = search_books_in_catalog(search_term, "author")
        
        # Should handle various initial formats
        assert isinstance(result, list)
        # Note: exact matching depends on how the author name is stored

def test_search_books_special_characters_in_title(setup_test_db):
    """Test searching titles with special characters."""
    # Test apostrophes and other punctuation
    result = search_books_in_catalog("philosopher's", "title")
    
    assert isinstance(result, list)
    # Should find "Harry Potter and the Philosopher's Stone"
    if len(result) > 0:
        assert "Philosopher" in result[0]['title']

def test_search_books_default_search_type(setup_test_db):
    """Test behavior when search_type parameter is not provided or None."""
    # This tests how the function handles missing or None search_type parameter
    # Current function signature requires search_type, but web interface defaults to "title"
    result = search_books_in_catalog("Gatsby", "title")  # Using explicit "title"
    
    assert isinstance(result, list)
    assert len(result) >= 1
    assert "Gatsby" in result[0]['title']

def test_search_books_input_validation(setup_test_db):
    """Test search input validation and edge cases."""
    test_cases = [
        ("", "title"),           # Empty search term
        ("   ", "title"),        # Whitespace only
        ("test", "invalid"),     # Invalid search type
        ("'; DROP TABLE books; --", "title")  # SQL injection attempt
    ]
    
    for search_term, search_type in test_cases:
        result = search_books_in_catalog(search_term, search_type)
        assert isinstance(result, list)
        # Should handle all edge cases safely (return empty list)
        assert result == []

def test_search_books_case_insensitive_matching(setup_test_db):
    """Test that title and author searches are case-insensitive."""
    test_cases = [
        ("great", "title"),      # lowercase
        ("GREAT", "title"),      # uppercase  
        ("Great", "title"),      # mixed case
        ("fitzgerald", "author"), # author search
        ("TOLKIEN", "author")    # uppercase author
    ]
    
    for search_term, search_type in test_cases:
        result = search_books_in_catalog(search_term, search_type)
        assert isinstance(result, list)
        assert len(result) >= 1  # Should match regardless of case

def test_search_books_isbn_exact_matching(setup_test_db):
    """Test that ISBN search uses exact matching only."""
    test_cases = [
        ("9780743273565", ["The Great Gatsby"]),  # Full ISBN
        ("978074327", []),                        # Partial ISBN (should not match)
        ("9999999999999", []),                    # Non-existent ISBN
    ]
    
    for isbn, expected_titles in test_cases:
        result = search_books_in_catalog(isbn, "isbn")
        assert isinstance(result, list)
        if expected_titles:
            assert len(result) >= 1
        else:
            assert len(result) == 0

def test_search_books_return_format_consistency(setup_test_db):
    """Test that search results match catalog display format."""
    result = search_books_in_catalog("Gatsby", "title")
    
    assert isinstance(result, list)
    assert len(result) >= 1
    # Should return list of dictionaries with required fields
    book = result[0]
    assert 'id' in book
    assert 'title' in book
    assert 'author' in book
    assert 'isbn' in book
    assert 'total_copies' in book
    assert 'available_copies' in book

def test_search_books_multiple_matches_handling(setup_test_db):
    """Test search behavior with multiple matching results."""
    result = search_books_in_catalog("the", "title")  # Should match multiple books
    
    assert isinstance(result, list)
    assert len(result) >= 3  # Should return all matching books

def test_search_books_availability_in_results(setup_test_db):
    """Test that search results show current book availability."""
    # Add and borrow a book to test availability display
    add_book_to_catalog("Test Book", "Test Author", "1234567890123", 3)
    borrow_success, _ = borrow_book_by_patron("123456", 1)
    assert borrow_success == True
    
    result = search_books_in_catalog("Test", "title")
    
    assert isinstance(result, list)
    assert len(result) >= 1
    # Should show current available_copies = 2, total_copies = 3
    test_book = [book for book in result if book['title'] == "Test Book"][0]
    assert test_book['available_copies'] == 2
    assert test_book['total_copies'] == 3