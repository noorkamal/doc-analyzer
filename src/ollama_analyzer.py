# src/ollama_analyzer.py - Enhanced version
import requests
import json
from dataclasses import dataclass
from typing import List, Dict, Any
import re

@dataclass
class AnalysisResult:
    """Enhanced analysis result with additional metrics"""
    summary: str
    executive_summary: str
    key_themes: List[str]
    slide_headlines: List[str]
    word_count: int
    sentiment: str
    confidence_score: float = 0.0
    processing_time: float = 0.0

class OllamaAnalyzer:
    def __init__(self, model: str = "llama3.1", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.session = requests.Session()
    
    def _make_request(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.3) -> str:
        """Make request to Ollama API with optimized parameters"""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "num_predict": max_tokens,
                "num_ctx": 4096,
                "num_batch": 8,
                "num_threads": -1,
            }
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '').strip()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama API request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse Ollama response: {str(e)}")
    
    def generate_response(self, prompt: str, max_tokens: int = 1024) -> str:
        """Generate a response for chatbot functionality"""
        return self._make_request(prompt, max_tokens)
    
    def analyze_document(self, document_data: Dict[str, Any]) -> AnalysisResult:
        """Enhanced document analysis with better prompts and error handling"""
        content = document_data.get('content', '')
        
        if not content:
            raise ValueError("Document content is empty")
        
        # Calculate word count
        word_count = len(content.split())
        
        # Truncate content if too long (keep first and last parts)
        max_content_length = 3000
        if len(content) > max_content_length:
            content = content[:max_content_length//2] + "\n\n[...content truncated...]\n\n" + content[-max_content_length//2:]
        
        try:
            # Generate summary
            summary = self._generate_summary(content)
            
            # Generate executive summary
            executive_summary = self._generate_executive_summary(content)
            
            # Extract key themes
            key_themes = self._extract_key_themes(content)
            
            # Generate slide headlines
            slide_headlines = self._generate_slide_headlines(content, key_themes)
            
            # Analyze sentiment
            sentiment = self._analyze_sentiment(content)
            
            return AnalysisResult(
                summary=summary,
                executive_summary=executive_summary,
                key_themes=key_themes,
                slide_headlines=slide_headlines,
                word_count=word_count,
                sentiment=sentiment,
                confidence_score=0.85  # Default confidence
            )
            
        except Exception as e:
            # Return partial results if something fails
            return AnalysisResult(
                summary=f"Error generating summary: {str(e)}",
                executive_summary="Analysis partially failed",
                key_themes=["Error in theme extraction"],
                slide_headlines=["Error in headline generation"],
                word_count=word_count,
                sentiment="Unknown"
            )
    
    def _generate_summary(self, content: str) -> str:
        """Generate document summary"""
        prompt = f"""Please provide a comprehensive summary of the following document content. Focus on the main points, key findings, and important details. Keep it informative but concise.

Document content:
{content}

Summary:"""
        
        return self._make_request(prompt, max_tokens=500)
    
    def _generate_executive_summary(self, content: str) -> str:
        """Generate executive summary"""
        prompt = f"""Create an executive summary of the following document. This should be a high-level overview suitable for executives and decision-makers. Focus on key insights, recommendations, and strategic implications.

Document content:
{content}

Executive Summary:"""
        
        return self._make_request(prompt, max_tokens=300)
    
    def _extract_key_themes(self, content: str) -> List[str]:
        """Extract key themes from document"""
        prompt = f"""Analyze the following document and identify the key themes, topics, and concepts discussed. Return exactly 8 distinct themes as a numbered list. Each theme should be specific and meaningful.

Document content:
{content}

Key themes (list 8 themes):
1."""
        
        response = self._make_request(prompt, max_tokens=400)
        
        # Parse the numbered list
        themes = []
        lines = response.split('\n')
        
        for line in lines:
            # Look for numbered items (1. 2. etc.)
            match = re.match(r'^\d+\.\s*(.+)', line.strip())
            if match:
                theme = match.group(1).strip()
                if theme and len(theme) > 5:  # Filter out very short themes
                    themes.append(theme)
        
        # If parsing failed, try to extract themes differently
        if len(themes) < 3:
            # Split by common delimiters and clean up
            potential_themes = re.split(r'[;\n]', response)
            themes = []
            for theme in potential_themes:
                theme = re.sub(r'^\d+\.\s*', '', theme.strip())  # Remove numbering
                if theme and len(theme) > 5:
                    themes.append(theme)
        
        return themes[:8]  # Return max 8 themes
    
    def _generate_slide_headlines(self, content: str, themes: List[str]) -> List[str]:
        """Generate presentation slide headlines"""
        themes_str = '\n'.join([f"- {theme}" for theme in themes[:5]])
        
        prompt = f"""Based on the following document content and key themes, create 8 compelling presentation slide headlines. Each headline should be concise, engaging, and capture a key aspect of the content.

Document content:
{content}

Key themes identified:
{themes_str}

Generate 8 slide headlines:
1."""
        
        response = self._make_request(prompt, max_tokens=400)
        
        # Parse the numbered list
        headlines = []
        lines = response.split('\n')
        
        for line in lines:
            match = re.match(r'^\d+\.\s*(.+)', line.strip())
            if match:
                headline = match.group(1).strip()
                if headline:
                    headlines.append(headline)
        
        return headlines[:8]  # Return max 8 headlines
    
    def _analyze_sentiment(self, content: str) -> str:
        """Analyze document sentiment"""
        # For longer content, sample from different parts
        if len(content) > 1000:
            sample_content = content[:300] + content[len(content)//2:len(content)//2+300] + content[-300:]
        else:
            sample_content = content
        
        prompt = f"""Analyze the overall sentiment and tone of the following document content. Classify it as one of: Positive, Negative, Neutral, Mixed, or Professional.

Content to analyze:
{sample_content}

Sentiment classification:"""
        
        response = self._make_request(prompt, max_tokens=50, temperature=0.1)
        
        # Clean up response and return appropriate sentiment
        sentiment_keywords = {
            'positive': 'Positive',
            'negative': 'Negative', 
            'neutral': 'Neutral',
            'mixed': 'Mixed',
            'professional': 'Professional'
        }
        
        response_lower = response.lower()
        for keyword, sentiment in sentiment_keywords.items():
            if keyword in response_lower:
                return sentiment
        
        return 'Neutral'  # Default fallback
    
    def search_document_content(self, documents: List[Dict], query: str) -> List[Dict]:
        """Search for content across multiple documents"""
        results = []
        query_lower = query.lower()
        
        for doc in documents:
            content = doc.get('content', '')
            if not content:
                continue
            
            # Split into sentences
            sentences = re.split(r'[.!?]+', content)
            
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 20:  # Skip very short sentences
                    continue
                
                # Calculate relevance score
                sentence_lower = sentence.lower()
                query_words = query_lower.split()
                relevance = sum(1 for word in query_words if word in sentence_lower)
                
                if relevance > 0:
                    results.append({
                        'document': doc.get('filename', 'Unknown'),
                        'content': sentence,
                        'relevance_score': relevance / len(query_words),
                        'context': self._get_sentence_context(content, sentence)
                    })
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results[:10]
    
    def _get_sentence_context(self, full_content: str, target_sentence: str) -> str:
        """Get context around a sentence"""
        try:
            # Find the sentence in the full content
            sentence_start = full_content.find(target_sentence)
            if sentence_start == -1:
                return target_sentence
            
            # Get some context before and after
            context_start = max(0, sentence_start - 200)
            context_end = min(len(full_content), sentence_start + len(target_sentence) + 200)
            
            context = full_content[context_start:context_end]
            
            # Clean up context
            if context_start > 0:
                context = "..." + context
            if context_end < len(full_content):
                context = context + "..."
            
            return context
        except:
            return target_sentence
    
    def generate_comparative_analysis(self, documents: List[Dict]) -> str:
        """Generate analysis comparing multiple documents"""
        if len(documents) < 2:
            return "Need at least 2 documents for comparative analysis."
        
        # Create summary of each document
        doc_summaries = []
        for i, doc in enumerate(documents):
            content_preview = doc.get('content', '')[:500] + "..."
            doc_summaries.append(f"Document {i+1} ({doc.get('filename', 'Unknown')}):\n{content_preview}")
        
        summaries_text = "\n\n".join(doc_summaries)
        
        prompt = f"""Compare and analyze the following documents. Identify common themes, differences, and key insights across all documents. Provide a comprehensive comparative analysis.

Documents to compare:
{summaries_text}

Comparative Analysis:"""
        
        return self._make_request(prompt, max_tokens=800)
    
    def answer_question_about_documents(self, documents: List[Dict], question: str, conversation_history: List[Dict] = None) -> str:
        """Answer questions about the documents with conversation context"""
        
        # Create document context
        doc_context = "Available documents:\n"
        for i, doc in enumerate(documents):
            doc_context += f"\nDocument {i+1}: {doc.get('filename', 'Unknown')}\n"
            doc_context += f"Content preview: {doc.get('content', '')[:800]}...\n"
            doc_context += "---\n"
        
        # Add conversation history if available
        context_prompt = ""
        if conversation_history:
            recent_history = conversation_history[-4:]  # Last 4 exchanges
            context_prompt = "\nRecent conversation:\n"
            for msg in recent_history:
                context_prompt += f"{msg['role']}: {msg['content']}\n"
        
        prompt = f"""You are an AI assistant helping analyze uploaded documents. Use the document content to answer the user's question accurately and helpfully.

{doc_context}
{context_prompt}

User question: {question}

Please provide a helpful and accurate answer based on the documents. If you reference specific information, mention which document it came from."""
        
        return self._make_request(prompt, max_tokens=600)
