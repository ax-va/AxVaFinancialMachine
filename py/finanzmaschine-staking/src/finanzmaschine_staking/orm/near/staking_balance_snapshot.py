from pydantic import field_validator
from sqlalchemy import BigInteger
from sqlmodel import Field, SQLModel


class StakingBalanceSnapshot(SQLModel, table=True):
    __tablename__ = "near_staking_balance_snapshots"

    account_id: str = Field(primary_key=True)
    pool_id: str = Field(primary_key=True)

    block_height: int = Field(
        primary_key=True,
        foreign_key='near_block_heights.block_height',
        sa_type=BigInteger,
    )

    staked_balance_yocto_str: str
    unstaked_balance_yocto_str: str

    @field_validator(
        'staked_balance_yocto_str',
        'unstaked_balance_yocto_str',
    )
    @classmethod
    def validate_balance_yocto_str(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError(f"Balance yocto sting must contain only digits: {value}")
        return value

    @property
    def staked_balance_yocto(self) -> int:
        return int(self.staked_balance_yocto_str)

    @property
    def unstaked_balance_yocto(self) -> int:
        return int(self.unstaked_balance_yocto_str)

    @property
    def total_balance_yocto(self) -> int:
        return self.staked_balance_yocto + self.unstaked_balance_yocto
