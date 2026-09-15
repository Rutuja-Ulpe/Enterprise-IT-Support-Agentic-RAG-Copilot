import json
import logging
import re
from typing import Literal

from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END

from app.core.config import get_settings
from app.rag.state import AgentState
from app.rag.vectorstore import get_retriever


logger = logging.getLogger(__name__)
settings = get_settings()

_llm = None
_web_search = None


# --------------------------------------------------
# LLM
# --------------------------------------------------

def llm():
    global _llm

    if _llm is None:
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is missing")

        _llm = ChatGroq(
            model=settings.groq_model,
            temperature=0,
            api_key=settings.groq_api_key,
        )

    return _llm


# --------------------------------------------------
# Tavily Web Search
# --------------------------------------------------

def web_search_tool():
    global _web_search

    if _web_search is None:
        if not settings.tavily_api_key:
            raise RuntimeError("TAVILY_API_KEY is missing")

        _web_search = TavilySearch(
            tavily_api_key=settings.tavily_api_key,
            max_results=5,
            topic="general",
            include_answer=True,
            include_raw_content=False,
        )

    return _web_search


# --------------------------------------------------
# Helper Functions
# --------------------------------------------------

def add_trace(state: AgentState, message: str):
    return [
        *state.get("trace", []),
        message,
    ]


def extract_json(text: str) -> dict:
    """
    Extract JSON object from normal text or markdown code block.
    """

    text = str(text).strip()

    # Remove markdown code fences
    text = re.sub(r"```json", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text).strip()

    # Try direct JSON parsing
    try:
        result = json.loads(text)

        if isinstance(result, dict):
            return result

    except json.JSONDecodeError:
        pass

    # Find JSON object inside text
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)

    if match:
        try:
            result = json.loads(match.group(0))

            if isinstance(result, dict):
                return result

        except json.JSONDecodeError:
            pass

    return {}


# --------------------------------------------------
# Route Question
# --------------------------------------------------

def route_question(state: AgentState):
    response = llm().invoke(
        f"""
You are a router for an Enterprise IT Support Assistant.

Choose exactly one route.

Use "kb" for:
- Company IT policies
- VPN
- Password reset
- MFA
- Laptop setup
- Software access
- Security
- Email
- Devices
- Troubleshooting
- Technical support

Use "direct" only for:
- Greetings
- Thanks
- Casual conversation

User question:
{state["question"]}

Return only valid JSON in this format:

{{"route": "kb"}}

or:

{{"route": "direct"}}
"""
    )

    raw_response = response.content
    parsed_response = extract_json(raw_response)

    selected_route = parsed_response.get("route")

    # Fallback if the model does not return proper JSON
    if selected_route not in {"kb", "direct"}:
        lower_response = str(raw_response).lower()

        if any(
            word in lower_response
            for word in [
                "vpn",
                "password",
                "mfa",
                "laptop",
                "software",
                "email",
                "security",
                "technical",
                "support",
                "troubleshoot",
                "it policy",
            ]
        ):
            selected_route = "kb"
        else:
            selected_route = "direct"

    return {
        "source_used": selected_route,
        "trace": add_trace(
            state,
            f"Router → {selected_route.upper()}",
        ),
    }


def route_after_router(
    state: AgentState,
) -> Literal["retrieve_kb", "direct_answer"]:

    selected_route = state.get("source_used", "direct")

    if selected_route == "kb":
        return "retrieve_kb"

    return "direct_answer"


# --------------------------------------------------
# Retrieve Private Knowledge Base
# --------------------------------------------------

def retrieve_kb(state: AgentState):
    documents = get_retriever().invoke(
        state["current_query"]
    )

    return {
        "kb_docs": documents,
        "trace": add_trace(
            state,
            f"Private KB retrieval → {len(documents)} chunks",
        ),
    }


# --------------------------------------------------
# Grade Private KB Evidence
# --------------------------------------------------

