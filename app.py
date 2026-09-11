from flask import Flask, render_template, request, jsonify
import os, requests

app = Flask(__name__)

# Put the NEW rotated credentials in environment variables.
API_URL = os.getenv("RESELLER_API_URL", "https://bantibhaiya.com/api/reseller_v1.php")
API_KEY = os.getenv("RESELLER_API_KEY", "")
MASTER_KEY = os.getenv("RESELLER_MASTER_KEY", "")

PRODUCTS = {
    "133": {"name": "AIM HACK FF ROOT+NONROOT+IOS IPHONE+PC"},
    "149": {"name": "XRAG FF ROOT+NONROOT+IOS IPHONE+PC"},
}

DURATIONS = ["1 Hours", "3 Hours", "6 Hours", "12 Hours", "1 Day", "3 Days", "7 Days"]

@app.get("/")
def home():
    return render_template("index.html", products=PRODUCTS, durations=DURATIONS)

@app.post("/buy")
def buy():
    data = request.get_json(silent=True) or {}
    pid = str(data.get("product_id", ""))
    duration = data.get("duration", "")
    android_id = data.get("android_id", "").strip()

    if pid not in PRODUCTS:
        return jsonify(ok=False, error="Invalid product."), 400
    if duration not in DURATIONS:
        return jsonify(ok=False, error="Invalid duration."), 400
    if not API_KEY or not MASTER_KEY:
        return jsonify(ok=False, error="API credentials are not configured on the server."), 500

    payload = {
        "api_key": API_KEY,
        "action": "buy",
        "product_id": pid,
        "duration": duration,
    }
    if android_id:
        payload["android_id"] = android_id

    try:
        r = requests.post(
            API_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded",
                     "x-master-key": MASTER_KEY},
            timeout=20,
        )
        try:
            result = r.json()
        except ValueError:
            result = {"raw": r.text}
        return jsonify(ok=r.ok, status=r.status_code, response=result), r.status_code
    except requests.RequestException as e:
        return jsonify(ok=False, error="Reseller API connection failed."), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
