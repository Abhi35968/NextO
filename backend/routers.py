"""
API Routers — Auth, Residents, Flats, Maintenance, Visitors, Complaints, Notices
"""
import json, secrets
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database import get_db
from auth import (hash_password, verify_password, create_access_token,
                  get_current_user, require_role)
import models

# ═══════════════════════════════════════════════════════
#  AUTH
# ═══════════════════════════════════════════════════════
auth_router = APIRouter(prefix="/api/auth", tags=["auth"])

class RegisterIn(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    password: str
    role: str = "resident"

class TokenOut(BaseModel):
    access_token: str
    token_type: str
    user: dict

@auth_router.post("/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(400, "Email already registered")
    user = models.User(
        name=data.name, email=data.email, phone=data.phone,
        hashed_password=hash_password(data.password),
        role=data.role,
    )
    db.add(user); db.commit(); db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer",
            "user": {"id": user.id, "name": user.name, "role": user.role, "email": user.email}}

@auth_router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer",
            "user": {"id": user.id, "name": user.name, "role": user.role, "email": user.email}}

@auth_router.get("/me")
def me(user: models.User = Depends(get_current_user)):
    flat = None
    if user.flat:
        flat = {"flat_number": user.flat.flat_number, "block": user.flat.block}
    return {"id": user.id, "name": user.name, "email": user.email,
            "role": user.role, "phone": user.phone, "flat": flat}


# ═══════════════════════════════════════════════════════
#  FLATS & RESIDENTS
# ═══════════════════════════════════════════════════════
resident_router = APIRouter(prefix="/api/residents", tags=["residents"])

class FlatIn(BaseModel):
    flat_number: str
    block: Optional[str] = None
    floor: Optional[int] = None
    area_sqft: Optional[float] = None
    resident_id: Optional[int] = None
    is_owner: bool = True

@resident_router.get("")
def list_residents(db: Session = Depends(get_db),
                   _: models.User = Depends(require_role("admin", "security", "staff"))):
    flats = db.query(models.Flat).all()
    result = []
    for f in flats:
        result.append({
            "id": f.id, "flat_number": f.flat_number, "block": f.block,
            "floor": f.floor, "area_sqft": f.area_sqft, "is_owner": f.is_owner,
            "resident": {"id": f.resident.id, "name": f.resident.name,
                         "email": f.resident.email, "phone": f.resident.phone,
                         "role": f.resident.role} if f.resident else None,
        })
    return result

@resident_router.post("")
def add_flat(data: FlatIn, db: Session = Depends(get_db),
             _: models.User = Depends(require_role("admin"))):
    if db.query(models.Flat).filter(models.Flat.flat_number == data.flat_number).first():
        raise HTTPException(400, "Flat already exists")
    flat = models.Flat(**data.dict())
    db.add(flat); db.commit(); db.refresh(flat)
    return flat

@resident_router.put("/{flat_id}")
def update_flat(flat_id: int, data: FlatIn, db: Session = Depends(get_db),
                _: models.User = Depends(require_role("admin"))):
    flat = db.query(models.Flat).filter(models.Flat.id == flat_id).first()
    if not flat: raise HTTPException(404, "Flat not found")
    for k, v in data.dict(exclude_unset=True).items():
        setattr(flat, k, v)
    db.commit(); db.refresh(flat)
    return flat

@resident_router.get("/users")
def list_users(db: Session = Depends(get_db),
               _: models.User = Depends(require_role("admin"))):
    users = db.query(models.User).all()
    return [{"id": u.id, "name": u.name, "email": u.email,
             "role": u.role, "phone": u.phone, "is_active": u.is_active} for u in users]


# ═══════════════════════════════════════════════════════
#  MAINTENANCE
# ═══════════════════════════════════════════════════════
maintenance_router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])

class BillIn(BaseModel):
    flat_id: int
    month: str
    amount: float
    due_date: str

class PaymentIn(BaseModel):
    transaction_id: str

