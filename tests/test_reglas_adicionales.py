"""
Pruebas adicionales para el punto 12 de la práctica (TechStore U4).
Copiar a: tests/test_reglas_adicionales.py   |   Ejecutar: python -m pytest -v

Estas pruebas construyen sus propios pedidos (no dependen de los CSV),
solo prueban el dominio (las pruebas de API ya las tienes en test_api.py).
"""
from decimal import Decimal

import pytest

from app.domain import (
    Customer, DomainException, InvalidOrderData, InvalidOrderTransition,
    Money, Order, OrderItem, OrderItemLimitExceeded, OrderStatus,
)
from app.specifications import (
    ActivePromotionSpec, MinimumAmountSpec, MinimumUnitsSpec, VIPCustomerSpec,
)


# ---------- Preparar datos ----------
def hacer_pedido(unidades=0, precio="100.00", vip=True, activo=True,
                 promo=False, oid="T001"):
    pedido = Order(customer=Customer("C-T", is_vip=vip, active=activo),
                   id=oid, has_promotion=promo)
    if unidades:
        pedido.add_item(OrderItem("SKU001", unidades, Money(Decimal(precio))))
    return pedido


def regla_10():
    return (MinimumAmountSpec(Decimal("500")) & VIPCustomerSpec()
            & MinimumUnitsSpec(4) & ~ActivePromotionSpec())


def regla_5():
    return MinimumAmountSpec(Decimal("5000")) & ~ActivePromotionSpec()


def nombres(pedido):
    return [e.name for e in pedido.events]


# ---------- Límite de 20 unidades ----------
def test_20_unidades_exactas_son_validas():
    pedido = hacer_pedido(unidades=20)
    assert pedido.units == 20


def test_21_unidades_se_rechazan_y_no_modifican_el_pedido():
    pedido = hacer_pedido()
    with pytest.raises(OrderItemLimitExceeded):
        pedido.add_item(OrderItem("SKU001", 21, Money(Decimal("10.00"))))
    assert pedido.units == 0 and pedido.items == []


def test_limite_suma_unidades_no_renglones():
    pedido = hacer_pedido(unidades=19)
    with pytest.raises(OrderItemLimitExceeded):
        pedido.add_item(OrderItem("SKU002", 2, Money(Decimal("10.00"))))
    assert pedido.units == 19 and len(pedido.items) == 1


def test_20_renglones_de_una_unidad_son_validos_el_21_no():
    pedido = hacer_pedido()
    for i in range(20):
        pedido.add_item(OrderItem(f"SKU{i:03}", 1, Money(Decimal("1.00"))))
    with pytest.raises(OrderItemLimitExceeded):
        pedido.add_item(OrderItem("SKU999", 1, Money(Decimal("1.00"))))


def test_cantidad_cero_o_negativa_es_invalida():
    for cantidad in (0, -1):
        with pytest.raises(InvalidOrderData):
            OrderItem("SKU001", cantidad, Money(Decimal("10.00")))


# ---------- Confirmación ----------
def test_cliente_inactivo_no_puede_confirmar():
    pedido = hacer_pedido(unidades=1, activo=False)
    with pytest.raises(InvalidOrderData):
        pedido.confirm()
    assert pedido.status == OrderStatus.DRAFT and pedido.events == []


def test_pedido_vacio_no_puede_confirmar():
    pedido = hacer_pedido()
    with pytest.raises(InvalidOrderData):
        pedido.confirm()
    assert pedido.status == OrderStatus.DRAFT and pedido.events == []


def test_confirmacion_doble_no_agrega_segundo_evento():
    pedido = hacer_pedido(unidades=1)
    pedido.confirm()
    with pytest.raises(InvalidOrderTransition):
        pedido.confirm()
    assert pedido.status == OrderStatus.CONFIRMED
    assert nombres(pedido) == ["OrderConfirmed"]


# ---------- Specifications ----------
def test_descuento_vip_10_cumple():
    assert regla_10().is_satisfied_by(hacer_pedido(unidades=4, precio="200.00"))


def test_cliente_no_vip_no_obtiene_10():
    assert not regla_10().is_satisfied_by(
        hacer_pedido(unidades=4, precio="200.00", vip=False))


def test_promocion_activa_excluye_ambos_descuentos():
    pedido = hacer_pedido(unidades=20, precio="300.00", promo=True)
    assert not regla_10().is_satisfied_by(pedido)
    assert not regla_5().is_satisfied_by(pedido)


def test_monto_exacto_500_no_supera_el_umbral():
    pedido = hacer_pedido(unidades=4, precio="125.00")      # total = 500.00
    assert pedido.total.amount == Decimal("500.00")
    assert not regla_10().is_satisfied_by(pedido)


def test_menos_de_4_unidades_no_obtiene_10():
    assert not regla_10().is_satisfied_by(hacer_pedido(unidades=3, precio="300.00"))


def test_regla_5_exige_mas_de_5000():
    assert not regla_5().is_satisfied_by(hacer_pedido(unidades=20, precio="250.00"))  # 5000
    assert regla_5().is_satisfied_by(hacer_pedido(unidades=20, precio="250.05"))      # 5001


# ---------- Envío, cancelación y demás transiciones ----------
def test_envio_sin_guia_se_rechaza():
    pedido = hacer_pedido(unidades=1)
    pedido.confirm()
    with pytest.raises(InvalidOrderData):
        pedido.ship("")
    assert pedido.status == OrderStatus.CONFIRMED
    assert nombres(pedido) == ["OrderConfirmed"]


def test_cancelacion_desde_shipped_se_rechaza():
    pedido = hacer_pedido(unidades=1)
    pedido.confirm()
    pedido.ship("GUIA123")
    with pytest.raises(InvalidOrderTransition):
        pedido.cancel("Ya no lo quiero")
    assert pedido.status == OrderStatus.SHIPPED
    assert "OrderCancelled" not in nombres(pedido)


def test_cancelacion_sin_motivo_se_rechaza():
    pedido = hacer_pedido(unidades=1)
    pedido.confirm()
    with pytest.raises(DomainException):
        pedido.cancel("")
    assert pedido.status == OrderStatus.CONFIRMED


def test_flujo_completo_hasta_entregado_y_sus_eventos():
    pedido = hacer_pedido(unidades=2)
    pedido.confirm()
    pedido.ship("GUIA123")
    pedido.deliver()
    assert pedido.status == OrderStatus.DELIVERED
    assert nombres(pedido) == ["OrderConfirmed", "OrderShipped", "OrderDelivered"]


def test_devolucion_desde_shipped():
    pedido = hacer_pedido(unidades=2)
    pedido.confirm()
    pedido.ship("GUIA123")
    pedido.return_order()
    assert pedido.status == OrderStatus.RETURNED
    assert nombres(pedido)[-1] == "OrderReturned"


def test_no_se_agregan_articulos_a_pedido_confirmado():
    pedido = hacer_pedido(unidades=1)
    pedido.confirm()
    with pytest.raises(InvalidOrderTransition):
        pedido.add_item(OrderItem("SKU002", 1, Money(Decimal("10.00"))))