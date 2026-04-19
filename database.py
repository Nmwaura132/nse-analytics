from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    DateTime, Boolean, Date, UniqueConstraint, Index, text
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from datetime import datetime, timezone
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///portfolio.db"  # fallback for local dev only
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=False,
)


class Base(DeclarativeBase):
    pass


class PortfolioItem(Base):
    __tablename__ = "portfolio"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(64), nullable=False, index=True)
    ticker = Column(String(16), nullable=False)
    quantity = Column(Float, nullable=False)
    avg_cost = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<PortfolioItem({self.ticker} x{self.quantity} @ {self.avg_cost})>"


class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(64), nullable=False, index=True)
    ticker = Column(String(16), nullable=False)
    condition = Column(String(8), nullable=False)   # 'above' | 'below'
    target_price = Column(Float, nullable=False)
    triggered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        sym = ">" if self.condition == "above" else "<"
        return f"<Alert({self.ticker} {sym} {self.target_price})>"


class PriceHistory(Base):
    """Daily OHLCV price record per ticker — the ML training corpus."""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True)
    ticker = Column(String(16), nullable=False)
    date = Column(Date, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, default=0)
    change_abs = Column(Float, default=0)
    change_pct = Column(Float, default=0)
    source = Column(String(32), default="afx")   # 'afx' | 'rapidapi' | 'seed'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_price_history_ticker_date"),
        Index("ix_price_history_ticker_date", "ticker", "date"),
    )

    def __repr__(self):
        return f"<PriceHistory({self.ticker} {self.date} close={self.close})>"


class MLFeatures(Base):
    """Pre-computed technical indicators per ticker per day for ML training."""
    __tablename__ = "ml_features"

    id = Column(Integer, primary_key=True)
    ticker = Column(String(16), nullable=False)
    date = Column(Date, nullable=False)

    # Price features
    close = Column(Float)
    ma_7 = Column(Float)
    ma_20 = Column(Float)
    ma_50 = Column(Float)

    # Momentum
    rsi_14 = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_hist = Column(Float)

    # Volatility
    bb_upper = Column(Float)
    bb_mid = Column(Float)
    bb_lower = Column(Float)
    volatility_20d = Column(Float)   # 20-day rolling std of returns

    # Volume
    volume = Column(Float)
    volume_ma_20 = Column(Float)
    volume_ratio = Column(Float)     # volume / volume_ma_20

    # Target labels (computed after the fact)
    return_1d = Column(Float)        # next-day return
    return_5d = Column(Float)        # 5-day forward return
    direction_5d = Column(Integer)   # 1 = up >1%, 0 = flat, -1 = down >1%

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_ml_features_ticker_date"),
        Index("ix_ml_features_ticker_date", "ticker", "date"),
    )


# Create all tables
Base.metadata.create_all(engine)

# Session factory
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
