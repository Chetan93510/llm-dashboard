"""
LLM Observability Dashboard - Groq LLM Service

This module provides a wrapper around the Groq API that automatically
logs all LLM requests to the database.
"""

import time
import uuid
import logging
from decimal import Decimal
from typing import Optional, Dict, Any

import requests
from django.conf import settings
from django.utils import timezone

from .models import LLMRequestLog

logger = logging.getLogger('llm')


class GroqAPIError(Exception):
    """Custom exception for Groq API errors."""
    
    def __init__(self, message: str, error_type: str = 'provider_error'):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)


class GroqLLMService:
    """
    Service wrapper for Groq LLM API with automatic logging.
    
    This service handles all communication with the Groq API and
    automatically logs every request to the database for observability.
    """
    
    def __init__(self):
        """Initialize the Groq service with API credentials from settings."""
        self.api_key = settings.GROQ_API_KEY
        self.base_url = settings.GROQ_API_BASE_URL
        self.default_model = settings.GROQ_DEFAULT_MODEL
        self.token_pricing = settings.LLM_TOKEN_PRICING
        
        if not self.api_key:
            logger.warning("GROQ_API_KEY not set. LLM calls will fail.")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
    
    def _calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> Decimal:
        """
        Calculate estimated cost based on token usage.
        
        Args:
            model: The model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            
        Returns:
            Estimated cost in USD
        """
        pricing = self.token_pricing.get(model, self.token_pricing['default'])
        
        # Prices are per 1M tokens
        input_cost = (prompt_tokens / 1_000_000) * pricing['input']
        output_cost = (completion_tokens / 1_000_000) * pricing['output']
        
        return Decimal(str(round(input_cost + output_cost, 6)))
    
    def _map_error_type(self, status_code: int, error_message: str) -> str:
        """Map HTTP status code and error message to error type."""
        if status_code == 401:
            return 'authentication'
        elif status_code == 429:
            return 'rate_limit'
        elif status_code == 408 or 'timeout' in error_message.lower():
            return 'timeout'
        elif status_code == 400:
            return 'invalid_prompt'
        elif status_code >= 500:
            return 'provider_error'
        else:
            return 'unknown'
    
    def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        user_id: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send a completion request to Groq and log the result.
        
        Args:
            prompt: The prompt to send to the LLM
            model: The model to use (defaults to settings.GROQ_DEFAULT_MODEL)
            user_id: Optional user identifier for tracking
            max_tokens: Maximum tokens in the response
            temperature: Sampling temperature
            metadata: Optional additional metadata to store
            
        Returns:
            Dictionary containing the response and metadata
            
        Raises:
            GroqAPIError: If the API request fails
        """
        model = model or self.default_model
        request_id = uuid.uuid4()
        start_time = time.time()
        
        # Initialize log entry values
        log_data = {
            'request_id': request_id,
            'user_id': user_id,
            'model_name': model,
            'prompt_text': prompt,
            'response_text': None,
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0,
            'latency_ms': 0,
            'cost_estimate': Decimal('0'),
            'status': 'success',
            'error_type': 'none',
            'error_message': None,
            'metadata': metadata or {},
        }
        
        try:
            # Validate API key
            if not self.api_key:
                raise GroqAPIError(
                    "GROQ_API_KEY not configured",
                    error_type='authentication'
                )
            
            # Prepare the request
            url = f"{self.base_url}/chat/completions"
            payload = {
                'model': model,
                'messages': [
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': max_tokens,
                'temperature': temperature,
            }
            
            # Make the API request
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=60
            )
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            log_data['latency_ms'] = latency_ms
            
            # Handle errors
            if response.status_code != 200:
                error_message = response.text
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', error_message)
                except:
                    pass
                
                error_type = self._map_error_type(response.status_code, error_message)
                log_data['status'] = 'error'
                log_data['error_type'] = error_type
                log_data['error_message'] = error_message
                
                # Log the failed request
                self._save_log(log_data)
                
                raise GroqAPIError(error_message, error_type=error_type)
            
            # Parse successful response
            data = response.json()
            
            # Extract response content
            response_text = data['choices'][0]['message']['content']
            usage = data.get('usage', {})
            
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            total_tokens = usage.get('total_tokens', prompt_tokens + completion_tokens)
            
            # Calculate cost
            cost = self._calculate_cost(model or self.default_model, prompt_tokens, completion_tokens)
            
            # Update log data
            log_data.update({
                'response_text': response_text,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens,
                'cost_estimate': cost,
            })
            
            # Log the successful request
            self._save_log(log_data)
            
            logger.info(
                f"LLM Request completed: model={model}, "
                f"tokens={total_tokens}, latency={latency_ms}ms, cost=${cost}"
            )
            
            return {
                'request_id': str(request_id),
                'response': response_text,
                'model': model,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens,
                'latency_ms': latency_ms,
                'cost_estimate': cost,
            }
            
        except requests.exceptions.Timeout:
            latency_ms = int((time.time() - start_time) * 1000)
            log_data['latency_ms'] = latency_ms
            log_data['status'] = 'error'
            log_data['error_type'] = 'timeout'
            log_data['error_message'] = 'Request timed out'
            
            self._save_log(log_data)
            logger.error(f"LLM Request timeout: model={model}")
            
            raise GroqAPIError("Request timed out", error_type='timeout')
            
        except requests.exceptions.RequestException as e:
            latency_ms = int((time.time() - start_time) * 1000)
            log_data['latency_ms'] = latency_ms
            log_data['status'] = 'error'
            log_data['error_type'] = 'network'
            log_data['error_message'] = str(e)
            
            self._save_log(log_data)
            logger.error(f"LLM Request network error: {e}")
            
            raise GroqAPIError(str(e), error_type='network')
            
        except GroqAPIError:
            # Re-raise our custom errors (already logged)
            raise
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            log_data['latency_ms'] = latency_ms
            log_data['status'] = 'error'
            log_data['error_type'] = 'unknown'
            log_data['error_message'] = str(e)
            
            self._save_log(log_data)
            logger.exception(f"LLM Request unexpected error: {e}")
            
            raise GroqAPIError(str(e), error_type='unknown')
    
    def _save_log(self, log_data: Dict[str, Any]) -> Optional[LLMRequestLog]:
        """
        Save the request log to database.
        
        Args:
            log_data: Dictionary containing all log fields
            
        Returns:
            Created LLMRequestLog instance, or None if saving failed
        """
        try:
            log = LLMRequestLog.objects.create(**log_data)
            return log
        except Exception as e:
            logger.error(f"Failed to save LLM request log: {e}")
            # Don't raise - logging should not break the main flow
            return None


# Create a singleton instance for easy access
groq_service = GroqLLMService()
