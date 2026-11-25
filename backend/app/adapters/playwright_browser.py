from typing import Any

from backend.app.services.url_security import (
    Resolver,
    URLSecurityError,
    URLSecurityPolicy,
    validate_fetch_target,
)


class PlaywrightBrowserFactory:
    """Own a Chromium process and expose only the snapshot operations we need."""

    def __init__(self) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise ImportError("Playwright is not installed") from exc
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)

    def new_context(self, *, accept_downloads: bool):
        return _PlaywrightContext(self._browser.new_context(accept_downloads=accept_downloads))

    def close(self) -> None:
        self._browser.close()
        self._playwright.stop()


class _PlaywrightContext:
    def __init__(self, context: Any) -> None:
        self._context = context

    def configure_navigation(self, *, url_policy: URLSecurityPolicy, resolver: Resolver | None) -> None:
        def route_handler(route: Any, request: Any) -> None:
            try:
                validate_fetch_target(request.url, policy=url_policy, resolver=resolver)
            except URLSecurityError:
                route.abort()
            else:
                route.continue_()

        self._context.route("**/*", route_handler)

    def new_page(self):
        return _PlaywrightPage(self._context.new_page())

    def close(self) -> None:
        self._context.close()


class _PlaywrightPage:
    def __init__(self, page: Any) -> None:
        self._page = page

    @property
    def url(self) -> str:
        return self._page.url

    def goto(self, url: str, *, timeout_ms: int) -> int | None:
        response = self._page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
        return response.status if response is not None else None

    def title(self) -> str:
        return self._page.title()

    def screenshot(self, *, full_page: bool) -> bytes:
        return self._page.screenshot(full_page=full_page, type="png")

    def content(self) -> str:
        return self._page.content()

    def close(self) -> None:
        self._page.close()
