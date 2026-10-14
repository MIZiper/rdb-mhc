"""Uvicorn entrypoint (``tc.main:app``)."""

from tc.app import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
