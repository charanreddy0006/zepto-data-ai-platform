# Zepto Data & AI Platform

An end-to-end AI/ML engineering capstone that combines web data engineering, exploratory data analysis, predictive modeling, retrieval-augmented generation (RAG), FastAPI, and Docker in a single repository.

---

##  Project Overview

The **Zepto Data & AI Platform** is organized into three major modules. Each module demonstrates a different stage of a practical data and AI engineering workflow, from data collection and analytics to an AI-powered customer support assistant.

```text
                         Zepto Data & AI Platform
                                  |
              +-------------------+-------------------+
              |                   |                   |
              v                   v                   v
       Data Pipeline          Analytics         Support Assistant
              |                Pipeline                |
              v                   |                    v
        Web Scraping             v               Policy Corpus
              |             EDA + ML                 |
              v                   |                    v
      SQLite + SQL               v             Embeddings
              |             Model Training            |
              |                   |                    v
              |                   v               ChromaDB
              |             Saved Model                |
              |                   |                    v
              +-------------------+              LangGraph
                                                   |
                                                   v
                                                FastAPI
                                                   |
                                                   v
                                                 Docker
```

---

# 📂 Project Modules

## 1. Data Pipeline

The Data Pipeline module focuses on collecting, cleaning, transforming, storing, and querying structured data.

### Main tasks

- Web scraping from Books to Scrape
- Category discovery
- Multi-category pagination
- Data extraction and normalization
- Currency conversion
- Relational database design
- SQLite storage
- SQL querying
- Pandas-based analysis
- SQL/Pandas join validation

### Key technologies

- Python
- Requests / web scraping
- Pandas
- SQLite
- SQL

### Module location

```text
data_pipeline/
```

---

## 2. Analytics Pipeline

The Analytics Pipeline module focuses on exploratory data analysis and machine learning using the Titanic dataset.

### Main tasks

- Dataset profiling
- Data cleaning and preprocessing
- Exploratory data analysis
- Data visualization
- Classification
- Regression
- Model evaluation
- Hyperparameter tuning
- Model persistence

### Key artifacts

```text
analytics/
├── titanic.csv
├── titanic_analysis.ipynb
├── models/
│   └── best_titanic_classifier.joblib
└── README.md
```

### Key technologies

- Python
- Pandas
- NumPy
- Matplotlib
- Scikit-learn
- Joblib

### Module location

```text
analytics/
```

---

# 3. 🤖 Support Assistant

The Support Assistant is a policy-aware AI customer-support application based on the Zepto policy corpus.

It uses:

- Eight policy documents
- Sentence Transformers
- `all-MiniLM-L6-v2`
- ChromaDB
- LangGraph
- Structured prompts
- Pydantic
- FastAPI
- Uvicorn
- Docker

The assistant supports two query paths:

```text
                         User Query
                             |
                             v
                       classify_intent
                         /                                  /                                   v              v
              policy_question   general_question
                     |                 |
                     v                 v
          retrieve_and_answer     direct_answer
                     |                 |
                     +--------+--------+
                              |
                              v
                       Pydantic Schema
                              |
                              v
                         JSON Response
```

---

## 📚 Support Assistant Policy Corpus

The Support Assistant uses eight policy documents:

```text
support_assistant/
└── docs/
    ├── doc_01.txt   # Delivery policy
    ├── doc_02.txt   # Returns and refunds
    ├── doc_03.txt   # Membership tiers
    ├── doc_04.txt   # Order tracking
    ├── doc_05.txt   # Order cancellation
    ├── doc_06.txt   # Damaged, spoiled, or missing items
    ├── doc_07.txt   # Gift cards
    └── doc_08.txt   # Customer support
```

The documents are loaded, embedded, and stored in a persistent ChromaDB collection.

---

## 🔎 Embeddings and Retrieval

The embedding model used by the Support Assistant is:

```text
all-MiniLM-L6-v2
```

The document ingestion flow is:

```text
Policy Documents
      |
      v
Load Documents
      |
      v
Create Embeddings
      |
      v
Store in ChromaDB
      |
      v
User Query
      |
      v
Create Query Embedding
      |
      v
Cosine Similarity Search
      |
      v
Top 3 Relevant Documents
```

