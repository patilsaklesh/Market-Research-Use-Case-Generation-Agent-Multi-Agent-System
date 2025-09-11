from dotenv import load_dotenv
load_dotenv()

import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Any

def setup_kaggle_api():
    """Set up and authenticate Kaggle API with proper error handling"""
    try:
        # Create .kaggle directory if it doesn't exist
        kaggle_dir = os.path.expanduser('~/.kaggle')
        os.makedirs(kaggle_dir, exist_ok=True)
        
        # Check if we have environment variables
        username = os.environ.get('KAGGLE_USERNAME')
        key = os.environ.get('KAGGLE_KEY')
        
        kaggle_json_path = os.path.join(kaggle_dir, 'kaggle.json')
        
        # Create kaggle.json from environment variables if they exist
        if username and key and not os.path.exists(kaggle_json_path):
            with open(kaggle_json_path, 'w') as f:
                json.dump({'username': username, 'key': key}, f)
            # Set appropriate permissions
            os.chmod(kaggle_json_path, 0o600)
            print("Created kaggle.json from environment variables")
        
        # Try to import and initialize Kaggle API only if credentials exist
        if os.path.exists(kaggle_json_path):
            from kaggle.api.kaggle_api_extended import KaggleApi
            api = KaggleApi()
            api.authenticate()
            return api
        else:
            print("Kaggle credentials not found. Using fallback mode.")
            return None
            
    except Exception as e:
        print(f"Kaggle API setup failed: {e}")
        return None

def search_kaggle_datasets(query: str, max_results: int = 2) -> List[Dict]:
    """Search for datasets on Kaggle using the official API with fallback"""
    try:
        api = setup_kaggle_api()
        if not api:
            # Fallback: return mock data or use alternative search
            return search_kaggle_fallback(query, max_results)
        
        # Search for datasets using Kaggle API
        datasets = api.dataset_list(search=query)
        
        results = []
        for dataset in datasets[:max_results]:
            results.append({
                "title": dataset.title,
                "url": f"https://www.kaggle.com/datasets/{dataset.ref}",
                "ref": dataset.ref,
                "source": "Kaggle",
                "description": f"Dataset for {query}"
            })
        
        return results
    except Exception as e:
        print(f"Kaggle search error: {e}, using fallback")
        return search_kaggle_fallback(query, max_results)

def search_kaggle_fallback(query: str, max_results: int = 2) -> List[Dict]:
    """Fallback function when Kaggle API is not available"""
    print(f"Using fallback search for: {query}")
    
    # Return mock data or use alternative search methods
    return [
        {
            "title": f"{query} Dataset 1",
            "url": "https://www.kaggle.com/datasets/example1",
            "source": "Kaggle (Fallback)",
            "description": f"Example dataset for {query} - use real Kaggle API for actual results"
        },
        {
            "title": f"{query} Dataset 2", 
            "url": "https://www.kaggle.com/datasets/example2",
            "source": "Kaggle (Fallback)",
            "description": f"Example dataset for {query} - install kaggle.json for real results"
        }
    ][:max_results]

def resource_agent_kaggle(use_cases: str, company_industry: str, max_results: int = 2) -> Dict[str, List[Dict]]:
    """
    Resource agent that finds relevant Kaggle datasets for given AI use cases.
    Returns a dict mapping each use case to a list of dataset resources.
    """
    try:
        # Extract use cases 
        use_case_list = []
        lines = use_cases.split('\n')
        current_case = ""
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('*') or line.startswith('1.') or line.startswith('2.') or ':' in line):
                if current_case:
                    use_case_list.append(current_case.strip())
                current_case = line
            elif line:
                current_case += " " + line
        
        if current_case:
            use_case_list.append(current_case.strip())
        
        # If we can't parse use cases, use the company industry
        if not use_case_list:
            use_case_list = [f"AI applications in {company_industry}"]
        
        resource_map = {}
        
        for case in use_case_list[:2]:  
            query = f"{case} {company_industry}"
            datasets = search_kaggle_datasets(query, max_results)
            
            resource_map[case] = datasets if datasets else [
                {
                    "title": "No specific dataset found", 
                    "url": "https://www.kaggle.com/datasets", 
                    "source": "Kaggle",
                    "description": "Search for relevant datasets on Kaggle"
                }
            ]
        
        return resource_map
        
    except Exception as e:
        print(f"Kaggle resource agent error: {e}")
        return {
            "Error": [{
                "title": f"Kaggle API Error: {str(e)}", 
                "url": "", 
                "source": "Error", 
                "description": "Failed to fetch datasets from Kaggle. Make sure to set up Kaggle API credentials."
            }]
        }

