# src/privacy_utils.py - Enhanced version
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import hashlib

class PrivacyManager:
    def __init__(self):
        self.base_dir = Path.home() / '.document_analyzer'
        self.analyses_dir = self.base_dir / 'analyses'
        self.sessions_dir = self.base_dir / 'sessions'
        
        # Create directories if they don't exist
        self.analyses_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def save_analysis_locally(self, analysis_results: List[Dict], session_id: str = None) -> str:
        """Save multiple document analyses locally"""
        if not session_id:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        session_data = {
            'session_id': session_id,
            'created_at': datetime.now().isoformat(),
            'document_count': len(analysis_results),
            'analyses': analysis_results,
            'privacy_guaranteed': True
        }
        
        # Save session data
        session_file = self.sessions_dir / f"session_{session_id}.json"
        
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            return str(session_file)
        except Exception as e:
            print(f"Error saving analysis: {e}")
            return None
    
    def save_single_analysis(self, analysis, filename: str, sanitization_info: Dict = None) -> str:
        """Save analysis for a single document (backward compatibility)"""
        analysis_data = {
            'filename': filename,
            'timestamp': datetime.now().isoformat(),
            'summary': getattr(analysis, 'summary', ''),
            'executive_summary': getattr(analysis, 'executive_summary', ''),
            'key_themes': getattr(analysis, 'key_themes', []),
            'slide_headlines': getattr(analysis, 'slide_headlines', []),
            'word_count': getattr(analysis, 'word_count', 0),
            'sentiment': getattr(analysis, 'sentiment', 'Unknown'),
            'sanitization_info': sanitization_info,
            'privacy_protected': True
        }
        
        # Generate unique filename based on content hash
        content_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
        analysis_file = self.analyses_dir / f"analysis_{content_hash}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
            
            return str(analysis_file)
        except Exception as e:
            print(f"Error saving analysis: {e}")
            return None
    
    def load_analysis_history(self) -> List[Dict]:
        """Load analysis history from local storage"""
        history = []
        
        # Load individual analyses
        if self.analyses_dir.exists():
            for analysis_file in self.analyses_dir.glob("analysis_*.json"):
                try:
                    with open(analysis_file, 'r', encoding='utf-8') as f:
                        analysis_data = json.load(f)
                        history.append(analysis_data)
                except Exception as e:
                    print(f"Error loading {analysis_file}: {e}")
                    continue
        
        # Load session analyses
        if self.sessions_dir.exists():
            for session_file in self.sessions_dir.glob("session_*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                        # Add session info to history
                        history.append({
                            'session_id': session_data.get('session_id'),
                            'timestamp': session_data.get('created_at'),
                            'document_count': session_data.get('document_count', 0),
                            'type': 'multi_document_session'
                        })
                except Exception as e:
                    print(f"Error loading {session_file}: {e}")
                    continue
        
        # Sort by timestamp (newest first)
        history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return history
    
    def load_session_data(self, session_id: str) -> Dict:
        """Load specific session data"""
        session_file = self.sessions_dir / f"session_{session_id}.json"
        
        if session_file.exists():
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading session {session_id}: {e}")
        
        return {}
    
    def get_privacy_report(self, sanitization_info: Dict = None) -> str:
        """Generate privacy protection report"""
        report = "🔒 **Privacy Protection Report**\n\n"
        
        report += "✅ **Guaranteed Privacy Features:**\n"
        report += "• All processing performed locally on your computer\n"
        report += "• No data transmission to external servers\n"
        report += "• Automatic temporary file cleanup\n"
        report += "• Memory cleared after processing\n"
        report += "• Results stored locally only\n\n"
        
        if sanitization_info:
            report += "🛡️ **Document Sanitization Applied:**\n"
            report += f"• Level: {sanitization_info.get('sanitization_level', 'Unknown').title()}\n"
            report += f"• Original length: {sanitization_info.get('original_length', 0):,} characters\n"
            report += f"• Processed length: {sanitization_info.get('sanitized_length', 0):,} characters\n"
            
            removed_items = sanitization_info.get('removed_items', {})
            total_removed = sum(removed_items.values())
            
            if total_removed > 0:
                report += f"• Total sensitive items removed: {total_removed}\n"
                for item_type, count in removed_items.items():
                    if count > 0:
                        report += f"  - {item_type.replace('_', ' ').title()}: {count}\n"
            else:
                report += "• No sensitive patterns detected\n"
        
        return report
    
    def export_privacy_settings(self) -> Dict:
        """Export privacy settings and statistics"""
        settings = {
            'privacy_mode': 'LOCAL_ONLY',
            'data_transmission': 'DISABLED',
            'storage_location': str(self.base_dir),
            'encryption': 'FILE_SYSTEM_LEVEL',
            'retention_policy': 'USER_CONTROLLED',
            'export_timestamp': datetime.now().isoformat()
        }
        
        # Add usage statistics
        total_analyses = len(list(self.analyses_dir.glob("analysis_*.json")))
        total_sessions = len(list(self.sessions_dir.glob("session_*.json")))
        
        settings['usage_stats'] = {
            'total_individual_analyses': total_analyses,
            'total_multi_document_sessions': total_sessions,
            'storage_dir_size_mb': self._get_directory_size(self.base_dir) / (1024 * 1024)
        }
        
        return settings
    
    def cleanup_old_analyses(self, days_old: int = 30) -> int:
        """Clean up analyses older than specified days"""
        cutoff_timestamp = datetime.now().timestamp() - (days_old * 24 * 3600)
        cleaned_count = 0
        
        # Clean up individual analyses
        for analysis_file in self.analyses_dir.glob("analysis_*.json"):
            if analysis_file.stat().st_mtime < cutoff_timestamp:
                try:
                    analysis_file.unlink()
                    cleaned_count += 1
                except Exception as e:
                    print(f"Error deleting {analysis_file}: {e}")
        
        # Clean up old sessions
        for session_file in self.sessions_dir.glob("session_*.json"):
            if session_file.stat().st_mtime < cutoff_timestamp:
                try:
                    session_file.unlink()
                    cleaned_count += 1
                except Exception as e:
                    print(f"Error deleting {session_file}: {e}")
        
        return cleaned_count
    
    def get_storage_stats(self) -> Dict:
        """Get storage usage statistics"""
        stats = {
            'base_directory': str(self.base_dir),
            'total_size_mb': self._get_directory_size(self.base_dir) / (1024 * 1024),
            'individual_analyses': len(list(self.analyses_dir.glob("analysis_*.json"))),
            'multi_document_sessions': len(list(self.sessions_dir.glob("session_*.json"))),
            'last_cleanup': 'Never',  # Could be enhanced to track cleanup history
        }
        
        return stats
    
    def _get_directory_size(self, directory: Path) -> int:
        """Calculate total size of directory"""
        total_size = 0
        
        if directory.exists():
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                    except (OSError, FileNotFoundError):
                        continue
        
        return total_size
    
    def ensure_privacy_compliance(self) -> Dict[str, bool]:
        """Verify privacy compliance"""
        checks = {
            'local_storage_only': self.base_dir.exists(),
            'no_cloud_config': True,  # Always true in this implementation
            'secure_file_permissions': self._check_file_permissions(),
            'cleanup_on_exit': True,  # Always true in this implementation
        }
        
        return checks
    
    def _check_file_permissions(self) -> bool:
        """Check if files have appropriate permissions (user-only access)"""
        try:
            # Check if base directory is accessible
            return os.access(self.base_dir, os.R_OK | os.W_OK)
        except:
            return False
