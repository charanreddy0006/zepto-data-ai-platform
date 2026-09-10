from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field, ValidationError


class AskResponse(BaseModel):
    """
    Final validated response returned by the support assistant.
    """

    answer: str
    sources: list[str]
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )


def validate_response(
    payload: dict[str, Any],
    generator: Callable[[str], dict[str, Any]] | None = None,
    max_retries: int = 2,
) -> AskResponse:
    """
    Validate an LLM or mock response against the Pydantic schema.

    If validation fails and a generator is provided, the generator
    may be called up to two additional times with a corrective
    instruction.

    The default mock path does not need retries because it produces
    deterministic valid output.
    """

    try:
        return AskResponse.model_validate(payload)

    except ValidationError as first_error:

        if generator is None:
            raise first_error

        last_error = first_error

        for _ in range(max_retries):
            corrective_instruction = (
                "Correct your previous response so that it strictly "
                "matches the required JSON schema: "
                "answer must be a string, sources must be a list of "
                "document or chunk IDs, and confidence must be a "
                "number between 0 and 1. Return only valid JSON."
            )

            try:
                retry_payload = generator(corrective_instruction)
                return AskResponse.model_validate(retry_payload)

            except ValidationError as retry_error:
                last_error = retry_error

        raise last_error