@maintenance_router.get("")
def list_bills(db: Session = Depends(get_db),
               user: models.User = Depends(get_current_user),
               flat_id: Optional[int] = Query(None)):
    q = db.query(models.MaintenanceBill)
    if user.role == "resident":
        if user.flat:
            q = q.filter(models.MaintenanceBill.flat_id == user.flat.id)
        else:
            return []
    elif flat_id:
        q = q.filter(models.MaintenanceBill.flat_id == flat_id)
    bills = q.order_by(models.MaintenanceBill.created_at.desc()).all()
    return [{
        "id": b.id, "flat_id": b.flat_id, "month": b.month,
        "amount": b.amount, "due_date": str(b.due_date),
        "status": b.status, "paid_date": str(b.paid_date) if b.paid_date else None,
        "transaction_id": b.transaction_id,
        "flat_number": b.flat.flat_number if b.flat else None,
    } for b in bills]

@maintenance_router.post("")
def create_bill(data: BillIn, db: Session = Depends(get_db),
                _: models.User = Depends(require_role("admin"))):
    bill = models.MaintenanceBill(
        flat_id=data.flat_id, month=data.month, amount=data.amount,
        due_date=datetime.fromisoformat(data.due_date),
    )
    db.add(bill); db.commit(); db.refresh(bill)
    return bill

@maintenance_router.post("/generate-all")
def generate_all_bills(month: str, amount: float, due_date: str,
                       db: Session = Depends(get_db),
                       _: models.User = Depends(require_role("admin"))):
    flats = db.query(models.Flat).filter(models.Flat.resident_id != None).all()
    created = 0
    for flat in flats:
        exists = db.query(models.MaintenanceBill).filter(
            models.MaintenanceBill.flat_id == flat.id,
            models.MaintenanceBill.month == month).first()
        if not exists:
            db.add(models.MaintenanceBill(
                flat_id=flat.id, month=month, amount=amount,
                due_date=datetime.fromisoformat(due_date)))
            created += 1
    db.commit()
    return {"created": created, "month": month}

@maintenance_router.post("/{bill_id}/pay")
def mark_paid(bill_id: int, data: PaymentIn, db: Session = Depends(get_db),
              user: models.User = Depends(get_current_user)):
    bill = db.query(models.MaintenanceBill).filter(models.MaintenanceBill.id == bill_id).first()
    if not bill: raise HTTPException(404, "Bill not found")
    bill.status = "paid"
    bill.paid_date = datetime.utcnow()
    bill.transaction_id = data.transaction_id
    db.commit()
    return {"message": "Payment recorded", "bill_id": bill_id}

@maintenance_router.get("/summary")
def summary(db: Session = Depends(get_db),
            _: models.User = Depends(require_role("admin"))):
    from sqlalchemy import func
    total = db.query(func.sum(models.MaintenanceBill.amount)).scalar() or 0
    paid  = db.query(func.sum(models.MaintenanceBill.amount)).filter(
        models.MaintenanceBill.status == "paid").scalar() or 0
    return {"total_billed": total, "total_collected": paid,
            "pending": total - paid,
            "bills_count": db.query(models.MaintenanceBill).count()}


# ═══════════════════════════════════════════════════════
#  VISITORS
# ═══════════════════════════════════════════════════════
visitor_router = APIRouter(prefix="/api/visitors", tags=["visitors"])

class VisitorIn(BaseModel):
    name: str
    phone: Optional[str] = None
    purpose: Optional[str] = None
    vehicle_no: Optional[str] = None
    flat_id: int
    pre_approved: bool = False

@visitor_router.post("")
def add_visitor(data: VisitorIn, db: Session = Depends(get_db),
                user: models.User = Depends(get_current_user)):
    token = secrets.token_urlsafe(16)
    visitor = models.Visitor(**data.dict(), qr_token=token,
                             approved_by=user.id if data.pre_approved else None)
    db.add(visitor); db.commit(); db.refresh(visitor)
    return {"id": visitor.id, "qr_token": token, "name": visitor.name}

@visitor_router.get("")
def list_visitors(db: Session = Depends(get_db),
                  user: models.User = Depends(get_current_user),
                  date: Optional[str] = Query(None)):
    q = db.query(models.Visitor)
    if user.role == "resident" and user.flat:
        q = q.filter(models.Visitor.flat_id == user.flat.id)
    if date:
        d = datetime.fromisoformat(date)
        q = q.filter(models.Visitor.created_at >= d,
                     models.Visitor.created_at < d + timedelta(days=1))
    visitors = q.order_by(models.Visitor.created_at.desc()).limit(100).all()
    return [{
        "id": v.id, "name": v.name, "phone": v.phone, "purpose": v.purpose,
        "vehicle_no": v.vehicle_no, "flat_id": v.flat_id,
        "flat_number": v.flat.flat_number if v.flat else None,
        "pre_approved": v.pre_approved, "qr_token": v.qr_token,
        "entry_time": str(v.entry_time) if v.entry_time else None,
        "exit_time": str(v.exit_time) if v.exit_time else None,
        "created_at": str(v.created_at),
    } for v in visitors]

