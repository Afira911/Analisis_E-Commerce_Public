import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="E-Commerce Analytics Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── STYLING ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem; font-weight: 800;
        background: linear-gradient(90deg, #1565C0, #42A5F5);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .metric-card {
        background: #f0f4ff; border-radius: 12px; padding: 1rem 1.2rem;
        border-left: 4px solid #1565C0;
    }
    .section-header {
        font-size: 1.3rem; font-weight: 700; color: #1565C0;
        border-bottom: 2px solid #90CAF9; padding-bottom: 0.3rem;
        margin-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ── LOAD DATA ────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    main = pd.read_csv("dashboard/main_data.csv", parse_dates=["order_purchase_timestamp"])
    rfm  = pd.read_csv("dashboard/rfm_data.csv")
    return main, rfm

main_data, rfm_data = load_data()

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/4/4a/Olist_logo.svg", width=160)
    st.title("🔧 Filter Data")

    # Date range
    min_date = main_data["order_purchase_timestamp"].min().date()
    max_date = main_data["order_purchase_timestamp"].max().date()

    date_range = st.date_input(
        "Rentang Tanggal Pembelian",
        value=(pd.to_datetime("2017-01-01").date(), max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Category filter
    all_cats = sorted(main_data["product_category_name_english"].unique())
    selected_cats = st.multiselect(
        "Kategori Produk",
        options=all_cats,
        default=[]
    )

    # State filter
    all_states = sorted(main_data["customer_state"].dropna().unique())
    selected_states = st.multiselect(
        "Negara Bagian Pelanggan",
        options=all_states,
        default=[]
    )

    st.markdown("---")
    st.caption("📊 Data: Olist E-Commerce Public Dataset\n\n👩‍💻 Annisa Fathia Rahmah")

# ── FILTER ───────────────────────────────────────────────────────────────────
df = main_data.copy()
if len(date_range) == 2:
    df = df[(df["order_purchase_timestamp"].dt.date >= date_range[0]) &
            (df["order_purchase_timestamp"].dt.date <= date_range[1])]
if selected_cats:
    df = df[df["product_category_name_english"].isin(selected_cats)]
if selected_states:
    df = df[df["customer_state"].isin(selected_states)]

df_clean = df.dropna(subset=["review_score", "delivery_status"])

# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown('<p class="main-title">🛒 E-Commerce Analytics Dashboard</p>', unsafe_allow_html=True)
st.markdown("**Brazilian E-Commerce Public Dataset by Olist** | Analisis transaksi 2016–2018")

# ── METRICS ──────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
total_orders   = df["order_id"].nunique()
total_revenue  = df["revenue"].sum()
avg_review     = df_clean["review_score"].mean()
late_pct       = (df_clean["delivery_status"] == "Late").mean() * 100

col1.metric("📦 Total Orders",    f"{total_orders:,}")
col2.metric("💰 Total Revenue",   f"R$ {total_revenue/1e6:.2f}M")
col3.metric("⭐ Avg Review Score", f"{avg_review:.2f} / 5.00")
col4.metric("🚚 Late Delivery %", f"{late_pct:.1f}%")

st.markdown("---")

# ── TAB LAYOUT ───────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📦 Revenue Analysis", "⭐ Delivery & Reviews", "👥 RFM Segmentation"])

# ═══════════════════════════════════════════════════════════════════════
# TAB 1: Revenue Analysis
# ═══════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<p class="section-header">Pertanyaan 1: Kategori Produk dengan Revenue Tertinggi</p>',
                unsafe_allow_html=True)

    n_top = st.slider("Tampilkan Top-N Kategori", 5, 20, 10, key="slider_top")

    rev_cat = (df.groupby("product_category_name_english")["revenue"]
               .sum().nlargest(n_top).sort_values().reset_index())
    rev_cat.columns = ["category", "total_revenue"]

    col_a, col_b = st.columns([1, 1])

    with col_a:
        fig, ax = plt.subplots(figsize=(7, max(4, n_top * 0.45)))
        bar_colors = ["#1565C0" if i == len(rev_cat)-1 else "#90CAF9"
                      for i in range(len(rev_cat))]
        bars = ax.barh(rev_cat["category"], rev_cat["total_revenue"]/1e6, color=bar_colors)
        for bar in bars:
            ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
                    f"R$ {bar.get_width():.1f}M", va="center", fontsize=7.5)
        ax.set_xlabel("Total Revenue (Million BRL)")
        ax.set_title(f"Top {n_top} Product Categories by Revenue")
        ax.set_xlim(0, rev_cat["total_revenue"].max()/1e6 * 1.2)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig)

    with col_b:
        st.markdown("**📊 Revenue per Kategori (Tabel)**")
        rev_display = rev_cat.sort_values("total_revenue", ascending=False).copy()
        rev_display["total_revenue"] = rev_display["total_revenue"].apply(lambda x: f"R$ {x:,.2f}")
        rev_display.columns = ["Kategori", "Total Revenue"]
        st.dataframe(rev_display, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("**📈 Tren Revenue Bulanan – Top 5 Kategori**")

    top5_list = (df.groupby("product_category_name_english")["revenue"]
                 .sum().nlargest(5).index.tolist())
    df5 = df[df["product_category_name_english"].isin(top5_list)].copy()
    df5["ym"] = df5["order_purchase_timestamp"].dt.to_period("M").dt.to_timestamp()
    trend5 = (df5.groupby(["ym","product_category_name_english"])["revenue"]
              .sum().reset_index())

    fig2, ax2 = plt.subplots(figsize=(12, 4.5))
    line_colors = ["#1565C0","#E53935","#43A047","#FB8C00","#8E24AA"]
    for i, cat in enumerate(top5_list):
        sub = trend5[trend5["product_category_name_english"] == cat]
        ax2.plot(sub["ym"], sub["revenue"]/1e3, marker="o", markersize=4,
                 label=cat.replace("_"," ").title(), color=line_colors[i], linewidth=2)
    ax2.set_ylabel("Revenue (Thousand BRL)")
    ax2.set_title("Monthly Revenue Trend – Top 5 Categories")
    ax2.legend(fontsize=9)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig2)

    with st.expander("💡 Insight"):
        st.markdown("""
- **`health_beauty`** secara konsisten menjadi kategori dengan revenue tertinggi.
- Terdapat **lonjakan tajam pada November 2017** (Black Friday) di hampir semua kategori.
- **`computers_accessories`** menunjukkan tren pertumbuhan paling konsisten sepanjang 2018.
- **Rekomendasi**: Tingkatkan stok & promosi untuk Top 5 kategori, khususnya mulai Oktober.
        """)

