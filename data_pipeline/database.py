import sqlite3
from pathlib import Path

import pandas as pd


# -------------------------------------------------------------
# Database configuration
# -------------------------------------------------------------

DATABASE_PATH = Path(__file__).resolve().parent / "books.db"


# -------------------------------------------------------------
# Create database tables
# -------------------------------------------------------------

def create_tables(connection: sqlite3.Connection) -> None:
    """
    Create the normalized SQLite database schema.

    Tables:
        categories
            Stores each unique book category once.

        books
            Stores book-level information and references the
            categories table through category_id.

    Relationships:
        categories.category_id
            ↓
        books.category_id
    """

    # Enable foreign-key enforcement.
    connection.execute("PRAGMA foreign_keys = ON")

    # ---------------------------------------------------------
    # Categories table
    # ---------------------------------------------------------
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL UNIQUE
        )
        """
    )

    # ---------------------------------------------------------
    # Books table
    # ---------------------------------------------------------
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            book_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price_gbp REAL NOT NULL,
            price_inr REAL NOT NULL,
            rating INTEGER NOT NULL
                CHECK (rating BETWEEN 1 AND 5),
            in_stock INTEGER NOT NULL
                CHECK (in_stock IN (0, 1)),
            category_id INTEGER NOT NULL,
            FOREIGN KEY (category_id)
                REFERENCES categories(category_id)
        )
        """
    )

    connection.commit()


# -------------------------------------------------------------
# Insert cleaned data
# -------------------------------------------------------------

