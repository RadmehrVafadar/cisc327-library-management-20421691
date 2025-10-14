"""
Library Service Module - Business Logic Functions
Contains all the core business logic for the Library Management System
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import (
    get_book_by_id, get_book_by_isbn, get_patron_borrow_count,
    insert_book, insert_borrow_record, update_book_availability,
    update_borrow_record_return_date, get_all_books, get_borrow_record,
    search_books, get_patron_borrowed_books, get_patron_borrowing_history
)

def add_book_to_catalog(title: str, author: str, isbn: str, total_copies: int) -> Tuple[bool, str]:
    """Add a new book to the catalog (R1)"""
    
    if not title or not title.strip():
        return False, "Title is required."
    
    if len(title.strip()) > 200:
        return False, "Title must be less than 200 characters."
    
    if not author or not author.strip():
        return False, "Author is required."
    
    if len(author.strip()) > 100:
        return False, "Author must be less than 100 characters."
    
    if len(isbn) != 13:
        return False, "ISBN must be exactly 13 digits."
    
    if not isinstance(total_copies, int) or total_copies <= 0:
        return False, "Total copies must be a positive integer."
    
    existing = get_book_by_isbn(isbn)
    if existing:
        return False, "A book with this ISBN already exists."
    
    success = insert_book(title.strip(), author.strip(), isbn, total_copies, total_copies)
    if success:
        return True, f'Book "{title.strip()}" has been successfully added to the catalog.'
    else:
        return False, "Database error occurred while adding the book."

def borrow_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """Process book borrowing (R3)"""
    
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."
    
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."
    
    if book['available_copies'] <= 0:
        return False, "This book is currently not available."
    
    current_borrowed = get_patron_borrow_count(patron_id)
    if current_borrowed >= 5:
        return False, "You have reached the maximum borrowing limit of 5 books."
    
    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=14)
    
    borrow_success = insert_borrow_record(patron_id, book_id, borrow_date, due_date)
    if not borrow_success:
        return False, "Database error occurred while creating borrow record."
    
    availability_success = update_book_availability(book_id, -1)
    if not availability_success:
        return False, "Database error occurred while updating book availability."
    
    return True, f'Successfully borrowed "{book["title"]}". Due date: {due_date.strftime("%Y-%m-%d")}.'

def return_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """Handle book returns and calculate late fees (R4)"""
    
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."
    
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."
    
    borrow_record = get_borrow_record(patron_id, book_id)
    if not borrow_record:
        return False, "This book is not currently borrowed by you or has already been returned."
    
    return_date = datetime.now()
    due_date = datetime.fromisoformat(borrow_record['due_date'])
    late_fee = 0.0
    
    if return_date > due_date:
        days_overdue = (return_date - due_date).days
        if days_overdue <= 7:
            late_fee = days_overdue * 0.50
        else:
            late_fee = (7 * 0.50) + ((days_overdue - 7) * 1.00)
        late_fee = min(late_fee, 15.00)
    
    return_success = update_borrow_record_return_date(patron_id, book_id, return_date)
    if not return_success:
        return False, "Database error occurred while updating return record."
    
    availability_success = update_book_availability(book_id, 1)
    if not availability_success:
        return False, "Database error occurred while updating book availability."
    
    if late_fee > 0:
        return True, f'Successfully returned "{book["title"]}". Late fee: ${late_fee:.2f}.'
    else:
        return True, f'Successfully returned "{book["title"]}". No late fee.'

def calculate_late_fee_for_book(patron_id: str, book_id: int) -> Dict:
    """Calculate late fee for API endpoint (R5)"""
    
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return {
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'Invalid patron ID. Must be exactly 6 digits.'
        }
    
    book = get_book_by_id(book_id)
    if not book:
        return {
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'Book not found.'
        }
    
    borrow_record = get_borrow_record(patron_id, book_id)
    if not borrow_record:
        return {
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'This book is not currently borrowed by you.'
        }
    
    current_date = datetime.now()
    due_date = datetime.fromisoformat(borrow_record['due_date'])
    
    if current_date <= due_date:
        return {
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'Book is not overdue.'
        }
    
    days_overdue = (current_date - due_date).days
    
    if days_overdue <= 7:
        late_fee = days_overdue * 0.50
    else:
        late_fee = (7 * 0.50) + ((days_overdue - 7) * 1.00)
    late_fee = min(late_fee, 15.00)
    
    return {
        'fee_amount': round(late_fee, 2),
        'days_overdue': days_overdue,
        'status': f'Late fee calculated for "{book["title"]}".'
    }

def search_books_in_catalog(search_term: str, search_type: str) -> List[Dict]:
    """Search catalog by title, author, or ISBN (R6)"""
    
    if not search_term or not search_term.strip():
        return []
    
    if search_type not in ['title', 'author', 'isbn']:
        return []
    
    return search_books(search_term.strip(), search_type)

def get_patron_status_report(patron_id: str) -> Dict:
    """Get complete status report for a patron (R7)"""
    
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return {
            'error': 'Invalid patron ID. Must be exactly 6 digits.',
            'currently_borrowed': [],
            'total_late_fees': 0.00,
            'current_borrow_count': 0,
            'borrowing_history': []
        }
    
    currently_borrowed = get_patron_borrowed_books(patron_id)
    total_late_fees = 0.0
    current_date = datetime.now()
    
    for book in currently_borrowed:
        if book['is_overdue']:
            days_overdue = (current_date - book['due_date']).days
            if days_overdue <= 7:
                fee = days_overdue * 0.50
            else:
                fee = (7 * 0.50) + ((days_overdue - 7) * 1.00)
            fee = min(fee, 15.00)
            total_late_fees += fee
    
    borrowing_history = get_patron_borrowing_history(patron_id)
    
    formatted_borrowed = []
    for book in currently_borrowed:
        formatted_borrowed.append({
            'book_id': book['book_id'],
            'title': book['title'],
            'author': book['author'],
            'borrow_date': book['borrow_date'].strftime('%Y-%m-%d'),
            'due_date': book['due_date'].strftime('%Y-%m-%d'),
            'is_overdue': book['is_overdue'],
            'days_overdue': (current_date - book['due_date']).days if book['is_overdue'] else 0
        })
    
    formatted_history = []
    for record in borrowing_history:
        formatted_history.append({
            'book_id': record['book_id'],
            'title': record['title'],
            'author': record['author'],
            'borrow_date': record['borrow_date'].strftime('%Y-%m-%d'),
            'due_date': record['due_date'].strftime('%Y-%m-%d'),
            'return_date': record['return_date'].strftime('%Y-%m-%d') if record['return_date'] else None,
            'is_returned': record['is_returned']
        })
    
    return {
        'patron_id': patron_id,
        'currently_borrowed': formatted_borrowed,
        'total_late_fees': round(total_late_fees, 2),
        'current_borrow_count': len(currently_borrowed),
        'borrowing_history': formatted_history
    }
