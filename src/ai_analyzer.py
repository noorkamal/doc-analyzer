import openai
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

class AIAnalyzer:
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
    
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
        prompt = f"""
        Please provide a comprehensive summary of the following document in approximately {max_length} words.
        Focus on the main points, key findings, and important conclusions.
        
        Document:
        {text[:8000]}  # Limit input text
        
        Summary:
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_length + 100,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            st.error(f"Error generating summary: {str(e)}")
            return "Summary generation failed."
    
    def generate_executive_summary(self, text: str) -> str:
        """Generate executive summary"""
        prompt = f"""
        Create a concise executive summary of the following document. 
        Focus on:
        - Key business insights
        - Main recommendations
        - Critical findings
        - Strategic implications
        
        Keep it professional and action-oriented, maximum 150 words.
        
        Document:
        {text[:8000]}
        
        Executive Summary:
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.6
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            st.error(f"Error generating executive summary: {str(e)}")
            return "Executive summary generation failed."
    
    def extract_key_themes(self, text: str, num_themes: int = 5) -> List[str]:
        """Extract key themes from document"""
        prompt = f"""
        Analyze the following document and identify the {num_themes} most important themes or topics.
        Return only the themes as a numbered list, one theme per line.
        
        Document:
        {text[:8000]}
        
        Key Themes:
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.5
            )
            
            themes_text = response.choices[0].message.content.strip()
            # Extract themes from numbered list
            themes = []
            for line in themes_text.split('\n'):
                # Remove numbering and clean up
                theme = re.sub(r'^\d+\.?\s*', '', line.strip())
                if theme:
                    themes.append(theme)
            
            return themes[:num_themes]
        except Exception as e:
            st.error(f"Error extracting themes: {str(e)}")
            return ["Theme extraction failed."]
    
    def suggest_slide_headlines(self, text: str, num_slides: int = 6) -> List[str]:
        """Generate slide headlines based on content"""
        prompt = f"""
        Based on the following document, suggest {num_slides} compelling slide headlines for a presentation.
        Make them engaging, clear, and presentation-ready.
        Return only the headlines as a numbered list.
        
        Document:
        {text[:8000]}
        
        Slide Headlines:
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )
            
            headlines_text = response.choices[0].message.content.strip()
            headlines = []
            for line in headlines_text.split('\n'):
                headline = re.sub(r'^\d+\.?\s*', '', line.strip())
                if headline:
                    headlines.append(headline)
            
            return headlines[:num_slides]
        except Exception as e:
            st.error(f"Error generating headlines: {str(e)}")
            return ["Slide headline generation failed."]
    
    def analyze_sentiment(self, text: str) -> str:
        """Basic sentiment analysis"""
        prompt = f"""
        Analyze the overall sentiment/tone of this document. 
        Classify it as: Positive, Negative, Neutral, or Mixed.
        Provide a brief explanation.
        
        Document:
        {text[:4000]}
        
        Sentiment:
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return "Neutral - Analysis unavailable"
    
    def analyze_document(self, document_data: Dict) -> AnalysisResult:
        """Main analysis method"""
        text = document_data.get('text', '')
        word_count = len(text.split())
        
        with st.spinner("Generating AI analysis..."):
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
