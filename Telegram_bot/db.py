import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, JSON, select
from contextlib import asynccontextmanager

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Создание асинхронного двигателя
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Создание асинхронной фабрики сессий
SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)

Base = declarative_base()

class Client(Base):
    __tablename__ = "clients"

    chat_id = Column(Integer, primary_key=True, index=True)
    wireguard_config = Column(JSON, index=True)
    outline_key = Column(JSON, index=True)
    payment_dates = Column(JSON, index=True)

async def init_db():
    async with engine.begin() as conn:
        # Создание всех таблиц
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_client(db: AsyncSession, chat_id: int) -> Client:
    result = await db.execute(
        select(Client).filter(Client.chat_id == chat_id)
    )
    return result.scalars().first()

async def save_client(db: AsyncSession, client: Client):
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client