def grade_kb(state: AgentState):
    context = "\n\n".join(
        (
            f"Source: {document.metadata.get('source', 'unknown')}\n"
            f"{document.page_content}"
        )
        for document in state["kb_docs"]
    )

    response = llm().invoke(
        f"""
You are grading evidence for an Enterprise IT Support Assistant.

User question:
{state["question"]}

Private company knowledge base evidence:
{context}

Return "good" only when the evidence is sufficient to answer
the question confidently and specifically.

Otherwise return "weak".

Return only JSON:

{{"grade": "good"}}

or:

{{"grade": "weak"}}
"""
    )

    parsed_response = extract_json(response.content)
    selected_grade = parsed_response.get("grade")

    if selected_grade not in {"good", "weak"}:
        selected_grade = "weak"

    return {
        "kb_grade": selected_grade,
        "trace": add_trace(
            state,
            f"KB evidence grade → {selected_grade.upper()}",
        ),
    }


def after_kb(
    state: AgentState,
) -> Literal["generate_from_kb", "search_web"]:

    if state.get("kb_grade") == "good":
        return "generate_from_kb"

    return "search_web"


# --------------------------------------------------
# Web Search
# --------------------------------------------------

def search_web(state: AgentState):
    result = web_search_tool().invoke(
        {
            "query": state["current_query"],
        }
    )

    lines = []
    citations = []

    if isinstance(result, dict):
        search_answer = result.get("answer")

        if search_answer:
            lines.append(
                f"Search answer: {search_answer}"
            )

        for item in result.get("results", []):
            title = item.get("title", "")
            url = item.get("url", "")
            content = item.get("content", "")

            lines.append(
                f"Title: {title}\n"
                f"URL: {url}\n"
                f"Content: {content}"
            )

            citations.append(
                {
                    "title": title or url,
                    "url": url,
                    "type": "web",
                }
            )

    else:
        lines.append(str(result))

    return {
        "web_results": "\n\n".join(lines),
        "citations": citations,
        "source_used": "web",
        "trace": add_trace(
            state,
            "Web fallback → Tavily search",
        ),
    }


# --------------------------------------------------
# Grade Web Evidence
# --------------------------------------------------

def grade_web(state: AgentState):
    response = llm().invoke(
        f"""
You are grading external web evidence.

User question:
{state["question"]}

Web evidence:
{state["web_results"]}

Return "good" if the evidence is directly relevant and sufficient.
Otherwise return "weak".

Return only JSON:

{{"grade": "good"}}

or:

{{"grade": "weak"}}
"""
    )

    parsed_response = extract_json(response.content)
    selected_grade = parsed_response.get("grade")

    if selected_grade not in {"good", "weak"}:
        selected_grade = "weak"

    return {
        "web_grade": selected_grade,
        "trace": add_trace(
            state,
            f"Web evidence grade → {selected_grade.upper()}",
        ),
    }


def after_web(
    state: AgentState,
) -> Literal[
    "generate_from_web",
    "rewrite_query",
    "insufficient",
]:

    if state.get("web_grade") == "good":
        return "generate_from_web"

    if state.get("retry_count", 0) < settings.max_retries:
        return "rewrite_query"

    return "insufficient"


# --------------------------------------------------
# Rewrite Query
# --------------------------------------------------

def rewrite_query(state: AgentState):
    response = llm().invoke(
        f"""
Rewrite the following IT support question for better
private knowledge base retrieval and web search.

Preserve the original intent.
Add useful technical keywords.
Do not answer the question.
Return only the rewritten query.

Original question:
{state["question"]}
"""
    )

    rewritten_query = str(response.content).strip()

    return {
        "current_query": rewritten_query,
        "retry_count": state["retry_count"] + 1,
        "trace": add_trace(
            state,
            f"Query rewrite → {rewritten_query}",
        ),
    }


# --------------------------------------------------
# Generate Answer From Private KB
# --------------------------------------------------

def generate_from_kb(state: AgentState):
    context = "\n\n".join(
        (
            f"[Source: {document.metadata.get('source', 'unknown')}]\n"
            f"{document.page_content}"
        )
        for document in state["kb_docs"]
    )

    response = llm().invoke(
        f"""
You are an Enterprise IT Support Copilot.

Answer only from the private company knowledge base below.

Rules:
- Be concise and actionable.
- Show steps clearly when required.
- Do not invent company policies.
- Mention that the answer is based on the private company
  knowledge base.

User question:
{state["question"]}

Private company knowledge base:
{context}
"""
    )

    answer = response.content

    citations = []
    seen_sources = set()

    for document in state["kb_docs"]:
        source = document.metadata.get(
            "source",
            "Private KB",
        )

        if source not in seen_sources:
            seen_sources.add(source)

            citations.append(
                {
                    "title": source.split("/")[-1],
                    "url": "",
                    "type": "private_kb",
                }
            )

    return {
        "answer": answer,
        "source_used": "private_kb",
        "citations": citations,
        "trace": add_trace(
            state,
            "Answer generation → PRIVATE KB",
        ),
    }


