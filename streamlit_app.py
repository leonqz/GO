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
    # Replace with your actual file path
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
df["Safeway_price"] = df["Safeway"].astype(str).apply(price_to_float)

# Initialize session state for quantities if not present
if "quantities" not in st.session_state:
    st.session_state.quantities = {name: 0 for name in df["Name"]}

# --- Layout: left = item grid, right = basket comparison ------------------- #
left_col, right_col = st.columns([3, 2])

# ===================== LEFT: ITEM GRID ===================================== #
with left_col:
    st.subheader("Items – Add to Basket")

    n_cols = 2  # grid: 2 product cards per row

    for i in range(0, len(df), n_cols):
        row_df = df.iloc[i : i + n_cols]
        cols = st.columns(n_cols)

        for col, (_, row) in zip(cols, row_df.iterrows()):
            with col:
                name = row["Name"]

                # --- Walmart image (small) ---
                walmart_img = row.get("Walmart Image")
                if pd.notna(walmart_img) and str(walmart_img).strip():
                    st.image(str(walmart_img), width=80, caption="Walmart")

                # --- Safeway image (small) ---
                safeway_img = row.get("Safeway Image")
                if pd.notna(safeway_img) and str(safeway_img).strip():
                    st.image(str(safeway_img), width=80, caption="Safeway")

                st.markdown(f"**{name}**")

                # Prices
                if pd.notna(row["Walmart_price"]):
                    st.write(f"Walmart: **${row['Walmart_price']:.2f}**")
                if pd.notna(row["Safeway_price"]):
                    st.write(f"Safeway: **${row['Safeway_price']:.2f}**")

                # Links
                walmart_link = row.get("Walmart link")
                safeway_link = row.get("Safeway link")
                links_parts = []
                if isinstance(walmart_link, str) and walmart_link.strip():
                    links_parts.append(f"[Walmart link]({walmart_link})")
                if isinstance(safeway_link, str) and safeway_link.strip():
                    links_parts.append(f"[Safeway link]({safeway_link})")
                if links_parts:
                    st.markdown(" · ".join(links_parts))

                # Quantity control (adds to basket)
                qty_key = f"qty_{name}"
                current_qty = st.session_state.quantities.get(name, 0)

                new_qty = st.number_input(
                    "Qty",
                    min_value=0,
                    step=1,
                    value=int(current_qty),
                    key=qty_key,
                )
                st.session_state.quantities[name] = new_qty

# Build basket from quantities
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
    # create empty columns so right side code doesn't crash
    basket_df["Walmart_line_total"] = 0.0
    basket_df["Safeway_line_total"] = 0.0

# ===================== RIGHT: BASKET COMPARISON ============================ #
with right_col:
    st.subheader("Basket Comparison")

    # Competitor setup
    competitor_name = st.text_input("Competitor name", value="My Competitor")
    st.caption("Enter competitor prices for items in your basket (if any).")

    # competitor prices only for items in basket
    comp_prices = {}
    comp_upcs = {}

    if not basket_df.empty:
        for _, row in basket_df.iterrows():
            name = row["Name"]
            p_key = f"comp_price_{name}"
            u_key = f"comp_upc_{name}"

            comp_price = st.number_input(
                f"{competitor_name} price – {name}",
                min_value=0.0,
                step=0.01,
                value=0.0,
                key=p_key,
            )
            comp_upc = st.text_input(
                f"UPC for {name} (optional)",
                key=u_key,
            )

            comp_prices[name] = comp_price
            comp_upcs[name] = comp_upc

        basket_df["Competitor_price"] = basket_df["Name"].map(comp_prices)
        basket_df["Competitor_line_total"] = (
            basket_df["Competitor_price"] * basket_df["Quantity"]
        )
    else:
        basket_df["Competitor_price"] = 0.0
        basket_df["Competitor_line_total"] = 0.0

    # Totals
    walmart_total = float(basket_df["Walmart_line_total"].sum())
    safeway_total = float(basket_df["Safeway_line_total"].sum())
    comp_valid = basket_df["Competitor_price"] > 0
    competitor_total = float(basket_df.loc[comp_valid, "Competitor_line_total"].sum())

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

    if competitor_total > 0:
        comp_delta = competitor_total - walmart_total
        comp_delta_label = (
            f"+${abs(comp_delta):,.2f} vs Walmart"
            if comp_delta >= 0
            else f"-${abs(comp_delta):,.2f} vs Walmart"
        )
        m3.metric(
            f"{competitor_name} basket",
            f"${competitor_total:,.2f}",
            comp_delta_label,
        )
    else:
        m3.metric(f"{competitor_name} basket", "—", "Enter prices")

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
            "Competitor_price",
            "Competitor_line_total",
        ]
        pretty_basket = basket_df[display_cols].rename(
            columns={
                "Walmart_price": "Walmart price",
                "Walmart_line_total": "Walmart total",
                "Safeway_price": "Safeway price",
                "Safeway_line_total": "Safeway total",
                "Competitor_price": f"{competitor_name} price",
                "Competitor_line_total": f"{competitor_name} total",
            }
        )
        st.dataframe(pretty_basket, use_container_width=True)
    else:
        st.info("No items in your basket yet – add quantities on the left.")
