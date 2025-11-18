

import streamlit as st
import pandas as pd
import re
import csv



st.set_page_config(
    page_title="Basket Price Comparator",
    layout="wide",
)

st.title("Basket Price Comparator – Walmart vs Safeway vs Your Store")

# --- Load data ------------------------------------------------------------- #
@st.cache_data
def load_data():
    df = pd.read_csv("walmart_data.csv")  # your file
    return df

df = load_data()

# Load store logos (local files in same folder)
wmt_logo = "wmt.png"
safeway_logo = "safeway.png"

# --- Price cleaning: "$1.27" -> 1.27 -------------------------------------- #
def price_to_float(price_str):
    if pd.isna(price_str):
        return None
    cleaned = re.sub(r"[^0-9.\-]", "", str(price_str))
    return float(cleaned) if cleaned else None

df["Walmart_price"] = df["Walmart"].astype(str).apply(price_to_float)
df["Safeway_price"]  = df["Safeway"].astype(str).apply(price_to_float)

df["Walmart_price"] = df["Walmart_price"].fillna(0)
df["Safeway_price"]  = df["Safeway_price"].fillna(0)

# --- Session state: quantities + your store prices ------------------------ #
if "quantities" not in st.session_state:
    st.session_state.quantities = {name: 1 for name in df["Name"]}

if "your_store_prices" not in st.session_state:
    # item name -> price at "Your Store"
    st.session_state.your_store_prices = {}

# --- Sidebar: Request a UPC ----------------------------------------------- #
st.sidebar.header("Request a UPC")
st.sidebar.caption("Need us to look up a UPC? Tell us which item below.")

if "requested_upcs" not in st.session_state:
    st.session_state.requested_upcs = []

upc_request = st.sidebar.text_input("Item name or description", key="upc_request_input")

if st.sidebar.button("Submit UPC Request"):
    if upc_request.strip():
        cleaned = upc_request.strip()

        # Save in session state (for display)
        st.session_state.requested_upcs.append(cleaned)

        # Append to CSV file
        try:
            with open("upc_requests.csv", "a", newline="") as f:
                writer = csv.writer(f)
                # you can add more fields here later (e.g. timestamp, user, etc.)
                writer.writerow([cleaned])
        except Exception as e:
            st.sidebar.warning(f"Could not write to CSV: {e}")

        st.sidebar.success("UPC request submitted!")
    else:
        st.sidebar.warning("Please enter a valid item name or description.")

if st.session_state.requested_upcs:
    st.sidebar.markdown("**Requested UPCs**")
    for r in st.session_state.requested_upcs:
        st.sidebar.markdown(f"- {r}")

# --- Basket summary container (defined BEFORE catalog) -------------------- #
basket_container = st.container()

st.markdown("---")
st.subheader("Catalog – Adjust Your Basket")

# ===================== CATALOG GRID (BOTTOM) =============================== #
n_cols = 4  # compact layout, 4 items per row

for i in range(0, len(df), n_cols):
    row_df = df.iloc[i: i + n_cols]
    cols = st.columns(len(row_df))

    for col, (idx, row) in zip(cols, row_df.iterrows()):
        with col:
            name = row["Name"]

            # small product image (from Walmart)
            walmart_img = row.get("Walmart Image")
            if isinstance(walmart_img, str) and walmart_img.strip():
                st.image(walmart_img, width=60)

            # Name
            st.caption(name)

            # Prices for Walmart & Safeway
            w_price = float(row["Walmart_price"]) if pd.notna(row["Walmart_price"]) else 0.0
            s_price = float(row["Safeway_price"]) if pd.notna(row["Safeway_price"]) else 0.0

            price_col1, price_col2, price_col3 = st.columns([1, 1, 1])

            # Walmart logo + price
            with price_col1:
                st.image(wmt_logo, width=22)
                st.write(f"${w_price:.2f}")

            # Safeway logo + price
            with price_col2:
                st.image(safeway_logo, width=22)
                st.write(f"${s_price:.2f}")

            # Your Store price input
            with price_col3:
                st.write("Your Store")
                default_your_price = st.session_state.your_store_prices.get(
                    name,
                    w_price if w_price > 0 else 0.0,
                )
                your_price = st.number_input(
                    "",
                    min_value=0.0,
                    step=0.01,
                    value=float(default_your_price),
                    key=f"your_store_price_{idx}",
                    label_visibility="collapsed",
                )
                st.session_state.your_store_prices[name] = your_price

            # Quantity input
            qty_key = f"qty_{idx}"
            current_qty = int(st.session_state.quantities.get(name, 1))
            new_qty = st.number_input(
                "Qty",
                min_value=0,
                step=1,
                value=current_qty,
                key=qty_key,
                label_visibility="collapsed",
            )
            st.session_state.quantities[name] = new_qty

