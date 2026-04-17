from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

def convert_html_to_object(html):
    pass

def normalize_urls(url: bytes | str):
    url_object = urlparse(url)

    return url_object.netloc + url_object.path.rstrip("/")

def get_heading_from_html(html:str):
    page = BeautifulSoup(html, 'html.parser')
    header = page.find('h1')
    if header is not None:
        return header.get_text()

    header = page.find('h2')
    if header is not None:
        return header.get_text()
    
    return None

def get_first_paragraph_from_html(html: str):
    page = BeautifulSoup(html, 'html.parser')
    main_html = page.find('main')
    if main_html is not None:
        first_paragraph = main_html.find('p')
        if first_paragraph is not None:
            return first_paragraph.get_text()
        
    first_paragraph = page.find('p')
    if first_paragraph is not None:
            return first_paragraph.get_text()
    
    if first_paragraph is None:
        return ""
    else:
        return first_paragraph
    
def get_urls_from_html(html: str, base_url: str):
    try:
        page = BeautifulSoup(html, "html.parser")
    except Exception as e:
        return f"Parser error: {e}"
    
    urls_list = []

    for a in page.find_all('a'):
        url = a.get('href')
        if url is None or url == "":
            continue
        
        if base_url not in url:
            if not url.startswith("mailto:"):
                url = urljoin(base_url, url)

        if url not in urls_list:
            urls_list.append(url)
    
    return urls_list

def get_images_from_html(html: str, base_url: str):
    try:
        page = BeautifulSoup(html, "html.parser")
    except Exception as e:
        return f"Parser error: {e}"
    
    img_list = []

    for a in page.find_all('img'):
        img = a.get('src')

        if img is None or img == "":
            img = a.get('srcset')
            if img is None or img == "":
                continue
        
        #remove leading and trailing whitespaces
        img = img.strip()
        #if link contains spaces, it's invalid
        if " " in img:
            continue
        
        #creates an absolute link from a relative one
        if base_url not in img:
            #ignore invalid links and <img> data attributes 
            if not img.startswith("/"):
                continue

            img = urljoin(base_url, img)

        #only unique entires
        if img not in img_list:
            img_list.append(img)

    return img_list

