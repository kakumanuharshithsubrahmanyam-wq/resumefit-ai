import logging


def configure_logging() -> None:
    """Configure safe application logging without resume or job-description payloads."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
