"""
SQLAlchemy Models — NestO
"""
from datetime import datetime
from sqlalchemy import (Column, Integer, String, Float, Boolean,
                        DateTime, ForeignKey, Text, Enum as SAEnum)
from sqlalchemy.orm import relationship
from database import Base
import enum


class UserRole(str, enum.Enum):
    admin    = "admin"
    resident = "resident"
    security = "security"
    staff    = "staff"


class ComplaintStatus(str, enum.Enum):
    open       = "open"
    assigned   = "assigned"
    in_progress = "in_progress"
    resolved   = "resolved"
    closed     = "closed"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    paid    = "paid"
    overdue = "overdue"


# ── Users ────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"
    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String(100), nullable=False)
    email        = Column(String(150), unique=True, index=True, nullable=False)
    phone        = Column(String(15))
    hashed_password = Column(String(200), nullable=False)
    role         = Column(SAEnum(UserRole), default=UserRole.resident)
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime, default=datetime.utcnow)

    flat         = relationship("Flat", back_populates="resident", uselist=False)
    complaints   = relationship("Complaint", back_populates="raised_by", foreign_keys="Complaint.raised_by_id")
    votes        = relationship("Vote", back_populates="user")


# ── Flats ────────────────────────────────────────────────────
class Flat(Base):
    __tablename__ = "flats"
    id           = Column(Integer, primary_key=True, index=True)
    flat_number  = Column(String(20), unique=True, nullable=False)
    block        = Column(String(10))
    floor        = Column(Integer)
    area_sqft    = Column(Float)
    is_owner     = Column(Boolean, default=True)   # True=owner, False=tenant
    resident_id  = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)

    resident     = relationship("User", back_populates="flat")
    bills        = relationship("MaintenanceBill", back_populates="flat")
    visitors     = relationship("Visitor", back_populates="flat")


# ── Maintenance Bills ────────────────────────────────────────
class MaintenanceBill(Base):
    __tablename__ = "maintenance_bills"
    id           = Column(Integer, primary_key=True, index=True)
    flat_id      = Column(Integer, ForeignKey("flats.id"))
    month        = Column(String(10))   # e.g. "2025-04"
    amount       = Column(Float, nullable=False)
    due_date     = Column(DateTime)
    paid_date    = Column(DateTime, nullable=True)
    status       = Column(SAEnum(PaymentStatus), default=PaymentStatus.pending)
    transaction_id = Column(String(100), nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)

    flat         = relationship("Flat", back_populates="bills")


# ── Visitors ─────────────────────────────────────────────────
class Visitor(Base):
    __tablename__ = "visitors"
    id           = Column(Integer, primary_key=True, index=True)
    flat_id      = Column(Integer, ForeignKey("flats.id"))
    name         = Column(String(100), nullable=False)
    phone        = Column(String(15))
    purpose      = Column(String(200))
    vehicle_no   = Column(String(20), nullable=True)
    pre_approved = Column(Boolean, default=False)
    qr_token     = Column(String(100), unique=True, nullable=True)
    entry_time   = Column(DateTime, nullable=True)
    exit_time    = Column(DateTime, nullable=True)
    approved_by  = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)

    flat         = relationship("Flat", back_populates="visitors")


# ── Complaints ───────────────────────────────────────────────
class Complaint(Base):
    __tablename__ = "complaints"
    id           = Column(Integer, primary_key=True, index=True)
    title        = Column(String(200), nullable=False)
    description  = Column(Text)
    category     = Column(String(50))   # plumbing, electrical, cleanliness…
    status       = Column(SAEnum(ComplaintStatus), default=ComplaintStatus.open)
    priority     = Column(String(10), default="medium")  # low/medium/high
    raised_by_id = Column(Integer, ForeignKey("users.id"))
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    sla_hours    = Column(Integer, default=24)
    resolved_at  = Column(DateTime, nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    raised_by    = relationship("User", foreign_keys=[raised_by_id], back_populates="complaints")
    assigned_to  = relationship("User", foreign_keys=[assigned_to_id])
    comments     = relationship("ComplaintComment", back_populates="complaint")


class ComplaintComment(Base):
    __tablename__ = "complaint_comments"
    id           = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"))
    author_id    = Column(Integer, ForeignKey("users.id"))
    text         = Column(Text, nullable=False)
    created_at   = Column(DateTime, default=datetime.utcnow)

    complaint    = relationship("Complaint", back_populates="comments")
    author       = relationship("User")


# ── Notices ──────────────────────────────────────────────────
class Notice(Base):
    __tablename__ = "notices"
    id           = Column(Integer, primary_key=True, index=True)
    title        = Column(String(200), nullable=False)
    body         = Column(Text, nullable=False)
    category     = Column(String(50), default="general")
    posted_by_id = Column(Integer, ForeignKey("users.id"))
    is_poll      = Column(Boolean, default=False)
    poll_options = Column(Text, nullable=True)   # JSON string
    poll_deadline= Column(DateTime, nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)

    posted_by    = relationship("User")
    votes        = relationship("Vote", back_populates="notice")


class Vote(Base):
    __tablename__ = "votes"
    id           = Column(Integer, primary_key=True, index=True)
    notice_id    = Column(Integer, ForeignKey("notices.id"))
    user_id      = Column(Integer, ForeignKey("users.id"))
    option_index = Column(Integer)
    created_at   = Column(DateTime, default=datetime.utcnow)

    notice       = relationship("Notice", back_populates="votes")
    user         = relationship("User", back_populates="votes")
