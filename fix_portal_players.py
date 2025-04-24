#!/usr/bin/env python3
import pandas as pd

def dedupe_portal(df: pd.DataFrame) -> pd.DataFrame:
    """
    For any name that appears more than once, keep the row
    where status == "Committed" if present, otherwise keep the first.
    """
    # Define priority: Committed > Entered > anything else
    priority = {"Committed": 1, "Entered": 0}
    # Map statuses to numeric, default to 0
    df["_prio"] = df["status"].map(priority).fillna(0).astype(int)
    # Sort so higher-priority rows come first
    df = df.sort_values(["name", "_prio"], ascending=[True, False])
    # Drop duplicates, keeping first (i.e. highest priority)
    df = df.drop_duplicates(subset=["name"], keep="first")
    return df.drop(columns=["_prio"])

def main():
    portal_csv = "portal_players.csv"
    stats_csv  = "player_stats.csv"
    out_with   = "portal_with_stats.csv"
    out_without= "portal_no_stats.csv"

    # 1) load
    portal = pd.read_csv(portal_csv)
    stats  = pd.read_csv(stats_csv)

    # 2) dedupe portal list
    portal = dedupe_portal(portal)

    # 3) exact merge on name
    merged = pd.merge(
        portal, stats,
        how="inner",
        left_on="name",
        right_on="Name",
        suffixes=("", "_stats")
    )
    # drop duplicate stats Name column
    if "Name" in merged:
        merged = merged.drop(columns=["Name"])

    # 4) find portal rows without stats
    no_stats = portal[~portal["name"].isin(stats["Name"])]

    # 5) save
    merged.to_csv(out_with, index=False)
    no_stats.to_csv(out_without, index=False)

    print(f"✔ {len(merged)} portal players matched → {out_with}")
    print(f"⚠ {len(no_stats)} portal players missing stats → {out_without}")

if __name__ == "__main__":
    main()
