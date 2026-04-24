from crawl import AsyncCrawler
import argparse
import asyncio

async def main_async():
    parser = argparse.ArgumentParser(description="Simple WebScraper")
    parser.add_argument("URL", help="Base URL")
    parser.add_argument("max_req", default=4, type=int, help="How many URLs are scanned concurrently. Default 4.")
    parser.add_argument("max_pages", default=-1, type=int, help="How many other URLs are scanned, besides the Base URL. By default, it scannes the whole website.")
    args = parser.parse_args()

    print(f"Starting crawl of: {args.URL}")
    
    async with AsyncCrawler(args.URL, max_requests = args.max_req, max_pages = args.max_pages) as crawler: 
        await crawler.crawl_site(args.URL)
    
    print(f"Scanned {len(crawler.page_data)} links on the website.")

if __name__ == "__main__":
    asyncio.run(main_async())
