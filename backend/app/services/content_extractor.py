from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit


_SENSITIVE_NAMES = {
    "password", "passwd", "pass", "otp", "pin", "cvv", "cvc", "card",
    "card_number", "account_number", "bank_account", "ssn", "social_security",
}
_ROLE_WORDS = {
    "registration": {"register", "registration", "sign up", "đăng ký", "khuyến mãi", "bonus"},
    "login": {"login", "log in", "đăng nhập", "sign in"},
    "verification": {"verify", "verification", "xác minh", "confirm"},
    "payment": {"pay", "payment", "thanh toán", "deposit", "nạp tiền"},
}


@dataclass(frozen=True)
class FormField:
    name: str
    input_type: str
    sensitivity: str
    value: None = None


@dataclass(frozen=True)
class ExtractedForm:
    action_url: str
    method: str
    fields: tuple[FormField, ...]


@dataclass(frozen=True)
class ExtractedImage:
    url: str
    alt: str


@dataclass(frozen=True)
class ExtractedLink:
    text: str
    url: str
    domain: str
    rel: tuple[str, ...]
    target: str | None
    is_internal: bool
    role: str | None


@dataclass(frozen=True)
class WebsiteContent:
    title: str
    meta_description: str
    headings: list[str]
    visible_text: str
    forms: list[ExtractedForm] = field(default_factory=list)
    images: list[ExtractedImage] = field(default_factory=list)
    links: list[ExtractedLink] = field(default_factory=list)


@dataclass
class _OpenForm:
    action_url: str
    method: str
    fields: list[FormField] = field(default_factory=list)


class _ContentParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.base_domain = (urlsplit(base_url).hostname or "").lower()
        self.title = ""
        self.meta_description = ""
        self.headings: list[str] = []
        self.text_parts: list[str] = []
        self.forms: list[_OpenForm] = []
        self._form: _OpenForm | None = None
        self.images: list[ExtractedImage] = []
        self.links: list[ExtractedLink] = []
        self._title_depth = 0
        self._heading_depth = 0
        self._link_text: list[str] | None = None
        self._link_attrs: dict[str, str] = {}
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        attrs = {key.lower(): value or "" for key, value in attrs_list}
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "template"}:
            self._ignored_depth += 1
            return
        if self._ignored_depth:
            return
        if tag == "title":
            self._title_depth = 1
        elif tag in {"h1", "h2", "h3"}:
            self._heading_depth = 1
        elif tag == "meta" and attrs.get("name", "").lower() == "description":
            self.meta_description = attrs.get("content", "").strip()
        elif tag == "form":
            action = urljoin(self.base_url, attrs.get("action") or self.base_url)
            self._form = _OpenForm(action, (attrs.get("method") or "get").lower())
        elif tag == "input" and self._form is not None:
            name = attrs.get("name") or attrs.get("id")
            if name:
                input_type = (attrs.get("type") or "text").lower()
                sensitivity = "sensitive" if input_type in {"password", "tel"} or name.casefold() in _SENSITIVE_NAMES else "normal"
                self._form.fields.append(FormField(name=name, input_type=input_type, sensitivity=sensitivity))
        elif tag == "img":
            if attrs.get("src"):
                self.images.append(ExtractedImage(urljoin(self.base_url, attrs["src"]), attrs.get("alt", "").strip()))
        elif tag == "a":
            href = attrs.get("href", "")
            if href and not href.lower().startswith(("javascript:", "mailto:", "tel:", "#")):
                self._link_text = []
                self._link_attrs = attrs

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._ignored_depth:
            if tag in {"script", "style", "noscript", "template"}:
                self._ignored_depth -= 1
            return
        if tag == "title":
            self._title_depth = 0
        elif tag in {"h1", "h2", "h3"}:
            self._heading_depth = 0
        elif tag == "form" and self._form is not None:
            self.forms.append(self._form)
            self._form = None
        elif tag == "a" and self._link_text is not None:
            url = urljoin(self.base_url, self._link_attrs.get("href", ""))
            domain = (urlsplit(url).hostname or "").lower()
            text = " ".join("".join(self._link_text).split())
            self.links.append(ExtractedLink(
                text=text,
                url=url,
                domain=domain,
                rel=tuple(self._link_attrs.get("rel", "").split()),
                target=self._link_attrs.get("target") or None,
                is_internal=domain == self.base_domain,
                role=_classify_role(text),
            ))
            self._link_text = None
            self._link_attrs = {}

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        text = " ".join(data.split())
        if not text:
            return
        self.text_parts.append(text)
        if self._title_depth:
            self.title += text
        if self._heading_depth:
            self.headings.append(text)
        if self._link_text is not None:
            self._link_text.append(text)


def _classify_role(text: str) -> str | None:
    lowered = text.casefold()
    for role, words in _ROLE_WORDS.items():
        if any(word in lowered for word in words):
            return role
    return None


def extract_website_content(html: str, *, base_url: str) -> WebsiteContent:
    parser = _ContentParser(base_url)
    parser.feed(html)
    parser.close()
    return WebsiteContent(
        title=" ".join(parser.title.split()),
        meta_description=parser.meta_description,
        headings=parser.headings,
        visible_text=" ".join(parser.text_parts),
        forms=[ExtractedForm(f.action_url, f.method, tuple(f.fields)) for f in parser.forms],
        images=parser.images,
        links=parser.links,
    )
