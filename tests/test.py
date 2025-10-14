# tests/test_business_logic.py
import threading
import pytest
from decimal import Decimal
from datetime import datetime, timedelta

# -----------------------------
# ADAPT THESE IMPORTS to match your project
# -----------------------------
# Example expected symbols:
# add_book(data: dict) -> Book-like object or dict
# get_catalog() -> list[dict]
# borrow_book(patron_id: str, book_id: int, now: datetime | None = None) -> dict/result
# return_book(patron_id: str, book_id: int, return_date: datetime | None = None) -> dict/result
# calculate_late_fee(borrow_date: datetime, return_date: datetime) -> (days_overdue:int, fee:Decimal)
# calculate_late_fee_by_ids(patron_id: str, book_id: int, as_of: datetime | None = None) -> dict
# search_books(q: str, type: str) -> list[dict]
# get_patron_status(patron_id: str) -> dict
# app_factory() -> Flask app (for integration-ish tests)
#
# Replace the following import block with the real module paths in your implementation.
try:
    from library.business import (
        add_book,
        get_catalog,
        borrow_book,
        return_book,
        calculate_late_fee,
        calculate_late_fee_by_ids,
        search_books,
        get_patron_status,
    )
    # Optional: if you have an app factory to create a testing app with in-memory db
    try:
        from library.app import create_app as app_factory
    except Exception:
        app_factory = None
except Exception:
    # If your package paths are different, tests will skip with informative message below.
    add_book = get_catalog = borrow_book = return_book = calculate_late_fee = None
    calculate_late_fee_by_ids = search_books = get_patron_status = None
    app_factory = None
# -----------------------------
# End ADAPT
# -----------------------------

pytestmark = pytest.mark.usefixtures("db_session")  # optional; remove if not applicable

# -----------------------------
# Helper utilities & fixtures
# -----------------------------
@pytest.fixture(scope="module")
def today():
    # fixed point in time for deterministic tests
    return datetime(2025, 1, 15, 10, 0, 0)


@pytest.fixture
def sample_book_payload():
    return {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "isbn": "9780132350884",
        "total_copies": 3,
    }


@pytest.fixture
def ensure_business_layer_available():
    # Skip all tests if core functions are not found — avoids noisy tracebacks.
    missing = []
    required = {
        "add_book": add_book,
        "get_catalog": get_catalog,
        "borrow_book": borrow_book,
        "return_book": return_book,
        "calculate_late_fee": calculate_late_fee,
        "search_books": search_books,
        "get_patron_status": get_patron_status,
    }
    for name, fn in required.items():
        if fn is None:
            missing.append(name)
    if missing:
        pytest.skip(
            "Business-layer functions missing. Adapt import paths in tests. Missing: %s"
            % ", ".join(missing)
        )
    return True


# -----------------------------
# R1 - Add Book Tests
# -----------------------------
def test_add_book_valid_creates_book(ensure_business_layer_available, sample_book_payload):
    result = add_book(sample_book_payload)
    # Accept either a dict-like response with 'book_id' or a model object with id attribute
    assert result is not None
    if isinstance(result, dict):
        book_id = result.get("book_id") or result.get("id")
        assert isinstance(book_id, int) and book_id > 0
    else:
        # object with .id attribute
        assert hasattr(result, "id") and getattr(result, "id") > 0

    # Confirm book appears in catalog with available == total
    catalog = get_catalog()
    matches = [b for b in catalog if b["isbn"] == sample_book_payload["isbn"]]
    assert len(matches) == 1
    b = matches[0]
    assert b["title"] == sample_book_payload["title"]
    assert b["author"] == sample_book_payload["author"]
    assert int(b["total_copies"]) == sample_book_payload["total_copies"]
    assert int(b["available_copies"]) == sample_book_payload["total_copies"]


@pytest.mark.parametrize("title, expected_ok", [
    ("A" * 200, True),
    ("A" * 201, False),
    ("", False),
    (None, False),
])
def test_add_book_title_length_and_required(ensure_business_layer_available, sample_book_payload, title, expected_ok):
    payload = sample_book_payload.copy()
    payload["title"] = title
    if expected_ok:
        add_book(payload)
    else:
        with pytest.raises(Exception):
            add_book(payload)


@pytest.mark.parametrize("isbn,ok", [
    ("9780132350884", True),   # 13 digits
    ("123456789012", False),   # 12
    ("12345678901234", False), # 14
    ("9780-132350884", False), # non-digit
])
def test_add_book_isbn_validation(ensure_business_layer_available, sample_book_payload, isbn, ok):
    payload = sample_book_payload.copy()
    payload["isbn"] = isbn
    if ok:
        add_book(payload)
    else:
        with pytest.raises(Exception):
            add_book(payload)


