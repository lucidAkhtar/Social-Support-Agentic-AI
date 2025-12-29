"""
LangGraph-based Agent Orchestration for Social Support Application Processing
Implements ReAct reasoning framework with multi-agent collaboration
"""

from typing import TypedDict, Annotated, Sequence, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_community.llms import Ollama
from langfuse import Langfuse
import operator
import logging
from datetime import datetime

from src.agents.extraction_agent import ExtractionAgent
from src.agents.validation_agent import ValidationAgent
from src.agents.eligibility_agent import EligibilityAgent
from src.agents.decision_agent import DecisionAgent
from src.agents.enablement_agent import EnablementAgent
from src.models.ml_models import RiskScorer, FraudDetector, EligibilityClassifier

logger = logging.getLogger(__name__)


class ApplicationState(TypedDict):
    """Shared state across all agents in the workflow"""
    application_id: str
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # Raw Input Data
    form_data: Dict[str, Any]
    uploaded_files: Dict[str, bytes]
    
    # Extracted Data
    extracted_data: Dict[str, Any]
    emirates_id_info: Dict[str, Any]
    bank_statement_data: Dict[str, Any]
    resume_data: Dict[str, Any]
    assets_data: Dict[str, Any]
    credit_report_data: Dict[str, Any]
    
    # Validation Results
    validation_status: str
    inconsistencies: List[Dict[str, Any]]
    data_quality_score: float
    
    # ML Predictions
    risk_score: float
    fraud_probability: float
    eligibility_prediction: str
    eligibility_confidence: float
    
    # Decision
    final_decision: str  # 'approved', 'soft_decline', 'manual_review'
    decision_reasoning: str
    explainability: Dict[str, Any]
    
    # Enablement Recommendations
    upskilling_recommendations: List[Dict[str, Any]]
    job_matches: List[Dict[str, Any]]
    career_counseling: Dict[str, Any]
    
    # Workflow Control
    current_step: str
    needs_human_review: bool
    error_messages: List[str]
    retry_count: int
    
    # Observability
    trace_id: str
    start_time: str
    processing_time: float


