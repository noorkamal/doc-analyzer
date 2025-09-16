import streamlit as st
import os
import requests
from src.document_processor import DocumentProcessor
from src.ollama_analyzer import OllamaAnalyzer
from src.privacy_utils import PrivacyManager
import plotly.express as px
import pandas as pd
from datetime import datetime

# Page config
st.set_page_config(
    page_title="🔒 Private AI Document Analyzer",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

def check_ollama_status():
    """Check if Ollama is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models_data = response.json()
            available_models = [model['name'] for model in models_data.get('models', [])]
            return True, available_models
        return False, []
    except:
        return False, []

def main():
    # Initialize privacy manager
    privacy_manager = PrivacyManager()
    
    st.title("🔒 Private AI Document Analyzer")
    st.markdown("**Powered by Ollama** - Your documents never leave your computer!")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("🛡️ Privacy & Configuration")
        
        # Ollama Status Check
        ollama_running, available_models = check_ollama_status()
        
        if ollama_running:
            st.success("✅ Ollama is running!")
            st.info(f"📊 {len(available_models)} models available")
            
            if available_models:
                selected_model = st.selectbox(
                    "Select AI Model", 
                    available_models,
                    help="Choose which local AI model to use for analysis"
                )
            else:
                st.warning("No models found. Please download a model first.")
                selected_model = "llama3.1"  # Default fallback
        else:
            st.error("❌ Ollama not detected")
            st.markdown("""
            **Quick Setup:**
            1. Install: `curl -fsSL https://ollama.ai/install.sh | sh`
            2. Download model: `ollama pull llama3.1`
            3. Start: `ollama serve`
            4. Refresh this page
            """)
            selected_model = "llama3.1"
        
        st.divider()
        
        # Privacy Settings
        st.subheader("🔐 Privacy Controls")
        
        # Document Sanitization
        st.write("**Document Sanitization:**")
        sanitization_level = st.selectbox(
            "Sanitization Level",
            ["none", "low", "medium", "high"],
            index=2,  # Default to "medium"
            help="""
            • None: No sanitization
            • Low: Remove obvious sensitive data
            • Medium: Remove emails, phones, cards
            • High: Remove names, addresses, SSNs
            """
        )
        
        # Show what each level does
        sanitization_info = {
            "none": "No privacy filtering applied",
            "low": "Basic filtering: obvious patterns only",
            "medium": "Standard filtering: emails, phones, credit cards",
            "high": "Aggressive filtering: names, addresses, SSNs, emails, phones, cards"
        }
        st.caption(sanitization_info[sanitization_level])
        
        # Local Storage Options
        st.write("**Local Storage:**")
        save_analysis = st.checkbox("Save analysis locally", value=True, 
                                  help="Save results to ~/.document_analyzer/analyses/")
        
        if save_analysis:
            # Show storage info
            analyses_count = len(privacy_manager.load_analysis_history())
            st.caption(f"💾 {analyses_count} previous analyses stored")
        
        st.divider()
        
        # Analysis Options
        st.subheader("⚙️ Analysis Settings")
        max_themes = st.slider("Key themes to extract", 3, 10, 5)
        max_headlines = st.slider("Slide headlines to generate", 3, 10, 6)
        summary_length = st.slider("Summary length (words)", 100, 500, 300)
        
        st.divider()
        
        # Privacy Status
        st.subheader("🔒 Privacy Status")
        privacy_features = [
            "✅ Local AI processing only",
            "✅ No cloud data transmission", 
            "✅ Automatic memory clearing",
            "✅ Anonymous local storage",
            "✅ Document sanitization"
        ]
        
        for feature in privacy_features:
            st.write(feature)
    
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
            st.success(f"✅ File: {uploaded_file.name}")
            file_size = len(uploaded_file.getvalue())
            st.info(f"📊 Size: {file_size / 1024:.1f} KB")
            
            # Privacy assurance
            st.success("🔒 **Privacy Guaranteed**\nThis file will be processed locally and never sent to any cloud service!")
            
            # Show what will be sanitized
            if sanitization_level != "none":
                st.info(f"🛡️ **Protection Level**: {sanitization_level.title()}\n{sanitization_info[sanitization_level]}")
    
    with col2:
        st.header("📊 Document Analysis")
        
        if uploaded_file and ollama_running:
            # Process document with privacy features
            processor = DocumentProcessor(enable_privacy=True)
            
            with st.spinner("🔒 Processing document locally with privacy protection..."):
                document_data = processor.process_document(uploaded_file, sanitization_level)
            
            if document_data:
                st.success("✅ Document processed successfully!")
                
                # Show document info
                with st.expander("📄 Document Information", expanded=False):
                    st.write(f"**File Type:** {document_data['type'].upper()}")
                    st.write(f"**Original Size:** {document_data['file_size']} bytes")
                    
                    if document_data['type'] == 'pdf':
                        st.write(f"**Pages:** {document_data['pages']}")
                    elif document_data['type'] == 'pptx':
                        st.write(f"**Slides:** {document_data['slide_count']}")
                    elif document_data['type'] == 'docx':
                        st.write(f"**Paragraphs:** {len(document_data['paragraphs'])}")
                    
                    # Show sanitization info if applied
                    if 'sanitization_info' in document_data:
                        sanitization_data = document_data['sanitization_info']
                        st.write("**Privacy Protection Applied:**")
                        st.write(f"- Sanitization Level: {sanitization_data['sanitization_level'].title()}")
                        st.write(f"- Original Length: {sanitization_data['original_length']:,} chars")
                        st.write(f"- Processed Length: {sanitization_data['sanitized_length']:,} chars")
                        
                        removed_items = sanitization_data['removed_items']
                        if sum(removed_items.values()) > 0:
                            st.write("- **Items Removed:**")
                            for item_type, count in removed_items.items():
                                if count > 0:
                                    st.write(f"  - {item_type.title()}: {count}")
                
                # AI Analysis
                if selected_model in [m for m in available_models] if available_models else [selected_model]:
                    analyzer = OllamaAnalyzer(model=selected_model)
                    
                    # Perform analysis
                    analysis = analyzer.analyze_document(document_data)
                    
                    # Save analysis locally if enabled
                    if save_analysis:
                        save_path = privacy_manager.save_analysis_locally(
                            analysis, 
                            uploaded_file.name,
                            document_data.get('sanitization_info')
                        )
                        if save_path:
                            st.success(f"💾 Analysis saved locally (private storage)")
                    
                    # Create tabs for results
                    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                        "📝 Summary", 
                        "📋 Executive Summary", 
                        "🎯 Key Themes", 
                        "📊 Slide Headlines",
                        "📈 Analytics",
                        "🔒 Privacy Report"
                    ])
                    
                    with tab1:
                        st.subheader("Document Summary")
                        st.write(analysis.summary)
                        
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
                            st.metric("Word Count", f"{analysis.word_count:,}")
                        with col_b:
                            st.metric("Themes Found", len(analysis.key_themes))
                        with col_c:
                            st.metric("Headlines Generated", len(analysis.slide_headlines))
                        
                        st.write(f"**Document Sentiment:** {analysis.sentiment}")
                        
                        # Reading time calculation
                        if analysis.word_count > 0:
                            reading_time = max(1, analysis.word_count // 200)
                            st.info(f"📖 Estimated reading time: {reading_time} minute(s)")
                        
                        # Model info
                        st.write(f"**AI Model Used:** {selected_model}")
                        st.write(f"**Processing Time:** {datetime.now().strftime('%H:%M:%S')}")
                    
                    with tab6:
                        st.subheader("🔒 Privacy & Security Report")
                        
                        # Privacy confirmation
                        st.success("✅ **Complete Privacy Maintained**")
                        
                        privacy_report_items = [
                            "🏠 All processing performed locally on your computer",
                            "🚫 No data transmitted to external servers", 
                            "🗑️ Temporary files automatically deleted",
                            "🧹 Memory cleared after processing",
                            "📁 Results stored locally only (if enabled)"
                        ]
                        
                        for item in privacy_report_items:
                            st.write(item)
                        
                        # Show sanitization report if applied
                        if 'sanitization_info' in document_data:
                            st.divider()
                            st.subheader("🛡️ Document Sanitization Report")
                            privacy_report = privacy_manager.get_privacy_report(
                                document_data['sanitization_info']
                            )
                            st.info(privacy_report)
                        
                        # Privacy settings export
                        if st.button("📤 Export Privacy Settings"):
                            privacy_settings = privacy_manager.export_privacy_settings()
                            st.json(privacy_settings)
                else:
                    st.error(f"Selected model '{selected_model}' is not available. Please download it first.")
        
        elif uploaded_file and not ollama_running:
            st.error("🚫 Please install and start Ollama to analyze documents privately!")
            st.markdown("""
            **Setup Instructions:**
            1. Install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
            2. Download model: `ollama pull llama3.1`
            3. Start Ollama: `ollama serve`
            """)
        
        elif not uploaded_file:
            st.info("👆 Upload a document to get started with private AI analysis!")

    # Analysis History (if enabled)
    if save_analysis:
        st.divider()
        with st.expander("📚 Analysis History", expanded=False):
            history = privacy_manager.load_analysis_history()
            
            if history:
                st.write(f"**{len(history)} previous analyses found:**")
                
                for i, analysis_data in enumerate(history[:5]):  # Show last 5
                    timestamp = analysis_data.get('timestamp', 'Unknown')
                    word_count = analysis_data.get('word_count', 0)
                    themes_count = len(analysis_data.get('key_themes', []))
                    
                    st.write(f"**{i+1}.** {timestamp} - {word_count:,} words, {themes_count} themes")
                
                if len(history) > 5:
                    st.caption(f"... and {len(history) - 5} more")
            else:
                st.info("No previous analyses found.")

    # Footer