# --------------------------------------------------
# Generate Answer From Web
# --------------------------------------------------

def generate_from_web(state: AgentState):
    response = llm().invoke(
        f"""
You are an Enterprise IT Support Copilot.

The private company knowledge base was insufficient.

Answer only from the external web evidence below.

Clearly mention that:
- This is external web information.
- The information may require IT validation before changing
  company-managed systems.

User question:
{state["question"]}

External web evidence:
{state["web_results"]}
"""
    )

    return {
        "answer": response.content,
        "source_used": "web_search",
        "trace": add_trace(
            state,
            "Answer generation → WEB SEARCH",
        ),
    }


# --------------------------------------------------
# Direct Answer
# --------------------------------------------------

def direct_answer(state: AgentState):
    response = llm().invoke(
        f"""
Respond briefly and naturally to this message:

{state["question"]}
"""
    )

    return {
        "answer": response.content,
        "source_used": "direct",
        "trace": add_trace(
            state,
            "Direct response → no retrieval",
        ),
    }


# --------------------------------------------------
# Insufficient Evidence
# --------------------------------------------------

def insufficient(state: AgentState):
    return {
        "answer": (
            "I couldn't find enough reliable evidence in the "
            "company knowledge base or external search to answer "
            "confidently. Please contact the IT help desk or "
            "provide more details."
        ),
        "source_used": "insufficient_evidence",
        "trace": add_trace(
            state,
            "Stopped → insufficient reliable evidence",
        ),
    }


# --------------------------------------------------
# Build LangGraph
# --------------------------------------------------

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("route_question", route_question)
    graph.add_node("retrieve_kb", retrieve_kb)
    graph.add_node("grade_kb", grade_kb)
    graph.add_node("search_web", search_web)
    graph.add_node("grade_web", grade_web)
    graph.add_node("rewrite_query", rewrite_query)
    graph.add_node("generate_from_kb", generate_from_kb)
    graph.add_node("generate_from_web", generate_from_web)
    graph.add_node("direct_answer", direct_answer)
    graph.add_node("insufficient", insufficient)

    graph.add_edge(
        START,
        "route_question",
    )

    graph.add_conditional_edges(
        "route_question",
        route_after_router,
        {
            "retrieve_kb": "retrieve_kb",
            "direct_answer": "direct_answer",
        },
    )

    graph.add_edge(
        "retrieve_kb",
        "grade_kb",
    )

    graph.add_conditional_edges(
        "grade_kb",
        after_kb,
        {
            "generate_from_kb": "generate_from_kb",
            "search_web": "search_web",
        },
    )

    graph.add_edge(
        "search_web",
        "grade_web",
    )

    graph.add_conditional_edges(
        "grade_web",
        after_web,
        {
            "generate_from_web": "generate_from_web",
            "rewrite_query": "rewrite_query",
            "insufficient": "insufficient",
        },
    )

    graph.add_edge(
        "rewrite_query",
        "retrieve_kb",
    )

    graph.add_edge(
        "generate_from_kb",
        END,
    )

    graph.add_edge(
        "generate_from_web",
        END,
    )

    graph.add_edge(
        "direct_answer",
        END,
    )

    graph.add_edge(
        "insufficient",
        END,
    )

    return graph.compile()


agent_graph = build_graph()


# --------------------------------------------------
# Ask Agent
# --------------------------------------------------

def ask(question: str):
    initial_state: AgentState = {
        "question": question,
        "current_query": question,
        "kb_docs": [],
        "web_results": "",
        "kb_grade": "",
        "web_grade": "",
        "answer": "",
        "source_used": "",
        "retry_count": 0,
        "trace": [],
        "citations": [],
    }

    return agent_graph.invoke(initial_state)