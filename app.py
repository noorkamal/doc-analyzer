import streamlit as st
import os
from src.document_processor import DocumentProcessor
from src.ai_analyzer import AIAnalyzer
import plotly.express as px
import pandas as pd

# Page config
st.set_page_config(
    page_title="AI Document Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("🤖 AI Document Analyzer")
    st.markdown("Upload your documents and get AI-powered insights, summaries, and analysis!")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input
        api_key = st.text_input(
            "OpenAI API Key", 
            type="password",
            help="Enter your OpenAI API key to enable AI features"
        )
        
        if api_key:
            st.success("API Key configured!")
        else:
            st.warning("Please enter your OpenAI API key to use AI features")
        
        st.divider()
        
        # Analysis options
        st.subheader("Analysis Options")
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
    
    with col2:
        st.header("📊 Document Analysis")
        
        if uploaded_file and api_key:
            # Process document
            processor = DocumentProcessor()
            
            with st.spinner("Processing document..."):
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
                analyzer = AIAnalyzer(api_key)
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
                        reading_time = max(1, analysis.word_count // 200)  # Assume 200 words per minute
                        st.info(f"📖 Estimated reading time: {reading_time} minute(s)")
        
        elif uploaded_file and not api_key:
            st.warning("Please enter your OpenAI API key in the sidebar to analyze the document.")
        
        elif not uploaded_file:
            st.info("Upload a document to get started!")

    # Footer
    st.divider()
    st.markdown("""
    ### 🚀 Features
    - **Multi-format Support**: PDF, Word (.docx), and PowerPoint (.pptx)
    - **AI-Powered Analysis**: Summaries, themes, and insights
    - **Executive Summaries**: Business-focused summaries
    - **Slide Headlines**: Ready-to-use presentation titles
    - **Document Analytics**: Word count, sentiment, and more
    """)

if __name__ == "__main__":
    main()
