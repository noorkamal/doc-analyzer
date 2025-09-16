from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
from typing import Dict, List
import streamlit as st
import re
from dataclasses import dataclass
import nltk
from collections import Counter

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('vader_lexicon', quiet=True)
except:
    pass

@dataclass
class AnalysisResult:
    summary: str
    executive_summary: str
    key_themes: List[str]
    slide_headlines: List[str]
    word_count: int
    sentiment: str

class HuggingFaceAnalyzer:
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium"):
        """
        Initialize with a local model. Options:
        - "facebook/bart-large-cnn" (good for summarization)
        - "microsoft/DialoGPT-medium" (conversational)
        - "google/flan-t5-base" (instruction following)
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.summarizer = None
        self.generator = None
        self.sentiment_analyzer = None
        self.load_models()
    
    @st.cache_resource
    def load_models(_self):
        """Load models with caching"""
        try:
            # Load summarization model
            _self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=0 if torch.cuda.is_available() else -1,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )
            
            # Load text generation model
            _self.generator = pipeline(
                "text-generation",
                model="google/flan-t5-base",
                device=0 if torch.cuda.is_available() else -1,
                max_length=512
            )
            
            # Load sentiment analysis
            _self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=0 if torch.cuda.is_available() else -1
            )
            
            st.success("✅ Local AI models loaded successfully!")
            return True
            
        except Exception as e:
            st.error(f"Error loading models: {str(e)}")
            return False
    
    def chunk_text(self, text: str, max_chunk_size: int = 1000) -> List[str]:
        """Split text into chunks suitable for local models"""
        sentences = nltk.sent_tokenize(text)
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            if current_size + len(sentence) > max_chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_size = len(sentence)
            else:
                current_chunk.append(sentence)
                current_size += len(sentence)
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def generate_summary(self, text: str, max_length: int = 300) -> str:
        """Generate document summary using BART"""
        try:
            if not self.summarizer:
                return "Summarizer not loaded"
            
            # Chunk text for processing
            chunks = self.chunk_text(text, 1000)
            summaries = []
            
            for chunk in chunks[:3]:  # Limit to first 3 chunks to avoid memory issues
                try:
                    result = self.summarizer(
                        chunk,
                        max_length=min(max_length // len(chunks), 150),
                        min_length=30,
                        do_sample=False
                    )
                    summaries.append(result[0]['summary_text'])
                except Exception as e:
                    st.warning(f"Error summarizing chunk: {str(e)}")
            
            return ' '.join(summaries) if summaries else "Could not generate summary"
            
        except Exception as e:
            st.error(f"Error generating summary: {str(e)}")
            return "Summary generation failed"
    
    def generate_executive_summary(self, text: str) -> str:
        """Generate executive summary using key sentence extraction"""
        try:
            # Use extractive summarization approach
            sentences = nltk.sent_tokenize(text)
            
            # Simple scoring based on word frequency
            words = nltk.word_tokenize(text.lower())
            word_freq = Counter(word for word in words if word.isalnum())
            
            # Score sentences
            sentence_scores = {}
            for sentence in sentences:
                words_in_sentence = nltk.word_tokenize(sentence.lower())
                score = sum(word_freq[word] for word in words_in_sentence if word in word_freq)
                sentence_scores[sentence] = score
            
            # Get top sentences
            top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            executive_summary = ' '.join([sentence for sentence, score in top_sentences])
            
            return executive_summary[:500] + "..." if len(executive_summary) > 500 else executive_summary
            
        except Exception as e:
            st.error(f"Error generating executive summary: {str(e)}")
            return "Executive summary generation failed"
    
    def extract_key_themes(self, text: str, num_themes: int = 5) -> List[str]:
        """Extract key themes using keyword extraction"""
        try:
            # Simple keyword extraction
            words = nltk.word_tokenize(text.lower())
            
            # Remove stopwords
            from nltk.corpus import stopwords
            stop_words = set(stopwords.words('english'))
            words = [word for word in words if word.isalnum() and word not in stop_words and len(word) > 3]
            
            # Get most frequent words as themes
            word_freq = Counter(words)
            themes = [word.title() for word, freq in word_freq.most_common(num_themes)]
            
            # Convert single words to more descriptive themes
            theme_phrases = []
            for theme in themes:
                theme_phrases.append(f"{theme}-related topics and discussions")
            
            return theme_phrases
            
        except Exception as e:
            st.error(f"Error extracting themes: {str(e)}")
            return ["Theme extraction failed"]
    
    def suggest_slide_headlines(self, text: str, num_slides: int = 6) -> List[str]:
        """Generate slide headlines using sentence extraction"""
        try:
            sentences = nltk.sent_tokenize(text)
            
            # Find sentences that could be good headlines
            headline_candidates = []
            for sentence in sentences:
                # Look for sentences with key indicators
                if any(indicator in sentence.lower() for indicator in 
                      ['key', 'important', 'main', 'significant', 'critical', 'overview', 'introduction']):
                    headline_candidates.append(sentence)
            
            # If not enough candidates, use first sentences of paragraphs
            if len(headline_candidates) < num_slides:
                paragraphs = text.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        first_sentence = nltk.sent_tokenize(para.strip())[0]
                        if first_sentence not in headline_candidates:
                            headline_candidates.append(first_sentence)
            
            # Clean and format headlines
            headlines = []
            for candidate in headline_candidates[:num_slides]:
                # Make it more headline-like
                headline = candidate.strip()
                if headline.endswith('.'):
                    headline = headline[:-1]
                if len(headline) > 80:
                    headline = headline[:77] + "..."
                headlines.append(headline)
            
            # Fill remaining slots if needed
            while len(headlines) < num_slides:
                headlines.append(f"Key Point {len(headlines) + 1}")
            
            return headlines[:num_slides]
            
        except Exception as e:
            st.error(f"Error generating headlines: {str(e)}")
            return ["Slide headline generation failed"]
    
    def analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment using local model"""
        try:
            if not self.sentiment_analyzer:
                return "Neutral - Analyzer not loaded"
            
            # Analyze first 500 characters for efficiency
            text_sample = text[:500]
            result = self.sentiment_analyzer(text_sample)
            
            label = result[0]['label']
            score = result[0]['score']
            
            # Map labels (different models use different labels)
            sentiment_map = {
                'POSITIVE': 'Positive',
                'NEGATIVE': 'Negative', 
                'NEUTRAL': 'Neutral',
                'LABEL_0': 'Negative',
                'LABEL_1': 'Neutral',
                'LABEL_2': 'Positive'
            }
            
            sentiment = sentiment_map.get(label, 'Neutral')
            return f"{sentiment} (confidence: {score:.2f})"
            
        except Exception as e:
            st.error(f"Error analyzing sentiment: {str(e)}")
            return "Neutral - Analysis failed"
    
    def analyze_document(self, document_data: Dict) -> AnalysisResult:
        """Main analysis method"""
        text = document_data.get('text', '')
        word_count = len(text.split())
        
        with st.spinner("Generating AI analysis using local models..."):
            # Generate all analyses
            summary = self.generate_summary(text)
            executive_summary = self.generate_executive_summary(text)
            key_themes = self.extract_key_themes(text)
            slide_headlines = self.suggest_slide_headlines(text)
            sentiment = self.analyze_sentiment(text)
        
        return AnalysisResult(
            summary=summary,
            executive_summary=executive_summary,
            key_themes=key_themes,
            slide_headlines=slide_headlines,
            word_count=word_count,
            sentiment=sentiment
        )
