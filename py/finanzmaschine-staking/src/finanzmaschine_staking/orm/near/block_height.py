from datetime import datetime

from sqlalchemy import BigInteger
from sqlmodel import Field, SQLModel


class BlockHeight(SQLModel, table=True):
    __tablename__ = 'near_block_heights'

    block_height: int = Field(
        primary_key=True,
        sa_type=BigInteger,
    )

    timestamp: datetime

    timestamp_nanosec: int = Field(
        sa_type=BigInteger,
    )
