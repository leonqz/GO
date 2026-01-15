

import streamlit as st
import pandas as pd
import re
import csv

# --- helpers -------------------------------------------------------------- #
def price_to_float(price_str):
    if pd.isna(price_str):
        return None
    cleaned = re.sub(r"[^0-9.\-]", "", str(price_str))
    return float(cleaned) if cleaned else None

def safe_url(u):
    if not isinstance(u, str):
        return None
    u = u.strip()
    return u if u.startswith(("http://", "https://")) else None

@st.cache_data
def load_offers():
    offers = pd.read_csv("go_demodata_spokane.csv")
    offers.columns = [c.strip() for c in offers.columns]

    # Numeric prices
    offers["OurPrice_num"] = offers["Our Price"].apply(price_to_float)
    offers["WalmartPrice_num"] = offers["Walmart Price"].apply(price_to_float)
    offers["SafewayPrice_num"] = offers["Safeway Price"].apply(price_to_float)

    # Choose comparison priority: Walmart first, else Safeway
    offers["Compare Store"] = None
    offers["ComparePrice_num"] = None
    offers["Compare Link"] = None
    offers["Compare Image"] = None

    walmart_mask = offers["WalmartPrice_num"].notna()
    safeway_mask = offers["WalmartPrice_num"].isna() & offers["SafewayPrice_num"].notna()

    offers.loc[walmart_mask, "Compare Store"] = "Walmart"
    offers.loc[walmart_mask, "ComparePrice_num"] = offers.loc[walmart_mask, "WalmartPrice_num"]
    offers.loc[walmart_mask, "Compare Link"] = offers.loc[walmart_mask, "Walmart Link"]
    offers.loc[walmart_mask, "Compare Image"] = offers.loc[walmart_mask, "Walmart Image"]

    offers.loc[safeway_mask, "Compare Store"] = "Safeway"
    offers.loc[safeway_mask, "ComparePrice_num"] = offers.loc[safeway_mask, "SafewayPrice_num"]
    offers.loc[safeway_mask, "Compare Link"] = offers.loc[safeway_mask, "Safeway Link"]
    offers.loc[safeway_mask, "Compare Image"] = offers.loc[safeway_mask, "Safeway Image"]

    # Savings vs chosen comparison store
    offers["Savings_num"] = offers["ComparePrice_num"] - offers["OurPrice_num"]
    offers["Savings_pct"] = (offers["Savings_num"] / offers["ComparePrice_num"]) * 100

    # Clean URLs + text
    offers["Compare Link"] = offers["Compare Link"].apply(safe_url)
    offers["Inexact Match"] = offers["Inexact Match"].fillna("").astype(str)

    # Keep only rows with something to compare against
    offers = offers.dropna(subset=["ComparePrice_num"])

    # Sort best deals first
    offers = offers.sort_values(["Savings_pct", "Savings_num"], ascending=False)

    return offers

# ------------------------------------------------------------------------- #
# Put this where you want the tabs to start (replacing your existing single-page layout)

st.set_page_config(
    page_title="Basket Price Comparator",
    layout="wide",
)
st.image("spokane.jpeg", width = 400)

st.title("Spokane Basket Comparison")
st.markdown("_Updated January 12, 2025_")

tab2, tab1 = st.tabs(["🔥 Offers", "🧺 Basket Comparator"])


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




