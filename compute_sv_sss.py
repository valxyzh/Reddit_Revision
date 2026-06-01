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
OUT_SSS         = "output/sss_overall_by_week.csv"
OUT_SSS_AGNOSTIC = "output/sss_firm_agnostic_by_week.csv"
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
df["week_start"] = df["date"] - pd.to_timedelta(df["date"].dt.dayofweek, unit="D")

# Explode ticker (stored as array in parquet) into clean scalar strings
df["ticker_list"] = df["ticker"].apply(lambda t: re.findall(r"[A-Z]{1,5}", str(t)))
df_exploded = df.explode("ticker_list").dropna(subset=["ticker_list"])
df_exploded = df_exploded.rename(columns={"ticker_list": "ticker_clean"})

# Prior tone: most recent prior week with posts, per author × ticker_clean
print("Computing per-author-ticker prior week tone...", flush=True)

weekly_tone = (
    df_exploded.groupby(["author_id", "ticker_clean", "week_start"])["tone"]
    .mean()
    .reset_index()
    .rename(columns={"tone": "week_tone"})
)

df_weeks = df_exploded[["id", "author_id", "ticker_clean", "week_start"]].merge(
    weekly_tone, on=["author_id", "ticker_clean"], suffixes=("", "_hist")
)
df_weeks = df_weeks[df_weeks["week_start_hist"] < df_weeks["week_start"]]
df_weeks = (
    df_weeks.sort_values("week_start_hist")
    .groupby("id")
    .last()
    .reset_index()[["id", "week_tone"]]
    .rename(columns={"week_tone": "prior_tone"})
)

df_exploded = df_exploded.merge(df_weeks, on="id", how="left")
print(f"  Prior tone valid for {df_exploded['prior_tone'].notna().sum():,} rows", flush=True)

print("Computing tone shift per reply...", flush=True)
replies = df_exploded[["id", "parent_id", "tone", "prior_tone", "date", "ticker_clean"]].copy()
replies = replies.rename(columns={
    "id":           "reply_id",
    "tone":         "reply_tone",
    "prior_tone":   "reply_prior_tone",
    "date":         "reply_date",
    "ticker_clean": "reply_ticker",
})

# Parents: use original df (pre-explode) — ticker_clean from exploded df_exploded
parents = df_exploded[["id", "date", "ticker_clean"]].drop_duplicates("id").copy()
parents = parents.rename(columns={
    "id":           "parent_id",
    "date":         "parent_date",
    "ticker_clean": "parent_ticker",
})

print("  Merging replies with parent info...", flush=True)
merged = replies.merge(parents, on="parent_id", how="inner")
print(f"  Matched replies: {len(merged):,}", flush=True)

merged["tone_shift"] = merged["reply_tone"] - merged["reply_prior_tone"]
merged = merged.dropna(subset=["tone_shift"])
print(f"  Valid tone shifts: {len(merged):,}", flush=True)

print("Aggregating per parent comment...", flush=True)
sss_comment = (
    merged.groupby(["parent_id", "parent_date", "parent_ticker"])
          .agg(
              sss_mean=("tone_shift", "mean"),
              sss_abs=("tone_shift", lambda x: x.abs().mean()),
              n_replies=("reply_id", "count"),
          )
          .reset_index()
)

# ticker_clean is already a scalar string — no need to re-explode
sss_comment = sss_comment.rename(columns={"parent_ticker": "ticker_list"})

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

# ══════════════════════════════════════════════════════════════════════════════
# PART 3: SSS — firm-agnostic prior tone (cross-stock cumulative author baseline)
# prior_tone = cumulative mean tone across all posts by this author (any stock),
# requires >= 3 prior posts. Type-agnostic and firm-agnostic.
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== PART 3: SSS — Firm-Agnostic ===", flush=True)
print("Loading parquet...", flush=True)
df2 = pd.read_parquet(PARQUET, columns=["datetime", "author_id", "id", "ticker", "parent_id", "date", "tone"])
print(f"  Rows: {len(df2):,}", flush=True)

