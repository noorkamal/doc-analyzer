import requests
import json
from typing import Dict, List
import streamlit as st
import re
from dataclasses import dataclass

@dataclass
class AnalysisResult:
    summary: str
    executive_summary: str
    key_themes: List[str]
    slide_headlines: List[str]
    word_count: int
    sentiment: str

class OllamaAnalyzer:
    def __init__(self, model: str = "llama3.1", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
    
    def test_connection(self) -> bool:
        """Test if Ollama is running and model is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json()
                available_models = [model['name'] for model in models.get('models', [])]
                return self.model in available_models
            return False
        except Exception as e:
            st.error(f"Cannot connect to Ollama: {str(e)}")
            return False
    
    def generate_response(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate response using Ollama"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": max_tokens
                }
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=120  # Longer timeout for local processing
            )
            
            if response.status_code == 200:
                return response.json()['response'].strip()
            else:
                st.error(f"Ollama API error: {response.status_code}")
                return "Error generating response"
                
        except Exception as e:
            st.error(f"Error calling Ollama: {str(e)}")
            return "Error generating response"
    
    def chunk_text(self, text: str, max_chunk_size: int = 4000) -> List[str]:
        """Split text into manageable chunks"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            if current_size + len(word) > max_chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
                current_size += len(word) + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def generate_summary(self, text: str, max_length: int = 300) -> str:
        """Generate document summary"""
        # Truncate text to fit context window
        text_chunk = text[:6000]  # Conservative limit for local models
        
        prompt = f"""Please provide a comprehensive summary of the following document in approximately {max_length} words. Focus on the main points, key findings, and important conclusions.

Document:
{text_chunk}

Summary:"""
        
        return self.generate_response(prompt, max_tokens=max_length + 50)
    
    def generate_executive_summary(self, text: str) -> str:
        """Generate executive summary"""
        text_chunk = text[:6000]
        
        prompt = f"""Create a concise executive summary of the following document. Focus on:
- Key business insights
- Main recommendations  
- Critical findings
- Strategic implications

Keep it professional and action-oriented, maximum 150 words.

Document:
{text_chunk}

Executive Summary:"""
        
        return self.generate_response(prompt, max_tokens=200)
    
    def extract_key_themes(self, text: str, num_themes: int = 5) -> List[str]:
        """Extract key themes from document"""
        text_chunk = text[:6000]
        
        prompt = f"""Analyze the following document and identify the {num_themes} most important themes or topics. Return only the themes as a numbered list, one theme per line.

Document:
{text_chunk}

Key Themes:
1."""
        
        response = self.generate_response(prompt, max_tokens=300)
        
        # Extract themes from response
        themes = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith(tuple('123456789')) or line.startswith('-') or line.startswith('•')):
                # Clean up the theme text
                theme = re.sub(r'^\d+\.?\s*[-•]?\s*', '', line)
                if theme and len(theme) > 5:  # Filter out very short themes
                    themes.append(theme)
        
        return themes[:num_themes] if themes else ["Could not extract themes"]
    
    def suggest_slide_headlines(self, text: str, num_slides: int = 6) -> List[str]:
        """Generate slide headlines based on content"""
        text_chunk = text[:6000]
        
        prompt = f"""Based on the following document, suggest {num_slides} compelling slide headlines for a presentation. Make them engaging, clear, and presentation-ready. Return only the headlines as a numbered list.

Document:
{text_chunk}

Slide Headlines:
1."""
        
        response = self.generate_response(prompt, max_tokens=300)
        
        # Extract headlines from response
        headlines = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith(tuple('123456789')) or line.startswith('-') or line.startswith('•')):
                headline = re.sub(r'^\d+\.?\s*[-•]?\s*', '', line)
                if headline and len(headline) > 5:
                    headlines.append(headline)
        
        return headlines[:num_slides] if headlines else ["Could not generate headlines"]
    
    def analyze_sentiment(self, text: str) -> str:
        """Basic sentiment analysis"""
        text_chunk = text[:4000]
        
        prompt = f"""Analyze the overall sentiment/tone of this document. Classify it as: Positive, Negative, Neutral, or Mixed. Provide a brief explanation in 1-2 sentences.

Document:
{text_chunk}

Sentiment Analysis:"""
        
        return self.generate_response(prompt, max_tokens=100)
    
    def analyze_document(self, document_data: Dict) -> AnalysisResult:
        """Main analysis method"""
        text = document_data.get('text', '')
        word_count = len(text.split())
        
        if not self.test_connection():
            st.error(f"Cannot connect to Ollama or model '{self.model}' not found. Please ensure Ollama is running and the model is installed.")
            return AnalysisResult(
                summary="Connection to local AI failed",
                executive_summary="Connection to local AI failed", 
                key_themes=["Connection failed"],
                slide_headlines=["Connection failed"],
                word_count=word_count,
                sentiment="Unknown"
            )
        
        with st.spinner(f"Generating AI analysis using {self.model}..."):
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