# ═══════════════════════════════════════════════════════════════════════
# TAB 2: Delivery & Reviews
# ═══════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<p class="section-header">Pertanyaan 2: Dampak Keterlambatan Pengiriman terhadap Kepuasan Pelanggan</p>',
                unsafe_allow_html=True)

    if df_clean.empty:
        st.warning("Tidak ada data review untuk filter yang dipilih.")
    else:
        palette_map = {"On-time": "#43A047", "Late": "#E53935"}
        order_stat  = ["On-time", "Late"]

        # Metric cards
        col_m1, col_m2, col_m3 = st.columns(3)
        ontime_score = df_clean[df_clean["delivery_status"]=="On-time"]["review_score"].mean()
        late_score   = df_clean[df_clean["delivery_status"]=="Late"]["review_score"].mean()
        late_count   = (df_clean["delivery_status"]=="Late").sum()

        col_m1.metric("✅ Avg Score (On-time)", f"{ontime_score:.2f}")
        col_m2.metric("❌ Avg Score (Late)",    f"{late_score:.2f}",
                      delta=f"{late_score - ontime_score:.2f}")
        col_m3.metric("🚚 Late Orders",         f"{late_count:,}")

        col_c, col_d = st.columns(2)

        with col_c:
            fig, ax = plt.subplots(figsize=(6.5, 5))
            width = 0.38
            for i, status in enumerate(order_stat):
                sub = df_clean[df_clean["delivery_status"]==status]
                pct = sub["review_score"].value_counts(normalize=True).sort_index() * 100
                ax.bar(pct.index + (i-0.5)*width, pct.values, width=width,
                       label=status, color=palette_map[status], alpha=0.88, edgecolor="white")
            ax.set_xlabel("Review Score")
            ax.set_ylabel("Percentage (%)")
            ax.set_title("Review Score Distribution by Delivery Status")
            ax.set_xticks([1,2,3,4,5])
            ax.legend(title="Delivery Status")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig)

        with col_d:
            fig2, ax2 = plt.subplots(figsize=(6.5, 5))
            sns.boxplot(data=df_clean, x="delivery_status", y="review_score",
                        order=order_stat, palette=palette_map, ax=ax2,
                        width=0.5, linewidth=1.5, fliersize=2)
            avg_sc = df_clean.groupby("delivery_status")["review_score"].mean()
            for i, status in enumerate(order_stat):
                ax2.text(i, avg_sc[status]+0.12, f"μ = {avg_sc[status]:.2f}",
                         ha="center", fontsize=11, fontweight="bold")
            ax2.set_xlabel("Delivery Status")
            ax2.set_ylabel("Review Score")
            ax2.set_title("Review Score Boxplot by Delivery Status")
            ax2.spines["top"].set_visible(False)
            ax2.spines["right"].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig2)

        # Delay distribution
        st.markdown("**📊 Distribusi Keterlambatan (hari) — Pesanan Late**")
        late_df = df_clean[df_clean["delivery_status"]=="Late"]
        if not late_df.empty:
            fig3, ax3 = plt.subplots(figsize=(10, 3.5))
            ax3.hist(late_df["delivery_delay"].clip(upper=60), bins=40,
                     color="#E53935", edgecolor="white", alpha=0.85)
            ax3.axvline(late_df["delivery_delay"].median(), color="#1565C0",
                        linestyle="--", linewidth=2,
                        label=f'Median: {late_df["delivery_delay"].median():.0f} hari')
            ax3.set_xlabel("Delivery Delay (days)")
            ax3.set_ylabel("Number of Orders")
            ax3.set_title("Distribution of Late Delivery Delays (capped at 60 days)")
            ax3.legend()
            ax3.spines["top"].set_visible(False)
            ax3.spines["right"].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig3)

        with st.expander("💡 Insight"):
            st.markdown(f"""
- Pesanan **Late** memiliki mean review score **{late_score:.2f}** vs **On-time {ontime_score:.2f}** — selisih hampir 2 poin.
- Lebih dari **55% pesanan terlambat** mendapatkan skor 1 (sangat tidak puas).
- Median keterlambatan sekitar **10 hari** — sangat berpengaruh pada pengalaman pelanggan.
- **Rekomendasi**: Tetapkan target on-time delivery ≥95%, dan berikan kompensasi otomatis untuk pesanan terlambat.
            """)

