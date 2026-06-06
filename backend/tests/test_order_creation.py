import asyncio

import pytest

from agent.gemini_agent import execute_tool
from harness import policy_engine
from harness.policy_engine import evaluate_tool_call


VALID_SKU = "USBG5000DTF-Black-L"
VALID_ADDRESS = {
    "name": "Le Quoc Anh",
    "street": "84 Le Dinh Ly",
    "city": "Da Nang",
    "state": "Hai Chau",
    "zip": "550000",
    "country": "VN",
}


def order_args(**overrides):
    data = {
        "sku": VALID_SKU,
        "quantity": 1,
        "address": VALID_ADDRESS.copy(),
        "design_url_front": "https://example.com/design-front.png",
        "shipping_method": "standard",
    }
    data.update(overrides)
    return data


@pytest.fixture(autouse=True)
def enable_order_creation(monkeypatch):
    monkeypatch.setattr(policy_engine.ff_manager, "is_order_creation_enabled", lambda: True)


def test_create_order_requires_exact_sku_confirmation():
    decision = evaluate_tool_call(
        "create_order",
        order_args(),
        user_message="Tôi đồng ý đặt đơn này",
    )

    assert not decision.allowed
    assert decision.code == "ORDER_CONFIRMATION_REQUIRED"


def test_create_order_rejects_unknown_sku_even_with_confirmation():
    decision = evaluate_tool_call(
        "create_order",
        order_args(sku="FAKE-SKU-DOES-NOT-EXIST"),
        user_message="Xác nhận đặt SKU FAKE-SKU-DOES-NOT-EXIST",
    )

    assert not decision.allowed
    assert decision.code == "SKU_NOT_FOUND"


def test_create_order_rejects_missing_address_field():
    address = VALID_ADDRESS.copy()
    address["zip"] = ""

    decision = evaluate_tool_call(
        "create_order",
        order_args(address=address),
        user_message=f"Xác nhận đặt SKU {VALID_SKU}",
    )

    assert not decision.allowed
    assert decision.code == "ADDRESS_REQUIRED"


def test_create_order_rejects_large_quantity_for_manual_review():
    decision = evaluate_tool_call(
        "create_order",
        order_args(quantity=100),
        user_message=f"Xác nhận đặt SKU {VALID_SKU}",
    )

    assert not decision.allowed
    assert decision.code == "QUANTITY_REQUIRES_REVIEW"


def test_create_order_rejects_missing_design_url():
    decision = evaluate_tool_call(
        "create_order",
        order_args(design_url_front=""),
        user_message=f"Xac nhan dat SKU {VALID_SKU}",
    )

    assert not decision.allowed
    assert decision.code == "DESIGN_URL_REQUIRED"


def test_create_order_rejects_address_country_mismatch():
    address = {
        "name": "John Carter",
        "street": "2458 West Sunset Blvd",
        "city": "Paris",
        "state": "Ile-de-France",
        "zip": "75004",
        "country": "US",
    }

    decision = evaluate_tool_call(
        "create_order",
        order_args(address=address),
        user_message=f"Xac nhan dat SKU {VALID_SKU}",
    )

    assert not decision.allowed
    assert decision.code == "ADDRESS_COUNTRY_MISMATCH"


def test_create_order_rejects_invalid_design_url():
    decision = evaluate_tool_call(
        "create_order",
        order_args(design_url_front="not-a-public-url"),
        user_message=f"Xac nhan dat SKU {VALID_SKU}",
    )

    assert not decision.allowed
    assert decision.code == "INVALID_DESIGN_URL"


def test_create_order_policy_allows_valid_confirmed_order():
    decision = evaluate_tool_call(
        "create_order",
        order_args(),
        user_message=f"Xác nhận đặt SKU {VALID_SKU}",
    )

    assert decision.allowed
    assert decision.code == "POLICY_ALLOWED"


def test_create_order_tool_does_not_call_real_api(monkeypatch):
    async def fake_create_order(order):
        return type(
            "FakeOrderResponse",
            (),
            {
                "model_dump": lambda self: {
                    "order_id": "TEST-ORDER-1",
                    "status": "created",
                    "message": "Order created in test",
                }
            },
        )()

    monkeypatch.setattr(
        "agent.tool_handlers.bp_client.check_sku_availability",
        lambda sku_codes: _async_result({sku_codes[0]: "present_in_catalog"}),
    )
    monkeypatch.setattr(
        "agent.tool_handlers.bp_client.check_region_support",
        lambda sku_codes, region: _async_result({"_unsupported": "not implemented in test"}),
    )
    monkeypatch.setattr(
        "agent.tool_handlers.bp_client.check_provider_status",
        lambda provider_ids: _async_result({"_unsupported": "not implemented in test"}),
    )
    monkeypatch.setattr("agent.tool_handlers.bp_client.create_order", fake_create_order)

    result = asyncio.run(
        execute_tool(
            "create_order",
            order_args(),
            user_message=f"Xác nhận đặt SKU {VALID_SKU}",
        )
    )

    assert result == {
        "order_id": "TEST-ORDER-1",
        "status": "created",
        "message": "Order created in test",
    }


async def _async_result(value):
    return value
