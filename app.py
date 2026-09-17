from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

app = Flask(__name__)

# -----------------------------
# Synthetic product master data
# -----------------------------
products = pd.DataFrame([
    ["P1001","Steel Rod 10mm","Steel","TMT Bars","Tata Steel",62000],
    ["P1002","Steel Rod 12mm","Steel","TMT Bars","JSW Steel",63500],
    ["P1003","Steel Plate 5mm","Steel","Plates","SAIL",71000],
    ["P1004","Iron Ore Pellets","Raw Material","Pellets","NMDC",12500],
    ["P1005","Coking Coal","Raw Material","Coal","Imported Supplier",18500],
    ["P1006","GI Sheet","Steel","Sheets","JSW Steel",76000],
    ["P1007","MS Angle 50x50","Steel","Structural","SAIL",59000],
], columns=["product_id","product_name","category","subcategory","brand","price"])

# -----------------------------
# Supplier data
# -----------------------------
suppliers = pd.DataFrame([
    ["S001","Tata Steel Supplier","P1001",10,500,58500,"Vizag Port"],
    ["S002","JSW Supplier","P1002",14,300,59800,"Krishnapatnam Port"],
    ["S003","SAIL Distributor","P1003",12,250,68000,"Paradip Port"],
    ["S004","NMDC Supplier","P1004",8,1000,11200,"Visakhapatnam Port"],
    ["S005","Imported Coal Supplier","P1005",25,500,17200,"Paradip Port"],
    ["S006","JSW Sheet Supplier","P1006",15,200,72000,"Krishnapatnam Port"],
    ["S007","SAIL Structural Supplier","P1007",11,400,55500,"Vizag Port"],
], columns=["supplier_id","supplier","product_id","lead_time_days","min_order_qty","unit_cost","port"])

# -----------------------------
# Synthetic historical data
# -----------------------------
def generate_history(product_id, years=5):
    rng = np.random.default_rng(sum(ord(c) for c in product_id))
    end = pd.Timestamp.today().normalize()
    start = end - pd.DateOffset(years=years)
    dates = pd.date_range(start, end, freq="W")
    base = {
        "P1001": 430, "P1002": 390, "P1003": 260, "P1004": 700,
        "P1005": 560, "P1006": 240, "P1007": 350
    }.get(product_id, 300)
    rows = []
    for d in dates:
        season = 1 + 0.18*np.sin(2*np.pi*d.dayofyear/365.25)
        festival = 1.15 if d.month in [10,11] else 1.0
        weather = rng.normal(1, 0.08)
        promotion = 1.0 + (0.22 if rng.random() < 0.08 else 0)
        market = rng.normal(1, 0.06)
        demand = max(20, base * season * festival * weather * promotion * market)
        rows.append([d.strftime("%Y-%m-%d"), product_id, round(demand), round(promotion,2),
                     round(weather,2), round(market,2)])
    return pd.DataFrame(rows, columns=["date","product_id","demand","promotion","weather_factor","market_factor"])

# -----------------------------
# Forecast logic
# -----------------------------
def get_forecast(product_id, weeks=12):
    hist = generate_history(product_id, 5)
    y = hist["demand"].astype(float).values
    # Simple robust baseline forecast: weighted moving average + trend
    recent = y[-12:]
    weights = np.arange(1, len(recent)+1)
    baseline = np.average(recent, weights=weights)
    x = np.arange(len(recent))
    slope = np.polyfit(x, recent, 1)[0]
    last_date = pd.to_datetime(hist["date"].iloc[-1])
    out = []
    for i in range(1, weeks+1):
        seasonal = 1 + 0.10*np.sin(2*np.pi*(last_date.dayofyear + 7*i)/365.25)
        value = max(1, baseline + slope*(len(recent)+i-1)) * seasonal
        out.append({
            "date": (last_date + timedelta(days=7*i)).strftime("%Y-%m-%d"),
            "forecast": round(value)
        })
    return hist, pd.DataFrame(out)

