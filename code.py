import os
import time
import requests
import pandas as pd
import io
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("COVALENT_API_KEY")
CSV_URL = (
    "https://docs.google.com/spreadsheets/"
    "d/1ZzaeMgNYnxvriYYpe8PE7uMEblTI0GV5GIVUnsP-sBs/"
    "export?format=csv"
)
CHAIN_ID = "1"
PAGE_SIZE = 100
SLEEP_BETWEEN = 0.2
TARGET_EVENTS = {"Mint", "Redeem", "Borrow", "RepayBorrow", "LiquidateBorrow"}
WEIGHTS = {"tx_count": 0.20, "net_borrow": 0.25, "liquidations": 0.30, "recency": 0.25}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def parse_timestamp(ts_str: str) -> int:
    if not ts_str:
        return 0
    iso = ts_str.rstrip("Z") + "+00:00"
    return int(datetime.fromisoformat(iso).timestamp())

def fetch_transactions(wallet: str) -> list:
    url = (
        f"https://api.covalenthq.com/v1/{CHAIN_ID}/address/"
        f"{wallet}/transactions_v3/"
        f"?quote-currency=USD&format=JSON&no-logs=false"
        f"&page-size={PAGE_SIZE}&key={API_KEY}"
    )
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json().get("data", {}).get("items", [])

def extract_features(wallet: str, txs: list, now_ts: int) -> dict:
    borrow = repay = liquidations = 0
    timestamps = []
    for tx in txs:
        ts = parse_timestamp(tx.get("block_signed_at_timestamp"))
        for log in tx.get("log_events", []):
            dec = log.get("decoded")
            if not dec:
                continue
            name = dec.get("name")
            if name not in TARGET_EVENTS:
                continue
            timestamps.append(ts)
            if name == "Borrow":
                borrow += 1
            elif name == "RepayBorrow":
                repay += 1
            elif name == "LiquidateBorrow":
                liquidations += 1
    if timestamps:
        time_since_last = now_ts - max(timestamps)
    else:
        time_since_last = now_ts
    return {
        "wallet_id": wallet,
        "tx_count": len(timestamps),
        "borrow_count": borrow,
        "repay_count": repay,
        "net_borrow": borrow - repay,
        "liquidations": liquidations,
        "time_since_last": time_since_last
    }

def normalize_series(s: pd.Series) -> pd.Series:
    return (s - s.min()) / (s.max() - s.min() + 1e-9)

def main():
    if not API_KEY:
        logger.error("Please set COVALENT_API_KEY in your .env file")
        return
    logger.info("Loading wallet list from Google Sheets...")
    r = requests.get(CSV_URL)
    r.raise_for_status()
    wallets = pd.read_csv(io.StringIO(r.text)).iloc[:,0].dropna().astype(str).tolist()
    logger.info(f"Found {len(wallets)} wallets.")
    now_ts = int(time.time())
    records = []
    for w in wallets:
        try:
            txs = fetch_transactions(w)
        except Exception as e:
            logger.warning(f"Failed to fetch for {w}: {e}")
            continue
        feats = extract_features(w, txs, now_ts)
        if feats["tx_count"] == 0:
            logger.info(f"No Compound events for {w}.")
        records.append(feats)
        time.sleep(SLEEP_BETWEEN)
    df = pd.DataFrame(records)
    df["n_tx"] = normalize_series(df["tx_count"])
    df["n_nb"] = normalize_series(df["net_borrow"])
    df["n_liq"] = normalize_series(df["liquidations"])
    df["n_rec"] = 1 - normalize_series(df["time_since_last"])
    df["score"] = (
        WEIGHTS["tx_count"] * df["n_tx"] +
        WEIGHTS["net_borrow"] * df["n_nb"] +
        WEIGHTS["liquidations"] * df["n_liq"] +
        WEIGHTS["recency"] * df["n_rec"]
    ) * 1000
    df["score"] = df["score"].round().astype(int)
    df.loc[df["tx_count"] == 0, "score"] = 0
    out = df[["wallet_id", "score"]].sort_values("score", ascending=False)
    out.to_csv("wallet_scores.csv", index=False)
    logger.info(" wallet_scores.csv written successfully.")
    print(out.head(10).to_string(index=False))

if __name__ == "__main__":
    main()
