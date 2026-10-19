from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import date, datetime, timedelta
from functools import wraps
from werkzeug.security import check_password_hash
from database.db import (
    get_db,
    init_db,
    seed_db,
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_expense_summary,
    get_category_breakdown,
)

app = Flask(__name__)
app.secret_key = "dev-secret-change-in-prod"


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

with app.app_context():
    init_db()
    seed_db()


def parse_date_filter(raw_from, raw_to):
    """Validate the from/to query params. Returns (date_from, date_to, error)."""
    values = {}
    error = None
    for key, raw in (("from", raw_from), ("to", raw_to)):
        if not raw:
            continue
        try:
            values[key] = datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            error = "Invalid date. Use the YYYY-MM-DD format."

    date_from = values.get("from")
    date_to = values.get("to")
    if date_from and date_to and date_from > date_to:
        return None, None, "Start date must be on or before the end date."
    return date_from, date_to, error


def format_range_label(date_from, date_to):
    fmt = "%d %b %Y"
    if date_from and date_to:
        return f"{date_from.strftime(fmt)} – {date_to.strftime(fmt)}"
    if date_from:
        return f"From {date_from.strftime(fmt)}"
    if date_to:
        return f"Until {date_to.strftime(fmt)}"
    return "All time"


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    user = get_user_by_id(session["user_id"]) if session.get("user_id") else None
    return render_template("landing.html", user=user)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name     = request.form.get("name", "").strip()
    email    = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not name or not email or not password:
        return render_template("register.html", error="All fields are required.")
    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters.")

    try:
        create_user(name, email, password)
    except sqlite3.IntegrityError:
        return render_template("register.html", error="An account with that email already exists.")

    flash("Account created! Please sign in.", "success")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "GET":
        return render_template("login.html")

    email    = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    user = get_user_by_email(email)

    if not user or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid email or password.")

    session["user_id"] = user["id"]
    return redirect(url_for("landing"))


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
@login_required
def profile():
    user_row = get_user_by_id(session["user_id"])
    date_from, date_to, filter_error = parse_date_filter(
        request.args.get("from", "").strip(), request.args.get("to", "").strip()
    )
    iso_from = date_from.isoformat() if date_from else None
    iso_to = date_to.isoformat() if date_to else None

    summary = get_expense_summary(session["user_id"], iso_from, iso_to)
    breakdown_rows = get_category_breakdown(session["user_id"], iso_from, iso_to)

    today = date.today()
    presets = [
        {"label": "This Month", "params": {"from": today.replace(day=1).isoformat(), "to": today.isoformat()}},
        {"label": "Last 30 Days", "params": {"from": (today - timedelta(days=29)).isoformat(), "to": today.isoformat()}},
        {"label": "All Time", "params": {}},
    ]

    member_since = datetime.strptime(
        user_row["created_at"], "%Y-%m-%d %H:%M:%S"
    ).strftime("%B %d, %Y")

    user = {"name": user_row["name"], "email": user_row["email"]}

    max_total = max((row["total"] for row in breakdown_rows), default=0)
    category_breakdown = [
        {
            "category": row["category"],
            "total_display": f"₹{row['total']:,.2f}",
            "percent": max(round((row["total"] / max_total) * 100), 4) if max_total else 0,
        }
        for row in breakdown_rows
    ]

    return render_template(
        "profile.html",
        user=user,
        member_since=member_since,
        summary=summary,
        total_spent_display=f"₹{summary['total_spent']:,.2f}",
        category_breakdown=category_breakdown,
        date_from=iso_from or "",
        date_to=iso_to or "",
        filter_error=filter_error,
        is_filtered=bool(date_from or date_to),
        range_label=format_range_label(date_from, date_to),
        presets=presets,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
