# NekoRamen

A small ramen-blog scraper, optional Twitter posting script, and Bottle health
endpoint. The runtime targets Python 3.14; use the latest available 3.14 patch.

## Install and verify

`Pipfile` lists direct dependencies. `Pipfile.lock` locks runtime and development
dependencies, and `requirements.txt` is the hash-checked runtime export of that
lock. Do not edit the export separately.

```sh
python -m pip install pipenv==2026.8.0
pipenv sync --dev
pipenv run python -m unittest discover -s tests -v
pipenv run python -m pip check
pipenv run pip-audit -r requirements.txt --strict
```

For a runtime-only installation in an existing virtual environment:

```sh
python -m pip install --require-hashes -r requirements.txt
```

After intentionally changing dependencies:

```sh
pipenv lock
pipenv requirements --hash > requirements.txt
pipenv verify
```

Tests mock network requests and posting. They do not scrape the live blog, post
tweets, start a server, or deploy anything. CI checks the locked install, export
consistency, unit tests, and known dependency vulnerabilities. The historical
`analyze_neko.ipynb` is optional historical analysis: it needs a separate environment
with pandas, NumPy, and Jupyter. It is outside the deployed bot runtime and this
offline verification; compatibility of its old analysis cells has not been tested.

## Run explicitly

- `pipenv run python index.py` starts the health server on `PORT` (default 5000)
- `pipenv run python ramen.py` reads the live blog and updates `ramen.info`
- `pipenv run python tweet_neko_ramen.py` may publish a tweet

Importing the modules does not start a server, fetch the blog, or send a tweet.
The original status wording, duplicate check, and truncation behavior are retained.
Unknown statuses are skipped and an empty timeline can receive its first update.

## Twitter credentials and dormant deployments

Before ever resuming Twitter posting, revoke/rotate the previously committed
credentials in the provider account. Removing them from the current source does
not invalidate them or remove them from Git history. This update does not rewrite
history or rotate account credentials.

Configure `CONSUMER_KEY`, `CONSUMER_SECRET`, `ACCESS_TOKEN`, and `ACCESS_SECRET` in
your shell or the hosting environment. `.env.example` contains names only; the
application does not automatically load `.env`. Missing credentials fail with a
message listing names, never values. Do not commit real credentials.

The posting script retains the same Twitter API v1.1 timeline/posting endpoints;
actual availability depends on the account's current API plan and permissions.
Live API access and the blog's current layout are not verified by offline tests.
Tweepy has been replaced by a small `requests-oauthlib` adapter for just these two
operations, allowing OAuthlib 4.0.0 without overriding Tweepy's `<4` constraint.
This avoids carrying the known OAuthlib 3.x PKCE advisory (PYSEC-2026-4114), even
though this bot uses OAuth1 rather than an OAuth2 authorization server.
No automatic posting or deployment workflow is included. Disconnect any old
Heroku/GitHub integration in the relevant account before merging maintenance
changes if automatic deployment must stay disabled; a repository change alone
cannot disconnect an account integration.
