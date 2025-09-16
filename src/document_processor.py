import PyPDF2
from docx import Document
from pptx import Presentation
import streamlit as st
from typing import Dict, List, Tuple
import os
import tempfile

class DocumentProcessor:
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.pptx']
    
    def extract_text_from_pdf(self, file_path: str) -> Dict:
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page_num, page in enumerate(pdf_reader.pages):
                    text += f"\n--- Page {page_num + 1} ---\n"
                    text += page.extract_text()
                
                return {
                    'text': text,
                    'pages': len(pdf_reader.pages),
                    'type': 'pdf'
                }
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
            return None
    
    def extract_text_from_docx(self, file_path: str) -> Dict:
        """Extract text from Word document"""
        try:
            doc = Document(file_path)
            text = ""
            paragraphs = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    paragraphs.append(paragraph.text)
                    text += paragraph.text + "\n"
            
            return {
                'text': text,
                'paragraphs': paragraphs,
                'type': 'docx'
            }
        except Exception as e:
            st.error(f"Error processing Word document: {str(e)}")
            return None
    
    def extract_text_from_pptx(self, file_path: str) -> Dict:
        """Extract text from PowerPoint presentation"""
        try:
            prs = Presentation(file_path)
            slides_content = []
            all_text = ""
            
            for slide_num, slide in enumerate(prs.slides):
                slide_text = f"\n--- Slide {slide_num + 1} ---\n"
                slide_content = {"slide_number": slide_num + 1, "text": ""}
                
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:
                        slide_text += shape.text + "\n"
                        slide_content["text"] += shape.text + "\n"
                
                slides_content.append(slide_content)
                all_text += slide_text
            
            return {
                'text': all_text,
                'slides': slides_content,
                'slide_count': len(prs.slides),
                'type': 'pptx'
            }
        except Exception as e:
            st.error(f"Error processing PowerPoint: {str(e)}")
            return None
    
    def process_document(self, uploaded_file) -> Dict:
        """Main method to process uploaded document"""
        if uploaded_file is None:
            return None
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            temp_path = tmp_file.name
        
        try:
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            
            if file_extension == '.pdf':
                result = self.extract_text_from_pdf(temp_path)
            elif file_extension == '.docx':
                result = self.extract_text_from_docx(temp_path)
            elif file_extension == '.pptx':
                result = self.extract_text_from_pptx(temp_path)
            else:
                st.error(f"Unsupported file format: {file_extension}")
                return None
            
            if result:
                result['filename'] = uploaded_file.name
                result['file_size'] = len(uploaded_file.getvalue())
            
            return result
            
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
