from bs4 import BeautifulSoup, SoupStrainer
import requests
from typing import List, Optional
import json
from urllib.parse import urlparse
import aiohttp
import asyncio
import redis


class Crawler:
    
    __redis = redis.Redis(host='localhost', port=6379, db=0)

    def __init__(self, URL: str = "", subject: str = "") -> None:
        self.__url = URL
        self.__data_html = None
        self.__soup = None
        self.__subject_filter = subject
        self.__semaphore = asyncio.Semaphore(50)
        self.__results = []
        self.__redis.delete("visited_urls")

    @property
    def soup(self) -> str:
        return self.__soup.prettify() if self.__soup else ""

    @property
    def url(self) -> str:
        return self.__url

    @property
    def subject_filter(self) -> str:
        return self.__subject_filter

    @subject_filter.setter
    def subject_filter(self, subject: str) -> None:
        self.__subject_filter = subject

    @url.setter
    def url(self, URL: str) -> None:
        self.__url = URL

    async def asyncFetch(self, url: str, session: aiohttp.ClientSession) -> Optional[str]:
        if self.__redis.sismember("visited_urls", url):
            return None

        async with self.__semaphore:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        html = await response.text()
                        self.__data_html = html
                        self.__soup = BeautifulSoup(html, "html.parser")
                        self.__redis.sadd("visited_urls", url)
                        return html
                    else:
                        print(f"[!] Failed: {url} ({response.status})")
            except Exception as e:
                print(f"[!] Error fetching {url}: {type(e).__name__} - {e}")
        return None

    def is_valid(self, link: str) -> bool:
        path = urlparse(link).path
        return (
            path.startswith("/wiki/")
            and ":" not in path
            and not path.startswith("/wiki/Main_Page")
        )

    def linkExtractor(self) -> List[dict]:
        tag = SoupStrainer("a")
        if self.__soup is None:
            return []

        data = self.__soup.find_all(tag)
        links = []

        blacklist = ["portal", "template", "help", "category", "talk", "file", "main_page"]

        for tg in data:
            if not tg.has_attr("href"):
                continue

            href = tg["href"]
            text = tg.get_text(strip=True)

            if not href.startswith("/wiki/"):
                continue
            if ":" in href:
                continue
            if any(bad in href.lower() for bad in blacklist):
                continue
            if href == "#" or len(text) < 3:
                continue

            full_url = "https://en.wikipedia.org" + href
            links.append({"text": text, "url": full_url})

        return links

    async def multi_crawler_async(self, url: str, depth: int = 0, max_depth: int = 2, tolerant_depth: int = 4, session=None):
        if depth > tolerant_depth or self.__redis.sismember("visited_urls", url):
            return

        if session is None:
            async with aiohttp.ClientSession() as new_session:
                await self.multi_crawler_async(url, depth, max_depth, tolerant_depth, session=new_session)
                return

        html = await self.asyncFetch(url, session)
        if html is None or self.__soup is None:
            return

        go_deeper = False
        if self.__subject_filter and self.__subject_filter.lower() in self.__soup.get_text().lower():
            title = self.__soup.title.string if self.__soup.title else "No title"
            print(f"URL: [{url}] \t Depth: {depth}, title: {title}")

            first_paragraph = self.__soup.find("p")
            snippet = first_paragraph.get_text(strip=True) if first_paragraph else ""

            self.__results.append({
                "url": url,
                "title": title,
                "snippet": snippet,
            })
            go_deeper = True
        elif depth < max_depth:
            go_deeper = True

        if not go_deeper:
            return

        links = self.linkExtractor()

        tasks = [
            self.multi_crawler_async(link['url'], depth + 1, max_depth, tolerant_depth, session)
            for link in links
            if isinstance(link, dict)
            and 'url' in link
            and not self.__redis.sismember("visited_urls", link['url'])
            and self.is_valid(link['url'])
        ]

        if tasks:
            await asyncio.gather(*tasks)
            await asyncio.sleep(0.1)

    async def fetchPage(self, url) -> None:
        async with self.__semaphore:
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                              "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
                            }
                    
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:   
                            html = await response.text()

                            self.__data_html = html
                            self.__soup = BeautifulSoup(html, "html.parser")
                            filters = self.__soup.find_all("div", class_="filter")
                            for div in filters:
                                print(div.text.strip())
                            self.__results = filters
            except Exception as e:
                print(f'[!] Error fetching {url}: {type(e).__name__} - {e}')

    def save_links_to_json(self, filename: str) -> None:
        with open(filename, 'w', encoding="utf-8") as f:
            json.dump(self.__results, f, indent=2, ensure_ascii=False)
