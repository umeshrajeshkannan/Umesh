import sqlite3
from datetime import datetime

DB_NAME = "orders.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Create menu table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    """)

    # Create orders table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_time TEXT NOT NULL,
            status TEXT NOT NULL,
            payment_status TEXT NOT NULL
        )
    """)

    # Create order_items table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            line_total REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(item_id) REFERENCES menu_items(id)
        )
    """)

    conn.commit()
    conn.close()


# ---------- MENU FUNCTIONS ----------

def add_menu_item():
    name = input("Enter item name: ")
    try:
        price = float(input("Enter item price: "))
    except ValueError:
        print("Invalid price.")
        return

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO menu_items (name, price) VALUES (?, ?)", (name, price))
    conn.commit()
    conn.close()
    print("Item added successfully.")


def list_menu_items():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, price FROM menu_items")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("No menu items found.")
        return

    print("\n--- MENU ---")
    for r in rows:
        print(f"{r[0]}. {r[1]} - Rs.{r[2]:.2f}")
    print("------------")


# ---------- ORDER FUNCTIONS ----------

def place_order():
    # show menu
    list_menu_items()
    conn = get_connection()
    cur = conn.cursor()

    # check if menu has items
    cur.execute("SELECT COUNT(*) FROM menu_items")
    if cur.fetchone()[0] == 0:
        print("Cannot place order. Menu is empty.")
        conn.close()
        return

    order_items = []
    while True:
        item_id = input("Enter item id to add to order (or 'done' to finish): ")
        if item_id.lower() == "done":
            break
        try:
            item_id_int = int(item_id)
        except ValueError:
            print("Invalid item id.")
            continue

        quantity = input("Enter quantity: ")
        try:
            qty_int = int(quantity)
        except ValueError:
            print("Invalid quantity.")
            continue

        # get item price
        cur.execute("SELECT price FROM menu_items WHERE id = ?", (item_id_int,))
        row = cur.fetchone()
        if not row:
            print("Item id not found.")
            continue

        price = row[0]
        line_total = price * qty_int
        order_items.append((item_id_int, qty_int, line_total))
        print("Item added to order.")

    if not order_items:
        print("No items in order. Cancelled.")
        conn.close()
        return

    # create order header
    order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "Placed"
    payment_status = "Pending"

    cur.execute(
        "INSERT INTO orders (order_time, status, payment_status) VALUES (?, ?, ?)",
        (order_time, status, payment_status),
    )
    order_id = cur.lastrowid

    # insert order items
    cur.executemany(
        "INSERT INTO order_items (order_id, item_id, quantity, line_total) "
        "VALUES (?, ?, ?, ?)",
        [(order_id, item_id, qty, total) for (item_id, qty, total) in order_items],
    )

    conn.commit()
    conn.close()
    print(f"Order #{order_id} placed successfully with {len(order_items)} items.")


def view_order_history():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT o.id, o.order_time, o.status, o.payment_status,
               SUM(oi.line_total) as total_amount
        FROM orders o
        LEFT JOIN order_items oi ON o.id = oi.order_id
        GROUP BY o.id, o.order_time, o.status, o.payment_status
        ORDER BY o.id DESC
    """)

    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("No orders found.")
        return

    print("\n--- ORDER HISTORY ---")
    for r in rows:
        order_id, order_time, status, payment_status, total_amount = r
        total_amount = total_amount if total_amount is not None else 0.0
        print(
            f"Order #{order_id} | Time: {order_time} | "
            f"Status: {status} | Payment: {payment_status} | "
            f"Total: Rs.{total_amount:.2f}"
        )
    print("----------------------")


def update_payment_status():
    try:
        order_id = int(input("Enter order id to update payment status: "))
    except ValueError:
        print("Invalid order id.")
        return

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, payment_status FROM orders WHERE id = ?", (order_id,))
    row = cur.fetchone()
    if not row:
        print("Order not found.")
        conn.close()
        return

    print(f"Current payment status: {row[1]}")
    new_status = input("Enter new payment status (e.g., Paid, Pending): ").strip()

    cur.execute(
        "UPDATE orders SET payment_status = ? WHERE id = ?",
        (new_status, order_id),
    )
    conn.commit()
    conn.close()
    print("Payment status updated.")


# ---------- MAIN MENU ----------

def main_menu():
    init_db()

    while True:
        print("\n===== ONLINE ORDER SYSTEM =====")
        print("1. Add item to menu")
        print("2. View menu")
        print("3. Place order")
        print("4. View order history")
        print("5. Update payment status")
        print("0. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            add_menu_item()
        elif choice == "2":
            list_menu_items()
        elif choice == "3":
            place_order()
        elif choice == "4":
            view_order_history()
        elif choice == "5":
            update_payment_status()
        elif choice == "0":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Try again.")


if __name__ == "__main__":
    main_menu()
