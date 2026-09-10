# Zepto Support Assistant

## 1. Overview

The Zepto Support Assistant is a policy-aware question-answering system built as Module 3 of the Zepto Data & AI Platform capstone project.

The assistant answers Zepto policy questions using eight policy documents, `all-MiniLM-L6-v2` embeddings, ChromaDB retrieval, and a LangGraph workflow.

The system supports:
1. Policy questions — retrieve relevant policy documents and generate a grounded answer.
2. General questions — return a deterministic response explaining that the assistant currently answers Zepto policy questions only.

The default configuration uses `MOCK_LLM=1`, so no external LLM API or paid service is required.

---

## 2. Architecture

```text
Zepto Policy Documents
        |
        v
Document Loading
        |
        v
Document Preparation
        |
        v
all-MiniLM-L6-v2 Embeddings
        |
        v
ChromaDB Vector Store
        |
User Query
        |
        v
FastAPI POST /ask
        |
        v
LangGraph StateGraph
        |
        v
classify_intent
        |
        +-----------------------------+
        |                             |
        v                             v
policy_question                general_question
        |                             |
        v                             v
retrieve_and_answer             direct_answer
        |                             |
        +-------------+---------------+
                      |
                      v
              Pydantic Validation
                      |
                      v
                 JSON Response
```

### Main components

| Component | File | Purpose |
|---|---|---|
| Document corpus | `docs/doc_01.txt` - `doc_08.txt` | Zepto policy knowledge base |
| Vector store | `app/vector_store.py` | Loads documents, creates embeddings and stores them in ChromaDB |
| Prompt construction | `app/prompt.py` | Creates structured grounded prompts |
| LangGraph workflow | `app/graph.py` | Performs intent classification, routing, retrieval and answering |
| Response schema | `app/schemas.py` | Validates the final JSON response |
| FastAPI application | `app/main.py` | Exposes the `/ask` API |
| Docker configuration | `Dockerfile` | Builds and runs the application in a container |

---

## 3. Document Corpus

The assistant uses eight Zepto policy documents:

```text
docs/
├── doc_01.txt   # Delivery policy
├── doc_02.txt   # Returns and refunds
├── doc_03.txt   # Membership tiers
├── doc_04.txt   # Order tracking
├── doc_05.txt   # Order cancellation
├── doc_06.txt   # Damaged, spoiled or missing items
├── doc_07.txt   # Gift cards
└── doc_08.txt   # Customer support
```

Each document represents one policy area.

The documents are loaded by `vector_store.py`, embedded using `all-MiniLM-L6-v2`, and stored in a persistent ChromaDB collection named `zepto_policy_corpus`.

The ChromaDB collection uses cosine similarity for semantic retrieval.

---

## 4. Embedding and Retrieval

The embedding model used by the project is:

```text
all-MiniLM-L6-v2
```

During ingestion, each policy document is converted into an embedding vector and stored in ChromaDB.

For every policy question, the query is embedded using the same model. The application then retrieves the top three most relevant documents using cosine similarity.

Example:

```text
Query:
How much does priority delivery cost?

Retrieved documents:
1. doc_01
2. doc_05
3. doc_03
```

`doc_01` contains the delivery policy and provides the relevant priority-delivery information.

---

## 5. LangGraph Workflow

The application uses a LangGraph `StateGraph`.

The state is defined using `TypedDict`:

```python
class SupportState(TypedDict, total=False):
    query: str
    intent: str
    answer: str
    sources: list[str]
    confidence: float
    prompt: str
```

The graph contains three required nodes.

### 5.1 `classify_intent`

This is the first node.

With the default:

```text
MOCK_LLM=1
```

the application uses a deterministic keyword heuristic.

The policy keywords are:

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

If the lowercased query contains any of these keywords, the intent becomes:

```text
policy_question
```

Otherwise:

```text
general_question
```

No LLM call is made in mock mode.

### 5.2 `retrieve_and_answer`

This node handles `policy_question`.

It:
1. Embeds the user query.
2. Queries ChromaDB.
3. Retrieves the top three documents.
4. Builds the grounded support prompt.
5. Uses the highest-ranked document for the deterministic mock answer.
6. Returns the retrieved document IDs as sources.

In mock mode, the answer begins with:

```text
Based on the retrieved context:
```

and contains an approximately 200-character excerpt from the highest-ranked document.

### 5.3 `direct_answer`

This node handles `general_question`.

In mock mode, it returns:

```text
I can only answer questions about Zepto policies right now.
```

No ChromaDB retrieval is required for a general question, so the `sources` list is empty.

---

## 6. Conditional Routing

The graph uses a conditional edge after `classify_intent`:

```text
classify_intent
       |
       +---- policy_question ----> retrieve_and_answer
       |
       +---- general_question --> direct_answer
```

The routing decision does not depend on `MOCK_LLM`.

---

## 7. Structured Prompt

The retrieval prompt is implemented in:

```text
app/prompt.py
```

The prompt contains the required components:

```text
ROLE
CONTEXT
TASK
FORMAT
LENGTH
```

It also contains the explicit negative constraint:

```text
Do not answer using information not present in the provided context.
```

If the context does not contain enough information, the prompt instructs the assistant to state that the available Zepto policy context does not provide the answer.

A few-shot example is included:

```text
Question:
How long does Zepto take to deliver?

Context:
Zepto delivers grocery and household essentials within 10 to 30
minutes of order confirmation, depending on the delivery zone and
current order volume.

Answer:
Zepto delivery typically takes 10 to 30 minutes after order
confirmation, depending on the delivery zone and current order volume.
```

---

## 8. MOCK_LLM Mode

