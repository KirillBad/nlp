from typing import Annotated
from autogen.agentchat.group import ReplyResult, AgentNameTarget


def classify_query(
    query: Annotated[str, "The user query to classify"],
) -> ReplyResult:
    """
    Classify a user query to route it to the appropriate agent.
    """
    query_lower = query.lower()

    if "переведи" in query_lower or "translate" in query_lower:
        return ReplyResult(
            message=query,
            target=AgentNameTarget("translate_agent"),
        )
    elif (
        "реферат" in query_lower
        or "summary" in query_lower
        or "сократи" in query_lower
        or "analyze" in query_lower
        or "analysis" in query_lower
        or "data" in query_lower
    ):
        return ReplyResult(
            message=query,
            target=AgentNameTarget("report_agent"),
        )
    elif "аннотация" in query_lower or "annotation" in query_lower:
        return ReplyResult(
            message=query,
            target=AgentNameTarget("annotation_agent"),
        )
    elif "ключевые слова" in query_lower or "keywords" in query_lower:
        return ReplyResult(
            message=query,
            target=AgentNameTarget("keyword_agent"),
        )

    return ReplyResult(
        message="No specific keywords found. Please decide the target agent based on the content.",
    )
