"""Isolated database fixture for API tests."""

import asyncio
from collections.abc import Callable, Generator

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.seed import seed_database
from app.database.session import get_db
from app.main import app


@pytest.fixture()
def client() -> Generator[Callable[..., httpx.Response], None, None]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    with factory() as db:
        seed_database(db)

    async def override_db() -> Generator[Session, None, None]:
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db

    def request(method: str, path: str, **kwargs: object) -> httpx.Response:
        async def send() -> httpx.Response:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.request(method, path, **kwargs)

        return asyncio.run(send())

    request.session_factory = factory  # type: ignore[attr-defined]
    yield request
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