For example:

```text
Query:
How much does priority delivery cost?

Top retrieved documents:
1. doc_01
2. doc_05
3. doc_03
```

`doc_01` is the relevant delivery-policy document.

---

# 🧠 LangGraph Workflow

The Support Assistant uses a LangGraph `StateGraph` with three main nodes.

### `classify_intent`

Determines whether the query is a:

```text
policy_question
```

or:

```text
general_question
```

In the default mock mode, the following keywords are used:

```text
delivery
return
refund
membership
tracking
cancel
gift card
support hours
```

### `retrieve_and_answer`

Handles policy questions.

It:

1. Embeds the query.
2. Searches ChromaDB.
3. Retrieves the top three documents.
4. Builds the structured support prompt.
5. Generates the deterministic mock answer.
6. Returns the source document IDs.

### `direct_answer`

Handles general questions.

In mock mode, it returns:

```text
I can only answer questions about Zepto policies right now.
```

No policy retrieval is performed for general questions.

---

# 📝 Structured Prompt

The Support Assistant uses a structured prompt containing:

```text
ROLE
CONTEXT
TASK
FORMAT
LENGTH
```

The prompt also contains an explicit negative constraint:

```text
Do not answer using information not present in the provided context.
```

A few-shot example is included to demonstrate the expected grounded response format.

The prompt is implemented in:

```text
support_assistant/app/prompt.py
```

---

# 🎭 MOCK_LLM Mode

The default configuration is:

```text
MOCK_LLM=1
```

Mock mode provides deterministic local execution without requiring an external or paid LLM service.

### Policy question response

The response begins with:

```text
Based on the retrieved context:
```

and uses an approximately 200-character excerpt from the highest-ranked retrieved document.

### General question response

The fixed response is:

```text
I can only answer questions about Zepto policies right now.
```

The embedding and ChromaDB retrieval components continue to work normally.

---

# 📋 Response Schema

The final API response is validated with Pydantic.

```json
{
  "answer": "string",
  "sources": ["document_id"],
  "confidence": 0.0
}
```

The confidence value must satisfy:

```text
0.0 <= confidence <= 1.0
```

### Policy question example

```json
{
  "answer": "Based on the retrieved context: Zepto delivers grocery and household essentials to serviceable pin codes within 10 to 30 minutes of order confirmation, depending on the customer's delivery zone and current order volume. Standard del",
  "sources": [
    "doc_01",
    "doc_05",
    "doc_03"
  ],
  "confidence": 0.9
}
```

### General question example

```json
{
  "answer": "I can only answer questions about Zepto policies right now.",
  "sources": [],
  "confidence": 1.0
}
```

---

# 🔁 Validation and Retry Logic

Response validation is implemented in:

```text
support_assistant/app/schemas.py
```

The response is first validated against the Pydantic schema.

The optional real-LLM path supports up to two additional validation attempts when invalid output is produced.

The corrective instruction requires:

- `answer` to be a string
- `sources` to be a list of document or chunk IDs
- `confidence` to be between `0` and `1`
- valid JSON output

The default mock mode is deterministic and does not require retries.

---

# 🚀 FastAPI

The Support Assistant exposes:

```text
POST /ask
```

### Request

```json
{
  "query": "How much does priority delivery cost?"
}
```

### Response

```json
{
  "answer": "Based on the retrieved context: ...",
  "sources": [
    "doc_01",
    "doc_05",
    "doc_03"
  ],
  "confidence": 0.9
}
```

---

# 💻 Run Locally

From the repository root:

```powershell
cd support_assistant
```

Activate the Python virtual environment and install the required dependencies.

Then:

```powershell
cd app
uvicorn main:app --host 0.0.0.0 --port 7860
```

Open the FastAPI Swagger interface:

```text
http://127.0.0.1:7860/docs
```

---

# 🧪 API Testing

## Test 1 — Policy Question

Request:

```json
{
  "query": "How much does priority delivery cost?"
}
```

Expected response structure:

```json
{
  "answer": "Based on the retrieved context: ...",
  "sources": [
    "doc_01",
    "doc_05",
    "doc_03"
  ],
  "confidence": 0.9
}
```