def insert_data(
    connection: sqlite3.Connection,
    df: pd.DataFrame,
) -> None:
    """
    Insert cleaned book data into the normalized database.

    Categories are inserted first so that their generated
    category IDs can be used as foreign keys in the books table.
    """

    # ---------------------------------------------------------
    # Start with a clean database
    # ---------------------------------------------------------

    # Delete child records first because books references
    # categories through a foreign key.
    connection.execute("DELETE FROM books")
    connection.execute("DELETE FROM categories")

    # Reset AUTOINCREMENT counters so each fresh pipeline run
    # starts IDs from 1.
    connection.execute(
        """
        DELETE FROM sqlite_sequence
        WHERE name IN ('books', 'categories')
        """
    )

    # ---------------------------------------------------------
    # Insert unique categories
    # ---------------------------------------------------------

    categories = (
        df[["category"]]
        .drop_duplicates()
        .sort_values("category")
        .reset_index(drop=True)
    )

    for category in categories["category"]:
        connection.execute(
            """
            INSERT INTO categories (category_name)
            VALUES (?)
            """,
            (str(category),),
        )

    # ---------------------------------------------------------
    # Build category name → category ID mapping
    # ---------------------------------------------------------

    category_rows = connection.execute(
        """
        SELECT
            category_id,
            category_name
        FROM categories
        ORDER BY category_id
        """
    ).fetchall()

    category_map = {
        category_name: category_id
        for category_id, category_name in category_rows
    }

    # ---------------------------------------------------------
    # Insert books
    # ---------------------------------------------------------

    for _, row in df.iterrows():

        category_id = category_map[row["category"]]

        connection.execute(
            """
            INSERT INTO books (
                title,
                price_gbp,
                price_inr,
                rating,
                in_stock,
                category_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(row["title"]),
                float(row["price_gbp"]),
                float(row["price_inr"]),
                int(row["rating"]),
                int(bool(row["in_stock"])),
                category_id,
            ),
        )

    connection.commit()


# -------------------------------------------------------------
# Verify database
# -------------------------------------------------------------

def verify_database(
    connection: sqlite3.Connection,
) -> None:
    """
    Verify that the normalized database contains the expected
    number of categories and books and that the foreign-key JOIN
    works correctly.
    """

    print("\n" + "=" * 60)
    print("DATABASE VERIFICATION")
    print("=" * 60)

    # ---------------------------------------------------------
    # Count categories
    # ---------------------------------------------------------

    category_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM categories
        """
    ).fetchone()[0]

    # ---------------------------------------------------------
    # Count books
    # ---------------------------------------------------------

    book_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM books
        """
    ).fetchone()[0]

    print(f"\nCategories: {category_count}")
    print(f"Books: {book_count}")

    # ---------------------------------------------------------
    # Display categories
    # ---------------------------------------------------------

    print("\nCategories table:")

    categories_df = pd.read_sql(
        """
        SELECT
            category_id,
            category_name
        FROM categories
        ORDER BY category_id
        """,
        connection,
    )

    print(
        categories_df.to_string(index=False)
    )

    # ---------------------------------------------------------
    # Display sample books
    # ---------------------------------------------------------

    print("\nBooks sample:")

    books_df = pd.read_sql(
        """
        SELECT
            book_id,
            title,
            price_gbp,
            price_inr,
            rating,
            in_stock,
            category_id
        FROM books
        ORDER BY book_id
        LIMIT 5
        """,
        connection,
    )

    print(
        books_df.to_string(index=False)
    )

    # ---------------------------------------------------------
    # Verify foreign-key JOIN
    # ---------------------------------------------------------

    print("\nBooks with categories:")

    joined_df = pd.read_sql(
        """
        SELECT
            b.book_id,
            b.title,
            b.price_gbp,
            b.price_inr,
            b.rating,
            b.in_stock,
            c.category_name
        FROM books AS b
        INNER JOIN categories AS c
            ON b.category_id = c.category_id
        ORDER BY b.book_id
        LIMIT 5
        """,
        connection,
    )

    print(
        joined_df.to_string(index=False)
    )

    # ---------------------------------------------------------
    # Validation checks
    # ---------------------------------------------------------

    assert category_count >= 3, (
        "Database must contain at least 3 categories."
    )

    assert book_count >= 60, (
        "Database must contain at least 60 books."
    )

    # Make sure every book has a valid category.
    orphaned_books = connection.execute(
        """
        SELECT COUNT(*)
        FROM books AS b
        LEFT JOIN categories AS c
            ON b.category_id = c.category_id
        WHERE c.category_id IS NULL
        """
    ).fetchone()[0]

    assert orphaned_books == 0, (
        "Found books with invalid category references."
    )

    # Make sure IDs start at 1 after a fresh load.
    first_book_id = connection.execute(
        """
        SELECT MIN(book_id)
        FROM books
        """
    ).fetchone()[0]

    first_category_id = connection.execute(
        """
        SELECT MIN(category_id)
        FROM categories
        """
    ).fetchone()[0]

    assert first_book_id == 1, (
        "Book IDs should start at 1."
    )

    assert first_category_id == 1, (
        "Category IDs should start at 1."
    )

    print("\n✓ DATABASE VALIDATION PASSED")


# -------------------------------------------------------------
# Main pipeline
# -------------------------------------------------------------

def main() -> None:
    """
    Run the complete data pipeline:

        Scrape
           ↓
        Clean
           ↓
        Store in SQLite
           ↓
        Verify
    """

    # Import pipeline components.
    from cleaner import clean_books
    from scraper import scrape_target_categories

    print("=" * 60)
    print("DATABASE PIPELINE")
    print("=" * 60)

    # ---------------------------------------------------------
    # 1. Scrape
    # ---------------------------------------------------------

    print("\n[1/4] Scraping books...")

    records = scrape_target_categories()

    raw_df = pd.DataFrame(records)

    print(f"Raw records: {len(raw_df)}")

    # ---------------------------------------------------------
    # 2. Clean
    # ---------------------------------------------------------

    print("\n[2/4] Cleaning data...")

    cleaned_df = clean_books(raw_df)

    print(f"Cleaned records: {len(cleaned_df)}")

    # ---------------------------------------------------------
    # 3. Create database and insert data
    # ---------------------------------------------------------

    print("\n[3/4] Creating SQLite database...")

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        # Create tables.
        create_tables(connection)

        # Insert cleaned records.
        insert_data(
            connection,
            cleaned_df,
        )

        # -----------------------------------------------------
        # 4. Verify database
        # -----------------------------------------------------

        print("\n[4/4] Verifying database...")

        verify_database(connection)

    finally:
        connection.close()

    print("\nDatabase created at:")
    print(DATABASE_PATH)


# -------------------------------------------------------------
# Entry point
# -------------------------------------------------------------

if __name__ == "__main__":
    main()