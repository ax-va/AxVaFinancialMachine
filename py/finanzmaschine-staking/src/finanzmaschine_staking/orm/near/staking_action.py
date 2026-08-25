from enum import StrEnum
from typing import Any, Self

from pydantic import field_validator
from sqlalchemy import BigInteger
from sqlmodel import Field, SQLModel


class StakingActionType(StrEnum):
    DEPOSIT_AND_STAKE = "deposit_and_stake"
    DEPOSIT = "deposit"
    STAKE = "stake"
    STAKE_ALL = "stake_all"
    UNSTAKE = "unstake"
    UNSTAKE_ALL = "unstake_all"
    WITHDRAW = "withdraw"
    WITHDRAW_ALL = "withdraw_all"


class StakingAction(SQLModel, table=True):
    __tablename__ = "near_staking_actions"

    receipt_id: str = Field(primary_key=True)
    tx_tash: str = Field(index=True)
    account_id: str = Field(index=True)
    pool_id: str = Field(index=True)

    block_height: int = Field(
        foreign_key='near_block_heights.block_height',
        index=True,
        sa_type=BigInteger,
    )

    action_type: StakingActionType
    quantity_yocto_str: str | None = None

    @field_validator("quantity_yocto_str")
    @classmethod
    def validate_quantity_yocto_str(cls, value: str | None) -> str | None:
        if value is not None and not value.isdigit():
            raise ValueError(f"Quantity yocto string must contain only digits: {value}")
        return value

    @property
    def quantity_yocto(self) -> int | None:
        if self.quantity_yocto_str is None:
            return None
        return int(self.quantity_yocto_str)
