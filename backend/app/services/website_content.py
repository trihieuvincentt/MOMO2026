from backend.app.services.browser_snapshot import BrowserSnapshot
from backend.app.services.content_extractor import WebsiteContent, extract_website_content


class WebsiteContentService:
    def extract(self, snapshot: BrowserSnapshot) -> WebsiteContent:
        return extract_website_content(snapshot.html, base_url=snapshot.final_url)
