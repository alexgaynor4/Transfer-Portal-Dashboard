#!/usr/bin/env python3
"""
merge_portal_stats_full.py

This script:
1. Loads portal_players.csv and player_stats.csv.
2. Deduplicates portal entries (keeps 'Committed' over 'Entered').
3. Normalizes names (strips Jr/Sr/II/III/IV/V, punctuation, lowercases).
4. Performs exact merge on normalized names.
5. Fuzzy-matches remaining unmatched portal names to stats names (threshold ≥85).
6. Outputs portal_with_stats.csv and portal_no_stats.csv.
"""

import re
import pandas as pd
from rapidfuzz import process, fuzz

# Regex to strip common suffixes (Jr, Sr, II, III, IV, V), with optional period
SUFFIX_PATTERN = r'\b(?:JR|SR|II|III|IV|V)\b\.?'

def normalize_name(col: pd.Series) -> pd.Series:
    """Strip suffixes, remove punctuation, lowercase, collapse spaces."""
    s = col.fillna('').astype(str)
    s = s.str.replace(SUFFIX_PATTERN, '', flags=re.IGNORECASE, regex=True)
    s = s.str.replace(r'[^\w\s]', '', regex=True)
    s = s.str.lower().str.strip()
    return s.str.replace(r'\s+', ' ', regex=True)

def dedupe_portal(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only the 'Committed' row if duplicates exist, else first occurrence."""
    prio = {'Committed': 1}
    df['_prio'] = df['status'].map(prio).fillna(0).astype(int)
    df = df.sort_values(['name', '_prio'], ascending=[True, False])
    df = df.drop_duplicates(subset=['name'], keep='first')
    return df.drop(columns=['_prio'])

def main():
    # File paths
    portal_csv = 'portal_players.csv'
    stats_csv  = 'player_stats.csv'
    out_with   = 'portal_with_stats.csv'
    out_without= 'portal_no_stats.csv'

    # Load data
    portal = pd.read_csv(portal_csv, dtype=str)
    stats  = pd.read_csv(stats_csv, dtype=str)

    # 1) Deduplicate portal
    portal = dedupe_portal(portal)

    # 2) Normalize names
    portal['NormName'] = normalize_name(portal['name'])
    stats['NormName']  = normalize_name(stats['Name'])

    # 3) Exact merge on normalized names
    merged = pd.merge(
        portal, stats,
        how='inner', on='NormName',
        suffixes=('', '_stats')
    )
    matched_norms = set(merged['NormName'])

    # 4) Fuzzy-match remaining portal names
    unmatched = portal[~portal['NormName'].isin(matched_norms)].copy()
    stats_norms = stats['NormName'].tolist()
    fuzzy_rows = []
    for _, prow in unmatched.iterrows():
        best = process.extractOne(
            prow['NormName'],
            stats_norms,
            scorer=fuzz.token_sort_ratio
        )
        if best and best[1] >= 85 and best[0] not in matched_norms:
            srow = stats[stats['NormName'] == best[0]].iloc[0]
            combined = {**prow.to_dict(), **srow.to_dict()}
            fuzzy_rows.append(combined)
            matched_norms.add(best[0])

    if fuzzy_rows:
        fuzzy_df = pd.DataFrame(fuzzy_rows)
        merged = pd.concat([merged, fuzzy_df], ignore_index=True)

    # 5) Prepare final unmatched list
    final_unmatched = portal[~portal['NormName'].isin(matched_norms)].drop(columns=['NormName'])

    # 6) Clean up merged output
    merged_out = merged.drop(columns=['NormName', 'Name'])

    # 7) Save CSVs
    merged_out.to_csv(out_with, index=False)
    final_unmatched.to_csv(out_without, index=False)

    print(f"✔ Matched {len(merged_out)} portal players → {out_with}")
    print(f"⚠ {len(final_unmatched)} portal players unmatched → {out_without}")

if __name__ == '__main__':
    main()
