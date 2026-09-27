import pandas as pd
import plotly.express as px
import streamlit as st

# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Fire Burned in Lebanon over the Years",
    page_icon="🔥",
    layout="wide",
)

st.title("🔥 Fire Burned in Lebanon over the Years")

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("fire_data.csv")

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    df["Item"] = df["Item"].astype("string").str.strip()

    df = df.dropna(subset=["Year", "Value", "Item"])
    df["Year"] = df["Year"].astype(int)
    return df


try:
    df = load_data()
except FileNotFoundError:
    st.error("Place fire_data.csv in the same folder as this Streamlit app.")
    st.stop()

if df.empty:
    st.warning("The CSV contains no valid Year, Item, and Value rows.")
    st.stop()

# ── Shared filters ────────────────────────────────────────────────────────────
year_options = ["All years"] + sorted(df["Year"].unique().tolist())
land_options = ["All land types"] + sorted(df["Item"].unique().tolist())

filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    selected_year = st.selectbox("Select year", year_options)

with filter_col2:
    selected_land_type = st.selectbox("Select land type", land_options)

filtered_df = df.copy()

if selected_year != "All years":
    filtered_df = filtered_df[filtered_df["Year"] == selected_year]

if selected_land_type != "All land types":
    filtered_df = filtered_df[filtered_df["Item"] == selected_land_type]

if filtered_df.empty:
    st.info("There are no records for this selection.")
    st.stop()

total_burned = filtered_df["Value"].sum()

st.metric(
    "Total burned area",
    f"{total_burned:,.0f} hectares",
)

# Keep category colors consistent across both charts
palette = px.colors.qualitative.Bold
color_map = {
    category: palette[i % len(palette)]
    for i, category in enumerate(sorted(df["Item"].unique()))
}

# ── Pie chart ─────────────────────────────────────────────────────────────────
pie_data = filtered_df.groupby("Item", as_index=False)["Value"].sum()

pie_fig = px.pie(
    pie_data,
    names="Item",
    values="Value",
    hole=0.48,
    color="Item",
    color_discrete_map=color_map,
)

pie_fig.update_traces(
    textposition="inside",
    textinfo="percent",
    hovertemplate=(
        "<b>%{label}</b><br>"
        "%{value:,.0f} hectares"
        "<extra></extra>"
    ),
)

pie_fig.update_layout(
    height=480,
    margin=dict(l=20, r=20, t=35, b=20),
    legend_title_text="Land type",
)

# ── Bar chart ─────────────────────────────────────────────────────────────────
# All years + all land types: one total bar per land type
# One year + all land types: one bar per land type for that year
# All years + one land type: one bar for each year
# One year + one land type: one narrow bar

if selected_land_type != "All land types" and selected_year == "All years":
    bar_data = (
        filtered_df.groupby("Year", as_index=False)["Value"]
        .sum()
        .sort_values("Year")
    )

    bar_fig = px.bar(
        bar_data,
        x="Year",
        y="Value",
        text="Value",
        title=f"{selected_land_type} burned area by year",
        labels={
            "Value": "Total burned area (hectares)",
            "Year": "Year",
        },
        color_discrete_sequence=[color_map[selected_land_type]],
    )
    bar_fig.update_xaxes(type="category")

else:
    bar_data = (
        filtered_df.groupby("Item", as_index=False)["Value"]
        .sum()
        .sort_values("Value", ascending=False)
    )

    bar_fig = px.bar(
        bar_data,
        x="Item",
        y="Value",
        color="Item",
        text="Value",
        title=(
            "Total burned area by land type"
            if selected_year == "All years"
            else f"Burned area by land type in {selected_year}"
        ),
        labels={
            "Item": "Land type",
            "Value": "Total burned area (hectares)",
        },
        color_discrete_map=color_map,
    )

bar_fig.update_traces(
    texttemplate="%{y:,.0f}",
    textposition="inside",
    insidetextanchor="middle",
    textfont=dict(color="white", size=16),
    hovertemplate="%{y:,.0f} hectares<extra></extra>",
)

if selected_land_type != "All land types" and selected_year != "All years":
    bar_fig.update_traces(width=0.35)
    bar_fig.update_xaxes(range=[-0.8, 0.8])

bar_fig.update_layout(
    height=480,
    showlegend=False,
    margin=dict(l=20, r=20, t=60, b=60),
    yaxis=dict(rangemode="tozero"),
)

# ── Display charts side by side ───────────────────────────────────────────────
pie_col, bar_col = st.columns(2, gap="large")

with pie_col:
    st.subheader("🥧 Share of burned area")
    st.plotly_chart(
        pie_fig,
        use_container_width=True,
        key="burned_area_pie",
    )

with bar_col:
    st.subheader("📊 Total burned area")
    st.plotly_chart(
        bar_fig,
        use_container_width=True,
        key="burned_area_bar",
    )

# ── Insight for the current selection ────────────────────────────────────────
st.subheader("💡 Insight")

if selected_land_type == "All land types":
    leading_row = pie_data.loc[pie_data["Value"].idxmax()]
    leading_type = leading_row["Item"]
    leading_value = leading_row["Value"]

    if total_burned != 0:
        leading_share = leading_value / total_burned * 100

        if selected_year == "All years":
            st.write(
                f"Across all recorded years, **{leading_type}** has the "
                f"largest recorded burned area: **{leading_value:,.0f} hectares**, "
                f"representing **{leading_share:.1f}%** of the total."
            )
        else:
            st.write(
                f"In **{selected_year}**, **{leading_type}** has the "
                f"largest recorded burned area: **{leading_value:,.0f} hectares**, "
                f"representing **{leading_share:.1f}%** of that year's total."
            )
    else:
        st.write("The selected records have a total burned area of zero.")

elif selected_year == "All years":
    peak_row = bar_data.loc[bar_data["Value"].idxmax()]
    peak_year = int(peak_row["Year"])
    peak_value = peak_row["Value"]

    st.write(
        f"For **{selected_land_type}**, the highest recorded burned area "
        f"was in **{peak_year}**, at **{peak_value:,.0f} hectares**."
    )

else:
    st.write(
        f"In **{selected_year}**, the recorded burned area for "
        f"**{selected_land_type}** was **{total_burned:,.0f} hectares**."
    )