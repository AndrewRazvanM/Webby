from urllib.parse import urlparse
from bs4 import BeautifulSoup

def convert_html_to_object(html):
    pass

def normalize_urls(url):
    url_object = urlparse(url)

    return url_object.netloc + url_object.path.rstrip("/")

def get_heading_from_html(html):
    page = BeautifulSoup(html, 'html.parser')
    header = page.find('h1')
    if header is not None:
        return header.get_text()

    header = page.find('h2')
    if header is not None:
        return header.get_text()
    
    return None

def get_first_paragraph_from_html(html):
    page = BeautifulSoup(html, 'html.parser')
    main = page.find('main')
    if main is not None:
        first_paragraph = main.find('p')
        if first_paragraph is not None:
            return first_paragraph.get_text()
        
    first_paragraph = page.find('p').get_text()
    if first_paragraph is None:
        return ""
    else:
        return first_paragraph