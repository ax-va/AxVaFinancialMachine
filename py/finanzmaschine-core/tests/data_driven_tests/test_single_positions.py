import re
from decimal import Decimal
from typing import TypeVar

import polars as pl
import pytest

from finanzmaschine_core.portfolio.operations.operation import parse_operation
from finanzmaschine_core.portfolio.positions.base_position import ClosingOrder
from finanzmaschine_core.helpers.decimal_helper import round_to_quantum
from finanzmaschine_core.portfolio.positions.priced_position import PricedPosition

P = TypeVar("P", bound="PricedPosition")


@pytest.fixture(scope="function")
def position(request) -> P:
    return request.getfixturevalue(request.param)


@pytest.fixture(scope="function")
def df_golden_values(request) -> pl.DataFrame:
    return request.getfixturevalue(request.param)


@pytest.fixture(scope="function")
def df_sold(request) -> pl.DataFrame:
    return request.getfixturevalue(request.param)


@pytest.mark.parametrize(
    "position,"
    "df_golden_values,"
    "df_sold,"
    "expected_position_quantity_in,"
    "expected_position_quantity_open,"
    "expected_position_quantity_closed,"
    "expected_position_proceeds_sold,"
    "expected_position_cost_basis_sold,"
    "expected_position_pnl_sold",
    [
        (
            "ton_etp_position_fifo_fifo",
            "df_expected_ton_etp_fifo_fifo",
            "df_ton_etp_sold",
            Decimal("920.459107"),
            Decimal("109.459107"),
            Decimal("811"),
            Decimal("5065.52"),
            Decimal("5621.84"),
            Decimal("-556.32"),
        ),
        (
            "ton_etp_position_fifo_lifo",
            "df_expected_ton_etp_fifo_lifo",
            "df_ton_etp_sold",
            Decimal("920.459107"),
            Decimal("109.459107"),
            Decimal("811"),
            Decimal("5065.52"),
            Decimal("5441.20"),
            Decimal("-375.68"),
        ),
        (
            "ton_etp_position_lifo_fifo",
            "df_expected_ton_etp_lifo_fifo",
            "df_ton_etp_sold",
            Decimal("920.459107"),
            Decimal("109.459107"),
            Decimal("811"),
            Decimal("5065.52"),
            Decimal("5455.02"),
            Decimal("-389.50"),
        ),
        (
            "ton_etp_position_lifo_lifo",
            "df_expected_ton_etp_lifo_lifo",
            "df_ton_etp_sold",
            Decimal("920.459107"),
            Decimal("109.459107"),
            Decimal("811"),
            Decimal("5065.52"),
            Decimal("5241.67"),
            Decimal("-176.15"),
        ),
    ],
    indirect=["position", "df_golden_values", "df_sold"],
)
def test_position_closing(
    position: P,
    df_golden_values: pl.DataFrame,
    df_sold: pl.DataFrame,
    expected_position_quantity_in: Decimal,
    expected_position_quantity_open: Decimal,
    expected_position_quantity_closed: Decimal,
    expected_position_proceeds_sold: Decimal,
    expected_position_cost_basis_sold: Decimal,
    expected_position_pnl_sold: Decimal,
):
    # workaround for typechecker
    position: PricedPosition

    # Set initial sell-values
    sell_index = 0
    base_asset_flow = Decimal(df_sold.row(sell_index, named=True)["base_asset_flow"])
    record_quantity_to_close = abs(base_asset_flow)
    record_fee_to_close = Decimal(df_sold.row(sell_index, named=True)["fee"])

    # Set initial lot values
    lot_values = {
        lot: {
            "lot_quantity_open": lot.record_in.quantity,
            "lot_quantity_closed": Decimal("0"),
            "lot_proceeds_sold": Decimal("0"),
            "lot_cost_basis_sold": Decimal("0"),
            "lot_pnl_sold": Decimal("0"),
        } for lot in position.lots
    }

    for index, (record, lot) in enumerate(position.lot_by_record_sold.items()):

        record_quantity_open_before = lot_values[lot]["lot_quantity_open"]

        # Test closing_order
        expected_record_closing_order = ClosingOrder(df_golden_values.row(index, named=True)["closing_order"])
        assert position.closing_order_by_record_out[record] == expected_record_closing_order

        # Test sell_id
        expected_sell_id = df_golden_values.row(index, named=True)["sell_id"]
        assert sell_index + 1 == int(re.search(r"\d+", expected_sell_id).group())
        operation_type_str = df_sold.row(sell_index, named=True)["operation_type"]
        operation_variant_str = df_sold.row(sell_index, named=True)["operation_variant"]
        operation_named_tuple = parse_operation(operation_type_str, operation_variant_str)
        assert operation_named_tuple.variant in expected_sell_id

        # Test datetime_closed
        expected_record_datetime_sold = df_golden_values.row(index, named=True)["datetime_closed"]
        assert df_sold.row(sell_index, named=True)["datetime"] == expected_record_datetime_sold

        # Test lot_id
        expected_lot_id = df_golden_values.row(index, named=True)["lot_id"]
        assert position.get_lot_id(lot) == expected_lot_id

        # Test datetime_open
        expected_record_datetime_open = df_golden_values.row(index, named=True)["datetime_open"]
        assert lot.record_in.datetime == expected_record_datetime_open

        # Test quantity_open_before
        expected_record_quantity_open_before = Decimal(df_golden_values.row(index, named=True)["quantity_open_before"])
        assert record_quantity_open_before == expected_record_quantity_open_before

        # Test quantity_to_close
        expected_record_quantity_to_close = Decimal(df_golden_values.row(index, named=True)["quantity_to_close"])
        assert record_quantity_to_close == expected_record_quantity_to_close

        # Test quantity_closed
        expected_record_quantity_closed = Decimal(df_golden_values.row(index, named=True)["quantity_closed"])
        assert record.quantity == expected_record_quantity_closed
        record_quantity_open_after = record_quantity_open_before - expected_record_quantity_closed

        # Test quantity_remaining
        expected_record_quantity_remaining = Decimal(df_golden_values.row(index, named=True)["quantity_remaining"])
        record_quantity_remaining = record_quantity_to_close - record.quantity
        assert record_quantity_remaining == expected_record_quantity_remaining

        # Test quantity_open_after
        expected_record_quantity_open_after = Decimal(df_golden_values.row(index, named=True)["quantity_open_after"])
        assert record_quantity_open_after == expected_record_quantity_open_after

        # Test fee_to_closed
        expected_record_fee_to_close = Decimal(df_golden_values.row(index, named=True)["fee_to_close"])
        assert record_fee_to_close == expected_record_fee_to_close

        # Test fee_closed
        expected_record_fee_closed = Decimal(df_golden_values.row(index, named=True)["fee_closed"])
        assert record.fee == expected_record_fee_closed

        # Test fee_remaining
        expected_record_fee_remaining = Decimal(df_golden_values.row(index, named=True)["fee_remaining"])
        record_fee_remaining = record_fee_to_close - record.fee
        assert record_fee_remaining == expected_record_fee_remaining

        # Test proceeds_sold
        expected_record_proceeds_sold = Decimal(df_golden_values.row(index, named=True)["proceeds_sold"])
        record_proceeds_sold = round_to_quantum(
            record.quantity * record.price - record.fee,
            lot.record_in.quote_asset.quantum,
        )
        assert record_proceeds_sold == expected_record_proceeds_sold

        # Test cost_basis_sold
        expected_record_cost_basis_sold = Decimal(df_golden_values.row(index, named=True)["cost_basis_sold"])
        record_cost_basis_sold = round_to_quantum(
            record.quantity / lot.record_in.quantity * lot.cost_basis,
            lot.record_in.quote_asset.quantum,
        )
        assert record_cost_basis_sold == expected_record_cost_basis_sold

        # Test pnl_sold
        expected_record_pnl_sold = Decimal(df_golden_values.row(index, named=True)["pnl_sold"])
        record_pnl_sold = record_proceeds_sold - record_cost_basis_sold
        assert record_pnl_sold == expected_record_pnl_sold

        # Update values
        record_quantity_to_close = record_quantity_remaining
        record_fee_to_close = record_fee_remaining
        if record_quantity_to_close == Decimal("0"):
            sell_index += 1
            if sell_index < len(df_sold):
                base_asset_flow = Decimal(df_sold.row(sell_index, named=True)["base_asset_flow"])
                record_quantity_to_close = abs(base_asset_flow)
                record_fee_to_close = Decimal(df_sold.row(sell_index, named=True)["fee"])

        lot_values[lot]["lot_quantity_open"] = record_quantity_open_after
        lot_values[lot]["lot_quantity_closed"] += record.quantity
        lot_values[lot]["lot_proceeds_sold"] += record_proceeds_sold
        lot_values[lot]["lot_cost_basis_sold"] += record_cost_basis_sold
        lot_values[lot]["lot_pnl_sold"] += record_pnl_sold

    # Test position attributes
    assert position.quantity_open == expected_position_quantity_open
    assert position.quantity_closed == expected_position_quantity_closed
    assert position.quantity_open + position.quantity_closed == expected_position_quantity_in
    assert position.proceeds_sold == expected_position_proceeds_sold
    assert position.cost_basis_sold == expected_position_cost_basis_sold
    assert position.pnl_sold == expected_position_pnl_sold

    # Set initial position values to test through lots
    position_proceeds_sold = Decimal("0")
    position_cost_basis_sold = Decimal("0")
    position_pnl_sold = Decimal("0")

    for lot in position.lots:

        # Test lot attributes
        assert lot.quantity_open == lot_values[lot]["lot_quantity_open"]
        assert lot.quantity_closed == lot_values[lot]["lot_quantity_closed"]
        assert lot.proceeds_sold == lot_values[lot]["lot_proceeds_sold"]
        assert lot.cost_basis_sold == lot_values[lot]["lot_cost_basis_sold"]
        assert lot.pnl_sold == lot_values[lot]["lot_pnl_sold"]

        position_proceeds_sold += lot.proceeds_sold
        position_cost_basis_sold += lot.cost_basis_sold
        position_pnl_sold += lot.pnl_sold

    # Test position attributes through lots
    assert position.proceeds_sold == position_proceeds_sold
    assert position.cost_basis_sold == position_cost_basis_sold
    assert position.pnl_sold == position_pnl_sold
