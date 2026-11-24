"""Seed reproducible synthetic campus users and complaints for CA4 demonstrations.
All records are fictional. Run: python seed_synthetic_data.py
"""
from datetime import datetime, timedelta, timezone
import random
from sqlalchemy import select
from app.database import Base, engine, SessionLocal
from app.models import User, Complaint, AIUsage
from app.security import hash_password

random.seed(42)
Base.metadata.create_all(bind=engine)
db = SessionLocal()

ACCOUNTS = [
    ("Campus Administrator", "admin@gmail.com", "Admin@12345", "admin", "Administration"),
    ("Ravi Kumar · Plumbing", "worker1@gmail.com", "Worker@12345", "staff", "Plumbing"),
    ("Aman Singh · Electrical", "worker2@gmail.com", "Worker@12345", "staff", "Electrical"),
    ("Karan Sharma · Carpentry", "worker3@gmail.com", "Worker@12345", "staff", "Carpentry"),
    ("Arjun Kumar · Cleaning", "worker4@gmail.com", "Worker@12345", "staff", "Housekeeping"),
    ("Sandeep Verma · HVAC", "worker5@gmail.com", "Worker@12345", "staff", "HVAC"),
    ("Mohit Singh · IT and Network", "worker6@gmail.com", "Worker@12345", "staff", "IT and Network"),
    ("Rahul Das · Civil Maintenance", "worker7@gmail.com", "Worker@12345", "staff", "Civil Maintenance"),
    ("Deepak Kumar · General Maintenance", "worker8@gmail.com", "Worker@12345", "staff", "General Maintenance"),
    ("Student One", "student1@gmail.com", "Student@12345", "student", ""),
    ("Student Two", "student2@gmail.com", "Student@12345", "student", ""),
    ("Student Three", "student3@gmail.com", "Student@12345", "student", ""),
    ("Student Four", "student4@gmail.com", "Student@12345", "student", ""),
    ("Student Five", "student5@gmail.com", "Student@12345", "student", ""),
]

SAMPLES = [
    ("Water leakage near washroom", "Water is continuously leaking from the pipe near the second floor washroom.", "Plumbing", "high", "Academic Block B, Floor 2"),
    ("Projector not working", "The classroom projector does not turn on during lectures.", "IT / Network", "medium", "Block A, Room 204"),
    ("Broken corridor light", "The corridor light is flickering and the area is dark after 6 PM.", "Electrical / Safety", "high", "Library, East Corridor"),
    ("Overflowing dustbin", "Waste bin has not been cleared and there is a bad smell.", "Sanitation", "medium", "Hostel C, Ground Floor"),
    ("Wi-Fi unavailable", "Campus Wi-Fi is disconnected in the computer lab.", "IT / Network", "high", "Computer Lab 3"),
    ("Broken classroom chair", "Several chairs have loose screws and are unsafe to use.", "Facilities", "low", "Block D, Room 110"),
    ("Air conditioner issue", "The air conditioner is not cooling the seminar room.", "Facilities", "medium", "Seminar Hall"),
    ("Exposed electrical wire", "An exposed wire is visible beside the staircase. Please inspect urgently.", "Electrical / Safety", "high", "Block C, Staircase 1"),
    ("Tap water not stopping", "The tap keeps running even when closed tightly.", "Plumbing", "low", "Hostel A, Floor 1"),
    ("Washroom cleaning required", "The washroom needs cleaning and replenishment of supplies.", "Sanitation", "medium", "Admin Building, Floor 1"),
]
STATUSES = ["submitted", "assigned", "accepted", "in_progress", "completed", "reopened"]

try:
    users = {}
    for name, email, password, role, specialization in ACCOUNTS:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(name=name, email=email, password_hash=hash_password(password), role=role, specialization=specialization)
            db.add(user)
        else:
            user.name, user.role, user.password_hash, user.specialization = name, role, hash_password(password), specialization
        users[email] = user
    db.flush()

    students = [users[x] for x in ["student1@gmail.com", "student2@gmail.com", "student3@gmail.com", "student4@gmail.com", "student5@gmail.com"]]
    workers = [users[f"worker{i}@gmail.com"] for i in range(1, 9)]
    existing = db.scalar(select(Complaint.id).where(Complaint.title.like("SYNTH-%")).limit(1))
    if not existing:
        for i in range(100):
            title, description, category, priority, location = random.choice(SAMPLES)
            status = random.choices(STATUSES, weights=[18, 20, 12, 15, 30, 5])[0]
            worker = random.choice(workers)
            assigned = None if status == "submitted" else worker.id
            created = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 75), hours=random.randint(0, 23))
            complaint = Complaint(
                title=f"SYNTH-{i+1:03d} · {title}", description=description,
                category=category, priority=priority, status=status,
                location=location, reporter_id=random.choice(students).id,
                assigned_to_id=assigned, ai_provider=random.choice(["groq", "gemini", "local_tfidf"]),
                ai_model="synthetic-demo-classifier", ai_confidence=round(random.uniform(0.72, 0.99), 2),
                ai_review_required=(i % 9 == 0),
                resolution_note="Issue inspected and addressed (synthetic demo record)." if status == "completed" else "",
                created_at=created, updated_at=created + timedelta(hours=random.randint(1, 48)),
            )
            db.add(complaint)
        db.add(AIUsage(provider="local_tfidf", model="synthetic-demo-classifier", input_tokens=0, output_tokens=0, estimated_cost_usd=0.0, success=True))
    db.commit()
    print("Synthetic campus data is ready (fictional records).")
    print("ADMIN: admin@gmail.com / Admin@12345")
    print("WORKER: worker1@gmail.com / Worker@12345")
    print("WORKERS: worker1@gmail.com through worker8@gmail.com / Worker@12345")
    print("STUDENT: student1@gmail.com / Student@12345")
    print("STUDENT 2: student2@gmail.com / Student@12345")
    print("100 synthetic complaints are generated once; rerunning does not duplicate them.")
finally:
    db.close()
