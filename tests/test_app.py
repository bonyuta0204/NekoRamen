"""Offline regression tests: no real scrape, tweet, browser, or web server."""

import datetime
import importlib
import json
from io import BytesIO
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from wsgiref.util import setup_testing_defaults

from bs4 import BeautifulSoup
from PIL import Image
import requests

# Block side effects during test discovery as well as during individual tests.
with (
    patch("requests.sessions.Session.send", side_effect=AssertionError("Network is disabled in tests")),
    patch("socket.socket.connect", side_effect=AssertionError("Network is disabled in tests")),
    patch("bottle.run", side_effect=AssertionError("A server must not start on import")),
    patch("requests_oauthlib.OAuth1Session", side_effect=AssertionError("Authentication must be lazy")),
):
    import index
    import ramen
    import ScrapingFunctions
    import tweet_neko_ramen
    import twy


class OfflineTestCase(unittest.TestCase):
    def setUp(self):
        # A forgotten mock must fail locally rather than send a real request.
        for target in ("requests.sessions.Session.send", "socket.socket.connect"):
            blocker = patch(target, side_effect=AssertionError("Network is disabled in tests"))
            blocker.start()
            self.addCleanup(blocker.stop)


def make_post(status=ramen.OPEN, content=None):
    post = ramen.Post()
    post.set_time("2026年10月4日 09時30分")
    post.set_title("売り切れです" if status == ramen.SOLD_OUT else "本日の営業")
    post.set_content(content or {
        ramen.OPEN: "本日営業いたします",
        ramen.CLOSED: "本日は休みとなります",
        ramen.SOLD_OUT: "ありがとうございました",
        None: "お知らせ",
    }[status])
    return post


class ScrapingTests(OfflineTestCase):
    def test_html5lib_parses_links_and_ignores_missing_href(self):
        response = Mock(content=b'<a href="/blog">Blog</a><a>Blank</a><a href="/shop">Shop</a>')
        with patch("ScrapingFunctions.requests.get", return_value=response) as get:
            self.assertEqual(ScrapingFunctions.find_link("https://example.test"), ["/blog", "/shop"])
            self.assertEqual(ScrapingFunctions.find_link("https://example.test", ["blog"]), ["/blog"])
        get.assert_called_with("https://example.test", timeout=30)
        self.assertEqual(response.raise_for_status.call_count, 2)

    def test_http_errors_propagate(self):
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError("failed")
        with patch("ScrapingFunctions.requests.get", return_value=response):
            with self.assertRaises(requests.HTTPError):
                ScrapingFunctions.make_soup("https://example.test")

    def test_image_helper_uses_pillow(self):
        content = BytesIO()
        Image.new("RGB", (2, 3), "red").save(content, "PNG")
        response = Mock(content=content.getvalue())
        with patch("ScrapingFunctions.requests.get", return_value=response) as get:
            result = ScrapingFunctions.get_image("https://example.test/image.png")
        self.assertEqual(result.size, (2, 3))
        get.assert_called_once_with("https://example.test/image.png", timeout=30)
        response.raise_for_status.assert_called_once_with()

    def test_browser_helper_does_not_invoke_a_shell(self):
        with patch("ScrapingFunctions.webbrowser.open", return_value=True) as open_browser:
            self.assertTrue(ScrapingFunctions.open_browser("https://example.test/?q=a;b"))
        open_browser.assert_called_once_with("https://example.test/?q=a;b")


