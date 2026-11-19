"""Validated, tenant-scoped synthetic telecom tools. Never accept customer_id from the model."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import Subscription, Ticket, UsageRecord

PLANS = [{"name": "باقة النيل", "price_egp": 250, "data_gb": 100}, {"name": "باقة الأهرام", "price_egp": 400, "data_gb": 250}]

async def get_subscription_details(customer_id: str) -> dict:
    async with SessionLocal() as s:
        row = (await s.execute(select(Subscription).where(Subscription.customer_id == customer_id))).scalar_one_or_none()
    if not row: return {"error": "لم يتم العثور على اشتراك."}
    return {"plan": row.plan_name, "monthly_price_egp": row.monthly_price, "data_gb": row.data_gb, "status": row.status}

async def get_usage_summary(customer_id: str) -> dict:
    async with SessionLocal() as s:
        row = (await s.execute(select(UsageRecord).where(UsageRecord.customer_id == customer_id).order_by(UsageRecord.period.desc()))).scalars().first()
    if not row: return {"error": "لا توجد بيانات استخدام."}
    return {"period": row.period, "data_gb": row.data_gb, "minutes": row.minutes}

async def list_available_plans(_: str) -> dict: return {"plans": PLANS}

async def create_support_ticket(customer_id: str, subject: str, description: str) -> dict:
    subject, description = subject.strip()[:200], description.strip()[:2000]
    if not subject or not description: return {"error": "يلزم عنوان ووصف للتذكرة."}
    ticket_id = f"T-{uuid4().hex[:8].upper()}"
    async with SessionLocal() as s:
        s.add(Ticket(id=ticket_id, customer_id=customer_id, subject=subject, description=description))
        await s.commit()
    return {"ticket_id": ticket_id, "status": "open", "created_at": datetime.utcnow().isoformat()}

async def check_ticket_status(customer_id: str, ticket_id: str) -> dict:
    # Scope lookup to the authenticated customer: prevents cross-account disclosure.
    async with SessionLocal() as s:
        ticket = await s.get(Ticket, ticket_id.strip().upper())
    if not ticket or ticket.customer_id != customer_id: return {"error": "لم يتم العثور على تذكرة ضمن حسابك."}
    return {"ticket_id": ticket.id, "subject": ticket.subject, "status": ticket.status}
