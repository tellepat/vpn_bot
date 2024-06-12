import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Date, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import date
from sqlalchemy import JSON

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
print(DATABASE_URL)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Client(Base):
    __tablename__ = "clients"

    chat_id = Column(Integer, primary_key=True, index=True)
    wireguard_config = Column(JSON, index=True)
    outline_key = Column(JSON, index=True)
    payment_dates = Column(JSON, index=True)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_client(db, chat_id: int) -> Client:
    return db.query(Client).filter(Client.chat_id == chat_id).first()


def save_client(db, client: Client):
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

