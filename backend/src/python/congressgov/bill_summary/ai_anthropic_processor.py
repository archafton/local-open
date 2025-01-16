import os
import anthropic
from typing import Dict, List
from .ai_processor_base import AIProcessorBase

class AnthropicProcessor(AIProcessorBase):
    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.max_tokens = 8000

    async def generate_summary(self, bill_text: str) -> str:
        """Generate summary using Anthropic's Claude model with structured output"""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                tools=[{
                    "name": "generate_bill_summary",
                    "description": "Generate a comprehensive summary of a legislative bill",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "summary": {
                                "type": "string",
                                "description": "Concise summary of the bill's key points and objectives"
                            },
                            "impact": {
                                "type": "string",
                                "description": "Potential impact and implications of the bill"
                            }
                        },
                        "required": ["summary", "impact"]
                    }
                }],
                tool_choice={"type": "tool", "name": "generate_bill_summary"},
                messages=[{
                    "role": "user",
                    "content": f"Generate a comprehensive summary of this bill: {bill_text}"
                }]
            )
            return message.content

        except Exception as e:
            raise Exception(f"Error generating summary: {str(e)}")

    async def extract_tags(self, bill_text: str, tag_categories: list) -> dict:
        """Extract tags using Anthropic's Claude model with structured output"""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                tools=[{
                    "name": "extract_bill_tags",
                    "description": "Extract relevant tags from bill text",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "policy_areas": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Main policy areas addressed in the bill"
                            },
                            "affected_groups": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Groups or entities affected by the bill"
                            },
                            "key_topics": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Key topics and themes in the bill"
                            }
                        },
                        "required": ["policy_areas", "affected_groups", "key_topics"]
                    }
                }],
                tool_choice={"type": "tool", "name": "extract_bill_tags"},
                messages=[{
                    "role": "user",
                    "content": f"Extract relevant tags from this bill text, considering these categories: {tag_categories}\n\nBill text: {bill_text}"
                }]
            )
            return message.content

        except Exception as e:
            raise Exception(f"Error extracting tags: {str(e)}")

    async def validate_response(self, response: dict) -> bool:
        """Validate Anthropic API response format"""
        required_fields = ["summary", "impact"] if "summary" in response else ["policy_areas", "affected_groups", "key_topics"]
        return all(field in response for field in required_fields)

    async def get_model_info(self) -> dict:
        """Return current Anthropic model information"""
        return {
            "provider": "Anthropic",
            "model": self.model,
            "max_tokens": self.max_tokens
        }
