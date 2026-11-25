from types import SimpleNamespace

from backend.app.adapters.playwright_browser import _PlaywrightContext
from backend.app.services.url_security import URLSecurityPolicy, validate_fetch_target


class FakeRoute:
    def __init__(self):
        self.action = None

    def abort(self):
        self.action = "abort"

    def continue_(self):
        self.action = "continue"


class FakeBrowserContext:
    def __init__(self):
        self.handler = None

    def route(self, pattern, handler):
        assert pattern == "**/*"
        self.handler = handler


def test_navigation_route_rejects_hostname_when_dns_rebinds_to_private_address():
    browser_context = FakeBrowserContext()
    calls = []

    def resolver(hostname):
        calls.append(hostname)
        return ["93.184.216.34"] if len(calls) == 1 else ["127.0.0.1"]

    context = _PlaywrightContext(browser_context)
    context.configure_navigation(
        url_policy=URLSecurityPolicy(),
        resolver=resolver,
    )

    initial = validate_fetch_target(
        "https://example.com/",
        policy=URLSecurityPolicy(),
        resolver=resolver,
    )
    assert initial.hostname == "example.com"

    route = FakeRoute()
    browser_context.handler(route, SimpleNamespace(url="https://example.com/"))

    assert route.action == "abort"
    assert calls == ["example.com", "example.com"]
