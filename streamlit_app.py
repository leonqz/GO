import streamlit as st
import pandas as pd
import re

st.set_page_config(
    page_title="Basket Price Comparator",
    layout="wide",
)

st.title("Basket Price Comparator – Walmart vs Safeway vs Your Competitor")

# --- Load data ------------------------------------------------------------- #
@st.cache_data
def load_data():
    df = pd.read_csv("walmart_data.csv")
    return df

df = load_data()

# Clean price strings like "$1.27" → 1.27
def price_to_float(price_str):
    if pd.isna(price_str):
        return None
    cleaned = re.sub(r"[^0-9.\-]", "", str(price_str))
    return float(cleaned) if cleaned else None

df["Walmart_price"] = df["Walmart"].astype(str).apply(price_to_float)
df["Safeway_price"]  = df["Safeway"].astype(str).apply(price_to_float)

# Replace missing prices with 0 to avoid math issues
df["Walmart_price"] = df["Walmart_price"].fillna(0)
df["Safeway_price"]  = df["Safeway_price"].fillna(0)

# --- Session state: default 1 of each item -------------------------------- #
if "quantities" not in st.session_state:
    st.session_state.quantities = {name: 1 for name in df["Name"]}

# --- Layout: left = item grid, right = basket comparison ------------------- #
left_col, right_col = st.columns([3, 2])

# ===================== LEFT: COMPACT ITEM GRID ============================ #
with left_col:
    st.subheader("Items – Adjust Your Basket")

    # 4 compact cards per row
    n_cols = 4

    for i in range(0, len(df), n_cols):
        row_df = df.iloc[i : i + n_cols]
        cols = st.columns(len(row_df))

        for col, (_, row) in zip(cols, row_df.iterrows()):
            with col:
                name = row["Name"]

                # One small image (Walmart)
                walmart_img = row.get("Walmart Image")
                if pd.notna(walmart_img) and str(walmart_img).strip():
                    st.image(str(walmart_img), width=60)

                # Name (short, compact)
                st.caption(name)

                # Tiny price line
                price_parts = []
                if row["Walmart_price"] > 0:
                    price_parts.append(f"W: ${row['Walmart_price']:.2f}")
                if row["Safeway_price"] > 0:
                    price_parts.append(f"S: ${row['Safeway_price']:.2f}")
                if price_parts:
                    st.markdown(" · ".join(price_parts))

                # Quantity control (defaults to 1)
                qty_key = f"qty_{name}"
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

# Build basket from current quantities
basket_names = [name for name, q in st.session_state.quantities.items() if q > 0]
basket_df = df[df["Name"].isin(basket_names)].copy()
basket_df["Quantity"] = basket_df["Name"].map(st.session_state.quantities).astype(int)

if not basket_df.empty:
    basket_df["Walmart_line_total"] = (
        basket_df["Walmart_price"] * basket_df["Quantity"]
    )
    basket_df["Safeway_line_total"] = (
        basket_df["Safeway_price"] * basket_df["Quantity"]
    )
else:
    basket_df["Walmart_line_total"] = 0.0
    basket_df["Safeway_line_total"] = 0.0

# ===================== RIGHT: BASKET COMPARISON ============================ #
with right_col:
    st.subheader("Basket Comparison")

    # Totals
    walmart_total = float(basket_df["Walmart_line_total"].sum()) if not basket_df.empty else 0.0
    safeway_total = float(basket_df["Safeway_line_total"].sum()) if not basket_df.empty else 0.0

    # Summary metrics
    st.markdown("### Basket Totals")

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
        st.info("No items in your basket yet – adjust quantities on the left.")

    # Summary metrics
    st.markdown("### Basket Totals")

    m1, m2, m3 = st.columns(3)

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
        st.info("No items in your basket yet – adjust quantities on the left.")

    # ===================== UPC REQUEST SECTION ============================ #
    st.markdown("---")
    st.subheader("Request a UPC")

    st.caption("If you need us to look up a UPC for any item, request it here:")

    # Initialize list if not present
    if "requested_upcs" not in st.session_state:
        st.session_state.requested_upcs = []

    new_request = st.text_input(
        "Enter item name or description",
        key="upc_request_input"
    )

    if st.button("Submit UPC Request"):
        if new_request.strip():
            st.session_state.requested_upcs.append(new_request.strip())
            st.success("UPC request submitted!")
        else:
            st.warning("Please enter a valid item name or description.")

    # Show requested UPCs
    if st.session_state.requested_upcs:
        st.markdown("### Requested UPCs")
        for r in st.session_state.requested_upcs:
            st.markdown(f"- {r}")