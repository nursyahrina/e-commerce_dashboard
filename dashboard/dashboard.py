import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

sns.set(style="white")


def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule="D", on="order_purchase_timestamp").agg(
        {"order_id": "nunique", "order_item_value": "sum"}
    )
    daily_orders_df = daily_orders_df.reset_index()
    daily_orders_df.rename(
        columns={"order_id": "order_count", "order_item_value": "revenue"}, inplace=True
    )

    return daily_orders_df


def create_category_sum_order_df(df):
    category_sum_order_df = (
        df.groupby("product_category_name_english")
        .order_id.nunique()
        .sort_values(ascending=False)
        .reset_index()
    )
    category_sum_order_df.columns = ["category", "order_count"]
    return category_sum_order_df


def create_category_revenue_df(df):
    category_revenue_df = (
        df.groupby("product_category_name_english")
        .order_item_value.sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    category_revenue_df.columns = ["category", "revenue"]
    return category_revenue_df


def create_bystate_df(df):
    bystate_df = (
        df.groupby(by="customer_state").customer_unique_id.nunique().reset_index()
    )
    bystate_df.rename(columns={"customer_unique_id": "customer_count"}, inplace=True)

    return bystate_df


def create_bycity_df(df):
    bycity_df = (
        df.groupby(by="customer_city").customer_unique_id.nunique().reset_index()
    )
    bycity_df.rename(columns={"customer_unique_id": "customer_count"}, inplace=True)

    return bycity_df


def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_unique_id", as_index=False).agg(
        {
            "order_purchase_timestamp": "max",
            "order_id": "nunique",
            "order_item_value": "sum",
        }
    )
    rfm_df.columns = [
        "customer_unique_id",
        "max_order_timestamp",
        "frequency",
        "monetary",
    ]

    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(
        lambda x: (recent_date - x).days
    )

    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)

    return rfm_df


all_df = pd.read_csv("main_data.csv")

datetime_columns = ["order_purchase_timestamp"]
all_df.sort_values(by="order_purchase_timestamp", inplace=True)
all_df.reset_index(inplace=True)

for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()

with st.sidebar:
    # Menambahkan logo perusahaan Olist Brazil
    st.image("img/logo.png")

    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label="Rentang Waktu",
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date],
    )

    # Menambahkan 1 hari pada end_date agar end_date yang dipilih masuk dalam rentang waktu data (inclusive)
    end_date += pd.DateOffset(days=1)

main_df = all_df[
    (all_df["order_purchase_timestamp"] >= str(start_date))
    & (all_df["order_purchase_timestamp"] <= str(end_date))
]

daily_orders_df = create_daily_orders_df(main_df)
category_sum_order_df = create_category_sum_order_df(main_df)
category_revenue_df = create_category_revenue_df(main_df)
bystate_df = create_bystate_df(main_df)
bycity_df = create_bycity_df(main_df)
rfm_df = create_rfm_df(main_df)

st.header("Olist Brazillian E-Commerce Dashboard :chart_with_upwards_trend:")

st.subheader("Daily Orders")

col1, col2 = st.columns(2)

with col1:
    total_orders = daily_orders_df.order_count.sum()
    st.metric("Total orders", value=total_orders)

with col2:
    total_revenue = format_currency(
        daily_orders_df.revenue.sum(), "BRL", locale="pt_BR"
    )
    st.metric("Total Revenue", value=total_revenue)

fig, ax = plt.subplots(figsize=(20, 8))
ax.plot(
    daily_orders_df["order_purchase_timestamp"],
    daily_orders_df["order_count"],
    marker="o",
    linewidth=1.5,
    color="cornflowerblue",
)
ax.tick_params(axis="y", labelsize=20)
ax.tick_params(axis="x", labelsize=20)

st.pyplot(fig)


st.subheader("Best and Worst Performing Product Category by Number of Order")

# Membuat figure dengan 2 subplot
fig, axes = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [2, 1]})

colors = ["blue", "lightgrey", "lightgrey", "lightgrey", "lightgrey"]

# Plot untuk best product category
sns.barplot(
    x="order_count",
    y="category",
    data=category_sum_order_df.head(5),
    palette=colors,
    ax=axes[0],
)
axes[0].set_ylabel(None)
axes[0].set_xlabel(None)
axes[0].set_title("Best Performing Product Category", loc="center", fontsize=16)
axes[0].tick_params(axis="x", labelsize=14)
axes[0].tick_params(axis="y", labelsize=14)

# Plot untuk worst product category
sns.barplot(
    x="order_count",
    y="category",
    data=category_sum_order_df.sort_values(by="order_count", ascending=True).head(5),
    palette=colors,
    ax=axes[1],
)
axes[1].set_ylabel(None)
axes[1].set_xlabel(None)
axes[1].invert_xaxis()
axes[1].yaxis.set_label_position("right")
axes[1].yaxis.tick_right()
axes[1].set_title("Worst Performing Product Category", loc="center", fontsize=16)
axes[1].tick_params(axis="x", labelsize=14)
axes[1].tick_params(axis="y", labelsize=14)

