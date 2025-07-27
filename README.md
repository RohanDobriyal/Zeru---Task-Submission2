# Wallet Risk Scoring From Scratch

This repository implements an end-to-end workflow to evaluate the on-chain **risk exposure** of Ethereum wallets by analyzing their interactions with the Compound protocol (V2/V3).

## Overview

1. **Fetch Transaction History**: Retrieves protocol events (`Mint`, `Redeem`, `Borrow`, `RepayBorrow`, `LiquidateBorrow`) for each wallet via the Covalent API.
2. **Feature Extraction**: Computes counts of each event type, net borrow activity, and recency of the last event.
3. **Risk Scoring**: Normalizes each feature, applies configurable weights, and scales the weighted sum to an integer score between **0** and **1000**.
4. **Output**: Generates `wallet_scores.csv`, sorted by descending risk score, and verifies that all input wallet IDs appear exactly once.

## Features

- Deduplicates input wallet addresses and logs any duplicates removed.
- Handles wallets with zero protocol activity by assigning a score of **0**.
- Logs fetch errors per wallet without interrupting the batch.
- Verifies post-export that the output IDs exactly match the source list.

## Prerequisites

- **Python 3.7+**
- **Covalent API Key** (free signup): https://www.covalenthq.com/
- Git (for cloning and version control)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/RohanDobriyal/Zeru---Task-Submission2.git
   cd Zeru---Task-Submission2
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # macOS/Linux
   .\.venv\Scripts\activate   # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install pandas requests python-dotenv
   ```

## Configuration

1. **Create a `.env` file** in the project root:
   ```ini
   COVALENT_API_KEY=YOUR_COVALENT_API_KEY
   ```
  or you can use my api key in the code

2. **(Optional)** Update the Google Sheets URL in `wallet_risk_scoring.py` if you host your own wallet list.

## Usage

Run the main script:

```bash
python wallet_risk_scoring.py
```

The script will:

- Load and dedupe wallet addresses from the configured CSV URL.
- Fetch and decode Compound events for each address.
- Compute and normalize features, then calculate the final score.
- Write `wallet_scores.csv` with columns `wallet_id,score`.
- Log any missing or extra wallet IDs relative to the source.

## Output

- **wallet_scores.csv**: CSV file sorted by descending `score`.

Sample:
```
wallet_id,score
0x9e6ec4e98793970a1307262ba68d37594e58cd78,629
...
0x0039f22efb07a647557c7c5d17854cfd6d489ef3,0
```
