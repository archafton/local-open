import os
from .ai_anthropic_processor import AnthropicProcessor

class AIProcessorFactory:
    @staticmethod
    def create_processor(processor_type: str = None) -> AnthropicProcessor:
        """
        Create AI processor based on AI_PROCESSOR_ENDPOINT env var
        Currently only supporting Anthropic
        """
        if processor_type is None:
            processor_type = os.getenv('AI_PROCESSOR_ENDPOINT', 'anthropic')

        if processor_type.lower() == 'anthropic':
            return AnthropicProcessor()
        else:
            raise ValueError(f"Unsupported AI processor type: {processor_type}")
