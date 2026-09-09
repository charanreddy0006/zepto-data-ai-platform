import requests
from bs4 import BeautifulSoup


URL = "https://books.toscrape.com/"

response = requests.get(URL, timeout=10)
response.raise_for_status()

response.encoding = "utf-8"

soup = BeautifulSoup(response.text, "html.parser")

category_links = soup.select(".side_categories ul li ul li a")

print(f"Categories found: {len(category_links)}")
print()

for link in category_links:
    category_name = link.get_text(strip=True)
    category_url = link.get("href")

    print(f"{category_name:30} -> {category_url}")