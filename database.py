from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, UniqueConstraint, Date
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from datetime import datetime, timezone
import os

# Use DATABASE_URL env var (PostgreSQL on VPS), fallback to SQLite locally
_db_url = os.environ.get("DATABASE_URL", "sqlite:///portfolio.db")
# SQLAlchemy requires postgresql+psycopg2:// scheme
if _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
engine = create_engine(_db_url, echo=False, pool_pre_ping=True)


class Base(DeclarativeBase):
    pass


class PortfolioItem(Base):
    __tablename__ = 'portfolio'

    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)  # Telegram User ID
    ticker = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    avg_cost = Column(Float, nullable=False)  # Average cost basis
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<PortfolioItem(ticker='{self.ticker}', qty={self.quantity}, cost={self.avg_cost})>"


class PriceAlert(Base):
    __tablename__ = 'price_alerts'

    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    ticker = Column(String, nullable=False)
    condition = Column(String, nullable=False)  # 'above' or 'below'
    target_price = Column(Float, nullable=False)
    triggered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        symbol = '>' if self.condition == 'above' else '<'
        return f"<Alert({self.ticker} {symbol} {self.target_price})>"


class StockPriceLog(Base):
    """
    One row per ticker per trading day — built from RapidAPI cache refreshes.
    Accumulates into the historical dataset used by ml_predictor.py.
    """
    __tablename__ = 'stock_price_log'
    __table_args__ = (
        UniqueConstraint('ticker', 'trade_date', name='uq_ticker_date'),
    )

    id = Column(Integer, primary_key=True)
    ticker = Column(String(16), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)
    close = Column(Float, nullable=False)
    volume = Column(Float)
    change = Column(Float)
    change_pct = Column(Float)
    logged_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<PriceLog({self.ticker} {self.trade_date} close={self.close})>"


# Create tables
Base.metadata.create_all(engine)

# Session factory
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
