"""
main.py
Marketplace E-commerce Application (Python / Flet)

A single codebase that runs on Desktop, Web, and Mobile via Flet.

Run:
    python main.py                 # desktop window
    flet run --web main.py         # web (SPA)
    flet build apk / ipa / ...     # mobile packaging (see README.md)

Demo accounts (also printed on first run):
    buyer@marketplace.test   / buyer123
    seller1@marketplace.test / seller123
    admin@marketplace.test   / admin123
"""

import flet as ft
import database as db
from external_links import build_links

db.init_db()


def naira(amount: float) -> str:
    return f"₦{amount:,.2f}"


def main(page: ft.Page):
    page.title = "MarketLink — Multi-Vendor Marketplace"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = "#f5f6fa"
    page.window.width = 420
    page.window.height = 850

    # ---- in-memory session state (per connected client) ----
    state = {"user": None, "search": "", "category": "All", "editing_product": None}

    body = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)
    snack = ft.SnackBar(content=ft.Text(""))
    page.overlay.append(snack)

    def toast(msg, error=False):
        snack.content = ft.Text(msg)
        snack.bgcolor = "#d32f2f" if error else "#2e7d32"
        snack.open = True
        page.update()

    def set_body(*controls):
        body.controls = list(controls)
        page.update()

    # ---------------------------------------------------------------
    # NAV BAR
    # ---------------------------------------------------------------
    def nav_bar():
        user = state["user"]
        items = [
            ft.TextButton("Browse", on_click=lambda e: show_browse()),
        ]
        if user:
            if user["role"] == "buyer":
                items.append(ft.TextButton("Cart", on_click=lambda e: show_cart()))
                items.append(ft.TextButton("My Orders", on_click=lambda e: show_buyer_orders()))
            if user["role"] == "seller":
                items.append(ft.TextButton("Dashboard", on_click=lambda e: show_seller_dashboard()))
                items.append(ft.TextButton("Orders", on_click=lambda e: show_seller_orders()))
            items.append(ft.TextButton(f"👤 {user['name']}", disabled=True))
            items.append(ft.IconButton(ft.Icons.LOGOUT, tooltip="Log out", on_click=lambda e: logout()))
        else:
            items.append(ft.TextButton("Login", on_click=lambda e: show_login()))
            items.append(ft.TextButton("Register", on_click=lambda e: show_register()))

        return ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [ft.Icon(ft.Icons.STOREFRONT, color="white"),
                         ft.Text("MarketLink", size=20, weight="bold", color="white")]
                    ),
                    ft.Row(items, wrap=True),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            bgcolor="#2e3192",
            padding=15,
        )

    def refresh_shell():
        page.controls.clear()
        page.controls.append(nav_bar())
        page.controls.append(body)
        page.update()

    def logout():
        state["user"] = None
        refresh_shell()
        show_browse()

    # ---------------------------------------------------------------
    # AUTH
    # ---------------------------------------------------------------
    def show_login():
        email = ft.TextField(label="Email", autofocus=True)
        password = ft.TextField(label="Password", password=True, can_reveal_password=True)
        error = ft.Text("", color="red")

        def do_login(e):
            user = db.authenticate(email.value.strip(), password.value)
            if user:
                state["user"] = user
                refresh_shell()
                toast(f"Welcome back, {user['name']}!")
                show_browse()
            else:
                error.value = "Invalid email or password."
                page.update()

        set_body(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Login", size=24, weight="bold"),
                        email,
                        password,
                        error,
                        ft.ElevatedButton("Login", on_click=do_login, width=300),
                        ft.Text("Demo: buyer@marketplace.test / buyer123", size=11, color="grey"),
                        ft.Text("Demo: seller1@marketplace.test / seller123", size=11, color="grey"),
                    ],
                    spacing=15,
                ),
                padding=30,
            )
        )

    def show_register():
        name = ft.TextField(label="Full name", autofocus=True)
        email = ft.TextField(label="Email")
        password = ft.TextField(label="Password", password=True, can_reveal_password=True)
        role = ft.Dropdown(
            label="I am a...",
            options=[ft.dropdown.Option("buyer", "Buyer"), ft.dropdown.Option("seller", "Seller")],
            value="buyer",
        )
        error = ft.Text("", color="red")

        def do_register(e):
            if not (name.value and email.value and password.value):
                error.value = "All fields are required."
                page.update()
                return
            ok, msg = db.create_user(name.value.strip(), email.value.strip(), password.value, role.value)
            if ok:
                toast("Account created — please log in.")
                show_login()
            else:
                error.value = msg
                page.update()

        set_body(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Create account", size=24, weight="bold"),
                        name, email, password, role, error,
                        ft.ElevatedButton("Register", on_click=do_register, width=300),
                    ],
                    spacing=15,
                ),
                padding=30,
            )
        )

    # ---------------------------------------------------------------
    # BROWSE / PRODUCT CARD / DETAIL
    # ---------------------------------------------------------------
    def product_card(p):
        def open_detail(e):
            show_product_detail(p["id"])

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(p["image_emoji"], size=40),
                    ft.Text(p["name"], weight="bold", max_lines=2),
                    ft.Text(p["category"], size=11, color="grey"),
                    ft.Text(naira(p["price"]), color="#2e3192", weight="bold"),
                    ft.Text(f"Stock: {p['stock']}", size=11,
                            color="red" if p["stock"] == 0 else "grey"),
                    ft.OutlinedButton("View", on_click=open_detail, width=150),
                ],
                spacing=4,
            ),
            padding=12,
            bgcolor="white",
            border_radius=10,
            width=180,
            on_click=open_detail,
        )

    def show_browse():
        products = db.list_products(search=state["search"], category=state["category"])

        def do_search(e):
            state["search"] = e.control.value
            show_browse()

        def do_category(e):
            state["category"] = e.control.value
            show_browse()

        search_box = ft.TextField(
            label="Search products", value=state["search"], on_submit=do_search, expand=True,
            prefix_icon=ft.Icons.SEARCH,
        )
        cat_dropdown = ft.Dropdown(
            label="Category",
            width=180,
            value=state["category"],
            options=[ft.dropdown.Option("All")] + [ft.dropdown.Option(c) for c in db.CATEGORIES],
            on_change=do_category,
        )

        grid = ft.Row(wrap=True, spacing=12, run_spacing=12)
        for p in products:
            grid.controls.append(product_card(p))
        if not products:
            grid.controls.append(ft.Text("No products found.", color="grey"))

        set_body(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row([search_box, cat_dropdown]),
                        ft.Divider(),
                        grid,
                    ]
                ),
                padding=20,
            )
        )

    def show_product_detail(product_id):
        p = db.get_product(product_id)
        if not p:
            show_browse()
            return

        qty = ft.TextField(label="Quantity", value="1", width=100)

        def add_cart(e):
            if not state["user"] or state["user"]["role"] != "buyer":
                toast("Please log in as a buyer to add items to cart.", error=True)
                return
            try:
                q = max(1, int(qty.value))
            except ValueError:
                q = 1
            db.add_to_cart(state["user"]["id"], p["id"], q)
            toast(f"Added {q} × {p['name']} to cart.")

        links = build_links(p["name"])
        link_buttons = ft.Row(
            [
                ft.ElevatedButton(
                    f"Compare on {name}",
                    url=url,
                    icon=ft.Icons.OPEN_IN_NEW,
                )
                for name, url in links.items()
            ],
            wrap=True,
        )

        set_body(
            ft.Container(
                content=ft.Column(
                    [
                        ft.TextButton("← Back to browsing", on_click=lambda e: show_browse()),
                        ft.Text(p["image_emoji"], size=70),
                        ft.Text(p["name"], size=24, weight="bold"),
                        ft.Text(p["category"], color="grey"),
                        ft.Text(p["description"] or "", size=14),
                        ft.Text(naira(p["price"]), size=22, color="#2e3192", weight="bold"),
                        ft.Text(f"{p['stock']} in stock"),
                        ft.Row([qty, ft.ElevatedButton("Add to Cart", icon=ft.Icons.ADD_SHOPPING_CART, on_click=add_cart)]),
                        ft.Divider(),
                        ft.Text("Compare prices on other marketplaces:", weight="bold"),
                        ft.Text(
                            "These buttons open that platform's own search results for "
                            "this product name in a new tab — MarketLink does not pull "
                            "live data from these sites.",
                            size=11, color="grey", italic=True,
                        ),
                        link_buttons,
                    ],
                    spacing=10,
                ),
                padding=25,
            )
        )

    # ---------------------------------------------------------------
    # CART / CHECKOUT
    # ---------------------------------------------------------------
    def show_cart():
        user = state["user"]
        if not user or user["role"] != "buyer":
            toast("Please log in as a buyer to view your cart.", error=True)
            show_login()
            return

        items = db.get_cart(user["id"])
        rows = []
        total = 0
        for it in items:
            total += it["price"] * it["quantity"]

            def make_handlers(product_id):
                def dec(e):
                    item = next(i for i in db.get_cart(user["id"]) if i["id"] == product_id)
                    db.set_cart_quantity(user["id"], product_id, item["quantity"] - 1)
                    show_cart()

                def inc(e):
                    item = next(i for i in db.get_cart(user["id"]) if i["id"] == product_id)
                    db.set_cart_quantity(user["id"], product_id, item["quantity"] + 1)
                    show_cart()

                def remove(e):
                    db.set_cart_quantity(user["id"], product_id, 0)
                    show_cart()

                return dec, inc, remove

            dec, inc, remove = make_handlers(it["id"])
            rows.append(
                ft.Row(
                    [
                        ft.Text(it["image_emoji"], size=24),
                        ft.Text(it["name"], expand=True),
                        ft.IconButton(ft.Icons.REMOVE, on_click=dec),
                        ft.Text(str(it["quantity"])),
                        ft.IconButton(ft.Icons.ADD, on_click=inc),
                        ft.Text(naira(it["price"] * it["quantity"]), width=100),
                        ft.IconButton(ft.Icons.DELETE, icon_color="red", on_click=remove),
                    ]
                )
            )

        def do_checkout(e):
            order_id, msg = db.checkout(user["id"])
            if order_id:
                toast(f"Order #{order_id} placed successfully!")
                show_buyer_orders()
            else:
                toast(msg, error=True)

        set_body(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Your Cart", size=24, weight="bold"),
                        *(rows if rows else [ft.Text("Your cart is empty.", color="grey")]),
                        ft.Divider(),
                        ft.Text(f"Total: {naira(total)}", size=18, weight="bold"),
                        ft.ElevatedButton(
                            "Checkout", icon=ft.Icons.PAYMENT, on_click=do_checkout, disabled=not rows
                        ),
                    ],
                    spacing=10,
                ),
                padding=25,
            )
        )

    def show_buyer_orders():
        user = state["user"]
        orders = db.get_orders_for_buyer(user["id"])
        controls = [ft.Text("My Orders", size=24, weight="bold")]
        if not orders:
            controls.append(ft.Text("No orders yet.", color="grey"))
        for o in orders:
            item_lines = [ft.Text(f"  {i['quantity']} × {i['name']} — {naira(i['price']*i['quantity'])}") for i in o["items"]]
            controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(f"Order #{o['id']}", weight="bold"),
                                    ft.Text(o["status"], color="orange" if o["status"] == "Pending" else "green"),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Text(o["created_at"][:19], size=11, color="grey"),
                            *item_lines,
                            ft.Text(f"Total: {naira(o['total'])}", weight="bold"),
                        ]
                    ),
                    bgcolor="white",
                    padding=15,
                    border_radius=10,
                )
            )
        set_body(ft.Container(content=ft.Column(controls, spacing=12), padding=25))

    # ---------------------------------------------------------------
    # SELLER DASHBOARD
    # ---------------------------------------------------------------
    def show_seller_dashboard():
        user = state["user"]
        if not user or user["role"] != "seller":
            toast("Please log in as a seller.", error=True)
            show_login()
            return

        products = db.list_products(seller_id=user["id"])

        name = ft.TextField(label="Product name")
        desc = ft.TextField(label="Description", multiline=True)
        cat = ft.Dropdown(label="Category", options=[ft.dropdown.Option(c) for c in db.CATEGORIES])
        price = ft.TextField(label="Price (₦)", keyboard_type=ft.KeyboardType.NUMBER)
        stock = ft.TextField(label="Stock", keyboard_type=ft.KeyboardType.NUMBER)
        emoji = ft.TextField(label="Icon (emoji)", value="📦", width=100)
        form_error = ft.Text("", color="red")

        editing_id = state.get("editing_product")
        submit_label = "Save Changes" if editing_id else "Add Product"

        if editing_id:
            p = db.get_product(editing_id)
            name.value, desc.value, cat.value = p["name"], p["description"], p["category"]
            price.value, stock.value, emoji.value = str(p["price"]), str(p["stock"]), p["image_emoji"]

        def submit(e):
            if not (name.value and cat.value and price.value and stock.value):
                form_error.value = "Please fill in all required fields."
                page.update()
                return
            try:
                price_v, stock_v = float(price.value), int(stock.value)
            except ValueError:
                form_error.value = "Price/Stock must be numeric."
                page.update()
                return

            if editing_id:
                db.update_product(
                    editing_id, name=name.value, description=desc.value, category=cat.value,
                    price=price_v, stock=stock_v, image_emoji=emoji.value or "📦",
                )
                toast("Product updated.")
                state["editing_product"] = None
            else:
                db.add_product(user["id"], name.value, desc.value, cat.value, price_v, stock_v, emoji.value or "📦")
                toast("Product added.")
            show_seller_dashboard()

        def edit_product(pid):
            state["editing_product"] = pid
            show_seller_dashboard()

        def delete_product(pid):
            db.delete_product(pid)
            toast("Product deleted.")
            show_seller_dashboard()

        product_rows = []
        for p in products:
            product_rows.append(
                ft.Row(
                    [
                        ft.Text(p["image_emoji"]),
                        ft.Text(p["name"], expand=True),
                        ft.Text(naira(p["price"]), width=110),
                        ft.Text(f"Stock: {p['stock']}", width=90),
                        ft.IconButton(ft.Icons.EDIT, on_click=lambda e, pid=p["id"]: edit_product(pid)),
                        ft.IconButton(ft.Icons.DELETE, icon_color="red", on_click=lambda e, pid=p["id"]: delete_product(pid)),
                    ]
                )
            )

        set_body(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Seller Dashboard", size=24, weight="bold"),
                        ft.Text(f"{'Editing product' if editing_id else 'Add a new product'}", weight="bold"),
                        name, desc, cat, price, stock, emoji, form_error,
                        ft.ElevatedButton(submit_label, on_click=submit),
                        ft.Divider(),
                        ft.Text("My Products", size=18, weight="bold"),
                        *(product_rows if product_rows else [ft.Text("No products listed yet.", color="grey")]),
                    ],
                    spacing=10,
                ),
                padding=25,
            )
        )

    def show_seller_orders():
        user = state["user"]
        rows = db.get_orders_for_seller(user["id"])
        controls = [ft.Text("Orders for My Products", size=24, weight="bold")]
        if not rows:
            controls.append(ft.Text("No orders yet.", color="grey"))

        STATUSES = ["Pending", "Processing", "Shipped", "Delivered", "Cancelled"]

        for r in rows:
            def make_change(order_id):
                def change(e):
                    db.update_order_item_status(order_id, e.control.value)
                    toast(f"Order #{order_id} marked {e.control.value}.")
                return change

            controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(f"Order #{r['order_id']}"),
                            ft.Text(r["product_name"], expand=True),
                            ft.Text(f"× {r['quantity']}"),
                            ft.Text(r["buyer_name"], italic=True),
                            ft.Dropdown(
                                value=r["order_status"],
                                options=[ft.dropdown.Option(s) for s in STATUSES],
                                width=150,
                                on_change=make_change(r["order_id"]),
                            ),
                        ]
                    ),
                    bgcolor="white",
                    padding=10,
                    border_radius=8,
                )
            )
        set_body(ft.Container(content=ft.Column(controls, spacing=10), padding=25))

    # ---------------------------------------------------------------
    refresh_shell()
    show_browse()


if __name__ == "__main__":
    ft.app(target=main)
