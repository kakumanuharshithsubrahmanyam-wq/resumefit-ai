from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.middleware.rate_limit import RateLimitMiddleware


async def homepage(_request):
    return PlainTextResponse("ok")


def test_rate_limit_returns_structured_error() -> None:
    app = Starlette(routes=[Route("/", homepage)])
    app.add_middleware(RateLimitMiddleware, requests_per_minute=2)
    client = TestClient(app)

    assert client.get("/").status_code == 200
    assert client.get("/").status_code == 200
    blocked = client.get("/")
    assert blocked.status_code == 429
    body = blocked.json()
    assert body["error"]["code"] == "rate_limit_exceeded"
