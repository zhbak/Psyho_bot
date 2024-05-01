from sqlalchemy import Table, Column, Integer, DateTime, String, MetaData
from sqlalchemy import create_engine, Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column ,sessionmaker

Base = declarative_base()


class PsyUsersTable(Base):
    __tablename__ = "psy_users_table"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    remaining_sessions_count: Mapped[int]
    unix_time_end: Mapped[int]
    remaining_days: Mapped[int]


"""
# postgres modelling
metadata_obj = MetaData()

psy_users_table = Table(
    "psy_users_table",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("remaining_sessions_count", Integer),
    Column("date_period_start", DateTime),
    Column("date_period_end", DateTime)
)
"""