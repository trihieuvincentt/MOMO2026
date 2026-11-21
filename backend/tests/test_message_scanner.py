from backend.app.services.message_scanner import MessageScanRequest, analyze_message


def test_advance_fee_message_returns_grounded_finding():
    text = "Congratulations! Pay a verification fee of $20 before receiving your job offer."
    result = analyze_message(MessageScanRequest(text=text))

    assert result.status == "success"
    assert any(f.category == "advance_fee" for f in result.findings)
    assert all(f.evidence_excerpt in text for f in result.findings if f.evidence_excerpt)


def test_urgent_benign_message_is_not_high_risk_by_urgency_alone():
    text = "Urgent: the library closes at 5 PM today. Please return your book."
    result = analyze_message(MessageScanRequest(text=text))

    assert not any(f.severity == "high" for f in result.findings)


def test_empty_message_is_rejected():
    try:
        MessageScanRequest(text="   ")
    except ValueError:
        return
    raise AssertionError("blank message must be rejected")
