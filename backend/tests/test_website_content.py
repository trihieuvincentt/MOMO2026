from backend.app.services.website_content import WebsiteContentService
from backend.app.services.browser_snapshot import BrowserSnapshot


def test_extracts_content_from_browser_snapshot_html():
    snapshot = BrowserSnapshot(
        requested_url="https://example.com",
        normalized_url="https://example.com/",
        final_url="https://example.com/",
        status_code=200,
        title="Example",
        screenshot_bytes=b"PNG",
        html='<html><title>Example</title><a href="/login">Login</a></html>',
        redirect_chain=("https://example.com/",),
    )

    result = WebsiteContentService().extract(snapshot)

    assert result.title == "Example"
    assert result.links[0].url == "https://example.com/login"
