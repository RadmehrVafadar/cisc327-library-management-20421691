# Assignment 1 - Library Management System Implementation Status

**Student Name:** Radmehr Vafadarfalavarjani 
**Student ID:** 20421691
**Group Number/Name:** Group 4 (TA-Fozle Shafi)
## 2. Project Implementation Status

| Function Name | Implementation Status | What is Missing (if any) |
|---------------|----------------------|---------------------------|
| `add_book_to_catalog` | Complete | None - fully implements R1 with proper validation for title (max 200 chars), author (max 100 chars), ISBN (exactly 13 digits), total copies (positive integer), and duplicate ISBN checking |
| `borrow_book_by_patron` | Partial | Has a bug in patron borrowing limit check - uses `>` instead of `>=`, allowing 6 books instead of maximum 5. Otherwise implements R3 correctly with patron ID validation (6 digits), book availability check, and borrowing record creation |
| `return_book_by_patron` | Not Implemented | Complete implementation missing for R4. Function returns hardcoded error message. Needs: patron validation, book return verification, available copies update, return date recording, and late fee calculation |
| `calculate_late_fee_for_book` | Not Implemented | Complete implementation missing for R5. Function is empty with commented placeholder. Needs: overdue calculation (14 days due period), fee structure ($0.50/day first 7 days, $1.00/day after, max $15.00), and JSON response format |
| `search_books_in_catalog` | Not Implemented | Complete implementation missing for R6. Function returns empty list. Needs: search term validation, search type handling (title/author/isbn), partial matching for title/author (case-insensitive), exact matching for ISBN |
| `get_patron_status_report` | Not Implemented | Complete implementation missing for R7. Function returns empty dictionary. Needs: currently borrowed books with due dates, total late fees calculation, current borrow count, borrowing history display |
| **Web Routes** | **Status** | **Notes** |
| Catalog display (R2) | Complete | Properly displays all books with ID, title, author, ISBN, available/total copies, and borrow buttons |
| Add book form | Complete | Web interface properly calls business logic function |
| Borrow book form | Complete | Web interface properly calls business logic function |
| Return book form | Partial | Form exists but underlying business logic not implemented |
| Search interface | Partial | Form exists but underlying business logic not implemented |
| API late fee endpoint | Partial | Endpoint exists but underlying business logic not implemented |
| API search endpoint | Partial | Endpoint exists but underlying business logic not implemented |

## Summary

- **Complete Functions:** 1 out of 6 core business logic functions (17%)
- **Partial Functions:** 1 out of 6 core business logic functions (17%) 
- **Not Implemented:** 4 out of 6 core business logic functions (66%)

The project has a solid architectural foundation with proper separation of concerns, database layer, and web interfaces. However, most core business logic functions require implementation to meet the requirements specification.

## 3. Unit Test Summary

### Test Scripts Created:
- `tests/test_add_book.py` - Tests for add_book_to_catalog function (16 test cases)
- `tests/test_borrow_book.py` - Tests for borrow_book_by_patron function (12 test cases)  
- `tests/test_return_book.py` - Tests for return_book_by_patron function (8 test cases)
- `tests/test_late_fee.py` - Tests for calculate_late_fee_for_book function (8 test cases)
- `tests/test_search.py` - Tests for search_books_in_catalog function (8 test cases)
- `tests/test_patron_status.py` - Tests for get_patron_status_report function (8 test cases)
- `tests/test_patron_status_web.py` - Tests for R7 web interface requirements (8 test cases)

### Test Coverage Details:

#### Complete Functions (Implemented):
- **add_book_to_catalog**: 16 comprehensive test cases covering input validation, ISBN validation, duplicate prevention, boundary conditions, and data formatting

- **borrow_book_by_patron**: 12 test cases covering valid scenarios, patron ID validation, availability checks, borrowing limit enforcement (including bug detection), and database updates

#### Partial/Not Implemented Functions:
- **return_book_by_patron**: 8 focused test cases covering:
  - Input validation (patron ID formats, book ID validation)
  - Business logic verification (wrong patron returns, already returned books)
  - Success message formatting and late fee integration
  - Database state updates (available copies, return dates)

- **calculate_late_fee_for_book**: 8 essential test cases covering:
  - Fee calculation structure ($0.50/day first 7 days, $1.00/day after, max $15.00)
  - Overdue scenarios (within 7 days, over 7 days, maximum fee cap)
  - Input validation (patron ID formats, book ID validation)
  - API response format requirements for JSON endpoint

- **search_books_in_catalog**: 8 comprehensive test cases covering:
  - Input validation and security (SQL injection protection)
  - Case-insensitive partial matching for title/author
  - Exact ISBN matching vs partial matching
  - Return format consistency with catalog display
  - Multiple matches and availability display

- **get_patron_status_report**: 8 core test cases covering:
  - Comprehensive patron ID validation
  - Multi-patron data isolation
  - Format consistency (dates, monetary values)
  - Complete data structure requirements
  - Security and performance considerations

#### Web Interface Requirements:
- **test_patron_status_web.py**: 8 test cases documenting R7 web interface requirements:
  - Missing menu option verification (currently no patron status link)
  - Missing routes and templates (404 errors expected)
  - Form and display requirements documentation
  - Integration with existing system consistency
  - URL patterns and routing structure needs

### Testing Approach:
- **Focused Test Cases**: Streamlined to 5-8 most important tests per function
- **Requirements Coverage**: Each test maps to specific requirement (R1-R7)
- **Bug Detection**: Dedicated tests identify and document existing bugs
- **Implementation Guidance**: Tests serve as specifications for developers
- **Security Testing**: SQL injection and input validation coverage

### Test Database Strategy:
- Each test file uses isolated test database (`test_library.db`)
- Automatic setup and teardown for each test
- Sample data creation for comprehensive testing
- Database state verification for data integrity tests

**Total Test Cases**: 68 focused test cases across all functions, providing comprehensive coverage with emphasis on the most critical scenarios for both implemented and planned functionality.
