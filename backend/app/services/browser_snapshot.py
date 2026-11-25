from dataclasses import dataclass
from typing import Protocol

from backend.app.services.url_security import (
    BrowserSecurityPolicy,
    Resolver,
    ResourceLimits,
    URLSecurityError,
    URLSecurityPolicy,
    validate_fetch_target,
)


class BrowserSnapshotError(RuntimeError):
    """A browser snapshot could not be captured safely."""


@dataclass(frozen=True)
class BrowserSnapshot:
    requested_url: str
    normalized_url: str
    final_url: str
    status_code: int | None
    title: str
    screenshot_bytes: bytes
    html: str
    redirect_chain: tuple[str, ...]
    content_type: str | None = None


class SnapshotPage(Protocol):
    url: str

    def goto(self, url: str, *, timeout_ms: int) -> int | None: ...
    def title(self) -> str: ...
    def screenshot(self, *, full_page: bool) -> bytes: ...
    def content(self) -> str: ...
    def close(self) -> None: ...


class SnapshotContext(Protocol):
    def new_page(self) -> SnapshotPage: ...
    def close(self) -> None: ...


class BrowserFactory(Protocol):
    def new_context(self, *, accept_downloads: bool) -> SnapshotContext: ...

    def close(self) -> None: ...


def _default_browser_factory() -> BrowserFactory:
    try:
        from backend.app.adapters.playwright_browser import PlaywrightBrowserFactory

        return PlaywrightBrowserFactory()
    except ImportError as exc:
        raise BrowserSnapshotError(
            "Playwright is not installed; install the browser optional dependency"
        ) from exc


class BrowserSnapshotService:
    def __init__(
        self,
        *,
        factory: BrowserFactory | None = None,
        browser_policy: BrowserSecurityPolicy | None = None,
        resource_limits: ResourceLimits | None = None,
        url_policy: URLSecurityPolicy | None = None,
        resolver: Resolver | None = None,
    ) -> None:
        self.factory = factory
        self.browser_policy = browser_policy or BrowserSecurityPolicy()
        self.resource_limits = resource_limits or ResourceLimits(
            max_external_targets=self.browser_policy.max_external_targets,
            max_pages=self.browser_policy.max_pages,
            max_depth=self.browser_policy.max_depth,
        )
        self.url_policy = url_policy or URLSecurityPolicy()
        self.resolver = resolver

    def capture(self, raw_url: str) -> BrowserSnapshot:
        try:
            observation = validate_fetch_target(
                raw_url, policy=self.url_policy, resolver=self.resolver
            )
        except URLSecurityError as exc:
            raise BrowserSnapshotError(str(exc)) from exc

        factory = self.factory
        owns_factory = factory is None
        if factory is None:
            factory = _default_browser_factory()
        context = None
        page = None
        try:
            context = factory.new_context(
                accept_downloads=self.browser_policy.accept_downloads
            )
            configure_navigation = getattr(context, "configure_navigation", None)
            if configure_navigation is not None:
                configure_navigation(
                    url_policy=self.url_policy,
                    resolver=self.resolver,
                )
            page = context.new_page()
            status_code = page.goto(
                observation.normalized_url,
                timeout_ms=self.browser_policy.navigation_timeout_ms,
            )
            screenshot = page.screenshot(full_page=True)
            if len(screenshot) > self.browser_policy.max_screenshot_bytes:
                raise BrowserSnapshotError("screenshot exceeds the allowed limit")
            return BrowserSnapshot(
                requested_url=raw_url.strip(),
                normalized_url=observation.normalized_url,
                final_url=page.url or observation.normalized_url,
                status_code=status_code,
                title=page.title(),
                screenshot_bytes=screenshot,
                html=page.content(),
                redirect_chain=(observation.normalized_url, page.url or observation.normalized_url),
            )
        except BrowserSnapshotError:
            raise
        except Exception as exc:
            raise BrowserSnapshotError("browser snapshot failed") from exc
        finally:
            if page is not None:
                try:
                    page.close()
                except Exception:
                    pass
            if context is not None:
                try:
                    context.close()
                except Exception:
                    pass
            if owns_factory:
                try:
                    factory.close()
                except Exception:
                    pass
