from playwright.sync_api import expect

def test_homepage(page):
    page.goto("/home")    
    expect(page.get_by_text("CPT Dashboard")).to_be_visible()
