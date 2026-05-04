# This file is responsible for opening and managing the connection to Postgres.

# Python code
#    ↓
# Session (ORM unit of work)
#    ↓
# Engine (SQLAlchemy core coordinator)
#    ↓
# DB Driver (psycopg2)
#    ↓
# Connection (TCP socket)
#    ↓
# PostgreSQL server

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# =========================
# CONFIGURATION
# =========================

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# =========================
# ENGINE
# =========================

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    echo=False  # set True for debugging SQL
)

# =========================
# SESSION
# =========================

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

# =========================
# BASE CLASS (for models)
# =========================

Base = declarative_base()
