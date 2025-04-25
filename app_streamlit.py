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
df.rename(columns={"profile": "On3 Profile", "ProfileURL": "CBS Profile"}, inplace=True)

# 2) Reorder columns
base_cols = [
    "name", "position", "height", "weight", "class", "status",
    "last_team", "new_team", "rating",
    # stats
    "GP", "GS", "MPG", "PPG", "FG%", "3FG%", "FT%",
    "RPG", "APG", "TOPG", "SPG", "BPG",
    "FGM", "FGA", "3FGM", "3FGA", "FTM", "FTA",
    "OREB", "DREB", "REB", "AST", "TO", "STL", "BLK"
]
# Include detail-only cols at end: they'll be hidden in main grid
detail_only = ["On3 Profile", "CBS Profile", "hometown"]
df = df[[c for c in (base_cols + detail_only) if c in df.columns]]

# 3) JS LinkRenderer for profile URLs
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

# 4) Build grid options
gb = GridOptionsBuilder.from_dataframe(df)
# suppress three-dot menu on all columns
gb.configure_default_column(suppressHeaderMenuButton=True)
# master-detail on 'name'
gb.configure_column(
    'name',
    headerName='Player',
    cellRenderer='agGroupCellRenderer',
    cellRendererParams={'suppressCount': True},
    width=200
)
# hide detail-only fields
for col in detail_only:
    if col in df.columns:
        gb.configure_column(col, hide=True)
# configure categorical filters
for col, width in [('position', 120), ('class', 120), ('status', 120), ('height', 80)]:
    if col in df.columns:
        gb.configure_column(
            col,
            filter='agSetColumnFilter',
            filterParams={'values': sorted(df[col].dropna().unique().tolist())},
            width=width
        )
# configure numeric stats filters
stat_cols = [c for c in base_cols if c not in ['name','position','height','weight','class','status','last_team','new_team','rating'] and c in df.columns]
for col in stat_cols:
    gb.configure_column(
        col,
        filter='agNumberColumnFilter',
        filterParams={'defaultOption': 'greaterThanOrEqual'},
        minWidth=80,
        maxWidth=120
    )

# detail grid options with LinkRenderer registered locally
detail_grid_opts = {
    'columnDefs': [
        {'field': 'On3 Profile', 'cellRenderer': 'LinkRenderer'},
        {'field': 'CBS Profile', 'cellRenderer': 'LinkRenderer'},
        {'field': 'hometown'}
    ],
    'defaultColDef': {'flex': 1, 'minWidth': 100},
    'components': {'LinkRenderer': grid_link}
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

# auto-size columns on first render
auto_size = JsCode("""
function(params) {
  const cols = params.columnApi.getAllColumns().map(c => c.getColId());
  params.columnApi.autoSizeColumns(cols, false);
}
""")
grid_options['onFirstDataRendered'] = auto_size

# 5) Display
st.title("Portal Players Dashboard")
st.markdown("""
- Click the expand icon in the Player column to show that player's On3/CBS profile links and hometown  
- Use the funnel icon on **Position, Class, Status, Height** to filter  
- **Stats** use numeric ≥ filters  
""")
AgGrid(
    df,
    gridOptions=grid_options,
    allow_unsafe_jscode=True,
    enable_enterprise_modules=True,
    theme='alpine',
    fit_columns_on_grid_load=False
)
