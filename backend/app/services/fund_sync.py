from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Fund
from app.services.fund_search_source import FundSearchResult


def upsert_funds(db: Session, funds: list[FundSearchResult]) -> list[Fund]:
    persisted: list[Fund] = []
    for item in funds:
        row = db.scalar(select(Fund).where(Fund.code == item.code))
        if not row:
            row = Fund(code=item.code, name=item.name, category=item.category or "未分类")
            db.add(row)
        else:
            row.name = item.name or row.name
            row.category = item.category or row.category
        persisted.append(row)

    if funds:
        db.commit()

    return persisted
