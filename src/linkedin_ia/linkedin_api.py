"""LinkedIn's REST API: who the token belongs to, image upload, posts and comments."""

import http.client
import json
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import quote, urlsplit

API = "https://api.linkedin.com"


@dataclass(frozen=True)
class Response:
    status: int
    headers: dict[str, str]
    body: bytes


Transport = Callable[[urllib.request.Request], Response]


class ApiError(Exception):
    """LinkedIn refused the request (4xx): nothing was created."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"HTTP {status}: {message}")
        self.status = status


class NoAnswer(Exception):
    """No answer, a server error (5xx) or an unreadable one: whether it took effect is unknown."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect would carry the token elsewhere: refuse it."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def urllib_transport(request: urllib.request.Request) -> Response:
    try:
        with _OPENER.open(request, timeout=60) as response:
            headers = {k.lower(): v for k, v in response.headers.items()}
            return Response(response.status, headers, response.read())
    except urllib.error.HTTPError as error:
        headers = {k.lower(): v for k, v in error.headers.items()}
        return Response(error.code, headers, error.read())
    except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError) as error:
        raise NoAnswer(str(error)) from error


def _message(body: bytes) -> str:
    try:
        return str(json.loads(body).get("message", ""))[:300]
    except (ValueError, AttributeError):
        return body[:300].decode("utf-8", "replace")


class Client:
    def __init__(self, token: str, version: str, transport: Transport = urllib_transport):
        self._token = token
        self._version = version
        self._transport = transport

    def _send(
        self,
        method: str,
        url: str,
        payload: object = None,
        data: bytes | None = None,
        rest: bool = True,
    ) -> Response:
        headers = {"Authorization": f"Bearer {self._token}"}
        if rest:
            headers["LinkedIn-Version"] = self._version
            headers["X-Restli-Protocol-Version"] = "2.0.0"
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif data is not None:
            headers["Content-Type"] = "application/octet-stream"
        response = self._transport(
            urllib.request.Request(url, data=data, headers=headers, method=method)
        )
        if response.status >= 500 or 300 <= response.status < 400:
            raise NoAnswer(f"HTTP {response.status}: {_message(response.body)}")
        if response.status >= 400:
            raise ApiError(response.status, _message(response.body))
        return response

    def member(self) -> tuple[str, str]:
        """The person URN and display name of the token's owner."""
        info = json.loads(self._send("GET", f"{API}/v2/userinfo", rest=False).body)
        return f"urn:li:person:{info['sub']}", str(info.get("name", ""))

    def upload_image(self, owner: str, image: bytes) -> str:
        """Upload image bytes and return the image URN to attach to a post."""
        init = self._send(
            "POST",
            f"{API}/rest/images?action=initializeUpload",
            {"initializeUploadRequest": {"owner": owner}},
        )
        value = json.loads(init.body)["value"]
        upload = urlsplit(value["uploadUrl"])
        host = upload.hostname or ""
        if upload.scheme != "https" or not (
            host == "linkedin.com" or host.endswith(".linkedin.com")
        ):
            raise ApiError(0, f"uploadUrl fora do LinkedIn: {host}")
        self._send("PUT", value["uploadUrl"], data=image, rest=False)
        return str(value["image"])

    def create_post(self, author: str, commentary: str, image: str | None = None) -> str:
        """Publish a post and return its URN."""
        post: dict[str, object] = {
            "author": author,
            "commentary": commentary,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        if image:
            post["content"] = {"media": {"id": image}}
        response = self._send("POST", f"{API}/rest/posts", post)
        urn = response.headers.get("x-restli-id", "")
        if not urn:
            raise NoAnswer("post criado sem x-restli-id na resposta")
        return urn

    def comment(self, post: str, actor: str, text: str) -> None:
        self._send(
            "POST",
            f"{API}/rest/socialActions/{quote(post, safe='')}/comments",
            {"actor": actor, "object": post, "message": {"text": text}},
        )


def post_url(urn: str) -> str:
    return f"https://www.linkedin.com/feed/update/{urn}/"
