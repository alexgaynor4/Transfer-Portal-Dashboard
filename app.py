import dash
from dash import dash_table, html
import pandas as pd

# 1) Load and clean
df = pd.read_csv("portal_with_stats.csv")

df = df.drop(columns=[
    "high_school", "nil_value",  # on3 extras
    "position",                   # on3 position
    "Team",                       # CBS team
    "A/TO"                        # assist/turnover ratio
], errors="ignore")

# drop any GP.x or GS.x columns
df = df.loc[:, ~df.columns.str.match(r'^(GP|GS)\.\d+$')]
# drop exact-duplicate columns (keep first)
df = df.loc[:, ~df.columns.duplicated()]

# rename the URL columns
df = df.rename(columns={
    "profile": "On3 Profile",
    "ProfileURL": "CBS Profile"
})

# render URLs as markdown links
df["On3 Profile"] = df["On3 Profile"].apply(lambda u: f"[Link]({u})")
df["CBS Profile"] = df["CBS Profile"].apply(lambda u: f"[Link]({u})")

# 2) Define your exact column order
col_order = [
    "name", "On3 Profile", "CBS Profile",
    "Position", "height", "weight", "class", "status",
    "last_team", "new_team", "hometown", "rating",
    "GP", "GS", "MPG", "PPG", "FG%", "3FG%", "FT%",
    "RPG", "APG", "TOPG", "SPG", "BPG",
    "FGM", "FGA", "3FGM", "3FGA", "FTM", "FTA",
    "OREB", "DREB", "REB", "AST", "TO", "STL", "BLK"
]
# keep only those that actually exist
cols = [c for c in col_order if c in df.columns]

import dash
import dash_auth
from dash import dash_table, html
import pandas as pd

# 2) Create your Dash app & enable Basic Auth
USERNAME_PASSWORD_PAIRS = {
    "your_username": "your_password"
}

app = dash.Dash(__name__)
auth = dash_auth.BasicAuth(app, USERNAME_PASSWORD_PAIRS)

# 3) Define your layout
app.layout = html.Div([
    html.H1("Portal Players Dashboard (Protected)"),
    dash_table.DataTable(
        id="portal-table",
        columns=[{"name": c, "id": c,
                  **({"presentation": "markdown"}
                     if c in ["On3 Profile","CBS Profile"] else {})}
                 for c in df.columns],
        data=df.to_dict("records"),
        page_size=20,
        filter_action="native",
        sort_action="native",
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left", "minWidth": "80px"},
    )
])

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