@visitor_router.post("/checkin/{token}")
def checkin(token: str, db: Session = Depends(get_db),
            _: models.User = Depends(require_role("admin", "security"))):
    v = db.query(models.Visitor).filter(models.Visitor.qr_token == token).first()
    if not v: raise HTTPException(404, "Invalid QR token")
    v.entry_time = datetime.utcnow()
    db.commit()
    return {"message": f"{v.name} checked in", "flat": v.flat.flat_number if v.flat else ""}

@visitor_router.post("/checkout/{token}")
def checkout(token: str, db: Session = Depends(get_db),
             _: models.User = Depends(require_role("admin", "security"))):
    v = db.query(models.Visitor).filter(models.Visitor.qr_token == token).first()
    if not v: raise HTTPException(404, "Invalid QR token")
    v.exit_time = datetime.utcnow()
    db.commit()
    return {"message": f"{v.name} checked out"}


# ═══════════════════════════════════════════════════════
#  COMPLAINTS
# ═══════════════════════════════════════════════════════
complaint_router = APIRouter(prefix="/api/complaints", tags=["complaints"])

class ComplaintIn(BaseModel):
    title: str
    description: Optional[str] = None
    category: str = "general"
    priority: str = "medium"

class AssignIn(BaseModel):
    assigned_to_id: int
    sla_hours: int = 24

class CommentIn(BaseModel):
    text: str

@complaint_router.get("")
def list_complaints(db: Session = Depends(get_db),
                    user: models.User = Depends(get_current_user),
                    status: Optional[str] = Query(None)):
    q = db.query(models.Complaint)
    if user.role == "resident":
        q = q.filter(models.Complaint.raised_by_id == user.id)
    if status:
        q = q.filter(models.Complaint.status == status)
    complaints = q.order_by(models.Complaint.created_at.desc()).all()
    return [{
        "id": c.id, "title": c.title, "description": c.description,
        "category": c.category, "status": c.status, "priority": c.priority,
        "raised_by": c.raised_by.name if c.raised_by else None,
        "assigned_to": c.assigned_to.name if c.assigned_to else None,
        "sla_hours": c.sla_hours, "created_at": str(c.created_at),
        "resolved_at": str(c.resolved_at) if c.resolved_at else None,
        "sla_breached": (
            datetime.utcnow() - c.created_at > timedelta(hours=c.sla_hours)
            and c.status not in ("resolved", "closed")
        ),
    } for c in complaints]

@complaint_router.post("")
def raise_complaint(data: ComplaintIn, db: Session = Depends(get_db),
                    user: models.User = Depends(get_current_user)):
    c = models.Complaint(**data.dict(), raised_by_id=user.id)
    db.add(c); db.commit(); db.refresh(c)
    return {"id": c.id, "title": c.title, "status": c.status}

@complaint_router.put("/{cid}/assign")
def assign(cid: int, data: AssignIn, db: Session = Depends(get_db),
           _: models.User = Depends(require_role("admin", "staff"))):
    c = db.query(models.Complaint).filter(models.Complaint.id == cid).first()
    if not c: raise HTTPException(404)
    c.assigned_to_id = data.assigned_to_id
    c.sla_hours = data.sla_hours
    c.status = "assigned"
    db.commit()
    return {"message": "Assigned"}

@complaint_router.put("/{cid}/status")
def update_status(cid: int, status: str, db: Session = Depends(get_db),
                  _: models.User = Depends(require_role("admin", "staff"))):
    c = db.query(models.Complaint).filter(models.Complaint.id == cid).first()
    if not c: raise HTTPException(404)
    c.status = status
    if status == "resolved":
        c.resolved_at = datetime.utcnow()
    db.commit()
    return {"message": "Status updated"}

