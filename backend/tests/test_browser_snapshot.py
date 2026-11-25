from dataclasses import dataclass

import pytest

from backend.app.services.browser_snapshot import BrowserSnapshotError, BrowserSnapshotService


@dataclass
class FakePage:
    url: str = "https://example.com/final"
    closed: bool = False

    def goto(self, url, *, timeout_ms):
        assert timeout_ms == 15000
        return 200

    def title(self):
        return "Example"

    def screenshot(self, *, full_page):
        assert full_page is True
        return b"PNG"

    def content(self):
        return "<html><title>Example</title></html>"

    def close(self):
        self.closed = True


@dataclass
class FakeContext:
    page: FakePage
    accept_downloads: bool | None = None
    closed: bool = False

    def new_page(self):
        return self.page

    def close(self):
        self.closed = True


class FakeFactory:
    def __init__(self, context):
        self.context = context
        self.closed = False

    def new_context(self, *, accept_downloads):
        self.context.accept_downloads = accept_downloads
        return self.context

    def close(self):
        self.closed = True


def test_capture_returns_metadata_and_always_closes_browser_resources():
    page = FakePage()
    context = FakeContext(page)
    service = BrowserSnapshotService(
        factory=FakeFactory(context),
        resolver=lambda hostname: ["93.184.216.34"],
    )

    snapshot = service.capture("https://example.com/#home")

    assert snapshot.normalized_url == "https://example.com/"
    assert snapshot.final_url == "https://example.com/final"
    assert snapshot.status_code == 200
    assert snapshot.title == "Example"
    assert snapshot.screenshot_bytes == b"PNG"
    assert snapshot.html == "<html><title>Example</title></html>"
    assert context.accept_downloads is False
    assert page.closed is True
    assert context.closed is True
    assert service.factory is not None


def test_capture_rejects_private_target_before_starting_browser():
    class ExplodingFactory:
        def new_context(self, *, accept_downloads):
            raise AssertionError("browser must not start")

    service = BrowserSnapshotService(
        factory=ExplodingFactory(),
        resolver=lambda hostname: ["127.0.0.1"],
    )

    with pytest.raises(BrowserSnapshotError, match="private"):
        service.capture("https://example.com")


def test_capture_rejects_oversized_screenshot_and_closes_resources():
    page = FakePage()
    context = FakeContext(page)
    service = BrowserSnapshotService(
        factory=FakeFactory(context),
        browser_policy=__import__("backend.app.services.url_security", fromlist=["BrowserSecurityPolicy"]).BrowserSecurityPolicy(max_screenshot_bytes=2),
        resolver=lambda hostname: ["93.184.216.34"],
    )

    with pytest.raises(BrowserSnapshotError, match="screenshot"):
        service.capture("https://example.com")
    assert page.closed is True
    assert context.closed is True


def test_capture_hides_browser_failure_details():
    class FailingPage(FakePage):
        def goto(self, url, *, timeout_ms):
            raise RuntimeError("password=secret should not escape")

    page = FailingPage()
    context = FakeContext(page)
    service = BrowserSnapshotService(
        factory=FakeFactory(context),
        resolver=lambda hostname: ["93.184.216.34"],
    )

    with pytest.raises(BrowserSnapshotError, match="browser snapshot failed") as error:
        service.capture("https://example.com")
    assert "secret" not in str(error.value)
    assert page.closed is True
    assert context.closed is True
