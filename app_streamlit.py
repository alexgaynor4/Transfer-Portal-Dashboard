# app_streamlit.py

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import streamlit_authenticator as stauth
import yaml

# --- Authentication setup ---
# Replace these with your own users and passwords
names = ["Your Name"]
usernames = ["your_username"]
passwords = ["your_password"]  # plaintext, they will be hashed

hashed_passwords = stauth.Hasher(passwords).generate()

credentials = {
    "usernames": {
        usernames[i]: {
            "name": names[i],
            "password": hashed_passwords[i]
        } for i in range(len(usernames))
    }
}

authenticator = stauth.Authenticate(
    credentials,
    cookie_name="portal_dashboard_auth",
    key="abcdef",  # change this to a strong key
    cookie_expiry_days=30
)

name, auth_status, username = authenticator.login("Login", "main")

if auth_status:
    authenticator.logout("Logout", "sidebar")
    st.title("Portal Players Dashboard")

    # --- Load and clean data ---
    df = pd.read_csv("portal_with_stats.csv")

    # Drop unwanted columns
    df = df.drop(columns=[
        "high_school", "nil_value", "position", "Team", "A/TO"
    ], errors="ignore")

    # Remove GP.x or GS.x duplicate columns
    df = df.loc[:, ~df.columns.str.match(r'^(GP|GS)\.\d+$')]
    df = df.loc[:, ~df.columns.duplicated()]

    # Rename profile links
    df = df.rename(columns={
        "profile": "On3 Profile",
        "ProfileURL": "CBS Profile"
    })

    # Reorder columns
    col_order = [
        "name", "On3 Profile", "CBS Profile",
        "Position", "height", "weight", "class", "status",
        "last_team", "new_team", "hometown", "rating",
        "GP", "GS", "MPG", "PPG", "FG%", "3FG%", "FT%",
        "RPG", "APG", "TOPG", "SPG", "BPG",
        "FGM", "FGA", "3FGM", "3FGA", "FTM", "FTA",
        "OREB", "DREB", "REB", "AST", "TO", "STL", "BLK"
    ]
    cols = [c for c in col_order if c in df.columns]
    df = df[cols]

    # --- Display with AgGrid ---
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(filterable=True, sortable=True, resizable=True)
    grid_options = gb.build()

    st.subheader("Filter & Sort Players")
    AgGrid(df, gridOptions=grid_options, enable_enterprise_modules=False)

elif auth_status is False:
    st.error("Username/password is incorrect")
elif auth_status is None:
    st.warning("Please enter your username and password")

# To run locally: pip install streamlit pandas streamlit-authenticator streamlit-aggrid
# Then: streamlit run app_streamlit.py
