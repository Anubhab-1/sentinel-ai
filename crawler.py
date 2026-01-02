import asyncio
import logging
from urllib.parse import urlparse, urljoin
import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

async def fetch_links(session, url):
    """
    Fetches a URL and extracts all same-domain links.
    Returns: (set_of_links, error_message)
    """
    try:
        async with session.get(url, timeout=5, allow_redirects=True) as response:
            if response.status != 200:
                return set(), f"Status {response.status}"
            
            # Content check
            ctype = response.headers.get("Content-Type", "").lower()
            if "text/html" not in ctype:
                return set(), "Not HTML"

            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            
            extracted = set()
            base_netloc = urlparse(url).netloc

            for a in soup.find_all("a", href=True):
                href = a['href']
                full_url = urljoin(url, href)
                parsed = urlparse(full_url)
                
                # Cleanup: Remove fragments and queries for crawling consistency
                clean_url = parsed.scheme + "://" + parsed.netloc + parsed.path
                if clean_url.endswith("/"):
                    clean_url = clean_url[:-1]

                # Filter: Same Domain, HTTP/S only
                if parsed.netloc == base_netloc and parsed.scheme in ["http", "https"]:
                    extracted.add(clean_url)
            
            return extracted, None

    except Exception as e:
        logger.warning(f"Crawl error on {url}: {e}")
        return set(), str(e)


async def crawl(start_url, max_pages=15, max_depth=2):
    """
    BFS Crawler to find pages on the same domain.
    """
    # Normalize start
    parsed_start = urlparse(start_url)
    base_domain = parsed_start.netloc
    start_url = start_url.rstrip("/")

    visited = set()
    queue = [(start_url, 0)] # (url, depth)
    results = set()

    async with aiohttp.ClientSession() as session:
        while queue and len(visited) < max_pages:
            current_url, depth = queue.pop(0)
            
            if current_url in visited:
                continue
            
            visited.add(current_url)
            results.add(current_url)
            
            # If we haven't reached max depth, fetch children
            if depth < max_pages:
                links, err = await fetch_links(session, current_url)
                if not err:
                    for link in links:
                        if link not in visited:
                            queue.append((link, depth + 1))
            
            # Tiny sleep to be nice
            await asyncio.sleep(0.1)

    # Ensure start_url is definitely in results
    if start_url in results:
        # Move it to front if we returned a list, but for set it doesn't matter.
        pass
    
    logger.info(f"🕸️ Spider finished. Explored {len(results)} pages on {base_domain}")
    return list(results)
