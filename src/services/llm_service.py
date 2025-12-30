"""
LLM Service - Production-grade Ollama Integration
Handles all LLM interactions with retry logic, fallback, and error handling
"""
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)


@dataclass
class LLMConfig:
    """LLM configuration"""
    base_url: str = "http://localhost:11434"
    model: str = "mistral:latest"  # Default model (use what's installed)
    fallback_model: str = "mistral:latest"  # Same as primary for now
    timeout: int = 120
    max_retries: int = 3
    temperature: float = 0.7
    max_tokens: int = 2000


class LLMService:
    """
    Production-grade LLM service with Ollama integration
    Features:
    - Automatic retries with exponential backoff
    - Fallback to smaller models
    - Connection pooling
    - Error handling and logging
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self.logger = logging.getLogger("LLMService")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Check if Ollama is available
        self._check_ollama_availability()
    
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = self.session.get(
                f"{self.config.base_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                models = response.json().get("models", [])
                self.logger.info(f"Ollama is running. Available models: {len(models)}")
                return True
            else:
                self.logger.warning(f"Ollama returned status {response.status_code}")
                return False
        except Exception as e:
            self.logger.warning(f"Ollama not available: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, TimeoutError)),
        before_sleep=before_sleep_log(logging.getLogger("LLMService"), logging.WARNING)
    )
    def _call_ollama_api(self, 
                        prompt: str, 
                        model: str,
                        temperature: float = 0.7,
                        max_tokens: int = 2000,
                        system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Call Ollama API with retry logic
        
        Args:
            prompt: User prompt
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            
        Returns:
            API response
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        self.logger.debug(f"Calling Ollama API with model: {model}")
        
        response = self.session.post(
            f"{self.config.base_url}/api/generate",
            json=payload,
            timeout=self.config.timeout
        )
        
        response.raise_for_status()
        return response.json()
    
    async def generate(self,
                      prompt: str,
                      max_tokens: Optional[int] = None,
                      temperature: Optional[float] = None,
                      system_prompt: Optional[str] = None,
                      use_fallback: bool = True) -> str:
        """
        Generate text with primary model and fallback
        
        Args:
            prompt: User prompt
            max_tokens: Maximum tokens (defaults to config)
            temperature: Temperature (defaults to config)
            system_prompt: Optional system prompt
            use_fallback: Whether to use fallback model on failure
            
        Returns:
            Generated text
        """
        max_tokens = max_tokens or self.config.max_tokens
        temperature = temperature or self.config.temperature
        
        # Try primary model
        try:
            self.logger.info(f"Generating with primary model: {self.config.model}")
            response = self._call_ollama_api(
                prompt=prompt,
                model=self.config.model,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt
            )
            
            generated_text = response.get("response", "")
            self.logger.info(f"Generated {len(generated_text)} characters")
            return generated_text
            
        except Exception as e:
            self.logger.error(f"Primary model failed: {e}")
            
            if use_fallback:
                # Try fallback model
                try:
                    self.logger.warning(f"Attempting fallback model: {self.config.fallback_model}")
                    response = self._call_ollama_api(
                        prompt=prompt,
                        model=self.config.fallback_model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        system_prompt=system_prompt
                    )
                    
                    generated_text = response.get("response", "")
                    self.logger.info(f"Fallback generated {len(generated_text)} characters")
                    return generated_text
                    
                except Exception as fallback_error:
                    self.logger.error(f"Fallback model also failed: {fallback_error}")
            
            # Both failed - return empty or raise
            raise RuntimeError(f"LLM generation failed: {str(e)}")
    
    async def extract_structured_data(self,
                                     text: str,
                                     fields: List[str],
                                     context: str = "") -> Dict[str, Any]:
        """
        Extract structured data from text using LLM
        
        Args:
            text: Input text
            fields: List of fields to extract
            context: Additional context about the document
            
        Returns:
            Dictionary of extracted fields
        """
        prompt = f"""Extract the following information from the text below.
Return ONLY a JSON object with the requested fields. If a field is not found, use null.

Requested fields: {', '.join(fields)}

