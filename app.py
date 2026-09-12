from flask import Flask, request, jsonify, render_template
import os, requests

app = Flask(__name__)

API_URL = "https://banti2haiyo.com/api/reseller_v1.php"
API_KEY = os.getenv("RESELLER_API_KEY")
MASTER_KEY = os.getenv("RESELLER_MASTER_KEY")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/buy", methods=["POST"])
def buy():
    try:
        data = request.get_json() if request.is_json else request.form
        pid = str(data.get("product_id","")).strip()
        duration = str(data.get("duration","")).strip()
        payload = {"api_key": API_KEY, "action": "buy", "product_id": pid, "duration": duration}
        r = requests.post(API_URL, data=payload, headers={"x-master-key": MASTER_KEY}, timeout=20)
        try:
            result = r.json()
        except:
            result = {"raw": r.text}
        key = result.get("key") or result.get("license") or result.get("data") or str(result)
        return jsonify(ok=True, response=result, key=key, generated_key=key)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

if __name__ == "__main__":
    app.run()
