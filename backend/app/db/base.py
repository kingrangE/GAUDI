"""Shared SQLAlchemy declarative base.

Every feature's models inherit from this `Base` so a single `create_all()`
sees all tables. Keep this module dependency-free (no feature imports).
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
