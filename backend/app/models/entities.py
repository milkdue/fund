from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Fund(Base):
    __tablename__ = "funds"

    code: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)


class Quote(Base):
    __tablename__ = "quotes"
    __table_args__ = (UniqueConstraint("fund_code", "as_of", name="uq_quote_fund_as_of"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fund_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    nav: Mapped[float] = mapped_column(Float, nullable=False)
    daily_change_pct: Mapped[float] = mapped_column(Float, nullable=False)
    volatility_20d: Mapped[float] = mapped_column(Float, nullable=False)
    as_of: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (UniqueConstraint("fund_code", "horizon", "as_of", name="uq_pred_fund_horizon_as_of"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fund_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    horizon: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    up_probability: Mapped[float] = mapped_column(Float, nullable=False)
    expected_return_pct: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    as_of: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)


class Watchlist(Base):
    __tablename__ = "watchlist"
    __table_args__ = (UniqueConstraint("user_id", "fund_code", name="uq_watchlist_user_fund"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    fund_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class NewsRaw(Base):
    __tablename__ = "news_raw"
    __table_args__ = (UniqueConstraint("fund_code", "title_hash", "published_at", name="uq_news_raw_fund_hash_pub"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fund_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    title_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    event_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class NewsSignalDaily(Base):
    __tablename__ = "news_signal_daily"
    __table_args__ = (UniqueConstraint("fund_code", "trade_date", name="uq_news_signal_fund_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fund_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    headline_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    event_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    volume_shock: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sample_title: Mapped[str] = mapped_column(String(256), nullable=False, default="暂无新增公告/舆情")
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
