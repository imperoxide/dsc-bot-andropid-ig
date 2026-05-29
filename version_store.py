import json
import os

STORE_FILE = "version_data.json"


def load_data():
    if not os.path.exists(STORE_FILE):
        return {}
    try:
        with open(STORE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_data(data: dict):
    with open(STORE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_known_version() -> str | None:
    return load_data().get("latest_version")


def set_known_version(version: str):
    data = load_data()
    data["latest_version"] = version
    save_data(data)


def get_tracked_channel() -> int | None:
    val = load_data().get("channel_id")
    return int(val) if val else None


def set_tracked_channel(channel_id: int):
    data = load_data()
    data["channel_id"] = channel_id
    save_data(data)


def get_check_interval() -> int:
    return int(load_data().get("check_interval", 300))


def set_check_interval(seconds: int):
    data = load_data()
    data["check_interval"] = seconds
    save_data(data)
