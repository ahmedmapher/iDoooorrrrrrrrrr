from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
from functools import wraps

app = Flask(__name__)
# Intentionally weak secret for a CTF demo (do NOT do this in production)
app.secret_key = "ctf-demo-secret"

# --- Fake database (in-memory) ---
USERS = {
    "alice": {"id": 1, "password": "wonderland", "name": "Alice Liddell"},
    "bob":   {"id": 2, "password": "builder",    "name": "Bob The Builder"},
}

INVOICES = [
    {"id": 1001, "user_id": 1, "amount": 42.00, "description": "Starter Plan - October", "line_items": ["Service fee"], "notes": "Have a great day!"},
    {"id": 1002, "user_id": 1, "amount": 15.99, "description": "Add-on - Extra storage", "line_items": ["Storage 10GB"]},
    # 👇 Bob's invoice contains the flag
    {"id": 2001, "user_id": 2, "amount": 1337.00, "description": "Executive Plan - Confidential",
     "line_items": ["Retainer", "Special ops"],
     "notes": "FLAG{IDOR_PWNED_2025}"}
]

def current_user():
    uname = session.get("username")
    if uname and uname in USERS:
        user = USERS[uname]
        return {"username": uname, **user}
    return None

def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user():
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return wrapped

@app.get("/")
def index():
    if current_user():
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user = USERS.get(username)
        if user and user["password"] == password:
            session["username"] = username
            return redirect(url_for("dashboard"))
        error = "Invalid credentials"
    return render_template("login.html", error=error)

@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.get("/dashboard")
@login_required
def dashboard():
    user = current_user()
    # Only show the user's own invoice IDs in the dashboard list
    my_invoices = [i for i in INVOICES if i["user_id"] == user["id"]]
    return render_template("dashboard.html", user=user, invoices=my_invoices)

# --- Intentionally Vulnerable Endpoint (IDOR) ---
# This route returns invoice details by "id" without verifying ownership.
# The front-end links to /invoice?id=<id>, so a curious player can swap the id
# to access another user's invoice and recover the flag.
@app.get("/invoice")
@login_required
def invoice_view():
    inv_id = request.args.get("id", type=int)
    if inv_id is None:
        abort(400, description="Missing id")
    invoice = next((i for i in INVOICES if i["id"] == inv_id), None)
    if not invoice:
        abort(404)
    # 🚨 IDOR: No check that invoice['user_id'] == current_user()['id']
    return render_template("invoice.html", user=current_user(), invoice=invoice)

# --- Optional JSON API (also vulnerable) ---
@app.get("/api/invoice")
@login_required
def invoice_api():
    inv_id = request.args.get("id", type=int)
    if inv_id is None:
        return jsonify({"error": "missing id"}), 400
    invoice = next((i for i in INVOICES if i["id"] == inv_id), None)
    if not invoice:
        return jsonify({"error": "not found"}), 404
    # 🚨 IDOR: No ownership check here either
    return jsonify(invoice)

# --- A hardened example to show the fix (not wired into the UI) ---
@app.get("/secure/invoice")
@login_required
def secure_invoice():
    inv_id = request.args.get("id", type=int)
    if inv_id is None:
        return jsonify({"error": "missing id"}), 400
    user = current_user()
    invoice = next((i for i in INVOICES if i["id"] == inv_id and i["user_id"] == user["id"]), None)
    if not invoice:
        # Mask whether it exists at all to avoid leaking object existence
        return jsonify({"error": "not found"}), 404
    return jsonify(invoice)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
