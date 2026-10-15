import uuid
from typing import Optional

from fastapi import Request, Response

SESSION_HEADER = "X-Analysis-Session-Id"
SESSION_COOKIE = "resumefit_session"


def resolve_session_id(request: Request, response: Optional[Response] = None) -> str:
    header_value = request.headers.get(SESSION_HEADER)
    if header_value and header_value.strip():
        session_id = header_value.strip()[:64]
        if response is not None:
            response.headers[SESSION_HEADER] = session_id
        return session_id

    cookie_value = request.cookies.get(SESSION_COOKIE)
    if cookie_value and cookie_value.strip():
        session_id = cookie_value.strip()[:64]
        if response is not None:
            response.headers[SESSION_HEADER] = session_id
        return session_id

    session_id = str(uuid.uuid4())
    if response is not None:
        response.set_cookie(
            key=SESSION_COOKIE,
            value=session_id,
            httponly=True,
            samesite="lax",
            max_age=60 * 60 * 24 * 30,
        )
        response.headers[SESSION_HEADER] = session_id
    return session_id
