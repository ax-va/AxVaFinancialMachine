from finanzmaschine_data.staking.orm.near_staking_action import NearStakingAction, NearStakingActionType


def create_near_staking_action(
    raw_tx: dict,
) -> NearStakingAction | None:
    transaction = raw_tx["transaction"]

    actions = transaction.get("actions", [])
    if not actions:
        return None

    if len(actions) > 1:
        # TODO: Support multi-action transactions
        raise NotImplementedError(f"Multi-action transactions not supported yet: {actions}")

    function_call = actions[0].get("FunctionCall")
    if function_call is None:
        return None

    method_name = function_call["method_name"]

    try:
        action_type = NearStakingActionType(method_name)
    except ValueError:
        return None

    receipt_id = _extract_receipt_id(raw_tx)

    receipt = _extract_receipt(
        raw_tx=raw_tx,
        receipt_id=receipt_id,
    )

    return NearStakingAction(
        receipt_id=receipt_id,
        tx_hash=transaction["hash"],
        account_id=transaction["signer_id"],
        pool_id=transaction["receiver_id"],
        block_height=receipt["execution_outcome"]["block_height"],
        action_type=action_type,
        quantity_yocto_str=_extract_quantity_yocto_str(
            function_call=function_call,
            action_type=action_type,
        ),
    )


def _extract_receipt_id(raw_tx: dict) -> str:
    receipt_ids = (
        raw_tx["execution_outcome"]
        ["outcome"]
        ["receipt_ids"]
    )

    if len(receipt_ids) != 1:
        raise RuntimeError(f"Expected exactly one receipt, got {receipt_ids}")

    return receipt_ids[0]


def _extract_receipt(
    raw_tx: dict,
    receipt_id: str,
) -> dict:
    for item in raw_tx["receipts"]:
        if item["receipt"]["receipt_id"] == receipt_id:
            return item

    raise RuntimeError(f"Receipt {receipt_id} not found")


def _extract_quantity_yocto_str(
    function_call: dict,
    action_type: NearStakingActionType,
) -> str | None:

    if action_type in (
        NearStakingActionType.DEPOSIT,
        NearStakingActionType.DEPOSIT_AND_STAKE,
    ):
        return function_call["deposit"]

    if action_type in (
        NearStakingActionType.STAKE_ALL,
        NearStakingActionType.UNSTAKE_ALL,
        NearStakingActionType.WITHDRAW_ALL,
    ):
        return None

    if action_type in (
        NearStakingActionType.STAKE,
        NearStakingActionType.UNSTAKE,
        NearStakingActionType.WITHDRAW,
    ):
        # TODO: STAKE, UNSTAKE, WITHDRAW
        raise NotImplementedError(f"TAKE, UNSTAKE, WITHDRAW not supported yet: {action_type}")

    return None
