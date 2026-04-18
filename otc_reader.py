from playwright.sync_api import sync_playwright

def get_otc_price():

    with sync_playwright() as p:

        browser=p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        page=browser.new_page()

        page.goto(
            "https://pocketoption.com/en/cabinet/demo-quick-high-low/",
            timeout=60000
        )

        # tegereza chart
        page.wait_for_timeout(15000)

        price=page.locator("span.price").first.inner_text()

        browser.close()

        return price
