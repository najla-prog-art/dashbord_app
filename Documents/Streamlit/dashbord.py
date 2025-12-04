import streamlit as st
import plotly.express as px 
import pandas as pd
import os 
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="superstore!!!", page_icon=":bar_chart:", layout="wide")

st.title(":bar_chart: Sample SuperStore EDA")
st.markdown('<style>div.block-container{padding-top:1rem;}</style>', unsafe_allow_html=True)

fl = st.file_uploader(":file_folder: upload a file", type=(["csv","txt","xlsx","xls"]))

# Robust loader: handle uploaded file, local placeholder file, or fetch from GitHub raw URL.
def _load_superstore(uploaded_file):
    raw_url = (
        "https://raw.githubusercontent.com/najla-prog-art/dashbord_app/main/Documents/Streamlit/Superstore.csv"
    )

    # 1) If user uploaded a file, try to read it
    if uploaded_file is not None:
        try:
            df_local = pd.read_csv(uploaded_file, encoding="ISO-8859-1")
            source = f"uploaded file: {getattr(uploaded_file, 'name', 'uploaded') }"
        except Exception:
            try:
                uploaded_file.seek(0)
            except Exception:
                pass
            try:
                df_local = pd.read_csv(uploaded_file)
                source = f"uploaded file (no encoding): {getattr(uploaded_file, 'name', 'uploaded') }"
            except Exception as e:
                st.error(f"Unable to read the uploaded file: {e}")
                return None

    else:
        # 2) Try to read repository file (when running locally or on Cloud this may exist)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(script_dir, "Superstore.csv")
        try:
            df_local = pd.read_csv(csv_path, encoding="ISO-8859-1")
            source = f"local file: {csv_path}"
        except Exception:
            # Fallback to the raw GitHub URL
            try:
                df_local = pd.read_csv(raw_url, encoding="ISO-8859-1")
                source = f"raw url: {raw_url}"
            except Exception as e:
                st.error(f"Unable to load Superstore data from local file or GitHub: {e}")
                return None

    # Detect placeholder file (common mistake: file contains a single 'wget ...' line)
    try:
        if df_local.shape[1] == 1:
            # inspect first cell for 'wget' or a URL
            first_cell = str(df_local.iloc[0, 0]) if not df_local.empty else ""
            if first_cell.strip().startswith("wget") or first_cell.strip().startswith("https://"):
                # try downloading the real file from raw GitHub URL
                try:
                    df_local = pd.read_csv(raw_url, encoding="ISO-8859-1")
                    source = f"re-downloaded from raw url: {raw_url}"
                except Exception:
                    pass
    except Exception:
        # if anything goes wrong during placeholder detection, continue with df_local
        pass

    # Normalize column names (strip whitespace)
    df_local.columns = [str(c).strip() for c in df_local.columns]

    # If expected 'Order Date' column isn't present, try to find a close match
    if "Order Date" not in df_local.columns:
        candidates = [c for c in df_local.columns if "order" in c.lower() and "date" in c.lower()]
        if candidates:
            df_local = df_local.rename(columns={candidates[0]: "Order Date"})
        else:
            # helpful error in the app and stop further execution
            st.error(
                "The dataset does not contain an 'Order Date' column. "
                f"Columns found: {', '.join(df_local.columns[:50])}"
            )
            return None

    # Convert 'Order Date' to datetime where possible
    try:
        df_local["Order Date"] = pd.to_datetime(df_local["Order Date"], errors="coerce")
    except Exception:
        pass

    # small note for debugging in the app (optional)
    st.session_state.setdefault("_data_source", source)
    return df_local


df = _load_superstore(fl)
if df is None:
    st.stop()

# Show which data source was used (helpful when debugging deployments)
data_source = st.session_state.get("_data_source", "unknown")
st.info(f"Data source: {data_source}")

col1,col2 = st.columns ((2))
df["Order Date"]= pd.to_datetime (df["Order Date"])

# Getting the min and max date 
startDate = pd.to_datetime (df["Order Date"]).min()
endDate = pd.to_datetime (df["Order Date"]).max()

with col1: 
    date1= pd.to_datetime (st.date_input("Start Date", startDate))

with col2:
    date2= pd.to_datetime (st.date_input("Start Date", endDate))

df= df[(df["Order Date"]>= date1)&(df["Order Date"]<=date2)].copy()

st.sidebar.header("Choose your filter: ")
#Create for Region
region =st.sidebar.multiselect("Pick Your Region",df["Region"].unique())
if not region:
    df2= df.copy()
else:
    df2 = df[df ["Region"].isin(region)]

#Create for State
state =st.sidebar.multiselect("Pick Your State",df2["State"].unique())
if not state:
    df3= df2.copy()
else:
    df3 = df2[df2["State"].isin(state)]

#Create for City
city =st.sidebar.multiselect("Pick Your City",df3["City"].unique())

#Filter the data based on Region, State and City

if not region and not state and not city:
    filtered_df =df
elif not state and not city:
    filtered_df=df[df["Region"].isin(region)]
elif not region and not city:
    filtered_df= df[df["State"].isin(state)]
