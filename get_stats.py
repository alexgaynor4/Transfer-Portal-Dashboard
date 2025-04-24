#!/usr/bin/env python3
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from functools import reduce

HEADERS = {'User-Agent': 'Mozilla/5.0'}
BASE_URL = (
    "https://www.cbssports.com/college-basketball/stats/player/"
    "{category}/all-conf/all-pos/all/"
)

# The five stat categories we want
CATEGORIES = [
    "scoring",
    "rebounds",
    "assists-turnovers",
    "steals",
    "blocks"
]

def scrape_category(category: str) -> pd.DataFrame:
    page = 1
    headers = None
    rows = []

    while True:
        print(f"  → {category}: scraping page {page}")
        resp = requests.get(
            BASE_URL.format(category=category),
            params={'page': page},
            headers=HEADERS
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table', class_='TableBase-table')
        if table is None:
            break

        # Build header row once
        if headers is None:
            ths = table.find('thead').find_all('th')
            # skip the first TH (“Player”), then take the first token of each header cell
            stats_cols = [
                ' '.join(th.get_text(separator=' ').split()).split()[0]
                for th in ths[1:]
            ]
            headers = ['Name', 'ProfileURL', 'Position', 'Team'] + stats_cols

        # Extract each player row
        body = table.find('tbody')
        if not body:
            break
        for tr in body.find_all('tr'):
            tds = tr.find_all('td')
            long_span = tds[0].find('span', class_='CellPlayerName--long')
            link     = long_span.find('a')
            name     = link.text.strip()
            profile  = "https://www.cbssports.com" + link['href']
            pos      = long_span.find('span', class_='CellPlayerName-position').text.strip()
            team     = long_span.find('span', class_='CellPlayerName-team').text.strip()
            stats    = [td.text.strip() for td in tds[1:]]
            rows.append([name, profile, pos, team] + stats)

        page += 1
        time.sleep(1)

    return pd.DataFrame(rows, columns=headers) if headers else pd.DataFrame()

def main():
    # 1) scrape each category into its own DataFrame
    dfs = []
    for cat in CATEGORIES:
        df_cat = scrape_category(cat)
        if df_cat.empty:
            print(f"⚠️  No data for category {cat}")
            continue
        # prefix every stat col so they don't collide on merge
        stat_cols = df_cat.columns.tolist()[4:]
        df_cat = df_cat.rename(
            columns={c: f"{cat}_{c}" for c in stat_cols}
        )
        dfs.append(df_cat)

    if not dfs:
        print("No data scraped; exiting.")
        return

    # 2) merge all DataFrames on Name/ProfileURL/Position/Team
    key_cols = ['Name', 'ProfileURL', 'Position', 'Team']
    combined = reduce(
        lambda left, right: pd.merge(left, right, on=key_cols, how='outer'),
        dfs
    )

    # 3) simplify column names by stripping "<category>_" prefixes
    new_cols = []
    for col in combined.columns:
        if "_" in col:
            prefix, rest = col.split("_", 1)
            if prefix in CATEGORIES:
                new_cols.append(rest)
                continue
        new_cols.append(col)
    combined.columns = new_cols

    # 4) write out the final CSV
    combined.to_csv("player_stats.csv", index=False)
    print(f"\n✅ Saved {len(combined)} players to player_stats.csv")

if __name__ == "__main__":
    main()
