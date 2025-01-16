# Bill Text Processing and AI Summary Implementation Plan

## Overview
This document outlines the implementation plan for fetching bill text, processing it through various AI APIs, and storing summaries and tags in the database, using a modular approach with separate components for each major functionality.

## 1. Database Modifications

### Add New Fields to Bills Table
```sql
ALTER TABLE bills
ADD COLUMN IF NOT EXISTS bill_text_link VARCHAR(255),
ADD COLUMN IF NOT EXISTS bill_law_link VARCHAR(255);
```

## 2. Module Structure

### A. Database Module (`db_handler.py`)
```python
class DatabaseHandler:
    def __init__(self, connection_string):
        self.conn_string = connection_string
    
    async def get_bills_without_text(self):
        """Fetch bills that need text processing"""
    
    async def update_bill_links(self, bill_id, text_link, law_link):
        """Update bill text and law links"""
    
    async def update_bill_summary(self, bill_id, summary):
        """Update bill summary"""
    
    async def update_bill_tags(self, bill_id, tags):
        """Update bill tags"""
```

### B. Congress.gov API Module (`congress_api.py`)
```python
class CongressAPI:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
    
    async def fetch_bill_text_versions(self, congress, bill_type, number):
        """Fetch text versions from Congress.gov API"""
    
    async def extract_latest_text_link(self, versions_data):
        """Extract latest XML text link"""
    
    async def extract_law_link(self, versions_data):
        """Extract public law link if available"""
```

### C. XML Handler Module (`xml_handler.py`)
```python
class XMLHandler:
    def __init__(self, raw_dir):
        self.raw_dir = raw_dir
    
    async def download_xml(self, url, bill_number):
        """Download and save XML content"""
    
    async def parse_xml(self, xml_path):
        """Parse XML content for AI processing"""
    
    async def validate_xml(self, xml_content):
        """Validate XML structure"""
```

### D. AI Processor Modules

#### Base AI Processor (`ai_processor_base.py`)
```python
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
```

#### Anthropic Processor (`ai_anthropic_processor.py`)

We will make use the anthropic python library, and make use of "tools", so that the structure returned is predictable. See below for peritnent excerpt from Anthropic API docs: 

 You can use tools to get Claude produce JSON output that follows a schema, even if you don’t have any intention of running that output through a tool or function.

 When using tools in this way:

 You usually want to provide a single tool
 
 You should set tool_choice (see Forcing tool use) to instruct the model to explicitly use that tool
 
 Remember that the model will pass the input to the tool, so the name of the tool and description should be from the model’s perspective.
 
 The following uses a record_summary tool to describe an image following a particular format.

```python
import base64
import anthropic
import httpx

image_url = "https://upload.wikimedia.org/wikipedia/commons/a/a7/Camponotus_flavomarginatus_ant.jpg"
image_media_type = "image/jpeg"
image_data = base64.b64encode(httpx.get(image_url).content).decode("utf-8")

message = anthropic.Anthropic().messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=[
        {
            "name": "record_summary",
            "description": "Record summary of an image using well-structured JSON.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "key_colors": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "r": {
                                    "type": "number",
                                    "description": "red value [0.0, 1.0]",
                                },
                                "g": {
                                    "type": "number",
                                    "description": "green value [0.0, 1.0]",
                                },
                                "b": {
                                    "type": "number",
                                    "description": "blue value [0.0, 1.0]",
                                },
                                "name": {
                                    "type": "string",
                                    "description": "Human-readable color name in snake_case, e.g. \"olive_green\" or \"turquoise\""
                                },
                            },
                            "required": ["r", "g", "b", "name"],
                        },
                        "description": "Key colors in the image. Limit to less then four.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Image description. One to two sentences max.",
                    },
                    "estimated_year": {
                        "type": "integer",
                        "description": "Estimated year that the images was taken, if it a photo. Only set this if the image appears to be non-fictional. Rough estimates are okay!",
                    },
                },
                "required": ["key_colors", "description"],
            },
        }
    ],
    tool_choice={"type": "tool", "name": "record_summary"},
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image_media_type,
                        "data": image_data,
                    },
                },
                {"type": "text", "text": "Describe this image."},
            ],
        }
    ],
)
print(message)

```
 Controlling Claude’s output
​
 Forcing tool use
 In some cases, you may want Claude to use a specific tool to answer the user’s question, even if Claude thinks it can provide an answer without using a tool. You can do this by specifying the tool in the tool_choice field like so:


 ```tool_choice = {"type": "tool", "name": "get_weather"}```

 When working with the tool_choice parameter, we have three possible options:

 auto allows Claude to decide whether to call any provided tools or not. This is the default value.

 any tells Claude that it must use one of the provided tools, but doesn’t force a particular tool.

 tool allows us to force Claude to always use a particular tool."

