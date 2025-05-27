# 🏠 HCAD Scraper

A Python scraper for Harris County Appraisal District (HCAD) property data. Extracts appraised and market values for specified account numbers and computes year-over-year percentage changes.

## 📋 Features

* Pulls:
  * Appraised Value (Current and Previous Year)
  * Market Value (Current and Previous Year)
  * Property Address
  * Percent Change for Appraised and Market Values
* Supports:
  * Rate limiting
  * Debug mode (saves raw HTML for inspection)
  * Custom tax year (--taxyear)
  * CSV export

## 🚀 Setup

### 📦 Install Dependencies

Make sure you have Python 3 installed. Install required libraries:

```bash
pip install requests beautifulsoup4
```

### 📝 Prepare `accounts.txt`

Create a file named `accounts.txt` with one HCAD Account Number per line, like:

```python-repl
1234567890123
9876543210987
...
```

### 🔍 Pulling Account Numbers from HCAD

1. Go to: https://hcad.org/property-search/property-search/
2. Select Advanced Search.
3. Choose your filters (e.g., Tax Year, Neighborhood, Property Type).
4. Click Submit.
5. In the results table, right-click the account number links, copy them, and paste into `accounts.txt`.

Example account numbers:
* 1234567890123
* 9876543210987

> 💡 Tip: Account numbers are typically 13 digits.

## 🛠️ Usage

Run the script with:

```bash
python hcad-scraper.py [options]
```

### Options

| Option | Description | Example |
|--------|-------------|---------|
| --rate | Delay between requests (in seconds) | --rate 2 (default: 1) |
| --limit | Limit number of accounts to process | --limit 10 |
| --taxyear | Specify tax year (default: current) | --taxyear 2024 |
| --debug | Enable debug mode (saves HTML files) | --debug |

### Example

```bash
python hcad-scraper.py --rate 2 --limit 5 --taxyear 2025 --debug
```

## 📊 Output

A CSV file `hcad_results.csv` is generated with:

| Account Number | Property Address | 2025 Appraised Value | 2024 Appraised Value | % Change Appraised | 2025 Market Value | 2024 Market Value | % Change Market |
|----------------|------------------|----------------------|----------------------|--------------------|-------------------|-------------------|-----------------|
| 1234567890123 | 123 MAIN ST | 450,000 | 400,000 | 12.50% | 450,000 | 400,000 | 12.50% |
| — | — | — | — | — | — | — | — |

## 🔧 Notes

* HCAD may throttle or block requests after too many hits. Use a reasonable `--rate` (e.g., 2+ seconds).
* Debug mode (`--debug`) saves HTML for troubleshooting in the `debug_html/` folder.

## 📜 Disclaimer

This project is for educational purposes. Always respect website terms of service and local laws.
