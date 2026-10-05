"""The two Twitter API v1.1 operations used by this bot, with OAuth1 signing."""

from dataclasses import dataclass
import os

import requests_oauthlib


CREDENTIAL_NAMES = (
    "CONSUMER_KEY",
    "CONSUMER_SECRET",
    "ACCESS_TOKEN",
    "ACCESS_SECRET",
)
API_BASE = "https://api.twitter.com/1.1"


@dataclass(frozen=True)
class Tweet:
    text: str


class TwitterAPI:
    """Small adapter preserving this bot's timeline and posting interface."""

    def __init__(self, session):
        self.session = session

    def user_timeline(self, count=1):
        response = self.session.get(
            f"{API_BASE}/statuses/user_timeline.json",
            params={"count": count},
            timeout=30,
            allow_redirects=False,
        )
        response.raise_for_status()
        return [Tweet(text=item["text"]) for item in response.json()]

    def update_status(self, status):
        response = self.session.post(
            f"{API_BASE}/statuses/update.json",
            data={"status": status},
            timeout=30,
            allow_redirects=False,
        )
        response.raise_for_status()
        return response.json()


def create_api():
    """Read credentials from the environment without logging their values."""
    missing = [name for name in CREDENTIAL_NAMES if not os.environ.get(name)]
    if missing:
        raise RuntimeError("Missing Twitter credentials: " + ", ".join(missing))
    session = requests_oauthlib.OAuth1Session(
        os.environ["CONSUMER_KEY"],
        client_secret=os.environ["CONSUMER_SECRET"],
        resource_owner_key=os.environ["ACCESS_TOKEN"],
        resource_owner_secret=os.environ["ACCESS_SECRET"],
    )
    return TwitterAPI(session)
