import re
import hashlib
import json
import gc
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import streamlit as st

class PrivacyManager:
    """Handles document sanitization and privacy features"""
    
    def __init__(self):
        self.storage_dir = Path.home() / ".document_analyzer" / "analyses"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def sanitize_document(self, text: str, sanitization_level: str = "medium") -> Dict[str, Any]:
        """
        Remove sensitive information before processing
        
        Args:
            text: Original document text
            sanitization_level: "low", "medium", "high"
        
        Returns:
            Dict with sanitized text and removed items count
        """
        original_text = text
        removed_items = {
            'emails': 0,
            'phones': 0,
            'cards': 0,
            'ssns': 0,
            'names': 0,
            'addresses': 0
        }
        
        if sanitization_level in ["medium", "high"]:
            # Remove email addresses
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails_found = len(re.findall(email_pattern, text))
            text = re.sub(email_pattern, '[EMAIL_REDACTED]', text)
            removed_items['emails'] = emails_found
            
            # Remove phone numbers (various formats)
            phone_patterns = [
                r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # US format
                r'\(\d{3}\)\s?\d{3}[-.]?\d{4}',    # (555) 123-4567
                r'\+\d{1,3}\s?\d{1,4}\s?\d{1,4}\s?\d{1,9}'  # International
            ]
            
            total_phones = 0
            for pattern in phone_patterns:
                phones_found = len(re.findall(pattern, text))
                text = re.sub(pattern, '[PHONE_REDACTED]', text)
                total_phones += phones_found
            removed_items['phones'] = total_phones
            
            # Remove credit card numbers
            card_pattern = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
            cards_found = len(re.findall(card_pattern, text))
            text = re.sub(card_pattern, '[CARD_REDACTED]', text)
            removed_items['cards'] = cards_found
        
        if sanitization_level == "high":
            # Remove SSN patterns
            ssn_pattern = r'\b\d{3}[-]?\d{2}[-]?\d{4}\b'
            ssns_found = len(re.findall(ssn_pattern, text))
            text = re.sub(ssn_pattern, '[SSN_REDACTED]', text)
            removed_items['ssns'] = ssns_found
            
            # Remove potential names (capitalized words that appear multiple times)
            words = text.split()
            word_counts = {}
            for word in words:
                if word.istitle() and len(word) > 2 and word.isalpha():
                    word_counts[word] = word_counts.get(word, 0) + 1
            
            # Replace names that appear multiple times
            names_removed = 0
            for word, count in word_counts.items():
                if count >= 2:  # Appears multiple times, likely a name
                    text = text.replace(word, '[NAME_REDACTED]')
                    names_removed += 1
            removed_items['names'] = names_removed
            
            # Remove potential addresses
            address_patterns = [
                r'\d+\s+[A-Za-z\s]+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)',
                r'\b\d{5}(-\d{4})?\b'  # ZIP codes
            ]
            
            total_addresses = 0
            for pattern in address_patterns:
                addresses_found = len(re.findall(pattern, text, re.IGNORECASE))
                text = re.sub(pattern, '[ADDRESS_REDACTED]', text, flags=re.IGNORECASE)
                total_addresses += addresses_found
            removed_items['addresses'] = total_addresses
        
        return {
            'sanitized_text': text,
            'original_length': len(original_text),
            'sanitized_length': len(text),
            'removed_items': removed_items,
            'sanitization_level': sanitization_level
        }
    
    def save_analysis_locally(self, analysis_result, filename: str, 
                            sanitization_info: Dict = None) -> str:
        """Save analysis results locally without exposing original content"""
        
        # Create anonymized filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
        save_filename = f"analysis_{timestamp}_{file_hash}.json"
        save_path = self.storage_dir / save_filename
        
        # Prepare data to save
        save_data = {
            'timestamp': datetime.now().isoformat(),
            'original_filename_hash': file_hash,  # Don't save actual filename
            'word_count': analysis_result.word_count,
            'summary': analysis_result.summary,
            'executive_summary': analysis_result.executive_summary,
            'key_themes': analysis_result.key_themes,
            'slide_headlines': analysis_result.slide_headlines,
            'sentiment': analysis_result.sentiment,
            'privacy_info': {
                'sanitization_applied': sanitization_info is not None,
                'sanitization_level': sanitization_info.get('sanitization_level') if sanitization_info else 'none',
                'items_removed': sanitization_info.get('removed_items') if sanitization_info else {}
            }
        }
        
        # Save to file
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            return str(save_path)
        
        except Exception as e:
            st.error(f"Error saving analysis: {str(e)}")
            return None
    
    def load_analysis_history(self) -> list:
        """Load previously saved analyses"""
        analyses = []
        
        for json_file in self.storage_dir.glob("analysis_*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['file_path'] = str(json_file)
                    analyses.append(data)
            except Exception as e:
                st.warning(f"Could not load {json_file.name}: {str(e)}")
        
        # Sort by timestamp (newest first)
        analyses.sort(key=lambda x: x['timestamp'], reverse=True)
        return analyses
    
    def clear_memory(self):
        """Clear memory after processing"""
        gc.collect()
        # Note: GPU memory clearing would go here if using GPU models
    
    def get_privacy_report(self, sanitization_info: Dict) -> str:
        """Generate a privacy report showing what was sanitized"""
        if not sanitization_info:
            return "No sanitization applied."
        
        removed = sanitization_info['removed_items']
        total_removed = sum(removed.values())
        
        if total_removed == 0:
            return "✅ No sensitive information detected."
        
        report = f"🔒 Privacy Report - {sanitization_info['sanitization_level'].title()} Level:\n"
        report += f"• Total items redacted: {total_removed}\n"
        
        if removed['emails'] > 0:
            report += f"• Email addresses: {removed['emails']}\n"
        if removed['phones'] > 0:
            report += f"• Phone numbers: {removed['phones']}\n"
        if removed['cards'] > 0:
            report += f"• Credit card numbers: {removed['cards']}\n"
        if removed['ssns'] > 0:
            report += f"• Social Security Numbers: {removed['ssns']}\n"
        if removed['names'] > 0:
            report += f"• Potential names: {removed['names']}\n"
        if removed['addresses'] > 0:
            report += f"• Addresses: {removed['addresses']}\n"
        
        original_len = sanitization_info['original_length']
        sanitized_len = sanitization_info['sanitized_length']
        reduction_pct = ((original_len - sanitized_len) / original_len) * 100
        
        report += f"• Text reduced by {reduction_pct:.1f}%"
        
        return report
    
    def export_privacy_settings(self) -> Dict:
        """Export current privacy settings for backup"""
        return {
            'storage_directory': str(self.storage_dir),
            'total_analyses_stored': len(list(self.storage_dir.glob("analysis_*.json"))),
            'privacy_features_enabled': [
                'Local storage only',
                'Filename hashing',
                'Content sanitization',
                'No cloud processing',
                'Memory clearing'
            ]
        }
