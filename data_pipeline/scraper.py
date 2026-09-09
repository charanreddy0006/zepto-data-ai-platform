from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

from book_parser import parse_book


BASE_URL = "https://books.toscrape.com/"

TARGET_CATEGORIES = {
    "Fiction",
    "Mystery",
    "Historical Fiction",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ZeptoDataAIPlatform/1.0)"
}


def get_page(url: str) -> BeautifulSoup:
    """
    Download a webpage and return its parsed BeautifulSoup object.
    """

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10,
    )

    response.raise_for_status()

    # The website uses UTF-8 encoding.
    response.encoding = "utf-8"

    return BeautifulSoup(response.text, "html.parser")


def get_category_links() -> dict[str, str]:
    """
    Discover category names and URLs from the website home page.

    Returns
    -------
    dict
        Mapping of category name to absolute URL.
    """

    soup = get_page(BASE_URL)

    category_links = soup.select(
        ".side_categories ul li ul li a"
    )

    categories = {}

    for link in category_links:
        category_name = link.get_text(strip=True)
        relative_url = link.get("href")

        if not relative_url:
            continue

        absolute_url = urljoin(BASE_URL, relative_url)

        categories[category_name] = absolute_url

    return categories


def scrape_category(
    category_name: str,
    category_url: str,
) -> list[dict]:
    """
    Scrape all books from one category, including all paginated pages.
    """

    records = []

    current_url = category_url
    page_number = 1

    while current_url:

        print(
            f"Scraping category='{category_name}' "
            f"page={page_number}"
        )

        soup = get_page(current_url)

        books = soup.select("article.product_pod")

        print(f"  Books found on page: {len(books)}")

        for book in books:

            parsed_book = parse_book(
                book,
                category=category_name,
            )

            if parsed_book is not None:
                records.append(parsed_book)

        # Find the next page.
        next_link = soup.select_one("li.next a")

        if next_link and next_link.get("href"):

            current_url = urljoin(
                current_url,
                next_link["href"],
            )

            page_number += 1

        else:
            current_url = None

    print(
        f"Finished category='{category_name}'. "
        f"Books collected: {len(records)}"
    )

    return records


def scrape_target_categories() -> list[dict]:
    """
    Discover the requested categories and scrape all their books.
    """

    available_categories = get_category_links()

    missing_categories = (
        TARGET_CATEGORIES - set(available_categories)
    )

    if missing_categories:
        raise ValueError(
            "The following target categories were not found: "
            f"{sorted(missing_categories)}"
        )

    all_records = []

    for category_name in TARGET_CATEGORIES:

        category_url = available_categories[category_name]

        category_records = scrape_category(
            category_name,
            category_url,
        )

        all_records.extend(category_records)

    return all_records


def main() -> None:
    """
    Run the complete scraping process.
    """

    records = scrape_target_categories()

    df = pd.DataFrame(records)

    print("\n" + "=" * 60)
    print("SCRAPING SUMMARY")
    print("=" * 60)

    print(f"Total books collected: {len(df)}")
    print(
        f"Categories collected: "
        f"{df['category'].nunique()}"
    )

    print("\nBooks by category:")
    print(df["category"].value_counts())

    print("\nDataset shape:")
    print(df.shape)

    print("\nFirst 5 rows:")
    print(df.head())

    print("\nColumn names:")
    print(df.columns.tolist())

    if len(df) < 60:
        raise ValueError(
            f"Scraping requirement not satisfied. "
            f"Only {len(df)} books were collected; "
            f"at least 60 are required."
        )

    if df["category"].nunique() < 3:
        raise ValueError(
            "Scraping requirement not satisfied. "
            "At least 3 categories are required."
        )

    print("\n✓ Minimum scraping requirements satisfied.")


if __name__ == "__main__":
    main()