st.pyplot(fig)


st.subheader("Best and Worst Performing Product Category by Revenue (R$)")

# Membuat figure dengan 2 subplot
fig, axes = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [2, 1]})

colors = ["blue", "lightgrey", "lightgrey", "lightgrey", "lightgrey"]

# Plot untuk best product category
sns.barplot(
    x="revenue",
    y="category",
    data=category_revenue_df.head(5),
    palette=colors,
    ax=axes[0],
)
axes[0].set_ylabel(None)
axes[0].set_xlabel(None)
axes[0].set_title("Highest Revenue Categories", loc="center", fontsize=16)
axes[0].tick_params(axis="x", labelsize=14)
axes[0].tick_params(axis="y", labelsize=14)

# Plot untuk worst product category
sns.barplot(
    x="revenue",
    y="category",
    data=category_revenue_df.sort_values(by="revenue", ascending=True).head(5),
    palette=colors,
    ax=axes[1],
)
axes[1].set_ylabel(None)
axes[1].set_xlabel(None)
axes[1].invert_xaxis()
axes[1].yaxis.set_label_position("right")
axes[1].yaxis.tick_right()
axes[1].set_title("Lowest Revenue Categories", loc="center", fontsize=16)
axes[1].tick_params(axis="x", labelsize=14)
axes[1].tick_params(axis="y", labelsize=14)

st.pyplot(fig)


st.subheader("Customer Demographics by State and City")

# Membuat figure dengan 2 subplot
fig, axes = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [3, 2]})

colors = [
    "blue",
    "lightgrey",
    "lightgrey",
    "lightgrey",
    "lightgrey",
    "lightgrey",
    "lightgrey",
]

# Plot untuk best product category
sns.barplot(
    x="customer_count",
    y="customer_state",
    data=bystate_df.sort_values(by="customer_count", ascending=False).head(7),
    palette=colors,
    ax=axes[0],
)
axes[0].set_ylabel(None)
axes[0].set_xlabel(None)
axes[0].set_title("Number of Customer by State", loc="center", fontsize=16)
axes[0].tick_params(axis="x", labelsize=14)
axes[0].tick_params(axis="y", labelsize=14)

# Plot untuk worst product category
sns.barplot(
    x="customer_count",
    y="customer_city",
    data=bycity_df.sort_values(by="customer_count", ascending=False).head(7),
    palette=colors,
    ax=axes[1],
)
axes[1].set_ylabel(None)
axes[1].set_xlabel(None)
axes[1].invert_xaxis()
axes[1].yaxis.set_label_position("right")
axes[1].yaxis.tick_right()
axes[1].set_title("Number of Customer by City", loc="center", fontsize=16)
axes[1].tick_params(axis="x", labelsize=14)
axes[1].tick_params(axis="y", labelsize=14)

st.pyplot(fig)


st.subheader("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_frequency = format_currency(rfm_df.monetary.mean(), "BRL", locale="pt_BR")
    st.metric("Average Monetary", value=avg_frequency)


fig, ax = plt.subplots(3, 1, figsize=(14, 20), gridspec_kw={"hspace": 0.3})
colors = ["blue", "lightgrey", "lightgrey", "lightgrey", "lightgrey"]

sns.barplot(
    x="recency",
    y="customer_unique_id",
    data=rfm_df.sort_values(by="recency", ascending=True).head(5),
    palette=colors,
    ax=ax[0],
)
ax[0].set_xlabel("Recency (days)", fontsize=14)
ax[0].set_ylabel(None)
ax[0].set_title(
    "Best Customer Based on RFM Parameters By Recency (days)", loc="center", fontsize=18
)
ax[0].tick_params(axis="x", labelsize=14)
ax[0].tick_params(axis="y", labelsize=14)

sns.barplot(
    x="frequency",
    y="customer_unique_id",
    data=rfm_df.sort_values(by="frequency", ascending=False).head(5),
    palette=colors,
    ax=ax[1],
)
ax[1].set_xlabel("Frequency of Orders", fontsize=14)
ax[1].set_ylabel(None)
ax[1].set_title(
    "Best Customer Based on RFM Parameters By Frequency", loc="center", fontsize=18
)
ax[1].tick_params(axis="x", labelsize=14)
ax[1].tick_params(axis="y", labelsize=14)

sns.barplot(
    x="monetary",
    y="customer_unique_id",
    data=rfm_df.sort_values(by="monetary", ascending=False).head(5),
    palette=colors,
    ax=ax[2],
)
ax[2].set_xlabel("Monetary (R$)", fontsize=14)
ax[2].set_ylabel(None)
ax[2].set_title(
    "Best Customer Based on RFM Parameters By Monetary (R$)", loc="center", fontsize=18
)
ax[2].tick_params(axis="x", labelsize=14)
ax[2].tick_params(axis="y", labelsize=14)

st.pyplot(fig)

st.caption("Copyright (c) Nursyahrina 2023")
