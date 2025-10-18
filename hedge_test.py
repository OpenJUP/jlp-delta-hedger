import argparse
import asyncio
import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, Tuple, Optional, List

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed
from solders.pubkey import Pubkey

# If you prefer importing addresses/helpers from hedge.py, you can replace these duplicates with:
# from hedge import JLP_TOKEN_MINT, RPC_ENDPOINT, USD_DECIMALS, CUSTODIES
# and the scale/safe_div functions.

# ----------------------------
# Chain constants & endpoints
# ----------------------------
USD_DECIMALS = 6
JLP_TOKEN_MINT = "27G8MtK7VtTcCHkpASjSDdkWWYfoqT6ggEuKidVJidD4"
RPC_ENDPOINT = "https://api.mainnet-beta.solana.com"
NETWORK = "mainnet-beta"

# Custody mapping (symbol -> pubkey)
# WBTC custody is represented as BTC exposure for hedging purposes.
CUSTODIES: Tuple[Tuple[str, str], ...] = (
    ("SOL",  "7xS2gz2bTp3fwCC7knJvUWTEU9Tycczu6VhJYKgi1wdz"),
    ("BTC",  "5Pv3gM9JrFFH883SWAhvJC9RPYmo8UNxuFtv5bMMALkm"),
    ("ETH",  "AQCGyheWPLeo6Qp9WpYS9m3Qj479t7R636N9ey1rEjEn"),
)

VOLATILE = {"SOL", "BTC", "ETH"}

# ----------------------------
# Anchor-generated types (lightweight import)
# ----------------------------
from jlp.accounts import Custody  # ensure jlp/ is generated in the repo (see README)


# ----------------------------
# Helpers
# ----------------------------
def scale(val, decimals) -> float:
    return float(val) / float(10 ** decimals)


def safe_div(a: float, b: float, fallback: float = 0.0) -> float:
    return a / b if b else fallback


def human(n: float, big: int = 1000) -> str:
    if abs(n) >= big:
        return f"{n:,.2f}"
    return f"{n:,.6f}"


# ----------------------------
# Data classes
# ----------------------------
@dataclass
class TokenBreakdown:
    token: str
    decimals: int
    owned_tokens: float
    locked_tokens: float
    unlocked_tokens: float
    short_notional_usd: float
    short_avg_price_usd: float
    short_qty_tokens: float
    pool_exposure_tokens: float  # unlocked + short_qty
    per_1000jlp_tokens: float
    my_hedge_tokens: Optional[float]  # signed (+ = SHORT, - = LONG)

@dataclass
class HedgeTestResult:
    network: str
    timestamp_ns: int
    supply: float
    jlp_input: Optional[float]
    sign_convention: str
    tokens: List[TokenBreakdown]


# ----------------------------
# Chain fetch
# ----------------------------
async def _fetch_supply(client: AsyncClient) -> float:
    resp = await client.get_token_supply(Pubkey.from_string(JLP_TOKEN_MINT))
    return float(resp.value.ui_amount)


async def _fetch_custodies(client: AsyncClient) -> Dict[str, Custody]:
    pubkeys = [Pubkey.from_string(pk) for _, pk in CUSTODIES]
    accs = await Custody.fetch_multiple(client, pubkeys, commitment=Processed)
    return {sym: acc for (sym, _), acc in zip(CUSTODIES, accs)}


# ----------------------------
# Core breakdown logic
# ----------------------------
async def compute_breakdown(my_jlp_tokens: Optional[float], only_token: Optional[str]) -> HedgeTestResult:
    client = AsyncClient(RPC_ENDPOINT)
    try:
        supply, custodies = await asyncio.gather(
            _fetch_supply(client),
            _fetch_custodies(client),
        )
        ts_ns = time.time_ns()

        # Normalize filter token symbol, if provided
        only = only_token.upper() if only_token else None

        rows: List[TokenBreakdown] = []

        for symbol, custody in custodies.items():
            if symbol not in VOLATILE:
                continue
            if only and symbol != only:
                continue

            dec = int(custody.decimals)

            owned = scale(custody.assets.owned, dec)
            locked = scale(custody.assets.locked, dec)
            unlocked = owned - locked

            short_notional_usd = scale(custody.assets.global_short_sizes, USD_DECIMALS)
            short_avg_price_usd = scale(custody.assets.global_short_average_prices, USD_DECIMALS)
            short_qty = safe_div(short_notional_usd, short_avg_price_usd, 0.0)

            pool_exposure = unlocked + short_qty
            per_1000 = safe_div(pool_exposure, supply, 0.0) * 1000.0

            my_hedge = None
            if my_jlp_tokens is not None:
                share = safe_div(my_jlp_tokens, supply, 0.0)
                my_hedge = pool_exposure * share  # signed: + = SHORT, - = LONG

            rows.append(TokenBreakdown(
                token=symbol,
                decimals=dec,
                owned_tokens=owned,
                locked_tokens=locked,
                unlocked_tokens=unlocked,
                short_notional_usd=short_notional_usd,
                short_avg_price_usd=short_avg_price_usd,
                short_qty_tokens=short_qty,
                pool_exposure_tokens=pool_exposure,
                per_1000jlp_tokens=per_1000,
                my_hedge_tokens=my_hedge,
            ))

        return HedgeTestResult(
            network=NETWORK,
            timestamp_ns=ts_ns,
            supply=supply,
            jlp_input=my_jlp_tokens,
            sign_convention="+ve = SHORT, -ve = LONG",
            tokens=rows
        )
    finally:
        await client.close()


