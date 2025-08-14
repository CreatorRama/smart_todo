# tasks/ai_service.py
import requests
import json
import time
from datetime import datetime, timedelta
from django.conf import settings
from typing import Dict, List, Optional, Tuple
import logging
from .models import ContextEntry, Task, Category, AIProcessingLog

logger = logging.getLogger(__name__)

class LMStudioClient:
    def __init__(self):
        self.base_url = settings.LM_STUDIO_BASE_URL
        self.model = settings.LM_STUDIO_MODEL
        
    def _make_request(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> Optional[str]:
        """Make request to LM Studio API"""
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an AI assistant specialized in task management and productivity. Provide structured, actionable responses in JSON format when requested."
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
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                logger.error(f"LM Studio API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling LM Studio API: {str(e)}")
            return None

class AITaskManager:
    def __init__(self):
        self.client = LMStudioClient()
        
    def _log_processing(self, processing_type: str, input_data: dict, output_data: dict, 
                       processing_time: int, success: bool, error_message: str = None):
        """Log AI processing for monitoring"""
        AIProcessingLog.objects.create(
            processing_type=processing_type,
            input_data=input_data,
            output_data=output_data,
            processing_time_ms=processing_time,
            model_used=self.client.model,
            success=success,
            error_message=error_message
        )

    def analyze_context(self, context_entries: List[ContextEntry]) -> Dict:
        """Analyze daily context entries to extract insights"""
        start_time = time.time()
        
        context_text = ""
        for entry in context_entries:
            context_text += f"[{entry.source_type.upper()}] {entry.content}\n"
        
        prompt = f"""
        Analyze the following daily context and extract task-related insights:
        
        {context_text}
        
        Please provide a JSON response with the following structure:
        {{
            "extracted_tasks": ["task1", "task2", ...],
            "urgency_indicators": ["urgent phrase1", "urgent phrase2", ...],
            "mentioned_deadlines": [
                {{"task": "task description", "deadline": "date/time", "source": "email/whatsapp/etc"}}
            ],
            "priority_signals": {{"high": ["signal1"], "medium": ["signal2"], "low": ["signal3"]}},
            "context_summary": "brief summary of the overall context",
            "workload_assessment": "light/moderate/heavy"
        }}
        
        Focus on extracting actionable tasks, deadlines, and priority indicators.
        """
        
        try:
            response = self.client._make_request(prompt, max_tokens=1500)
            if response:
                # Try to parse JSON from response
                try:
                    # Extract JSON from response if it's wrapped in text
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    if json_start != -1 and json_end != -1:
                        json_str = response[json_start:json_end]
                        result = json.loads(json_str)
                    else:
                        result = {"error": "No valid JSON found in response"}
                except json.JSONDecodeError:
                    result = {"error": "Failed to parse JSON", "raw_response": response}
                
                processing_time = int((time.time() - start_time) * 1000)
                self._log_processing('context_analysis', {'context_entries': len(context_entries)}, 
                                   result, processing_time, True)
                return result
            else:
                error_result = {"error": "No response from AI model"}
                processing_time = int((time.time() - start_time) * 1000)
                self._log_processing('context_analysis', {'context_entries': len(context_entries)}, 
                                   error_result, processing_time, False, "No response from AI model")
                return error_result
                
        except Exception as e:
            error_result = {"error": str(e)}
            processing_time = int((time.time() - start_time) * 1000)
            self._log_processing('context_analysis', {'context_entries': len(context_entries)}, 
                               error_result, processing_time, False, str(e))
            return error_result

    def prioritize_task(self, task: Task, context_data: Dict = None, current_tasks: List[Task] = None) -> Dict:
        """Calculate priority score and suggestions for a task"""
        start_time = time.time()
        
        # Prepare task context
        task_info = {
            "title": task.title,
            "description": task.description or "",
            "category": task.category.name if task.category else "uncategorized",
            "current_priority": task.priority,
            "deadline": task.deadline.isoformat() if task.deadline else None,
            "estimated_duration": task.estimated_duration
        }
        
        # Add context information
        context_summary = ""
        if context_data:
            context_summary = f"Context: {context_data.get('context_summary', '')}\n"
            context_summary += f"Workload: {context_data.get('workload_assessment', '')}\n"
        
        # Add current task load
        task_load_info = ""
        if current_tasks:
            pending_tasks = len([t for t in current_tasks if t.status == 'pending'])
            in_progress_tasks = len([t for t in current_tasks if t.status == 'in_progress'])
            task_load_info = f"Current load: {pending_tasks} pending, {in_progress_tasks} in progress tasks"
        
        prompt = f"""
        Analyze this task and provide prioritization recommendations:
        
        Task Details:
        Title: {task_info['title']}
        Description: {task_info['description']}
        Category: {task_info['category']}
        Current Priority: {task_info['current_priority']}
        Deadline: {task_info['deadline']}
        Estimated Duration: {task_info['estimated_duration']} minutes
        
        {context_summary}
        {task_load_info}
        
        Provide a JSON response:
        {{
            "priority_score": 0.0-1.0,
            "suggested_priority": "low/medium/high/urgent",
            "reasoning": "explanation of priority decision",
            "urgency_factors": ["factor1", "factor2"],
            "suggested_deadline": "ISO datetime or null",
            "estimated_duration_refined": "minutes as integer or null",
            "context_relevance": "how context affects this task"
        }}
        
        Consider deadline proximity, task complexity, context urgency, and current workload.
        """
        
        try:
            response = self.client._make_request(prompt, max_tokens=1000)
            if response:
                try:
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    if json_start != -1 and json_end != -1:
                        json_str = response[json_start:json_end]
                        result = json.loads(json_str)
                    else:
                        result = self._fallback_prioritization(task)
                except json.JSONDecodeError:
                    result = self._fallback_prioritization(task)
                
                processing_time = int((time.time() - start_time) * 1000)
                self._log_processing('task_prioritization', task_info, result, processing_time, True)
                return result
            else:
                result = self._fallback_prioritization(task)
                processing_time = int((time.time() - start_time) * 1000)
                self._log_processing('task_prioritization', task_info, result, processing_time, False)
                return result
                
        except Exception as e:
            result = self._fallback_prioritization(task)
            processing_time = int((time.time() - start_time) * 1000)
            self._log_processing('task_prioritization', task_info, result, processing_time, False, str(e))
            return result

    def enhance_task(self, task_data: Dict, context_data: Dict = None) -> Dict:
        """Enhance task with AI-powered suggestions"""
        start_time = time.time()
        
        context_info = ""
        if context_data:
            context_info = f"Available Context: {context_data.get('context_summary', '')}"
        
        prompt = f"""
        Enhance this task with better descriptions, tags, and categorization:
        
        Task:
        Title: {task_data.get('title', '')}
        Description: {task_data.get('description', '')}
        Category: {task_data.get('category', '')}
        
        {context_info}
        
        Provide JSON response:
        {{
            "enhanced_description": "improved task description",
            "suggested_tags": ["tag1", "tag2", "tag3"],
            "suggested_category": "category name",
            "breakdown_suggestions": ["subtask1", "subtask2"],
            "resource_suggestions": ["resource1", "resource2"],
            "difficulty_assessment": "easy/medium/hard",
            "context_connections": "how this relates to current context"
        }}
        
        Make suggestions actionable and specific.
        """
        
        try:
            response = self.client._make_request(prompt, max_tokens=1200)
            if response:
                try:
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    if json_start != -1 and json_end != -1:
                        json_str = response[json_start:json_end]
                        result = json.loads(json_str)
                    else:
                        result = self._fallback_enhancement(task_data)
                except json.JSONDecodeError:
                    result = self._fallback_enhancement(task_data)
                
                processing_time = int((time.time() - start_time) * 1000)
                self._log_processing('task_enhancement', task_data, result, processing_time, True)
                return result
            else:
                result = self._fallback_enhancement(task_data)
                processing_time = int((time.time() - start_time) * 1000)
                self._log_processing('task_enhancement', task_data, result, processing_time, False)
                return result
                
        except Exception as e:
            result = self._fallback_enhancement(task_data)
            processing_time = int((time.time() - start_time) * 1000)
            self._log_processing('task_enhancement', task_data, result, processing_time, False, str(e))
            return result

    def suggest_deadline(self, task_data: Dict, context_data: Dict = None, current_workload: int = 0) -> Optional[datetime]:
        """Suggest realistic deadline for a task"""
        start_time = time.time()
        
        current_date = datetime.now().isoformat()
        workload_info = f"Current workload: {current_workload} active tasks" if current_workload else ""
        context_info = f"Context: {context_data.get('workload_assessment', 'moderate')}" if context_data else ""
        
        prompt = f"""
        Suggest a realistic deadline for this task based on current date {current_date}:
        
        Task: {task_data.get('title', '')}
        Description: {task_data.get('description', '')}
        Estimated Duration: {task_data.get('estimated_duration', 'unknown')} minutes
        Priority: {task_data.get('priority', 'medium')}
        
        {workload_info}
        {context_info}
        
        Provide JSON response:
        {{
            "suggested_deadline": "ISO datetime string",
            "reasoning": "explanation for the deadline choice",
            "buffer_time_included": "yes/no",
            "urgency_level": "low/medium/high",
            "recommended_start_date": "ISO datetime string"
        }}
        
        Consider task complexity, current workload, and reasonable time buffers.
        """
        
        try:
            response = self.client._make_request(prompt, max_tokens=800)
            if response:
                try:
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    if json_start != -1 and json_end != -1:
                        json_str = response[json_start:json_end]
                        result = json.loads(json_str)
                        
                        # Try to parse the suggested deadline
                        deadline_str = result.get('suggested_deadline')
                        if deadline_str:
                            try:
                                suggested_deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
                                result['parsed_deadline'] = suggested_deadline
                            except ValueError:
                                result['parsed_deadline'] = None
                        
                    else:
                        result = self._fallback_deadline(task_data)
                except json.JSONDecodeError:
                    result = self._fallback_deadline(task_data)
                
                processing_time = int((time.time() - start_time) * 1000)
                self._log_processing('deadline_suggestion', task_data, result, processing_time, True)
                return result
            else:
                result = self._fallback_deadline(task_data)
                processing_time = int((time.time() - start_time) * 1000)
                self._log_processing('deadline_suggestion', task_data, result, processing_time, False)
                return result
                
        except Exception as e:
            result = self._fallback_deadline(task_data)
            processing_time = int((time.time() - start_time) * 1000)
            self._log_processing('deadline_suggestion', task_data, result, processing_time, False, str(e))
            return result

    def _fallback_prioritization(self, task: Task) -> Dict:
        """Fallback priority calculation when AI is unavailable"""
        score = 0.5  # Default medium priority
        
        # Adjust based on explicit priority
        priority_scores = {'low': 0.25, 'medium': 0.5, 'high': 0.75, 'urgent': 0.95}
        if task.priority in priority_scores:
            score = priority_scores[task.priority]
        
        # Adjust based on deadline
        if task.deadline:
            days_until_deadline = (task.deadline - datetime.now()).days
            if days_until_deadline <= 1:
                score = min(score + 0.3, 1.0)
            elif days_until_deadline <= 3:
                score = min(score + 0.2, 1.0)
            elif days_until_deadline <= 7:
                score = min(score + 0.1, 1.0)
        
        return {
            "priority_score": score,
            "suggested_priority": task.priority,
            "reasoning": "Fallback calculation based on deadline and current priority",
            "urgency_factors": [],
            "suggested_deadline": task.deadline.isoformat() if task.deadline else None,
            "estimated_duration_refined": task.estimated_duration,
            "context_relevance": "Unable to analyze context"
        }

    def _fallback_enhancement(self, task_data: Dict) -> Dict:
        """Fallback task enhancement when AI is unavailable"""
        title = task_data.get('title', '')
        description = task_data.get('description', '')
        
        # Simple tag extraction from title and description
        text = f"{title} {description}".lower()
        suggested_tags = []
        
        common_tags = {
            'urgent': ['urgent', 'asap', 'immediately'],
            'meeting': ['meeting', 'call', 'conference'],
            'email': ['email', 'send', 'reply'],
            'research': ['research', 'investigate', 'analyze'],
            'development': ['develop', 'code', 'program', 'build'],
            'review': ['review', 'check', 'verify'],
            'planning': ['plan', 'schedule', 'organize']
        }
        
        for tag, keywords in common_tags.items():
            if any(keyword in text for keyword in keywords):
                suggested_tags.append(tag)
        
        return {
            "enhanced_description": description or f"Complete task: {title}",
            "suggested_tags": suggested_tags[:3],  # Limit to 3 tags
            "suggested_category": "general",
            "breakdown_suggestions": [],
            "resource_suggestions": [],
            "difficulty_assessment": "medium",
            "context_connections": "Unable to analyze context"
        }

    def _fallback_deadline(self, task_data: Dict) -> Dict:
        """Fallback deadline suggestion when AI is unavailable"""
        # Simple heuristic: add days based on priority and estimated duration
        priority = task_data.get('priority', 'medium')
        duration = task_data.get('estimated_duration', 60)
        
        days_to_add = {
            'urgent': 1,
            'high': 3,
            'medium': 7,
            'low': 14
        }
        
        base_days = days_to_add.get(priority, 7)
        
        # Adjust based on duration
        if duration and duration > 240:  # More than 4 hours
            base_days += 2
        elif duration and duration > 120:  # More than 2 hours
            base_days += 1
        
        suggested_deadline = datetime.now() + timedelta(days=base_days)
        
        return {
            "suggested_deadline": suggested_deadline.isoformat(),
            "reasoning": f"Fallback calculation: {base_days} days based on priority and duration",
            "buffer_time_included": "yes",
            "urgency_level": priority,
            "recommended_start_date": datetime.now().isoformat(),
            "parsed_deadline": suggested_deadline
        }

    def get_task_recommendations(self, task_data: Dict, context_entries: List[ContextEntry] = None,
                               user_preferences: Dict = None, current_task_load: int = 0) -> Dict:
        """Get comprehensive AI recommendations for a task"""
        
        # Analyze context if provided
        context_analysis = {}
        if context_entries:
            context_analysis = self.analyze_context(context_entries)
        
        # Get task prioritization
        temp_task = type('Task', (), task_data)()  # Create temporary task object
        for key, value in task_data.items():
            setattr(temp_task, key, value)
        
        # Set defaults for missing attributes
        if not hasattr(temp_task, 'category'):
            temp_task.category = None
        if not hasattr(temp_task, 'deadline'):
            temp_task.deadline = None
        if not hasattr(temp_task, 'estimated_duration'):
            temp_task.estimated_duration = None
        if not hasattr(temp_task, 'priority'):
            temp_task.priority = 'medium'
        
        prioritization = self.prioritize_task(temp_task, context_analysis)
        
        # Get task enhancement
        enhancement = self.enhance_task(task_data, context_analysis)
        
        # Get deadline suggestion
        deadline_suggestion = self.suggest_deadline(task_data, context_analysis, current_task_load)
        
        return {
            "priority_score": prioritization.get("priority_score", 0.5),
            "suggested_priority": prioritization.get("suggested_priority", "medium"),
            "enhanced_description": enhancement.get("enhanced_description", ""),
            "suggested_tags": enhancement.get("suggested_tags", []),
            "suggested_category": enhancement.get("suggested_category", ""),
            "suggested_deadline": deadline_suggestion.get("parsed_deadline"),
            "estimated_duration": prioritization.get("estimated_duration_refined"),
            "context_analysis": {
                "context_summary": context_analysis.get("context_summary", ""),
                "workload_assessment": context_analysis.get("workload_assessment", "moderate"),
                "urgency_indicators": context_analysis.get("urgency_indicators", []),
                "priority_reasoning": prioritization.get("reasoning", ""),
                "enhancement_reasoning": enhancement.get("context_connections", "")
            },
            "reasoning": f"AI Analysis: {prioritization.get('reasoning', '')} | {enhancement.get('context_connections', '')}"
        }