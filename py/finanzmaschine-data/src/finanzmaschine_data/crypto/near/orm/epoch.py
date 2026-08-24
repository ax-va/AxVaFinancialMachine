from sqlalchemy import BigInteger
from sqlmodel import Field, SQLModel


class Epoch(SQLModel, table=True):
    __tablename__ = 'epochs'

    epoch_id: str = Field(primary_key=True)

    block_height_start: int = Field(
        index=True,
        unique=True,
        sa_type=BigInteger,
    )

    block_height_end: int | None = Field(
        default=None,
        sa_type=BigInteger,
    )
