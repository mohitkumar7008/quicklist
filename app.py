"""
QuickList -- a tiny CRUD app, built as a TEMPLATE.

The idea on purpose: "items" with a title + description is generic enough
that renaming a few words turns this into a dozen different real projects
(see the Day 8 deck / README for the list). The code itself should be small
enough to read start to finish in a few minutes -- that's the point.
"""
from flask import Flask, request, jsonify, render_template, g
import sqlite3
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "items.db")


def get_db():
    """One connection per request, reused if already open this request."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.commit()
    db.close()


@app.route("/")
def home():
    db = get_db()
    rows = db.execute("SELECT * FROM items ORDER BY id DESC").fetchall()
    return render_template("index.html", items=rows)


@app.route("/add", methods=["POST"])
def add_item_form():
    # Plain HTML form submission (not JSON) -- so the browser demo works
    # with zero JavaScript. The /items JSON endpoints below are the ones
    # meant for curl/Postman/another program to use.
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    if title:
        db = get_db()
        db.execute(
            "INSERT INTO items (title, description) VALUES (?, ?)",
            (title, description),
        )
        db.commit()
    return home_redirect()


@app.route("/delete/<int:item_id>", methods=["POST"])
def delete_item_form(item_id):
    db = get_db()
    db.execute("DELETE FROM items WHERE id = ?", (item_id,))
    db.commit()
    return home_redirect()


def home_redirect():
    from flask import redirect, url_for
    return redirect(url_for("home"))


@app.route("/health")
def health():
    # Same pattern as Day 6/7: a machine-readable liveness check.
    try:
        get_db().execute("SELECT 1")
        return jsonify(status="ok"), 200
    except Exception as exc:
        return jsonify(status="error", detail=str(exc)), 500


@app.route("/items", methods=["GET"])
def list_items():
    db = get_db()
    rows = db.execute("SELECT * FROM items ORDER BY id DESC").fetchall()
    return jsonify([dict(row) for row in rows])


@app.route("/items", methods=["POST"])
def create_item():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    if not title:
        return jsonify(error="title is required"), 400
    db = get_db()
    cur = db.execute(
        "INSERT INTO items (title, description) VALUES (?, ?)",
        (title, description),
    )
    db.commit()
    new_row = db.execute("SELECT * FROM items WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(new_row)), 201


@app.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    db = get_db()
    row = db.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        return jsonify(error="not found"), 404
    return jsonify(dict(row))


@app.route("/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    db = get_db()
    row = db.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        return jsonify(error="not found"), 404
    data = request.get_json(silent=True) or {}
    title = data.get("title", row["title"])
    description = data.get("description", row["description"])
    db.execute(
        "UPDATE items SET title = ?, description = ? WHERE id = ?",
        (title, description, item_id),
    )
    db.commit()
    updated = db.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    return jsonify(dict(updated))


@app.route("/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    db = get_db()
    row = db.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        return jsonify(error="not found"), 404
    db.execute("DELETE FROM items WHERE id = ?", (item_id,))
    db.commit()
    return jsonify(deleted=item_id), 200


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
