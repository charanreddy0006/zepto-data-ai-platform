# Module 1 — Data Pipeline

## Overview

This module implements an end-to-end data engineering pipeline for collecting, cleaning, transforming, storing, and querying book data from **Books to Scrape**.

The pipeline performs the following operations:

1. Scrapes book data from multiple categories.
2. Handles pagination automatically.
3. Parses and validates individual book records.
4. Cleans and transforms the scraped data.
5. Converts GBP prices to INR.
6. Stores the processed data in a normalized SQLite database.
7. Executes SQL queries using `pandas.read_sql()`.
8. Reproduces the SQL JOIN using `pandas.merge()`.
9. Validates the final dataset and database.

---

## Pipeline Architecture

```text
Books to Scrape
       |
       v
Category Discovery
       |
       v
Paginated Web Scraping
       |
       v
Book Parser
       |
       v
Data Cleaning & Transformation
       |
       +-- Price Conversion GBP -> INR
       +-- Rating Normalization
       +-- Stock Normalization
       +-- Missing Value Handling
       +-- Duplicate Removal
       |
       v
Normalized SQLite Database
       |
       +-- categories
       |
       +-- books
       |
       v
SQL Queries
       |
       v
Pandas JOIN Validation
```

---

## Dataset

The scraper collects books from three required categories:

| Category | Books |
|---|---:|
| Fiction | 65 |
| Mystery | 32 |
| Historical Fiction | 26 |
| **Total** | **123** |

The final cleaned dataset contains:

- **123 books**
- **3 categories**
- **8 columns**

### Final Columns

| Column | Description |
|---|---|
| `title` | Book title |
| `price_gbp` | Original price in GBP |
| `star_rating` | Original rating text |
| `rating` | Numeric rating from 1 to 5 |
| `availability` | Availability text |
| `in_stock` | Boolean stock indicator |
| `category` | Book category |
| `price_inr` | Converted price in INR |

---

# 1. Web Scraping

## Source

The data is collected from:

**Books to Scrape**

<https://books.toscrape.com/>

The scraper first discovers the available categories from the website instead of hardcoding the category URLs.

### Target Categories

```python
TARGET_CATEGORIES = {
    "Fiction",
    "Mystery",
    "Historical Fiction"
}
```

---

## Pagination

The scraper automatically follows the `next` link available on each category page.

For every page, it:

1. Requests the page.
2. Parses the HTML using BeautifulSoup.
3. Extracts all book cards.
4. Parses each book.
5. Checks for the next page.
6. Continues until there are no more pages.

This allows the pipeline to collect all books available in the selected categories.

---

## Book Fields Extracted

For every book, the scraper extracts:

- Title
- Price in GBP
- Star rating
- Numeric rating
- Availability
- Stock status
- Category

Malformed records are skipped safely instead of stopping the complete pipeline.

---

# 2. Data Cleaning

The cleaning logic is implemented in:

```text
data_pipeline/cleaner.py
```

The cleaning process includes the following steps.

## Text Cleaning

Book titles and text fields are stripped of unnecessary whitespace.

Repeated spaces, tabs, and newline characters are normalized.

For example:

```text
"  Example   Book  "
```

becomes:

```text
"Example Book"
```

The actual words in the title are not changed.

---

## Numeric Conversion

Prices are converted into numeric values.

```python
price_gbp = pd.to_numeric(...)
```

Ratings are also converted into integer values between 1 and 5.

---

## Missing Values

The pipeline checks for missing values in required fields.

Numeric missing values are handled using median imputation where applicable.

Records missing essential fields such as title or price are removed.

---

## Duplicate Removal

Duplicate books are removed using:

```text
title + category
```

as the duplicate criteria.

---

# 3. Currency Conversion

The project uses the fixed conversion rate specified for this assignment:

```text
1 GBP = 105.50 INR
```

The INR price is calculated as:

```python
price_inr = price_gbp * 105.50
```

The result is rounded to two decimal places.

### Example

```text
50.10 GBP x 105.50 = 5285.55 INR
```

---

# 4. Data Validation

The cleaning pipeline validates the final dataset.

The following conditions are checked:

- At least 60 books are collected.
- At least 3 categories are present.
- No missing prices remain.
- No missing INR prices remain.
- Ratings are between 1 and 5.
- `in_stock` is boolean.
- Book titles are not empty.

The final dataset successfully passes these validation checks.

---

# 5. SQLite Database

The cleaned data is stored in:

```text
data_pipeline/books.db
```

The database uses a normalized relational structure with two tables:

```text
categories
     |
     | 1
     |
     | N
     |
books
```

---

## Categories Table

```sql
CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT NOT NULL UNIQUE
);
```

### Columns

| Column | Type | Description |
|---|---|---|
| `category_id` | INTEGER | Primary key |
| `category_name` | TEXT | Unique category name |

---

## Books Table

```sql
CREATE TABLE books (
    book_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    price_gbp REAL NOT NULL,
    price_inr REAL NOT NULL,
    rating INTEGER NOT NULL,
    in_stock INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    FOREIGN KEY (category_id)
        REFERENCES categories(category_id)
);
```

### Columns

| Column | Type | Description |
|---|---|---|
| `book_id` | INTEGER | Primary key |
| `title` | TEXT | Book title |
| `price_gbp` | REAL | Price in GBP |
| `price_inr` | REAL | Price in INR |
| `rating` | INTEGER | Rating from 1 to 5 |
| `in_stock` | INTEGER | Stock status |
| `category_id` | INTEGER | Foreign key to categories |

---

# 6. Database Validation

The database currently contains:

```text
Categories: 3
Books:      123
```

The pipeline also validates:

- Primary keys.
- Foreign key relationships.
- Number of books.
- Number of categories.
- Absence of orphaned books.
- Correct starting IDs.

Foreign key enforcement is enabled using:

```sql
PRAGMA foreign_keys = ON;
```

---

# 7. SQL Queries

The SQL analysis is implemented in:

```text
data_pipeline/queries.py
```

The queries demonstrate the required SQL operations.

---

## Query 1 — SELECT and WHERE

Retrieve books with a rating of 5.

```sql
SELECT
    title,
    price_gbp,
    rating
FROM books
WHERE rating = 5;
```

This demonstrates:

- `SELECT`
- `WHERE`

---

## Query 2 — ORDER BY

Retrieve books ordered from most expensive to least expensive.

```sql
SELECT
    title,
    price_gbp,
    price_inr
FROM books
ORDER BY price_gbp DESC;
```

This demonstrates:

- `ORDER BY`
- Descending sorting

---

## Query 3 — ORDER BY and LIMIT

Retrieve the 10 cheapest books.

```sql
SELECT
    title,
    price_gbp,
    price_inr
FROM books
ORDER BY price_gbp ASC
LIMIT 10;
```

This demonstrates:

- `ORDER BY`
- `LIMIT`

---

## Query 4 — DISTINCT

Find the unique book ratings.

```sql
SELECT DISTINCT
    rating
FROM books
ORDER BY rating;
```

This returns the available rating values from 1 to 5.

---

## Query 5 — IN and BETWEEN

Find books belonging to the available category IDs with prices between £20 and £40.

```sql
SELECT
    title,
    price_gbp,
    rating,
    category_id
FROM books
WHERE category_id IN (1, 2, 3)
  AND price_gbp BETWEEN 20 AND 40
ORDER BY price_gbp DESC;
```

This demonstrates:

- `IN`
- `BETWEEN`
- `ORDER BY`

---

# 8. SQL JOIN

The normalized database allows book information to be combined with category information.

```sql
SELECT
    b.book_id,
    b.title,
    b.price_gbp,
    b.price_inr,
    b.rating,
    c.category_name
FROM books b
JOIN categories c
    ON b.category_id = c.category_id
LIMIT 10;
```

This demonstrates a relational `JOIN` using the foreign key relationship.

---

# 9. Pandas Integration

SQL query results are loaded using:

```python
pd.read_sql()
```

Example:

```python
books_df = pd.read_sql(
    "SELECT * FROM books",
    connection
)
```

The categories table is also loaded:

```python
categories_df = pd.read_sql(
    "SELECT * FROM categories",
    connection
)
```

## Reproducing the SQL JOIN with Pandas

The SQL JOIN is reproduced using:

```python
merged_df = pd.merge(
    books_df,
    categories_df,
    on="category_id",
    how="inner"
)
```

The resulting Pandas merge is compared with the SQL JOIN result.

```text
SQL JOIN records:       123
Pandas merge records:   123
```

Therefore, the SQL JOIN and Pandas merge produce the same number of records.

The JOIN validation passes successfully.

---

# 10. Project Files

The Module 1 directory contains:

```text
data_pipeline/
|
+-- README.md
+-- scraper.py
+-- book_parser.py
+-- cleaner.py
+-- database.py
+-- queries.py
+-- test_scraping.py
+-- books.db
```

### File Responsibilities

| File | Purpose |
|---|---|
| `README.md` | Module documentation |
| `scraper.py` | Category discovery and paginated scraping |
| `book_parser.py` | Individual book parsing and validation |
| `cleaner.py` | Data cleaning and transformation |
| `database.py` | SQLite database creation and loading |
| `queries.py` | SQL queries and Pandas JOIN validation |
| `test_scraping.py` | Website connectivity test |
| `books.db` | Final SQLite database |

---

# 11. Running the Pipeline

Activate the project virtual environment first.

```powershell
.venv\Scripts\Activate.ps1
```

Run the scraper:

```powershell
python data_pipeline/scraper.py
```

Run the cleaning pipeline:

```powershell
python data_pipeline/cleaner.py
```

Create and populate the database:

```powershell
python data_pipeline/database.py
```

Run the SQL queries:

```powershell
python data_pipeline/queries.py
```

---

# 12. Validation Summary

The completed Module 1 pipeline successfully satisfies the major requirements.

| Requirement | Status |
|---|---|
| Web scraping | ✅ |
| Multiple categories | ✅ |
| Pagination | ✅ |
| Book parsing | ✅ |
| Data cleaning | ✅ |
| GBP → INR conversion | ✅ |
| SQLite database | ✅ |
| Normalized tables | ✅ |
| Primary key | ✅ |
| Foreign key | ✅ |
| SQL queries | ✅ |
| SQL JOIN | ✅ |
| `pd.read_sql()` | ✅ |
| `pd.merge()` | ✅ |
| JOIN validation | ✅ |
| 60+ books | ✅ |
| 3 categories | ✅ |

---

## Final Dataset

```text
Total books:       123
Categories:        3
Final columns:     8
Database records:  123
```

---

# Module 1 Status

## Module 1 — Data Pipeline: COMPLETE ✅

The pipeline provides a complete workflow from:

```text
Web Source
    |
    v
Scraping
    |
    v
Parsing
    |
    v
Cleaning
    |
    v
Transformation
    |
    v
SQLite Storage
    |
    v
SQL Analysis
    |
    v
Pandas Validation
```

The Module 1 data pipeline is complete and ready to be committed and merged into the `main` branch.