import os
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./jobscout.db")

engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
