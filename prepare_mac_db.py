import csv
import re
import os

INPUT  = "static_mac_database.csv"
OUTPUT = "assets/mac_vendors.csv"

def normalize_prefix(prefix):
    clean = re.sub(r'[:\-\.]', '', prefix.strip().upper())
    if len(clean) >= 6:
        return f"{clean[0:2]}:{clean[2:4]}:{clean[4:6]}"
    return None

count = 0
seen  = set()

os.makedirs("assets", exist_ok=True)

with open(INPUT, "r", encoding="utf-8", errors="replace") as fin, \
     open(OUTPUT, "w", encoding="utf-8", newline="") as fout:

    reader = csv.DictReader(fin)
    writer = csv.writer(fout)
    writer.writerow(["Mac Prefix", "Vendor Name"])

    for row in reader:
        prefix = normalize_prefix(row.get("Mac Prefix", ""))
        vendor = row.get("Vendor Name", "").strip()
        if prefix and vendor and prefix not in seen:
            seen.add(prefix)
            writer.writerow([prefix, vendor])
            count += 1

print(f"Kész! {count} gyártó mentve: {OUTPUT}")