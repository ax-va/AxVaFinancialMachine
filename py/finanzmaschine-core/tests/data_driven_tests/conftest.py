from decimal import Decimal
from pathlib import Path
from typing import List

import polars as pl
import pytest

from finanzmaschine_core.catalog import asset_registry
from finanzmaschine_core.portfolio.assets import CryptoEtp
from finanzmaschine_core.portfolio.operations import TradeEnum
from finanzmaschine_core.portfolio.operations.operation import parse_operation, Operation
from finanzmaschine_core.portfolio.positions import CryptoEtpPosition
from finanzmaschine_core.portfolio.records import CryptoEtpBrokerTradeRecord


def create_df_expected_closing(file_path: Path) -> pl.DataFrame:
    df = pl.read_csv(
        source=file_path,
        try_parse_dates=True,
        schema_overrides={
          "quantity_open_before": pl.String,
          "quantity_to_close": pl.String,
          "quantity_open_after": pl.String,
          "quantity_closed": pl.String,
          "quantity_remaining": pl.String,
          "fee_to_close": pl.String,
          "fee_closed": pl.String,
          "fee_remaining": pl.String,
          "proceeds_sold": pl.String,
          "cost_basis_sold": pl.String,
          "pnl_sold": pl.String,
        },
    )
    return df


@pytest.fixture(scope="session")
def df_expected_ton_etp_fifo_fifo(data_dir: Path) -> pl.DataFrame:
    return create_df_expected_closing(data_dir / "etps/expected_ton_etp_fifo_fifo.csv")


@pytest.fixture(scope="session")
def df_expected_ton_etp_fifo_lifo(data_dir: Path) -> pl.DataFrame:
    return create_df_expected_closing(data_dir / "etps/expected_ton_etp_fifo_lifo.csv")


@pytest.fixture(scope="session")
def df_expected_ton_etp_lifo_fifo(data_dir: Path) -> pl.DataFrame:
    return create_df_expected_closing(data_dir / "etps/expected_ton_etp_lifo_fifo.csv")


@pytest.fixture(scope="session")
def df_expected_ton_etp_lifo_lifo(data_dir: Path) -> pl.DataFrame:
    return create_df_expected_closing(data_dir / "etps/expected_ton_etp_lifo_lifo.csv")


@pytest.fixture(scope="session")
def df_ton_etp_flow(data_dir) -> pl.DataFrame:
    df = pl.read_csv(data_dir / "etps/ton_etp_flow.csv",
        try_parse_dates=True,
        schema_overrides={
            "price": pl.String,
            "fee": pl.String,
            "base_asset_flow": pl.String,
            "quote_asset_flow": pl.String,
        },
    ).sort("datetime")
    return df


@pytest.fixture(scope="session")
def df_ton_etp_broker_trade_metadata(data_dir) -> pl.DataFrame:
    df = pl.read_csv(data_dir / "etps/ton_etp_broker_trade_metadata.csv")
    return df


@pytest.fixture(scope="session")
def df_ton_etp_sold(df_ton_etp_flow) -> pl.DataFrame:
    return df_ton_etp_flow.filter((pl.col("operation_type") == "TRADE") & (pl.col("operation_variant") == "SELL"))


def create_ton_etp_position(
    df_ton_etp_flow: pl.DataFrame,
    df_ton_etp_broker_trade_metadata: pl.DataFrame,
    closing_orders: List[str]
) -> CryptoEtpPosition:
    base_asset: CryptoEtp = asset_registry.get("CH1297762812")
    position = CryptoEtpPosition(base_asset=base_asset)
    closing_order_index = 0
    position.set_closing_order(closing_orders[closing_order_index])

    for row in df_ton_etp_flow.iter_rows(named=True):
        group_id = row["group_id"]
        datetime = row["datetime"]
        operation: Operation = parse_operation(row["operation_type"], row["operation_variant"])
        base_asset_flow = row["base_asset_flow"]
        quantity = abs(Decimal(base_asset_flow))
        entitlement = Decimal(row["entitlement"]) if row["entitlement"] else None

        quote_asset = asset_registry.get(row["quote_asset_id"])
        price = Decimal(row["price"])
        price_source = row["price_source"]
        fee = Decimal(row["fee"])

        metadata_row = df_ton_etp_broker_trade_metadata.filter(
            pl.col("group_id") == group_id
        ).row(0, named=True)

        broker = metadata_row["broker"]
        account_id = metadata_row["account_id"]
        order_id = metadata_row["order_id"]
        exchange = metadata_row["exchange"]
        trade_id = metadata_row["trade_id"]

        record = CryptoEtpBrokerTradeRecord(
            quantity=quantity,
            datetime=datetime,
            operation=operation,
            quote_asset=quote_asset,
            price=price,
            price_source=price_source,
            fee=fee,
            broker=broker,
            account_id=account_id,
            order_id=order_id,
            exchange=exchange,
            trade_id=trade_id,
            entitlement=entitlement,
        )
        position.apply(record)

        if operation.variant == TradeEnum.SELL and closing_order_index < len(closing_orders) - 1:
            closing_order_index += 1
            position.set_closing_order(closing_orders[closing_order_index])

    return position


@pytest.fixture(scope="session")
def ton_etp_position_fifo_fifo(df_ton_etp_flow, df_ton_etp_broker_trade_metadata) -> CryptoEtpPosition:
    return create_ton_etp_position(
        df_ton_etp_flow,
        df_ton_etp_broker_trade_metadata,
        ["FIFO", "FIFO"],
    )


@pytest.fixture(scope="session")
def ton_etp_position_fifo_lifo(df_ton_etp_flow, df_ton_etp_broker_trade_metadata) -> CryptoEtpPosition:
    return create_ton_etp_position(
        df_ton_etp_flow,
        df_ton_etp_broker_trade_metadata,
        ["FIFO", "LIFO"],
    )


@pytest.fixture(scope="session")
def ton_etp_position_lifo_fifo(df_ton_etp_flow, df_ton_etp_broker_trade_metadata) -> CryptoEtpPosition:
    return create_ton_etp_position(
        df_ton_etp_flow,
        df_ton_etp_broker_trade_metadata,
        ["LIFO", "FIFO"],
    )


@pytest.fixture(scope="session")
def ton_etp_position_lifo_lifo(df_ton_etp_flow, df_ton_etp_broker_trade_metadata) -> CryptoEtpPosition:
    return create_ton_etp_position(
        df_ton_etp_flow,
        df_ton_etp_broker_trade_metadata,
        ["LIFO", "LIFO"],
    )
