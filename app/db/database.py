from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.db.models import Base, Customer, Subscription, UsageRecord

engine = create_async_engine(settings.database_url, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def initialize_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as s:
        if not await s.get(Customer, "cust_demo"):
            s.add_all([Customer(id="cust_demo", name="أحمد علي", phone="01000000000"),
                Subscription(customer_id="cust_demo", plan_name="باقة النيل", monthly_price=250, data_gb=100),
                UsageRecord(customer_id="cust_demo", period="2026-11", data_gb=42.5, minutes=380)])
            await s.commit()