# ═══════════════════════════════════════════════════════════════════════
# TAB 3: RFM Segmentation
# ═══════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<p class="section-header">Analisis Lanjutan: RFM Customer Segmentation</p>',
                unsafe_allow_html=True)
    st.markdown("""
    **RFM Analysis** mengelompokkan pelanggan berdasarkan:
    - **Recency (R)**: Berapa hari sejak transaksi terakhir
    - **Frequency (F)**: Berapa kali melakukan pembelian
    - **Monetary (M)**: Total nilai pembayaran
    """)

    seg_order  = ["Champions","Loyal Customers","Potential Loyalist","At Risk","Lost"]
    seg_colors = ["#1565C0","#1E88E5","#64B5F6","#EF5350","#B71C1C"]
    seg_count  = rfm_data["segment"].value_counts().reindex(seg_order)

    col_e, col_f = st.columns(2)

    with col_e:
        fig, ax = plt.subplots(figsize=(6, 6))
        wedge = dict(width=0.52)
        ax.pie(seg_count.values, labels=seg_count.index, colors=seg_colors,
               autopct="%1.1f%%", startangle=90, wedgeprops=wedge,
               textprops={"fontsize":9})
        ax.set_title("Customer Segment Distribution", fontsize=12, fontweight="bold")
        plt.tight_layout()
        st.pyplot(fig)

    with col_f:
        seg_stats = rfm_data.groupby("segment")[["recency","frequency","monetary"]].mean().reindex(seg_order)
        seg_stats["count"] = rfm_data["segment"].value_counts().reindex(seg_order)
        seg_stats = seg_stats.round(2)
        seg_stats.columns = ["Avg Recency (days)","Avg Frequency","Avg Monetary (BRL)","Count"]
        st.markdown("**📋 RFM Metrics per Segment**")
        st.dataframe(seg_stats, use_container_width=True)

    # Bar chart RFM metrics
    fig2, ax2 = plt.subplots(figsize=(11, 4.5))
    x = np.arange(len(seg_order))
    w = 0.25
    ax2.bar(x-w, seg_stats["Avg Recency (days)"],  w, label="Avg Recency (days)",  color="#42A5F5")
    ax2.bar(x,   seg_stats["Avg Frequency"],        w, label="Avg Frequency",       color="#66BB6A")
    ax3 = ax2.twinx()
    ax3.bar(x+w, seg_stats["Avg Monetary (BRL)"],   w, label="Avg Monetary (BRL)", color="#FFA726", alpha=0.85)
    ax2.set_xticks(x)
    ax2.set_xticklabels([s.replace(" ","\n") for s in seg_order], fontsize=9)
    ax2.set_ylabel("Recency (days) / Frequency")
    ax3.set_ylabel("Monetary (BRL)", color="#E65100")
    ax2.set_title("Average RFM Metrics per Customer Segment", fontweight="bold")
    lines1,lab1 = ax2.get_legend_handles_labels()
    lines2,lab2 = ax3.get_legend_handles_labels()
    ax2.legend(lines1+lines2, lab1+lab2, fontsize=9)
    ax2.spines["top"].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig2)

    with st.expander("💡 Insight & Rekomendasi per Segmen"):
        st.markdown("""
| Segmen | Karakteristik | Rekomendasi |
|---|---|---|
| **Champions** | Beli baru-baru ini, sering, nilai tinggi | Program VIP, early access, exclusive rewards |
| **Loyal Customers** | Sering beli, nilai baik | Reward points, referral program |
| **Potential Loyalist** | Aktif tapi belum rutin | Cross-sell/upsell, personalized offers |
| **At Risk** | Lama tidak beli | Win-back email + voucher reaktivasi |
| **Lost** | Sangat lama tidak aktif | Campaign hemat biaya atau abaikan |
        """)

# ── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Dashboard dibuat untuk submission Proyek Analisis Data — Dicoding | Annisa Fathia Rahmah")