**This means the following will need to be adjusted to make use of the above**

```python
from ai_processor_base import AIProcessorBase

class AnthropicProcessor(AIProcessorBase):
    def __init__(self, config: dict):
        self.api_key = config['api_key']
        self.model = config['model']  # claude-2, claude-instant-1, etc.
        self.max_tokens = config['max_tokens']
    
    async def generate_summary(self, bill_text: str) -> str:
        """
        Generate summary using Anthropic's Claude models
        Model determined by ANTHROPIC_MODEL env var
        """
    
    async def extract_tags(self, bill_text: str, tag_categories: list) -> dict:
        """Extract tags using Anthropic's Claude models"""
    
    async def validate_response(self, response: dict) -> bool:
        """Validate Anthropic API response format"""
    
    async def get_model_info(self) -> dict:
        """Return current Anthropic model information"""
```

#### OpenAI Processor (`ai_openai_processor.py`)
```python
from ai_processor_base import AIProcessorBase

class OpenAIProcessor(AIProcessorBase):
    def __init__(self, config: dict):
        self.api_key = config['api_key']
        self.model = config['model']  # gpt-4, gpt-3.5-turbo, etc.
        self.max_tokens = config['max_tokens']
    
    async def generate_summary(self, bill_text: str) -> str:
        """
        Generate summary using OpenAI models
        Model determined by OPENAI_MODEL env var
        """
    
    async def extract_tags(self, bill_text: str, tag_categories: list) -> dict:
        """Extract tags using OpenAI models"""
    
    async def validate_response(self, response: dict) -> bool:
        """Validate OpenAI API response format"""
    
    async def get_model_info(self) -> dict:
        """Return current OpenAI model information"""
```

#### AI Processor Factory (`ai_processor_factory.py`)
```python
class AIProcessorFactory:
    @staticmethod
    def create_processor(processor_type: str, config: dict) -> AIProcessorBase:
        """
        Create AI processor based on AI_PROCESSOR_ENDPOINT env var
        """
        if processor_type.lower() == 'anthropic':
            return AnthropicProcessor(config)
        elif processor_type.lower() == 'openai':
            return OpenAIProcessor(config)
        else:
            raise ValueError(f"Unsupported AI processor type: {processor_type}")
```

### E. Tag Processor Module (`tag_processor.py`)
```python
class TagProcessor:
    def __init__(self, tag_categories):
        self.categories = tag_categories
    
    async def validate_tags(self, tags):
        """Validate tags against known categories"""
    
    async def normalize_tags(self, tags):
        """Normalize tag format and naming"""
    
    async def suggest_new_tags(self, content):
        """Suggest new tag categories based on content"""
```

### F. Logger Module (`logger.py`)
```python
class ProcessLogger:
    def __init__(self, log_config):
        self.config = log_config
    
    def log_processing_start(self, bill_id):
        """Log start of bill processing"""
    
    def log_api_request(self, api_name, endpoint):
        """Log API requests"""
    
    def log_error(self, error_type, details):
        """Log errors with context"""
    
    def log_metrics(self, metrics_data):
        """Log processing metrics"""
```

## 3. Main Processing Script (`bill_text_process.py`)

