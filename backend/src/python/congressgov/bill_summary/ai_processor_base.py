from abc import ABC, abstractmethod

class AIProcessorBase(ABC):
    """Abstract base class for AI processors"""
    
    @abstractmethod
    async def generate_summary(self, bill_text: str) -> str:
        """Generate bill summary"""
        pass
    
    @abstractmethod
    async def extract_tags(self, bill_text: str, tag_categories: list) -> dict:
        """Extract relevant tags"""
        pass
    
    @abstractmethod
    async def validate_response(self, response: dict) -> bool:
        """Validate AI response format"""
        pass

    @abstractmethod
    async def get_model_info(self) -> dict:
        """Get information about the current model"""
        pass
