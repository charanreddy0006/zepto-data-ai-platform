import sqlite3
from pathlib import Path

import pandas as pd


DATABASE_PATH = Path(__file__).resolve().parent / "books.db"


def run_query(connection, query, title):
    """Execute a SQL query and display the result."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

    df = pd.read_sql(query, connection)
    print(df.to_string(index=False))

    return df


def main():
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        # -----------------------------------------------------
        # Query 1: SELECT + WHERE
        # Find books with a rating of 5.
        # -----------------------------------------------------
        run_query(
            connection,
            """
            SELECT
                title,
                price_gbp,
                rating
            FROM books
            WHERE rating = 5
            """,
            "QUERY 1: Five-Star Books",
        )

        # -----------------------------------------------------
        # Query 2: ORDER BY
        # Find the most expensive books.
        # -----------------------------------------------------
        run_query(
            connection,
            """
            SELECT
                title,
                price_gbp,
                price_inr
            FROM books
            ORDER BY price_gbp DESC
            """,
            "QUERY 2: Most Expensive Books",
        )

        # -----------------------------------------------------
        # Query 3: LIMIT
        # Display the 10 cheapest books.
        # -----------------------------------------------------
        run_query(
            connection,
            """
            SELECT
                title,
                price_gbp,
                price_inr
            FROM books
            ORDER BY price_gbp ASC
            LIMIT 10
            """,
            "QUERY 3: 10 Cheapest Books",
        )

        # -----------------------------------------------------
        # Query 4: DISTINCT
        # Find all unique ratings.
        # -----------------------------------------------------
        run_query(
            connection,
            """
            SELECT DISTINCT rating
            FROM books
            ORDER BY rating
            """,
            "QUERY 4: Distinct Ratings",
        )

        # -----------------------------------------------------
        # Query 5: IN + BETWEEN
        # Find books in selected categories with prices
        # between £20 and £40.
        # -----------------------------------------------------
        run_query(
            connection,
            """
            SELECT
                title,
                price_gbp,
                rating,
                category_id
            FROM books
            WHERE category_id IN (1, 2, 3)
              AND price_gbp BETWEEN 20 AND 40
            ORDER BY price_gbp DESC
            """,
            "QUERY 5: Selected Categories + Price Range",
        )

        # -----------------------------------------------------
        # Query 6: JOIN
        # Combine books with their category names.
        # -----------------------------------------------------
        joined_df = run_query(
            connection,
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
            LIMIT 10
            """,
            "QUERY 6: Books + Categories JOIN",
        )

        # -----------------------------------------------------
        # Reproduce the JOIN using pandas.merge()
        # -----------------------------------------------------
        print("\n" + "=" * 70)
        print("PANDAS MERGE: Reproducing the SQL JOIN")
        print("=" * 70)

        books_df = pd.read_sql(
            """
            SELECT *
            FROM books
            """,
            connection,
        )

        categories_df = pd.read_sql(
            """
            SELECT *
            FROM categories
            """,
            connection,
        )

        merged_df = pd.merge(
            books_df,
            categories_df,
            on="category_id",
            how="inner",
        )

        merged_df = merged_df[
            [
                "book_id",
                "title",
                "price_gbp",
                "price_inr",
                "rating",
                "in_stock",
                "category_name",
            ]
        ]

        print(merged_df.head(10).to_string(index=False))

        # -----------------------------------------------------
        # Verify SQL JOIN and pandas.merge() produce the same
        # number of records.
        # -----------------------------------------------------
        sql_join_count = len(
            pd.read_sql(
                """
                SELECT
                    b.book_id,
                    b.title,
                    c.category_name
                FROM books AS b
                INNER JOIN categories AS c
                    ON b.category_id = c.category_id
                """,
                connection,
            )
        )

        pandas_merge_count = len(merged_df)

        print("\nSQL JOIN records:", sql_join_count)
        print("Pandas merge records:", pandas_merge_count)

        assert sql_join_count == pandas_merge_count

        print("\n✓ SQL AND PANDAS JOIN VALIDATION PASSED")

    finally:
        connection.close()


if __name__ == "__main__":
    main()