import requests
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from django.conf import settings
from django.utils import timezone
from pybreaker import CircuitBreaker
from .models import ContextEntry, Task, AIProcessingLog

logger = logging.getLogger(__name__)

# Circuit breaker for AI service
ai_breaker = CircuitBreaker(fail_max=3, reset_timeout=60)

class LMStudioClient:
    """Client for interacting with LM Studio API"""
    
    def __init__(self):
        self.base_url = settings.LM_STUDIO_BASE_URL
        self.model = settings.LM_STUDIO_MODEL
        self.timeout = settings.LM_STUDIO_TIMEOUT
        self.max_retries = 3
        self.retry_delay = 1
        
    def _make_request(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> Optional[str]:
        """Make request to LM Studio API with retry logic"""
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an AI assistant specialized in task management and productivity."
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
                response = requests.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
                
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
            except (KeyError, json.JSONDecodeError) as e:
                last_error = e
                logger.error(f"Response parsing error: {str(e)}")
                break
        
        logger.error(f"All retries failed. Last error: {str(last_error)}")
        return None

class AITaskManager:
    """Main class for AI-powered task management features"""
    
    def __init__(self):
        self.client = LMStudioClient()
        self.default_timeout = 30  # seconds
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
        try:
            # First try to parse directly
            return json.loads(response)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON substring
            try:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    return json.loads(response[json_start:json_end])
            except Exception:
                pass
        return {"error": "Failed to parse JSON response", "raw_response": response}

    @ai_breaker
    def analyze_context(self, context_entries: List[ContextEntry]) -> Dict:
        """Analyze daily context entries to extract insights"""
        start_time = time.time()
        processing_id = f"ctx_{time.time()}"
        logger.info(f"[{processing_id}] Starting context analysis")
        
        try:
            # Prepare context text
            context_text = "\n".join(
                f"[{entry.source_type.upper()} {entry.timestamp}] {entry.content}"
                for entry in context_entries
            )
            
            prompt = f"""
            Analyze this context and extract task insights (respond in JSON):
            
            Context:
            {context_text}
            
            Required JSON format:
            {{
                "extracted_tasks": ["task1", "task2"],
                "urgency_indicators": ["urgent phrase1"],
                "mentioned_deadlines": [{{"task": "...", "deadline": "ISO date", "source": "..."}}],
                "priority_signals": {{"high": [...], "medium": [...], "low": [...]}},
                "context_summary": "brief summary",
                "workload_assessment": "light/moderate/heavy",
                "key_themes": ["theme1", "theme2"]
            }}
            """
            
            # Make API request
            response = self.client._make_request(prompt, max_tokens=2000)
            if not response:
                raise ValueError("No response from AI model")
            
            # Parse response
            result = self._extract_json_from_response(response)
            
            # Validate minimum required fields
            if not all(k in result for k in ["extracted_tasks", "context_summary"]):
                raise ValueError("Invalid response format from AI")
            
            # Log successful processing
            processing_time = int((time.time() - start_time) * 1000)
            self._log_processing(
                'context_analysis',
                {'num_entries': len(context_entries)},
                result,
                processing_time,
                True
            )
            
            logger.info(f"[{processing_id}] Completed in {processing_time}ms")
            return result
            
        except Exception as e:
            error_result = {
                "error": str(e),
                "extracted_tasks": [],
                "context_summary": "Analysis failed"
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

    @ai_breaker
    def prioritize_task(self, task: Task, context_data: Dict = None, current_tasks: List[Task] = None) -> Dict:
        """Calculate priority score and suggestions for a task"""
        start_time = time.time()
        processing_id = f"pri_{task.id}_{time.time()}"
        logger.info(f"[{processing_id}] Starting prioritization for task {task.id}")
        
        try:
            # Prepare task context with timezone-aware datetimes
            task_info = {
                "title": task.title,
                "description": task.description or "",
                "category": task.category.name if task.category else "uncategorized",
                "current_priority": task.priority,
                "deadline": task.deadline.isoformat() if task.deadline else None,
                "estimated_duration": task.estimated_duration,
                "status": task.status
            }
            
            # Prepare context summary
            context_summary = ""
            if context_data:
                context_summary = (
                    f"Context Summary: {context_data.get('context_summary', 'No context')}\n"
                    f"Workload: {context_data.get('workload_assessment', 'moderate')}\n"
                    f"Urgency Indicators: {len(context_data.get('urgency_indicators', []))}"
                )
            
            # Prepare current tasks info
            task_load_info = ""
            if current_tasks:
                pending = sum(1 for t in current_tasks if t.status == 'pending')
                in_progress = sum(1 for t in current_tasks if t.status == 'in_progress')
                task_load_info = f"Current load: {pending} pending, {in_progress} in progress tasks"
            
            prompt = f"""
            Analyze this task and provide prioritization recommendations (respond in JSON):
            
            Task:
            {json.dumps(task_info, indent=2)}
            
            {context_summary}
            {task_load_info}
            
            Required JSON response:
            {{
                "priority_score": 0.0-1.0,
                "suggested_priority": "low/medium/high/urgent",
                "reasoning": "detailed explanation",
                "urgency_factors": ["factor1", "factor2"],
                "suggested_deadline": "ISO datetime or null",
                "estimated_duration_refined": "minutes or null",
                "context_relevance": "how context affects priority",
                "recommended_actions": ["action1", "action2"]
            }}
            """
            
            # Make API request
            response = self.client._make_request(prompt, max_tokens=1500)
            if not response:
                raise ValueError("No response from AI model")
            
            # Parse response
            result = self._extract_json_from_response(response)
            
            # Validate and normalize priority score
            try:
                raw_score = float(result.get('priority_score', 0.5))
                result['priority_score'] = max(0.0, min(1.0, raw_score))
            except (TypeError, ValueError):
                result['priority_score'] = 0.5
                result['score_error'] = "Invalid priority score"
            
            # Log successful processing
            processing_time = int((time.time() - start_time) * 1000)
            self._log_processing(
                'task_prioritization',
                task_info,
                result,
                processing_time,
                True
            )
            
            logger.info(f"[{processing_id}] Completed in {processing_time}ms")
            return result
            
        except Exception as e:
            # Fallback to non-AI prioritization
            result = self._fallback_prioritization(task)
            processing_time = int((time.time() - start_time) * 1000)
            self._log_processing(
                'task_prioritization',
                {"task_id": task.id, "title": task.title},
                result,
                processing_time,
                False,
                str(e)
            )
            logger.error(f"[{processing_id}] Failed after {processing_time}ms: {str(e)}")
            return result

    def _fallback_prioritization(self, task: Task) -> Dict:
        """Fallback priority calculation when AI is unavailable"""
        # Base score from explicit priority
        priority_scores = {
            'low': 0.3,
            'medium': 0.5,
            'high': 0.7,
            'urgent': 0.9
        }
        score = priority_scores.get(task.priority, 0.5)
        
        # Adjust based on deadline
        if task.deadline:
            now = timezone.now()
            if timezone.is_naive(task.deadline):
                deadline = timezone.make_aware(task.deadline)
            else:
                deadline = task.deadline
            
            days_until = (deadline - now).days
            if days_until <= 0:
                score = min(score + 0.3, self.max_fallback_priority_score)
            elif days_until <= 2:
                score = min(score + 0.2, self.max_fallback_priority_score)
            elif days_until <= 7:
                score = min(score + 0.1, self.max_fallback_priority_score)
        
        return {
            "priority_score": score,
            "suggested_priority": task.priority,
            "reasoning": "Fallback calculation based on priority and deadline",
            "urgency_factors": ["Fallback mode"],
            "suggested_deadline": task.deadline.isoformat() if task.deadline else None,
            "estimated_duration_refined": task.estimated_duration,
            "context_relevance": "Fallback mode - context not analyzed",
            "is_fallback": True
        }

    @ai_breaker
    def enhance_task(self, task_data: Dict, context_data: Dict = None) -> Dict:
        """Enhance task with AI-powered suggestions"""
        start_time = time.time()
        processing_id = f"enh_{time.time()}"
        logger.info(f"[{processing_id}] Starting task enhancement")
        
        try:
            # Prepare context info
            context_info = ""
            if context_data:
                context_info = (
                    f"Available Context:\n"
                    f"Summary: {context_data.get('context_summary', 'None')}\n"
                    f"Themes: {', '.join(context_data.get('key_themes', []))}"
                )
            
            prompt = f"""
            Enhance this task with better descriptions and metadata (respond in JSON):
            
            Task Data:
            {json.dumps(task_data, indent=2)}
            
            {context_info}
            
            Required JSON response:
            {{
                "enhanced_description": "improved description",
                "suggested_tags": ["tag1", "tag2"],
                "suggested_category": "category name",
                "breakdown_suggestions": ["subtask1", "subtask2"],
                "resource_suggestions": ["resource1", "resource2"],
                "difficulty_assessment": "easy/medium/hard",
                "context_connections": "how this relates to context"
            }}
            """
            
            # Make API request
            response = self.client._make_request(prompt, max_tokens=1500)
            if not response:
                raise ValueError("No response from AI model")
            
            # Parse response
            result = self._extract_json_from_response(response)
            
            # Ensure required fields
            if "enhanced_description" not in result:
                result["enhanced_description"] = task_data.get("description", "")
            
            # Log successful processing
            processing_time = int((time.time() - start_time) * 1000)
            self._log_processing(
                'task_enhancement',
                task_data,
                result,
                processing_time,
                True
            )
            
            logger.info(f"[{processing_id}] Completed in {processing_time}ms")
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
        title = task_data.get("title", "")
        description = task_data.get("description", "")
        
        # Simple tag extraction from title
        title_lower = title.lower()
        suggested_tags = []
        
        tag_keywords = {
            "meeting": ["meeting", "call", "discuss"],
            "research": ["research", "study", "analyze"],
            "coding": ["code", "program", "develop"],
            "urgent": ["urgent", "asap", "immediately"]
        }
        
        for tag, keywords in tag_keywords.items():
            if any(kw in title_lower for kw in keywords):
                suggested_tags.append(tag)
        
        return {
            "enhanced_description": description or f"Complete: {title}",
            "suggested_tags": suggested_tags[:3],
            "suggested_category": "general",
            "breakdown_suggestions": [],
            "resource_suggestions": [],
            "difficulty_assessment": "medium",
            "context_connections": "Fallback mode - no context analysis",
            "is_fallback": True
        }

    def get_task_recommendations(self, task_data: Dict, context_entries: List[ContextEntry] = None,
                               user_preferences: Dict = None, current_task_load: int = 0) -> Dict:
        """Get comprehensive AI recommendations for a task"""
        start_time = time.time()
        
        try:
            # Analyze context if provided
            context_analysis = {}
            if context_entries:
                context_analysis = self.analyze_context(context_entries)
            
            # Create temporary task object for prioritization
            class TempTask:
                def __init__(self, **kwargs):
                    for k, v in kwargs.items():
                        setattr(self, k, v)
            
            temp_task = TempTask(
                id="temp",
                title=task_data.get("title", ""),
                description=task_data.get("description", ""),
                category=task_data.get("category"),
                priority=task_data.get("priority", "medium"),
                deadline=task_data.get("deadline"),
                estimated_duration=task_data.get("estimated_duration"),
                status="pending"
            )
            
            # Get all recommendations
            prioritization = self.prioritize_task(temp_task, context_analysis)
            enhancement = self.enhance_task(task_data, context_analysis)
            
            # Prepare final response
            result = {
                "priority_score": prioritization.get("priority_score", 0.5),
                "suggested_priority": prioritization.get("suggested_priority", "medium"),
                "enhanced_description": enhancement.get("enhanced_description", ""),
                "suggested_tags": enhancement.get("suggested_tags", []),
                "suggested_category": enhancement.get("suggested_category", ""),
                "context_analysis": {
                    "summary": context_analysis.get("context_summary", ""),
                    "urgency_indicators": context_analysis.get("urgency_indicators", []),
                    "themes": context_analysis.get("key_themes", [])
                },
                "reasoning": (
                    f"Priority: {prioritization.get('reasoning', '')} | "
                    f"Enhancement: {enhancement.get('context_connections', '')}"
                ),
                "success": True
            }
            
            # Add deadline if available
            if "suggested_deadline" in prioritization:
                result["suggested_deadline"] = prioritization["suggested_deadline"]
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get task recommendations: {str(e)}")
            return {
                "error": str(e),
                "success": False,
                "is_fallback": True
            }