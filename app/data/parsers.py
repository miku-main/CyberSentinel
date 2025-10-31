from __future__ import annotations
from pathlib import Path
import pandas as pd

REQUIRED_COLS = [
    "ts","src_ip","dst_ip","src_port","dst_port","proto","packets","bytes","tcp_flags","scenario","flow_id"
]

def load_flows(csv_path: Path | str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    
    # basic dtype cleanup
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df["src_port"] = df["src_port"].astype("int32")
    df["dst_port"] = df["dst_port"].astype("int32")
    df["packets"] = df["packets"].astype("int32")
    df["bytes"] = df["bytes"].astype("int32")
    return df