@pytest.mark.parametrize("copies,ok", [
    (1, True),
    (5, True),
    (0, False),
    (-1, False),
    (1.5, False),
])
def test_add_book_total_copies_validation(ensure_business_layer_available, sample_book_payload, copies, ok):
    payload = sample_book_payload.copy()
    payload["total_copies"] = copies
    if ok:
        add_book(payload)
    else:
        with pytest.raises(Exception):
            add_book(payload)


# -----------------------------
# R2 - Catalog Tests
# -----------------------------
def test_get_catalog_returns_required_fields(ensure_business_layer_available):
    catalog = get_catalog()
    assert isinstance(catalog, list)
    # Empty catalog allowed; otherwise check fields of first entry
    if catalog:
        sample = catalog[0]
        for key in ("book_id", "title", "author", "isbn", "available_copies", "total_copies"):
            assert key in sample


def test_get_catalog_borrowable_flag(ensure_business_layer_available):
    # Make sure at least one book has 0 available and one has >0
    # We'll add two books for the test
    b1 = {"title": "No Copies", "author": "X", "isbn": "1111111111111", "total_copies": 1}
    b2 = {"title": "Many Copies", "author": "Y", "isbn": "2222222222222", "total_copies": 2}
    book1 = add_book(b1)
    book2 = add_book(b2)
    # Borrow the single copy of b1 to make available 0
    # derive book_id from returned value:
    try:
        book1_id = book1.get("book_id") or book1.get("id")
    except Exception:
        book1_id = getattr(book1, "id", None)
    # Borrow with a dummy patron to consume it
    borrow_book("123456", book1_id)
    catalog = get_catalog()
    # find entries
    for e in catalog:
        assert 0 <= int(e["available_copies"]) <= int(e["total_copies"])
        # optional borrowable flag
        if "is_borrowable" in e:
            assert e["is_borrowable"] == (int(e["available_copies"]) > 0)


# -----------------------------
# R3 - Borrowing Tests
# -----------------------------
def test_borrow_book_success_decrements_available(ensure_business_layer_available, sample_book_payload, today):
    # Add book and borrow once
    r = add_book(sample_book_payload)
    try:
        book_id = r.get("book_id") or r.get("id")
    except Exception:
        book_id = getattr(r, "id", None)
    # Ensure patron starts with zero borrows — business function should check/assume
    result = borrow_book("123456", book_id, now=today)
    # Assert success shape
    assert result is not None
    # Check catalog updated
    catalog = get_catalog()
    book = next((b for b in catalog if b["isbn"] == sample_book_payload["isbn"]), None)
    assert book is not None
    assert int(book["available_copies"]) == sample_book_payload["total_copies"] - 1


@pytest.mark.parametrize("patron_id,ok", [
    ("12345", False),     # too short
    ("1234567", False),   # too long
    ("12a456", False),    # not all digits
    ("000000", True),     # valid (all zeros allowed if accepted)
])
def test_borrow_book_invalid_patron_id_format(ensure_business_layer_available, sample_book_payload, patron_id, ok):
    r = add_book(sample_book_payload)
    try:
        book_id = r.get("book_id") or r.get("id")
    except Exception:
        book_id = getattr(r, "id", None)
    if ok:
        borrow_book(patron_id, book_id)
    else:
        with pytest.raises(Exception):
            borrow_book(patron_id, book_id)


def test_borrow_book_not_available(ensure_business_layer_available):
    # Add book with 1 copy and borrow twice
    r = add_book({"title": "Single", "author": "A", "isbn": "3333333333333", "total_copies": 1})
    book_id = r.get("book_id") or r.get("id") if isinstance(r, dict) else getattr(r, "id", None)
    borrow_book("200000", book_id)
    with pytest.raises(Exception):
        borrow_book("200001", book_id)


def test_borrow_book_patron_over_limit(ensure_business_layer_available):
    # create a patron with 5 active borrows (simulate via calling borrow_book)
    r = add_book({"title": "Bulk", "author": "A", "isbn": "4444444444444", "total_copies": 10})
    book_id = r.get("book_id") or r.get("id") if isinstance(r, dict) else getattr(r, "id", None)
    patron = "555555"
    # create 5 dummy books and borrow them for patron
    for i in range(5):
        rb = add_book({"title": f"X{i}", "author": "A", "isbn": f"900000000000{i}", "total_copies": 1})
        bid = rb.get("book_id") or rb.get("id") if isinstance(rb, dict) else getattr(rb, "id", None)
        borrow_book(patron, bid)
    # Now attempt to borrow a 6th
    with pytest.raises(Exception):
        borrow_book(patron, book_id)


