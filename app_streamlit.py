#!/usr/bin/env python3
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

# 0) Page config
st.set_page_config(page_title="Portal Players Dashboard", layout="wide")

# 1) Load & clean
df = pd.read_csv("portal_with_stats.csv")
df.drop(columns=["high_school", "nil_value", "Team", "A/TO"], errors=True, inplace=True)
df = df.loc[:, ~df.columns.str.match(r'^(GP|GS)\.\d+$')]
df = df.loc[:, ~df.columns.duplicated()]

# Rename raw profile and standardize key fields
df.rename(columns={
    "profile": "On3 Profile",
    "ProfileURL": "CBS Profile"
}, inplace=True)

# 1.1) Standardize and rename categorical fields
if 'position' in df.columns:
    df['position'] = df['position'].str.upper()
if 'last_team' in df.columns:
    df['last_team'] = df['last_team'].str.title()
if 'new_team' in df.columns:
    df['new_team'] = df['new_team'].str.title()
# Capitalize header names for key columns
df.rename(columns={
    'position': 'POS',
    'height': 'Height',
    'weight': 'Weight',
    'class': 'Class',
    'status': 'Status',
    'rating': 'Rating',
    'last_team': 'Last Team',
    'new_team': 'First Team'
}, inplace=True)

# 2) Reorder columns
base_cols = [
    "name", "POS", "Height", "Weight", "Class", "Status",
    "Last Team", "First Team", "Rating",
    # stats
    "GP", "GS", "MPG", "PPG", "FG%", "3FG%", "FT%",
    "RPG", "APG", "TOPG", "SPG", "BPG",
    "FGM", "FGA", "3FGM", "3FGA", "FTM", "FTA",
    "OREB", "DREB", "REB", "AST", "TO", "STL", "BLK"
]
# detail-only in master view
detail_only = ["On3 Profile", "CBS Profile", "hometown"]
df = df[[c for c in (base_cols + detail_only) if c in df.columns]]

# 3) Convert percentage & stat columns to numeric (coerce '--' to NaN)
stat_cols = [
    c for c in base_cols if c not in [
        'name','POS','Height','Weight','Class','Status',
        'Last Team','First Team','Rating'
    ] and c in df.columns
]
for col in stat_cols:
    df[col] = df[col].replace('--', pd.NA)
    df[col] = pd.to_numeric(df[col], errors='coerce')

# 4) JS LinkRenderer for profile URLs
grid_link = JsCode("""
class LinkRenderer {
  init(params) {
    const a = document.createElement('a');
    a.href = params.value;
    a.target = '_blank';
    a.textContent = 'Link';
    this.eGui = a;
  }
  getGui() { return this.eGui; }
}
""")

# 5) Build grid options
gb = GridOptionsBuilder.from_dataframe(df)
# default: suppress menu, make columns flex and resizable
gb.configure_default_column(
    suppressHeaderMenuButton=True,
    flex=1,
    minWidth=100,
    resizable=True
)
# master-detail on 'name'
gb.configure_column(
    'name',
    headerName='Player',
    cellRenderer='agGroupCellRenderer',
    cellRendererParams={'suppressCount': True},
    width=200,
    flex=0
)
# hide detail-only fields
for col in detail_only:
    if col in df.columns:
        gb.configure_column(col, hide=True)
# configure categorical filters with explicit widths
for col, width in [("POS", 120), ("Class", 120), ("Status", 120), ("Height", 80), ("Weight", 80)]:
    if col in df.columns:
        gb.configure_column(
            col,
            filter='agSetColumnFilter',
            filterParams={'values': sorted(df[col].dropna().unique().tolist())},
            width=width,
            flex=0
        )
# configure numeric stats filters
for col in stat_cols:
    gb.configure_column(
        col,
        filter='agNumberColumnFilter',
        filterParams={'defaultOption': 'greaterThanOrEqual'},
        minWidth=100,
        maxWidth=150
    )

# detail grid options
detail_grid_opts = {
    'columnDefs': [
        {'field': 'On3 Profile', 'cellRenderer': 'LinkRenderer'},
        {'field': 'CBS Profile', 'cellRenderer': 'LinkRenderer'},
        {'field': 'hometown'}
    ],
    'defaultColDef': {'flex': 1, 'minWidth': 100},
    'components': {'LinkRenderer': grid_link},
    'domLayout': 'autoHeight',
    'onFirstDataRendered': JsCode("""
        function(params) {
            const allCols = params.columnApi.getAllColumns().map(c => c.getColId());
            params.columnApi.autoSizeColumns(allCols, false);
        }
    """)
}

gb.configure_grid_options(
    masterDetail=True,
    detailCellRendererParams={
        'detailGridOptions': detail_grid_opts,
        'frameworkComponents': {'LinkRenderer': grid_link},
        'getDetailRowData': JsCode("""
            function(params) {
                params.successCallback([params.data]);
            }
        """)
    }
)

# build final grid options
grid_options = gb.build()
# shrink detail panel height to content
grid_options['detailRowHeight'] = 140

# auto-size parent columns on first render
auto_size = JsCode("""
function(params) {
  const cols = params.columnApi.getAllColumns().map(c => c.getColId());
  params.columnApi.autoSizeColumns(cols, false);
}
""")
grid_options['onFirstDataRendered'] = auto_size

# 6) Display
st.title("Portal Players Dashboard")
st.markdown("""
- Click the expand icon in the Player column to show that player's On3/CBS profile links and hometown  
- Use the funnel icon on **POS, Class, Status, Height, Weight, Rating** to filter  
- **Stats** use numeric ≥ filters  
""")
AgGrid(
    df,
    gridOptions=grid_options,
    allow_unsafe_jscode=True,
    enable_enterprise_modules=True,
    theme='alpine',
    height=700,
    width='100%'
)
