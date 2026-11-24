import re
from collections import defaultdict

from backend.app.schemas.dataset import CleanDatasetRecord

_PATTERNS = {
    "credential_request": (r"\b(?:otp|password|m[aậ]t\s*kh[aẩ]u|recovery code|m[aã]\s*x[aá]c\s*th[ựu]c)\b",),
    "account_deactivation": (r"(?:account|t[aà]i\s*kho[aả]n).{0,35}(?:deactiv|suspend|lock|kh[oó]a|v[oô]\s*hi[eệ]u)",),
    "verification_phishing": (r"(?:verify|confirm|x[aá]c\s*minh|th[eự]c\s*hi[eệ]n).{0,40}(?:account|identity|t[aà]i\s*kho[aả]n|danh\s*t[ií]nh)",),
    "external_link_request": (r"(?:https?://|www\.|click|link|truy\s*c[aậ]p|b[aấ]m\s*v[aà]o)",),
    "prize_claim": (r"(?:prize|tr[uú]ng\s*gi[aả]i|gi[aả]i\s*th[uư][oơ]ng|winner|may\s*m[aắ]n)",),
    "investment_scam": (r"(?:guaranteed\s+(?:profit|return)|guaranteed\s*profit|deposit\s+now|l[oợ]i\s*nhu[aậ]n|đ[aầ]u\s*tư)",),
    "advance_fee": (r"(?:fee|ph[ií]|pay|payment|chuy[eể]n\s*kho[aả]n)",),
    "urgency": (r"(?:urgent|immediately|now|today|kh[aẩ]n\s*c[aấ]p|ngay\s*l[aậ]p\s*t[uứ]c)",),
    "secrecy": (r"(?:keep\s+secret|do\s+not\s+tell|gi[uữ]\s*b[ií]\s*m[aậ]t|kh[oô]ng\s*n[oó]i)",),
    "brand_impersonation": (r"(?:facebook|meta|bank|ng[aâ]n\s*h[aà]ng|mobi\s*fone|zalo).{0,100}(?:verify|prize|account|x[aá]c\s*minh|tr[uú]ng)",),
}


def extract_feature_families(record: CleanDatasetRecord) -> dict[str, list[dict]]:
    text = record.normalized_text
    features: dict[str, list[dict]] = defaultdict(list)
    for family, patterns in _PATTERNS.items():
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
            features[family].append({"source": record.source, "source_row_id": record.source_row_id, "is_synthetic": record.is_synthetic})
    return dict(features)


def build_feature_catalog(records: list[CleanDatasetRecord]) -> dict[str, list[dict]]:
    catalog: dict[str, list[dict]] = defaultdict(list)
    seen: set[tuple[str, str, str]] = set()
    for record in records:
        for family, matches in extract_feature_families(record).items():
            key = (family, record.source, record.source_row_id)
            if key not in seen:
                seen.add(key)
                catalog[family].extend(matches)
    return dict(catalog)
