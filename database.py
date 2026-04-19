from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from datetime import datetime, timezone
import os

# Create database engine
# Use SQLite for simplicity, but can swap for Postgres
DB_URL = "sqlite:///portfolio.db"
engine = create_engine(DB_URL, echo=False)


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