The application defaults to:

```text
MOCK_LLM=1
```

This mode provides deterministic local execution and does not require an external LLM API.

For policy questions:

```python
answer = f"Based on the retrieved context: {top_chunk_snippet}"
```

For general questions:

```text
I can only answer questions about Zepto policies right now.
```

The embedding model and ChromaDB retrieval still operate normally. Mock mode replaces only the final LLM generation step.

---

## 9. Response Schema

The final response is validated using Pydantic:

```python
class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: float
```

The confidence value is constrained to:

```text
0.0 <= confidence <= 1.0
```

Example policy response:

```json
{
  "answer": "Based on the retrieved context: ...",
  "sources": ["doc_01", "doc_05", "doc_03"],
  "confidence": 0.9
}
```

Example general response:

```json
{
  "answer": "I can only answer questions about Zepto policies right now.",
  "sources": [],
  "confidence": 1.0
}
```

---

## 10. Validation and Retry Logic

Response validation is implemented in:

```text
app/schemas.py
```

The `validate_response()` function first validates the generated payload against the Pydantic schema.

For an optional real-LLM integration, invalid output can be sent through a corrective retry instruction.

The implementation supports up to two additional validation attempts.

The corrective instruction requires:
- `answer` to be a string
- `sources` to be a list of document or chunk IDs
- `confidence` to be a number between 0 and 1
- only valid JSON to be returned

The default mock mode is deterministic and does not require retries.

---

## 11. FastAPI API

The application exposes:

```text
POST /ask
```

Request:

```json
{
  "query": "How much does priority delivery cost?"
}
```

Response:

```json
{
  "answer": "Based on the retrieved context: ...",
  "sources": ["doc_01", "doc_05", "doc_03"],
  "confidence": 0.9
}
```

The application runs using Uvicorn on port `7860`.

---

## 12. Local Execution

From the repository root:

```powershell
cd support_assistant
```

Make sure the Python environment is activated and dependencies are installed.

Then:

```powershell
cd app
uvicorn main:app --host 0.0.0.0 --port 7860
```

Open Swagger:

```text
http://127.0.0.1:7860/docs
```

---

## 13. Example API Calls

### Example 1 — Policy question

Request:

```json
{
  "query": "How much does priority delivery cost?"
}
```

Response:

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

The query is classified as a policy question and routed to `retrieve_and_answer`. The correct delivery policy document, `doc_01`, is the top retrieved document.

### Example 2 — General question

Request:

```json
{
  "query": "What is the capital of India?"
}
```

Response:

```json
{
  "answer": "I can only answer questions about Zepto policies right now.",
  "sources": [],
  "confidence": 1.0
}
```

The query is classified as `general_question` and routed to `direct_answer`. No policy documents are retrieved.

---

## 14. Docker

The application includes a Dockerfile for containerized execution.

Build the image from the repository root:

```powershell
docker build --no-cache -t zepto-support-assistant ./support_assistant
```

Run the container:

```powershell
docker run --rm -p 7860:7860 zepto-support-assistant
```

The container starts Uvicorn on:

```text
0.0.0.0:7860
```

Access it from the host machine:

```text
http://127.0.0.1:7860/docs
```

The Docker image was successfully built and the container was successfully started and tested using both the policy and general-question API examples.

---

## 15. Data Flow

```text
1. Eight policy documents are stored in docs/.

2. vector_store.py loads the documents.

3. all-MiniLM-L6-v2 converts the documents into embeddings.

4. ChromaDB stores the embeddings and source documents.

5. A user sends a question through POST /ask.

6. classify_intent determines the question type.

7. Policy questions are sent to retrieve_and_answer.

8. The query is embedded and the top three documents are retrieved.

9. The retrieved context is inserted into the structured prompt.

10. MOCK_LLM mode produces a deterministic grounded response.

11. General questions are sent to direct_answer.

12. The final payload is validated by Pydantic.

13. FastAPI returns the validated JSON response.
```

---

## 16. Project Files

```text
support_assistant/
├── app/
│   ├── graph.py
│   ├── main.py
│   ├── prompt.py
│   ├── schemas.py
│   └── vector_store.py
│
├── data/
│   └── chroma/
│
├── docs/
│   ├── doc_01.txt
│   ├── doc_02.txt
│   ├── doc_03.txt
│   ├── doc_04.txt
│   ├── doc_05.txt
│   ├── doc_06.txt
│   ├── doc_07.txt
│   └── doc_08.txt
│
├── .dockerignore
├── Dockerfile
├── README.md
└── requirements.txt
```

---

## 17. Optional Real LLM Extension

The project is intentionally configured to work without a paid external LLM service.

The code separates deterministic mock behavior from the optional real-LLM generation path.

A future extension can connect a real LLM provider when:

```text
MOCK_LLM=0
```

The real generation path should continue to use only the retrieved policy context for policy questions and validate the generated response using the existing Pydantic schema and retry mechanism.

No paid service is required for the current assignment submission.

---

## 18. Module 3 Requirements Covered

This implementation covers the major Module 3 requirements:

- Eight Zepto policy documents
- Embedding with `all-MiniLM-L6-v2`
- ChromaDB vector storage
- Top-three semantic retrieval
- Structured role/context/task/format/length prompt
- Explicit negative constraint
- Few-shot example
- LangGraph `StateGraph`
- TypedDict state
- `classify_intent`
- `retrieve_and_answer`
- `direct_answer`
- Conditional graph routing
- Deterministic `MOCK_LLM` behavior
- Pydantic response validation
- Optional real-LLM retry mechanism
- FastAPI `/ask`
- Dockerized execution
- Local API demonstration
