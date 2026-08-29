from datetime import datetime
from pathlib import Path

import polars as pl

from finanzmaschine_staking.orm.near.balance_snapshot import BalanceSnapshot

ACCOUNT_ID = "account_id"
POOL_ID = "pool_id"
BLOCK_HEIGHT = "block_height"
STAKED_BALANCE_YOCTO_STR = "staked_balance_yocto_str"
UNSTAKED_BALANCE_YOCTO_STR = "unstaked_balance_yocto_str"

SCHEMA = {
    ACCOUNT_ID: pl.String,
    POOL_ID: pl.String,
    BLOCK_HEIGHT: pl.Int64,
    STAKED_BALANCE_YOCTO_STR: pl.String,
    UNSTAKED_BALANCE_YOCTO_STR: pl.String,
}

df_near_staking_balance_snapshots = pl.DataFrame(schema=SCHEMA)


def add_snapshot(snapshot: BalanceSnapshot) -> None:
    global df_near_staking_balance_snapshots

    df_duplicate = df_near_staking_balance_snapshots.filter(
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

    df_near_staking_balance_snapshots = (
        pl.concat([df_near_staking_balance_snapshots, df_row])
        .sort([
            ACCOUNT_ID,
            POOL_ID,
            BLOCK_HEIGHT,
        ])
    )


def get_snapshot(
    account_id: str,
    pool_id: str,
    block_height: int,
) -> BalanceSnapshot | None:
    df_snapshot = df_near_staking_balance_snapshots.filter(
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

    return BalanceSnapshot(
        account_id=row[ACCOUNT_ID],
        pool_id=row[POOL_ID],
        block_height=row[BLOCK_HEIGHT],
        staked_balance_yocto_str=row[STAKED_BALANCE_YOCTO_STR],
        unstaked_balance_yocto_str=row[UNSTAKED_BALANCE_YOCTO_STR],
    )


def save_snapshots(target_dir: str | Path | None = None) -> None:
    target_dir = Path(target_dir) if target_dir is not None else Path.cwd()
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

    file_stem = (
        target_dir / f"near_staking_balance_snapshots_{timestamp}"
    )

    df_near_staking_balance_snapshots.write_csv(
        file_stem.with_suffix(".csv")
    )
    df_near_staking_balance_snapshots.write_parquet(
        file_stem.with_suffix(".parquet")
    )


def load_snapshots_from_parquet(parquet_path: str | Path) -> None:
    global df_near_staking_balance_snapshots

    df = pl.read_parquet(parquet_path)

    if df.schema != SCHEMA:
        raise ValueError(
            f"Expected schema {SCHEMA}, got {df.schema}"
        )

    df_near_staking_balance_snapshots = df


def clear_snapshots() -> None:
    global df_near_staking_balance_snapshots

    df_near_staking_balance_snapshots = pl.DataFrame(schema=SCHEMA)


def get_snapshot_deltas() -> pl.DataFrame:
    return (
        df_near_staking_balance_snapshots
        .sort([
            ACCOUNT_ID,
            POOL_ID,
            BLOCK_HEIGHT,
        ])
        .select(
            pl.col(BLOCK_HEIGHT),
            pl.col(POOL_ID),
            pl.col(ACCOUNT_ID),

            pl.col(BLOCK_HEIGHT)
            .diff()
            .over([ACCOUNT_ID, POOL_ID])
            .alias("delta_blocks"),

            pl.col(STAKED_BALANCE_YOCTO_STR)
            .cast(pl.Decimal(precision=38, scale=0))
            .diff()
            .over([ACCOUNT_ID, POOL_ID])
            .alias("staked_delta_yocto"),

            pl.col(UNSTAKED_BALANCE_YOCTO_STR)
            .cast(pl.Decimal(precision=38, scale=0))
            .diff()
            .over([ACCOUNT_ID, POOL_ID])
            .alias("unstaked_delta_yocto"),
        )
    )
