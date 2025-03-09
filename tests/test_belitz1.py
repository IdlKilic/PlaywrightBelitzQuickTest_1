import pytest
from playwright.sync_api import sync_playwright, expect
import json
import os
import random


def load_config():
    config_file_path = '/Users/idil/Desktop/PlaywrightBelitzQuickTest_1/appsettings.json'
    if os.path.exists(config_file_path):
        with open(config_file_path, 'r') as f:
            return json.load(f)
    else:
        raise FileNotFoundError(f"{config_file_path} dosyası bulunamadı.")


def generate_random_phone():
    return f"+905{''.join([str(random.randint(0, 9)) for _ in range(9)])}"


def generate_random_email():
    return f"test{random.randint(1000, 9999)}@example.com"


@pytest.fixture(scope="function")
def setup(request):
    config = load_config()
    baseurl = config["Url"]
    username = config["UserEmail"]
    password = config["Password"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            locale="en-US",
            color_scheme="light",
            record_video_dir="videos/"
        )

        context.tracing.start(
            screenshots=True,
            snapshots=True,
            sources=True
        )

        page = context.new_page()
        page.set_default_timeout(45000)
        page.goto(baseurl, wait_until="networkidle")

        yield page, baseurl, username, password

        context.tracing.stop(
            path=f"traces/{request.node.name}.zip"
        )
        context.close()
        browser.close()


def validate_page(page, baseurl):
    page.wait_for_load_state("networkidle")
    assert page.url == baseurl, f"Expected URL: {baseurl}, Found URL: {page.url}"
    heading = page.locator('h1').first
    expect(heading).to_be_visible()
    heading_text = heading.inner_text().lower()
    assert 'belitz' in heading_text, f"Page heading '{heading_text}' does not contain 'belitz'"


def perform_login(page, baseurl, username, password):
    # Click Get Started
    get_started_button = page.locator('header button:has-text("Get Started")').first
    expect(get_started_button).to_be_visible()
    get_started_button.click()

    # Sign in process
    sign_in_url = baseurl + "sign-in"
    page.wait_for_url(sign_in_url)
    page.wait_for_selector('form', state='visible')

    email_input = page.locator('input[type="email"]').first
    password_input = page.locator('input[type="password"]').first
    expect(email_input).to_be_visible()
    expect(password_input).to_be_visible()

    email_input.fill(username)
    password_input.fill(password)

    sign_in_button = page.locator('form button[type="submit"]').first
    expect(sign_in_button).to_be_visible()
    sign_in_button.click()

    copilot_url = baseurl + "copilot"
    page.wait_for_url(copilot_url, timeout=10000)
    assert page.url == copilot_url


def test_complete_scenario(setup):
    page, baseurl, username, password = setup

    # 1. Validate initial page
    validate_page(page, baseurl)

    # 2. Perform login
    perform_login(page, baseurl, username, password)

    # 3. Check GenAI functionality
    ask_genai_textarea = page.locator('textarea[placeholder="Ask GenAI..."]')
    expect(ask_genai_textarea).to_be_visible()

    # Fill the textarea with "Hello"
    ask_genai_textarea.fill("Hello")

    # Check for Grammar text
    grammar_text = page.locator('span:text("Grammar")')
    expect(grammar_text).to_be_visible()

    nav_buttons = ["Documents", "Users", "Settings", "Copilot"]

    for click in nav_buttons:
        nav_button = page.locator(f'button:has-text("{click}")').first
        expect(nav_button).to_be_visible()
        nav_button.click()
        page.wait_for_load_state("networkidle")  # Sayfanın yüklenmesini bekleyin
        print(f"Clicked on {click} button successfully")

    # 5. Test Belitz link
    belitz_link = page.locator('a:has-text("Belitz")').first
    expect(belitz_link).to_be_visible()
    belitz_link.click()
    page.wait_for_url(baseurl)

    # 6-12. Book Demo flow
    demo_button = page.locator('header button:has-text("Book Demo")')
    expect(demo_button).to_be_visible()
    demo_button.click()

    # Verify Personal Information heading
    personal_info_heading = page.locator('h2:has-text("Personal Information")')
    expect(personal_info_heading).to_be_visible()

    # Fill demo form
    email_input = page.locator('input#email')
    phone_input = page.locator('input#phone')

    email_input.fill(generate_random_email())
    phone_input.fill(generate_random_phone())

    # Verify Next button is disabled
    next_button = page.locator('button:has-text("Next")')
    expect(next_button).to_be_visible()
    next_button.click()

    # Click Back
    back_button = page.locator('button:has-text("Back")')
    expect(back_button).to_be_visible()
    back_button.click()

    # Close demo popup
    close_button = page.locator('svg.lucide-x')
    expect(close_button).to_be_visible()
    close_button.click()

    # 13. Click Get Started
    get_started = page.locator('header button:has-text("Get Started")')
    expect(get_started).to_be_visible()
    get_started.click()

    # 14. Logout
    logout_button = page.locator(f'button[title="{username}"]')
    expect(logout_button).to_be_visible(timeout=10000)
    logout_button.click()

    # Verify redirect to login page
    login_url = baseurl + "sign-in"
    page.wait_for_url(login_url)
    assert page.url == login_url, f"Expected URL: {login_url}, Found URL: {page.url}"