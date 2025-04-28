import pandas as pd

def dedupe_portal(df: pd.DataFrame) -> pd.DataFrame:
    priority = {"Committed": 1, "Entered": 0}
    df["_prio"] = df["status"].map(priority).fillna(0).astype(int)
    df = df.sort_values(["name", "_prio"], ascending=[True, False])
    df = df.drop_duplicates(subset=["name"], keep="first")
    return df.drop(columns=["_prio"])

def main():
    portal_csv = "portal_players.csv"
    stats_csv  = "player_stats.csv"
    out_with   = "portal_with_stats.csv"
    out_without= "portal_no_stats.csv"

    portal = pd.read_csv(portal_csv)
    stats  = pd.read_csv(stats_csv)
    portal = dedupe_portal(portal)

    merged = pd.merge(
        portal, stats,
        how="inner",
        left_on="name",
        right_on="Name",
        suffixes=("", "_stats")
    )

    if "Name" in merged:
        merged = merged.drop(columns=["Name"])

    no_stats = portal[~portal["name"].isin(stats["Name"])]
    merged.to_csv(out_with, index=False)
    no_stats.to_csv(out_without, index=False)

    print(f"✔ {len(merged)} portal players matched → {out_with}")
    print(f"⚠ {len(no_stats)} portal players missing stats → {out_without}")

if __name__ == "__main__":
    main()