This demonstrates:

- Policy intent classification
- ChromaDB retrieval
- Top-3 document retrieval
- Correct source document retrieval
- Deterministic mock generation
- Pydantic validation

---

## Test 2 — General Question

Request:

```json
{
  "query": "What is the capital of India?"
}
```

Expected response:

```json
{
  "answer": "I can only answer questions about Zepto policies right now.",
  "sources": [],
  "confidence": 1.0
}
```

This demonstrates:

- General intent classification
- Conditional LangGraph routing
- Direct-answer node
- No policy retrieval
- Deterministic mock response

---

# 🐳 Docker

The Support Assistant includes a Dockerfile for containerized execution.

## Build

Run from the repository root:

```powershell
docker build --no-cache -t zepto-support-assistant ./support_assistant
```

## Run

```powershell
docker run --rm -p 7860:7860 zepto-support-assistant
```

Then open:

```text
http://127.0.0.1:7860/docs
```

The Docker image has been successfully built and the container has been successfully started and tested using both the policy-question and general-question API paths.

---

# 📁 Complete Repository Structure

```text
zepto-data-ai-platform/
│
├── data_pipeline/
│   ├── ...
│   └── README.md
│
├── analytics/
│   ├── titanic.csv
│   ├── titanic_analysis.ipynb
│   ├── models/
│   │   └── best_titanic_classifier.joblib
│   └── README.md
│
├── support_assistant/
│   ├── app/
│   │   ├── graph.py
│   │   ├── main.py
│   │   ├── prompt.py
│   │   ├── schemas.py
│   │   └── vector_store.py
│   │
│   ├── docs/
│   │   ├── doc_01.txt
│   │   ├── doc_02.txt
│   │   ├── doc_03.txt
│   │   ├── doc_04.txt
│   │   ├── doc_05.txt
│   │   ├── doc_06.txt
│   │   ├── doc_07.txt
│   │   └── doc_08.txt
│   │
│   ├── data/
│   │   └── chroma/
│   │
│   ├── .dockerignore
│   ├── Dockerfile
│   ├── README.md
│   └── requirements.txt
│
├── .gitignore
└── README.md
```

---

# 🛠️ Technologies Used

| Area | Technologies |
|---|---|
| Programming | Python |
| Data Processing | Pandas, NumPy |
| Web Scraping | Python web-scraping tools |
| Database | SQLite, SQL |
| Machine Learning | Scikit-learn |
| Visualization | Matplotlib |
| Embeddings | Sentence Transformers |
| Embedding Model | `all-MiniLM-L6-v2` |
| Vector Database | ChromaDB |
| Workflow Orchestration | LangGraph |
| API | FastAPI |
| Validation | Pydantic |
| Server | Uvicorn |
| Containerization | Docker |
| Version Control | Git, GitHub |

---

# 📊 Project Status

| Module | Status |
|---|---|
| Data Pipeline | ✅ Complete |
| Analytics Pipeline | ✅ Complete |
| Support Assistant | ✅ Complete |
| ChromaDB Retrieval | ✅ Tested |
| LangGraph Routing | ✅ Tested |
| FastAPI `/ask` | ✅ Tested |
| Docker Build | ✅ Successful |
| Docker Runtime | ✅ Successful |
| Policy API Test | ✅ Successful |
| General API Test | ✅ Successful |

---

# 🔮 Optional Future Extension

The Support Assistant can be extended with a real LLM provider by implementing the optional real-generation path when:

```text
MOCK_LLM=0
```

Possible future improvements include:

- More advanced document chunking
- Additional policy documents
- Better retrieval evaluation
- Retrieval confidence scoring
- Real LLM answer generation
- Streaming responses
- Authentication
- Monitoring and logging
- Deployment to a cloud platform

The current implementation intentionally uses deterministic mock generation so the project can be executed locally without requiring a paid LLM service.

---

# 👤 Project

**Zepto Data & AI Platform**

This repository contains all three capstone modules in a single project:

```text
Data Pipeline
      +
Analytics Pipeline
      +
AI Support Assistant
      =
Zepto Data & AI Platform
```
