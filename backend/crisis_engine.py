import json
from ai_model import CrisisModel
from services.risk_engine import calculate_risk
from services.resolver import resolve_conflicts
from services.dispatcher import execute_dispatch
from services.surveillance import surveillance_monitor
from services.audit import record_event


class CrisisEngine:
    """
    Crisis management engine that orchestrates the entire crisis response pipeline.
    
    Handles:
    - Crisis detection and extraction using AI model
    - Risk assessment
    - Resource conflict resolution
    - Dispatch execution
    - Surveillance monitoring
    - Audit logging
    """
    
    def __init__(self, crisis_model: CrisisModel):
        """
        Initialize the CrisisEngine with a crisis detection model.
        
        Args:
            crisis_model: An instance of CrisisModel for extracting crisis information
        """
        self.model = crisis_model
        
        # Default resource pool for crisis response
        self.resource_pool = {
            "Fire": 2,
            "Flood": 2,
            "Gas Leak": 1,
            "Accident": 2,
            "Earthquake": 1
        }
    
    def process_crises(self, crisis_texts: list, approved: bool) -> dict:
        """
        Process incoming crisis reports through the complete crisis management pipeline.
        
        Args:
            crisis_texts: List of text descriptions of crises to process
            approved: Boolean indicating if high-risk actions are pre-approved
        
        Returns:
            Dictionary with either:
            - PENDING_APPROVAL status if high-risk cases need authorization
            - EXECUTED status if crises were processed and dispatched
        
        Example:
            engine = CrisisEngine(model)
            result = engine.process_crises(["Fire downtown"], approved=False)
        """
        crises = []
        
        # Step 1: Extract crisis information from each text
        for text in crisis_texts:
            raw_output = self.model.extract_crisis(text)
            
            # Parse the model output to extract JSON
            try:
                # Try to extract JSON from the response
                crisis_data = self._parse_crisis_response(raw_output)
            except Exception as e:
                # Fallback if parsing fails
                crisis_data = {
                    "crisis_type": "Unknown",
                    "location": "Unknown",
                    "severity": "Low"
                }
            
            # Step 2: Calculate risk score
            crisis_data["risk_score"] = calculate_risk(crisis_data)
            crises.append(crisis_data)
        
        # Step 3: Record crisis received event
        record_event("CRISIS_RECEIVED", {
            "count": len(crises),
            "crises": crises
        })
        
        # Step 4: Resolve conflicts using resource allocation
        decision_output = resolve_conflicts(crises, self.resource_pool)
        
        # Step 5: Record decision made event
        record_event("DECISION_MADE", {
            "allocated": len(decision_output["decisions"]),
            "delayed": len(decision_output["tradeoffs"])
        })
        
        # Step 6: Check for high-risk cases requiring approval
        high_risk_cases = [
            d for d in decision_output["decisions"] 
            if d.get("risk_score", 0) >= 4
        ]
        
        if high_risk_cases and not approved:
            # Authorization required
            record_event("AUTHORIZATION_REQUIRED", {
                "high_risk_count": len(high_risk_cases),
                "risks": high_risk_cases
            })
            
            return {
                "status": "PENDING_APPROVAL",
                "details": high_risk_cases
            }
        
        # Step 7: Execute dispatch and surveillance
        execution_result = execute_dispatch(decision_output)
        alerts = surveillance_monitor(decision_output)
        
        # Record execution event
        record_event("EXECUTION_COMPLETED", {
            "execution_status": execution_result["execution_status"],
            "dispatch_count": len(execution_result["dispatch_log"]),
            "alert_count": len(alerts)
        })
        
        return {
            "status": "EXECUTED",
            "execution_result": execution_result,
            "alerts": alerts
        }
    
    def _parse_crisis_response(self, raw_output: str) -> dict:
        """
        Parse crisis information from model output.
        
        Args:
            raw_output: Raw string output from the crisis model
        
        Returns:
            Dictionary with parsed crisis data
        """
        # Try to find JSON in the output
        try:
            # Look for JSON-like pattern in the output
            start_idx = raw_output.find('{')
            end_idx = raw_output.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = raw_output[start_idx:end_idx]
                crisis_data = json.loads(json_str)
                return crisis_data
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Fallback: return minimal crisis data
        return {
            "crisis_type": "Unknown",
            "location": "Unknown",
            "severity": "Low"
        }
