from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
V2_BRIDGE_PATH = WORKSPACE_ROOT / "strategies" / "bt_strategies" / "sim" / "common" / "v2_bridge.py"

spec = importlib.util.spec_from_file_location("bt_v2_bridge_test", V2_BRIDGE_PATH)
assert spec is not None and spec.loader is not None
v2_bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = v2_bridge
spec.loader.exec_module(v2_bridge)

AiStocksV2Broker = v2_bridge.AiStocksV2Broker
V2ClientConfig = v2_bridge.V2ClientConfig


class DummyClient:
    def __init__(self, responses):
        self.responses = dict(responses)

    def request(self, action, payload=None, timeout=None):
        _ = payload, timeout
        return self.responses.get(action)


def _build_broker() -> AiStocksV2Broker:
    broker = AiStocksV2Broker(
        V2ClientConfig(
            host="127.0.0.1",
            port=59620,
            token="token",
            account_key="lxm_main",
            sub_account_id="btsim_core_etf",
        )
    )
    return broker


@pytest.mark.unit
def test_v2_sync_account_prefers_position_avg_cost_fields():
    broker = _build_broker()
    broker.client = DummyClient(
        {
            "broker.account": {
                "available_cash": 317.10,
                "frozen_cash": 491.20,
                "total_asset": 100000.0,
            },
            "broker.positions": [
                {
                    "security": "159915.SZ",
                    "amount": 30700,
                    "available_amount": 30700,
                    "open_price": 3.231,
                    "cost": 3.247,
                    "last_price": 3.231,
                    "position_value": 99191.70,
                    "source": "virtual_db",
                }
            ],
        }
    )

    snapshot = broker.sync_account()

    assert snapshot["available_cash"] == pytest.approx(317.10)
    assert snapshot["locked_cash"] == pytest.approx(491.20)
    assert snapshot["positions"][0]["avg_cost"] == pytest.approx(3.231)


@pytest.mark.unit
def test_v2_normalize_limit_order_row_separates_order_price_and_fill_price():
    broker = _build_broker()

    row = broker._normalize_order_row(
        {
            "order_id": "1082136090",
            "security": "159915.SZ",
            "side": "BUY",
            "amount": 30700,
            "filled_amount": 30700,
            "price": 3.247,
            "avg_cost": 3.231,
            "style": {"type": "limit", "price": 3.247},
            "status": "filled",
        }
    )

    assert row["style"] == "limit"
    assert row["style_type"] == "limit"
    assert row["price"] == pytest.approx(3.231)
    assert row["avg_cost"] == pytest.approx(3.231)
    assert row["order_price"] == pytest.approx(3.247)


@pytest.mark.unit
def test_v2_normalize_market_order_row_uses_fill_price_not_protect_price():
    broker = _build_broker()

    row = broker._normalize_order_row(
        {
            "order_id": "1082136091",
            "security": "159915.SZ",
            "side": "BUY",
            "amount": 30700,
            "filled_amount": 30700,
            "price": 3.279,
            "avg_cost": 3.231,
            "style": {"type": "market", "protect_price": 3.279},
            "status": "filled",
        }
    )

    assert row["style"] == "market"
    assert row["style_type"] == "market"
    assert row["price"] == pytest.approx(3.231)
    assert row["avg_cost"] == pytest.approx(3.231)
    assert row["order_price"] == pytest.approx(3.279)


@pytest.mark.unit
def test_v2_normalize_order_row_prefers_explicit_traded_price_when_service_returns_order_price():
    broker = _build_broker()

    row = broker._normalize_order_row(
        {
            "order_id": "1082136092",
            "security": "159915.SZ",
            "side": "BUY",
            "amount": 30700,
            "filled_amount": 30700,
            "price": 3.247,
            "order_price": 3.247,
            "traded_price": 3.231,
            "avg_price": 3.231,
            "deal_balance": 99201.7,
            "style_type": "limit",
            "status": "filled",
        }
    )

    assert row["price"] == pytest.approx(3.231)
    assert row["avg_cost"] == pytest.approx(3.231)
    assert row["order_price"] == pytest.approx(3.247)
    assert row["deal_balance"] == pytest.approx(99201.7)


@pytest.mark.unit
def test_v2_normalize_order_row_derives_fill_price_from_deal_balance_without_falling_back_to_order_price():
    broker = _build_broker()

    row = broker._normalize_order_row(
        {
            "order_id": "1082136093",
            "security": "159915.SZ",
            "side": "BUY",
            "amount": 30700,
            "filled_amount": 30700,
            "price": 3.247,
            "order_price": 3.247,
            "deal_balance": 99201.7,
            "style_type": "limit",
            "status": "filled",
        }
    )

    assert row["price"] == pytest.approx(99201.7 / 30700)
    assert row["avg_cost"] == pytest.approx(99201.7 / 30700)
    assert row["order_price"] == pytest.approx(3.247)


@pytest.mark.unit
def test_v2_normalize_order_row_does_not_use_order_price_as_fill_price_when_fill_fields_missing():
    broker = _build_broker()

    row = broker._normalize_order_row(
        {
            "order_id": "1082136094",
            "security": "159915.SZ",
            "side": "BUY",
            "amount": 30700,
            "filled_amount": 30700,
            "price": 3.247,
            "order_price": 3.247,
            "style_type": "limit",
            "status": "filled",
        }
    )

    assert row["price"] == pytest.approx(0.0)
    assert row["avg_cost"] == pytest.approx(0.0)
    assert row["order_price"] == pytest.approx(3.247)
