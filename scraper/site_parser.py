# scraper/site_parser.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from knowledge.db import add_knowledge, clear_knowledge_by_source

GRANT_KEYWORDS = ["грант", "стипендия", "финансирование", "льгота", "скидка"]
DORM_KEYWORDS = ["общежитие", "проживание", "комната", "жильё"]
SPEC_KEYWORDS = ["специальность", "направление", "программа", "обучение", "квалификация"]

def categorize_section(text: str) -> str:
    t = text.lower()
    if any(kw in t for kw in GRANT_KEYWORDS):
        return "гранты"
    if any(kw in t for kw in DORM_KEYWORDS):
        return "общежитие"
    if any(kw in t for kw in SPEC_KEYWORDS):
        return "специальности"
    return "общее"

def extract_text_chunks(html: str, min_length: int = 30) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["nav", "footer", "header", "script", "style"]):
        tag.decompose()
    container = soup.find("main") or soup.find("body") or soup
    chunks = []
    for el in container.find_all(["p", "li", "h1", "h2", "h3", "td"]):
        text = el.get_text(" ", strip=True)
        if len(text) >= min_length:
            chunks.append(text)
    return chunks

def get_internal_links(base_url: str, html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    base_domain = urlparse(base_url).netloc
    links = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        if urlparse(href).netloc == base_domain:
            links.add(href.split("#")[0])
    return list(links)

async def parse_site(base_url: str, max_pages: int = 50):
    await clear_knowledge_by_source("site")
    visited: set[str] = set()
    to_visit = [base_url]
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (compatible; CollegeBot/1.0)"

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        try:
            resp = session.get(url, timeout=10)
            resp.raise_for_status()
        except Exception:
            continue
        visited.add(url)
        for chunk in extract_text_chunks(resp.text):
            await add_knowledge("site", categorize_section(chunk), chunk)
        for link in get_internal_links(base_url, resp.text):
            if link not in visited:
                to_visit.append(link)
