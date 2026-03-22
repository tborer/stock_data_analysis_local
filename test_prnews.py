import requests
from bs4 import BeautifulSoup

url = "https://www.prnewswire.com/news-releases/optimax-eyewear-group-boosts-us-manufacturing-capacity-by-50-following-30-yoy-growth-302721499.html"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

response = requests.get(url, headers=headers)
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Title
    h1 = soup.find('h1')
    print(f"\n--- TITLE ---")
    print(h1.text.strip() if h1 else "No H1 found")
    
    # Date
    print(f"\n--- DATE ---")
    time_tags = soup.find_all('time')
    for t in time_tags:
        print(f"Time tag: {t.text.strip()} | datetime: {t.get('datetime')}")
    
    mb_no = soup.select('.mb-no')
    if mb_no:
        print(f".mb-no text: {mb_no[0].text.strip()}")
        
    date_p = soup.select('p.mb-no')
    if date_p:
        print(f"p.mb-no text: {date_p[0].text.strip()}")
        
    # Content
    print(f"\n--- CONTENT ---")
    release_body = soup.select_one('.release-body')
    if release_body:
        print(f"Found .release-body! Length: {len(release_body.text)}")
        print(release_body.text[:200].strip().replace('\n', ' ') + "...")
    else:
        article = soup.find('article')
        if article:
            print(f"Found article tag: {len(article.text)}")
        else:
            print("Trying to find section or main content...")
            section = soup.select_one('section.release-body')
            if section:
                print(f"Found section.release-body: {len(section.text)}")
            else:
                divs = soup.select('.col-sm-10')
                for d in divs:
                    if len(d.text) > 500:
                        print(f"Potential content div: {len(d.text)}")
