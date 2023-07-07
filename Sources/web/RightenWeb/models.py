"""from RightenWeb import db
from sqlalchemy import Table
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
CONN_STR = '///E:/Projects\Budgeter_personal\Finances.sqlite3'
engine = create_engine(CONN_STR, echo=True)
class MyClass(Base):
    __table__ = Table('Income', Base.metadata,
                    autoload=True, autoload_with=egine)
    
"""
from sqlalchemy.sql import select
from sqlalchemy import create_engine, MetaData, Table

CONN_STR = '///E:/Projects\Budgeter_personal\Finances.sqlite3'
engine = create_engine(CONN_STR, echo=True)
metadata = MetaData()
income = Table('Income', metadata, autoload=True,
                           autoload_with=engine)
cols = income.c


with engine.connect() as conn:

    query = (
        select([cols.created_at, cols.name])
                .order_by(cols.created_at)
                .limit(1)
    )
    for row in conn.execute(query):
        print(row)


