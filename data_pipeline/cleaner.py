import re

import pandas as pd


# -------------------------------------------------------------
# Configuration
# -------------------------------------------------------------

# Fixed exchange rate required by the project.
GBP_TO_INR = 105.50


# Columns expected from the scraper.
REQUIRED_COLUMNS = [
    "title",
    "price_gbp",
    "star_rating",
    "rating",
    "availability",
    "in_stock",
    "category",
]


# -------------------------------------------------------------
# Title cleaning
# -------------------------------------------------------------

def clean_title(title: str) -> str:
    """
    Clean book titles without changing the actual words.

    Only removes unwanted surrounding whitespace and normalizes
    repeated whitespace inside the title.
    """
    if pd.isna(title):
        return ""

    title = str(title).strip()

    # Normalize multiple spaces/tabs/newlines to a single space.
    title = re.sub(r"\s+", " ", title)

    return title

# -------------------------------------------------------------
# Stock-status cleaning
# -------------------------------------------------------------

def normalize_stock(value) -> bool:
    """
    Convert different stock representations into a boolean.
    """

    if isinstance(value, bool):
        return value

    if pd.isna(value):
        return False

    value = str(value).strip().lower()

    return value in {
        "true",
        "1",
        "yes",
        "in stock",
        "available",
    }


# -------------------------------------------------------------
# Main cleaning function
# -------------------------------------------------------------

