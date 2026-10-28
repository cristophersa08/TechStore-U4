from cargar_csv import load_fixture
from decimal import Decimal
from app.domain import OrderItem, Money
from app.specifications import MinimumAmountSpec, VIPCustomerSpec, MinimumUnitsSpec, ActivePromotionSpec

orders = load_fixture()
order = orders["O016"]

print(f"Estado inicial: {order.status.value}, Total: {order.total.amount}, Unidades: {order.units}")

try:
    order.confirm()
    order.ship("TRACK123")
    order.return_order()
    
    print("Éxito. Estado actual:", order.status.value)
    if order.events:
        print("Último evento emitido:", order.events[-1].name)
except Exception as e:
    print("Fallo:", type(e).__name__, "-", str(e))