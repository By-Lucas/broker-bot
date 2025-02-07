import os
import re
import json
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from ..http.automail import get_pin
from playwright_stealth import stealth_async
from playwright.async_api import Playwright, async_playwright


async def fill_form(page, email, password):
    email_selector = 'input.input-control-cabinet__input[type="email"]'
    password_selector = 'input.input-control-cabinet__input[type="password"]'
    login_button_selector = 'button.button--primary[type="submit"]'

    await page.locator(email_selector).wait_for(state="visible")
    await page.locator(email_selector).fill(email)

    await page.locator(password_selector).wait_for(state="visible")
    await page.locator(password_selector).fill(password)

    await page.locator(login_button_selector).wait_for(state="visible")
    await page.locator(login_button_selector).click()


async def fill_code_form(page, code):
    code_selector = 'input.input-control-cabinet__input[name="code"]'
    login_button_selector = 'button.button--primary[type="submit"]'

    await page.locator(code_selector).wait_for(state="visible")
    await page.locator(code_selector).fill(code)

    await page.locator(login_button_selector).wait_for(state="visible")
    await page.locator(login_button_selector).click()


class Browser(object):
    base_url = "qxbroker.com"
    https_base_url = f"https://{base_url}"
    args = [
        "--disable-web-security",
        "--no-sandbox",
        "--aggressive-cache-discard",
        "--disable-cache",
        "--disable-application-cache",
        "--disable-offline-load-stale-cache",
        "--disk-cache-size=0",
        "--disable-background-networking",
        "--disable-default-apps",
        "--disable-extensions",
        "--disable-sync",
        "--disable-translate",
        "--hide-scrollbars",
        "--metrics-recording-only",
        "--mute-audio",
        "--safebrowsing-disable-auto-update",
        "--ignore-certificate-errors",
        "--ignore-ssl-errors",
        "--ignore-certificate-errors-spki-list",
        "--disable-features=LeakyPeeker",
        "--disable-setuid-sandbox",
    ]

    def __init__(self, api):
        self.api = api
        self.html = None

    async def run(self, playwright: Playwright) -> None:
        if self.api.user_data_dir:
            browser = playwright.firefox
            context = await browser.launch_persistent_context(
                self.api.user_data_dir,
                args=self.args,
                headless=True,
            )
            page = context.pages[0]
        else:
            browser = await playwright.firefox.launch(
                headless=True,
                args=self.args,
            )
            context = await browser.new_context()
            page = await context.new_page()

        await page.set_extra_http_headers(
            {
                "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
            }
        )
        await stealth_async(page)
        url = f"{self.https_base_url}/{self.api.lang}/sign-in/modal/"
        await page.goto(url=url)
        if page.url != f"{self.https_base_url}/{self.api.lang}/trade":
            await page.wait_for_timeout(5000)
            await fill_form(page, self.api.email, self.api.password)
            await self.persist_sign(page)
        await page.wait_for_timeout(5000)
        source = await page.content()
        self.html = BeautifulSoup(source, "html.parser")
        status, message = self.is_success()
        if not status:
            print(message)
            await context.close() if self.api.user_data_dir else await browser.close()
            return
        await self.save_session(page, context)
        await context.close() if self.api.user_data_dir else await browser.close()

    async def persist_sign(self, page):
        async with page.expect_navigation():
            await page.wait_for_timeout(5000)
            soup = BeautifulSoup(await page.content(), "html.parser")
            required_keep_code = soup.find("input", {"name": "keep_code"})
            if required_keep_code:
                auth_body = soup.find("main", {"class": "auth__body"})
                input_message = (
                    f'{auth_body.find("p").text}: '
                    if auth_body.find("p")
                    else "Insira o código PIN que acabamos de enviar para o seu e-mail: "
                )
                pin_code = await get_pin(self.api.email, self.api.email_pass)
                code = pin_code or int(input(input_message))
                await fill_code_form(page, code)

    async def save_session(self, page, context):
        script = self.html.find_all("script", {"type": "text/javascript"})
        settings = script[1].get_text().strip().replace(";", "")
        match = re.sub("window.settings = ", "", settings)
        token = json.loads(match).get("token")
        self.api.session_data["token"] = token
        output_file = Path(
            os.path.join(self.api.resource_path, f"{self.api.email}_session.json")
        )
        output_file.parent.mkdir(exist_ok=True, parents=True)
        cookies = await context.cookies()
        cookiejar = requests.utils.cookiejar_from_dict(
            {c["name"]: c["value"] for c in cookies}
        )
        cookies_string = "; ".join([f"{c.name}={c.value}" for c in cookiejar])
        self.api.session_data["Cookie"] = cookies_string
        user_agent = await page.evaluate("() => navigator.userAgent;")
        self.api.session_data["User-Agent"] = user_agent
        result_dict = {"headers": {}}
        headers = result_dict["headers"]
        headers["User-Agent"] = user_agent
        headers["Cookie"] = cookies_string
        result_dict["token"] = token
        result_dict["headers"] = headers
        output_file.write_text(json.dumps(result_dict, indent=4))

    def is_success(self):
        match = self.html.find("div", {"class": "hint -danger"}) or self.html.find(
            "div", {"class": "hint hint--danger"}
        )
        if match is None:
            return True, "Login successful."

        return False, f"Login failed. {match.text.strip()}"

    async def main(self) -> None:
        async with async_playwright() as playwright:
            await self.run(playwright)

    async def get_cookies_and_ssid(self):
        await self.main()
        return self.is_success()
