import polars as pl

from finanzmaschine_staking.orm.near.staking_balance_snapshot import StakingBalanceSnapshot

ACCOUNT_ID = "account_id"
POOL_ID = "pool_id"
BLOCK_HEIGHT = "block_height"
STAKED_BALANCE_YOCTO_STR = "staked_balance_yocto_str"
UNSTAKED_BALANCE_YOCTO_STR = "staked_balance_yocto_str"

SCHEMA = {
    ACCOUNT_ID: pl.String,
    POOL_ID: pl.String,
    BLOCK_HEIGHT: pl.Int64,
    STAKED_BALANCE_YOCTO_STR: pl.String,
    UNSTAKED_BALANCE_YOCTO_STR: pl.String,
}

df_staking_balance_snapshots = pl.DataFrame(schema=SCHEMA)


def add_snapshot(
    df: pl.DataFrame,
    snapshot: StakingBalanceSnapshot,
) -> pl.DataFrame:

    df_duplicate = df.filter(
        (pl.col(ACCOUNT_ID) == snapshot.account_id)
        & (pl.col(POOL_ID) == snapshot.pool_id)
        & (pl.col(BLOCK_HEIGHT) == snapshot.block_height)
    )

    if not df_duplicate.is_empty():
        raise ValueError(
            "Snapshot already exists for "
            f"{ACCOUNT_ID}={snapshot.account_id}, "
            f"{POOL_ID}={snapshot.pool_id}, "
            f"{BLOCK_HEIGHT}={snapshot.block_height}"
        )

    df_row = pl.DataFrame(
        {
            ACCOUNT_ID: [snapshot.account_id],
            POOL_ID: [snapshot.pool_id],
            BLOCK_HEIGHT: [snapshot.block_height],
            STAKED_BALANCE_YOCTO_STR: [snapshot.staked_balance_yocto_str],
            UNSTAKED_BALANCE_YOCTO_STR: [snapshot.unstaked_balance_yocto_str],
        },
        schema=SCHEMA,
    )

    return (
        pl.concat([df, df_row])
        .sort([
            ACCOUNT_ID,
            POOL_ID,
            BLOCK_HEIGHT,
        ])
    )


def get_snapshot(
    df: pl.DataFrame,
    account_id: str,
    pool_id: str,
    block_height: int,
) -> StakingBalanceSnapshot | None:
    df_snapshot = df.filter(
        (pl.col(ACCOUNT_ID) == account_id)
        & (pl.col(POOL_ID) == pool_id)
        & (pl.col(BLOCK_HEIGHT) == block_height)
    )

    if df_snapshot.is_empty():
        return None

    if df_snapshot.height > 1:
        raise RuntimeError(
            "Multiple snapshots found for "
            f"{ACCOUNT_ID}={account_id}, "
            f"{POOL_ID}={pool_id}, "
            f"{BLOCK_HEIGHT}={block_height}"
        )

    row = df_snapshot.row(0, named=True)

    return StakingBalanceSnapshot(
        account_id=row[ACCOUNT_ID],
        pool_id=row[POOL_ID],
        block_height=row[BLOCK_HEIGHT],
        staked_balance_yocto_str=row[STAKED_BALANCE_YOCTO_STR],
        unstaked_balance_yocto_str=row[UNSTAKED_BALANCE_YOCTO_STR],
    )
