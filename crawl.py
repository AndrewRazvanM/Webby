from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from lxml import html
import requests
from time import sleep
from sys import exit as sys_exit

PARSING_ENGINE = 'lxml'
VERSION = 0.1
RECONNECT_ATTEMPS = 3
WAIT_BEFORE_RECONNECT = 0.5

def get_html(url: str) -> tuple[bytes, str]:

    for nr in range(RECONNECT_ATTEMPS):
        try:
            r = requests.get(url, headers={"User-Agent": f"WebbyCrawler /{VERSION}"})
            break
        except requests.exceptions.RequestException as e:
            if e.response is not None:
                if nr < RECONNECT_ATTEMPS - 1:
                    print(f"HTTP {e.response.status_code}: {e.response.reason}\nAttempt {nr}. Trying again...")
                else:
                    print(f"HTTP {e.response.status_code}: {e.response.reason}\nAttempt {nr}. Last try...")
            elif nr < RECONNECT_ATTEMPS - 1:
                print(f"Error: {e}\nAttempt {nr}. Trying again...")
            else:
                print(f"Error: {e}\nAttempt {nr}. Last Try...")
                    
            sleep(WAIT_BEFORE_RECONNECT)

        if nr == RECONNECT_ATTEMPS - 1:
            sys_exit(1)

    #makes sure page has proper content type
    try:
        if "text/html" not in r.headers["Content-Type"]:  # type: ignore
            print(f"Wrong Content-Type header : {r.headers["Content-Type"]}. Cannot scrape")  # type: ignore
            sys_exit(1)
    except KeyError:
        print(f"No Content-Type header on page. Cannot scrape")
        sys_exit(1)

    if r.encoding is None: # type: ignore
        encoding = "N/A"
    else:
        encoding = r.encoding # type: ignore
    
    return r._content, encoding # type: ignore

def convert_html_to_object(html):
    pass

def normalize_urls(url: str) -> str:
    url_object = urlparse(url)

    return url_object.netloc + url_object.path.rstrip("/") # type: ignore

def get_heading_from_html(html:str | bytes, encoding = "N/A") -> str:
    """Returns the heading from an html. If no heading is present, it wil lreturn an empty string."""
    try:
        if encoding == "N/A":
            page = BeautifulSoup(html, PARSING_ENGINE)
        else:
            page = BeautifulSoup(html, PARSING_ENGINE, from_encoding=f"{encoding}")
    except Exception as e:
        return f"Parser error: {e}"

    header = page.find('h1')
    if header is not None:
        return header.get_text().strip()

    header = page.find('h2')
    if header is not None:
        return header.get_text().strip()
    
    return ""

def get_first_paragraph_from_html(html: str | bytes, encoding = "N/A") -> str:
    """Returns the firs paragraph from an html. If no paragraph is present, it will return an empty string."""
    try:
        if encoding == "N/A":
            page = BeautifulSoup(html, PARSING_ENGINE)
        else:
            page = BeautifulSoup(html, PARSING_ENGINE, from_encoding=f"{encoding}")
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
    
def get_urls_from_html(html: str | bytes, base_url: str, keep_fragments = False, encoding = "N/A") -> list[str]:
    """Return all the urls from an html. 
        If no url is present, it wil lreturn an empty list.
        If there's an error while parsing, it will output a list of len 1 with the error message.
        If keep_fragments is True, then fragments will be preserved. Otherwise, they are dropped"""
    try:
        if encoding == "N/A":
            page = BeautifulSoup(html, PARSING_ENGINE)
        else:
            page = BeautifulSoup(html, PARSING_ENGINE, from_encoding=f"{encoding}")
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

def get_images_from_html(html: str | bytes, base_url: str, encoding = "N/A") -> list[str]:
    """Return all the images urls from an html. Data attributes are ignored.
        If no image url is present, it wil lreturn an empty list.
        If there's an error while parsing, it will output a list of len 1 with the error message."""
    try:
        if encoding == "N/A":
            page = BeautifulSoup(html, PARSING_ENGINE)
        else:
            page = BeautifulSoup(html, PARSING_ENGINE, from_encoding=f"{encoding}")
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