# ----------------------------
# Output formatters
# ----------------------------
def print_human(res: HedgeTestResult):
    print(f"Network: {res.network}")
    print(f"Timestamp (ns): {res.timestamp_ns}")
    print(f"Supply: {human(res.supply)} JLP")
    if res.jlp_input is None:
        print("JLP input: (none provided; showing per-1000 JLP only)")
    else:
        print(f"JLP input: {human(res.jlp_input)}")
    print(f"Sign convention: {res.sign_convention}")
    print("")

    for row in res.tokens:
        print(f"=== {row.token} Breakdown ===")
        print(f"Decimals:                  {row.decimals}")
        print(f"Owned (tokens):            {human(row.owned_tokens)}")
        print(f"Locked (tokens):           {human(row.locked_tokens)}")
        print(f"Unlocked (owned - locked): {human(row.unlocked_tokens)}")
        print("")
        print(f"Short Notional (USD):      {human(row.short_notional_usd)}")
        print(f"Short Avg Price (USD):     {human(row.short_avg_price_usd)}")
        print(f"Short Qty (tokens):        {human(row.short_qty_tokens)}   <-- = notional / avg_price")
        print("")
        print(f"POOL EXPOSURE (tokens):    {human(row.pool_exposure_tokens)}   <-- = unlocked + short_qty")
        print(f"Per 1,000 JLP (tokens):    {human(row.per_1000jlp_tokens)}")
        if row.my_hedge_tokens is not None:
            direction = "SHORT" if row.my_hedge_tokens >= 0 else "LONG"
            print(f"Your hedge (tokens):       {human(row.my_hedge_tokens)}   ({direction})")
        print("")


def to_json(res: HedgeTestResult) -> Dict:
    return {
        "network": res.network,
        "timestamp_ns": res.timestamp_ns,
        "supply": res.supply,
        "jlp_input": res.jlp_input,
        "sign_convention": res.sign_convention,
        "tokens": [
            {
                "token": t.token,
                "decimals": t.decimals,
                "owned_tokens": t.owned_tokens,
                "locked_tokens": t.locked_tokens,
                "unlocked_tokens": t.unlocked_tokens,
                "short_notional_usd": t.short_notional_usd,
                "short_avg_price_usd": t.short_avg_price_usd,
                "short_qty_tokens": t.short_qty_tokens,
                "pool_exposure_tokens": t.pool_exposure_tokens,
                "per_1000jlp_tokens": t.per_1000jlp_tokens,
                "my_hedge_tokens": t.my_hedge_tokens,
            } for t in res.tokens
        ]
    }


# ----------------------------
# CLI
# ----------------------------
def parse_args():
    p = argparse.ArgumentParser(
        description="Explain and verify the JLP hedge math step-by-step. "
                    "Omit --jlp to see per-1000 JLP only."
    )
    p.add_argument("--jlp", type=float, required=False,
                   help="Your JLP tokens (optional). If omitted, only per-1000 JLP values are shown.")
    p.add_argument("--token", type=str, required=False, choices=["SOL", "BTC", "ETH"],
                   help="Focus on a single token (SOL, BTC, or ETH).")
    p.add_argument("--json", action="store_true",
                   help="Emit machine-readable JSON instead of human text.")
    return p.parse_args()


def main():
    args = parse_args()
    res = asyncio.run(compute_breakdown(args.jlp, args.token))
    if args.json:
        print(json.dumps(to_json(res), separators=(",", ":"), sort_keys=True))
    else:
        print_human(res)


if __name__ == "__main__":
    main()