```python
class BillTextProcessor:
    def __init__(self, config):
        self.db = DatabaseHandler(config['database'])
        self.congress_api = CongressAPI(config['congress_api'])
        self.xml_handler = XMLHandler(config['raw_dir'])
        
        # Create AI processor based on environment variable
        processor_type = os.getenv('AI_PROCESSOR_ENDPOINT', 'anthropic')
        self.ai_processor = AIProcessorFactory.create_processor(
            processor_type,
            self._get_ai_config(processor_type)
        )
        
        self.tag_processor = TagProcessor(config['tags'])
        self.logger = ProcessLogger(config['logging'])
    
    def _get_ai_config(self, processor_type: str) -> dict:
        """Get AI configuration based on processor type"""
        if processor_type == 'anthropic':
            return {
                'api_key': os.getenv('ANTHROPIC_API_KEY'),
                'model': os.getenv('ANTHROPIC_MODEL'),
                'max_tokens': 8000
            }
        elif processor_type == 'openai':
            return {
                'api_key': os.getenv('OPENAI_API_KEY'),
                'model': os.getenv('OPENAI_MODEL', 'gpt-4'),
                'max_tokens': 2000
            }
        else:
            raise ValueError(f"Unsupported AI processor type: {processor_type}")

    async def process_single_bill(self, bill_id):
        """Process a single bill"""
        try:
            # 1. Fetch bill data
            bill_data = await self.db.get_bill_data(bill_id)
            
            # 2. Get text versions
            versions = await self.congress_api.fetch_bill_text_versions(
                bill_data['congress'],
                bill_data['type'],
                bill_data['number']
            )
            
            # 3. Extract links
            text_link = await self.congress_api.extract_latest_text_link(versions)
            law_link = await self.congress_api.extract_law_link(versions)
            
            # 4. Update links in database
            await self.db.update_bill_links(bill_id, text_link, law_link)
            
            # 5. Download and process XML
            xml_path = await self.xml_handler.download_xml(text_link, bill_data['number'])
            bill_text = await self.xml_handler.parse_xml(xml_path)
            
            # 6. Generate AI summary and tags
            summary = await self.ai_processor.generate_summary(bill_text)
            tags = await self.ai_processor.extract_tags(bill_text)
            
            # 7. Validate and normalize tags
            validated_tags = await self.tag_processor.validate_tags(tags)
            
            # 8. Update database
            await self.db.update_bill_summary(bill_id, summary)
            await self.db.update_bill_tags(bill_id, validated_tags)
            
        except Exception as e:
            self.logger.log_error('ProcessingError', str(e))
            raise

    async def process_pending_bills(self):
        """Process all pending bills"""
        bills = await self.db.get_bills_without_text()
        for bill in bills:
            await self.process_single_bill(bill['id'])
```

## 4. Environment Variables

backend/.env file contains variables.

```bash
# AI Provider Selection
AI_PROCESSOR_ENDPOINT=anthropic  # or 'openai'

# Anthropic Configuration
ANTHROPIC_API_KEY=your_anthropic_key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# OpenAI Configuration
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4  # or 'gpt-3.5-turbo'
```

## 5. Configuration Structure

```python
config = {
    'database': {
        'connection_string': 'postgresql://localhost/project_tacitus_test',
        'max_connections': 10,
        'timeout': 30
    },
    'congress_api': {
        'base_url': 'https://api.congress.gov/v3',
        'api_key': 'YOUR_API_KEY',
        'rate_limit': 5
    },
    'raw_dir': 'backend/src/python/bills-fetch/raw',
    'logging': {
        'file': 'bill_text_process.log',
        'level': 'INFO'
    }
}
```

## 6. Testing Structure

### A. Unit Tests
```python
# test_congress_api.py
class TestCongressAPI:
    async def test_fetch_bill_text_versions(self):
        """Test API fetching"""

# test_xml_handler.py
class TestXMLHandler:
    async def test_download_xml(self):
        """Test XML downloading"""

# test_ai_processors.py
class TestAIProcessors:
    async def test_anthropic_processor(self):
        """Test Anthropic API integration"""
    
    async def test_openai_processor(self):
        """Test OpenAI API integration"""
    
    async def test_processor_factory(self):
        """Test AI processor factory"""
```

### B. Integration Tests
```python
# test_integration.py
class TestIntegration:
    async def test_full_bill_processing(self):
        """Test complete bill processing flow"""
```

## 7. Implementation Steps

1. Create module directory structure
2. Implement database modifications
3. Create AI processor base class and implementations
4. Create remaining module base classes
5. Implement core functionality in each module
6. Add logging and error handling
7. Implement main processing script
8. Add monitoring and metrics
9. Deploy and verify

## 8. Future AI Provider Integration

To add a new AI provider:

1. Create new processor class implementing AIProcessorBase
2. Add provider configuration to environment variables
3. Update AIProcessorFactory
4. Add provider-specific tests
5. Update documentation

Example for adding a new provider:

```python
# ai_cohere_processor.py
class CohereProcessor(AIProcessorBase):
    def __init__(self, config: dict):
        self.api_key = config['api_key']
        self.model = config['model']
    
    async def generate_summary(self, bill_text: str) -> str:
        """Generate summary using Cohere models"""
        pass
    
    async def extract_tags(self, bill_text: str, tag_categories: list) -> dict:
        """Extract tags using Cohere models"""
        pass
    
    async def validate_response(self, response: dict) -> bool:
        """Validate Cohere API response format"""
        pass
    
    async def get_model_info(self) -> dict:
        """Return current Cohere model information"""
        pass
```

## Next Steps

1. Set up module directory structure
2. Implement database changes
3. Create AI processor base class and initial implementations
4. Create basic module templates
5. Add core functionality
6. Implement testing framework
7. Add monitoring
8. Deploy initial version
