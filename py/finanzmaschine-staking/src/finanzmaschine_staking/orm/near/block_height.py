from datetime import datetime, timezone

from sqlalchemy import BigInteger
from sqlmodel import Field, SQLModel


class BlockHeight(SQLModel, table=True):
    __tablename__ = 'near_block_heights'

    block_height: int = Field(
        primary_key=True,
        sa_type=BigInteger,
    )

    timestamp_nanosec: int = Field(
        sa_type=BigInteger,
    )

    @property
    def timestamp(self) -> datetime:
        return datetime.fromtimestamp(
            self.timestamp_nanosec / 1e9,
            tz=timezone.utc,
        )
