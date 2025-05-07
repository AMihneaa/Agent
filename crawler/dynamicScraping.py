from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import json
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


class DynamicScraping:
    """
    This class is responsible for dynamic scraping of web pages using Playwright.
    It includes methods to set up the browser, navigate to a URL, and extract content.
    """

    def __init__(self, base_url=None, browser_type="chromium", headless=True, timeout=10000):
        self.browser_type = browser_type
        self.headless = headless
        self.timeout = timeout
        self.base_url = base_url

        self.browser = None
        self.page = None
        self.context = None

        self.results = []
        self.selectors = {}
        self.filters = []

    async def __aenter__(self):
        await self.init_browser()
        await self.navigate()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def init_browser(self):
        self.playwright = await async_playwright().start()
        browser_launcher = getattr(self.playwright, self.browser_type)
        self.browser = await browser_launcher.launch(headless=self.headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.timeout)

    async def close(self):
        if self.browser:
            await self.browser.close()
        if hasattr(self, "playwright"):
            await self.playwright.stop()

    async def navigate(self, url: str = ""):
        try:
            target_url = url or self.base_url
            if not target_url:
                raise ValueError("No URL provided to navigate.")
            await self.page.goto(target_url, wait_until="domcontentloaded", timeout=self.timeout)
        except Exception as e:
            print(f"[!] Navigation error: {e}")

    async def wait_for_selector(self, selector):
        try:
            await self.page.wait_for_selector(selector)
        except PlaywrightTimeoutError:
            print(f"[!] Timeout waiting for selector: {selector}")

    async def extract_elements(self, selector, attrs):
        elements = await self.page.query_selector_all(selector)
        for el in elements:
            data = {}
            for attr in attrs:
                if attr == "text":
                    data[attr] = (await el.text_content()) or ""
                else:
                    data[attr] = (await el.get_attribute(attr)) or ""
            self.results.append(data)
        return self.results

    async def extract_filters(self):
        filter_container_selector = "div.filter-default"
        await self.wait_for_selector(filter_container_selector)
        filters = await self.page.query_selector_all(filter_container_selector)
        extracted = []

        for filter_div in filters:
            title_el = await filter_div.query_selector("span")  
            title = (await title_el.text_content()).strip() if title_el else "Unknown"

            option_els = await filter_div.query_selector_all("a") 
            options = []

            for opt_el in option_els:
                text = await opt_el.text_content()
                href = await opt_el.get_attribute("href")
                
                if text and href:
                    cleaned = text.strip().replace('\n', ' ').strip()
                    if cleaned and cleaned != title:
                        options.append({
                            "label": cleaned,
                            "url": href.strip()
                        })


            extracted.append({
                "category": title,
                "options": options
            })

        self.filters = extracted
        return extracted
    
    def build_filters(self, base_url, filters):
        parsed = urlparse(base_url)
        
        filter_paths = []
        for f in filters:
            url = f.get("url")
            if not isinstance(url, str):
                continue
            parsed_filter_url = urlparse(url)
            path_parts = parsed_filter_url.path.split("/filter/")[-1].split("/c")[0]
            filter_paths.append(path_parts)

        combined_filter_path = "/filter/" + "/".join(filter_paths)
        new_path = parsed.path.rstrip("/") + combined_filter_path + "/c"

        new_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            new_path,
            "",  
            "",  
            ""   
        ))

        self.base_url = new_url
        return new_url

    async def extract_products(self):
        product_selector = "div.card-item"
        await self.wait_for_selector(product_selector)
        products = await self.page.query_selector_all(product_selector)
        product_data = []
        for p in products:
            title = await p.query_selector("a.card-v2-title")
            price = await p.query_selector("p.product-new-price")
            item = {
                "title": await title.text_content() if title else "",
                "price": await price.text_content() if price else "",
            }

            [product_data.append(item) if item['title'] != '' and item['price'] != ''  else print("Empty Produs")]
            # product_data.append(item) -> numara si produsele goale
        self.results.extend(product_data)
        return product_data

    def set_custom_config(self, selectors: dict):
        self.selectors = selectors

    def saveToJson(self, filter_file_name: str = "filter.json", product_file_name: str = "product.json", number_of_product: int = 10):
        with open(filter_file_name, 'w', encoding="utf-8") as f:
            json.dump(self.filters, f, indent=2, ensure_ascii=False)

        with open(product_file_name, 'w', encoding='utf-8') as f:
            json.dump(self.results[:number_of_product], f, indent=2, ensure_ascii=False)
