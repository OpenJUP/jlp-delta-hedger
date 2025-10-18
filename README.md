# 🔧 JLP Delta Hedger  
Smart risk management for JLP exposure. Real numbers. Real hedging.

[![Built for Solana](https://img.shields.io/badge/Solana-Mainnet-purple.svg)]() 
[![Delta Neutral](https://img.shields.io/badge/Strategy-Delta%20Hedge-blue.svg)]()
[![Open Source](https://img.shields.io/badge/License-MIT-green.svg)]()

The **JLP Delta Hedger** calculates **how much SOL, BTC, and ETH you need to short or long** to **hedge your JLP position** and stay **delta neutral**. It pulls live on-chain position data directly from the **JLP program on Solana**—fast, precise, and up to date.

Perfect for:
- Market makers ✅
- Passive JLP LPs ✅
- Automated traders & bots ✅
- Risk managers ✅

---

## ✨ What It Does

JLP pools assets and market risk. When you hold JLP tokens, you inherit exposure to:
- ✅ Unhedged inventory (unlocked tokens inside the pool)
- ✅ Trader short positions (which make the pool **long**)
  
This tool computes **your exact exposure per asset** and tells you **how much to hedge**:

| Output | Meaning |
|--------|---------|
| Pool Exposure | Total net asset delta in the pool |
| Per 1,000 JLP Hedge | Token hedge required for each 1,000 JLP |
| Your Hedge | Based on your JLP holdings |

---

## 🚀 Quick Start

### ✅ Install

```bash
git clone https://github.com/OpenJUP/jlp-delta-hedger.git
cd jlp-delta-hedger
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
````

---

## ⚡ CLI Mode

### Show pool exposure & per-1,000 JLP hedge

```bash
python hedge.py
```

```
Network: mainnet-beta
Supply: 395,567,535.614754 JLP

Pool exposure (tokens)  [ +ve = SHORT to hedge | -ve = LONG to hedge ]:
  SOL: 4,501,577.69
  BTC: 118.42
  ETH: 14,702.91

Per 1,000 JLP hedge (signed):
  SOL: 11.387
  BTC: 0.0003
  ETH: 0.0372
```

---

### Hedge a specific JLP position

```bash
python hedge.py --jlp 25000
```

```
Your delta hedge (SHORT + / LONG -):
  SOL: 284.675
  BTC: 0.007
  ETH: 0.931
```

---

### JSON mode for trading bots 🤖

```bash
python hedge.py --jlp 25000 --json
```

```json
{
  "network": "mainnet-beta",
  "timestamp_ns": 1760743598385145260,
  "supply": 395567535.614754,
  "pool_exposure_tokens": {"SOL": 4501577.69, "BTC": 118.42, "ETH": 14702.91},
  "per_1000jlp_short": {"SOL": 11.387, "BTC": 0.0003, "ETH": 0.0372},
  "per_token_short": {"SOL": 284.675, "BTC": 0.007, "ETH": 0.931},
  "sign_convention": "+ve = SHORT, -ve = LONG"
}
```

---

## 🌐 API Mode (FastAPI server)

Start the API server:

```bash
python hedge.py --serve --host 0.0.0.0 --port 8000
```

Then query it:

```
GET /hedge
GET /hedge?jlp=25000
GET /health
```

Example:

```bash
curl "http://localhost:8000/hedge?jlp=25000"
```

---

## 🔢 How It Works

For each token (**SOL**, **BTC** (WBTC), **ETH**):

```
exposure_tokens = (owned - locked) + (short_notional_usd / short_avg_price_usd)
my_hedge_tokens = exposure_tokens * (my_jlp / total_supply)
```

* `+` means **SHORT** this many tokens
* `–` means **LONG** this many tokens
* Fully captures exposure from:
  ✅ Inventory (owned–locked)
  ✅ Trader shorts (short_qty = notional/avg_price)

---

## 📦 Project Structure

```
jlp-delta-hedger/
├── hedge.py                # CLI + API hedging
├── jlp/                    # Anchor-generated client for JLP program
├── requirements.txt
└── README.md
```

---

## 🔧 Optional: Update Anchor client

```bash
anchor idl fetch PERPHjGBqRHArX4DySjwM6UJHiR3sWAatqfdBS2qQJu -o PERP.idl
anchorpy client-gen PERP.idl ./jlp --program-id PERPHjGBqRHArX4DySjwM6UJHiR3sWAatqfdBS2qQJu
```

---

## 🛡️ Disclaimer

This project is provided **as-is** for educational and research purposes.
It is **not financial advice**. Use hedging strategies responsibly.

---

## 💪 Contributions Welcome

Got ideas? Want to add Bybit/Kraken price hedging? API trading hooks? PRs welcome.
Let’s build serious DeFi infrastructure together. 🧠⚡
