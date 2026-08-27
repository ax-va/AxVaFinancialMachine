from finanzmaschine_staking.orm.near.balance_snapshot import BalanceSnapshot
from finanzmaschine_staking.sync_clients.near.staking_client import StakingClient


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
    between `left_snapshot.block_height` and `right_block_height`.
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
        return None

    while right_snapshot.block_height - left_snapshot.block_height > 1:
        middle_block_height = (left_snapshot.block_height + right_snapshot.block_height) // 2

        middle_snapshot = staking_client.get_snapshot(
            account_id=account_id,
            pool_id=pool_id,
            block_height=middle_block_height,
        )

        if are_balances_equal(left_snapshot, middle_snapshot):
            left_snapshot = middle_snapshot

        else:
            right_snapshot = middle_snapshot

    return right_snapshot
