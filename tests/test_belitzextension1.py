import os
import asyncio
import json
from playwright.async_api import async_playwright, expect
import pytest

@pytest.mark.asyncio
async def test_belitz_extension():
    async with async_playwright() as p:
        extension_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '1.3.0_0')
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir="/tmp/test-user-data-dir",
            headless=False,
            args=[
                f"--disable-extensions-except={extension_path}",
                f"--load-extension={extension_path}",
            ],
        )

        page = await browser_context.new_page()
        await page.goto(f"chrome-extension://mijcclaopfkfbocihgdkhikgpkfnagph/")

        # 1. "Don't have an account? Sign up" tıklama testi
        await page.click("text=Don't have an account? Sign up")

        # 2. "Back to sign in" tıklama testi
        await page.click("text=Back to sign in")

        # 3. "Forgot your password?" tıklama testi
        await page.click("text=Forgot your password?")

        # 4. "Back to sign in" tıklama testi
        await page.click("text=Back to sign in")

        # 5. Kullanıcı girişi appsettings.jsondaki email ve şifre bilgileriyle
        with open("appsettings.json", "r") as f:
            settings = json.load(f)
        await page.fill("input[type=email]", settings["email"])
        await page.fill("input[type=password]", settings["password"])

        # 6. "Sign In" butonuna tıklama testi
        await page.click("button[type=submit]")

        # 7. "AI Assistant" başlığının görünüp görünmediğini kontrol etme testi
        assert await page.query_selector("h3.font-medium.text-sm") is not None

        # 8. "Ask GenAI..." alanına "Hello Belitz.ai" yazma testi
        await page.fill("textarea[placeholder='Ask GenAI...']", "Hello Belitz.ai")

        # 9. "Surprise me" metninin görünüp görünmediğini kontrol etme testi
        assert await page.query_selector("span:has-text('Surprise me')") is not None

        # 10. Silme butonuna tıklama testi
        await page.click("button[title='Clear']")

        # 11. "Are you sure?" sorusuna onay verme testi
        async with page.handle_dialog() as dialog:
            await dialog.accept()

        # 12. Kullanıcı çıkışı yapma testi
        await page.click("button[title='...']")

        await browser_context.close()
