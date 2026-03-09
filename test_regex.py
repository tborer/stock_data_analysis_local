import re

url = "https://www.stockwatch.com/News/Item/U-by1144152-U!SPTY-20260309/U/SPTY"
sw_match = re.search(r'U!([A-Za-z0-9.\-]+)-\d{8}', url)
if sw_match:
    print(f"Matched: {sw_match.group(1)}")
else:
    print("No match")
