"""Post ramen updates when run explicitly, never at import time."""

from ramen import CLOSED, OPEN, SOLD_OUT, NekoRamen
from twy import create_api


PREFIXES = {
    OPEN: "本日営業\n",
    CLOSED: "本日休業\n",
    SOLD_OUT: "売り切れました\n",
}


def make_tweet(post):
    """Preserve the original wording and 140-character truncation policy."""
    prefix = PREFIXES.get(post.check_status())
    if prefix is None:
        return None
    tweet = prefix + post.content
    if len(tweet) > 140:
        tweet = tweet[:140] + "..."
    return tweet


def main():
    api = create_api()
    new_post = NekoRamen().get_latest_post()
    tweet = make_tweet(new_post)
    if tweet is None:
        print("No recognized status; nothing to tweet")
        return False

    # These v1.1 endpoints are subject to the account's current API access.
    timeline = api.user_timeline(count=1)
    if timeline and timeline[0].text.split()[:2] == tweet.split()[:2]:
        print("Already tweeted")
        return False

    api.update_status(status=tweet)
    print("New tweet posted")
    return True


if __name__ == "__main__":
    main()
