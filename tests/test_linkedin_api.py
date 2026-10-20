import json
import urllib.error

import pytest

from linkedin_ia import linkedin_api
from linkedin_ia.linkedin_api import ApiError, Client, NoAnswer, Response


class Fake:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, request):
        self.requests.append(request)
        return self.responses.pop(0)


def ok(body=None, status=200, **headers):
    return Response(status, headers, json.dumps(body or {}).encode())


def sent(request):
    return json.loads(request.data)


def test_member_reads_the_person_urn_from_userinfo():
    fake = Fake(ok({"sub": "abc123", "name": "Bernardo Gualberto"}))
    assert Client("tok", "202610", fake).member() == ("urn:li:person:abc123", "Bernardo Gualberto")
    request = fake.requests[0]
    assert request.full_url == "https://api.linkedin.com/v2/userinfo"
    assert request.get_header("Authorization") == "Bearer tok"


def test_rest_calls_carry_the_version_and_protocol_headers():
    fake = Fake(ok(status=201, **{"x-restli-id": "urn:li:share:1"}))
    Client("tok", "202610", fake).create_post("urn:li:person:p", "Oi")
    request = fake.requests[0]
    assert request.get_header("Linkedin-version") == "202610"
    assert request.get_header("X-restli-protocol-version") == "2.0.0"


def test_create_post_sends_a_public_text_post_and_returns_its_urn():
    fake = Fake(ok(status=201, **{"x-restli-id": "urn:li:share:99"}))
    urn = Client("tok", "202610", fake).create_post("urn:li:person:p", "Olá {hashtag|\\#|IA}")
    assert urn == "urn:li:share:99"
    request = fake.requests[0]
    assert (request.get_method(), request.full_url) == (
        "POST",
        "https://api.linkedin.com/rest/posts",
    )
    body = sent(request)
    assert body["author"] == "urn:li:person:p"
    assert body["commentary"] == "Olá {hashtag|\\#|IA}"
    assert body["visibility"] == "PUBLIC"
    assert body["lifecycleState"] == "PUBLISHED"
    assert body["distribution"]["feedDistribution"] == "MAIN_FEED"
    assert "content" not in body


def test_create_post_attaches_the_image():
    fake = Fake(ok(status=201, **{"x-restli-id": "urn:li:share:1"}))
    Client("tok", "202610", fake).create_post("urn:li:person:p", "Oi", "urn:li:image:I")
    assert sent(fake.requests[0])["content"] == {"media": {"id": "urn:li:image:I"}}


def test_upload_image_initializes_then_puts_the_bytes():
    init = ok({"value": {"uploadUrl": "https://up.example/x", "image": "urn:li:image:I"}})
    fake = Fake(init, Response(201, {}, b""))
    assert Client("tok", "202610", fake).upload_image("urn:li:person:p", b"PNG") == "urn:li:image:I"
    first, second = fake.requests
    assert first.full_url == "https://api.linkedin.com/rest/images?action=initializeUpload"
    assert sent(first) == {"initializeUploadRequest": {"owner": "urn:li:person:p"}}
    assert (second.get_method(), second.full_url, second.data) == (
        "PUT",
        "https://up.example/x",
        b"PNG",
    )
    assert second.get_header("Authorization") == "Bearer tok"


def test_comment_posts_to_the_encoded_post_urn():
    fake = Fake(ok(status=201))
    Client("tok", "202610", fake).comment("urn:li:share:9", "urn:li:person:p", "Link: https://x")
    request = fake.requests[0]
    assert request.full_url == (
        "https://api.linkedin.com/rest/socialActions/urn%3Ali%3Ashare%3A9/comments"
    )
    assert sent(request) == {
        "actor": "urn:li:person:p",
        "object": "urn:li:share:9",
        "message": {"text": "Link: https://x"},
    }


def test_an_error_status_raises_api_error_with_linkedins_message():
    fake = Fake(Response(403, {}, b'{"message": "Not enough permissions", "status": 403}'))
    with pytest.raises(ApiError) as error:
        Client("segredo", "202610", fake).create_post("urn:li:person:p", "Oi")
    assert error.value.status == 403
    assert "Not enough permissions" in str(error.value)
    assert "segredo" not in str(error.value)


def test_a_created_post_without_its_id_is_an_unknown_outcome():
    fake = Fake(ok(status=201))
    with pytest.raises(NoAnswer):
        Client("tok", "202610", fake).create_post("urn:li:person:p", "Oi")


def test_a_network_failure_is_no_answer(monkeypatch):
    def fail(request, timeout):
        raise urllib.error.URLError("timed out")

    monkeypatch.setattr(linkedin_api.urllib.request, "urlopen", fail)
    with pytest.raises(NoAnswer):
        linkedin_api.urllib_transport(linkedin_api.urllib.request.Request("https://x"))


def test_post_url():
    assert linkedin_api.post_url("urn:li:share:1") == (
        "https://www.linkedin.com/feed/update/urn:li:share:1/"
    )
