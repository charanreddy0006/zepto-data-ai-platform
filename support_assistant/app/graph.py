import os
from typing import TypedDict

from langgraph.graph import StateGraph, END

from prompt import build_support_prompt, build_direct_prompt
from vector_store import retrieve_documents


MOCK_LLM = os.getenv("MOCK_LLM", "1") != "0"


class SupportState(TypedDict, total=False):
    query: str
    intent: str
    answer: str
    sources: list[str]
    confidence: float
    prompt: str


def classify_intent(state: SupportState) -> SupportState:
    """
    Classify the query as either a policy question or a general question.

    By default, MOCK_LLM is enabled and classification uses the required
    deterministic keyword heuristic.
    """

    query = state["query"].lower()

    policy_keywords = [
        "delivery",
        "return",
        "refund",
        "membership",
        "tracking",
        "cancel",
        "gift card",
        "support hours",
    ]

    if any(keyword in query for keyword in policy_keywords):
        intent = "policy_question"
    else:
        intent = "general_question"

    return {
        **state,
        "intent": intent,
    }


def retrieve_and_answer(state: SupportState) -> SupportState:
    """
    Retrieve the top-3 relevant policy documents and generate
    a deterministic mock answer.
    """

    query = state["query"]

    results = retrieve_documents(query, top_k=3)

    documents = results["documents"][0]
    document_ids = results["ids"][0]

    if not documents:
        return {
            **state,
            "answer": "Based on the retrieved context: No relevant policy context was found.",
            "sources": [],
            "confidence": 0.0,
        }

    # Combine the retrieved chunks into context for the structured prompt.
    retrieved_context_parts = []

    for document_id, document in zip(document_ids, documents):
        retrieved_context_parts.append(
            f"{document_id}: {document}"
        )

    retrieved_context = "\n\n".join(retrieved_context_parts)

    # Build the required structured prompt.
    support_prompt = build_support_prompt(
        query=query,
        retrieved_context=retrieved_context,
    )

    # Default assignment mode: deterministic mock response.
    if MOCK_LLM:
        top_chunk_snippet = documents[0][:200]

        answer = (
            f"Based on the retrieved context: "
            f"{top_chunk_snippet}"
        )

        return {
            **state,
            "answer": answer,
            "sources": document_ids,
            "confidence": 0.9,
            "prompt": support_prompt,
        }

    # Optional real-LLM path.
    #
    # The assignment allows a real LLM to be used when MOCK_LLM=0.
    # This implementation intentionally keeps the default mode
    # completely local and deterministic.
    raise RuntimeError(
        "MOCK_LLM=0 requires a configured real LLM integration. "
        "Run with the default MOCK_LLM=1 for the assignment's "
        "deterministic local mode."
    )


def direct_answer(state: SupportState) -> SupportState:
    """
    Return the deterministic response for a general question.
    """

    query = state["query"]

    direct_prompt = build_direct_prompt(query)

    if MOCK_LLM:
        return {
            **state,
            "answer": "I can only answer questions about Zepto policies right now.",
            "sources": [],
            "confidence": 1.0,
            "prompt": direct_prompt,
        }

    raise RuntimeError(
        "MOCK_LLM=0 requires a configured real LLM integration. "
        "Run with the default MOCK_LLM=1 for the assignment's "
        "deterministic local mode."
    )


def route_intent(state: SupportState) -> str:
    """
    Route the graph according to the classified intent.
    """

    if state["intent"] == "policy_question":
        return "retrieve_and_answer"

    return "direct_answer"


def build_graph():
    """
    Build and compile the LangGraph StateGraph.
    """

    workflow = StateGraph(SupportState)

    workflow.add_node(
        "classify_intent",
        classify_intent,
    )

    workflow.add_node(
        "retrieve_and_answer",
        retrieve_and_answer,
    )

    workflow.add_node(
        "direct_answer",
        direct_answer,
    )

    workflow.set_entry_point("classify_intent")

    workflow.add_conditional_edges(
        "classify_intent",
        route_intent,
        {
            "retrieve_and_answer": "retrieve_and_answer",
            "direct_answer": "direct_answer",
        },
    )

    workflow.add_edge(
        "retrieve_and_answer",
        END,
    )

    workflow.add_edge(
        "direct_answer",
        END,
    )

    return workflow.compile()


graph = build_graph()


if __name__ == "__main__":
    print("=" * 60)
    print("Zepto Support Assistant - LangGraph Test")
    print("=" * 60)

    policy_query = "How much does priority delivery cost?"

    policy_result = graph.invoke(
        {
            "query": policy_query,
        }
    )

    print("\nPolicy question:")
    print(policy_query)

    print("\nIntent:")
    print(policy_result["intent"])

    print("\nAnswer:")
    print(policy_result["answer"])

    print("\nSources:")
    print(policy_result["sources"])

    print("\nConfidence:")
    print(policy_result["confidence"])

    print("\n" + "-" * 60)

    general_query = "What is the capital of India?"

    general_result = graph.invoke(
        {
            "query": general_query,
        }
    )

    print("\nGeneral question:")
    print(general_query)

    print("\nIntent:")
    print(general_result["intent"])

    print("\nAnswer:")
    print(general_result["answer"])

    print("\nSources:")
    print(general_result["sources"])

    print("\nConfidence:")
    print(general_result["confidence"])

    print("\n" + "=" * 60)