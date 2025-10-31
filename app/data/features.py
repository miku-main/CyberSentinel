from __future__ import annotations
import numpy as np
import pandas as pd

# Helper: shannon entropy of a series of ints/strings

def shannon_entropy(values: pd.Series) -> float:
    if len(values) == 0:
        return 0.0
    counts = values.value_counts(normalize=True)
    probs = counts.values
    return float(-(probs * np.log2(probs + 1e-12)).sum())

def add_basic_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["bytes_per_packet"] = (df["bytes"] / df["packets"]).replace([np.inf, -np.inf], 0).fillna(0)
    return df

def add_window_features(df: pd.DataFrame, window_s: int = 60) -> pd.DataFrame:
    df = df.sort_values("ts").copy()
    df.set_index("ts", inplace=True)

    # Packet rate per src_ip over window
    pkt_rate = (
        df.groupby("src_ip")["packets"]
          .rolling(f"{window_s}s").sum()
          .rename("pkt_rate_src")
    )

    # Unique dst_ports per src_ip over window (port scan heuristic)
    uniq_ports = (
        df.groupby("src_ip")["dst_port"]
          .rolling(f"{window_s}s").apply(lambda s: s.nunique(), raw=False)
          .rename("uniq_dst_ports_src")
    )

    # Entropy of dst_port per src_ip over window
    entropy_ports = (
        df.groupby("src_ip")["dst_port"]
          .rolling(f"{window_s}s").apply(lambda s: shannon_entropy(s), raw=False)
          .rename("entropy_dst_port_src")
    )

    # Fill back to rows
    feats = pd.concat([pkt_rate, uniq_ports, entropy_ports], axis=1).reset_index(level=0, drop=True)
    out = df.reset_index().join(feats)

    # Replace NaNs introduced by short windows
    for c in ["pkt_rate_src", "uniq_dst_ports_src", "entropy_dst_port_src"]:
        out[c] = out[c].fillna(0.0)
    return out