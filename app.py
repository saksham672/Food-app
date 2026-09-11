from flask import Flask, render_template, request, redirect, session, flash, jsonify
import sqlite3, os, random, string
from functools import wraps
from datetime import datetime
app=Flask(__name__)
app.secret_key="saksham-final-123"
ADMIN_PIN=os.environ.get("ADMIN_PIN","7788")
SELL_PRICE={"1 Hours":16,"3 Hours":35,"6 Hours":65,"12 Hours":120}
PRODUCTS={"133":{"name":"AIM HACK"},"149":{"name":"XRAG HACK"}}
DURATIONS=["1 Hours","3 Hours","6 Hours","12 Hours"]
DB="/tmp/users.db"
def get_db():
 c=sqlite3.connect(DB)
 c.row_factory=sqlite3.Row
 return c
def init_db():
 c=get_db()
 c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, balance REAL DEFAULT 0, is_admin INTEGER DEFAULT 0)")
 c.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, user_id INTEGER, product_name TEXT, duration TEXT, price REAL, key_text TEXT, created_at TEXT)")
 a=c.execute("SELECT * FROM users WHERE username='admin'").fetchone()
 if not a:
  c.execute("INSERT INTO users VALUES (NULL,'admin','admin123',999999,1)")
 c.commit()
 c.close()
init_db()
def login_required(f):
 @wraps(f)
 def d(*a,**k):
  if 'user_id' not in session: return redirect('/login')
  return f(*a,**k)
 return d
@app.get("/")
@login_required
def home():
 c=get_db()
 u=c.execute("SELECT * FROM users WHERE id=?",(session['user_id'],)).fetchone()
 h=c.execute("SELECT * FROM history WHERE user_id=? ORDER BY id DESC",(u['id'],)).fetchall()
 c.close()
 return render_template("index.html",products=PRODUCTS,durations=DURATIONS,user=u,sell_price=SELL_PRICE,histories=h)
@app.route("/login",methods=["GET","POST"])
def login():
 if request.method=="POST":
  c=get_db()
  u=c.execute("SELECT * FROM users WHERE username=? AND password=?",(request.form['username'],request.form['password'])).fetchone()
  c.close()
  if u:
   session['user_id']=u['id'];session['username']=u['username'];session['is_admin']=bool(u['is_admin'])
   return redirect('/')
  flash("Wrong")
 return render_template("login.html")
@app.route("/register",methods=["GET","POST"])
def register():
 if request.method=="POST":
  c=get_db()
  try:
   c.execute("INSERT INTO users (username,password,balance) VALUES (?,?,0)",(request.form['username'],request.form['password']))
   c.commit();c.close()
   return redirect('/login')
  except:
   c.close();flash("Exists")
 return render_template("register.html")
@app.get("/logout")
def logout():
 session.clear()
 return redirect('/login')
@app.post("/generate")
@login_required
def generate():
 d=request.form['duration'];p=request.form['product_id']
 c=get_db();u=c.execute("SELECT * FROM users WHERE id=?",(session['user_id'],)).fetchone()
 price=SELL_PRICE.get(d,0)
 if not u['is_admin'] and u['balance']<price:
  c.close();return jsonify({"error":f"Balance low {u['balance']}"}),400
 key=f"{PRODUCTS[p]['name']} {d} - {''.join(random.choices(string.ascii_uppercase+string.digits,k=12))}"
 if not u['is_admin']: c.execute("UPDATE users SET balance=balance-? WHERE id=?",(price,u['id']))
 c.execute("INSERT INTO history (user_id,product_name,duration,price,key_text,created_at) VALUES (?,?,?,?,?,?)",(u['id'],PRODUCTS[p]['name'],d,price,key,datetime.now().strftime("%d-%m %H:%M")))
 c.commit();nb=c.execute("SELECT balance FROM users WHERE id=?",(u['id'],)).fetchone()['balance'];c.close()
 return jsonify({"key":key,"price":price,"new_balance":nb})
@app.route("/admin",methods=["GET","POST"])
def admin_panel():
 if request.method=="POST" and 'pin' in request.form:
  if request.form['pin']==ADMIN_PIN:
   session['admin_ok']=True
   return redirect('/admin')
  flash("Wrong PIN")
  return render_template("admin_login.html")
 if not session.get('admin_ok'):
  return render_template("admin_login.html")
 c=get_db();us=c.execute("SELECT * FROM users").fetchall();hs=c.execute("SELECT h.*,u.username FROM history h LEFT JOIN users u ON h.user_id=u.id ORDER BY h.id DESC LIMIT 100").fetchall();c.close()
 return render_template("admin.html",users=us,histories=hs)
@app.get("/admin/logout")
def admin_logout():
 session.pop('admin_ok',None)
 return redirect('/admin')
@app.post("/admin/add_balance")
def add_balance():
 if not session.get('admin_ok'): return "Admin only",403
 try:amt=float(request.form['amount'])
 except:flash("Invalid amount");return redirect('/admin')
 c=get_db();c.execute("UPDATE users SET balance=balance+? WHERE username=?",(amt,request.form['username']));c.commit();c.close()
 flash(f"Added {amt} Rs to {request.form['username']}")
 return redirect('/admin')
@app.post("/admin/delete_user")
def delete_user():
 if not session.get('admin_ok'): return "Admin only",403
 c=get_db();c.execute("DELETE FROM users WHERE username=? AND is_admin=0",(request.form['username'],));c.commit();c.close()
 return redirect('/admin')
@app.post("/admin/add_user")
def add_user():
 if not session.get('admin_ok'): return "Admin only",403
 c=get_db()
 try:c.execute("INSERT INTO users (username,password,balance) VALUES (?,?,0)",(request.form['username'],request.form['password']));c.commit()
 except:pass
 c.close();return redirect('/admin')