{context}

Text:
{text}

JSON Output:"""
        
        try:
            response = await self.generate(
                prompt=prompt,
                temperature=0.1,  # Low temperature for extraction
                max_tokens=1000
            )
            
            # Try to parse JSON from response
            import json
            import re
            
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                extracted = json.loads(json_match.group())
                self.logger.info(f"Extracted {len(extracted)} fields")
                return extracted
            else:
                self.logger.warning("No JSON found in response")
                return {field: None for field in fields}
                
        except Exception as e:
            self.logger.error(f"Structured extraction failed: {e}")
            return {field: None for field in fields}
    
    async def analyze_document(self,
                              text: str,
                              document_type: str,
                              questions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze document and answer questions
        
        Args:
            text: Document text
            document_type: Type of document (resume, bank_statement, etc.)
            questions: List of questions to answer
            
        Returns:
            Analysis results
        """
        if not questions:
            questions = self._get_default_questions(document_type)
        
        prompt = f"""Analyze this {document_type} and answer the following questions.
Be concise and factual.

Document:
{text}

Questions:
"""
        for i, q in enumerate(questions, 1):
            prompt += f"\n{i}. {q}"
        
        prompt += "\n\nAnswers:"
        
        try:
            response = await self.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=1500
            )
            
            return {
                "document_type": document_type,
                "analysis": response,
                "questions": questions
            }
            
        except Exception as e:
            self.logger.error(f"Document analysis failed: {e}")
            return {
                "document_type": document_type,
                "analysis": "",
                "error": str(e)
            }
    
    def _get_default_questions(self, document_type: str) -> List[str]:
        """Get default questions for document type"""
        questions_map = {
            "resume": [
                "What is the applicant's current position?",
                "How many years of experience do they have?",
                "What is their employment status?",
                "What are their key skills?"
            ],
            "bank_statement": [
                "What is the average monthly income?",
                "What is the average monthly expense?",
                "What is the account balance trend?",
                "Are there any irregularities?"
            ],
            "credit_report": [
                "What is the credit score?",
                "What is the outstanding debt?",
                "What is the payment history?",
                "Are there any defaults or late payments?"
            ]
        }
        
        return questions_map.get(document_type, [
            "What are the key details in this document?",
            "Are there any concerning factors?"
        ])
    
    async def chat(self,
                  query: str,
                  context: Optional[Dict[str, Any]] = None,
                  history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Chat interface for chatbot
        
        Args:
            query: User query
            context: Application context
            history: Conversation history
            
        Returns:
            Response text
        """
        system_prompt = """You are a helpful social support case assistant. 
You help applicants understand their eligibility decisions, simulate scenarios, 
and explain the assessment process. Be empathetic, clear, and factual."""
        
        # Build context-aware prompt
        prompt = ""
        if context:
            prompt += "Application Context:\n"
            for key, value in context.items():
                prompt += f"- {key}: {value}\n"
            prompt += "\n"
        
        if history:
            prompt += "Conversation History:\n"
            for turn in history[-5:]:  # Last 5 turns
                prompt += f"User: {turn.get('user', '')}\n"
                prompt += f"Assistant: {turn.get('assistant', '')}\n"
            prompt += "\n"
        
        prompt += f"User Query: {query}\n\nResponse:"
        
        try:
            response = await self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.8,
                max_tokens=800
            )
            return response
        except Exception as e:
            self.logger.error(f"Chat generation failed: {e}")
            return "I apologize, but I'm having trouble processing your request. Please try again or contact support."
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        try:
            response = self.session.get(
                f"{self.config.base_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [m.get("name", "") for m in models]
            return []
        except Exception as e:
            self.logger.error(f"Failed to get models: {e}")
            return []
    
    def close(self):
        """Close session"""
        self.session.close()


# Singleton instance
_llm_service_instance = None

def get_llm_service(config: Optional[LLMConfig] = None) -> LLMService:
    """Get or create LLM service singleton"""
    global _llm_service_instance
    if _llm_service_instance is None:
        _llm_service_instance = LLMService(config)
    return _llm_service_instance