@complaint_router.post("/{cid}/comments")
def add_comment(cid: int, data: CommentIn, db: Session = Depends(get_db),
                user: models.User = Depends(get_current_user)):
    comment = models.ComplaintComment(complaint_id=cid, author_id=user.id, text=data.text)
    db.add(comment); db.commit()
    return {"message": "Comment added"}

@complaint_router.get("/{cid}/comments")
def get_comments(cid: int, db: Session = Depends(get_db),
                 _: models.User = Depends(get_current_user)):
    comments = db.query(models.ComplaintComment).filter(
        models.ComplaintComment.complaint_id == cid).all()
    return [{"id": c.id, "text": c.text, "author": c.author.name,
             "created_at": str(c.created_at)} for c in comments]


# ═══════════════════════════════════════════════════════
#  NOTICES & VOTING
# ═══════════════════════════════════════════════════════
notice_router = APIRouter(prefix="/api/notices", tags=["notices"])

class NoticeIn(BaseModel):
    title: str
    body: str
    category: str = "general"
    is_poll: bool = False
    poll_options: Optional[List[str]] = None
    poll_deadline: Optional[str] = None

@notice_router.get("")
def list_notices(db: Session = Depends(get_db),
                 _: models.User = Depends(get_current_user)):
    notices = db.query(models.Notice).order_by(models.Notice.created_at.desc()).all()
    return [{
        "id": n.id, "title": n.title, "body": n.body, "category": n.category,
        "posted_by": n.posted_by.name if n.posted_by else None,
        "is_poll": n.is_poll,
        "poll_options": json.loads(n.poll_options) if n.poll_options else None,
        "poll_deadline": str(n.poll_deadline) if n.poll_deadline else None,
        "vote_counts": _vote_counts(n),
        "created_at": str(n.created_at),
    } for n in notices]

def _vote_counts(notice):
    if not notice.is_poll or not notice.poll_options:
        return None
    opts = json.loads(notice.poll_options)
    counts = {i: 0 for i in range(len(opts))}
    for v in notice.votes:
        counts[v.option_index] = counts.get(v.option_index, 0) + 1
    return counts

@notice_router.post("")
def create_notice(data: NoticeIn, db: Session = Depends(get_db),
                  user: models.User = Depends(require_role("admin"))):
    n = models.Notice(
        title=data.title, body=data.body, category=data.category,
        posted_by_id=user.id, is_poll=data.is_poll,
        poll_options=json.dumps(data.poll_options) if data.poll_options else None,
        poll_deadline=datetime.fromisoformat(data.poll_deadline) if data.poll_deadline else None,
    )
    db.add(n); db.commit(); db.refresh(n)
    return {"id": n.id, "title": n.title}

@notice_router.post("/{nid}/vote")
def vote(nid: int, option_index: int, db: Session = Depends(get_db),
         user: models.User = Depends(get_current_user)):
    exists = db.query(models.Vote).filter(
        models.Vote.notice_id == nid, models.Vote.user_id == user.id).first()
    if exists: raise HTTPException(400, "Already voted")
    db.add(models.Vote(notice_id=nid, user_id=user.id, option_index=option_index))
    db.commit()
    return {"message": "Vote recorded"}


# ═══════════════════════════════════════════════════════
#  DASHBOARD STATS
# ═══════════════════════════════════════════════════════
stats_router = APIRouter(prefix="/api/stats", tags=["stats"])

@stats_router.get("")
def get_stats(db: Session = Depends(get_db),
              user: models.User = Depends(get_current_user)):
    from sqlalchemy import func
    today = datetime.utcnow().date()
    return {
        "total_flats": db.query(models.Flat).count(),
        "occupied_flats": db.query(models.Flat).filter(models.Flat.resident_id != None).count(),
        "total_residents": db.query(models.User).filter(models.User.role == "resident").count(),
        "open_complaints": db.query(models.Complaint).filter(
            models.Complaint.status.in_(["open","assigned","in_progress"])).count(),
        "today_visitors": db.query(models.Visitor).filter(
            func.date(models.Visitor.created_at) == today).count(),
        "pending_bills": db.query(models.MaintenanceBill).filter(
            models.MaintenanceBill.status == "pending").count(),
        "maintenance_collected": db.query(func.sum(models.MaintenanceBill.amount)).filter(
            models.MaintenanceBill.status == "paid").scalar() or 0,
    }
