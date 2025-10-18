import argparse
import asyncio
import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, Tuple, Optional

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed
from solders.pubkey import Pubkey

from jlp.accounts import Custody  # generated via anchorpy client-gen

# ----------------------------
# Chain constants & endpoints
# ----------------------------
USD_DECIMALS = 6
JLP_TOKEN_MINT = "27G8MtK7VtTcCHkpASjSDdkWWYfoqT6ggEuKidVJidD4"
RPC_ENDPOINT = "https://api.mainnet-beta.solana.com"
NETWORK = "mainnet-beta"

# Custody mapping (symbol -> pubkey)
# WBTC custody treated as BTC exposure for hedging.
CUSTODIES: Tuple[Tuple[str, str], ...] = (
    ("SOL",  "7xS2gz2bTp3fwCC7knJvUWTEU9Tycczu6VhJYKgi1wdz"),
    ("BTC",  "5Pv3gM9JrFFH883SWAhvJC9RPYmo8UNxuFtv5bMMALkm"),
    ("ETH",  "AQCGyheWPLeo6Qp9WpYS9m3Qj479t7R636N9ey1rEjEn"),
)

VOLATILE = {"SOL", "BTC", "ETH"}


# ----------------------------
# Helpers
# ----------------------------
def scale(val, decimals) -> float:
    return float(val) / float(10 ** decimals)


def safe_div(a: float, b: float, fallback: float = 0.0) -> float:
    return a / b if b else fallback


def human(n: float) -> str:
    if abs(n) >= 1000:
        return f"{n:,.2f}"
    return f"{n:,.6f}"


# ----------------------------
# Result container
# ----------------------------
@dataclass
class HedgeResult:
    network: str
    timestamp_ns: int
    supply: float
    pool_exposure_tokens: Dict[str, float]     # pool-level exposure in tokens (signed)
    per_1000jlp_short: Dict[str, float]        # normalized per-1000 JLP (signed)
    per_token_short: Optional[Dict[str, float]] = None  # user-specific hedge (signed), optional
    sign_convention: str = "+ve = SHORT, -ve = LONG"


# ----------------------------
# Core logic
# ----------------------------
async def _fetch_supply(client: AsyncClient) -> float:
    resp = await client.get_token_supply(Pubkey.from_string(JLP_TOKEN_MINT))
    return float(resp.value.ui_amount)


async def _fetch_custodies(client: AsyncClient) -> Dict[str, Custody]:
    pubkeys = [Pubkey.from_string(pk) for _, pk in CUSTODIES]
    accs = await Custody.fetch_multiple(client, pubkeys, commitment=Processed)
    return {sym: acc for (sym, _), acc in zip(CUSTODIES, accs)}


def _pool_exposure_tokens(custodies: Dict[str, Custody]) -> Dict[str, float]:
    """
    Pool exposure in token units for SOL, BTC (WBTC), ETH.

    exposure_tokens = (owned - locked) + (short_notional / short_avg_price)

    - (owned - locked) = unlocked inventory → pool long this amount
    - short_notional / short_avg_price = short_qty → trader shorts make pool long
    The sign of exposure reflects the pool's delta:
      +ve  → pool long  → to hedge: SHORT that many tokens
      -ve  → pool short → to hedge: LONG  that many tokens
    """
    out: Dict[str, float] = {}

    for symbol, custody in custodies.items():
        if symbol not in VOLATILE:
            continue

        dec = int(custody.decimals)
        owned = scale(custody.assets.owned, dec)
        locked = scale(custody.assets.locked, dec)

        short_notional_usd = scale(custody.assets.global_short_sizes, USD_DECIMALS)
        short_avg_price_usd = scale(custody.assets.global_short_average_prices, USD_DECIMALS)

        short_qty = safe_div(short_notional_usd, short_avg_price_usd, 0.0)
        unlocked = owned - locked

        exposure_tokens = unlocked + short_qty
        out[symbol] = exposure_tokens

    return out


