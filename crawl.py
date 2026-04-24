from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from lxml import html
from time import sleep, monotonic
from sys import exit as sys_exit
import asyncio
import aiohttp

PARSING_ENGINE = 'lxml'
VERSION = 0.1
RECONNECT_ATTEMPS = 2
WAIT_BEFORE_RECONNECT = 0.5
NR_BATCH_CONNECTIONS = 10


class Queue:
    __slots__ = (
        "items",
        "seen",
        "len",
        )
    
    def __init__ (self):
        self.items = []
        self.len = 0
        self.seen = set()

    def push (self, website:str, website_norm_url: str):
        self.items.append(website)
        self.seen.add(website_norm_url)
        self.len += 1

    def pop (self) -> str :
        if self. len > 0:
            self.len -= 1
            return self.items.pop(0)
        else:
            return ""
        
    def peek(self) -> str:
        if self.len > 0:
            return self.items[self.len - 1]
        else:
            return ""
        
    def size(self) -> int:
        return self.len
    
    def was_in_queue(self, website:str) -> bool:
        if website in self.seen:
            return True
        else:
            return False
        
class AsyncCrawler:

    def __init__(self, base_url: str, max_requests = 4, max_pages = -1):
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self.page_data = {}
        self.lock = asyncio.Lock()
        self.crawl_queue = Queue()
        self.max_pages = max_pages
        self.semaphore = asyncio.Semaphore(max_requests)

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers={"User-Agent": f"WebbyCrawler/{VERSION}"})
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def add_page_visit(self, normalized_url: str) -> bool:
        lock = self.lock

        async with lock:
            if normalized_url in self.page_data:
                return False
            else:
                self.page_data[normalized_url] = None
                return True
            
    async def get_html(self, url: str) -> str | None:
        
        for nr in range(RECONNECT_ATTEMPS):
            try:
                async with self.session.get(url) as resp:
                    resp.raise_for_status()
                    #makes sure page has proper content type
                    if not resp.content_type.startswith("text/html"): 
                        print(f"Wrong Content-Type header : {resp.content_type}. Cannot scrape {url}")
                        return None
                            
                    text = await resp.text()
                            
                    return text
                
            except aiohttp.ClientResponseError as e:
                print(f"HTTP Error {e.status}: {e.message}")
                await asyncio.sleep(WAIT_BEFORE_RECONNECT)

            except aiohttp.ClientConnectorError as e:
                print(f"DNS error: {e}")
                await asyncio.sleep(WAIT_BEFORE_RECONNECT)

            except aiohttp.ClientError as e:
                print(f"Error {e}")
                await asyncio.sleep(WAIT_BEFORE_RECONNECT)
            
        return None
    
    async def crawl_site(self, new_url: str):
        max_pages = self.max_pages
        parsed_base_url = urlparse(new_url)
        base_url_norm = normalize_urls(new_url)
        
        crawl_queue = self.crawl_queue
        crawl_queue.push(new_url, base_url_norm)

        while crawl_queue.len > 0:
            # batch requests
            batch = []
            for _ in range(NR_BATCH_CONNECTIONS):
                url = crawl_queue.pop()
                if url == "":
                    continue
                normalized_url = normalize_urls(url)
                if await self.add_page_visit(normalized_url):
                    print(f"Scanning {url}")
                    batch.append(url)

            # fire all concurrently
            tasks = [asyncio.create_task(self.get_html(url)) for url in batch]
            results = await asyncio.gather(*tasks)  # all run at same time

            # process results, queue new urls
            for url, html_raw in zip(batch, results):
                if html_raw is None:
                    continue
                norm = normalize_urls(url)
                parsed = extract_page_data(html_raw, url)
            
                async with self.lock:
                    print(f"URL {url} was parsed and stored")
                    self.page_data[norm] = parsed

                if max_pages >= 0 and len(self.page_data) > max_pages:
                    print("Maximum number of URLs scanned. Stopping...")
                    return self.page_data

                for out_url in parsed["outgoing_links"]:
                    if urlparse(out_url).netloc == parsed_base_url.netloc:
                        next_norm = normalize_urls(out_url)
                        if not crawl_queue.was_in_queue(next_norm):
                            crawl_queue.push(out_url, next_norm)
    
    async def crawl(self):
        pass

def convert_html_to_object(html):
    pass

def normalize_urls(url: str) -> str:
    url_object = urlparse(url)

    return url_object.netloc + url_object.path.rstrip("/") # type: ignore