with tab2:
    st.markdown("""
    <style>
    .offer-row{
        display:grid;
        grid-template-columns: 260px 1fr 220px;
        gap: 18px;
        align-items: stretch;
        margin-bottom: 16px;
    }

    .offer-card{
    border-radius: 22px;
    padding: 18px;
    background: rgba(20,20,20,0.92);   /* dark card */
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 8px 22px rgba(0,0,0,0.6);
    color: #ffffff;
    }
                
    .offer-img{
    display:flex;
    align-items:center;
    justify-content:center;
    height: 220px;
    border-radius: 16px;
    background: rgba(255,255,255,0.06);
    overflow:hidden;
    }

    .offer-img img{
        width: 100%;
        height: 100%;
        object-fit: contain;
        padding: 10px;
    }

    .badge{
        display:inline-block;
        padding:6px 10px;
        border-radius:999px;
        font-weight:800;
        background:#00c853;
        color:#0b1a12;
        border:1px solid rgba(0,0,0,0.08);
        font-size:13px;
        margin-bottom: 10px;
    }

    .title{
        font-weight: 850;
        font-size: 18px;
        margin-bottom: 10px;
    }

    .price-big{
        font-size: 36px;
        font-weight: 900;
        letter-spacing: -0.5px;
        margin-top: 6px;
    }
    .muted{ opacity:0.75; }
    .small{ font-size:14px; opacity:0.80; }

    .btn{
        display:block;
        width:100%;
        text-align:center;
        padding: 12px 14px;
        border-radius: 12px;
        background: rgba(0,0,0,0.12);
        border: 1px solid rgba(0,0,0,0.12);
        text-decoration:none;
        font-weight: 800;
        margin-top: 12px;
    }
    </style>
    """, unsafe_allow_html=True)


    st.markdown("""
    <style>
    /* App background */
    .stApp {
        background-color: #000000;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        """
        <div class="offer-hero">
          <h1>🔥 This Week’s BEST Deals</h1>
          <p>Same brands you already buy — priced to beat Walmart.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    offers = load_offers()

    # Top summary stats
    valid = offers.dropna(subset=["OurPrice_num", "WalmartPrice_num"])
    if not valid.empty:
        avg_pct = valid["Savings_pct"].median()
        avg_dol = valid["Savings_num"].median()
        c1, c2, c3 = st.columns(3)
        c1.metric("Median % off Walmart", f"{avg_pct:.0f}%")
        c2.metric("Median $ savings", f"${avg_dol:.2f}")
        c3.metric("Offers this week", f"{len(offers)}")

    st.markdown("---")
    show_df = offers.copy()


    # Render cards (flashy flyer style)
    for _, row in show_df.iterrows():
        item = row.get("Item", "")
        img = row.get("Walmart Image", "")
        link = row.get("Walmart Link", None)

        our_p = row.get("OurPrice_num", None)
        wmt_p = row.get("WalmartPrice_num", None)
        sav = row.get("Savings_num", None)
        savp = row.get("Savings_pct", None)

        badge_text = ""
        if pd.notna(savp) and savp > 0:
            badge_text = f"SAVE {savp:.0f}%"
        elif pd.notna(sav) and sav > 0:
            badge_text = f"SAVE ${sav:.2f}"
        else:
            badge_text = "LOW PRICE"

        # Layout: image | info | CTA
        compare_store = row.get("Compare Store", "")
        compare_price = row.get("ComparePrice_num", None)
        compare_link = row.get("Compare Link", None)
        inexact_note = str(row.get("Inexact Match", "") or "").strip()

        img_url = img if isinstance(img, str) else ""
        link_url = compare_link if isinstance(compare_link, str) else ""

        # safe fallbacks for display
        our_price_txt = f"${our_p:.2f}" if pd.notna(our_p) else "$—"
        compare_price_txt = f"${compare_price:.2f}" if pd.notna(compare_price) else "$—"
        sav_txt = f"${sav:.2f}" if pd.notna(sav) else "$—"

        note_html = f"<div class='small muted' style='margin-top:8px;'>* {inexact_note}</div>" if inexact_note else ""

        # make the image clickable if link exists
        img_html = f"<img src='{img_url}' />"
        if link_url.strip():
            img_html = f"<a href='{link_url}' target='_blank' style='display:block; width:100%; height:100%;'>{img_html}</a>"

        btn_html = ""
        if link_url.strip():
            btn_html = f"<a class='btn' href='{link_url}' target='_blank'>View at {compare_store}</a>"
        else:
            btn_html = "<div class='small muted' style='margin-top:12px;'>No link available</div>"

        st.markdown(
            f"""
            <div class="offer-row">
            <div class="offer-card">
                <div class="offer-img">{img_html}</div>
            </div>

            <div class="offer-card">
                <div class="badge">{badge_text} vs {compare_store}</div>
                <div class="title">{item}</div>
                <div class="price-big">{our_price_txt} <span class="small muted">Our Price</span></div>
                <div class="small muted">{compare_store}: {compare_price_txt} • You save {sav_txt}</div>
                {note_html}
            </div>

            <div class="offer-card">
                <div style="font-size:22px; font-weight:900;">🔗 Link</div>
                <div class="small muted" style="margin-top:6px;">Open the comparison</div>
                {btn_html}
            </div>
            </div>
            """,
            unsafe_allow_html=True,
    )


with tab1:


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

                walmart_img = row.get("Walmart Image")
                walmart_link = row.get("Walmart link")
                safeway_link = row.get("Safeway link")

                # ---- ONE product image (clickable Walmart link if available) ----
                if isinstance(walmart_img, str) and walmart_img.strip():
                    if isinstance(walmart_link, str) and walmart_link.strip():
                        st.markdown(
                            f"<a href='{walmart_link}' target='_blank'>"
                            f"<img src='{walmart_img}' width='70'></a>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.image(walmart_img, width=70)

                # Item name
                st.caption(name)

                # Prices
                w_price = float(row["Walmart_price"]) if pd.notna(row["Walmart_price"]) else 0.0
                s_price = float(row["Safeway_price"]) if pd.notna(row["Safeway_price"]) else 0.0

                # ---- Walmart + Safeway: one logo column each, clickable price ----
                price_col1, price_col2, price_col3 = st.columns([1, 1, 1])

                # Walmart
                with price_col1:
                    st.image(wmt_logo, width=22)
                    if walmart_link and isinstance(walmart_link, str) and walmart_link.strip():
                        st.markdown(
                            f"<a href='{walmart_link}' target='_blank' "
                            f"style='text-decoration:none; color:inherit;'>"
                            f"${w_price:.2f}</a>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.write(f"${w_price:.2f}")

                # Safeway
                with price_col2:
                    st.image(safeway_logo, width=22)
                    if safeway_link and isinstance(safeway_link, str) and safeway_link.strip():
                        st.markdown(
                            f"<a href='{safeway_link}' target='_blank' "
                            f"style='text-decoration:none; color:inherit;'>"
                            f"${s_price:.2f}</a>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.write(f"${s_price:.2f}")

                # ---- Your Store price input ----
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

                # ---- Quantity input ----
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

                st.dataframe(table_df, width='stretch')
            else:
                st.write("Your basket is empty.")

  