elif state and city:
    filtered_df= df3 [df["State"].isin(state)& df3["City"].isin(city)]
elif region and city:
    filtered_df= df3 [df["Region"].isin(region)& df3["City"].isin(city)]
elif region and state:
    filtered_df= df3 [df["Region"].isin(region)& df3["State"].isin(state)]
elif city:
    filtered_df= df3[df3["City"].isin(city)]
else: 
    filtered_df = df3[df3["Region"]. isin(region)&df3["State"].isin(state)&df3["City"].isin(city)]

category_df = filtered_df.groupby(by= ["Category"], as_index= False)["Sales"].sum()

with col1:
    st.subheader("Category wise Sales")
    fig = px.bar(category_df, x ="Category", y = "Sales", text = ['$ {:,.2f}'.format(x) for x in category_df ["Sales"]],
                 template="seaborn")
    st.plotly_chart(fig,use_container_width= True, height =200)

with col2:
    st.subheader("Region wise Sales")
    fig= px.pie (filtered_df, values= "Sales", names= "Region", hole= 0.5)
    fig.update_traces(text= filtered_df ["Region"],textposition= "outside")
    st.plotly_chart(fig, use_container_width=True)

cl1,cl2= st.columns (2)
with cl1:
    with st.expander("Category_ViewData"):
        st.write( category_df. style.background_gradient(cmap="Blues"))
        csv= category_df.to_csv(index= False).encode('utf-8')
        st.download_button("Download Data", data = csv, file_name = "Category.csv", mime = "text/csv" ,
                            help= 'Click here to download the data as a csv file')

with cl2:
    with st.expander("Region_ViewData"):
        region_sales = filtered_df.groupby(by="Region", as_index=False)["Sales"].sum()
        st.write(region_sales.style.background_gradient(cmap="Oranges"))
        csv = region_sales.to_csv(index=False).encode('utf-8')
        st.download_button("Download Data", data=csv, file_name="Region.csv", mime="text/csv",
                        help='Click here to download the data as a csv file')
        
filtered_df["month_year"] = filtered_df ["Order Date"].dt.to_period("M")
st.subheader('Time Series Analysis')

linechart = pd.DataFrame (filtered_df.groupby (filtered_df["month_year"].dt.strftime("%Y : %b"))["Sales"].sum()).reset_index()
fig2 = px.line(linechart, x = "month_year", y="Sales", labels= {"Sales": "Amount"}, height= 500, width= 1000, template= "gridon")
st.plotly_chart(fig2,use_container_width=True)

with st.expander("View Data of TimeSeries:"):
    st.write(linechart.T.style.background_gradient(cmap="Blues"))
    csv = linechart.to_csv(index=False).encode("utf-8")
    st.download_button('Download Data', data=csv, file_name="TimeSeries.csv", mime='text/csv')

    # Create a tree based on Region, Category, Sub-Category
st.subheader("Hierarchical view of Sales using TreeMap")
fig3 = px.treemap(filtered_df, path=["Region", "Category", "Sub-Category"], values="Sales", hover_data=["Sales"], color="Sub-Category")
fig3.update_layout(width=800, height=650)
st.plotly_chart(fig3, use_container_width=True)

chart1, chart2 = st.columns((2, 2))

with chart1:
    st.subheader("Segment wise Sales")
    fig = px.pie(filtered_df, values="Sales", names="Segment", template="plotly_dark")
    fig.update_traces(text=filtered_df["Segment"], textposition="inside")
    st.plotly_chart(fig, use_container_width=True)

with chart2:
    st.subheader("Category wise Sales")
    fig = px.pie(filtered_df, values="Sales", names="Category", template="gridon")
    fig.update_traces(text=filtered_df["Category"], textposition="inside")
    st.plotly_chart(fig, use_container_width=True)

import plotly.figure_factory as ff
st.subheader(":point_right: Month wise Sub-Category Sales Summary")
with st.expander("Summary Table"):
    df_sample = df[0:5][["Region", "State", "City", "Category", "Sales", "Profit", "Quantity"]]
    fig = ff.create_table(df_sample, colorscale="Cividis")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("Month wise sub-Category Table")
    filtered_df["month"] = filtered_df["Order Date"].dt.month_name()
    sub_category_Year = pd.pivot_table(data=filtered_df, values="Sales", index=["Sub-Category"], columns="month")
    st.write(sub_category_Year.style.background_gradient(cmap="Blues"))

# Create a scatter plot
data1 = px.scatter(filtered_df, x="Sales", y="Profit", size="Quantity")
data1['layout'].update(title="Relationship between Sales and Profits using Scatter Plot.",
                        titlefont=dict(size=20), xaxis=dict(title="Sales", titlefont=dict(size=19)),
                        yaxis=dict(title="Profit", titlefont=dict(size=19)))
st.plotly_chart(data1, use_container_width=True)

with st.expander("View Data"):
    st.write(filtered_df.iloc[1:500, 1:20:2].style.background_gradient(cmap="Oranges"))

# Download original DataSet
csv = df.to_csv(index=False).encode('utf-8')
st.download_button('Download Data', data=csv, file_name="Data.csv", mime="text/csv")
