from dotenv import load_dotenv
load_dotenv()

import os
from typing import TypedDict, Optional

from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, END


from utils import (
    resource_agent_kaggle,
    format_resources_markdown,
    search_huggingface_datasets,
    search_github_repos,
)


llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.environ["GROQ_API_KEY"],
    temperature=0.1
)

search_tool = TavilySearchResults(
    max_results=1,
    api_key=os.environ["TAVILY_API_KEY"]
)


RESEARCH_AGENT_PROMPT = """You are an expert market research analyst. Research the provided company/industry and identify:
1. Industry segment and characteristics
2. Company's key offerings and strategic focus areas
3. Major competitors and their AI initiatives
4. Current challenges and opportunities

Provide comprehensive, well-structured research with citations from reliable sources."""

USE_CASE_AGENT_PROMPT = """You are an AI solutions architect. Analyze the research and identify relevant AI/ML use cases that address:
1. Operational efficiency improvements
2. Customer experience enhancements
3. Revenue growth opportunities
4. Competitive advantages through AI adoption

For each use case, provide:
- Clear title and description
- Business problem it solves
- Required AI technologies
- Expected impact and benefits
- Implementation complexity (Low/Medium/High)"""

PROPOSAL_AGENT_PROMPT = """You are a senior consultant. Create a business proposal that includes:
1. Executive summary
2. Top recommended use cases with implementation priority
3. Expected business impact and ROI considerations
4. Technical requirements and resource recommendations
5. Implementation roadmap"""


class MarketState(TypedDict):
    query: str
    research: Optional[str]
    use_cases: Optional[str]
    resources: Optional[str]
    proposal: Optional[str]


def research_agent_node(state: MarketState) -> MarketState:
    query = f"{RESEARCH_AGENT_PROMPT}\n\nResearch: {state['query']}"
    web_data = search_tool.invoke({"query": state["query"]})
    web_str = str(web_data)
    response = llm.invoke(query + "\n\nWeb Data:\n" + web_str)
    state["research"] = response.content[:600]
    return state


def use_case_agent_node(state: MarketState) -> MarketState:
    truncated_research = (state["research"] or "")[:300]
    query = f"{USE_CASE_AGENT_PROMPT}\n\nBased on: {truncated_research}"
    response = llm.invoke(query)
    state["use_cases"] = response.content[:400]
    return state


def resource_agent_node(state: MarketState) -> MarketState:
    use_cases = state["use_cases"] or ""
    company = state["query"]

    kaggle = resource_agent_kaggle(use_cases, company)
    hf = search_huggingface_datasets(company, 2)
    gh = search_github_repos(company, 2)

    if hf: kaggle["HuggingFace Datasets"] = hf
    if gh: kaggle["GitHub Repositories"] = gh

    state["resources"] = format_resources_markdown(kaggle)
    return state


def proposal_agent_node(state: MarketState) -> MarketState:
    r = (state["research"] or "")[:200]
    u = (state["use_cases"] or "")[:200]
    s = (state["resources"] or "")[:100]

    query = f"{PROPOSAL_AGENT_PROMPT}\n\nResearch: {r}\nUse Cases: {u}\nResources: {s}"
    response = llm.invoke(query)

    state["proposal"] = response.content
    return state


graph = StateGraph(MarketState)

graph.add_node("research_agent", research_agent_node)
graph.add_node("use_case_agent", use_case_agent_node)
graph.add_node("resource_agent", resource_agent_node)
graph.add_node("proposal_agent", proposal_agent_node)

graph.set_entry_point("research_agent")

graph.add_edge("research_agent", "use_case_agent")
graph.add_edge("use_case_agent", "resource_agent")
graph.add_edge("resource_agent", "proposal_agent")
graph.add_edge("proposal_agent", END)

app = graph.compile()

def orchestrate_agents_langgraph(company: str):
    init_state: MarketState = {
        "query": company,
        "research": None,
        "use_cases": None,
        "resources": None,
        "proposal": None
    }
    return app.invoke(init_state)