class RamenTests(OfflineTestCase):
    def test_status_classification(self):
        for status in (ramen.OPEN, ramen.CLOSED, ramen.SOLD_OUT):
            with self.subTest(status=status):
                self.assertEqual(make_post(status).check_status(), status)
        self.assertFalse(make_post(None).check_status())

    def test_timestamp_parsing(self):
        self.assertEqual(make_post().post_time, datetime.datetime(2026, 10, 4, 9, 30))

    def test_latest_post_from_fixture(self):
        soup = BeautifulSoup('''<div class="blogBlock"><h2>2026年10月4日 09時30分</h2>
            <p>本日の営業</p><div class="blogP">本日営業いたします</div></div>''', "html5lib")
        with patch("ramen.ScrapingFunctions.make_soup", return_value=soup):
            neko = ramen.NekoRamen("https://example.test")
            self.assertEqual(neko.get_latest_post().check_status(), ramen.OPEN)
            self.assertIn("blogBlock", str(neko))

    def check_timestamp_file(self, content):
        neko = object.__new__(ramen.NekoRamen)
        neko.get_latest_post = Mock(return_value=make_post())
        with tempfile.TemporaryDirectory() as directory:
            previous = os.getcwd()
            try:
                os.chdir(directory)
                if content is not None:
                    Path("ramen.info").write_text(content)
                result = neko.check_update()
                datetime.datetime.fromisoformat(Path("ramen.info").read_text())
                self.assertFalse(Path("should_not_exist").exists())
                return result
            finally:
                os.chdir(previous)

    def test_iso_timestamp_detects_new_post(self):
        self.assertTrue(self.check_timestamp_file("2026-10-03T00:00:00"))

    def test_legacy_timestamp_remains_readable(self):
        self.assertTrue(self.check_timestamp_file("datetime.datetime(2026, 10, 3, 0, 0, 0, 1234)"))

    def test_newer_timestamp_detects_no_update(self):
        self.assertFalse(self.check_timestamp_file("2026-10-05T00:00:00"))

    def test_missing_timestamp_is_recreated(self):
        self.assertTrue(self.check_timestamp_file(None))

    def test_corrupt_timestamp_is_not_evaluated(self):
        self.assertTrue(self.check_timestamp_file("__import__('pathlib').Path('should_not_exist').touch()"))


