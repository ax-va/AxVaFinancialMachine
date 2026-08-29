import logging
from pathlib import Path

from finanzmaschine_staking.dataframes.near.balance_snapshots import clear_snapshots, add_snapshot, save_snapshots
from finanzmaschine_staking.orm.near.balance_snapshot import BalanceSnapshot
from finanzmaschine_staking.sync_clients.near.rpc_client_exeptions import BlockHeightNotFoundError
from finanzmaschine_staking.sync_clients.near.staking_client import StakingClient

logger = logging.getLogger(__name__)


def are_balances_equal(
    snapshot_1: BalanceSnapshot,
    snapshot_2: BalanceSnapshot,
) -> bool:
    return (
        snapshot_1.staked_balance_yocto_str == snapshot_2.staked_balance_yocto_str
        and snapshot_1.unstaked_balance_yocto_str == snapshot_2.unstaked_balance_yocto_str
    )


def find_next_balance_change(
    staking_client: StakingClient,
    left_snapshot: BalanceSnapshot,
    right_block_height: int,
) -> BalanceSnapshot | None:
    """
    Finds the next snapshot with changed balance (staked or unstaked balances)
    between left snapshot and right block height searching from left to right.
    Returns `None`, if no balance snapshot is detected in the given interval.

    Args:
        staking_client: NEAR staking client.
        left_snapshot: Left snapshot that sets the left block height.
        right_block_height: Right block height.

    Returns:
        The snapshot of the next balance change or `None`.

    Raises:
        ValueError: If `right_block_height` is less than
        or equal to `left_snapshot.block_height`.
    """
    logger.debug(
        f"Starting search for next balance change between block heights "
        f"{left_snapshot.block_height} and {right_block_height}"
    )

    if right_block_height <= left_snapshot.block_height:
        raise ValueError(
            "`right_block_height` must be greater than `left_snapshot.block_height`"
        )

    account_id = left_snapshot.account_id
    pool_id = left_snapshot.pool_id

    right_snapshot = staking_client.get_snapshot(
        account_id=account_id,
        pool_id=pool_id,
        block_height=right_block_height,
    )

    if are_balances_equal(left_snapshot, right_snapshot):
        logger.debug(
            f"No balance change between block heights "
            f"{left_snapshot.block_height} and {right_snapshot.block_height}"
        )

        return None

    while right_snapshot.block_height - left_snapshot.block_height > 1:
        logger.debug(
            f"Searching balance change between block heights "
            f"{left_snapshot.block_height} and {right_snapshot.block_height}"
        )

        middle_block_height = (left_snapshot.block_height + right_snapshot.block_height) // 2
        right_block_height = middle_block_height

        while left_snapshot.block_height < right_block_height:
            try:
                middle_snapshot = staking_client.get_snapshot(
                    account_id=account_id,
                    pool_id=pool_id,
                    block_height=right_block_height,
                )

            except BlockHeightNotFoundError:
                logger.warning(f"Block height not found: {right_block_height}")

                right_block_height -= 1

            else:
                break

        else:
            left_block_height = middle_block_height
            left_block_height += 1

            while left_block_height < right_snapshot.block_height:
                try:
                    middle_snapshot = staking_client.get_snapshot(
                        account_id=account_id,
                        pool_id=pool_id,
                        block_height=left_block_height,
                    )

                except BlockHeightNotFoundError:
                    logger.warning(f"Block height not found: {left_block_height}")

                    left_block_height += 1

                else:
                    break

            else:
                logger.debug(f"Found next balance change at block height {right_snapshot.block_height}")

                return right_snapshot

        if are_balances_equal(left_snapshot, middle_snapshot):
            left_snapshot = middle_snapshot
        else:
            right_snapshot = middle_snapshot

    logger.debug(f"Found next balance change at block height {right_snapshot.block_height}")

    return right_snapshot


def find_balance_changes(
    staking_client: StakingClient,
    left_snapshot: BalanceSnapshot,
    right_block_height: int,
) -> list[BalanceSnapshot]:
    """
    Finds all balance changes between left snapshot and right block height.

    Args:
        staking_client: NEAR staking client.
        left_snapshot: Left snapshot that sets the left block height.
        right_block_height: Right block height.

    Returns:
        The snapshots in ascending block-height order.

    Raises:
        ValueError: If `find_next_balance_change` raises `ValueError`.
    """
    changes: list[BalanceSnapshot] = []

    while True:
        next_snapshot = find_next_balance_change(
            staking_client=staking_client,
            left_snapshot=left_snapshot,
            right_block_height=right_block_height,
        )

        if next_snapshot is None:
            break

        changes.append(next_snapshot)
        left_snapshot = next_snapshot

    return changes


def find_balance_changes_in_chunks(
    staking_client: StakingClient,
    left_snapshot: BalanceSnapshot,
    right_block_height: int,
    chunk_size: int,
    target_dir: str | Path,
) -> None:
    current_left_snapshot = left_snapshot
    chunk_left_block_height = current_left_snapshot.block_height

    while chunk_left_block_height < right_block_height:
        chunk_right_block_height = min(
            chunk_left_block_height + chunk_size,
            right_block_height,
        )

        snapshots = find_balance_changes(
            staking_client=staking_client,
            left_snapshot=current_left_snapshot,
            right_block_height=chunk_right_block_height,
        )

        clear_snapshots()

        for snapshot in snapshots:
            add_snapshot(snapshot)

        save_snapshots(target_dir)

        chunk_left_block_height = chunk_right_block_height

        block_height_offset = 0
        while True:

            if chunk_right_block_height + block_height_offset > right_block_height:
                return

            try:
                current_left_snapshot = staking_client.get_snapshot(
                    account_id=current_left_snapshot.account_id,
                    pool_id=current_left_snapshot.pool_id,
                    block_height=chunk_right_block_height + block_height_offset,
                )
                break

            except BlockHeightNotFoundError:
                block_height_offset += 1
