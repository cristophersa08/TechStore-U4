# TechStore U4 – Núcleo de lógica de negocio

Práctica de la **Unidad 4: Desarrollo de Componentes de Negocio**
(Componentes de Lógica de Negocios, FIME – UANL).

**Equipo 3**

- Cristopher Alan Pulgarin Santa Cruz – 2105894
- Francisco Sebastián Hernández Terán – 2115798
- Jesús Orlando Moreno Chávez – 2108300

## Descripción

Programa que administra los pedidos de una tienda ficticia. Lee clientes,
productos y pedidos desde archivos CSV, los convierte en objetos del dominio,
aplica reglas de descuento, controla el ciclo de vida de cada pedido con una
máquina de estados y expone sus operaciones mediante una API REST con FastAPI.

Todo se trabaja con objetos en memoria: **no usa base de datos** y los cambios
se pierden al cerrar el programa. El campo `existencia` del catálogo es solo
informativo; no se descuenta inventario.

## Estructura del proyecto

```text
techstore-u4/
├── datos/                    # CSV: clientes, productos, pedidos, detalle_pedidos, escenarios
├── app/
│   ├── __init__.py
│   ├── domain.py             # Money, OrderItem, Customer, Order, DomainEvent y excepciones
│   ├── specifications.py     # Specification Pattern (AND, OR, NOT) y reglas de descuento
│   └── api.py                # API REST con FastAPI
├── tests/
│   ├── test_domain.py
│   ├── test_api.py
│   └── test_reglas_adicionales.py
├── cargar_csv.py             # Carga los CSV y construye los 16 pedidos (load_fixture)
├── generar_bitacora.py       # Ejecuta los escenarios E01–E15
└── README.md
```

## Requisitos

- Python 3.11 o superior
- Paquetes: `fastapi`, `uvicorn`, `pytest`, `httpx`

## Instalación

```powershell
# 1. Entrar a la carpeta del proyecto
cd techstore-u4

# 2. Crear y activar el entorno virtual
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
# .venv\Scripts\activate.bat        # Windows CMD
# source .venv/bin/activate         # macOS / Linux

# 3. Instalar dependencias
python -m pip install fastapi uvicorn pytest httpx
```

## Ejecución

**Cargar los datos** (debe mostrar los 16 pedidos en `DRAFT`; `O001` con 4 unidades y 2100.00):

```powershell
python cargar_csv.py
```

**Ejecutar la bitácora de los 15 escenarios (E01–E15):**

```powershell
python generar_bitacora.py
```

**Levantar la API:**

```powershell
uvicorn app.api:app --reload
```

- Documentación interactiva (Swagger): <http://127.0.0.1:8000/docs>
- Contrato OpenAPI: <http://127.0.0.1:8000/openapi.json>

> Los pedidos viven en memoria. Para repetir una prueba en Swagger (por ejemplo,
> confirmar un pedido que ya se confirmó) reinicia el servidor.

**Ejecutar las pruebas (30 en total):**

```powershell
python -m pytest -v
python -m pytest -q
```

## Reglas de negocio

| Regla | Condición |
|---|---|
| Límite de pedido | Máximo **20 unidades** por pedido. Se cuenta la **suma de unidades**, no el número de renglones. |
| Descuento del 10 % | Cliente VIP, monto **mayor a 500**, al menos **4 unidades** y sin promoción activa. |
| Descuento del 5 % | Monto **mayor a 5000** y sin promoción activa. |
| Confirmar | Solo desde `DRAFT`, con al menos un artículo y con cliente activo. |
| Enviar | Solo desde `CONFIRMED` y con número de guía no vacío. |
| Cancelar | Solo desde `CONFIRMED` y con motivo no vacío. |
| Entregar / Devolver | Solo desde `SHIPPED`. |
| Dinero | `Money` usa `Decimal` y rechaza montos negativos. |

Una operación inválida lanza una excepción de dominio, **no cambia el estado y
no emite ningún evento**.

## Máquina de estados y Domain Events

```text
DRAFT --confirm--> CONFIRMED --ship--> SHIPPED --deliver--> DELIVERED
                       |                  |
                    cancel             return
                       |                  |
                   CANCELLED           RETURNED
```

| Evento | Método | Transición |
|---|---|---|
| `OrderConfirmed` | `confirm()` | DRAFT → CONFIRMED |
| `OrderShipped` | `ship(guía)` | CONFIRMED → SHIPPED |
| `OrderCancelled` | `cancel(motivo)` | CONFIRMED → CANCELLED |
| `OrderDelivered` | `deliver()` | SHIPPED → DELIVERED |
| `OrderReturned` | `return_order()` | SHIPPED → RETURNED |

Los eventos se registran **solo después** de validar la operación y cambiar el estado.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/orders/{id}` | Consulta un pedido. |
| `POST` | `/orders/{id}/confirm` | Confirma un pedido (DRAFT → CONFIRMED). |
| `POST` | `/orders/{id}/ship` | Envía un pedido con número de guía. |
| `POST` | `/orders/{id}/cancel` | Cancela un pedido con motivo. |

### Códigos de respuesta

| Código | Cuándo ocurre | Excepción de dominio |
|---|---|---|
| `200` | La operación fue válida. | – |
| `404` | El pedido no existe. | – |
| `409` | Transición no permitida (por ejemplo, confirmar dos veces o cancelar un pedido enviado). | `InvalidOrderTransition` |
| `422` | Datos inválidos (por ejemplo, pedido sin artículos, cliente inactivo o guía vacía). | `InvalidOrderData` |

El controlador no contiene reglas de negocio: busca el pedido, llama al método
de `Order` y traduce las excepciones de dominio a códigos HTTP.

## Pruebas

Se ejecutan **30 pruebas** con pytest, todas aprobadas:

- `test_domain.py` y `test_api.py`: pruebas base (Money, O001, descuento VIP, confirmación doble, cancelación desde SHIPPED y respuestas 404, 200, 409 y 422).
- `test_reglas_adicionales.py`: valores frontera (20 y 21 unidades, 500 y 5000 exactos), cliente inactivo, pedido vacío, promoción activa, envío sin guía, cancelación sin motivo y flujo completo con eventos.

## Evidencias

El reporte (`UNIDAD4_CLNEG_EQUIPO3.pdf`) incluye:

- Carga exitosa de los 16 pedidos.
- Bitácora de los 15 escenarios E01–E15.
- Capturas de Swagger (`/docs`) con una operación exitosa (200) y operaciones rechazadas (404, 409 y 422).
- Resultado de `pytest` (30 passed).
- Diagrama de estados y explicación de los Domain Events.
- Reflexión y respuestas a las preguntas del manual.

## Notas

- No se editaron los CSV para forzar que las pruebas pasaran.
- La advertencia `StarletteDeprecationWarning` que aparece al correr pytest viene de la dependencia `httpx` y no afecta los resultados.
