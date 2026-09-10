from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from pydantic import BaseModel


from graph import graph
from schemas import AskResponse, validate_response
from vector_store import build_index


# Build/update the local ChromaDB index when the application starts.
build_index()


app = FastAPI(
    title="Zepto Support Assistant",
    description="A policy-aware support assistant using ChromaDB and LangGraph.",
    version="1.0.0",
)


class AskRequest(BaseModel):
    query: str = Field(..., min_length=1)


@app.get("/")
def root():
    return {
        "message": "Zepto Support Assistant is running.",
        "endpoint": "POST /ask",
    }


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    try:
        result = graph.invoke(
            {
                "query": request.query,
            }
        )

        payload = {
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "confidence": result.get("confidence", 0.0),
        }

        validated_response = validate_response(payload)

        return validated_response

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to process the request: {error}",
        ) from error