df2["datetime"] = pd.to_datetime(df2["datetime"], utc=True)
df2["date"]     = pd.to_datetime(df2["date"])
df2["tone"]     = pd.to_numeric(df2["tone"], errors="coerce")

print("Computing cumulative cross-stock prior tone per author...", flush=True)
df2 = df2.sort_values(["author_id", "datetime"]).reset_index(drop=True)

df2["cum_sum"]   = df2.groupby("author_id")["tone"].cumsum()
df2["cum_count"] = df2.groupby("author_id").cumcount()  # posts BEFORE this one

df2["prior_sum"]   = df2.groupby("author_id")["cum_sum"].shift(1).fillna(0)
df2["prior_count"] = df2["cum_count"]

df2["prior_tone"] = np.where(
    df2["prior_count"] >= 3,
    df2["prior_sum"] / df2["prior_count"],
    np.nan
)
print(f"  Prior tone valid for {df2['prior_tone'].notna().sum():,} rows", flush=True)

# Explode tickers
df2["ticker_list"] = df2["ticker"].apply(lambda t: re.findall(r"[A-Z]{1,5}", str(t)))
df2_exp = df2.explode("ticker_list").dropna(subset=["ticker_list"])
df2_exp = df2_exp.rename(columns={"ticker_list": "ticker_clean"})

print("Computing tone shift per reply...", flush=True)
replies2 = df2_exp[["id", "parent_id", "tone", "prior_tone", "date", "ticker_clean"]].copy()
replies2 = replies2.rename(columns={
    "id":           "reply_id",
    "tone":         "reply_tone",
    "prior_tone":   "reply_prior_tone",
    "date":         "reply_date",
    "ticker_clean": "reply_ticker",
})

parents2 = df2_exp[["id", "date", "ticker_clean"]].drop_duplicates("id").copy()
parents2 = parents2.rename(columns={
    "id":           "parent_id",
    "date":         "parent_date",
    "ticker_clean": "parent_ticker",
})

merged2 = replies2.merge(parents2, on="parent_id", how="inner")
print(f"  Matched replies: {len(merged2):,}", flush=True)

merged2["tone_shift"] = merged2["reply_tone"] - merged2["reply_prior_tone"]
merged2 = merged2.dropna(subset=["tone_shift"])
print(f"  Valid tone shifts: {len(merged2):,}", flush=True)

sss_comment2 = (
    merged2.groupby(["parent_id", "parent_date", "parent_ticker"])
           .agg(
               sss_mean=("tone_shift", "mean"),
               sss_abs=("tone_shift", lambda x: x.abs().mean()),
               n_replies=("reply_id", "count"),
           )
           .reset_index()
)
sss_comment2 = sss_comment2.rename(columns={"parent_ticker": "ticker_list"})
sss_comment2["week_start"] = (
    sss_comment2["parent_date"] -
    pd.to_timedelta(sss_comment2["parent_date"].dt.dayofweek, unit="D")
)

agg2 = (
    sss_comment2
    .groupby(["ticker_list", "week_start"])
    .agg(
        sss_mean_tone_shift=("sss_mean",  "mean"),
        sss_abs_tone_shift =("sss_abs",   "mean"),
        n_comments         =("parent_id", "count"),
    )
    .reset_index()
    .rename(columns={"ticker_list": "ticker"})
)
print(f"  Rows: {len(agg2):,}", flush=True)

agg2.to_csv(OUT_SSS_AGNOSTIC, index=False)
print(f"\nSaved: {OUT_SSS_AGNOSTIC}  ({len(agg2):,} rows)", flush=True)
print(agg2.head(3).to_string())
print("\nSummary:")
print(agg2[["sss_mean_tone_shift","sss_abs_tone_shift","n_comments"]].describe().round(4).to_string())