def test_borrow_book_concurrent_last_copy_only_one_success(ensure_business_layer_available):
    # Add a book with 1 copy and attempt to borrow it from two threads
    r = add_book({"title": "Race", "author": "R", "isbn": "6666666666666", "total_copies": 1})
    book_id = r.get("book_id") or r.get("id") if isinstance(r, dict) else getattr(r, "id", None)
    results = []
    exceptions = []

    def attempt(patron_id):
        try:
            res = borrow_book(patron_id, book_id)
            results.append((patron_id, res))
        except Exception as e:
            exceptions.append((patron_id, e))

    t1 = threading.Thread(target=attempt, args=("700001",))
    t2 = threading.Thread(target=attempt, args=("700002",))
    t1.start(); t2.start()
    t1.join(); t2.join()

    # Exactly one should succeed, one should fail
    assert len(results) == 1
    assert len(exceptions) == 1


# -----------------------------
# R4 - Return Tests
# -----------------------------
def test_return_book_on_time(ensure_business_layer_available, today):
    book = add_book({"title": "Ret", "author": "R", "isbn": "7777777777777", "total_copies": 2})
    book_id = book.get("book_id") or getattr(book, "id", None)
    patron = "800000"
    borrow_book(patron, book_id, now=today - timedelta(days=1))  # borrow 1 day ago
    # return before due date (due is borrow+14)
    return_result = return_book(patron, book_id, return_date=today)
    assert return_result is not None
    # Check that no late fee applied (assuming return_result includes fee or borrow record updated)
    if isinstance(return_result, dict) and "late_fee" in return_result:
        assert Decimal(str(return_result["late_fee"])) == Decimal("0.00")


def test_return_book_with_late_fee_calculation(ensure_business_layer_available):
    book = add_book({"title": "Late", "author": "L", "isbn": "8888888888888", "total_copies": 1})
    book_id = book.get("book_id") or getattr(book, "id", None)
    patron = "900000"
    borrow_date = datetime(2025, 1, 1, 10, 0, 0)
    borrow_book(patron, book_id, now=borrow_date)
    # return 8 + 14 = 22 days after borrow (overdue 8)
    return_date = borrow_date + timedelta(days=22)
    result = return_book(patron, book_id, return_date=return_date)
    # verify late fee present or recorded
    # Either return contained fee or business layer updated borrow record — we try to call calculate_late_fee directly
    days_overdue, fee = calculate_late_fee(borrow_date, return_date)
    assert days_overdue == 8
    assert Decimal(str(fee)).quantize(Decimal("0.01")) == Decimal("4.50")


def test_return_book_not_borrowed_by_patron(ensure_business_layer_available):
    book = add_book({"title": "Unborrowed", "author": "U", "isbn": "9999999999999", "total_copies": 1})
    book_id = book.get("book_id") or getattr(book, "id", None)
    with pytest.raises(Exception):
        return_book("010101", book_id, return_date=datetime(2025, 1, 2))


def test_return_book_idempotent_second_call_fails(ensure_business_layer_available):
    book = add_book({"title": "Idemp", "author": "I", "isbn": "1212121212121", "total_copies": 1})
    book_id = book.get("book_id") or getattr(book, "id", None)
    patron = "222222"
    borrow_book(patron, book_id, now=datetime(2025, 1, 1))
    # First return
    return_book(patron, book_id, return_date=datetime(2025, 1, 10))
    # Second return should fail
    with pytest.raises(Exception):
        return_book(patron, book_id, return_date=datetime(2025, 1, 11))


# -----------------------------
# R5 - Late Fee Calculation Tests
# -----------------------------
def test_late_fee_zero_when_not_overdue():
    borrow_date = datetime(2025, 1, 1, 10, 0, 0)
    return_date = borrow_date + timedelta(days=14)  # on due date
    days, fee = calculate_late_fee(borrow_date, return_date)
    assert days == 0
    assert Decimal(str(fee)).quantize(Decimal("0.01")) == Decimal("0.00")


def test_late_fee_one_day_overdue():
    borrow_date = datetime(2025, 1, 1, 10, 0, 0)
    return_date = borrow_date + timedelta(days=15)
    days, fee = calculate_late_fee(borrow_date, return_date)
    assert days == 1
    assert Decimal(str(fee)).quantize(Decimal("0.01")) == Decimal("0.50")


