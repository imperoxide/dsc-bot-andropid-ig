import requests
import re

# Check multiple regions — some roll out updates earlier than others
GOOGLE_PLAY_REGIONS = [
    "https://play.google.com/store/apps/details?id=com.roblox.client&hl=en&gl=GB",
    "https://play.google.com/store/apps/details?id=com.roblox.client&hl=en&gl=US",
    "https://play.google.com/store/apps/details?id=com.roblox.client&hl=en&gl=CA",
]

APKMIRROR_BASE = "https://www.apkmirror.com/apk/roblox-corporation/roblox/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _version_tuple(v: str):
    try:
        return tuple(int(x) for x in v.split("."))
    except ValueError:
        return (0, 0, 0)


def _apkmirror_link(version: str) -> str:
    slug = version.replace(".", "-")
    return f"{APKMIRROR_BASE}roblox-{slug}-release/"


def fetch_latest_release() -> dict | None:
    """
    Fetches the latest Roblox Android version by checking Google Play across
    multiple regions and taking the highest version number found.
    Returns a dict with version info or None on failure.
    """
    all_versions = []

    for url in GOOGLE_PLAY_REGIONS:
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            matches = re.findall(r"\b(2\.\d{3,4}\.\d{3,4})\b", response.text)
            all_versions.extend(matches)
        except requests.RequestException as e:
            print(f"[Scraper] Failed for {url}: {e}")
            continue

    if not all_versions:
        print("[Scraper] No version numbers found across all regions.")
        return None

    latest = max(set(all_versions), key=_version_tuple)

    return {
        "version": latest,
        "title": f"Roblox {latest}",
        "url": _apkmirror_link(latest),
        "apkmirror_listing": APKMIRROR_BASE,
        "date": "",
        "type": "release",
        "source": "Google Play",
    }
