import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ---------------- DATABASE ----------------
conn = sqlite3.connect("wms.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    role TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS inventory (
    item TEXT PRIMARY KEY,
    category TEXT,
    stock INTEGER,
    reorder_level INTEGER,
    last_updated TEXT
)
""")

# Default admin
c.execute("SELECT * FROM users WHERE username='admin'")
if not c.fetchone():
    c.execute("INSERT INTO users VALUES ('admin','admin123','admin')")
    conn.commit()

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.session_state.role = ""
    st.session_state.page = "inventory"

# ---------------- LOGIN PAGE ----------------
def login_page():
    st.title("🔐 Warehouse Management System")
    st.subheader("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        c.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = c.fetchone()
        if user:
            st.session_state.logged_in = True
            st.session_state.user = user[0]
            st.session_state.role = user[2]
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")

# ---------------- INVENTORY ----------------
def inventory_management():
    st.header("📦 Inventory Management")

    with st.expander("➕ Add / Update Item"):
        item = st.text_input("Item Name")
        category = st.text_input("Category")
        stock = st.number_input("Stock", min_value=0, step=1)
        reorder = st.number_input("Reorder Level", min_value=0, step=1)

        if st.button("Save Item"):
            c.execute("""
            INSERT INTO inventory VALUES (?,?,?,?,?)
            ON CONFLICT(item) DO UPDATE SET
            category=excluded.category,
            stock=excluded.stock,
            reorder_level=excluded.reorder_level,
            last_updated=excluded.last_updated
            """, (
                item, category, stock, reorder,
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ))
            conn.commit()
            st.success("Item saved successfully")

    df = pd.read_sql("SELECT * FROM inventory", conn)
    st.subheader("📋 Inventory Data")
    st.dataframe(df, use_container_width=True)

# ---------------- STOCK ANALYSIS ----------------
def stock_analysis():
    st.header("📊 Stock Analysis")

    df = pd.read_sql("SELECT * FROM inventory", conn)

    if df.empty:
        st.warning("No inventory data found")
        return

    low_stock = df[df["stock"] <= df["reorder_level"]]

    col1, col2 = st.columns(2)
    col1.metric("Total Items", len(df))
    col2.metric("Low Stock Items", len(low_stock))

    st.subheader("⚠️ Low Stock Items")
    st.dataframe(low_stock, use_container_width=True)

# ---------------- PREDICTIVE ANALYTICS ----------------
def predictive_analytics():
    st.header("📈 Predictive Analytics")

    df = pd.read_sql("SELECT * FROM inventory", conn)

    if df.empty:
        st.warning("No data available")
        return

    df["forecast"] = df["stock"] + 10
    chart_df = df[["item", "stock", "forecast"]].set_index("item")

    st.line_chart(chart_df)

# ---------------- ADMIN PANEL ----------------
def admin_panel():
    st.header("🛠 Admin Panel")

    with st.expander("➕ Create User"):
        username = st.text_input("New Username")
        password = st.text_input("New Password")
        role = st.selectbox("Role", ["admin", "user"])

        if st.button("Create User"):
            c.execute(
                "INSERT OR IGNORE INTO users VALUES (?,?,?)",
                (username, password, role)
            )
            conn.commit()
            st.success("User created")

    users = pd.read_sql("SELECT username, role FROM users", conn)
    st.subheader("👥 Users")
    st.dataframe(users, use_container_width=True)

# ---------------- MAIN APP ----------------
def main_app():
    st.title("🏭 Warehouse Management System")

    col1, col2, col3, col4, col5 = st.columns(5)

    if col1.button("Inventory"):
        st.session_state.page = "inventory"
    if col2.button("Stock Analysis"):
        st.session_state.page = "analysis"
    if col3.button("Predictive"):
        st.session_state.page = "predict"
    if col4.button("Admin"):
        st.session_state.page = "admin"
    if col5.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    if st.session_state.page == "inventory":
        inventory_management()
    elif st.session_state.page == "analysis":
        stock_analysis()
    elif st.session_state.page == "predict":
        predictive_analytics()
    elif st.session_state.page == "admin":
        if st.session_state.role == "admin":
            admin_panel()
        else:
            st.error("Admin access only")

# ---------------- RUN ----------------
if not st.session_state.logged_in:
    login_page()
else:
    main_app()
