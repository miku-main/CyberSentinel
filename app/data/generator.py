from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict
import hashlib
import ipaddress
import json
import random
import csv

RNG_SEED = 1337

@dataclass
class Scenario:
    name: str # "port_scan" | "ddos"
    start: datetime
    duration_s: int
    actor_ips: List[str]
    victim_ip: str

def _hash_flow(row: Dict[str, str]) -> str:
    m = hashlib.sha1()
    m.update("|".join(str(row[k]) for k in [
        "ts","src_ip","dst_ip","src_port","dst_port","proto","bytes","packets","tcp_flags","scenario"
    ]).encode())
    return m.hexdigest()[:12]

def _rand_ip(rng: random.Random, private: bool = True) -> str:
    if private:
        # 10.0.0.0/8
        return str(ipaddress.IPv4Address(rng.randint(0x0A000000, 0x0AFFFFFF)))
    else:
        return str(ipaddress.IPv4Address(rng.randint(0x0B000000, 0xDF000000)))
    
def generate_dataset(out_csv: Path, out_json: Path, *, minutes: int = 10) -> None:
    rng = random.Random(RNG_SEED)
    t0 = datetime(2025, 10, 30, 12, 0, 0, tzinfo=timezone.utc)

    normal_rows: List[Dict[str, str]] = []
    # Background normal traffic (~60 flows/min)
    for i in range(minutes * 60):
        ts = t0 + timedelta(seconds=i)
        for _ in range(rng.randint(30, 60)):
            src_ip = _rand_ip(rng)
            dst_ip = _rand_ip(rng)
            row = {
                "ts": ts.isoformat().replace("+00:00", "Z"),
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "src_port": rng.randint(1024, 65535),
                "dst_port": rng.choice([22, 80, 443, 3389, 53, rng.randint(1024, 65535)]),
                "proto": rng.choice(["TCP","UDP"]),
                "packets": rng.randint(2, 40),
                "bytes": rng.randint(200, 20000),
                "tcp_flags": rng.choice(["S", "SA", "PA", "FA", "RA"]),
                "scenario": "normal",
            }
            row["flow_id"] = _hash_flow(row)
            normal_rows.append(row)

    # Attack scenarios
    scenarios: List[Scenario] = []

    # Port scan: one actor hitting many dst_ports on a victim /24
    scan_start = t0 + timedelta(minutes=2)
    scan_actor = _rand_ip(rng)
    victim = "10.0.42.10"
    scenarios.append(Scenario("port_scan", scan_start, duration_s=60, actor_ips=[scan_actor], victim_ip=victim))

    scan_rows: List[Dict[str, str]] = []
    for s in range(200): # 200 flows over 60s
        ts = scan_start + timedelta(seconds=rng.randint(0, 59))
        row = {
            "ts": ts.isoformat().replace("+00:00", "Z"),
            "src_ip": scan_actor,
            "dst_ip": victim, 
            "src_port": rng.randint(1024, 65535),
            "dst_port": 10 + s, # sequential ports 10..209
            "proto": "TCP",
            "packets": rng.randint(1, 5),
            "bytes": rng.randint(50, 500),
            "tcp_flags": "S",
            "scenario": "port_scan",
        }
        row["flow_id"] = _hash_flow(row)
        scan_rows.append(row)

    # DDoS burst: many actors to one victim
    ddos_start = t0 + timedelta(minutes=6)
    victim2 = "10.0.99.5"
    actors = [_rand_ip(rng) for _ in range(50)]
    scenarios.append(Scenario("ddos", ddos_start, duration_s=45, actor_ips=actors, victim_ip=victim2))

    ddos_rows: List[Dict[str, str]] = []
    for s in range(600): # 600 small flows
        ts = ddos_start + timedelta(seconds=rng.randint(0, 44))
        row = {
            "ts": ts.isoformat().replace("+00:00", "Z"),
            "tsp_ip": rng.choice(actors),
            "dst_ip": victim2,
            "src_port": rng.randint(1024, 65535),
            "dst_port": 443,
            "proto": "TCP",
            "packets": rng.randint(1, 3),
            "bytes": rng.randint(40, 300),
            "tcp_flags": "S",
            "scerario": "ddos",
        }
        row["flow_id"] = _hash_flow(row)
        ddos_rows.append(row)

    rows = normal_rows + scan_rows + ddos_rows

    # Write CSV
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # Write scenarios JSON
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w") as f:
        json.dump([
            {
                "name": s.name,
                "start": s.start.isoformat().replace("+00:00", "Z"),
                "duration_s": s.duration_s,
                "actor_ips": s.actor_ips,
                "victim_ip": s.victim_ip,
            }
            for s in scenarios
        ], f, indent=2)

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    csv_path = root / "demos" / "traffic_small.csv"
    json_path = root / "demos" / "attacks_scenarios.json"
    generate_dataset(csv_path, json_path)
    print(f"Wrote {csv_path} and {json_path}")