class TwitterTests(OfflineTestCase):
    def test_missing_credentials_fail_without_values(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "Missing Twitter credentials: CONSUMER_KEY"):
                twy.create_api()

    def test_blank_credentials_are_rejected(self):
        with patch.dict(os.environ, dict.fromkeys(twy.CREDENTIAL_NAMES, ""), clear=True):
            with self.assertRaises(RuntimeError):
                twy.create_api()

    def test_oauth1_client_accepts_environment_credentials(self):
        # Dummy values cannot authorize any account and no network is allowed.
        with patch.dict(os.environ, dict.fromkeys(twy.CREDENTIAL_NAMES, "test-placeholder"), clear=True):
            api = twy.create_api()
        self.assertTrue(callable(api.user_timeline))
        self.assertTrue(callable(api.update_status))
        self.assertEqual(type(api.session).__name__, "OAuth1Session")

    def make_api(self):
        with patch.dict(os.environ, dict.fromkeys(twy.CREDENTIAL_NAMES, "test-placeholder"), clear=True):
            return twy.create_api()

    def mock_response(self, payload, status=200):
        response = requests.Response()
        response.status_code = status
        response._content = json.dumps(payload).encode()
        response.headers["Content-Type"] = "application/json"
        return response

    def test_timeline_request_is_signed_and_parses_tweets(self):
        api = self.make_api()
        with patch.object(api.session, "send", return_value=self.mock_response([{"text": "previous tweet"}])) as send:
            timeline = api.user_timeline(count=1)
        self.assertEqual([tweet.text for tweet in timeline], ["previous tweet"])
        request = send.call_args.args[0]
        self.assertEqual(request.method, "GET")
        self.assertEqual(request.url, "https://api.twitter.com/1.1/statuses/user_timeline.json?count=1")
        self.assertTrue(request.headers["Authorization"].startswith(b"OAuth "))
        self.assertIn(b"oauth_signature=", request.headers["Authorization"])
        self.assertEqual(send.call_args.kwargs["timeout"], 30)
        self.assertFalse(send.call_args.kwargs["allow_redirects"])

    def test_post_request_is_signed_and_preserves_unicode_text(self):
        from urllib.parse import parse_qs
        api = self.make_api()
        with patch.object(api.session, "send", return_value=self.mock_response({"id": 123})) as send:
            result = api.update_status(status="本日営業\nラーメン")
        self.assertEqual(result, {"id": 123})
        request = send.call_args.args[0]
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.url, "https://api.twitter.com/1.1/statuses/update.json")
        body = request.body.decode("utf-8") if isinstance(request.body, bytes) else request.body
        self.assertEqual(parse_qs(body), {"status": ["本日営業\nラーメン"]})
        self.assertTrue(request.headers["Authorization"].startswith(b"OAuth "))
        self.assertIn(b"oauth_signature=", request.headers["Authorization"])
        self.assertEqual(send.call_args.kwargs["timeout"], 30)
        self.assertFalse(send.call_args.kwargs["allow_redirects"])

    def test_adapter_returns_empty_timeline(self):
        api = self.make_api()
        with patch.object(api.session, "send", return_value=self.mock_response([])):
            self.assertEqual(api.user_timeline(), [])

    def test_adapter_http_errors_propagate_without_retry(self):
        for method, arguments in (("user_timeline", {}), ("update_status", {"status": "test"})):
            with self.subTest(method=method):
                api = self.make_api()
                with patch.object(api.session, "send", return_value=self.mock_response({}, 403)) as send:
                    with self.assertRaises(requests.HTTPError):
                        getattr(api, method)(**arguments)
                send.assert_called_once()

    def test_adapter_timeout_propagates_without_retry(self):
        api = self.make_api()
        with patch.object(api.session, "send", side_effect=requests.Timeout("timed out")) as send:
            with self.assertRaises(requests.Timeout):
                api.update_status("test")
        send.assert_called_once()

    def test_wording_and_truncation_are_preserved(self):
        for status, prefix in tweet_neko_ramen.PREFIXES.items():
            with self.subTest(status=status):
                post = make_post(status)
                self.assertEqual(tweet_neko_ramen.make_tweet(post), prefix + post.content)
        post = make_post(content="営業いたします" + "あ" * 200)
        self.assertEqual(tweet_neko_ramen.make_tweet(post), ("本日営業\n" + post.content)[:140] + "...")
        self.assertIsNone(tweet_neko_ramen.make_tweet(make_post(None)))

    def run_main(self, timeline, post=None):
        api = Mock()
        api.user_timeline.return_value = timeline
        with patch("tweet_neko_ramen.create_api", return_value=api), patch("tweet_neko_ramen.NekoRamen") as neko:
            neko.return_value.get_latest_post.return_value = post or make_post()
            result = tweet_neko_ramen.main()
        return api, result

    def test_duplicate_tweet_is_skipped(self):
        tweet = tweet_neko_ramen.make_tweet(make_post())
        api, result = self.run_main([SimpleNamespace(text=tweet)])
        self.assertFalse(result)
        api.user_timeline.assert_called_once_with(count=1)
        api.update_status.assert_not_called()

    def test_new_tweet_is_posted_through_mock(self):
        api, result = self.run_main([SimpleNamespace(text="previous status")])
        self.assertTrue(result)
        api.update_status.assert_called_once_with(status="本日営業\n本日営業いたします")

    def test_empty_timeline_can_post_first_tweet(self):
        api, result = self.run_main([])
        self.assertTrue(result)
        api.update_status.assert_called_once()

    def test_unknown_status_does_not_call_twitter(self):
        api, result = self.run_main([], make_post(None))
        self.assertFalse(result)
        api.user_timeline.assert_not_called()
        api.update_status.assert_not_called()


class ImportAndWebTests(OfflineTestCase):
    def test_import_has_no_authentication_network_or_server_side_effect(self):
        with patch.dict(os.environ, {}, clear=True), patch("bottle.run") as run, patch("requests_oauthlib.OAuth1Session") as auth:
            for module in (twy, tweet_neko_ramen, index):
                importlib.reload(module)
        run.assert_not_called()
        auth.assert_not_called()

    def test_health_endpoint_via_wsgi(self):
        environ = {}
        setup_testing_defaults(environ)
        start_response = Mock()
        response = index.app(environ, start_response)
        try:
            body = b"".join(response)
        finally:
            if hasattr(response, "close"):
                response.close()
        self.assertEqual(body, b"hello world")
        self.assertEqual(start_response.call_args.args[0], "200 OK")


if __name__ == "__main__":
    unittest.main()
