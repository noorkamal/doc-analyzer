import streamlit as st
import os
from src.document_processor import DocumentProcessor
# Import different analyzers based on choice
from src.ollama_analyzer import OllamaAnalyzer
from src.huggingface_analyzer import HuggingFaceAnalyzer
import plotly.express as px
import pandas as pd

# Page config
st.set_page_config(
    page_title="Private AI Document Analyzer",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

def check_ollama_status():
    """Check if Ollama is running"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    st.title("🔒 Private AI Document Analyzer")
    st.markdown("Upload your documents and get AI-powered insights while keeping your data completely private!")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("🛡️ Privacy & Configuration")
        
        # AI Model Selection
        st.subheader("Choose AI Backend")
        ai_backend = st.selectbox(
            "Select AI Model",
            [
                "Ollama (Recommended)",
                "Hugging Face Transformers (Fully Offline)",
                "OpenAI (Cloud-based - Not Private)"
            ],
            help="Choose how you want to process your documents"
        )
        
        # Configuration based on selection
        if ai_backend == "Ollama (Recommended)":
            st.info("🏠 **Fully Local Processing**\nYour data never leaves your computer!")
            
            if check_ollama_status():
                st.success("✅ Ollama is running!")
                available_models = [
                    "llama3.1",
                    "llama3.1:70b", 
                    "mistral",
                    "codellama",
                    "phi3"
                ]
                selected_model = st.selectbox("Select Model", available_models)
            else:
                st.error("❌ Ollama not detected")
                st.markdown("""
                **Setup Instructions:**
                1. Install Ollama from https://ollama.ai
                2. Run: `ollama pull llama3.1`
                3. Restart this app
                """)
                selected_model = "llama3.1"
        
        elif ai_backend == "Hugging Face Transformers (Fully Offline)":
            st.info("🔒 **100% Offline Processing**\nNo internet required after initial model download!")
            
            hf_models = [
                "facebook/bart-large-cnn",
                "google/flan-t5-base",
                "microsoft/DialoGPT-medium"
            ]
            selected_model = st.selectbox("Select Base Model", hf_models)
            
            st.warning("⏳ First run will download models (~2-4GB). This may take several minutes.")
        
        else:  # OpenAI
            st.warning("⚠️ **Cloud Processing**\nYour data will be sent to OpenAI servers!")
            api_key = st.text_input("OpenAI API Key", type="password")
            selected_model = st.selectbox("Model", ["gpt-3.5-turbo", "gpt-4"])
        
        st.divider()
        
        # Privacy Information
        st.subheader("🔐 Privacy Features")
        if ai_backend.startswith("Ollama") or ai_backend.startswith("Hugging Face"):
            st.success("✅ Local processing only")
            st.success("✅ No data sent to cloud")
            st.success("✅ No internet required*")
            if ai_backend.startswith("Hugging Face"):
                st.caption("*Except for initial model download")
        else:
            st.error("❌ Data sent to OpenAI")
            st.error("❌ Internet required")
        
        st.divider()
        
        # Analysis options
        st.subheader("⚙️ Analysis Options")
        max_themes = st.slider("Number of themes to extract", 3, 10, 5)
        max_headlines = st.slider("Number of slide headlines", 3, 10, 6)
        summary_length = st.slider("Summary length (words)", 100, 500, 300)
    
    # Main content area
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("📁 Upload Document")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['pdf', 'docx', 'pptx'],
            help="Upload PDF, Word, or PowerPoint files"
        )
        
        if uploaded_file:
            st.success(f"File uploaded: {uploaded_file.name}")
            file_size = len(uploaded_file.getvalue())
            st.info(f"File size: {file_size / 1024:.1f} KB")
            
            # Privacy reminder
            if ai_backend.startswith("Ollama") or ai_backend.startswith("Hugging Face"):
                st.success("🔒 This file will be processed locally and privately!")
            else:
                st.warning("⚠️ This file will be sent to OpenAI for processing!")
    
    with col2:
        st.header("📊 Document Analysis")
        
        if uploaded_file:
            # Check if we can proceed based on backend selection
            can_proceed = False
            analyzer = None
            
            if ai_backend == "Ollama (Recommended)":
                if check_ollama_status():
                    analyzer = OllamaAnalyzer(model=selected_model)
                    can_proceed = True
                else:
                    st.error("Please install and run Ollama first!")
            
            elif ai_backend == "Hugging Face Transformers (Fully Offline)":
                try:
                    analyzer = HuggingFaceAnalyzer(model_name=selected_model)
                    can_proceed = True
                except Exception as e:
                    st.error(f"Error loading Hugging Face models: {str(e)}")
                    st.info("This might be the first run. Models are downloading in the background.")
            
            else:  # OpenAI
                if api_key:
                    # Import OpenAI analyzer (from your original code)
                    # analyzer = AIAnalyzer(api_key, selected_model)
                    st.warning("OpenAI integration available but not recommended for private documents!")
                    can_proceed = False
                else:
                    st.warning("Please enter your OpenAI API key")
            
            if can_proceed and analyzer:
                # Process document
                processor = DocumentProcessor()
                
                with st.spinner("Processing document locally..."):
                    document_data = processor.process_document(uploaded_file)
                
                if document_data:
                    st.success("Document processed successfully!")
                    
                    # Display document info
                    with st.expander("📄 Document Information", expanded=False):
                        st.write(f"**File Type:** {document_data['type'].upper()}")
                        st.write(f"**File Name:** {document_data['filename']}")
                        
                        if document_data['type'] == 'pdf':
                            st.write(f"**Pages:** {document_data['pages']}")
                        elif document_data['type'] == 'pptx':
                            st.write(f"**Slides:** {document_data['slide_count']}")
                        elif document_data['type'] == 'docx':
                            st.write(f"**Paragraphs:** {len(document_data['paragraphs'])}")
                    
                    # AI Analysis
                    analysis = analyzer.analyze_document(document_data)
                    
                    # Create tabs for different analysis results
                    tab1, tab2, tab3, tab4, tab5 = st.tabs([
                        "📝 Summary", 
                        "📋 Executive Summary", 
                        "🎯 Key Themes", 
                        "📊 Slide Headlines",
                        "📈 Analytics"
                    ])
                    
                    with tab1:
                        st.subheader("Document Summary")
                        st.write(analysis.summary)
                        
                        # Copy button
                        if st.button("📋 Copy Summary", key="copy_summary"):
                            st.code(analysis.summary, language=None)
                    
                    with tab2:
                        st.subheader("Executive Summary")
                        st.write(analysis.executive_summary)
                        
                        if st.button("📋 Copy Executive Summary", key="copy_exec"):
                            st.code(analysis.executive_summary, language=None)
                    
                    with tab3:
                        st.subheader("Key Themes")
                        for i, theme in enumerate(analysis.key_themes, 1):
                            st.write(f"**{i}.** {theme}")
                        
                        # Export themes
                        themes_text = "\n".join([f"{i}. {theme}" for i, theme in enumerate(analysis.key_themes, 1)])
                        if st.button("📋 Copy Themes", key="copy_themes"):
                            st.code(themes_text, language=None)
                    
                    with tab4:
                        st.subheader("Suggested Slide Headlines")
                        for i, headline in enumerate(analysis.slide_headlines, 1):
                            st.write(f"**Slide {i}:** {headline}")
                        
                        headlines_text = "\n".join([f"Slide {i}: {headline}" for i, headline in enumerate(analysis.slide_headlines, 1)])
                        if st.button("📋 Copy Headlines", key="copy_headlines"):
                            st.code(headlines_text, language=None)
                    
                    with tab5:
                        st.subheader("Document Analytics")
                        
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Word Count", analysis.word_count)
                        with col_b:
                            st.metric("Themes Found", len(analysis.key_themes))
                        with col_c:
                            st.metric("Headlines Generated", len(analysis.slide_headlines))
                        
                        st.write(f"**Document Sentiment:** {analysis.sentiment}")
                        
                        # Word count visualization
                        if analysis.word_count > 0:
                            reading_time = max(1, analysis.word_count // 200)
                            st.info(f"📖 Estimated reading time: {reading_time} minute(s)")
                        
                        # Privacy confirmation
                        if ai_backend.startswith("Ollama") or ai_backend.startswith("Hugging Face"):
                            st.success("🔒 All analysis performed locally - your data remained private!")
        
        elif not uploaded_file:
            st.info("Upload a document to get started!")

    # Footer with privacy information
    st.divider()
    
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.markdown("""
        ### 🚀 Features
        - **Multi-format Support**: PDF, Word (.docx), and PowerPoint (.pptx)
        - **Private AI Analysis**: Local processing only
        - **Executive Summaries**: Business-focused summaries
        - **Slide Headlines**: Ready-to-use presentation titles
        - **Document Analytics**: Word count, sentiment, and more
        """)
    
    with col_info2:
