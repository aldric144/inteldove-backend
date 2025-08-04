import pytesseract
from PIL import Image
import io
import re
from typing import Dict, List, Any
import json

class OCRService:
    def __init__(self):
        pass
    
    def extract_text_from_image(self, image_data: bytes) -> str:
        """Extract text from image using OCR"""
        try:
            image = Image.open(io.BytesIO(image_data))
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            return f"OCR extraction failed: {str(e)}"
    
    def extract_entities_from_text(self, text: str) -> Dict[str, List[str]]:
        """Extract key entities from text using regex patterns"""
        entities = {
            "names": [],
            "dates": [],
            "addresses": [],
            "phone_numbers": [],
            "case_numbers": [],
            "weapons": [],
            "threats": [],
            "relationships": []
        }
        
        name_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
        entities["names"] = re.findall(name_pattern, text)
        
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{1,2}-\d{1,2}-\d{4}',
            r'[A-Za-z]+ \d{1,2}, \d{4}'
        ]
        for pattern in date_patterns:
            entities["dates"].extend(re.findall(pattern, text))
        
        phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        entities["phone_numbers"] = re.findall(phone_pattern, text)
        
        case_pattern = r'Case\s*#?\s*:?\s*([A-Z0-9-]+)'
        entities["case_numbers"] = re.findall(case_pattern, text, re.IGNORECASE)
        
        weapon_keywords = ['gun', 'firearm', 'pistol', 'rifle', 'knife', 'weapon', 'bat', 'club']
        for keyword in weapon_keywords:
            if keyword.lower() in text.lower():
                entities["weapons"].append(keyword)
        
        threat_keywords = ['kill', 'murder', 'hurt', 'harm', 'threat', 'violence', 'beat', 'shoot']
        for keyword in threat_keywords:
            if keyword.lower() in text.lower():
                entities["threats"].append(keyword)
        
        relationship_keywords = ['husband', 'wife', 'boyfriend', 'girlfriend', 'ex-husband', 'ex-wife', 'partner', 'spouse']
        for keyword in relationship_keywords:
            if keyword.lower() in text.lower():
                entities["relationships"].append(keyword)
        
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    def analyze_document_content(self, text: str) -> Dict[str, Any]:
        """Analyze document content for DV-specific information"""
        analysis = {
            "document_type": self._identify_document_type(text),
            "severity_indicators": self._find_severity_indicators(text),
            "timeline_events": self._extract_timeline(text),
            "risk_factors": self._identify_risk_factors(text),
            "legal_elements": self._find_legal_elements(text)
        }
        
        return analysis
    
    def _identify_document_type(self, text: str) -> str:
        """Identify the type of document based on content"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['police report', 'incident report', 'officer']):
            return "police_report"
        elif any(word in text_lower for word in ['restraining order', 'protection order', 'court']):
            return "court_document"
        elif any(word in text_lower for word in ['medical', 'hospital', 'injury', 'treatment']):
            return "medical_record"
        elif any(word in text_lower for word in ['news', 'article', 'reported']):
            return "news_article"
        else:
            return "unknown"
    
    def _find_severity_indicators(self, text: str) -> List[str]:
        """Find indicators of violence severity"""
        indicators = []
        text_lower = text.lower()
        
        severity_terms = {
            "high": ["murder", "kill", "death", "fatal", "weapon", "gun", "knife", "strangulation"],
            "medium": ["assault", "battery", "injury", "hospital", "bruise", "cut"],
            "low": ["threat", "verbal", "argument", "yelling"]
        }
        
        for level, terms in severity_terms.items():
            for term in terms:
                if term in text_lower:
                    indicators.append(f"{level}_severity_{term}")
        
        return indicators
    
    def _extract_timeline(self, text: str) -> List[Dict[str, str]]:
        """Extract timeline events from text"""
        timeline = []
        
        time_phrases = re.findall(r'(on|at|during|after|before)\s+([^.]+)', text, re.IGNORECASE)
        
        for phrase in time_phrases[:5]:  # Limit to first 5 events
            timeline.append({
                "time_indicator": phrase[0],
                "event": phrase[1].strip()
            })
        
        return timeline
    
    def _identify_risk_factors(self, text: str) -> List[str]:
        """Identify DV risk factors mentioned in text"""
        risk_factors = []
        text_lower = text.lower()
        
        risk_indicators = {
            "weapon_access": ["gun", "firearm", "weapon", "knife"],
            "substance_abuse": ["alcohol", "drug", "drunk", "high", "substance"],
            "mental_health": ["depression", "mental", "suicide", "therapy"],
            "control": ["control", "isolate", "monitor", "track", "follow"],
            "escalation": ["worse", "increase", "more frequent", "escalat"],
            "separation": ["leave", "divorce", "separate", "break up"],
            "children": ["child", "kid", "custody", "visitation"]
        }
        
        for factor, keywords in risk_indicators.items():
            if any(keyword in text_lower for keyword in keywords):
                risk_factors.append(factor)
        
        return risk_factors
    
    def _find_legal_elements(self, text: str) -> List[str]:
        """Find legal elements and proceedings mentioned"""
        legal_elements = []
        text_lower = text.lower()
        
        legal_terms = [
            "restraining order", "protection order", "no contact order",
            "arrest", "charge", "conviction", "probation", "parole",
            "custody", "visitation", "divorce", "separation",
            "warrant", "bail", "bond", "court", "judge", "attorney"
        ]
        
        for term in legal_terms:
            if term in text_lower:
                legal_elements.append(term)
        
        return list(set(legal_elements))
