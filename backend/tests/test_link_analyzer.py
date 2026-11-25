from dataclasses import dataclass

from backend.app.adapters.reputation import ReputationLookup
from backend.app.services.content_extractor import ExtractedLink, WebsiteContent
from backend.app.services.link_analyzer import analyze_links


def link(text, url, domain, internal=False, role=None):
    return ExtractedLink(text, url, domain, (), None, internal, role)


def test_deduplicates_links_and_classifies_external_targets():
    content = WebsiteContent(
        title="Example", meta_description="", headings=[], visible_text="",
        links=[
            link("Login", "https://example.com/login#top", "example.com", True, "login"),
            link("Login", "https://example.com/login", "example.com", True, "login"),
            link("Register", "https://other.example/register", "other.example", False, "registration"),
        ],
    )

    result = analyze_links(content, source_url="https://example.com/home")

    assert len(result.links) == 2
    assert result.links[0].is_internal is True
    assert result.links[1].relationship == "external"
    assert result.links[1].requires_deep_analysis is True


def test_brand_domain_mismatch_is_reported_for_sensitive_external_link():
    content = WebsiteContent(
        title="Facebook Login", meta_description="", headings=[], visible_text="",
        links=[link("Login", "https://facebook-help.social/login", "facebook-help.social", False, "login")],
    )

    result = analyze_links(content, source_url="https://facebook-help.social/home", claimed_brands=["Facebook"])

    assert "brand_domain_mismatch" in result.links[0].indicators
    assert result.links[0].severity == "high"


def test_reputation_is_checked_only_for_bounded_external_targets():
    calls = []

    class Provider:
        def lookup(self, url):
            calls.append(url)
            return ReputationLookup(True, "test", "known match")

    links = [link("Register", f"https://target-{i}.example/register", f"target-{i}.example", False, "registration") for i in range(6)]
    result = analyze_links(
        WebsiteContent("", "", [], "", links=links),
        source_url="https://origin.example",
        reputation_provider=Provider(),
        max_external_targets=3,
    )

    assert len(calls) == 3
    assert len(result.deep_analysis_targets) == 3
    assert "external target limit" in " ".join(result.limitations).lower()
    assert all(link.reputation_matched is True for link in result.links[:3])


def test_internal_subdomain_is_same_site_domain():
    content = WebsiteContent(
        "", "", [], "",
        links=[link("Help", "https://login.example.com/help", "login.example.com", False, "login")],
    )

    result = analyze_links(content, source_url="https://www.example.com", claimed_brands=[])

    assert result.links[0].relationship == "internal"


def test_sensitive_external_link_not_matching_claimed_brand_is_flagged():
    content = WebsiteContent(
        "", "", [], "",
        links=[link("Login", "https://unrelated.example/login", "unrelated.example", False, "login")],
    )

    result = analyze_links(content, source_url="https://facebook.com", claimed_brands=["Facebook"])

    assert "brand_domain_mismatch" in result.links[0].indicators


    class ExplodingProvider:
        def lookup(self, url):
            raise AssertionError("internal link must not be looked up")

    result = analyze_links(
        WebsiteContent("", "", [], "", links=[link("Help", "https://example.com/help", "example.com", True)]),
        source_url="https://example.com",
        reputation_provider=ExplodingProvider(),
    )

    assert result.links[0].relationship == "internal"