def inventory_recommendation(product_id):
    hist, forecast = get_forecast(product_id, 12)
    s = suppliers[suppliers.product_id == product_id].iloc[0]
    p = products[products.product_id == product_id].iloc[0]

    daily_demand = hist.demand.tail(12).mean() / 7
    lead_demand = daily_demand * s.lead_time_days
    std_daily = hist.demand.tail(52).std() / math.sqrt(7)
    safety_stock = 1.65 * std_daily * math.sqrt(s.lead_time_days)
    reorder_point = lead_demand + safety_stock

    current_stock = max(0, round(daily_demand * random.uniform(5, 18)))
    projected_30 = forecast.forecast.head(5).sum()
    suggested = max(0, round(projected_30 + safety_stock - current_stock))
    suggested = max(suggested, int(s.min_order_qty))
    suggested = math.ceil(suggested / s.min_order_qty) * int(s.min_order_qty)

    if current_stock <= reorder_point:
        action = "ORDER NOW"
    elif current_stock <= reorder_point * 1.25:
        action = "ORDER SOON"
    else:
        action = "STOCK SUFFICIENT"

    return {
        "product_id": product_id,
        "product_name": p.product_name,
        "current_stock": current_stock,
        "daily_demand": round(daily_demand, 1),
        "lead_time_days": int(s.lead_time_days),
        "safety_stock": round(safety_stock),
        "reorder_point": round(reorder_point),
        "suggested_order_qty": int(suggested),
        "min_order_qty": int(s.min_order_qty),
        "unit_cost": float(s.unit_cost),
        "estimated_order_value": round(suggested * s.unit_cost, 2),
        "supplier": s.supplier,
        "port": s.port,
        "action": action
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/products")
def api_products():
    q = request.args.get("q","").lower()
    df = products.copy()
    if q:
        mask = (
            df.product_id.str.lower().str.contains(q) |
            df.product_name.str.lower().str.contains(q) |
            df.category.str.lower().str.contains(q) |
            df.subcategory.str.lower().str.contains(q) |
            df.brand.str.lower().str.contains(q)
        )
        df = df[mask]
    return jsonify(df.to_dict(orient="records"))

@app.route("/api/history/<product_id>")
def api_history(product_id):
    hist = generate_history(product_id, 5)
    return jsonify(hist.to_dict(orient="records"))

@app.route("/api/forecast/<product_id>")
def api_forecast(product_id):
    hist, forecast = get_forecast(product_id, 12)
    return jsonify(forecast.to_dict(orient="records"))

@app.route("/api/recommendation/<product_id>")
def api_recommendation(product_id):
    return jsonify(inventory_recommendation(product_id))

@app.route("/api/suppliers/<product_id>")
def api_suppliers(product_id):
    df = suppliers[suppliers.product_id == product_id]
    return jsonify(df.to_dict(orient="records"))

@app.route("/api/analytics/<product_id>")
def api_analytics(product_id):
    hist = generate_history(product_id, 5)
    return jsonify({
        "average_weekly_demand": round(hist.demand.mean(), 1),
        "peak_weekly_demand": int(hist.demand.max()),
        "lowest_weekly_demand": int(hist.demand.min()),
        "promotion_avg_factor": round(hist.promotion.mean(), 2),
        "weather_avg_factor": round(hist.weather_factor.mean(), 2),
        "market_avg_factor": round(hist.market_factor.mean(), 2),
        "records": len(hist)
    })

@app.route("/api/events")
def api_events():
    return jsonify([
        {"event":"Festival season","months":"Oct-Nov","impact":"High","factor":1.15},
        {"event":"Monsoon","months":"Jun-Sep","impact":"Medium","factor":0.92},
        {"event":"Construction season","months":"Jan-May","impact":"Medium","factor":1.08},
        {"event":"Promotion campaign","months":"Variable","impact":"High","factor":1.22}
    ])

if __name__ == "__main__":
    app.run(debug=True)
