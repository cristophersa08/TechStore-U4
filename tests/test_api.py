import pytest
from fastapi.testclient import TestClient
from app.api import app, orders
from cargar_csv import load_fixture

client = TestClient(app)
@pytest.fixture(autouse=True)
def reset_orders():
    orders.clear()
    orders.update(load_fixture())

def test_api_confirmar_pedido_inexistente_responde_404():
    response = client.post("/orders/O999/confirm")
    assert response.status_code == 404
    assert response.json()["detail"] == "No existe"

def test_api_confirmar_pedido_valido_responde_200():
    response = client.post("/orders/O001/confirm")
    assert response.status_code == 200
    assert response.json()["status"] == "CONFIRMED"
    assert "OrderConfirmed" in response.json()["events"]

def test_api_confirmacion_doble_responde_409():
    client.post("/orders/O013/confirm")
    response = client.post("/orders/O013/confirm")
    assert response.status_code == 409
    assert "Solo DRAFT" in response.json()["detail"]

def test_api_confirmar_pedido_sin_articulos_responde_422():
    orders["O001"].items.clear()
    response = client.post("/orders/O001/confirm")
    assert response.status_code == 422
    assert "Requiere artículos" in response.json()["detail"]

def test_api_cancelar_desde_shipped_responde_409():
    client.post("/orders/O001/confirm")
    client.post("/orders/O001/ship", json={"tracking_number": "123456"})
    
    # Intentar cancelar desde SHIPPED viola la máquina de estados
    response = client.post("/orders/O001/cancel", json={"reason": "Me arrepentí"})
    assert response.status_code == 409