from flask import Flask, render_template, request, jsonify
import os, requests
app = Flask(__name__)
API_URL = "https://bantibhaiya.com/api/reseller_v1.php"
API_KEY = os.getenv("RESELLER_API_KEY")
MASTER_KEY = os.getenv("RESELLER_MASTER_KEY")
PRODUCTS = {"133": {"name": "AIM TOOL"}, "149": {"name": "XRAG FF"}}
DURATIONS = ["1 Hour","3 Hours","6 Hours","12 Hours","1 Day","3 Days","7 Days"]
@app.route("/")
def home():
    return render_template("index.html")
@app.route("/buy", methods=["POST"])
def buy():
    data=request.get_json()
    pid=str(data.get("product_id","")).strip()
    duration=data.get("duration","").strip()
    payload={"api_key":API_KEY,"action":"buy","product_id":pid,"duration":duration}
    try:
        r=requests.post(API_URL,data=payload,headers={"x-master-key":MASTER_KEY},timeout=20)
        result=r.json()
        key=result.get("key") or result.get("license") or str(result)
        return jsonify(ok=True,response=result,key=key,generated_key=key),200
    except Exception as e:
        return jsonify(ok=False,error=str(e)),500
