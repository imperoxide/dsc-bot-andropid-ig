import requests
from bs4 import BeautifulSoup
import re

APKMIRROR_URL = "https://www.apkmirror.com/apk/roblox-corporation/roblox/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}


def fetch_latest_release():
    """
    Scrapes APKMirror for the latest Roblox Android release.
    Returns a dict with version info or None on failure.
    """
    try:
        response = requests.get(APKMIRROR_URL, headers=HEADERS, timeout=20)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[Scraper] Request failed: {e}")
        return None

    soup = BeautifulSoup(response.text, "lxml")

    # Each release is inside an article with class "appRow"
    releases = soup.select("div.appRow")
    if not releases:
        # Fallback selector
        releases = soup.select("div[class*='appRow']")

    if not releases:
        print("[Scraper] No releases found on page.")
        return None

    first = releases[0]

    # Version name link
    title_tag = first.select_one("h5.appRowTitle a")
    if not title_tag:
        title_tag = first.select_one("a[class*='fontBlack']")

    if not title_tag:
        print("[Scraper] Could not find release title.")
        return None

    title = title_tag.get_text(strip=True)
    link = title_tag.get("href", "")
    if link and not link.startswith("http"):
        link = "https://www.apkmirror.com" + link

    # Try to extract the version number from title
    version_match = re.search(r"(\d[\d.]+\d)", title)
    version = version_match.group(1) if version_match else title

    # Date published
    date_tag = first.select_one("span.dateyear_utc") or first.select_one("time")
    date_str = ""
    if date_tag:
        date_str = date_tag.get("data-utcdate", "") or date_tag.get_text(strip=True)

    # Release type tag (e.g. "release", "beta")
    tag_el = first.select_one("span.apkm-badge") or first.select_one("span[class*='badge']")
    release_type = tag_el.get_text(strip=True) if tag_el else "release"

    return {
        "version": version,
        "title": title,
        "url": link,
        "date": date_str,
        "type": release_type,
    }