class SocialSupportOrchestrator:
    """
    Master orchestrator implementing ReAct framework for agent coordination
    """
    
    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        langfuse_public_key: str = None,
        langfuse_secret_key: str = None
    ):
        self.llm = Ollama(
            base_url=ollama_base_url,
            model="llama3.1:8b",
            temperature=0.1
        )
        
        # Initialize Langfuse for observability
        self.langfuse = None
        if langfuse_public_key and langfuse_secret_key:
            self.langfuse = Langfuse(
                public_key=langfuse_public_key,
                secret_key=langfuse_secret_key
            )
        
        # Initialize all agents
        self.extraction_agent = ExtractionAgent(self.llm)
        self.validation_agent = ValidationAgent(self.llm)
        self.eligibility_agent = EligibilityAgent(self.llm)
        self.decision_agent = DecisionAgent(self.llm)
        self.enablement_agent = EnablementAgent(self.llm)
        
        # Initialize ML models
        self.risk_scorer = RiskScorer()
        self.fraud_detector = FraudDetector()
        self.eligibility_classifier = EligibilityClassifier()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """
        Build LangGraph workflow with ReAct reasoning
        """
        workflow = StateGraph(ApplicationState)
        
        # Add nodes for each processing step
        workflow.add_node("initialize", self.initialize_application)
        workflow.add_node("extract_data", self.extract_data_node)
        workflow.add_node("validate_data", self.validate_data_node)
        workflow.add_node("assess_risk", self.assess_risk_node)
        workflow.add_node("check_eligibility", self.check_eligibility_node)
        workflow.add_node("make_decision", self.make_decision_node)
        workflow.add_node("generate_recommendations", self.generate_recommendations_node)
        workflow.add_node("finalize", self.finalize_application)
        workflow.add_node("handle_error", self.handle_error_node)
        
        # Define the workflow edges
        workflow.set_entry_point("initialize")
        
        workflow.add_edge("initialize", "extract_data")
        workflow.add_conditional_edges(
            "extract_data",
            self.check_extraction_success,
            {
                "success": "validate_data",
                "retry": "extract_data",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "validate_data",
            self.check_validation_success,
            {
                "valid": "assess_risk",
                "minor_issues": "assess_risk",
                "major_issues": "handle_error"
            }
        )
        
        workflow.add_edge("assess_risk", "check_eligibility")
        workflow.add_edge("check_eligibility", "make_decision")
        
        workflow.add_conditional_edges(
            "make_decision",
            self.check_decision_type,
            {
                "approved": "generate_recommendations",
                "soft_decline": "generate_recommendations",
                "manual_review": "finalize"
            }
        )
        
        workflow.add_edge("generate_recommendations", "finalize")
        workflow.add_edge("handle_error", END)
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    # ==================== NODE IMPLEMENTATIONS ====================
    
    def initialize_application(self, state: ApplicationState) -> ApplicationState:
        """Initialize application processing"""
        logger.info(f"Initializing application {state['application_id']}")
        
        state["current_step"] = "initialization"
        state["start_time"] = datetime.utcnow().isoformat()
        state["retry_count"] = 0
        state["error_messages"] = []
        state["needs_human_review"] = False
        
        # Create Langfuse trace
        if self.langfuse:
            trace = self.langfuse.trace(
                name="social_support_application",
                input={"application_id": state["application_id"]},
                metadata={"start_time": state["start_time"]}
            )
            state["trace_id"] = trace.id
        
        state["messages"].append(
            AIMessage(content=f"Application {state['application_id']} initialized. Starting data extraction...")
        )
        
        return state
    
    def extract_data_node(self, state: ApplicationState) -> ApplicationState:
        """Extract data from all uploaded documents using ReAct"""
        logger.info(f"Extracting data from documents for {state['application_id']}")
        
        state["current_step"] = "data_extraction"
        
        try:
            # ReAct Reasoning: Thought -> Action -> Observation
            thought = "I need to extract structured data from multiple document types"
            action = "Use specialized extraction tools for each document type"
            
            # Extract Emirates ID
            if "emirates_id" in state["uploaded_files"]:
                state["emirates_id_info"] = self.extraction_agent.extract_emirates_id(
                    state["uploaded_files"]["emirates_id"]
                )
            
            # Extract Bank Statement
            if "bank_statement" in state["uploaded_files"]:
                state["bank_statement_data"] = self.extraction_agent.extract_bank_statement(
                    state["uploaded_files"]["bank_statement"]
                )
            
            # Extract Resume
            if "resume" in state["uploaded_files"]:
                state["resume_data"] = self.extraction_agent.extract_resume(
                    state["uploaded_files"]["resume"]
                )
            
            # Extract Assets/Liabilities Excel
            if "assets_excel" in state["uploaded_files"]:
                state["assets_data"] = self.extraction_agent.extract_excel_data(
                    state["uploaded_files"]["assets_excel"]
                )
            
            # Extract Credit Report
            if "credit_report" in state["uploaded_files"]:
                state["credit_report_data"] = self.extraction_agent.extract_credit_report(
                    state["uploaded_files"]["credit_report"]
                )
            
            # Consolidate extracted data
            state["extracted_data"] = self.extraction_agent.consolidate_data({
                "emirates_id": state.get("emirates_id_info", {}),
                "bank_statement": state.get("bank_statement_data", {}),
                "resume": state.get("resume_data", {}),
                "assets": state.get("assets_data", {}),
                "credit_report": state.get("credit_report_data", {})
            })
            
            observation = f"Successfully extracted data from {len(state['uploaded_files'])} documents"
            
            state["messages"].append(
                AIMessage(content=f"Data extraction completed. {observation}")
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            state["error_messages"].append(f"Extraction error: {str(e)}")
            state["retry_count"] += 1
            return state
    
    def validate_data_node(self, state: ApplicationState) -> ApplicationState:
        """Validate and cross-reference extracted data"""
        logger.info(f"Validating data for {state['application_id']}")
        
        state["current_step"] = "data_validation"
        
        try:
            # Perform cross-validation
            validation_result = self.validation_agent.validate(
                form_data=state["form_data"],
                extracted_data=state["extracted_data"]
            )
            
            state["validation_status"] = validation_result["status"]
            state["inconsistencies"] = validation_result["inconsistencies"]
            state["data_quality_score"] = validation_result["quality_score"]
            
            # Check for critical inconsistencies
            critical_issues = [
                issue for issue in state["inconsistencies"]
                if issue["severity"] == "critical"
            ]
            
            if len(critical_issues) > 0:
                state["messages"].append(
                    AIMessage(content=f"Found {len(critical_issues)} critical data inconsistencies. Flagging for review.")
                )
                state["needs_human_review"] = True
            else:
                state["messages"].append(
                    AIMessage(content=f"Data validation passed. Quality score: {state['data_quality_score']:.2f}")
                )
            
            return state
            
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            state["error_messages"].append(f"Validation error: {str(e)}")
            return state
    
    def assess_risk_node(self, state: ApplicationState) -> ApplicationState:
        """Assess financial risk and detect fraud"""
        logger.info(f"Assessing risk for {state['application_id']}")
        
        state["current_step"] = "risk_assessment"
        
        try:
            # Prepare features for ML models
            features = self._prepare_ml_features(state)
            
            # Risk scoring
            state["risk_score"] = self.risk_scorer.predict(features)
            
            # Fraud detection
            state["fraud_probability"] = self.fraud_detector.predict_proba(features)
            
            # Flag high-risk applications
            if state["risk_score"] > 0.7 or state["fraud_probability"] > 0.5:
                state["needs_human_review"] = True
                state["messages"].append(
                    AIMessage(content=f"High risk detected (Risk: {state['risk_score']:.2f}, Fraud: {state['fraud_probability']:.2f}). Flagging for review.")
                )
            else:
                state["messages"].append(
                    AIMessage(content=f"Risk assessment completed. Risk score: {state['risk_score']:.2f}")
                )
            
            return state
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {str(e)}")
            state["error_messages"].append(f"Risk assessment error: {str(e)}")
            return state
    
    def check_eligibility_node(self, state: ApplicationState) -> ApplicationState:
        """Check eligibility using ML classifier and rule-based system"""
        logger.info(f"Checking eligibility for {state['application_id']}")
        
        state["current_step"] = "eligibility_check"
        
        try:
            # Use eligibility agent with ML classifier
            eligibility_result = self.eligibility_agent.assess(
                extracted_data=state["extracted_data"],
                form_data=state["form_data"],
                risk_score=state["risk_score"]
            )
            
            state["eligibility_prediction"] = eligibility_result["prediction"]
            state["eligibility_confidence"] = eligibility_result["confidence"]
            state["explainability"] = eligibility_result["explainability"]
            
            state["messages"].append(
                AIMessage(content=f"Eligibility assessment: {state['eligibility_prediction']} (confidence: {state['eligibility_confidence']:.2f})")
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Eligibility check failed: {str(e)}")
            state["error_messages"].append(f"Eligibility error: {str(e)}")
            return state
    
    def make_decision_node(self, state: ApplicationState) -> ApplicationState:
        """Make final decision with explainability"""
        logger.info(f"Making decision for {state['application_id']}")
        
        state["current_step"] = "decision_making"
        
        try:
            # Use decision agent with LLM reasoning
            decision_result = self.decision_agent.decide(
                eligibility=state["eligibility_prediction"],
                confidence=state["eligibility_confidence"],
                risk_score=state["risk_score"],
                fraud_probability=state["fraud_probability"],
                data_quality=state["data_quality_score"],
                inconsistencies=state["inconsistencies"],
                needs_review=state["needs_human_review"]
            )
            
            state["final_decision"] = decision_result["decision"]
            state["decision_reasoning"] = decision_result["reasoning"]
            
            state["messages"].append(
                AIMessage(content=f"Decision: {state['final_decision']}. Reasoning: {state['decision_reasoning']}")
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Decision making failed: {str(e)}")
            state["error_messages"].append(f"Decision error: {str(e)}")
            return state
    
    def generate_recommendations_node(self, state: ApplicationState) -> ApplicationState:
        """Generate enablement recommendations"""
        logger.info(f"Generating recommendations for {state['application_id']}")
        
        state["current_step"] = "recommendation_generation"
        
        try:
            # Use enablement agent for personalized recommendations
            recommendations = self.enablement_agent.generate(
                resume_data=state.get("resume_data", {}),
                form_data=state["form_data"],
                decision=state["final_decision"]
            )
            
            state["upskilling_recommendations"] = recommendations["upskilling"]
            state["job_matches"] = recommendations["job_matches"]
            state["career_counseling"] = recommendations["career_counseling"]
            
            state["messages"].append(
                AIMessage(content=f"Generated {len(state['upskilling_recommendations'])} upskilling recommendations and {len(state['job_matches'])} job matches.")
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Recommendation generation failed: {str(e)}")
            state["error_messages"].append(f"Recommendation error: {str(e)}")
            return state
    
    def finalize_application(self, state: ApplicationState) -> ApplicationState:
        """Finalize application and save results"""
        logger.info(f"Finalizing application {state['application_id']}")
        
        state["current_step"] = "finalized"
        end_time = datetime.utcnow()
        start_time = datetime.fromisoformat(state["start_time"])
        state["processing_time"] = (end_time - start_time).total_seconds()
        
        # Complete Langfuse trace
        if self.langfuse and state.get("trace_id"):
            self.langfuse.trace(
                id=state["trace_id"],
                output={
                    "decision": state["final_decision"],
                    "processing_time": state["processing_time"]
                },
                metadata={"end_time": end_time.isoformat()}
            )
        
        state["messages"].append(
            AIMessage(content=f"Application processing completed in {state['processing_time']:.2f} seconds. Final decision: {state['final_decision']}")
        )
        
        return state
    
    def handle_error_node(self, state: ApplicationState) -> ApplicationState:
        """Handle errors and determine retry or escalation"""
        logger.error(f"Handling errors for {state['application_id']}")
        
        state["current_step"] = "error_handling"
        state["final_decision"] = "manual_review"
        state["needs_human_review"] = True
        
        error_summary = "; ".join(state["error_messages"])
        state["decision_reasoning"] = f"Application requires manual review due to errors: {error_summary}"
        
        state["messages"].append(
            AIMessage(content=f"Errors encountered. Application flagged for manual review: {error_summary}")
        )
        
        return state
    
    # ==================== CONDITIONAL EDGE FUNCTIONS ====================
    
    def check_extraction_success(self, state: ApplicationState) -> str:
        """Check if data extraction was successful"""
        if len(state.get("error_messages", [])) > 0:
            if state["retry_count"] < 3:
                return "retry"
            return "error"
        return "success"
    
    def check_validation_success(self, state: ApplicationState) -> str:
        """Check validation results"""
        if state["validation_status"] == "valid":
            return "valid"
        elif state["validation_status"] == "minor_issues":
            return "minor_issues"
        return "major_issues"
    
    def check_decision_type(self, state: ApplicationState) -> str:
        """Route based on decision type"""
        if state["needs_human_review"]:
            return "manual_review"
        return state["final_decision"]
    
    # ==================== HELPER METHODS ====================
    
    def _prepare_ml_features(self, state: ApplicationState) -> Dict[str, Any]:
        """Prepare features for ML models"""
        extracted = state.get("extracted_data", {})
        form = state.get("form_data", {})
        
        return {
            "income": extracted.get("monthly_income", 0),
            "employment_duration": extracted.get("employment_duration_months", 0),
            "family_size": form.get("family_size", 1),
            "total_assets": extracted.get("total_assets", 0),
            "total_liabilities": extracted.get("total_liabilities", 0),
            "credit_score": extracted.get("credit_score", 0),
            "age": extracted.get("age", 0),
            "education_level": extracted.get("education_level", ""),
            "employment_type": extracted.get("employment_type", "")
        }
    
    def process_application(self, initial_state: ApplicationState) -> ApplicationState:
        """Process application through the complete workflow"""
        logger.info(f"Starting application processing: {initial_state['application_id']}")
        
        try:
            # Execute the workflow
            final_state = self.workflow.invoke(initial_state)
            return final_state
        
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            initial_state["error_messages"].append(f"Workflow error: {str(e)}")
            initial_state["final_decision"] = "manual_review"
            initial_state["needs_human_review"] = True
            return initial_state