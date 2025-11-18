import streamlit as st
import pandas as pd
import re

st.set_page_config(
    page_title="Basket Price Comparator",
    layout="wide",
)

st.title("Basket Price Comparator – Walmart vs Safeway")

# --- Load data ------------------------------------------------------------- #
@st.cache_data
def load_data():
    # Replace with your actual CSV path/name
    df = pd.read_csv("walmart_data.csv")
    return df

df = load_data()

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

# --- Session state: quantities (default 1 each) ---------------------------- #
if "quantities" not in st.session_state:
    st.session_state.quantities = {}

for name in df["Name"]:
    st.session_state.quantities.setdefault(name, 1)

# --- Sidebar: Request a UPC ----------------------------------------------- #
st.sidebar.header("Request a UPC")
st.sidebar.caption("Need us to look up a UPC? Tell us which item below.")

if "requested_upcs" not in st.session_state:
    st.session_state.requested_upcs = []

upc_request = st.sidebar.text_input("Item name or description", key="upc_request_input")
if st.sidebar.button("Submit UPC Request"):
    if upc_request.strip():
        st.session_state.requested_upcs.append(upc_request.strip())
        st.sidebar.success("UPC request submitted!")
    else:
        st.sidebar.warning("Please enter a valid item name or description.")

if st.session_state.requested_upcs:
    st.sidebar.markdown("**Requested UPCs**")
    for r in st.session_state.requested_upcs:
        st.sidebar.markdown(f"- {r}")

# --- Placeholder for TOP basket section ----------------------------------- #
basket_container = st.container()

st.markdown("---")
st.subheader("Catalog – Adjust Your Basket")

# ===================== BOTTOM: CATALOG GRID =============================== #
# Compact multi-column layout; changing quantities updates the basket
n_cols = 4  # number of items per row

for i in range(0, len(df), n_cols):
    row_df = df.iloc[i : i + n_cols]
    cols = st.columns(len(row_df))

    for col, (idx, row) in zip(cols, row_df.iterrows()):
        with col:
            name = row["Name"]

            # One small image (Walmart)
            walmart_img = row.get("Walmart Image")
            if isinstance(walmart_img, str) and walmart_img.strip():
                st.image(walmart_img, width=60)

            # Name
            st.caption(name)

            # Tiny price line
            price_parts = []
            if row["Walmart_price"] > 0:
                price_parts.append(f"W: ${row['Walmart_price']:.2f}")
            if row["Safeway_price"] > 0:
                price_parts.append(f"S: ${row['Safeway_price']:.2f}")
            if price_parts:
                st.markdown(" · ".join(price_parts))

            # Quantity control (defaults from session_state, usually 1)
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

# ===================== TOP: BASKET (renders via container) ================ #
with basket_container:
    st.subheader("Basket Summary")

    # Build basket from quantities
    basket_names = [name for name, q in st.session_state.quantities.items() if q > 0]
    basket_df = df[df["Name"].isin(basket_names)].copy()

    if not basket_df.empty:
        basket_df["Quantity"] = basket_df["Name"].map(st.session_state.quantities).astype(int)
        basket_df["Walmart_line_total"] = basket_df["Walmart_price"] * basket_df["Quantity"]
        basket_df["Safeway_line_total"] = basket_df["Safeway_price"] * basket_df["Quantity"]

        walmart_total = float(basket_df["Walmart_line_total"].sum())
        safeway_total = float(basket_df["Safeway_line_total"].sum())
    else:
        walmart_total = 0.0
        safeway_total = 0.0

    # Basket totals
    m1, m2 = st.columns(2)
    m1.metric("Walmart basket", f"${walmart_total:,.2f}")

    safeway_delta = safeway_total - walmart_total
    safeway_delta_label = (
        f"+${abs(safeway_delta):,.2f} vs Walmart"
        if safeway_delta >= 0
        else f"-${abs(safeway_delta):,.2f} vs Walmart"
    )
    m2.metric("Safeway basket", f"${safeway_total:,.2f}", safeway_delta_label)

    # Item-level breakdown
    st.markdown("### Item-level Breakdown")

    if not basket_df.empty:
        display_cols = [
            "Name",
            "Quantity",
            "Walmart_price",
            "Walmart_line_total",
            "Safeway_price",
            "Safeway_line_total",
        ]
        pretty_basket = basket_df[display_cols].rename(
            columns={
                "Walmart_price": "Walmart price",
                "Walmart_line_total": "Walmart total",
                "Safeway_price": "Safeway price",
                "Safeway_line_total": "Safeway total",
            }
        )
        st.dataframe(pretty_basket, use_container_width=True)
    else:
        st.info("No items in your basket yet – set quantities in the catalog below.")
