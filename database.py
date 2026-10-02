"""
database.py
Data-access layer for the Marketplace E-commerce Application.

Uses SQLite for simplicity and portability across Desktop, Web, and
Mobile deployments (single-file DB, zero server setup).
"""

import sqlite3
import hashlib
import os
import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "marketplace.db")

CATEGORIES = ["Electronics", "Fashion", "Groceries", "Books", "Pharmacy"]


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def init_db(reset: bool = False):
    """Create tables (and optionally seed demo data)."""
    if reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = get_conn()
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('buyer','seller','admin')),
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            image_emoji TEXT DEFAULT '📦',
            created_at TEXT NOT NULL,
            FOREIGN KEY (seller_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (buyer_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id),
            UNIQUE(buyer_id, product_id)
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_id INTEGER NOT NULL,
            total REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL,
            FOREIGN KEY (buyer_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            seller_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
        """
    )
    conn.commit()

    cur.execute("SELECT COUNT(*) AS c FROM users")
    if cur.fetchone()["c"] == 0:
        _seed(conn)

    conn.close()


def _seed(conn):
    now = datetime.datetime.now().isoformat()
    cur = conn.cursor()

    def add_user(name, email, password, role):
        salt = os.urandom(8).hex()
        cur.execute(
            "INSERT INTO users (name,email,salt,password_hash,role,created_at) VALUES (?,?,?,?,?,?)",
            (name, email, salt, hash_password(password, salt), role, now),
        )
        return cur.lastrowid

    admin_id = add_user("Admin", "admin@marketplace.test", "admin123", "admin")
    seller1 = add_user("TechHub Store", "seller1@marketplace.test", "seller123", "seller")
    seller2 = add_user("GadgetWorld", "seller2@marketplace.test", "seller123", "seller")
    add_user("Test Buyer", "buyer@marketplace.test", "buyer123", "buyer")

    demo_products = [
        (seller1, "Wireless Bluetooth Earbuds", "Noise-cancelling, 24h battery life", "Electronics", 15500, 40, "🎧"),
        (seller1, "Smartphone 128GB", "6.5-inch display, dual SIM, 5000mAh battery", "Electronics", 185000, 15, "📱"),
        (seller2, "Laptop Backpack", "Water-resistant, fits up to 15.6-inch laptops", "Fashion", 12000, 25, "🎒"),
        (seller2, "Smart Watch", "Heart-rate monitor, step counter, notifications", "Electronics", 32000, 20, "⌚"),
        (seller1, "LED Desk Lamp", "Adjustable brightness, USB powered", "Electronics", 8500, 30, "💡"),
        (seller2, "Men's Sneakers", "Breathable mesh, size 40-45 available", "Fashion", 21000, 18, "👟"),
        (seller1, "Power Bank 20000mAh", "Fast charging, dual USB output", "Electronics", 14000, 50, "🔋"),
        (seller2, "Kitchen Blender", "500W motor, 1.5L jug", "Groceries", 27000, 12, "🧃"),
    ]
    for seller_id, name, desc, cat, price, stock, emoji in demo_products:
        cur.execute(
            "INSERT INTO products (seller_id,name,description,category,price,stock,image_emoji,created_at) VALUES (?,?,?,?,?,?,?,?)",
            (seller_id, name, desc, cat, price, stock, emoji, now),
        )
    conn.commit()


# ---------- Users ----------

def create_user(name, email, password, role):
    conn = get_conn()
    try:
        salt = os.urandom(8).hex()
        conn.execute(
            "INSERT INTO users (name,email,salt,password_hash,role,created_at) VALUES (?,?,?,?,?,?)",
            (name, email, salt, hash_password(password, salt), role, datetime.datetime.now().isoformat()),
        )
        conn.commit()
        return True, "Account created."
    except sqlite3.IntegrityError:
        return False, "Email already registered."
    finally:
        conn.close()


def authenticate(email, password):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    if not row:
        return None
    if hash_password(password, row["salt"]) == row["password_hash"]:
        return dict(row)
    return None


# ---------- Products ----------

def list_products(search=None, category=None, seller_id=None):
    conn = get_conn()
    q = "SELECT * FROM products WHERE 1=1"
    params = []
    if search:
        q += " AND name LIKE ?"
        params.append(f"%{search}%")
    if category and category != "All":
        q += " AND category = ?"
        params.append(category)
    if seller_id:
        q += " AND seller_id = ?"
        params.append(seller_id)
    q += " ORDER BY created_at DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_product(product_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_product(seller_id, name, description, category, price, stock, emoji="📦"):
    conn = get_conn()
    conn.execute(
        "INSERT INTO products (seller_id,name,description,category,price,stock,image_emoji,created_at) VALUES (?,?,?,?,?,?,?,?)",
        (seller_id, name, description, category, price, stock, emoji, datetime.datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def update_product(product_id, **fields):
    if not fields:
        return
    conn = get_conn()
    cols = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(f"UPDATE products SET {cols} WHERE id = ?", list(fields.values()) + [product_id])
    conn.commit()
    conn.close()


def delete_product(product_id):
    conn = get_conn()
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()


# ---------- Cart ----------

def add_to_cart(buyer_id, product_id, quantity=1):
    conn = get_conn()
    existing = conn.execute(
        "SELECT * FROM cart_items WHERE buyer_id=? AND product_id=?", (buyer_id, product_id)
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE cart_items SET quantity = quantity + ? WHERE id = ?",
            (quantity, existing["id"]),
        )
    else:
        conn.execute(
            "INSERT INTO cart_items (buyer_id,product_id,quantity) VALUES (?,?,?)",
            (buyer_id, product_id, quantity),
        )
    conn.commit()
    conn.close()


def set_cart_quantity(buyer_id, product_id, quantity):
    conn = get_conn()
    if quantity <= 0:
        conn.execute("DELETE FROM cart_items WHERE buyer_id=? AND product_id=?", (buyer_id, product_id))
    else:
        conn.execute(
            "UPDATE cart_items SET quantity=? WHERE buyer_id=? AND product_id=?",
            (quantity, buyer_id, product_id),
        )
    conn.commit()
    conn.close()


def get_cart(buyer_id):
    conn = get_conn()
    rows = conn.execute(
        """SELECT c.id AS cart_id, c.quantity, p.*
           FROM cart_items c JOIN products p ON c.product_id = p.id
           WHERE c.buyer_id = ?""",
        (buyer_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def clear_cart(buyer_id):
    conn = get_conn()
    conn.execute("DELETE FROM cart_items WHERE buyer_id = ?", (buyer_id,))
    conn.commit()
    conn.close()


# ---------- Orders ----------

def checkout(buyer_id):
    """Create an order from the buyer's current cart and clear the cart."""
    items = get_cart(buyer_id)
    if not items:
        return None, "Cart is empty."

    for item in items:
        if item["quantity"] > item["stock"]:
            return None, f"Insufficient stock for {item['name']}."

    total = sum(item["price"] * item["quantity"] for item in items)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO orders (buyer_id,total,status,created_at) VALUES (?,?,?,?)",
        (buyer_id, total, "Pending", datetime.datetime.now().isoformat()),
    )
    order_id = cur.lastrowid
    for item in items:
        cur.execute(
            "INSERT INTO order_items (order_id,product_id,seller_id,quantity,price) VALUES (?,?,?,?,?)",
            (order_id, item["id"], item["seller_id"], item["quantity"], item["price"]),
        )
        cur.execute(
            "UPDATE products SET stock = stock - ? WHERE id = ?",
            (item["quantity"], item["id"]),
        )
    conn.commit()
    conn.close()
    clear_cart(buyer_id)
    return order_id, "Order placed."


def get_orders_for_buyer(buyer_id):
    conn = get_conn()
    orders = conn.execute(
        "SELECT * FROM orders WHERE buyer_id = ? ORDER BY created_at DESC", (buyer_id,)
    ).fetchall()
    result = []
    for o in orders:
        items = conn.execute(
            """SELECT oi.*, p.name FROM order_items oi
               JOIN products p ON oi.product_id = p.id WHERE oi.order_id = ?""",
            (o["id"],),
        ).fetchall()
        result.append({**dict(o), "items": [dict(i) for i in items]})
    conn.close()
    return result


def get_orders_for_seller(seller_id):
    """Order line-items belonging to a given seller, with buyer + order info."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT oi.*, o.created_at AS order_date, o.status AS order_status,
                  p.name AS product_name, u.name AS buyer_name
           FROM order_items oi
           JOIN orders o ON oi.order_id = o.id
           JOIN products p ON oi.product_id = p.id
           JOIN users u ON o.buyer_id = u.id
           WHERE oi.seller_id = ?
           ORDER BY o.created_at DESC""",
        (seller_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_order_item_status(order_id, new_status):
    conn = get_conn()
    conn.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
    conn.commit()
    conn.close()
