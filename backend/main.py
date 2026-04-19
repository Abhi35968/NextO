"""
NestO — FastAPI Main Application
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import engine, Base
import models
from routers import (auth_router, resident_router, maintenance_router,
                     visitor_router, complaint_router, notice_router, stats_router)
from auth import hash_password
from database import SessionLocal

# ── Create DB tables ──────────────────────────────────────────
Base.metadata.create_all(bind=engine)

app = FastAPI(title="NestO API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ──────────────────────────────────────────
for router in [auth_router, resident_router, maintenance_router,
               visitor_router, complaint_router, notice_router, stats_router]:
    app.include_router(router)

# ── Serve frontend ────────────────────────────────────────────
FRONTEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND, "static")), name="static")

@app.get("/", include_in_schema=False)
def root():
    return FileResponse(os.path.join(FRONTEND, "index.html"))

@app.get("/{page}.html", include_in_schema=False)
def pages(page: str):
    fp = os.path.join(FRONTEND, f"{page}.html")
    if os.path.exists(fp):
        return FileResponse(fp)
    return FileResponse(os.path.join(FRONTEND, "index.html"))


# ── Seed demo data ────────────────────────────────────────────
def seed():
    db = SessionLocal()
    try:
        if db.query(models.User).count() > 0:
            return  # Already seeded

        # Admin
        admin = models.User(name="Admin User", email="admin@society.com",
                            hashed_password=hash_password("admin123"), role="admin")
        # Resident
        r1 = models.User(name="Rahul Sharma", email="rahul@email.com",
                         phone="9876543210",
                         hashed_password=hash_password("resident123"), role="resident")
        r2 = models.User(name="Priya Patel", email="priya@email.com",
                         phone="9876543211",
                         hashed_password=hash_password("resident123"), role="resident")
        # Security
        sec = models.User(name="Ram Guard", email="guard@society.com",
                          hashed_password=hash_password("guard123"), role="security")
        db.add_all([admin, r1, r2, sec])
        db.commit()
        db.refresh(r1); db.refresh(r2)

        # Flats
        f1 = models.Flat(flat_number="A-101", block="A", floor=1,
                         area_sqft=1200, resident_id=r1.id, is_owner=True)
        f2 = models.Flat(flat_number="A-102", block="A", floor=1,
                         area_sqft=900, resident_id=r2.id, is_owner=False)
        f3 = models.Flat(flat_number="B-201", block="B", floor=2, area_sqft=1500)
        db.add_all([f1, f2, f3]); db.commit()

        # Notice
        from datetime import datetime
        notice = models.Notice(
            title="Society Meeting — April 30",
            body="Monthly society meeting to discuss maintenance charges and upcoming repairs. All residents are requested to attend.",
            category="event", posted_by_id=admin.id,
        )
        poll = models.Notice(
            title="Should we install EV charging stations?",
            body="Vote on whether we should install EV charging points in the parking area.",
            category="poll", posted_by_id=admin.id,
            is_poll=True, poll_options='["Yes, install immediately","Yes, but after 6 months","No, not needed"]',
            poll_deadline=datetime(2025, 5, 1),
        )
        db.add_all([notice, poll]); db.commit()
        print("[NestO] Demo data seeded.")
    finally:
        db.close()

seed()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
