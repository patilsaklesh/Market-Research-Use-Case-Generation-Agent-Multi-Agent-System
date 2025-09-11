from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import time
from agentai import orchestrate_agents
from utils import save_resources_markdown, save_architecture_mermaid, generate_full_report

# Set page config
st.set_page_config(
    page_title="AI Use Case Generator",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header { 
        font-size: 3rem; 
        color: #1f77b4; 
        text-align: center; 
    }
    .sub-header { 
        font-size: 1.5rem; 
        color: #ff7f0e; 
        margin-top: 1.5rem; 
    }
    .stButton button { 
        background-color: #1f77b4; 
        color: white; 
        font-weight: bold; 
        width: 200px;       /* fixed width */
        display: block;      /* needed for margin auto to work */
        margin: 0 auto;      /* centers the button horizontally */
    }
    .result-box { 
        background-color: #f0f2f6; 
        padding: 1rem; 
        border-radius: 0.5rem; 
        margin-bottom: 1rem; 
    }
</style>
""", unsafe_allow_html=True)


# App header
st.markdown('<h1 class="main-header">Market Research & Use Case Generation Agent</h1>', unsafe_allow_html=True)
st.markdown("Generates AI use cases for any company or industry")

# Input section
company_input = st.text_input(
    "Enter a company or industry :",
    placeholder="e.g., Tesla, Healthcare, Retail Banking"
)

generate_btn = st.button("Generate Use Cases", type="primary")

# Initialize session state
if "results" not in st.session_state:
    st.session_state.results = None

# Handle generation
if generate_btn and company_input:
    with st.spinner("Generating AI use cases... This may take 1-2 minutes."):
        try:
            results = orchestrate_agents(company_input)
            st.session_state.results = results
            
            # Save outputs
            save_resources_markdown(results["resources"], company_input)
            save_architecture_mermaid()
            generate_full_report(results, company_input)
            
            st.success("Analysis complete!")
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Display results
if st.session_state.results:
    results = st.session_state.results
    
    # Download buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "Download Resources",
            results["resources"],
            file_name=f"ai_resources_{company_input.replace(' ', '_')}.md",
            mime="text/markdown"
        )
    with col2:
        st.download_button(
            "Download Full Report",
            f"# AI Use Case Analysis\n\n{results['research']}\n\n{results['use_cases']}\n\n{results['resources']}\n\n{results['proposal']}",
            file_name=f"ai_use_cases_{company_input.replace(' ', '_')}.md",
            mime="text/markdown"
        )
    
    # Display results
    st.markdown('<h2 class="sub-header">Research Findings</h2>', unsafe_allow_html=True)
    st.info(results["research"])
    
    st.markdown('<h2 class="sub-header">AI Use Cases</h2>', unsafe_allow_html=True)
    st.success(results["use_cases"])
    
    st.markdown('<h2 class="sub-header">Resources</h2>', unsafe_allow_html=True)
    st.warning(results["resources"])
    
    st.markdown('<h2 class="sub-header">Final Proposal</h2>', unsafe_allow_html=True)
    st.info(results["proposal"])

# Footer
st.markdown("---")
