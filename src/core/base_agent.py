"""
Base Agent Interface - Foundation for all agents in the social support system.

PURPOSE:
    Abstract base class that defines the contract and common functionality for all agents.
    Provides execution lifecycle management, logging, and observability hooks.

ARCHITECTURE:
    - Abstract base class pattern for agent polymorphism
    - Built-in execution tracking and observability
    - Standard logging interface across all agents
    - Validation hooks for input/output integrity

DEPENDENCIES:
    - Used by: All 6 agents (extraction, validation, eligibility, recommendation, explanation, rag_chatbot)
    - Imported by: orchestrator.py to manage agent pipeline
    - Core abstraction that enables agent swapping and testing

USAGE:
    All agents inherit from BaseAgent and implement the execute() method:
    ```python
    class MyAgent(BaseAgent):
        async def execute(self, input_data: Dict) -> Dict:
            # Agent-specific logic
            pass
    ```

OBSERVABILITY:
    - Tracks execution count and timestamps
    - Logs execution duration, success/failure
    - Data summarization for privacy-safe logging
    - Integration with Langfuse for distributed tracing

Author: Core Infrastructure Team
Version: 2.0 - Production Grade
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
from datetime import datetime


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    
    Provides:
        - Standard initialization with name and config
        - Execution tracking and logging
        - Input/output validation hooks
        - Status reporting for monitoring
    """
    
    def __init__(self, agent_name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base agent.
        
        Args:
            agent_name: Unique identifier for this agent (e.g., "ExtractionAgent")
            config: Optional configuration dictionary for agent-specific settings
        """
        self.agent_name = agent_name
        self.config = config or {}
        self.logger = logging.getLogger(f"agent.{agent_name}")
        self.execution_count = 0
        self.last_execution = None
        
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method that all agents must implement.
        
        This is the core business logic method that performs the agent's task.
        Agents receive input data, process it, and return output data.
        
        Args:
            input_data: Dictionary containing all input parameters required by the agent.
                       Structure varies by agent type but typically includes:
                       - application_id: Unique application identifier
                       - Agent-specific data (documents, extracted_data, etc.)
            
        Returns:
            Dictionary containing agent execution results. Structure varies by agent:
                - extraction_agent: {"extracted_data": ExtractedData, "extraction_time": float}
                - validation_agent: {"validation_report": ValidationReport}
                - eligibility_agent: {"eligibility_result": EligibilityResult}
                - recommendation_agent: {"recommendation": Recommendation}
                - explanation_agent: {"explanation": str, "confidence": float}
                
        Raises:
            NotImplementedError: If subclass doesn't implement this method
            ValueError: For invalid input data
            Exception: For agent-specific processing errors
        """
        pass
    
    def log_execution(self, input_data: Dict[str, Any], output_data: Dict[str, Any], 
                     duration: float, success: bool):
        """
        Log agent execution for observability and debugging.
        
        Creates structured log entries with execution metadata, timing, and data summaries.
        Integrates with centralized logging and monitoring systems.
        
        Args:
            input_data: Input data passed to execute()
            output_data: Output data returned from execute()
            duration: Execution time in seconds
            success: Whether execution completed successfully
        """
        self.execution_count += 1
        self.last_execution = datetime.now()
        
        log_entry = {
            "agent": self.agent_name,
            "timestamp": self.last_execution.isoformat(),
            "execution_count": self.execution_count,
            "duration_seconds": duration,
            "success": success,
            "input_summary": self._summarize_data(input_data),
            "output_summary": self._summarize_data(output_data)
        }
        
        if success:
            self.logger.info(f"Execution completed", extra=log_entry)
        else:
            self.logger.error(f"Execution failed", extra=log_entry)
    
    def _summarize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create privacy-safe summary of data for logging.
        
        Avoids logging sensitive PII by summarizing complex objects as type names
        and sizes. Only logs primitive types that are safe for log aggregation.
        
        Args:
            data: Dictionary of data to summarize
            
        Returns:
            Dictionary with safe summaries (primitives kept, complex objects summarized)
        """
        summary = {}
        for key, value in data.items():
            if isinstance(value, (str, int, float, bool)):
                summary[key] = value
            elif isinstance(value, (list, dict)):
                summary[key] = f"{type(value).__name__} with {len(value)} items"
            else:
                summary[key] = type(value).__name__
        return summary
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data before execution.
        
        Override in subclasses to implement agent-specific validation logic.
        Called before execute() to ensure data integrity.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if input is valid, False otherwise
        """
        return True
    
    async def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """
        Validate output data after execution.
        
        Override in subclasses to implement agent-specific validation logic.
        Called after execute() to ensure output integrity.
        
        Args:
            output_data: Output data to validate
            
        Returns:
            True if output is valid, False otherwise
        """
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status for monitoring and health checks.
        
        Returns:
            Dictionary containing:
                - agent_name: Agent identifier
                - execution_count: Total executions since initialization
                - last_execution: ISO timestamp of last execution (None if never run)
                - config: Current configuration
        """
        return {
            "agent_name": self.agent_name,
            "execution_count": self.execution_count,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "config": self.config
        }