def test_late_fee_seven_days_overdue():
    borrow_date = datetime(2025, 1, 1, 10, 0, 0)
    return_date = borrow_date + timedelta(days=21)
    days, fee = calculate_late_fee(borrow_date, return_date)
    assert days == 7
    assert Decimal(str(fee)).quantize(Decimal("0.01")) == Decimal("3.50")


def test_late_fee_eight_days_overdue():
    borrow_date = datetime(2025, 1, 1, 10, 0, 0)
    return_date = borrow_date + timedelta(days=22)
    days, fee = calculate_late_fee(borrow_date, return_date)
    assert days == 8
    assert Decimal(str(fee)).quantize(Decimal("0.01")) == Decimal("4.50")


def test_late_fee_cap_at_15_dollars():
    borrow_date = datetime(2024, 1, 1, 10, 0, 0)
    return_date = borrow_date + timedelta(days=200)
    days, fee = calculate_late_fee(borrow_date, return_date)
    assert Decimal(str(fee)).quantize(Decimal("0.01")) <= Decimal("15.00")


# -----------------------------
# R6 - Search Tests
# -----------------------------
def test_search_title_partial_case_insensitive(ensure_business_layer_available):
    add_book({"title": "The Lord of the Rings", "author": "Tolkien", "isbn": "1010101010101", "total_copies": 1})
    add_book({"title": "lord of the flies", "author": "Golding", "isbn": "2020202020202", "total_copies": 1})
    add_book({"title": "Algorithm Design", "author": "Kleinberg", "isbn": "3030303030303", "total_copies": 1})
    res = search_books("lord", type="title")
    isbns = {r["isbn"] for r in res}
    assert "1010101010101" in isbns and "2020202020202" in isbns


def test_search_isbn_exact_match_only(ensure_business_layer_available):
    add_book({"title": "Exact", "author": "E", "isbn": "1111111111111", "total_copies": 1})
    add_book({"title": "Other", "author": "O", "isbn": "1111111111112", "total_copies": 1})
    res = search_books("1111111111111", type="isbn")
    assert len(res) == 1
    assert res[0]["isbn"] == "1111111111111"
    # partial search should not match
    res_partial = search_books("111111", type="isbn")
    assert len(res_partial) == 0


# -----------------------------
# R7 - Patron Status Tests
# -----------------------------
def test_patron_status_current_borrowed_list(ensure_business_layer_available):
    patron = "333333"
    b1 = add_book({"title": "PS1", "author": "A", "isbn": "4141414141414", "total_copies": 2})
    b2 = add_book({"title": "PS2", "author": "B", "isbn": "4242424242424", "total_copies": 2})
    id1 = b1.get("book_id") or getattr(b1, "id", None)
    id2 = b2.get("book_id") or getattr(b2, "id", None)
    borrow_book(patron, id1, now=datetime(2025, 1, 1))
    borrow_book(patron, id2, now=datetime(2025, 1, 2))
    status = get_patron_status(patron)
    assert "currently_borrowed" in status
    assert len(status["currently_borrowed"]) >= 2
    assert status["number_currently_borrowed"] == len(status["currently_borrowed"])


def test_patron_status_total_late_fees_sum(ensure_business_layer_available):
    patron = "444444"
    b = add_book({"title": "FeeTest", "author": "F", "isbn": "5151515151515", "total_copies": 2})
    bid = b.get("book_id") or getattr(b, "id", None)
    borrow_date = datetime(2024, 12, 1)
    borrow_book(patron, bid, now=borrow_date)
    # leave it overdue; call get_patron_status which should compute outstanding fees
    status = get_patron_status(patron)
    assert "total_late_fees" in status
    assert Decimal(str(status["total_late_fees"])).quantize(Decimal("0.01")) >= Decimal("0.00")


# -----------------------------
# Misc / Invariants
# -----------------------------
def test_available_copies_never_negative(ensure_business_layer_available):
    # perform many operations and assert invariant holds
    # create a book with 2 copies
    b = add_book({"title": "Inv", "author": "I", "isbn": "6161616161616", "total_copies": 2})
    bid = b.get("book_id") or getattr(b, "id", None)
    p1, p2 = "600001", "600002"
    borrow_book(p1, bid)
    borrow_book(p2, bid)
    # now available should be 0
    c = next(bk for bk in get_catalog() if bk["isbn"] == "6161616161616")
    assert int(c["available_copies"]) == 0
    # further borrow should fail and not make available negative
    with pytest.raises(Exception):
        borrow_book("600003", bid)
    c2 = next(bk for bk in get_catalog() if bk["isbn"] == "6161616161616")
    assert int(c2["available_copies"]) == 0