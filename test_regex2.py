import re
from datetime import datetime

text = "Mar 22, 2026, 10:26 ET"
# Let's see if there's any text around it or if it requires a specific regex
regex = r'([A-Za-z]{3} \d{1,2}, \d{4}, \d{2}:\d{2} ET)'
match = re.search(regex, text)
print("Regex Match:", match.group(1) if match else "None")

date_format = "%b %d, %Y, %H:%M ET"
if match:
    parsed_date = datetime.strptime(match.group(1), date_format)
    print("Parsed Date:", parsed_date)
