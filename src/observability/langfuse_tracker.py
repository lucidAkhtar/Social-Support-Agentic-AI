"""
Langfuse integration for end-to-end AI observability
Tracks: extraction, validation, ML scoring, decision making, recommendations
Exports metrics to Langfuse cloud or local instance
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import time
import json
from pathlib import Path

# Try to import Langfuse; gracefully degrade if not available
try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False


class LangfuseTracker:
    """
    Observability tracker for application processing pipeline.
    
    Features:
    - Trace each processing stage
    - Track latency and tokens
    - Log errors and exceptions
    - Export metrics for analysis
    - Graceful fallback if Langfuse unavailable
    """
    
    def __init__(self, 
                 public_key: Optional[str] = None,
                 secret_key: Optional[str] = None,
                 host: Optional[str] = None,
                 local_export_path: str = "data/observability"):
        """
        Initialize Langfuse tracker.
        
        Args:
            public_key: Langfuse public API key
            secret_key: Langfuse secret API key
            host: Langfuse host URL (for self-hosted)
            local_export_path: Path to export metrics locally if Langfuse unavailable
        """
        self.local_export_path = Path(local_export_path)
        self.local_export_path.mkdir(parents=True, exist_ok=True)
        
        self.langfuse = None
        self.fallback_mode = False
        
        # Try to initialize Langfuse with error suppression
        if LANGFUSE_AVAILABLE and public_key and secret_key:
            try:
                init_kwargs = {
                    "public_key": public_key,
                    "secret_key": secret_key,
                    "disabled": False
                }
                if host:
                    init_kwargs["host"] = host
                
                self.langfuse = Langfuse(**init_kwargs)
            except Exception as e:
                self.fallback_mode = True
        else:
            self.fallback_mode = True
        
        # Local metric storage
        self.traces: Dict[str, Dict[str, Any]] = {}
        self.current_trace_id: Optional[str] = None
        
    def start_trace(self, trace_id: str, application_id: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start a new trace for application processing"""
        self.current_trace_id = trace_id
        
        trace_data = {
            "trace_id": trace_id,
            "application_id": application_id,
            "start_time": datetime.now().isoformat(),
            "metadata": metadata or {},
            "spans": [],
            "metrics": {}
        }
        
        self.traces[trace_id] = trace_data
        
        if self.langfuse and not self.fallback_mode:
            try:
                self.langfuse.trace(
                    name=f"application_processing_{application_id}",
                    id=trace_id,
                    metadata=metadata
                )
            except Exception as e:
                print(f"⚠ Langfuse trace failed: {e}")
        
        return trace_id
    
    def log_span(self, span_name: str, span_type: str, 
                input_data: Optional[Dict] = None,
                output_data: Optional[Dict] = None,
                duration: Optional[float] = None,
                metadata: Optional[Dict] = None) -> str:
        """
        Log a processing span (e.g., extraction, validation).
        
        Args:
            span_name: Name of the operation (e.g., "extraction_stage")
            span_type: Type of span (e.g., "agent", "model", "database")
            input_data: Input to the operation
            output_data: Output from the operation
            duration: Processing time in seconds
            metadata: Additional metadata
        """
        span_id = f"{span_name}_{int(time.time() * 1000)}"
        
        span_data = {
            "span_id": span_id,
            "name": span_name,
            "type": span_type,
            "start_time": datetime.now().isoformat(),
            "duration": duration or 0,
            "input": input_data,
            "output": output_data,
            "metadata": metadata or {}
        }
        
        # Add to current trace
        if self.current_trace_id and self.current_trace_id in self.traces:
            self.traces[self.current_trace_id]["spans"].append(span_data)
        
        if self.langfuse and not self.fallback_mode:
            try:
                self.langfuse.span(
                    trace_id=self.current_trace_id,
                    name=span_name,
                    input=input_data,
                    output=output_data,
                    metadata=metadata,
                    end_time=time.time() + (duration or 0)
                )
            except Exception as e:
                print(f"⚠ Langfuse span failed: {e}")
        
        return span_id
    
    def log_extraction(self, application_id: str, 
                      extracted_fields: int,
                      confidence: float,
                      duration: float,
                      errors: Optional[List[str]] = None):
        """Log extraction stage results"""
        self.log_span(
            span_name="extraction_stage",
            span_type="agent",
            input_data={"application_id": application_id},
            output_data={
                "fields_extracted": extracted_fields,
                "confidence": confidence,
                "errors": errors or []
            },
            duration=duration,
            metadata={
                "agent": "ExtractionAgent",
                "model": "Mistral 7B"
            }
        )
    
    def log_validation(self, application_id: str,
                      quality_score: float,
                      issues_found: int,
                      duration: float,
                      auto_corrected: int = 0):
        """Log validation stage results"""
        self.log_span(
            span_name="validation_stage",
            span_type="agent",
            input_data={"application_id": application_id},
            output_data={
                "quality_score": quality_score,
                "issues_found": issues_found,
                "auto_corrected": auto_corrected
            },
            duration=duration,
            metadata={
                "agent": "ValidationAgent",
                "validation_rules_applied": 15
            }
        )
    
    def log_ml_scoring(self, application_id: str,
                      eligibility_score: float,
                      model_confidence: float,
                      duration: float,
                      features_used: int = 8):
        """Log ML model scoring results"""
        self.log_span(
            span_name="ml_scoring_stage",
            span_type="model",
            input_data={"application_id": application_id, "features": features_used},
            output_data={
                "eligibility_score": eligibility_score,
                "confidence": model_confidence
            },
            duration=duration,
            metadata={
                "model": "GradientBoostingClassifier",
                "accuracy": 0.98,
                "features": features_used
            }
        )
    
    def log_decision(self, application_id: str,
                    decision: str,
                    confidence: float,
                    duration: float,
                    rationale: Optional[str] = None):
        """Log decision making stage results"""
        self.log_span(
            span_name="decision_stage",
            span_type="agent",
            input_data={"application_id": application_id},
            output_data={
                "decision": decision,
                "confidence": confidence,
                "rationale": rationale
            },
            duration=duration,
            metadata={
                "agent": "DecisionAgent",
                "decision_framework": "Eligibility + Income Assessment"
            }
        )
    
    def log_recommendations(self, application_id: str,
                           recommendation_count: int,
                           duration: float,
                           programs: Optional[List[str]] = None):
        """Log recommendations generation results"""
        self.log_span(
            span_name="recommendations_stage",
            span_type="agent",
            input_data={"application_id": application_id},
            output_data={
                "recommendations_generated": recommendation_count,
                "programs": programs or []
            },
            duration=duration,
            metadata={
                "agent": "RecommendationEngine",
                "enablement_programs": ["job_matching", "upskilling", "career_counseling"]
            }
        )
    
    def log_error(self, application_id: str,
                 stage: str,
                 error_message: str,
                 error_type: str = "RuntimeError"):
        """Log errors during processing"""
        error_span = {
            "span_id": f"error_{int(time.time() * 1000)}",
            "name": f"error_{stage}",
            "type": "error",
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": error_message,
            "stage": stage,
            "application_id": application_id
        }
        
        if self.current_trace_id and self.current_trace_id in self.traces:
            self.traces[self.current_trace_id]["spans"].append(error_span)
        
        if self.langfuse and not self.fallback_mode:
            try:
                self.langfuse.event(
                    trace_id=self.current_trace_id,
                    name=f"error_{stage}",
                    input={"error": error_message},
                    metadata={"error_type": error_type}
                )
            except Exception as e:
                print(f"⚠ Langfuse error logging failed: {e}")
    
    def end_trace(self) -> Dict[str, Any]:
        """Complete the current trace and return summary"""
        if not self.current_trace_id or self.current_trace_id not in self.traces:
            return {}
        
        trace = self.traces[self.current_trace_id]
        trace["end_time"] = datetime.now().isoformat()
        
        # Calculate metrics
        total_duration = sum(span.get("duration", 0) for span in trace["spans"] 
                           if span.get("type") != "error")
        trace["metrics"]["total_duration"] = total_duration
        trace["metrics"]["span_count"] = len(trace["spans"])
        trace["metrics"]["error_count"] = len([s for s in trace["spans"] if s.get("type") == "error"])
        
        # Export locally
        self._export_trace_local(trace)
        
        return trace
    
    def _export_trace_local(self, trace: Dict[str, Any]):
        """Export trace to local JSON file"""
        try:
            export_file = self.local_export_path / f"trace_{trace['trace_id']}.json"
            with open(export_file, "w") as f:
                json.dump(trace, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠ Failed to export trace locally: {e}")
    
    def export_all_traces(self, output_file: Optional[str] = None) -> str:
        """Export all traces to JSON file"""
        output_file = output_file or str(self.local_export_path / "all_traces.json")
        
        try:
            # Prepare summary
            summary = {
                "export_time": datetime.now().isoformat(),
                "trace_count": len(self.traces),
                "traces": list(self.traces.values())
            }
            
            # Calculate aggregate metrics
            all_durations = []
            all_errors = 0
            
            for trace in self.traces.values():
                all_durations.extend([s.get("duration", 0) for s in trace.get("spans", []) 
                                     if s.get("type") != "error"])
                all_errors += trace["metrics"].get("error_count", 0)
            
            summary["aggregate_metrics"] = {
                "total_processing_time": sum(all_durations),
                "average_processing_time": sum(all_durations) / len(all_durations) if all_durations else 0,
                "total_errors": all_errors
            }
            
            # Write to file
            with open(output_file, "w") as f:
                json.dump(summary, f, indent=2, default=str)
            
            print(f"✓ Traces exported to {output_file}")
            return output_file
            
        except Exception as e:
            print(f"⚠ Failed to export traces: {e}")
            return ""
    
    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """Get summary of a specific trace"""
        if trace_id not in self.traces:
            return {}
        
        trace = self.traces[trace_id]
        
        return {
            "trace_id": trace["trace_id"],
            "application_id": trace["application_id"],
            "duration": trace["metrics"].get("total_duration", 0),
            "span_count": trace["metrics"].get("span_count", 0),
            "error_count": trace["metrics"].get("error_count", 0),
            "stages": [s["name"] for s in trace.get("spans", []) if s.get("type") != "error"],
            "errors": [s["error_message"] for s in trace.get("spans", []) if s.get("type") == "error"]
        }
    
    def flush(self):
        """Flush pending data to Langfuse"""
        if self.langfuse and not self.fallback_mode:
            try:
                self.langfuse.flush()
                print("✓ Langfuse data flushed")
            except Exception as e:
                print(f"⚠ Langfuse flush failed: {e}")


class ObservabilityIntegration:
    """Integration point for orchestrator to use LangfuseTracker"""
    
    _tracker: Optional[LangfuseTracker] = None
    
    @classmethod
    def initialize(cls, public_key: Optional[str] = None,
                   secret_key: Optional[str] = None,
                   host: Optional[str] = None) -> LangfuseTracker:
        """Initialize global tracker"""
        cls._tracker = LangfuseTracker(
            public_key=public_key,
            secret_key=secret_key,
            host=host
        )
        return cls._tracker
    
    @classmethod
    def get_tracker(cls) -> LangfuseTracker:
        """Get current tracker or create default"""
        if cls._tracker is None:
            cls._tracker = LangfuseTracker()
        return cls._tracker


if __name__ == "__main__":
    # Example usage
    tracker = LangfuseTracker()
    
    # Start trace
    trace_id = tracker.start_trace("trace_001", "app_001", {"version": "1.0"})
    
    # Log stages
    tracker.log_extraction("app_001", extracted_fields=25, confidence=0.92, duration=2.3)
    tracker.log_validation("app_001", quality_score=0.88, issues_found=2, duration=1.1, auto_corrected=2)
    tracker.log_ml_scoring("app_001", eligibility_score=0.78, model_confidence=0.95, duration=0.5)
    tracker.log_decision("app_001", decision="approve", confidence=0.82, duration=0.8)
    tracker.log_recommendations("app_001", recommendation_count=4, duration=0.6, 
                               programs=["job_matching", "upskilling"])
    
    # End trace and export
    trace = tracker.end_trace()
    tracker.export_all_traces()
    
    print("\n" + json.dumps(tracker.get_trace_summary(trace_id), indent=2))
