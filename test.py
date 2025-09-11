# kaggle test

from dotenv import load_dotenv
load_dotenv()
import os
# test for kaggle dataset search
from kaggle.api.kaggle_api_extended import KaggleApi

# Initialize Kaggle API
api = KaggleApi()
api.authenticate()  # reads KAGGLE_USERNAME and KAGGLE_KEY from environment

# Search datasets
datasets = api.dataset_list(search="customer churn", page=1)

for ds in datasets:
    print(ds.title, f"https://www.kaggle.com/datasets/{ds.ref}")


# test for tavily search tool
from langchain_community.tools.tavily_search import TavilySearchResults
TAVILY_API_KEY=os.environ.get("TAVILY_API_KEY")
search_tool=TavilySearchResults(max_results=2, api_key=TAVILY_API_KEY)
query = "AI applications in healthcare"
results = search_tool.run(query)

# Print results
for r in results:
    print(r.get("title"), r.get("url"), r.get("snippet"))
