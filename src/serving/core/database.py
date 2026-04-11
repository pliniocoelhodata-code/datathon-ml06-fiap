import logging
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

logger = logging.getLogger(__name__)

_raw_url = os.getenv("DATABASE_URL")
SQLALCHEMY_DATABASE_URL = (_raw_url.strip() if _raw_url else "")

if not SQLALCHEMY_DATABASE_URL:
    raise ValueError(
        "Defina DATABASE_URL no ambiente ou no arquivo .env (raiz do repositório)."
    )

_connect_args = (
    {"check_same_thread": False}
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite")
    else {}
)

logger.info("Engine SQLAlchemy inicializado.")

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