def extract_page_data(html: str | bytes, base_url:str, encoding: str, keep_fragments = False):

    page_data = {
        "url": base_url,
        "heading": get_heading_from_html(html, encoding),
        "first_paragraph": get_first_paragraph_from_html(html, encoding),
        "outgoing_links": get_urls_from_html(html, base_url, keep_fragments, encoding),
        "image_urls": get_images_from_html(html, base_url, encoding),
    }

    return page_data

def crawl_page(base_url: str):
    """
    Crawls a single page and all the links on it (depth = 1). Does not branch to other pages.
    """
    parsed_base_url = urlparse(base_url)
    page_data = {}

    #crawl through base_url page
    current_url_norm = normalize_urls(base_url)
    parsed_current_url = urlparse(base_url)

    print(f"Retrieving Page...")
    byte_html, encoding = get_html(base_url)
    print("Page succesfully retrieved. Getting page data...")
    page_data[current_url_norm] = extract_page_data(byte_html, base_url, encoding)
    print(f"Got page data. Moving to next page...")

    #crawl through all links on that page
    for url in page_data[current_url_norm]["outgoing_links"]:
        current_url_norm = normalize_urls(url)
        parsed_current_url = urlparse(url)

        if current_url_norm in page_data:
            continue
            
        if parsed_current_url.netloc != parsed_base_url.netloc:
            continue

        print(f"Crawling next page: {url}")
        print(f"Retrieving Page...")
        byte_html, encoding = get_html(url)

        print("Page succesfully retrieved. Getting page data...")
        page_data[current_url_norm] = extract_page_data(byte_html, base_url, encoding)
        print(f"Got page data. Moving to next page...")

    return page_data

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

    def push (self, website: str, website_norm_url: str):
        self.items.append(website)
        self.seen.add(website_norm_url)
        self.len += 1

    def pop (self) -> str:
        if self. len > 0:
            self.len -= 1
            return self.items.pop(0)
        else:
            return ""
        
    def peek(self):
        if self.len > 0:
            return self.items[self.len - 1]
        else:
            return None
        
    def size(self):
        return self.len
    
    def was_in_queue(self, website:str) -> bool:
        if website in self.seen:
            return True
        else:
            return False

def crawl_website(base_url: str):
    """
    Crawls a whole website and all the links on it. Branches to all links that point to the same domain.
    """

    current_url =  base_url
    page_data = {}

    parsed_base_url = urlparse(base_url)
    base_url_norm = normalize_urls(base_url)

    crawl_queue = Queue()
    crawl_queue.push(current_url, base_url_norm)

    while crawl_queue.len > 0:
        #get next item from queue
        current_url = crawl_queue.pop()   
            
        #get html page and normalize the url
        print(f"Retrieving Page...")
        html_byte, encoding = get_html(current_url)
        current_url_norm = normalize_urls(current_url)

        #extract data from page and store it if it's not already saved
        print("Page succesfully retrieved. Getting page data...")
        data = extract_page_data(html_byte, current_url, encoding)
        if current_url_norm not in page_data:
            page_data[current_url_norm]  = data
        
        print(f"Got page data. Analyzing outgoing links...")

        #crawl through all links on that page
        for out_url in page_data[current_url_norm]["outgoing_links"]:
            print(f"Checking {out_url}")
            next_parsed_url = urlparse(out_url)
            next_norm_url = normalize_urls(out_url)

            #check that's it's on the same domain
            print(f"New domain {next_parsed_url.netloc} compared to base domain {parsed_base_url.netloc}")
            if next_parsed_url.netloc != parsed_base_url.netloc:
                continue
            
            #check to see if it's already in the queue
            if out_url not in crawl_queue.items and not crawl_queue.was_in_queue(next_norm_url):
                print(f"Added {out_url} to the crawl queue")
                crawl_queue.push(out_url, next_norm_url)

        if crawl_queue.len == 1:
            print(f"Finished scanning the domain {parsed_base_url.netloc}")
        

