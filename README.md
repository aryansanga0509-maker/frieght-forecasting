# Intelligent Inventory & Freight Forecasting Dashboard

A VS Code-ready prototype for a Smart Inventory / Freight Forecasting system.

## Features

- Product search and fuzzy-style narrowing
- Product master data
- Synthetic 5-year weekly demand data
- 12-week demand forecasting
- Reorder point calculation
- Safety stock calculation
- Suggested order quantity
- Supplier, MOQ, lead time and unit cost
- Historical and forecast graphs
- Seasonal/event factors
- Supply-chain visualization
- Responsive dashboard

## Run in VS Code

### 1. Open the folder

Open `intelligent_inventory_dashboard` in VS Code.

### 2. Create virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Mac/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install packages

```bash
pip install -r requirements.txt
```

### 4. Run

```bash
python app.py
```

### 5. Open

Go to:

http://127.0.0.1:5000

## Important

The data is synthetic and intended for a prototype/demo. For the final SIH project, replace the synthetic generator with real sales, inventory, supplier, weather, event, promotion and geographic datasets.

## Suggested future modules

1. ML forecasting with XGBoost/LightGBM
2. Weather API
3. Indian festival/event calendar
4. Geographic demand model
5. Promotion uplift model
6. War/geopolitical risk indicator
7. Route optimization using graph algorithms
8. PostgreSQL/MySQL database
9. Authentication for retailers
10. Real-time inventory updates