async def compute_hedge_amounts(my_jlp_tokens: Optional[float]) -> HedgeResult:
    """
    If my_jlp_tokens is provided: compute user-specific hedge.
    If None: return only pool exposure and per-1000 JLP hedge.
    """
    client = AsyncClient(RPC_ENDPOINT)
    try:
        supply, custodies = await asyncio.gather(
            _fetch_supply(client),
            _fetch_custodies(client),
        )
        pool_exp = _pool_exposure_tokens(custodies)

        ts_ns = time.time_ns()

        # Normalize per 1,000 JLP (signed). Shows short(+) / long(-) per 1k JLP.
        per_1000jlp_short = {sym: safe_div(qty, supply, 0.0) * 1000.0 for sym, qty in pool_exp.items()}

        per_token_short: Optional[Dict[str, float]] = None
        if my_jlp_tokens is not None:
            share = safe_div(my_jlp_tokens, supply, 0.0)
            per_token_short = {sym: qty * share for sym, qty in pool_exp.items()}

        return HedgeResult(
            network=NETWORK,
            timestamp_ns=ts_ns,
            supply=supply,
            pool_exposure_tokens=pool_exp,
            per_1000jlp_short=per_1000jlp_short,
            per_token_short=per_token_short,
        )
    finally:
        await client.close()


# ----------------------------
# CLI & API
# ----------------------------
def to_jsonable(res: HedgeResult) -> Dict:
    """
    Produce a stable, friendly JSON dict without dataclass internals.
    """
    out = {
        "network": res.network,
        "timestamp_ns": res.timestamp_ns,
        "supply": res.supply,
        "pool_exposure_tokens": res.pool_exposure_tokens,
        "per_1000jlp_short": res.per_1000jlp_short,
        "sign_convention": res.sign_convention,
    }
    if res.per_token_short is not None:
        out["per_token_short"] = res.per_token_short
    return out


async def _run_cli(args):
    res = await compute_hedge_amounts(args.jlp)

    if args.json:
        print(json.dumps(to_jsonable(res), separators=(",", ":"), sort_keys=True))
        return

    # Human-friendly output
    print(f"Network: {NETWORK}")
    print(f"Supply: {human(res.supply)} JLP\n")

    print("Pool exposure (tokens)  [ +ve = SHORT to hedge | -ve = LONG to hedge ]:")
    for sym in ("SOL", "BTC", "ETH"):
        qty = res.pool_exposure_tokens.get(sym, 0.0)
        print(f"  {sym:<3}: {human(qty)}")

    if res.per_token_short is not None:
        print(f"\nYour JLP: {human(args.jlp)}")
        print("Your delta hedge (signed; +ve SHORT / -ve LONG):")
        for sym in ("SOL", "BTC", "ETH"):
            qty = res.per_token_short.get(sym, 0.0)
            print(f"  {sym:<3}: {human(qty)}")
    else:
        print("\n(JLP not provided; showing normalized hedge only)")

    print("\nPer 1,000 JLP hedge (signed; +ve SHORT / -ve LONG):")
    for sym in ("SOL", "BTC", "ETH"):
        qty = res.per_1000jlp_short.get(sym, 0.0)
        print(f"  {sym:<3}: {human(qty)}")


def _build_api_app():
    from fastapi import FastAPI, Query
    app = FastAPI(title="jlp-delta-hedger", version="1.0.0")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/hedge")
    async def hedge(jlp: Optional[float] = Query(default=None, description="JLP tokens to hedge (optional)")):
        res = await compute_hedge_amounts(jlp)
        return to_jsonable(res)

    return app


def _serve_api(host: str, port: int):
    import uvicorn
    app = _build_api_app()
    uvicorn.run(app, host=host, port=port, log_level="info")


def _parse_args():
    p = argparse.ArgumentParser(
        description="Compute per-asset hedge to delta-neutralize a JLP position. "
                    "If --jlp is omitted, prints per-1000 JLP hedge amounts."
    )
    p.add_argument("--jlp", type=float, required=False,
                   help="Your JLP token amount (e.g., 12500). If omitted, only per-1000 JLP values are returned.")
    p.add_argument("--json", action="store_true",
                   help="Output machine-readable JSON to stdout.")
    p.add_argument("--serve", action="store_true",
                   help="Run an HTTP API server instead of CLI output.")
    p.add_argument("--host", type=str, default="127.0.0.1",
                   help="API server host (default 127.0.0.1).")
    p.add_argument("--port", type=int, default=8000,
                   help="API server port (default 8000).")
    return p.parse_args()


def main():
    args = _parse_args()
    if args.serve:
        _serve_api(args.host, args.port)
    else:
        asyncio.run(_run_cli(args))


if __name__ == "__main__":
    main()
