import streamlit as st
import json
from typing import Dict, Any
import hashlib

def save_analysis_results(analysis_result, filename: str):
    """Save analysis results to JSON file"""
    try:
        results_dict = {
            'filename': filename,
            'summary': analysis_result.summary,
            'executive_summary': analysis_result.executive_summary,
            'key_themes': analysis_result.key_themes,
            'slide_headlines': analysis_result.slide_headlines,
            'word_count': analysis_result.word_count,
            'sentiment': analysis_result.sentiment
        }
        
        # Create download button
        json_string = json.dumps(results_dict, indent=2)
        st.download_button(
            label="💾 Download Analysis Results",
            data=json_string,
            file_name=f"analysis_{filename}.json",
            mime="application/json"
        )
        
    except Exception as e:
        st.error(f"Error saving results: {str(e)}")

def generate_file_hash(file_content: bytes) -> str:
    """Generate hash for file content to check for duplicates"""
    return hashlib.md5(file_content).hexdigest()

@st.cache_data
def cached_document_processing(file_hash: str, file_content: bytes, filename: str):
    """Cache document processing results"""
    # This function would be called by the document processor
    # to cache results and avoid reprocessing the same file
    pass
