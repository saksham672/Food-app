from flask import Flask, render_template, request, redirect, session, flash, jsonify
import os, random, string
from functools import wraps
from datetime import datetime
import psycopg2
import psycopg2.extras

app=Flask(__name__)
app.secret_key=os.environ.get("SECRET_KEY","saksham-final-123")
ADMIN_PIN=os.environ.get("ADMIN_PIN","7788")
SELL_PRICE={"1 Hours":16,"3 Hours":35,"6 Hours":65,"12 Hours":120}
PRODUCTS={"133":{"name":"AIM HACK"},"149":{"name":"XRAG HACK"}}
DURATIONS=["1 Hours","3 Hours","6 Hours","12 Hours"]
DATABASE_URL=os.environ.get("DATABASE_URL")

def get_db():
 return psycopg2.connect(DATABASE_URL,cursor_factory=psycopg2.extras.RealDictCursor)

def init_db():
 c=get_db();cur=c.cursor()
 cur.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username TEXT UNIQUE, password TEXT, balance REAL DEFAULT 0, is_admin INTEGER DEFAULT 0)")
 cur.execute("CREATE TABLE IF NOT EXISTS history (id SERIAL PRIMARY KEY, user_id INTEGER, product_name TEXT, duration TEXT, price REAL, key_text TEXT, created_at TEXT)")
 cur.execute("SELECT 1 FROM users WHERE username='admin'")
 if not cur.fetchone():
  cur.execute("INSERT INTO users (username,password,balance,is_admin) VALUES ('admin','admin123',999999,1)")
 c.commit();cur.close();c.close()

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
 c=get_db();cur=c.cursor()
 cur.execute("SELECT * FROM users WHERE id=%s",(session['user_id'],));u=cur.fetchone()
 cur.execute("SELECT * FROM history WHERE user_id=%s ORDER BY id DESC",(u['id'],));h=cur.fetchall()
 cur.close();c.close()
 return render_template("index.html",products=PRODUCTS,durations=DURATIONS,user=u,sell_price=SELL_PRICE,histories=h)

@app.route("/login",methods=["GET","POST"])
def login():
 if request.method=="POST":
  c=get_db();cur=c.cursor()
  cur.execute("SELECT * FROM users WHERE username=%s AND password=%s",(request.form['username'],request.form['password']));u=cur.fetchone()
  cur.close();c.close()
  if u:
   session['user_id']=u['id'];session['username']=u['username'];session['is_admin']=bool(u['is_admin'])
   return redirect('/')
  flash("Wrong")
 return render_template("login.html")

@app.route("/register",methods=["GET","POST"])
def register():
 if request.method=="POST":
  c=get_db();cur=c.cursor()
  try:
   cur.execute("INSERT INTO users (username,password,balance) VALUES (%s,%s,0)",(request.form['username'],request.form['password']))
   c.commit();cur.close();c.close()
   return redirect('/login')
  except:
   c.rollback();cur.close();c.close();flash("Exists")
 return render_template("register.html")

@app.get("/logout")
def logout():
 session.clear()
 return redirect('/login')

@app.post("/generate")
@login_required
def generate():
 d=request.form['duration'];p=request.form['product_id']
 c=get_db();cur=c.cursor()
 cur.execute("SELECT * FROM users WHERE id=%s",(session['user_id'],));u=cur.fetchone()
 price=SELL_PRICE.get(d,0)
 if not u['is_admin'] and u['balance']<price:
  cur.close();c.close();return jsonify({"error":f"Balance low {u['balance']}"}),400
 key=f"{PRODUCTS[p]['name']} {d} - {''.join(random.choices(string.ascii_uppercase+string.digits,k=12))}"
 if not u['is_admin']: cur.execute("UPDATE users SET balance=balance-%s WHERE id=%s",(price,u['id']))
 cur.execute("INSERT INTO history (user_id,product_name,duration,price,key_text,created_at) VALUES (%s,%s,%s,%s,%s,%s)",(u['id'],PRODUCTS[p]['name'],d,price,key,datetime.now().strftime("%d-%m %H:%M")))
 c.commit()
 cur.execute("SELECT balance FROM users WHERE id=%s",(u['id'],));nb=cur.fetchone()['balance']
 cur.close();c.close()
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
 c=get_db();cur=c.cursor()
 cur.execute("SELECT * FROM users ORDER BY id");us=cur.fetchall()
 cur.execute("SELECT h.*,u.username FROM history h LEFT JOIN users u ON h.user_id=u.id ORDER BY h.id DESC LIMIT 100");hs=cur.fetchall()
 cur.close();c.close()
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
 c=get_db();cur=c.cursor();cur.execute("UPDATE users SET balance=balance+%s WHERE username=%s",(amt,request.form['username']));c.commit();cur.close();c.close()
 flash(f"Added {amt} Rs to {request.form['username']}")
 return redirect('/admin')

@app.post("/admin/delete_user")
def delete_user():
 if not session.get('admin_ok'): return "Admin only",403
 c=get_db();cur=c.cursor();cur.execute("DELETE FROM users WHERE username=%s AND is_admin=0",(request.form['username'],));c.commit();cur.close();c.close()
 return redirect('/admin')

@app.post("/admin/add_user")
def add_user():
 if not session.get('admin_ok'): return "Admin only",403
 c=get_db();cur=c.cursor()
 try:cur.execute("INSERT INTO users (username,password,balance) VALUES (%s,%s,0)",(request.form['username'],request.form['password']));c.commit()
 except:c.rollback()
 cur.close();c.close();return redirect('/admin')
