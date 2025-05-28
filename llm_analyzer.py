from openai import AsyncOpenAI
from config import config
import logging
import json

logger = logging.getLogger(__name__)

class LLMAnalyzer:
    """Analyzes text content using OpenAI's API."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=config.openai_api_key)
    
    async def analyze_content(self, content: str) -> dict:
        """
        Analyze the content of a message and return its topic and summary.
        
        Args:
            content: The text content to analyze
            
        Returns:
            A dictionary containing the topic and summary
        """
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": """You are an expert at analyzing and categorizing text content for a personal knowledge management system.
                    
                    For each message, provide:
                    1. A concise topic (1-3 words) that captures the main subject or theme
                    2. A brief summary (1-2 sentences) that highlights the key points or insights
                    
                    Guidelines:
                    - Topics should be specific and meaningful (e.g., "Python Debugging" instead of just "Programming")
                    - Summaries should capture the essence and any actionable insights
                    - If the content is a question, include the question in the summary
                    - If the content is a task or todo, make it clear in the summary
                    - If the content is a reference or link, note what it's about
                    
                    Format your response as JSON with two fields:
                    - topic: the concise topic
                    - summary: the brief summary"""},
                    {"role": "user", "content": content}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            result = response.choices[0].message.content
            logger.info(f"Raw LLM response: {result}")
            
            # Parse the JSON string into a dictionary
            analysis_dict = json.loads(result)
            logger.info(f"Parsed analysis: {analysis_dict}")
            
            return analysis_dict
            
        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            return {
                "topic": "Unknown",
                "summary": "Failed to analyze content"
            }

# Create a global analyzer instance
analyzer = LLMAnalyzer() 