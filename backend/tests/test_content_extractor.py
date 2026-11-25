from backend.app.services.content_extractor import extract_website_content


HTML = """
<html>
<head><title>Register Now</title><meta name="description" content="Get bonus"></head>
<body>
<h1>Welcome</h1><h2>Login</h2><p>Deposit and bonus today</p>
<form action="/login" method="post"><input name="username"><input type="password" name="password"><input name="otp"></form>
<img src="/logo.png" alt="Example Bank logo">
<a rel="nofollow" target="_blank" href="https://other.example/register"><span>Đăng ký</span></a>
<a href="/help">Help</a>
</body></html>
"""


def test_extracts_page_metadata_text_forms_images_and_links():
    result = extract_website_content(HTML, base_url="https://example.com/home")

    assert result.title == "Register Now"
    assert result.meta_description == "Get bonus"
    assert result.headings == ["Welcome", "Login"]
    assert "Deposit and bonus today" in result.visible_text
    assert result.forms[0].action_url == "https://example.com/login"
    assert {field.name for field in result.forms[0].fields} == {"username", "password", "otp"}
    assert result.images[0].url == "https://example.com/logo.png"
    assert result.images[0].alt == "Example Bank logo"
    assert result.links[0].text == "Đăng ký"
    assert result.links[0].is_internal is False
    assert result.links[0].role == "registration"
    assert result.links[1].is_internal is True


def test_extracts_sensitive_form_fields_without_values():
    result = extract_website_content(
        '<form><input name="card_number" value="4111 1111 1111 1111"><input name="password"></form>',
        base_url="https://example.com",
    )

    fields = result.forms[0].fields
    assert all(field.value is None for field in fields)
    assert {field.sensitivity for field in fields} == {"sensitive"}


def test_malformed_and_unsupported_links_are_ignored():
    result = extract_website_content(
        '<script>secret = "do not show"</script><style>.x{}</style><a href="javascript:void(0)">JS</a><a href="mailto:a@example.com">Mail</a><a href="/ok">OK</a>',
        base_url="https://example.com",
    )

    assert [link.text for link in result.links] == ["OK"]
    assert "do not show" not in result.visible_text