# ===================== BUILD BASKET DATA (AFTER CATALOG) ================== #
basket_names = [name for name, q in st.session_state.quantities.items() if q > 0]
basket_df = df[df["Name"].isin(basket_names)].copy()

if not basket_df.empty:
    basket_df["Quantity"] = basket_df["Name"].map(st.session_state.quantities).astype(int)
    basket_df["Walmart_line_total"] = basket_df["Walmart_price"] * basket_df["Quantity"]
    basket_df["Safeway_line_total"] = basket_df["Safeway_price"] * basket_df["Quantity"]

    # Map your store prices from session_state
    basket_df["YourStore_price"] = basket_df["Name"].map(
        lambda n: st.session_state.your_store_prices.get(n, 0.0)
    )
    basket_df["YourStore_line_total"] = basket_df["YourStore_price"] * basket_df["Quantity"]

    walmart_total = float(basket_df["Walmart_line_total"].sum())
    safeway_total = float(basket_df["Safeway_line_total"].sum())
    your_store_total = float(basket_df["YourStore_line_total"].sum())
else:
    walmart_total = 0.0
    safeway_total = 0.0
    your_store_total = 0.0

# ===================== BASKET SUMMARY (TOP, USING CONTAINER) ============== #
with basket_container:
    st.subheader("Basket Summary")

    col1, col2, col3 = st.columns(3)

    col1.metric("Walmart basket", f"${walmart_total:,.2f}")

    safeway_delta = safeway_total - walmart_total
    safeway_delta_label = (
        f"+${abs(safeway_delta):,.2f} vs Walmart"
        if safeway_delta >= 0
        else f"-${abs(safeway_delta):,.2f} vs Walmart"
    )
    col2.metric("Safeway basket", f"${safeway_total:,.2f}", safeway_delta_label)

    your_store_delta = your_store_total - walmart_total
    your_store_delta_label = (
        f"+${abs(your_store_delta):,.2f} vs Walmart"
        if your_store_delta >= 0
        else f"-${abs(your_store_delta):,.2f} vs Walmart"
    )
    col3.metric("Your Store basket", f"${your_store_total:,.2f}", your_store_delta_label)

    # ---- Expandable table: item, qty, Walmart, Safeway, Your Store ----
    with st.expander("Items in your basket (click to expand)"):
        if not basket_df.empty:
            table_df = basket_df[
                ["Name", "Quantity", "Walmart_price", "Safeway_price", "YourStore_price"]
            ].copy()

            table_df = table_df.rename(columns={
                "Name": "Item",
                "Quantity": "Qty",
                "Walmart_price": "Walmart Price",
                "Safeway_price": "Safeway Price",
                "YourStore_price": "Your Store Price",
            })

            # Format prices with $
            for col in ["Walmart Price", "Safeway Price", "Your Store Price"]:
                table_df[col] = table_df[col].apply(lambda x: f"${x:.2f}")

            st.dataframe(table_df, use_container_width=True)
        else:
            st.write("Your basket is empty.")
