from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.session import Base
from app.models.entities import Fund
from app.services.fund_search_source import FundSearchResult
from app.services.fund_sync import upsert_funds


def test_upsert_funds_insert_and_update():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        upsert_funds(db, [FundSearchResult(code="110022", name="A", category="混合型")])
        first = db.scalar(select(Fund).where(Fund.code == "110022"))
        assert first is not None
        assert first.name == "A"

        upsert_funds(db, [FundSearchResult(code="110022", name="B", category="指数型")])
        second = db.scalar(select(Fund).where(Fund.code == "110022"))
        assert second is not None
        assert second.name == "B"
        assert second.category == "指数型"
