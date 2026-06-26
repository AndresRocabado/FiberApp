# Fiber Network Data Management System

Sistema de gestion de red de fibra optica desarrollado en Python con interfaz Streamlit.

## Tecnologias

- **Backend:** Python 3.10+
- **Base de datos:** SQLite (por defecto) / PostgreSQL (opcional)
- **UI:** Streamlit
- **Tests:** pytest

## Estructura del Proyecto

```
fiber-network-system/
├── app.py                    # Punto de entrada Streamlit
├── requirements.txt
├── .gitignore
├── README.md
├── database/
│   ├── connection.py         # Contexto de conexion SQLite/PostgreSQL
│   ├── schema.py             # Creacion de tablas
│   └── migrations/
│       └── 001_initial.sql   # Schema SQL de referencia
├── src/
│   ├── models/
│   │   ├── node.py           # Modelo Node (dataclass + enums)
│   │   └── link.py           # Modelo FiberLink (dataclass + enums)
│   ├── repositories/
│   │   ├── base_repository.py   # Interfaz abstracta CRUD
│   │   ├── node_repository.py   # Acceso a datos de nodos
│   │   └── link_repository.py   # Acceso a datos de enlaces
│   ├── services/
│   │   ├── node_service.py      # Logica de negocio - nodos
│   │   ├── link_service.py      # Logica de negocio - enlaces
│   │   └── report_service.py    # Generacion de reportes
│   └── utils/
│       └── csv_exporter.py      # Exportacion a CSV
├── tests/
│   ├── test_node_service.py
│   └── test_link_service.py
└── docs/
    └── architecture.md
```

## Instalacion

```bash
# 1. Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar la aplicacion
streamlit run app.py
```

## Ejecutar Tests

```bash
pytest tests/ -v
```

## Variables de Entorno

| Variable   | Descripcion                          | Valor por defecto     |
|------------|--------------------------------------|-----------------------|
| `DB_PATH`  | Ruta del archivo SQLite              | `fiber_network.db`    |
| `DATABASE_URL` | URL PostgreSQL (si se usa PG)    | *(no definida)*       |

## Funcionalidades

### Gestion de Nodos
- Crear, editar, eliminar y consultar nodos
- Campos: ID, Nombre, Ciudad, Tipo (Central/Distribucion/Acceso/Terminal), Estado

### Gestion de Enlaces
- Crear, editar, eliminar y consultar enlaces entre nodos
- Campos: ID, Nodo Origen, Nodo Destino, Distancia (km), Capacidad (Gbps), Estado

### Reportes
- Total de nodos y enlaces
- Longitud total de fibra desplegada
- Nodos agrupados por ciudad
- Estado de enlaces (activos / inactivos / mantenimiento)
- Exportacion a CSV

## Arquitectura

El proyecto sigue el patron de capas:

```
UI (Streamlit app.py)
    |
Services (logica de negocio)
    |
Repositories (acceso a datos)
    |
Database (SQLite / PostgreSQL)
```