def clean_books(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate the scraped books dataset.

    Cleaning steps:

    1. Validate required columns.
    2. Remove completely empty rows.
    3. Clean text fields.
    4. Remove rows without essential fields.
    5. Convert numeric columns.
    6. Handle missing numeric values using median imputation.
    7. Validate price values.
    8. Validate rating values.
    9. Normalize stock status.
    10. Convert GBP prices to INR.
    11. Remove duplicate books.
    12. Reset the DataFrame index.
    """

    # Work on a copy so the original DataFrame is not modified.
    df = df.copy()

    # ---------------------------------------------------------
    # 1. Validate required columns
    # ---------------------------------------------------------

    missing_columns = (
        set(REQUIRED_COLUMNS) - set(df.columns)
    )

    if missing_columns:
        raise ValueError(
            f"Missing required columns: "
            f"{sorted(missing_columns)}"
        )

    # ---------------------------------------------------------
    # 2. Remove completely empty rows
    # ---------------------------------------------------------

    df = df.dropna(
        how="all"
    ).copy()

    # ---------------------------------------------------------
    # 3. Clean text fields
    # ---------------------------------------------------------

    df["title"] = (
        df["title"]
        .astype("string")
        .apply(clean_title)
    )

    df["category"] = (
        df["category"]
        .astype("string")
        .str.strip()
    )

    df["availability"] = (
        df["availability"]
        .astype("string")
        .str.strip()
    )

    # ---------------------------------------------------------
    # 4. Remove rows without essential fields
    # ---------------------------------------------------------

    df = df.dropna(
        subset=[
            "title",
            "category",
        ]
    ).copy()

    df = df[
        (df["title"] != "")
        & (df["category"] != "")
    ].copy()

    # ---------------------------------------------------------
    # 5. Convert numeric columns
    # ---------------------------------------------------------

    df["price_gbp"] = pd.to_numeric(
        df["price_gbp"],
        errors="coerce",
    )

    df["rating"] = pd.to_numeric(
        df["rating"],
        errors="coerce",
    )

    # ---------------------------------------------------------
    # 6. Handle missing numeric values
    # ---------------------------------------------------------
    #
    # Median imputation is used because it is less sensitive
    # to extreme values than mean imputation.
    # ---------------------------------------------------------

    if df["price_gbp"].isna().any():

        median_price = df["price_gbp"].median()

        if pd.isna(median_price):
            raise ValueError(
                "Unable to impute price_gbp because "
                "no valid prices exist."
            )

        df["price_gbp"] = (
            df["price_gbp"]
            .fillna(median_price)
        )

    if df["rating"].isna().any():

        median_rating = df["rating"].median()

        if pd.isna(median_rating):
            raise ValueError(
                "Unable to impute rating because "
                "no valid ratings exist."
            )

        df["rating"] = (
            df["rating"]
            .fillna(median_rating)
        )

    # ---------------------------------------------------------
    # 7. Validate price values
    # ---------------------------------------------------------

    df = df[
        df["price_gbp"] >= 0
    ].copy()

    # ---------------------------------------------------------
    # 8. Validate rating values
    # ---------------------------------------------------------

    df = df[
        df["rating"].between(1, 5)
    ].copy()

    # Ratings must be integers from 1 to 5.
    df["rating"] = (
        df["rating"]
        .round()
        .astype(int)
    )

    # ---------------------------------------------------------
    # 9. Normalize stock status
    # ---------------------------------------------------------

    df["in_stock"] = (
        df["in_stock"]
        .apply(normalize_stock)
    )

    # ---------------------------------------------------------
    # 10. Convert GBP to INR
    # ---------------------------------------------------------

    df["price_inr"] = (
        df["price_gbp"] * GBP_TO_INR
    ).round(2)

    # ---------------------------------------------------------
    # 11. Remove duplicate books
    # ---------------------------------------------------------

    df = df.drop_duplicates(
        subset=[
            "title",
            "category",
        ]
    ).copy()

    # ---------------------------------------------------------
    # 12. Reset index
    # ---------------------------------------------------------

    df = df.reset_index(
        drop=True
    )

    return df


# -------------------------------------------------------------
# Test the cleaner
# -------------------------------------------------------------

def main():
    """
    Run the scraper and cleaner together to verify
    the complete cleaning pipeline.
    """

    from scraper import scrape_target_categories

    print("=" * 60)
    print("BOOK DATA CLEANING")
    print("=" * 60)

    # ---------------------------------------------------------
    # Step 1: Scrape raw data
    # ---------------------------------------------------------

    print("\n[1/2] Scraping data...")

    records = scrape_target_categories()

    raw_df = pd.DataFrame(records)

    print(
        f"Raw dataset shape: {raw_df.shape}"
    )

    # ---------------------------------------------------------
    # Step 2: Clean data
    # ---------------------------------------------------------

    print("\n[2/2] Cleaning data...")

    cleaned_df = clean_books(
        raw_df
    )

    print(
        f"Cleaned dataset shape: "
        f"{cleaned_df.shape}"
    )

    # ---------------------------------------------------------
    # Display columns
    # ---------------------------------------------------------

    print("\nColumns:")

    print(
        cleaned_df.columns.tolist()
    )

    # ---------------------------------------------------------
    # Display data types
    # ---------------------------------------------------------

    print("\nData types:")

    print(
        cleaned_df.dtypes
    )

    # ---------------------------------------------------------
    # Display missing values
    # ---------------------------------------------------------

    print("\nMissing values:")

    print(
        cleaned_df.isnull().sum()
    )

    # ---------------------------------------------------------
    # Display category distribution
    # ---------------------------------------------------------

    print("\nBooks by category:")

    print(
        cleaned_df[
            "category"
        ].value_counts()
    )

    # ---------------------------------------------------------
    # Display price conversion
    # ---------------------------------------------------------

    print("\nPrice conversion sample:")

    print(
        cleaned_df[
            [
                "title",
                "price_gbp",
                "price_inr",
            ]
        ]
        .head()
        .to_string(index=False)
    )

    # ---------------------------------------------------------
    # Display rating distribution
    # ---------------------------------------------------------

    print("\nRating distribution:")

    print(
        cleaned_df[
            "rating"
        ]
        .value_counts()
        .sort_index()
    )

    # ---------------------------------------------------------
    # Display stock distribution
    # ---------------------------------------------------------

    print("\nStock distribution:")

    print(
        cleaned_df[
            "in_stock"
        ].value_counts()
    )

    # ---------------------------------------------------------
    # Validation checks
    # ---------------------------------------------------------

    # At least 60 books are required.
    assert len(cleaned_df) >= 60

    # At least 3 categories are required.
    assert (
        cleaned_df["category"]
        .nunique()
        >= 3
    )

    # No missing GBP prices.
    assert (
        cleaned_df["price_gbp"]
        .notna()
        .all()
    )

    # No missing INR prices.
    assert (
        cleaned_df["price_inr"]
        .notna()
        .all()
    )

    # Ratings must be between 1 and 5.
    assert (
        cleaned_df["rating"]
        .between(1, 5)
        .all()
    )

    # Stock status must be boolean.
    assert (
        cleaned_df["in_stock"].dtype
        == bool
    )

    # Titles must not be empty.
    assert (
        cleaned_df["title"]
        .str.len()
        .gt(0)
        .all()
    )

    print("\n" + "=" * 60)
    print("✓ CLEANING VALIDATION PASSED")
    print("=" * 60)


# -------------------------------------------------------------
# Entry point
# -------------------------------------------------------------

if __name__ == "__main__":
    main()