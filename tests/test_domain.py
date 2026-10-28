import pytest
from decimal import Decimal
from app.domain import Money, InvalidOrderData, InvalidOrderTransition, OrderItemLimitExceeded
from app.specifications import MinimumAmountSpec, VIPCustomerSpec, MinimumUnitsSpec, ActivePromotionSpec
from cargar_csv import load_fixture

def test_money_negativo():
    with pytest.raises(InvalidOrderData):
        Money(Decimal("-1"))

def test_pedido_o001_inicia_draft():
    orders = load_fixture()
    assert orders["O001"].status.value == "DRAFT"
    assert orders["O001"].units == 4
    assert orders["O001"].total.amount == Decimal("2100.00")

def test_descuento_vip_reglas():
    orders = load_fixture()
    order = orders["O001"]
    regla_10_porciento = (
        MinimumAmountSpec(Decimal("500"))
        & VIPCustomerSpec()
        & MinimumUnitsSpec(4)
        & ~ActivePromotionSpec()
    )
    assert regla_10_porciento.is_satisfied_by(order) == True

def test_confirmacion_doble_falla():
    orders = load_fixture()
    order = orders["O013"]
    order.confirm()
    assert order.status.value == "CONFIRMED"
    
    with pytest.raises(InvalidOrderTransition):
        order.confirm()

def test_cancelacion_desde_shipped_falla():
    orders = load_fixture()
    order = orders["O013"]
    order.confirm()
    order.ship("TRACK123")
    
    with pytest.raises(InvalidOrderTransition):
        order.cancel("El cliente se arrepintió")