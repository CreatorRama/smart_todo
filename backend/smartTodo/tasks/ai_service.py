# ai_service.py - Fixed version with error handling improvements

import requests
import json
import time
import logging
from typing import Dict, List, Optional, Union
from django.conf import settings
from django.utils import timezone
from pybreaker import CircuitBreaker
from .models import ContextEntry, Task, AIProcessingLog

logger = logging.getLogger(__name__)

# Circuit breaker for AI service with adjusted settings
ai_breaker = CircuitBreaker(fail_max=3, reset_timeout=60, exclude=[ConnectionError, requests.exceptions.Timeout])


class LMStudioClient:
    """Client for interacting with LM Studio API"""

    def __init__(self):
        self.base_url = getattr(settings, 'LM_STUDIO_BASE_URL', 'http://192.168.51.161:1234')
        self.model = getattr(settings, 'LM_STUDIO_MODEL', 'local-model')
        self.timeout = getattr(settings, 'LM_STUDIO_TIMEOUT', 45)  # Increased timeout
        self.max_retries = 3
        self.retry_delay = 2  # Increased delay

    def _make_request(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> Optional[str]:
        """Make request to LM Studio API with improved retry logic"""
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an AI assistant specialized in task management and productivity. Always respond with valid JSON when requested."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        last_error = None
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Making request to LM Studio (attempt {attempt + 1}/{self.max_retries})")
                
                response = requests.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )

                response.raise_for_status()
                result = response.json()
                
                # Validate response structure
                if 'choices' not in result or not result['choices']:
                    raise ValueError("Invalid response structure: no choices")
                
                if 'message' not in result['choices'][0] or 'content' not in result['choices'][0]['message']:
                    raise ValueError("Invalid response structure: no message content")
                
                content = result['choices'][0]['message']['content'].strip()
                logger.info("Successfully received response from LM Studio")
                return content

            except requests.exceptions.Timeout as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} timed out after {self.timeout}s")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                    
            except requests.exceptions.ConnectionError as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: Connection error - {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: Request error - {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    
            except (KeyError, json.JSONDecodeError, ValueError) as e:
                last_error = e
                logger.error(f"Response parsing error: {str(e)}")
                break  # Don't retry parsing errors

        logger.error(f"All retries failed. Last error: {str(last_error)}")
        return None


class AITaskManager:
    """Main class for AI-powered task management features"""

    def __init__(self):
        self.client = LMStudioClient()
        self.default_timeout = 30
        self.max_fallback_priority_score = 0.8

    def _log_processing(self, processing_type: str, input_data: dict, output_data: dict,
                        processing_time: int, success: bool, error_message: str = None):
        """Log AI processing for monitoring and debugging"""
        try:
            AIProcessingLog.objects.create(
                processing_type=processing_type,
                input_data=input_data,
                output_data=output_data,
                processing_time_ms=processing_time,
                model_used=self.client.model,
                success=success,
                error_message=error_message[:500] if error_message else None
            )
        except Exception as e:
            logger.error(f"Failed to log processing: {str(e)}")

    def _extract_json_from_response(self, response: str) -> dict:
        """Try to extract JSON from potentially messy response"""
        if not response:
            return {"error": "Empty response", "raw_response": response}
            
        try:
            # First try to parse directly
            return json.loads(response)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON substring
            try:
                # Find the first { and last }
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    return json.loads(json_str)
            except Exception as e:
                logger.warning(f"Failed to extract JSON: {str(e)}")
                
        return {"error": "Failed to parse JSON response", "raw_response": response}

    @ai_breaker
    def analyze_context(self, context_entries: List[ContextEntry]) -> Dict:
        """Analyze daily context entries to extract insights"""
        start_time = time.time()
        processing_id = f"ctx_{time.time()}"
        logger.info(f"[{processing_id}] Starting context analysis for {len(context_entries)} entries")

        try:
            if not context_entries:
                return {
                    "extracted_tasks": [],
                    "urgency_indicators": [],
                    "mentioned_deadlines": [],
                    "priority_signals": {"high": [], "medium": [], "low": []},
                    "context_summary": "No context provided",
                    "workload_assessment": "light",
                    "key_themes": []
                }

            # Prepare context text with better formatting
            context_text = "\n".join(
                f"[{entry.source_type.upper()} {entry.timestamp.strftime('%Y-%m-%d %H:%M')}] {entry.content[:500]}"
                for entry in context_entries
            )

            prompt = f"""
            Analyze this context and extract task insights. Respond ONLY with valid JSON in the exact format shown:
            
            Context:
            {context_text}
            
            {{
                "extracted_tasks": ["task1", "task2"],
                "urgency_indicators": ["urgent phrase1", "urgent phrase2"],
                "mentioned_deadlines": [{{"task": "description", "deadline": "2025-08-18T10:00:00", "source": "whatsapp"}}],
                "priority_signals": {{"high": ["urgent", "asap"], "medium": ["soon"], "low": ["later"]}},
                "context_summary": "brief summary of context",
                "workload_assessment": "light",
                "key_themes": ["theme1", "theme2"]
            }}
            """

            # Make API request
            response = self.client._make_request(prompt, max_tokens=2000, temperature=0.3)
            if not response:
                raise ValueError("No response from AI model")

            # Parse response
            result = self._extract_json_from_response(response)

            # Validate and set defaults for required fields
            required_fields = {
                "extracted_tasks": [],
                "urgency_indicators": [],
                "mentioned_deadlines": [],
                "priority_signals": {"high": [], "medium": [], "low": []},
                "context_summary": "Analysis completed",
                "workload_assessment": "moderate",
                "key_themes": []
            }

            for field, default in required_fields.items():
                if field not in result or result[field] is None:
                    result[field] = default

            # Log successful processing
            processing_time = int((time.time() - start_time) * 1000)
            self._log_processing(
                'context_analysis',
                {'num_entries': len(context_entries)},
                result,
                processing_time,
                True
            )

            logger.info(f"[{processing_id}] Completed successfully in {processing_time}ms")
            return result

        except Exception as e:
            error_result = {
                "error": str(e),
                "extracted_tasks": [],
                "urgency_indicators": [],
                "mentioned_deadlines": [],
                "priority_signals": {"high": [], "medium": [], "low": []},
                "context_summary": "Analysis failed - using fallback",
                "workload_assessment": "moderate",
                "key_themes": []
            }
            processing_time = int((time.time() - start_time) * 1000)
            self._log_processing(
                'context_analysis',
                {'num_entries': len(context_entries)},
                error_result,
                processing_time,
                False,
                str(e)
            )
            logger.error(f"[{processing_id}] Failed after {processing_time}ms: {str(e)}")
            return error_result

    def _get_safe_category_name(self, category) -> str:
        """Safely get category name handling both objects and None"""
        if category is None:
            return "uncategorized"
        
        # If it's already a string, return it
        if isinstance(category, str):
            return category
            
        # If it's an object with a name attribute
        if hasattr(category, 'name'):
            return str(category.name)
            
        # If it's a dict with name key
        if isinstance(category, dict) and 'name' in category:
            return str(category['name'])
            
        # Fallback
        return "uncategorized"

    @ai_breaker
    def prioritize_task(self, task: Union[Task, object], context_data: Dict = None, current_tasks: List[Task] = None) -> Dict:
        """Calculate priority score and suggestions for a task"""
        start_time = time.time()
        processing_id = f"pri_{getattr(task, 'id', 'temp')}_{time.time()}"
        logger.info(f"[{processing_id}] Starting prioritization for task")

        try:
            # Safely extract task information
            task_info = {
                "title": getattr(task, 'title', ''),
                "description": getattr(task, 'description', '') or '',
                "category": self._get_safe_category_name(getattr(task, 'category', None)),
                "current_priority": getattr(task, 'priority', 'medium'),
                "deadline": getattr(task, 'deadline', None),
                "estimated_duration": getattr(task, 'estimated_duration', None),
                "status": getattr(task, 'status', 'pending')
            }

            # Convert deadline to string if it exists
            if task_info["deadline"]:
                try:
                    if hasattr(task_info["deadline"], 'isoformat'):
                        task_info["deadline"] = task_info["deadline"].isoformat()
                    else:
                        task_info["deadline"] = str(task_info["deadline"])
                except Exception:
                    task_info["deadline"] = None

            # Prepare context summary
            context_summary = ""
            if context_data and isinstance(context_data, dict):
                context_summary = (
                    f"Context Summary: {context_data.get('context_summary', 'No context')}\n"
                    f"Workload: {context_data.get('workload_assessment', 'moderate')}\n"
                    f"Urgency Indicators: {len(context_data.get('urgency_indicators', []))}"
                )

            # Prepare current tasks info
            task_load_info = ""
            if current_tasks:
                try:
                    pending = sum(1 for t in current_tasks if getattr(t, 'status', '') == 'pending')
                    in_progress = sum(1 for t in current_tasks if getattr(t, 'status', '') == 'in_progress')
                    task_load_info = f"Current load: {pending} pending, {in_progress} in progress tasks"
                except Exception as e:
                    logger.warning(f"Error calculating task load: {str(e)}")
                    task_load_info = "Task load calculation failed"

            prompt = f"""
            Analyze this task and provide prioritization recommendations. Respond ONLY with valid JSON:
            
            Task:
            {json.dumps(task_info, indent=2)}
            
            {context_summary}
            {task_load_info}
            
            {{
                "priority_score": 0.5,
                "suggested_priority": "medium",
                "reasoning": "detailed explanation of priority decision",
                "urgency_factors": ["factor1", "factor2"],
                "suggested_deadline": null,
                "estimated_duration_refined": null,
                "context_relevance": "how context affects this task priority",
                "recommended_actions": ["action1", "action2"]
            }}
            """

            # Make API request
            response = self.client._make_request(prompt, max_tokens=1500, temperature=0.3)
            if not response:
                raise ValueError("No response from AI model")

            # Parse response
            result = self._extract_json_from_response(response)

            # Validate and normalize priority score
            try:
                raw_score = result.get('priority_score', 0.5)
                if isinstance(raw_score, (int, float)):
                    result['priority_score'] = max(0.0, min(1.0, float(raw_score)))
                else:
                    result['priority_score'] = 0.5
            except (TypeError, ValueError):
                result['priority_score'] = 0.5

            # Ensure required fields exist
            defaults = {
                "suggested_priority": task_info.get("current_priority", "medium"),
                "reasoning": "Priority analysis completed",
                "urgency_factors": [],
                "suggested_deadline": task_info.get("deadline"),
                "estimated_duration_refined": task_info.get("estimated_duration"),
                "context_relevance": "Context considered in priority calculation",
                "recommended_actions": []
            }

            for field, default in defaults.items():
                if field not in result or result[field] is None:
                    result[field] = default

            # Log successful processing
            processing_time = int((time.time() - start_time) * 1000)
            self._log_processing(
                'task_prioritization',
                task_info,
                result,
                processing_time,
                True
            )

            logger.info(f"[{processing_id}] Completed successfully in {processing_time}ms")
            return result

        except Exception as e:
            # Fallback to non-AI prioritization
            result = self._fallback_prioritization(task)
            processing_time = int((time.time() - start_time) * 1000)
            self._log_processing(
                'task_prioritization',
                {"task_title": getattr(task, 'title', 'Unknown')},
                result,
                processing_time,
                False,
                str(e)
            )
            logger.error(f"[{processing_id}] Failed after {processing_time}ms: {str(e)}")
            return result

    def _fallback_prioritization(self, task) -> Dict:
        """Fallback priority calculation when AI is unavailable"""
        try:
            # Base score from explicit priority
            priority_scores = {
                'low': 0.3,
                'medium': 0.5,
                'high': 0.7,
                'urgent': 0.9
            }
            
            current_priority = getattr(task, 'priority', 'medium')
            score = priority_scores.get(current_priority, 0.5)

            # Adjust based on deadline
            deadline = getattr(task, 'deadline', None)
            if deadline:
                try:
                    now = timezone.now()
                    if hasattr(deadline, 'date'):  # datetime object
                        if timezone.is_naive(deadline):
                            deadline = timezone.make_aware(deadline)
                        days_until = (deadline - now).days
                    else:  # string or other format
                        days_until = 1  # Default assumption

                    if days_until <= 0:
                        score = min(score + 0.3, self.max_fallback_priority_score)
                    elif days_until <= 2:
                        score = min(score + 0.2, self.max_fallback_priority_score)
                    elif days_until <= 7:
                        score = min(score + 0.1, self.max_fallback_priority_score)
                except Exception as e:
                    logger.warning(f"Error processing deadline in fallback: {str(e)}")

            return {
                "priority_score": score,
                "suggested_priority": current_priority,
                "reasoning": "Fallback calculation based on priority and deadline",
                "urgency_factors": ["Fallback mode"],
                "suggested_deadline": str(deadline) if deadline else None,
                "estimated_duration_refined": getattr(task, 'estimated_duration', None),
                "context_relevance": "Fallback mode - no context analysis",
                "recommended_actions": ["Review task manually"],
                "is_fallback": True
            }
        except Exception as e:
            logger.error(f"Even fallback failed: {str(e)}")
            return {
                "priority_score": 0.5,
                "suggested_priority": "medium",
                "reasoning": "Emergency fallback - minimal processing",
                "urgency_factors": ["Emergency fallback"],
                "suggested_deadline": None,
                "estimated_duration_refined": None,
                "context_relevance": "Emergency fallback mode",
                "recommended_actions": [],
                "is_fallback": True,
                "error": str(e)
            }

    @ai_breaker
    def enhance_task(self, task_data: Dict, context_data: Dict = None) -> Dict:
        """Enhance task with AI-powered suggestions"""
        start_time = time.time()
        processing_id = f"enh_{time.time()}"
        logger.info(f"[{processing_id}] Starting task enhancement")

        try:
            # Validate task_data
            if not isinstance(task_data, dict):
                raise ValueError("task_data must be a dictionary")

            # Prepare context info
            context_info = ""
            if context_data and isinstance(context_data, dict):
                context_info = (
                    f"Available Context:\n"
                    f"Summary: {context_data.get('context_summary', 'None')}\n"
                    f"Themes: {', '.join(context_data.get('key_themes', []))}"
                )

            prompt = f"""
            Enhance this task with better descriptions and metadata. Respond ONLY with valid JSON:
            
            Task Data:
            {json.dumps(task_data, indent=2)}
            
            {context_info}
            
            {{
                "enhanced_description": "improved and detailed description",
                "suggested_tags": ["tag1", "tag2", "tag3"],
                "suggested_category": "appropriate category name",
                "breakdown_suggestions": ["subtask1", "subtask2"],
                "resource_suggestions": ["resource1", "resource2"],
                "difficulty_assessment": "medium",
                "context_connections": "how this task relates to provided context"
            }}
            """

            # Make API request
            response = self.client._make_request(prompt, max_tokens=1500, temperature=0.4)
            if not response:
                raise ValueError("No response from AI model")

            # Parse response
            result = self._extract_json_from_response(response)

            # Ensure required fields with sensible defaults
            defaults = {
                "enhanced_description": task_data.get("description", task_data.get("title", "")),
                "suggested_tags": [],
                "suggested_category": "general",
                "breakdown_suggestions": [],
                "resource_suggestions": [],
                "difficulty_assessment": "medium",
                "context_connections": "No specific context connections identified"
            }

            for field, default in defaults.items():
                if field not in result or result[field] is None:
                    result[field] = default

            # Log successful processing
            processing_time = int((time.time() - start_time) * 1000)
            self._log_processing(
                'task_enhancement',
                task_data,
                result,
                processing_time,
                True
            )

            logger.info(f"[{processing_id}] Completed successfully in {processing_time}ms")
            return result

        except Exception as e:
            # Fallback to simple enhancement
            result = self._fallback_enhancement(task_data)
            processing_time = int((time.time() - start_time) * 1000)
            self._log_processing(
                'task_enhancement',
                task_data,
                result,
                processing_time,
                False,
                str(e)
            )
            logger.error(f"[{processing_id}] Failed after {processing_time}ms: {str(e)}")
            return result

    def _fallback_enhancement(self, task_data: Dict) -> Dict:
        """Fallback task enhancement when AI is unavailable"""
        try:
            title = task_data.get("title", "")
            description = task_data.get("description", "")

            # Simple tag extraction from title
            title_lower = title.lower()
            suggested_tags = []

            tag_keywords = {
                "meeting": ["meeting", "call", "discuss", "conference"],
                "research": ["research", "study", "analyze", "investigate"],
                "coding": ["code", "program", "develop", "implement"],
                "urgent": ["urgent", "asap", "immediately", "priority"],
                "review": ["review", "check", "verify", "audit"],
                "planning": ["plan", "schedule", "organize", "prepare"]
            }

            for tag, keywords in tag_keywords.items():
                if any(kw in title_lower for kw in keywords):
                    suggested_tags.append(tag)

            return {
                "enhanced_description": description or f"Complete task: {title}",
                "suggested_tags": suggested_tags[:3],  # Limit to 3 tags
                "suggested_category": "general",
                "breakdown_suggestions": [],
                "resource_suggestions": [],
                "difficulty_assessment": "medium",
                "context_connections": "Fallback mode - no context analysis available",
                "is_fallback": True
            }
        except Exception as e:
            logger.error(f"Fallback enhancement failed: {str(e)}")
            return {
                "enhanced_description": task_data.get("title", "Task"),
                "suggested_tags": [],
                "suggested_category": "general",
                "breakdown_suggestions": [],
                "resource_suggestions": [],
                "difficulty_assessment": "medium",
                "context_connections": "Fallback failed",
                "is_fallback": True,
                "error": str(e)
            }

    def get_task_recommendations(self, task_data: Dict, context_entries: List[ContextEntry] = None,
                                 user_preferences: Dict = None, current_task_load: int = 0) -> Dict:
        """Get comprehensive AI recommendations for a task"""
        start_time = time.time()
        logger.info("Starting comprehensive task recommendation generation")

        try:
            # Validate inputs
            if not isinstance(task_data, dict):
                raise ValueError("task_data must be a dictionary")

            # Analyze context if provided
            context_analysis = {}
            if context_entries:
                logger.info(f"Analyzing {len(context_entries)} context entries")
                context_analysis = self.analyze_context(context_entries)

            # Create temporary task object for prioritization
            class TempTask:
                def __init__(self, **kwargs):
                    for k, v in kwargs.items():
                        setattr(self, k, v)

            # Handle deadline conversion
            deadline = task_data.get("deadline")
            if deadline and isinstance(deadline, str):
                try:
                    from django.utils.dateparse import parse_datetime
                    deadline = parse_datetime(deadline)
                except Exception:
                    deadline = None

            temp_task = TempTask(
                id="temp",
                title=task_data.get("title", ""),
                description=task_data.get("description", ""),
                category=task_data.get("category"),
                priority=task_data.get("priority", "medium"),
                deadline=deadline,
                estimated_duration=task_data.get("estimated_duration"),
                status="pending"
            )

            # Get all recommendations
            logger.info("Getting prioritization recommendations")
            prioritization = self.prioritize_task(temp_task, context_analysis)
            
            logger.info("Getting enhancement recommendations")
            enhancement = self.enhance_task(task_data, context_analysis)

            # Prepare final response
            result = {
                "priority_score": prioritization.get("priority_score", 0.5),
                "suggested_priority": prioritization.get("suggested_priority", "medium"),
                "enhanced_description": enhancement.get("enhanced_description", ""),
                "suggested_tags": enhancement.get("suggested_tags", []),
                "suggested_category": enhancement.get("suggested_category", "general"),
                "context_analysis": {
                    "summary": context_analysis.get("context_summary", "No context analyzed"),
                    "urgency_indicators": context_analysis.get("urgency_indicators", []),
                    "themes": context_analysis.get("key_themes", [])
                },
                "reasoning": (
                    f"Priority: {prioritization.get('reasoning', 'N/A')} | "
                    f"Enhancement: {enhancement.get('context_connections', 'N/A')}"
                ),
                "success": True
            }

            # Add optional fields if available
            if prioritization.get("suggested_deadline"):
                result["suggested_deadline"] = prioritization["suggested_deadline"]

            processing_time = int((time.time() - start_time) * 1000)
            logger.info(f"Task recommendations completed successfully in {processing_time}ms")
            
            return result

        except Exception as e:
            logger.error(f"Failed to get task recommendations: {str(e)}", exc_info=True)
            return {
                "priority_score": 0.5,
                "suggested_priority": "medium",
                "enhanced_description": task_data.get("description", task_data.get("title", "")),
                "suggested_tags": [],
                "suggested_category": "general",
                "context_analysis": {
                    "summary": "Analysis failed",
                    "urgency_indicators": [],
                    "themes": []
                },
                "reasoning": f"Fallback due to error: {str(e)}",
                "error": str(e),
                "success": False,
                "is_fallback": True
            }