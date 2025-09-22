from __future__ import annotations
from datetime import datetime, date
from typing import Optional
import enum

from sqlalchemy import (
    String, Date, DateTime, Enum, Numeric, Float, Integer, Text, func
)
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base

class DealStatus(str, enum.Enum):
    ANNOUNCED = "ANNOUNCED"
    CLOSED = "CLOSED"
    TERMINATED = "TERMINATED"

class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Core identifiers
    announcement_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    acquirer_name:    Mapped[str] = mapped_column(String(255), index=True)
    target_name:      Mapped[str] = mapped_column(String(255), index=True)

    # Economics
    deal_value_usd:   Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    currency:         Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    enterprise_value: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    ebitda:           Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    ev_to_ebitda:     Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Categorization
    sector:           Mapped[Optional[str]] = mapped_column(String(128), index=True)
    geography:        Mapped[Optional[str]] = mapped_column(String(128), index=True)

    # Misc
    status:           Mapped[DealStatus] = mapped_column(Enum(DealStatus), default=DealStatus.ANNOUNCED, index=True)
    source_url:       Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes:            Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at:       Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:       Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def compute_ev_ebitda(self) -> Optional[float]:
        """Compute EV/EBITDA if not stored and inputs are valid."""
        try:
            if self.enterprise_value and self.ebitda and float(self.ebitda) != 0.0:
                return float(self.enterprise_value) / float(self.ebitda)
        except Exception:
            return None
        return None
