import requests
from bs4 import BeautifulSoup
import csv
import time
import os
import argparse
from datetime import datetime

# Argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("--rate", type=float, default=1.0, help="Rate limit between requests (seconds)")
parser.add_argument("--limit", type=int, default=None, help="Limit number of accounts to process")
parser.add_argument("--debug", action="store_true", help="Enable debug mode")
parser.add_argument("--taxyear", type=int, default=datetime.now().year, help="Tax year (default: current year)")
args = parser.parse_args()

# Load account numbers
with open("accounts.txt") as f:
    account_numbers = [line.strip() for line in f if line.strip()]

if args.limit:
    account_numbers = account_numbers[:args.limit]

session = requests.Session()
session.headers.update({
    "Referer": "https://public.hcad.org/records/QuickSearch.asp",
    "Origin": "https://public.hcad.org",
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
})

# Create debug_html directory
if args.debug and not os.path.exists("debug_html"):
    os.makedirs("debug_html")

results = []

for i, account in enumerate(account_numbers, 1):
    data = {
        "TaxYear": str(args.taxyear),
        "searchtype": "strap",
        "searchval": account
    }

    try:
        response = session.post("https://public.hcad.org/records/QuickRecord.asp", data=data, timeout=15)
        response.raise_for_status()
        html = response.text

        if args.debug:
            debug_file = f"debug_html/{account}.html"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"[DEBUG] Saved HTML for account {account} to {debug_file}")

        soup = BeautifulSoup(html, "html.parser")

        # Property Address
        prop_addr_block = soup.find("td", string=lambda x: x and "Property Address" in x)
        property_address = prop_addr_block.find_next("th").get_text(separator=" ", strip=True) if prop_addr_block else "N/A"

        # Valuations (Appraised and Market)
        valuation_table = soup.find("th", string=lambda x: x and "Valuations" in x)
        if valuation_table:
            total_row = valuation_table.find_parent("table").find_all("tr")[-3]
            cells = total_row.find_all("td")

            appraised_prev = cells[2].get_text(strip=True).replace(",", "")
            appraised_curr = cells[5].get_text(strip=True).replace(",", "")
            market_prev = cells[1].get_text(strip=True).replace(",", "")
            market_curr = cells[4].get_text(strip=True).replace(",", "")
        else:
            print(f"[DEBUG] Valuation table not found for {account}")
            appraised_prev = appraised_curr = market_prev = market_curr = "N/A"

        # Percent Changes
        def calc_pct_change(current, previous):
            try:
                return round((float(current) - float(previous)) / float(previous) * 100, 2)
            except:
                return "N/A"

        pct_appraised = calc_pct_change(appraised_curr, appraised_prev)
        pct_market = calc_pct_change(market_curr, market_prev)

        print(f"✅ {account} | {args.taxyear} Appraised: {appraised_curr} | Prev Appraised: {appraised_prev} | % Change: {pct_appraised} | {args.taxyear} Market: {market_curr} | Prev Market: {market_prev} | % Change: {pct_market}")

        results.append({
            "Account Number": account,
            "Property Address": property_address,
            f"{args.taxyear} Appraised Value": appraised_curr,
            f"{args.taxyear - 1} Appraised Value": appraised_prev,
            "% Change Appraised": pct_appraised,
            f"{args.taxyear} Market Value": market_curr,
            f"{args.taxyear - 1} Market Value": market_prev,
            "% Change Market": pct_market
        })

    except Exception as e:
        print(f"Error fetching {account}: {e}")

    time.sleep(args.rate)

# Save results to CSV
with open("hcad_results.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

print(f"\n🎉 Scraping complete! {len(results)} records saved to hcad_results.csv")
