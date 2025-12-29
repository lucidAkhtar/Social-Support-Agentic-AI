from typing import TypedDict, Dict, Any
from langgraph.graph import StateGraph, END
from src.agents.extraction_agent import ExtractionAgent
from src.agents.decision_agent import DecisionAgent

class ApplicationState(TypedDict):
    application_id: str
    data: Dict[str, Any]
    extracted_data: Dict[str, Any]
    decision: Dict[str, Any]
    status: str

class ApplicationWorkflow:
    def __init__(self):
        self.extraction_agent = ExtractionAgent()
        self.decision_agent = DecisionAgent()
        self.workflow = self._build_workflow()
    
    def _build_workflow(self):
        workflow = StateGraph(ApplicationState)
        
        workflow.add_node("extract", self.extract_node)
        workflow.add_node("decide", self.decide_node)
        
        workflow.set_entry_point("extract")
        workflow.add_edge("extract", "decide")
        workflow.add_edge("decide", END)
        
        return workflow.compile()
    
    def extract_node(self, state: ApplicationState):
        result = self.extraction_agent.process(state['data'])
        state['extracted_data'] = result
        state['status'] = 'extracted'
        return state
    
    def decide_node(self, state: ApplicationState):
        result = self.decision_agent.process(state['data'])
        state['decision'] = result
        state['status'] = 'completed'
        return state
    
    def process(self, application_id: str, data: Dict[str, Any]):
        initial_state = {
            "application_id": application_id,
            "data": data,
            "extracted_data": {},
            "decision": {},
            "status": "started"
        }
        return self.workflow.invoke(initial_state)