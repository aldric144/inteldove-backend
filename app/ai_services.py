import openai
import json
from typing import Dict, List, Any
from app.models import Case, Suspect, Victim, RiskLevel
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class AIAnalysisService:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key="your-openai-api-key")
        
    async def analyze_suspect_profile(self, case: Case, suspect: Suspect) -> Dict[str, Any]:
        """Generate psychological profile for suspect using FBI BAU methods"""
        
        prompt = f"""
        As an expert criminal profiler using FBI Behavioral Analysis Unit methods, analyze this domestic violence suspect:
        
        Case Details:
        - Case Type: {case.case_type}
        - Location: {case.location_city}, {case.location_state}
        - Description: {case.description}
        
        Suspect Information:
        - Name: {suspect.name}
        - Age: {suspect.age}
        - Gender: {suspect.gender}
        - Relationship to victim: {suspect.relationship_to_victim}
        - Criminal history: {suspect.criminal_history}
        - Mental health history: {suspect.mental_health_history}
        - Substance abuse: {suspect.substance_abuse}
        - Firearm access: {suspect.firearm_access}
        - Employment status: {suspect.employment_status}
        
        Provide analysis based on:
        1. Coercive Control Theory (Dr. Evan Stark)
        2. Power & Control Wheel patterns
        3. Escalation indicators
        4. Risk factors for lethality
        
        Return JSON with:
        - psychological_profile: detailed analysis
        - behavioral_patterns: identified patterns
        - risk_factors: specific risk factors
        - warning_signs: red flags identified
        - lethality_risk: scale 1-10
        - recommendations: intervention strategies
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            analysis = json.loads(response.choices[0].message.content)
            analysis["confidence_score"] = 0.85  # Mock confidence score
            return analysis
            
        except Exception as e:
            return self._generate_fallback_suspect_analysis(suspect)
    
    async def analyze_victim_vulnerability(self, case: Case, victim: Victim) -> Dict[str, Any]:
        """Analyze victim vulnerability using Dr. Jacquelyn Campbell's research"""
        
        prompt = f"""
        As an expert in domestic violence victim analysis using Dr. Jacquelyn Campbell's Danger Assessment methodology, analyze:
        
        Victim Information:
        - Name: {victim.name}
        - Age: {victim.age}
        - Relationship to suspect: {victim.relationship_to_suspect}
        - Children involved: {victim.children_involved}
        - Financial dependence: {victim.financial_dependence}
        - Isolation level: {victim.isolation_level}
        - Prior DV reports: {victim.prior_dv_reports}
        - Protection order history: {victim.protection_order_history}
        
        Analyze based on:
        1. Battered Woman Syndrome (Dr. Lenore Walker)
        2. Trauma bonding patterns
        3. Separation timeline risks
        4. Support system availability
        
        Return JSON with:
        - vulnerability_profile: detailed analysis
        - trauma_indicators: signs of trauma bonding
        - risk_factors: vulnerability factors
        - protective_factors: strengths and resources
        - safety_recommendations: specific safety planning steps
        - lethality_risk: scale 1-10
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            analysis = json.loads(response.choices[0].message.content)
            analysis["confidence_score"] = 0.82
            return analysis
            
        except Exception as e:
            return self._generate_fallback_victim_analysis(victim)
    
    def calculate_lethality_score(self, assessment_data: Dict[str, Any]) -> tuple[float, RiskLevel]:
        """Calculate lethality score based on Campbell Danger Assessment"""
        
        risk_factors = {
            "increased_frequency": 2.0,
            "increased_severity": 2.5,
            "threats_to_kill": 4.0,
            "weapon_threats": 3.5,
            "firearm_access": 4.5,
            "forced_sex": 2.0,
            "drug_alcohol_abuse": 1.5,
            "controlling_behavior": 2.0,
            "jealousy": 1.5,
            "separation_threats": 3.0,
            "unemployment": 1.0,
            "stalking": 3.0,
            "children_threatened": 2.5,
            "suicide_threats": 2.0,
            "prior_police_calls": 1.5
        }
        
        total_score = 0.0
        max_possible = sum(risk_factors.values())
        
        for factor, weight in risk_factors.items():
            if assessment_data.get(factor, False):
                total_score += weight
        
        normalized_score = (total_score / max_possible) * 100
        
        if normalized_score >= 75:
            risk_level = RiskLevel.EXTREME
        elif normalized_score >= 50:
            risk_level = RiskLevel.HIGH
        elif normalized_score >= 25:
            risk_level = RiskLevel.MODERATE
        else:
            risk_level = RiskLevel.LOW
            
        return normalized_score, risk_level
    
    def find_pattern_matches(self, current_case: Case, all_cases: List[Case]) -> List[Dict[str, Any]]:
        """Find similar cases using AI pattern matching"""
        
        if not all_cases:
            return []
        
        current_features = self._extract_case_features(current_case)
        
        matches = []
        for case in all_cases:
            if case.id == current_case.id:
                continue
                
            case_features = self._extract_case_features(case)
            similarity = self._calculate_similarity(current_features, case_features)
            
            if similarity > 0.7:  # 70% similarity threshold
                matches.append({
                    "case_id": case.id,
                    "case_number": case.case_number,
                    "similarity_score": similarity,
                    "matching_factors": self._identify_matching_factors(current_features, case_features)
                })
        
        return sorted(matches, key=lambda x: x["similarity_score"], reverse=True)[:10]
    
    def _extract_case_features(self, case: Case) -> Dict[str, Any]:
        """Extract features from case for pattern matching"""
        return {
            "case_type": case.case_type.value if case.case_type else "",
            "location_state": case.location_state or "",
            "description_text": case.description or "",
            "risk_score": case.risk_score or 0,
            "has_suspects": len(case.suspects) > 0 if case.suspects else False,
            "has_victims": len(case.victims) > 0 if case.victims else False
        }
    
    def _calculate_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calculate similarity between two cases"""
        similarity_score = 0.0
        total_factors = 0
        
        if features1["case_type"] == features2["case_type"]:
            similarity_score += 0.3
        total_factors += 1
        
        if features1["location_state"] == features2["location_state"]:
            similarity_score += 0.2
        total_factors += 1
        
        if features1["risk_score"] and features2["risk_score"]:
            risk_diff = abs(features1["risk_score"] - features2["risk_score"])
            risk_similarity = max(0, 1 - (risk_diff / 100))
            similarity_score += risk_similarity * 0.3
        total_factors += 1
        
        text1 = features1["description_text"].lower()
        text2 = features2["description_text"].lower()
        if text1 and text2:
            common_words = set(text1.split()) & set(text2.split())
            text_similarity = len(common_words) / max(len(text1.split()), len(text2.split()))
            similarity_score += text_similarity * 0.2
        total_factors += 1
        
        return similarity_score / total_factors if total_factors > 0 else 0
    
    def _identify_matching_factors(self, features1: Dict, features2: Dict) -> List[str]:
        """Identify which factors contributed to the match"""
        factors = []
        
        if features1["case_type"] == features2["case_type"]:
            factors.append("case_type")
        if features1["location_state"] == features2["location_state"]:
            factors.append("location")
        if abs((features1["risk_score"] or 0) - (features2["risk_score"] or 0)) < 20:
            factors.append("risk_level")
            
        return factors
    
    def _generate_fallback_suspect_analysis(self, suspect: Suspect) -> Dict[str, Any]:
        """Generate basic analysis when AI service is unavailable"""
        risk_score = 5.0  # Base risk
        
        if suspect.firearm_access:
            risk_score += 2.0
        if suspect.substance_abuse:
            risk_score += 1.5
        if suspect.criminal_history:
            risk_score += 1.0
        if suspect.mental_health_history:
            risk_score += 1.0
            
        return {
            "psychological_profile": "Basic risk assessment based on available factors",
            "behavioral_patterns": ["Control", "Escalation"] if risk_score > 6 else ["Moderate risk"],
            "risk_factors": self._get_risk_factors(suspect),
            "warning_signs": ["Firearm access", "Substance abuse"] if suspect.firearm_access or suspect.substance_abuse else [],
            "lethality_risk": min(10, risk_score),
            "recommendations": ["Immediate safety planning", "Law enforcement notification"] if risk_score > 7 else ["Safety planning", "Monitoring"],
            "confidence_score": 0.6
        }
    
    def _generate_fallback_victim_analysis(self, victim: Victim) -> Dict[str, Any]:
        """Generate basic victim analysis when AI service is unavailable"""
        vulnerability_score = 3.0  # Base vulnerability
        
        if victim.financial_dependence:
            vulnerability_score += 2.0
        if victim.children_involved:
            vulnerability_score += 1.5
        if victim.prior_dv_reports and victim.prior_dv_reports > 2:
            vulnerability_score += 1.5
            
        return {
            "vulnerability_profile": "Basic vulnerability assessment",
            "trauma_indicators": ["Financial dependence", "Multiple reports"] if vulnerability_score > 5 else [],
            "risk_factors": self._get_victim_risk_factors(victim),
            "protective_factors": ["Support system"] if not victim.isolation_level == "high" else [],
            "safety_recommendations": ["Safety planning", "Resource connection", "Legal advocacy"],
            "lethality_risk": min(10, vulnerability_score),
            "confidence_score": 0.6
        }
    
    def _get_risk_factors(self, suspect: Suspect) -> List[str]:
        factors = []
        if suspect.firearm_access:
            factors.append("Firearm access")
        if suspect.substance_abuse:
            factors.append("Substance abuse")
        if suspect.criminal_history:
            factors.append("Criminal history")
        if suspect.mental_health_history:
            factors.append("Mental health concerns")
        return factors
    
    def _get_victim_risk_factors(self, victim: Victim) -> List[str]:
        factors = []
        if victim.financial_dependence:
            factors.append("Financial dependence")
        if victim.children_involved:
            factors.append("Children involved")
        if victim.isolation_level == "high":
            factors.append("Social isolation")
        if victim.prior_dv_reports and victim.prior_dv_reports > 2:
            factors.append("Multiple prior reports")
        return factors
