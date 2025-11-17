from flask import Flask, render_template, request, redirect, url_for, session, abort, jsonify, make_response
from functools import wraps
import base64, uuid, io, csv, time

app = Flask(__name__)

def b64encode_filter(s):
    s = str(s)
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")

app.add_template_filter(b64encode_filter, "b64encode")

app.secret_key = "advanced-idor-demo-not-for-prod"

# --- Fake DB ---
USERS = {
    "ahmed": {"id": 1, "password": "oppenheimer", "name": "Alice Liddell"},
    "alone":   {"id": 2, "password": "lonely",    "name": "Alone Musk."},
}

INVOICES = [
    {"uuid": "51e7b908-0a22-4b7e-8952-1d8a39506e10", "order_no": 100001, "user_id": 1, "amount": 42.00, "description": "Starter Plan - Oct", "line_items": ["Service fee"], "notes": "Thanks, Alice!"},
    {"uuid": "1d3edb0d-14a6-45a2-9f67-65c2a9b7b9a2", "order_no": 100002, "user_id": 1, "amount": 15.99, "description": "Add-on - Extra storage", "line_items": ["Storage 10GB"], "notes": ""},
    # Elon Musk invoice hides the flag
    {"uuid": "b5a7a7e6-8c17-4c9b-b2fc-2d7c0b9a3f16", "order_no": 200001, "user_id": 2, "amount": 1333333333333337.00, "description": "Executive Plan - Confidential", "line_items": ["Retainer", "Special ops"], "notes": "flag{IDOR_TEAM_42_s3ed_9f1c2a7b4d6e8c3f0b1}"}
]

def current_user():
    uname = session.get("username")
    if uname and uname in USERS:
        return {"username": uname, **USERS[uname]}
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
    return redirect(url_for("dashboard") if current_user() else url_for("login"))

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

@app.get("/invoice/<uuid_str>")
@login_required
def invoice_view(uuid_str):
    try:
        _ = uuid.UUID(uuid_str)
    except Exception:
        abort(404)
    u = current_user()
    inv = next((i for i in INVOICES if i["uuid"] == uuid_str and i["user_id"] == u["id"]), None)
    if not inv:
        abort(404)
    return render_template("invoice.html", user=u, invoice=inv)

# --- Dashboard ---
@app.get("/dashboard")
@login_required
def dashboard():
    u = current_user()
    my_invoices = [i for i in INVOICES if i["user_id"] == u["id"]]
    announcement = "Heads up: Legacy order numbers (>= 200000) will be retired soon in favor of UUIDs."
    return render_template("dashboard.html", user=u, invoices=my_invoices, announcement=announcement)

@app.get("/export/invoice")
@login_required
def export_invoice():
    ref = request.args.get("ref", "")
    if not ref:
        abort(400, description="missing ref")
    try:
        decoded = base64.urlsafe_b64decode(ref + "===")
        order_no = int(decoded.decode("utf-8"))
    except Exception:
        abort(400, description="bad ref")
    inv = next((i for i in INVOICES if i["order_no"] == order_no), None)
    if not inv:
        abort(404)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["order_no","uuid","amount","description","notes"])
    writer.writerow([inv["order_no"], inv["uuid"], inv["amount"], inv["description"], inv.get("notes","")])
    csv_bytes = output.getvalue().encode("utf-8")
    resp = make_response(csv_bytes)
    resp.headers["Content-Type"] = "text/csv"
    resp.headers["Content-Disposition"] = f'attachment; filename="invoice_{order_no}.csv"'
    return resp

@app.get("/support")
@login_required
def support():
    u = current_user()
    my_orders = [i["order_no"] for i in INVOICES if i["user_id"] == u["id"]]
    csrf = base64.urlsafe_b64encode(f"{u['username']}:{int(time.time())}".encode()).decode()
    return render_template("support.html", user=u, my_orders=my_orders, csrf=csrf)

@app.post("/support/preview")
@login_required
def support_preview():
    _csrf = request.form.get("csrf", "")
    try:
        base64.urlsafe_b64decode(_csrf + "===")
    except Exception:
        pass
    try:
        order_no = int(request.form.get("order_no", ""))
    except ValueError:
        abort(400)
    inv = next((i for i in INVOICES if i["order_no"] == order_no), None)
    if not inv:
        abort(404)
    return render_template("support_preview.html", invoice=inv, user=current_user())

# @app.get("/secure/export")
# @login_required
# def secure_export():
#     ref = request.args.get("ref", "")
#     try:
#         order_no = int(base64.urlsafe_b64decode(ref + "===").decode("utf-8"))
#     except Exception:
#         return jsonify({"error": "bad ref"}), 400
#     u = current_user()
#     inv = next((i for i in INVOICES if i["order_no"] == order_no and i["user_id"] == u["id"]), None)
#     if not inv:
#         return jsonify({"error": "not found"}), 404
#     return jsonify({"ok": True, "order_no": inv["order_no"], "uuid": inv["uuid"]})

@app.get("/api/invoice/search")
@login_required
def search_invoices():
    q = (request.args.get("q") or "").lower()
    u = current_user()
    results = [i for i in INVOICES if i["user_id"] == u["id"] and (q in i["description"].lower() or q in str(i["order_no"]))]
    return jsonify({"count": len(results), "results": [{"uuid": i["uuid"], "order_no": i["order_no"]} for i in results]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)

from jinja2 import Environment
def _b64encode(s):
    import base64
    if not isinstance(s, str): s = str(s)
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip('=')
app.jinja_env.filters['b64encode'] = _b64encode
