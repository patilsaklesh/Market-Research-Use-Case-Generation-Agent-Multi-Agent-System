from dotenv import load_dotenv
load_dotenv()

import os
from typing import Dict
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage

# Groq LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile", 
    api_key=os.environ.get("GROQ_API_KEY"),
    temperature=0.1,
    max_tokens=300
)

search_tool = TavilySearchResults(
    max_results=1,  # 1 to reduce tokens
    api_key=os.environ.get("TAVILY_API_KEY")
)

# Import utils functions
from utils import resource_agent_kaggle, format_resources_markdown, search_huggingface_datasets, search_github_repos

# Agent Prompts 
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

def research_agent(company_or_industry: str) -> str:
    """Research agent that conducts industry/company research"""
    try:
        query = f"Research {company_or_industry} industry overview and key facts"
        
        agent = create_react_agent(
            model=llm,  
            tools=[search_tool],
            state_modifier=RESEARCH_AGENT_PROMPT
        )
        
        state = {"messages": [HumanMessage(content=query)]}
        response = agent.invoke(state)
        messages = response.get("messages", [])
        ai_messages = [message.content for message in messages if isinstance(message, AIMessage)]
        
        return ai_messages[-1][:500] + "..." if ai_messages and len(ai_messages[-1]) > 500 else ai_messages[-1] if ai_messages else "No research results found"
    
    except Exception as e:
        return f"Research error: {str(e)}"

def use_case_agent(research_data: str) -> str:
    """Use case agent that generates AI use cases"""
    try:
        # TRUNCATE research data severely
        truncated_research = research_data[:300] + "..." if len(research_data) > 300 else research_data
        query = f"Based on: {truncated_research}\n\nSuggest 2 AI use cases"
        
        agent = create_react_agent(
            model=llm,  
            tools=[],
            state_modifier=USE_CASE_AGENT_PROMPT
        )
        
        state = {"messages": [HumanMessage(content=query)]}
        response = agent.invoke(state)
        messages = response.get("messages", [])
        ai_messages = [message.content for message in messages if isinstance(message, AIMessage)]
        
        return ai_messages[-1][:400] + "..." if ai_messages and len(ai_messages[-1]) > 400 else ai_messages[-1] if ai_messages else "No use cases generated"
    
    except Exception as e:
        return f"Use case error: {str(e)}"

def resource_agent(use_cases: str, company_industry: str) -> str:
    """Resource agent that finds relevant datasets and resources"""
    try:
        #  resources from Kaggle (with fallback)
        kaggle_resources = resource_agent_kaggle(use_cases, company_industry)
        
        #  additional resources 
        hf_resources = search_huggingface_datasets(company_industry, 2)
        github_resources = search_github_repos(company_industry, 2)
        
        if hf_resources:
            kaggle_resources["HuggingFace Datasets"] = hf_resources
        
        if github_resources:
            kaggle_resources["GitHub Repositories"] = github_resources
        
        return format_resources_markdown(kaggle_resources)
    
    except Exception as e:
        return f"Resource error: {str(e)}"

def proposal_agent(research: str, use_cases: str, resources: str) -> str:
    """Proposal agent that creates a final business proposal"""
    try:
        # SEVERELY truncate all inputs
        truncated_research = research[:200] + "..." if len(research) > 200 else research
        truncated_use_cases = use_cases[:200] + "..." if len(use_cases) > 200 else use_cases
        truncated_resources = resources[:100] + "..." if len(resources) > 100 else resources
        
        query = f"Research: {truncated_research}\nUse Cases: {truncated_use_cases}\nResources: {truncated_resources}\n\nCreate brief proposal"
        
        agent = create_react_agent(
            model=llm,  
            tools=[],
            state_modifier=PROPOSAL_AGENT_PROMPT
        )
        
        state = {"messages": [HumanMessage(content=query)]}
        response = agent.invoke(state)
        messages = response.get("messages", [])
        ai_messages = [message.content for message in messages if isinstance(message, AIMessage)]
        
        return ai_messages[-1] if ai_messages else "No proposal generated"
    
    except Exception as e:
        return f"Proposal error: {str(e)}"

def orchestrate_agents(company_or_industry: str) -> Dict[str, str]:
    """Orchestrate the multi-agent workflow"""
    print("Starting research agent...")
    research = research_agent(company_or_industry)
    
    print("Starting use case agent...")
    use_cases = use_case_agent(research)
    
    print("Starting resource agent...")
    resources = resource_agent(use_cases, company_or_industry)
    
    print("Starting proposal agent...")
    proposal = proposal_agent(research, use_cases, resources)
    
    return {
        "research": research,
        "use_cases": use_cases,
        "resources": resources,
        "proposal": proposal
    }