def get_heading_from_html(html:str) -> str:
    """Returns the heading from an html. If no heading is present, it wil lreturn an empty string."""
    try:

        page = BeautifulSoup(html, PARSING_ENGINE)

    except Exception as e:
        return f"Parser error: {e}"

    header = page.find('h1')
    if header is not None:
        return header.get_text().strip()

    header = page.find('h2')
    if header is not None:
        return header.get_text().strip()
    
    return ""

def get_first_paragraph_from_html(html: str) -> str:
    """Returns the firs paragraph from an html. If no paragraph is present, it will return an empty string."""
    try:

        page = BeautifulSoup(html, PARSING_ENGINE)

    except Exception as e:
        return f"Parser error: {e}"

    main_html = page.find('main')
    if main_html is not None:
        first_paragraph = main_html.find('p') # type: ignore
        if first_paragraph is not None:
            return first_paragraph.get_text().strip() # type: ignore
        
    first_paragraph = page.find('p')
    if first_paragraph is not None:
            return first_paragraph.get_text().strip()
    
    if first_paragraph is None:
        return ""
    else:
        return first_paragraph
    
def get_urls_from_html(html: str, base_url: str, keep_fragments = False) -> list[str]:
    """Return all the urls from an html. 
        If no url is present, it wil lreturn an empty list.
        If there's an error while parsing, it will output a list of len 1 with the error message.
        If keep_fragments is True, then fragments will be preserved. Otherwise, they are dropped"""
    try:
        
        page = BeautifulSoup(html, PARSING_ENGINE)

    except Exception as e:
        return [f"Parser error: {e}"]
    
    urls_list = []

    for a in page.find_all('a'):
        href = a.get('href') # type: ignore
        if href is None or href == "":
            continue
        
        #removes trailing and leading whitespaces
        url: str = href.strip() # type: ignore
        #ignores broken links
        if " " in url:
            url.replace(" ", "%20")

        #ignore non http schemes
        if url.startswith("mailto:") or url.startswith("javascript:"):
            continue
        
        url = urljoin(base_url, url, keep_fragments)
        #decides if fragments are kept
        if "#" in url and keep_fragments is False:
            fragment_index = url.index("#")
            url = url[:fragment_index]

        if url not in urls_list:
            urls_list.append(url)
    
    return urls_list

def get_images_from_html(html: str, base_url: str) -> list[str]:
    """Return all the images urls from an html. Data attributes are ignored.
        If no image url is present, it wil lreturn an empty list.
        If there's an error while parsing, it will output a list of len 1 with the error message."""
    try:
            
            page = BeautifulSoup(html, PARSING_ENGINE)

    except Exception as e:
        return [f"Parser error: {e}"]
    
    img_list = []
    parsed_base_url = urlparse(base_url)

    for a in page.find_all('img'):
        img: str = a.get('src') # type: ignore

        if img is None or img == "":
            img: str = a.get('srcset') # type: ignore
            if img is None or img == "":
                continue
            else:
                img = img.strip()
                #if srcset contains spaces, remove descriptors
                if " " in img: 
                    images_list = img.split(",")
                    for srcset_img in images_list:
                        parts = srcset_img.split()
                        img_url = parse_single_image_url(parts[0], base_url)
                        if img_url is None:
                            continue
                        #only valid and unique entires
                        if img not in img_list:
                            img_list.append(img_url)
                else:
                    img_url = parse_single_image_url(img, base_url)

        else:
            img_url = parse_single_image_url(img, base_url)
            #only unique entires
            if img_url is not None and img_url not in img_list:
                img_list.append(img_url)

    return img_list

def parse_single_image_url(url: str, base_url:str) -> str | None:
    #remove leading and trailing whitespaces
    img = url.strip()
    #if link contains spaces, it's invalid
    if " " in img:
        return None
            
    parsed_img = urlparse(img) 
    #ignore invalid links and <img> data attributes 
    if img.startswith("data"):
        return None
    #creates an absolute link from a relative path
    disable_fragments = False
    img =  urljoin(base_url, img, disable_fragments)

    if "#" in img:
        fragment_index = img.index("#")
        img = img[:fragment_index]
        
    return img

def extract_page_data(html: str, base_url:str, keep_fragments = False) -> dict[str, str | list[str]]:

    page_data = {
        "url": base_url,
        "heading": get_heading_from_html(html),
        "first_paragraph": get_first_paragraph_from_html(html),
        "outgoing_links": get_urls_from_html(html, base_url, keep_fragments),
        "image_urls": get_images_from_html(html, base_url),
    }

    return page_data

