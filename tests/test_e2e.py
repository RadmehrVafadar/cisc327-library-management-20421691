from playwright.sync_api import Playwright, sync_playwright, expect

# add a new book to catalog
def test_add_new_book(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("http://127.0.0.1:5000/catalog")
    page.get_by_role("link", name="➕ Add New Book").click()
    page.get_by_role("textbox", name="Title *").click()
    page.get_by_role("textbox", name="Title *").fill("How to do a backflip")
    page.get_by_role("textbox", name="Author *").click()
    page.get_by_role("textbox", name="Author *").fill("rad")
    page.get_by_role("textbox", name="ISBN *").click()
    page.get_by_role("textbox", name="ISBN *").fill("0000000000000")
    page.get_by_role("spinbutton", name="Total Copies *").click()
    page.get_by_role("spinbutton", name="Total Copies *").fill("3")
    page.get_by_role("button", name="Add Book to Catalog").click()

    # verify if the book appears in the catalog 
    expect(page.get_by_role("cell", name="0000000000000")).to_be_visible()


    # ---------------------
    context.close()
    browser.close()


# borrow using patron id
def test_borrow_book_using_patron_ID(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("http://127.0.0.1:5000/catalog")
    page.get_by_role("row", name="4 How to do a backflip rad").get_by_placeholder("Patron ID (6 digits)").click()
    page.get_by_role("row", name="4 How to do a backflip rad").get_by_placeholder("Patron ID (6 digits)").fill("111111")
    page.get_by_role("cell", name="111111 Borrow").get_by_role("button").click()


    # verify the borrow confirmation message appears
    expect(page.get_by_text("Successfully borrowed \"How to")).to_be_visible()

    # ---------------------
    context.close()
    browser.close()