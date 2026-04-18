from playwright.sync_api import sync_playwright
import time

def get_otc_prices(pair):

    symbol=pair.replace(" OTC","").replace("/","")

    prices=[]

    with sync_playwright() as p:

        browser=p.chromium.launch(headless=True)
        page=browser.new_page()

        # open pocket option demo chart
        page.goto("https://pocketoption.com/en/cabinet/demo-quick-high-low/")

        # wait chart load
        page.wait_for_timeout(12000)

        for _ in range(60):
            try:
                price=page.locator("span.price").first.inner_text()
                prices.append(float(price))
            except:
                pass

            time.sleep(1)

        browser.close()

    return prices
