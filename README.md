import streamlit as st
import pandas as pd

# ------------------ Page setup ------------------
st.set_page_config(
    page_title="Thanksgiving Basket",
    page_icon="🦃",
    layout="wide"
)

st.title("🦃 Thanksgiving Basket Builder")
st.caption("Pick your Thanksgiving items, watch your basket (and total) fill up.")

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
        opacity: 0.8;
        margin-bottom: 0.5rem;
    }
    .basket-container {
        border-radius: 1rem;
        padding: 0.75rem;
        background: #fffaf2;
        border: 1px solid #f3d2a2;
    }
    .basket-header {
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }
    .basket-summary {
        font-size: 0.95rem;
        margin-bottom: 0.75rem;
    }
    .basket-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 0.25rem;
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

# ------------------ Load data ------------------
st.sidebar.header("📄 Data")
st.sidebar.write("Upload a CSV with `item`, `price`, `image_url` columns.")

uploaded_file = st.sidebar.file_uploader("Upload Thanksgiving items CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
else:
    # Tiny fallback example (replace/remove once you have your CSV)
    df = pd.DataFrame(
        [
            {
                "item": "Turkey (12 lb)",
                "price": 29.99,
                "image_url": "https://images.pexels.com/photos/5718025/pexels-photo-5718025.jpeg"
            },
            {
                "item": "Pumpkin Pie",
                "price": 8.49,
                "image_url": "https://images.pexels.com/photos/4110004/pexels-photo-4110004.jpeg"
            },
            {
                "item": "Cranberry Sauce",
                "price": 3.99,
                "image_url": "https://images.pexels.com/photos/7157046/pexels-photo-7157046.jpeg"
            },
        ]
    )
    st.sidebar.info("Using demo data until you upload your own CSV.")

# Basic sanity check
required_cols = {"item", "price", "image_url"}
missing = required_cols - set(df.columns)
if missing:
    st.error(f"Your CSV is missing columns: {', '.join(missing)}")
    st.stop()

# Ensure price is numeric
df["price"] = pd.to_numeric(df["price"], errors="coerce")
df = df.dropna(subset=["price"])

# ------------------ Layout ------------------
left_col, right_col = st.columns([3, 2])

# -------- Catalog (left) --------
with left_col:
    st.subheader("🛒 Thanksgiving Items")

    for idx, row in df.iterrows():
        with st.container():
            st.markdown('<div class="catalog-card">', unsafe_allow_html=True)

            c1, c2 = st.columns([1, 2])
            with c1:
                st.image(row["image_url"], use_column_width=True)

            with c2:
                st.markdown(f'<div class="catalog-title">{row["item"]}</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="catalog-price">${row["price"]:.2f}</div>',
                    unsafe_allow_html=True
                )

                add_key = f"add_{idx}"
                if st.button("Add to basket", key=add_key, use_container_width=True):
                    basket = st.session_state.basket
                    basket[idx] = basket.get(idx, 0) + 1
                    st.session_state.basket = basket
                    st.session_state.last_added = idx
                    st.toast(f"Added {row['item']} to your basket 🧺")

            st.markdown("</div>", unsafe_allow_html=True)

# -------- Basket (right) --------
with right_col:
    st.subheader("🧺 Your Basket")

    # Compute totals
    total_price = 0.0
    total_items = 0

    for idx, qty in st.session_state.basket.items():
        if idx in df.index:
            price = df.loc[idx, "price"]
            total_price += price * qty
            total_items += qty

    with st.container():
        st.markdown('<div class="basket-container">', unsafe_allow_html=True)

        st.markdown('<div class="basket-header">Current Basket</div>', unsafe_allow_html=True)

        st.markdown(
            f'<div class="basket-summary">Items: <b>{total_items}</b> &nbsp;·&nbsp; '
            f'Total: <b>${total_price:.2f}</b></div>',
            unsafe_allow_html=True
        )

        if total_items == 0:
            st.write("Nothing in your basket yet — start adding some Thanksgiving goodness! 🥧")
        else:
            # Render images of all items in the basket
            basket_html = '<div class="basket-grid">'
            last = st.session_state.last_added

            for idx, qty in st.session_state.basket.items():
                if idx not in df.index:
                    continue
                row = df.loc[idx]
                for i in range(qty):
                    # Highlight the most recently added item with animation
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
