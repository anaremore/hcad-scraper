import requests
from bs4 import BeautifulSoup
import csv
import time
import os
import argparse
from datetime import datetime
import re

# Argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("--rate", type=float, default=1.0, help="Rate limit between requests (seconds)")
parser.add_argument("--limit", type=int, default=None, help="Limit number of accounts to process")
parser.add_argument("--taxyear", type=int, default=datetime.now().year, help="Tax year to scrape (default: current year)")
parser.add_argument("--debug", action="store_true", help="Enable debug mode")
args = parser.parse_args()

# Load account numbers
with open("accounts.txt") as f:
    account_numbers = [line.strip() for line in f if line.strip()]

if args.limit:
    account_numbers = account_numbers[:args.limit]

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Referer": "https://public.hcad.org/records/QuickSearch.asp",
    "Origin": "https://public.hcad.org",
    "Content-Type": "application/x-www-form-urlencoded"
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

        # Valuations (Appraised & Market)
        valuation_table = soup.find("th", string=lambda x: x and "Valuations" in x)
        appraised_current = appraised_previous = market_current = market_previous = "N/A"
        if valuation_table:
            rows = valuation_table.find_parent("table").find_all("tr")
            total_row = next((row for row in rows if "Total" in row.get_text()), None)
            if total_row:
                cells = total_row.find_all("td")
                market_previous = cells[1].get_text(strip=True).replace(",", "")
                appraised_previous = cells[2].get_text(strip=True).replace(",", "")
                market_current = cells[4].get_text(strip=True).replace(",", "")
                appraised_current = cells[5].get_text(strip=True).replace(",", "")

        # Percent Change Calculations
        def calc_pct(new, old):
            try:
                return round((float(new) - float(old)) / float(old) * 100, 2)
            except:
                return "N/A"

        appraised_pct = calc_pct(appraised_current, appraised_previous)
        market_pct = calc_pct(market_current, market_previous)

        # Land Area and Total Living Area
        land_area = total_living_area = "N/A"
        land_block = soup.find("td", string=lambda x: x and "Land Area" in x)
        if land_block:
            row = land_block.find_parent("tr").find_next_sibling("tr")
            if row:
                cells = row.find_all("td")
                land_area = re.sub(r"[^\d]", "", cells[0].get_text(strip=True))
                total_living_area = re.sub(r"[^\d]", "", cells[1].get_text(strip=True))

        print(f"✅ {account} | Appraised: {appraised_current} | Market: {market_current} | Land: {land_area} | Living: {total_living_area}")

        results.append({
            "Account Number": account,
            "Property Address": property_address,
            f"{args.taxyear} Appraised Value": appraised_current,
            f"{args.taxyear - 1} Appraised Value": appraised_previous,
            "Appraised % Change": appraised_pct,
            f"{args.taxyear} Market Value": market_current,
            f"{args.taxyear - 1} Market Value": market_previous,
            "Market % Change": market_pct,
            "Land Area": land_area,
            "Total Living Area": total_living_area
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
