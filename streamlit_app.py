import streamlit as st
import pandas as pd

# ------------------ Page setup ------------------
st.set_page_config(
    page_title="Thanksgiving Basket Compare",
    page_icon="🦃",
    layout="wide"
)

st.title("🦃 Thanksgiving Basket Compare")
st.caption("Build a basket and see how the total price compares across three stores.")

# ------------------ Session state ------------------
if "basket" not in st.session_state:
    # basket is: {row_index: quantity}
    st.session_state.basket = {}

if "last_added" not in st.session_state:
    st.session_state.last_added = None

# ------------------ Styling ------------------
st.markdown(
    """
    <style>
    .catalog-card {
        border-radius: 1rem;
        padding: 0.75rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        background: #ffffff;
    }
    .catalog-title {
        font-weight: 600;
        font-size: 1rem;
        margin-bottom: 0.25rem;
    }
    .catalog-price {
        font-size: 0.9rem;
        opacity: 0.85;
        margin-bottom: 0.5rem;
    }
    .basket-container {
        border-radius: 1rem;
        padding: 0.9rem;
        background: #fffaf2;
        border: 1px solid #f3d2a2;
    }
    .basket-header {
        font-weight: 700;
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
    }
    .basket-summary {
        font-size: 0.95rem;
        margin-bottom: 0.75rem;
    }
    .totals-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 0.5rem;
        margin-bottom: 0.75rem;
    }
    .totals-table td {
        padding: 4px 2px;
        font-size: 0.92rem;
    }
    .totals-label {
        font-weight: 600;
    }
    .totals-highlight {
        font-weight: 700;
        font-size: 1rem;
    }
    .basket-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 0.25rem;
        margin-top: 0.5rem;
    }
    .basket-image {
        width: 70px;
        height: 70px;
        object-fit: cover;
        border-radius: 0.75rem;
        box-shadow: 0 1px 5px rgba(0,0,0,0.12);
        border: 2px solid #f3d2a2;
    }
    .basket-image.float-in {
        animation: float-in 0.4s ease-out;
    }
    @keyframes float-in {
        0% { transform: translateY(-14px); opacity: 0; }
        100% { transform: translateY(0); opacity: 1; }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------ Sidebar ------------------
st.sidebar.header("📄 Data & Settings")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

store1_name = st.sidebar.text_input("Your store name", "Our Store")
store2_name = st.sidebar.text_input("Competitor 1 name", "Store A")
store3_name = st.sidebar.text_input("Competitor 2 name", "Store B")

# ------------------ Load data ------------------
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
else:
    # Demo data for structure
    df = pd.DataFrame(
        [
            {
                "item": "Turkey (12 lb)",
                "our_price": 29.99,
                "comp1_price": 32.99,
                "comp2_price": 27.49,
                "image_url": "https://images.pexels.com/photos/5718025/pexels-photo-5718025.jpeg"
            },
            {
                "item": "Pumpkin Pie",
                "our_price": 8.49,
                "comp1_price": 7.99,
                "comp2_price": 9.29,
                "image_url": "https://images.pexels.com/photos/4110004/pexels-photo-4110004.jpeg"
            },
            {
                "item": "Cranberry Sauce",
                "our_price": 3.99,
                "comp1_price": 3.49,
                "comp2_price": 4.19,
                "image_url": "https://images.pexels.com/photos/7157046/pexels-photo-7157046.jpeg"
            },
        ]
    )
    st.sidebar.info("Using demo data until you upload your own CSV.")

required_cols = {"item", "our_price", "comp1_price", "comp2_price", "image_url"}
missing = required_cols - set(df.columns)
if missing:
    st.error(f"Your CSV is missing columns: {', '.join(missing)}")
    st.stop()

# Cast prices numeric
for col in ["our_price", "comp1_price", "comp2_price"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df = df.dropna(subset=["our_price", "comp1_price", "comp2_price"])

# ------------------ Layout ------------------
left_col, right_col = st.columns([3, 2])

# -------- Catalog (left) --------
with left_col:
    st.subheader("🛒 Build Your Thanksgiving Basket")

    for idx, row in df.iterrows():
        with st.container():
            st.markdown('<div class="catalog-card">', unsafe_allow_html=True)

            c1, c2 = st.columns([1, 2])
            with c1:
                st.image(row["image_url"], width=True)

            with c2:
                st.markdown(
                    f'<div class="catalog-title">{row["item"]}</div>',
                    unsafe_allow_html=True
                )
                st.markdown(
                    f'<div class="catalog-price">{store1_name}: <b>${row["our_price"]:.2f}</b></div>',
                    unsafe_allow_html=True
                )

                add_key = f"add_{idx}"
                if st.button("Add to basket (at our price)", key=add_key, use_container_width=True):
                    basket = st.session_state.basket
                    basket[idx] = basket.get(idx, 0) + 1
                    st.session_state.basket = basket
                    st.session_state.last_added = idx
                    st.toast(f"Added {row['item']} to your basket 🧺")

            st.markdown("</div>", unsafe_allow_html=True)

# -------- Basket & totals (right) --------
with right_col:
    st.subheader("📊 Basket Price Comparison")

    # Compute totals across stores
    total_items = 0
    total_ours = 0.0
    total_c1 = 0.0
    total_c2 = 0.0

    for idx, qty in st.session_state.basket.items():
        if idx in df.index:
            r = df.loc[idx]
            total_items += qty
            total_ours += r["our_price"] * qty
            total_c1 += r["comp1_price"] * qty
            total_c2 += r["comp2_price"] * qty

    with st.container():
        st.markdown('<div class="basket-container">', unsafe_allow_html=True)
        st.markdown('<div class="basket-header">Current Basket</div>', unsafe_allow_html=True)

        if total_items == 0:
            st.markdown(
                '<div class="basket-summary">No items yet — add some from the left to compare full basket prices. 🥧</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="basket-summary">Items in basket: <b>{total_items}</b></div>',
                unsafe_allow_html=True
            )

            # Helper for diff text vs our basket
            def diff_text(label, value, base_value):
                if base_value == 0:
                    return ""
                diff = value - base_value
                pct = (diff / base_value) * 100 if base_value != 0 else 0
                if abs(diff) < 0.01:
                    return "same as our basket"
                sign = "+" if diff > 0 else "-"
                return f"{sign}${abs(diff):.2f} ({sign}{abs(pct):.0f}% vs our basket)"

            # Hero-style totals
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"**{store1_name}**")
                st.markdown(f"<div class='totals-highlight'>$ {total_ours:.2f}</div>", unsafe_allow_html=True)
                st.caption("Reference basket")

            with c2:
                st.markdown(f"**{store2_name}**")
                st.markdown(f"<div class='totals-highlight'>$ {total_c1:.2f}</div>", unsafe_allow_html=True)
                st.caption(diff_text(store2_name, total_c1, total_ours))

            with c3:
                st.markdown(f"**{store3_name}**")
                st.markdown(f"<div class='totals-highlight'>$ {total_c2:.2f}</div>", unsafe_allow_html=True)
                st.caption(diff_text(store3_name, total_c2, total_ours))

            # Simple table for clarity
            totals_html = (
                "<table class='totals-table'>"
                f"<tr><td class='totals-label'>{store1_name}</td><td>$ {total_ours:.2f}</td><td>reference</td></tr>"
                f"<tr><td class='totals-label'>{store2_name}</td><td>$ {total_c1:.2f}</td>"
                f"<td>{diff_text(store2_name, total_c1, total_ours)}</td></tr>"
                f"<tr><td class='totals-label'>{store3_name}</td><td>$ {total_c2:.2f}</td>"
                f"<td>{diff_text(store3_name, total_c2, total_ours)}</td></tr>"
                "</table>"
            )
            st.markdown(totals_html, unsafe_allow_html=True)

            # Basket images to keep the vibe
            basket_html = '<div class="basket-grid">'
            last = st.session_state.last_added

            for idx, qty in st.session_state.basket.items():
                if idx not in df.index:
                    continue
                row = df.loc[idx]
                for i in range(qty):
                    extra_class = " float-in" if idx == last and i == qty - 1 else ""
                    basket_html += (
                        f'<img src="{row["image_url"]}" '
                        f'alt="{row["item"]}" '
                        f'class="basket-image{extra_class}"/>'
                    )
            basket_html += "</div>"
            st.markdown(basket_html, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    if total_items > 0:
        if st.button("Clear basket 🧹", type="secondary"):
            st.session_state.basket = {}
            st.session_state.last_added = None
            st.experimental_rerun()
