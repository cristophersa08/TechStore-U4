from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from cargar_csv import load_fixture
from app.domain import InvalidOrderTransition, InvalidOrderData, OrderItemLimitExceeded

app = FastAPI(title="TechStore U4")
orders = load_fixture()

class ShipRequest(BaseModel):
    tracking_number: str

class CancelRequest(BaseModel):
    reason: str

@app.get("/orders/{order_id}")
def get_order(order_id: str):
    order = orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="No existe")
    return {
        "id": order.id,
        "status": order.status.value,
        "units": order.units,
        "total": order.total.amount
    }

@app.post("/orders/{order_id}/confirm")
def confirm_order(order_id: str):
    order = orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="No existe")
    try:
        order.confirm()
    except InvalidOrderTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except (InvalidOrderData, OrderItemLimitExceeded) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"id": order.id, "status": order.status.value, "events": [e.name for e in order.events]}

@app.post("/orders/{order_id}/ship")
def ship_order(order_id: str, request: ShipRequest):
    order = orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="No existe")
    try:
        order.ship(request.tracking_number)
    except InvalidOrderTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except InvalidOrderData as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"id": order.id, "status": order.status.value, "events": [e.name for e in order.events]}

@app.post("/orders/{order_id}/cancel")
def cancel_order(order_id: str, request: CancelRequest):
    order = orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="No existe")
    try:
        order.cancel(request.reason)
    except InvalidOrderTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except InvalidOrderData as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"id": order.id, "status": order.status.value, "events": [e.name for e in order.events]}