def search_huggingface_datasets(query: str, max_results: int = 2) -> List[Dict]:
    """Search for datasets on HuggingFace"""
    try:
        url = f"https://huggingface.co/api/datasets?search={query}&limit={max_results}"
        response = requests.get(url, timeout=10)
        datasets = response.json()
        
        results = []
        for dataset in datasets:
            results.append({
                "title": dataset.get('id', 'Unknown'),
                "url": f"https://huggingface.co/datasets/{dataset.get('id', '')}",
                "source": "HuggingFace",
                "description": dataset.get('description', 'No description available')[:200] + "...",
                "downloads": dataset.get('downloads', 0),
                "likes": dataset.get('likes', 0)
            })
        
        return results
    except Exception as e:
        print(f"HuggingFace search error: {e}")
        return []

def search_github_repos(query: str, max_results: int = 2) -> List[Dict]:
    """Search for relevant GitHub repositories"""
    try:
        url = f"https://api.github.com/search/repositories?q={query}+AI+dataset&sort=stars&order=desc"
        headers = {'Accept': 'application/vnd.github.v3+json'}
        
        if os.environ.get('GITHUB_TOKEN'):
            headers['Authorization'] = f"token {os.environ.get('GITHUB_TOKEN')}"
        
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        results = []
        for repo in data.get('items', [])[:max_results]:
            results.append({
                "title": repo.get('name', 'Unknown'),
                "url": repo.get('html_url', ''),
                "source": "GitHub",
                "description": repo.get('description', 'No description available'),
                "stars": repo.get('stargazers_count', 0),
                "language": repo.get('language', 'Unknown')
            })
        
        return results
    except Exception as e:
        print(f"GitHub search error: {e}")
        return []

def format_resources_markdown(resource_map: Dict[str, List[Dict]]) -> str:
    """Format resource map as markdown"""
    markdown_content = "# AI Implementation Resources\n\n"
    
    for use_case, resources in resource_map.items():
        markdown_content += f"## Use Case: {use_case}\n\n"
        
        if not resources or (len(resources) == 1 and "Error" in resources[0].get('title', '')):
            markdown_content += "No specific resources found for this use case.\n\n"
            continue
            
        for resource in resources:
            if resource['url']:
                markdown_content += f"- **[{resource['title']}]({resource['url']})** ({resource['source']})\n"
            else:
                markdown_content += f"- **{resource['title']}** ({resource['source']})\n"
            
            if 'description' in resource:
                markdown_content += f"  - {resource['description']}\n"
            if 'downloads' in resource:
                markdown_content += f"  - Downloads: {resource['downloads']}\n"
            if 'stars' in resource:
                markdown_content += f"  - Stars: {resource['stars']}\n"
            markdown_content += "\n"
    
    return markdown_content

def save_resources_markdown(resources: str, company: str) -> str:
    """Save resources to a markdown file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"outputs/resources_{company.replace(' ', '_').lower()}_{timestamp}.md"
    
    content = f"""# AI Resources for {company}

*Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*

{resources}

---
*This resource list was generated automatically using a multi-agent AI system.*
"""
    
    os.makedirs("outputs", exist_ok=True)
    with open(filename, "w") as f:
        f.write(content)
    
    return filename

def save_architecture_mermaid(company: str) -> str:
    """Save system architecture as Mermaid diagram"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"outputs/architecture_{company.replace(' ', '_').lower()}_{timestamp}.mmd"
    
    mermaid_content = """flowchart TD
    A[User Input: Company/Industry] --> B[Research Agent]
    
    subgraph MultiAgentSystem [Multi-Agent Architecture]
        B[Research Agent] --> C[Use Case Agent]
        C --> D[Resource Agent]
        D --> E[Proposal Agent]
    end

    B --> F[Web Search<br>Tavily API]
    D --> G[Dataset Platforms<br>Kaggle, HuggingFace, GitHub]
    
    E --> H[Final Report]
    E --> I[Use Cases with References]
    E --> J[Resource Assets]
    
    style MultiAgentSystem fill:#f9f9f9,stroke:#333,stroke-width:2px
"""
    
    os.makedirs("outputs", exist_ok=True)
    with open(filename, "w") as f:
        f.write(mermaid_content)
    
    return filename

def generate_full_report(results: Dict[str, str], company: str) -> str:
    """Generate a complete markdown report from all results"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"outputs/full_report_{company.replace(' ', '_').lower()}_{timestamp}.md"
    
    report = f"""# AI Use Case Analysis for {company}

*Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*

## Executive Summary

This report provides a comprehensive analysis of AI and Generative AI use cases for {company}, including market research, potential applications, and implementation resources.

## Market Research

{results['research']}

## AI Use Cases

{results['use_cases']}

## Resource Assets

{results['resources']}

## Final Proposal

{results['proposal']}

---
*This report was generated automatically using a multi-agent AI system.*
"""
    
    os.makedirs("outputs", exist_ok=True)
    with open(filename, "w") as f:
        f.write(report)
    
    return filename