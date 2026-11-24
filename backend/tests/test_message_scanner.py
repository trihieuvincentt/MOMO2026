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


def test_vietnamese_prize_claim_returns_high_risk_finding():
    text = (
        "Chúc mừng tài khoản Facebook của bạn đã may mắn trúng giải nhất. "
        "Giải thưởng gồm xe máy và phiếu quà tặng 55.000.000 VNĐ. "
        "Bây giờ bạn truy cập ngay website để nhận thưởng."
    )
    result = analyze_message(MessageScanRequest(text=text))

    assert result.status == "success"
    finding = next(f for f in result.findings if f.category == "prize_claim")
    assert finding.severity == "high"
    assert finding.evidence_excerpt in text


def test_brand_mention_without_prize_claim_is_not_flagged_as_impersonation():
    text = "Facebook published a new developer documentation update today."
    result = analyze_message(MessageScanRequest(text=text))

    assert not any(f.category == "brand_impersonation" for f in result.findings)


def test_account_deactivation_phishing_returns_multiple_findings():
    text = (
        "Your account will be deactivated. Please verify your account by clicking "
        "http://facebook-help.social/gbGPWUB before it is permanently locked."
    )
    result = analyze_message(MessageScanRequest(text=text))
    categories = {finding.category for finding in result.findings}

    assert {"account_deactivation_threat", "verification_phishing", "external_link_request"} <= categories
    assert any(finding.category == "account_deactivation_threat" and finding.severity == "high" for finding in result.findings)
    assert any(finding.category == "verification_phishing" and finding.severity == "high" for finding in result.findings)


def test_vietnamese_bank_transfer_and_otp_scam_is_detected():
    text = "Tài khoản sẽ bị khóa. Vui lòng xác minh OTP và chuyển khoản phí kích hoạt ngay hôm nay."
    result = analyze_message(MessageScanRequest(text=text))
    categories = {finding.category for finding in result.findings}

    assert "account_deactivation_threat" in categories
    assert "credential_request" in categories
    assert "advance_fee" in categories


def test_investment_scam_returns_investment_finding():
    text = "Guaranteed profit 300% in 24 hours. Deposit now and our expert will trade for you."
    result = analyze_message(MessageScanRequest(text=text))

    assert any(finding.category == "investment_scam" for finding in result.findings)


    try:
        MessageScanRequest(text="   ")
    except ValueError:
        return
    raise AssertionError("blank message must be rejected")
