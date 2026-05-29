import requests
import re

GOOGLE_PLAY_URL = "https://play.google.com/store/apps/details?id=com.roblox.client&hl=en"
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
    """
    Build a best-guess APKMirror link for a given version.
    e.g. 2.718.1110 -> /apk/roblox-corporation/roblox/roblox-2-718-1110-release/
    """
    slug = version.replace(".", "-")
    return f"{APKMIRROR_BASE}roblox-{slug}-release/"


def fetch_latest_release() -> dict | None:
    """
    Fetches the latest Roblox Android version from Google Play Store.
    Returns a dict with version info or None on failure.
    """
    try:
        response = requests.get(GOOGLE_PLAY_URL, headers=HEADERS, timeout=20)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[Scraper] Request failed: {e}")
        return None

    text = response.text

    # Roblox uses a 2.NNN.NNN versioning scheme on Android
    versions = re.findall(r"\b(2\.\d{3,4}\.\d{3,4})\b", text)
    if not versions:
        print("[Scraper] No version numbers found in page.")
        return None

    unique = list(set(versions))
    latest = max(unique, key=_version_tuple)

    return {
        "version": latest,
        "title": f"Roblox {latest}",
        "url": _apkmirror_link(latest),
        "apkmirror_listing": APKMIRROR_BASE,
        "date": "",
        "type": "release",
        "source": "Google Play",
    }
