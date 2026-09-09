import requests
from bs4 import BeautifulSoup


URL = "https://books.toscrape.com/"

response = requests.get(URL, timeout=10)

print("Status code:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")

print("Page title:", soup.title.get_text(strip=True))