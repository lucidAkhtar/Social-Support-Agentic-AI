"""
Base Agent Interface - All agents inherit from this
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
from datetime import datetime


class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, agent_name: str, config: Optional[Dict[str, Any]] = None):
        self.agent_name = agent_name
        self.config = config or {}
        self.logger = logging.getLogger(f"agent.{agent_name}")
        self.execution_count = 0
        self.last_execution = None
        
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method - must be implemented by all agents
        
        Args:
            input_data: Input data for the agent
            
        Returns:
            Output data from the agent
        """
        pass
    
    def log_execution(self, input_data: Dict[str, Any], output_data: Dict[str, Any], 
                     duration: float, success: bool):
        """Log agent execution for observability"""
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
        """Create a summary of data for logging"""
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
        """Validate input data - can be overridden"""
        return True
    
    async def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """Validate output data - can be overridden"""
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent_name": self.agent_name,
            "execution_count": self.execution_count,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "config": self.config
        }
