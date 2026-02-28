import os
import json
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

# =============================
# Database Setup
# =============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "crisis_reports.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed for FastAPI + SQLite
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()


# =============================
# Crisis Report Model
# =============================

class CrisisReport(Base):
    __tablename__ = "crisis_reports"

    id = Column(Integer, primary_key=True, index=True)

    crisis_id = Column(String, unique=True, index=True, nullable=False)

    submitted_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now
    )

    approval_status = Column(String, nullable=False)  # PENDING / APPROVED / REJECTED

    approval_time = Column(DateTime, nullable=True)

    dispatch_time = Column(DateTime, nullable=True)

    teams_notified = Column(
        Text,
        nullable=False,
        default="[]"
    )

    # =============================
    # Convert to JSON-safe dict
    # =============================

    def to_dict(self):
        return {
            "id": self.id,
            "crisis_id": self.crisis_id,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "approval_status": self.approval_status,
            "approval_time": self.approval_time.isoformat() if self.approval_time else None,
            "dispatch_time": self.dispatch_time.isoformat() if self.dispatch_time else None,
            "teams_notified": json.loads(self.teams_notified or "[]"),
        }


# =============================
# Create Tables
# =============================

def create_tables():
    Base.metadata.create_all(bind=engine)