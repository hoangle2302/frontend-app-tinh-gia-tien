import math

import pytest

from engine.calculator import CalculationInput, Calculators


def product(name, category, price=100, **spec):
    return {
        "name": name,
        "category": category,
        "unit": "pcs",
        "unit_price": price,
        "spec_json": spec,
    }


@pytest.fixture
def products():
    module = product(
        "Module P2",
        "module",
        width_mm=320,
        height_mm=160,
        pitch="P2",
        max_current_a=3.8,
        pixel_w=160,
        pixel_h=80,
    )
    power = product("Nguồn 5V40A", "power", max_current_a=40)
    card = product("Receiving card", "card", capacity_pixels=65_536)
    frame = product("Khung", "frame")
    processors = [
        product("Processor nhỏ", "processor", min_pixels=0, max_pixels=1_300_000),
        product("Processor trung", "processor", min_pixels=1_300_001, max_pixels=2_300_000),
        product("Processor cao cấp", "processor", min_pixels=2_300_001),
    ]
    return module, power, card, frame, processors


def calculate(products, **overrides):
    module, power, card, frame, processors = products
    values = {
        "width_m": 4,
        "height_m": 2.5,
        "environment": "indoor",
        "module": module,
        "power": power,
        "card": card,
        "frame": frame,
        "processors": processors,
        "include_install": False,
        "include_transport": False,
    }
    values.update(overrides)
    return Calculators().calculate(CalculationInput(**values))


def test_module_counts_reserve_and_resolution(products):
    result = calculate(products)
    assert result["summary"]["n_ngang"] == 13
    assert result["summary"]["n_doc"] == 16
    assert result["summary"]["n_base"] == 208
    assert result["summary"]["n_reserve"] == math.ceil(208 * 0.03)
    assert result["summary"]["n_total"] == 215
    assert result["summary"]["res_w"] == 2080
    assert result["summary"]["res_h"] == 1280


def test_power_cards_processor_and_pricing_layers(products):
    result = calculate(products, profit_percent=20, vat_percent=8, discount_percent=10)
    expected_power_count = math.ceil(
        result["summary"]["n_total"] / math.floor(200 * 0.8 / (5 * 3.8))
    )
    assert result["summary"]["power_count"] == expected_power_count
    assert result["summary"]["receiving_card_count"] == math.ceil(2080 * 1280 / 65_536)
    assert result["summary"]["processor_name"] == "Processor cao cấp"
    assert result["pricing"]["profit_value"] > 0
    assert result["pricing"]["vat_value"] > 0
    assert result["pricing"]["final_total"] > result["pricing"]["before_vat"]


def test_additional_items_and_quantity_are_included(products):
    result = calculate(
        products,
        screen_quantity=2,
        additional_items=[{"name": "Phụ kiện", "qty": 2, "unit_price": 50}],
    )
    assert any(row["name"] == "Phụ kiện" for row in result["bom"])
    assert result["pricing"]["cost_total"] > result["pricing"]["cost_per_screen"]


@pytest.mark.parametrize(
    "field,value",
    [("width_m", 0), ("height_m", -1), ("screen_quantity", 0), ("profit_percent", 101)],
)
def test_invalid_input_is_rejected(products, field, value):
    with pytest.raises(ValueError):
        calculate(products, **{field: value})
