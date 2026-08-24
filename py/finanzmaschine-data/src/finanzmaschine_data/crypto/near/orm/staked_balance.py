from pydantic import field_validator
from sqlalchemy import BigInteger
from sqlmodel import Field, SQLModel


class StakeBalance(SQLModel, table=True):
    __tablename__ = "staked_balances"

    account_id: str = Field(primary_key=True)
    pool_id: str = Field(primary_key=True)

    block_height: int = Field(
        primary_key=True,
        foreign_key='block_heights.block_height',
        sa_type=BigInteger,
    )

    balance_yocto_str: str

    @field_validator('balance_yocto_str')
    @classmethod
    def validate_balance_yocto_str(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError(f"`balance_yocto_str` must contain only digits: {value}")
        return value

    @property
    def balance_yocto(self) -> int:
        return int(self.balance_yocto_str)
