#!/usr/bin/env python3
# compute_sv_sss.py — extracted from compute_sv_sss.qmd
# Part 1: Structural Virality (SV)
# Part 2: Sentiment Shift Score (SSS) — firm-specific prior tone (most recent prior week)

import pandas as pd
import numpy as np
from collections import defaultdict, deque
from pathlib import Path
import re, os, warnings
warnings.filterwarnings("ignore")

PARQUET     = "reddit_2020_2025_with_type_tone.parquet"
OUT_THREADS = "output/sv_threads.csv"
OUT_WEEK    = "output/sv_by_week.csv"
OUT_SSS     = "output/sss_overall_by_week.csv"
Path("output").mkdir(exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Structural Virality
# ══════════════════════════════════════════════════════════════════════════════
print("=== PART 1: Structural Virality ===", flush=True)
print("Loading parquet...", flush=True)
df = pd.read_parquet(PARQUET, columns=["id","parent_id","type","ticker","date","author_id"])
df["type"] = pd.to_numeric(df["type"], errors="coerce")
df = df.dropna(subset=["type"])
df["type"] = df["type"].astype(int)
df["date"] = pd.to_datetime(df["date"])
print(f"  Rows: {len(df):,}", flush=True)

children = defaultdict(list)
for row in df[["id","parent_id"]].itertuples(index=False):
    children[row.parent_id].append(row.id)

all_ids = set(df["id"])
id_info = df.set_index("id")[["type","ticker","date"]].to_dict("index")

roots = df[~df["parent_id"].isin(all_ids)]["id"].unique()
print(f"  Root nodes: {len(roots):,}", flush=True)

def compute_sv(root):
    nodes = []
    parent_map = {}
    queue = deque([root])
    while queue:
        node = queue.popleft()
        nodes.append(node)
        for child in children.get(node, []):
            parent_map[child] = node
            queue.append(child)
    n = len(nodes)
    if n <= 1:
        return None
    subtree = {nd: 1 for nd in nodes}
    for nd in reversed(nodes):
        p = parent_map.get(nd)
        if p is not None:
            subtree[p] += subtree[nd]
    wiener = sum(subtree[nd] * (n - subtree[nd]) for nd in nodes if nd != root)
    sv = 2 * wiener / (n * (n - 1))
    depth = 0
    q2 = deque([(root, 0)])
    while q2:
        nd, d = q2.popleft()
        depth = max(depth, d)
        for ch in children.get(nd, []):
            q2.append((ch, d+1))
    return sv, n, depth

print("Computing SV for all root threads...", flush=True)
rows = []
for i, root in enumerate(roots):
    info = id_info.get(root)
    if info is None:
        continue
    res = compute_sv(root)
    if res is None:
        continue
    sv, n, depth = res
    rows.append({
        "root_id": root,
        "type":    info["type"],
        "ticker":  str(info["ticker"]),
        "date":    info["date"],
        "sv":      round(sv, 6),
        "size":    n,
        "depth":   depth
    })
    if (i+1) % 500000 == 0:
        print(f"  {i+1:,} / {len(roots):,} roots processed...", flush=True)

sv_df = pd.DataFrame(rows)
sv_df.to_csv(OUT_THREADS, index=False)
print(f"\nSaved: {OUT_THREADS}  ({len(sv_df):,} rows)", flush=True)

type_map = {1:"fanatic", 2:"rational", 3:"naive"}
sv_df["type_label"] = sv_df["type"].map(type_map)
sv_df["ticker_clean"] = sv_df["ticker"].apply(lambda t: re.findall(r"[A-Z]{1,5}", str(t)))
sv_long = sv_df.explode("ticker_clean").dropna(subset=["ticker_clean"])
sv_long["week_start"] = sv_long["date"] - pd.to_timedelta(sv_long["date"].dt.dayofweek, unit="D")

agg = (sv_long.groupby(["ticker_clean","week_start","type_label"])
       .agg(sv_mean=("sv","mean"), sv_max=("sv","max"),
            depth_max=("depth","max"), n_threads=("root_id","count"))
       .reset_index())

sv_wide = agg.pivot_table(
    index=["ticker_clean","week_start"],
    columns="type_label",
    values=["sv_mean","sv_max","depth_max","n_threads"],
    aggfunc="first")
sv_wide.columns = ["_".join(c) for c in sv_wide.columns]
sv_wide = sv_wide.reset_index().rename(columns={"ticker_clean":"ticker"})

sv_wide.to_csv(OUT_WEEK, index=False)
print(f"Saved: {OUT_WEEK}  ({len(sv_wide):,} rows)", flush=True)
print(sv_wide.describe().to_string())

# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Sentiment Shift Score (SSS) — firm-specific prior tone
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== PART 2: Sentiment Shift Score ===", flush=True)
print("Loading parquet...", flush=True)
cols = ["datetime", "author_id", "id", "ticker", "parent_id", "date", "tone"]
df = pd.read_parquet(PARQUET, columns=cols)
print(f"  Rows: {len(df):,}", flush=True)

df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
df["date"]     = pd.to_datetime(df["date"])
df["tone"]     = pd.to_numeric(df["tone"], errors="coerce")

# Prior tone: most recent prior week with posts, per author × ticker
print("Computing per-author-ticker prior week tone...", flush=True)
df["week_start"] = df["date"] - pd.to_timedelta(df["date"].dt.dayofweek, unit="D")

weekly_tone = (
    df.groupby(["author_id", "ticker", "week_start"])["tone"]
    .mean()
    .reset_index()
    .rename(columns={"tone": "week_tone"})
)

df_weeks = df[["id", "author_id", "ticker", "week_start"]].merge(
    weekly_tone, on=["author_id", "ticker"], suffixes=("", "_hist")
)
df_weeks = df_weeks[df_weeks["week_start_hist"] < df_weeks["week_start"]]
df_weeks = (
    df_weeks.sort_values("week_start_hist")
    .groupby("id")
    .last()
    .reset_index()[["id", "week_tone"]]
    .rename(columns={"week_tone": "prior_tone"})
)

df = df.merge(df_weeks, on="id", how="left")
print(f"  Prior tone valid for {df['prior_tone'].notna().sum():,} rows", flush=True)

print("Computing tone shift per reply...", flush=True)
replies = df[["id", "parent_id", "tone", "prior_tone", "date", "ticker"]].copy()
replies = replies.rename(columns={
    "id":          "reply_id",
    "tone":        "reply_tone",
    "prior_tone":  "reply_prior_tone",
    "date":        "reply_date",
    "ticker":      "reply_ticker",
})

parents = df[["id", "date", "ticker"]].copy()
parents = parents.rename(columns={
    "id":     "parent_id",
    "date":   "parent_date",
    "ticker": "parent_ticker",
})

print("  Merging replies with parent info...", flush=True)
merged = replies.merge(parents, on="parent_id", how="inner")
print(f"  Matched replies: {len(merged):,}", flush=True)

merged["tone_shift"] = merged["reply_tone"] - merged["reply_prior_tone"]
merged = merged.dropna(subset=["tone_shift"])
print(f"  Valid tone shifts: {len(merged):,}", flush=True)

print("Aggregating per parent comment...", flush=True)
merged["parent_ticker"] = merged["parent_ticker"].astype(str)

sss_comment = (
    merged.groupby(["parent_id", "parent_date", "parent_ticker"])
          .agg(
              sss_mean=("tone_shift", "mean"),
              sss_abs=("tone_shift", lambda x: x.abs().mean()),
              n_replies=("reply_id", "count"),
          )
          .reset_index()
)

def extract_tickers(t):
    if pd.isna(t):
        return []
    return re.findall(r"[A-Z]{1,5}", str(t))

sss_comment["ticker_list"] = sss_comment["parent_ticker"].apply(extract_tickers)
sss_comment = sss_comment.explode("ticker_list").dropna(subset=["ticker_list"])

sss_comment["week_start"] = (
    sss_comment["parent_date"] -
    pd.to_timedelta(sss_comment["parent_date"].dt.dayofweek, unit="D")
)

print("Aggregating to stock×week (type-agnostic)...", flush=True)
agg = (
    sss_comment
    .groupby(["ticker_list", "week_start"])
    .agg(
        sss_mean_tone_shift=("sss_mean",  "mean"),
        sss_abs_tone_shift =("sss_abs",   "mean"),
        n_comments         =("parent_id", "count"),
    )
    .reset_index()
    .rename(columns={"ticker_list": "ticker"})
)
print(f"  Rows: {len(agg):,}", flush=True)

agg.to_csv(OUT_SSS, index=False)
print(f"\nSaved: {OUT_SSS}  ({len(agg):,} rows)", flush=True)
print(agg.head(3).to_string())
print("\nSummary:")
print(agg[["sss_mean_tone_shift","sss_abs_tone_shift","n_comments"]].describe().round(4).to_string())
