from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3, os, random, string
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = "saksham-final-123"

SELL_PRICE = {"1 Hours": 16, "3 Hours": 35, "6 Hours": 65, "12 Hours": 120}
PRODUCTS = {"133": {"name": "AIM HACK"}, "149": {"name": "XRAG HACK"}}
DURATIONS = ["1 Hours", "3 Hours", "6 Hours", "12 Hours"]
DB = "/tmp/users.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if os.path.exists(DB):
        try: os.remove(DB)
        except: pass
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, balance REAL DEFAULT 0, is_admin INTEGER DEFAULT 0)")
    conn.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, user_id INTEGER, product_name TEXT, duration TEXT, price REAL, key_text TEXT, created_at TEXT)")
    conn.execute("INSERT INTO users (username,password,balance,is_admin) VALUES (?,?,?,?)", ("admin", "admin123", 999999, 1))
    conn.commit()
    conn.close()

init_db()

def login_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if 'user_id' not in session: return redirect(url_for('login'))
        return f(*args, **kwargs)
    return dec

@app.get("/")
@login_required
def home():
    conn=get_db()
    user=conn.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
    if not user:
        conn.close()
        session.clear()
        return redirect(url_for('login'))
    conn.close()
    return render_template("index.html", products=PRODUCTS, durations=DURATIONS, user=user, sell_price=SELL_PRICE)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=request.form.get('username','').strip()
        p=request.form.get('password','').strip()
        conn=get_db()
        user=conn.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p)).fetchone()
        conn.close()
        if user:
            session['user_id']=user['id']
            session['username']=user['username']
            session['is_admin']=bool(user['is_admin'])
            return redirect(url_for('home'))
        flash("Wrong password")
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        u=request.form.get('username','').strip()
        p=request.form.get('password','').strip()
        if not u or not p:
            flash("Username password dalo")
            return render_template("register.html")
        conn=get_db()
        try:
            conn.execute("INSERT INTO users (username,password,balance) VALUES (?,?,?)", (u,p,0))
            conn.commit()
            conn.close()
            flash("ID ban gayi! Ab login karo")
            return redirect(url_for('login'))
        except:
            conn.close()
            flash("Ye username pehle se hai")
    return render_template("register.html")

@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.post("/generate")
@login_required
def generate():
    product_id=request.form['product_id']
    duration=request.form['duration']
    conn=get_db()
    user=conn.execute("SELECT * FROM users WHERE id=?",(session['user_id'],)).fetchone()
    price=SELL_PRICE.get(duration,0)
    if not user['is_admin'] and user['balance'] < price:
        conn.close()
        return jsonify({"error": f"Balance low! Need {price}, you have {user['balance']}"}), 400
    key = f"{duration}-KEY-{''.join(random.choices(string.ascii_uppercase+string.digits,k=10))}"
    if not user['is_admin']:
        conn.execute("UPDATE users SET balance=balance-? WHERE id=?", (price, user['id']))
    conn.execute("INSERT INTO history (user_id,product_name,duration,price,key_text,created_at) VALUES (?,?,?,?,?,?)", (user['id'], PRODUCTS.get(product_id,{}).get('name','HACK'), duration, price, key, datetime.now().strftime("%d-%m %H:%M")))
    conn.commit()
    conn.close()
    return jsonify({"key": key, "price": price})

@app.get("/admin")
def admin_panel():
    if not session.get('is_admin'): return "Admin only", 403
    conn=get_db()
    users=conn.execute("SELECT * FROM users").fetchall()
    history=conn.execute("SELECT h.*, u.username FROM history h LEFT JOIN users u ON h.user_id=u.id ORDER BY h.id DESC LIMIT 100").fetchall()
    conn.close()
    return render_template("admin.html", users=users, histories=history)

@app.post("/admin/add_user")
def add_user():
    conn=get_db()
    try:
        conn.execute("INSERT INTO users (username,password,balance) VALUES (?,?,?)", (request.form['username'], request.form['password'], 0))
        conn.commit()
    except: pass
    conn.close()
    return redirect("/admin")

@app.post("/admin/add_balance")
def add_balance():
    conn=get_db()
    conn.execute("UPDATE users SET balance=balance+? WHERE username=?", (float(request.form['amount']), request.form['username']))
    conn.commit(); conn.close()
    return redirect("/admin")

@app.post("/admin/delete_user")
def delete_user():
    conn=get_db()
    conn.execute("DELETE FROM users WHERE username=?", (request.form['username'],))
    conn.commit(); conn.close()
    return redirect("/admin")
