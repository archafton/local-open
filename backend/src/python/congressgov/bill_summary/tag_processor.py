import logging
from typing import List, Dict, Set

class TagProcessor:
    def __init__(self):
        self._setup_logging()
        self._initialize_tag_categories()

    def _setup_logging(self):
        """Set up logging configuration"""
        self.logger = logging.getLogger('tag_processor')
        self.logger.setLevel(logging.INFO)
        
        file_handler = logging.FileHandler('tag_processor.log')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def _initialize_tag_categories(self):
        """Initialize known tag categories"""
        self.categories = {
            'policy_areas': {
                'agriculture', 'budget', 'civil_rights', 'defense',
                'economy', 'education', 'energy', 'environment',
                'finance', 'foreign_policy', 'healthcare', 'housing',
                'immigration', 'infrastructure', 'labor', 'national_security',
                'science', 'social_services', 'taxation', 'technology',
                'trade', 'transportation', 'veterans'
            },
            'affected_groups': {
                'businesses', 'children', 'consumers', 'elderly',
                'employees', 'employers', 'families', 'farmers',
                'federal_agencies', 'healthcare_providers', 'immigrants',
                'local_governments', 'military', 'minorities', 'students',
                'taxpayers', 'veterans', 'workers'
            },
            'key_topics': {
                'appropriations', 'authorization', 'compliance',
                'enforcement', 'funding', 'grants', 'oversight',
                'regulation', 'research', 'safety', 'security',
                'standards', 'tax_credits', 'transparency'
            }
        }

    async def validate_tags(self, tags: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Validate tags against known categories
        Returns validated tags with invalid ones removed
        """
        try:
            validated_tags = {}
            
            for category, tag_list in tags.items():
                if category in self.categories:
                    valid_tags = [
                        tag for tag in tag_list
                        if self._is_valid_tag(tag, category)
                    ]
                    validated_tags[category] = valid_tags
                    
                    # Log any invalid tags
                    invalid_tags = set(tag_list) - set(valid_tags)
                    if invalid_tags:
                        self.logger.warning(f"Invalid tags found in {category}: {invalid_tags}")
            
            return validated_tags
        except Exception as e:
            self.logger.error(f"Error validating tags: {str(e)}")
            raise

    def _is_valid_tag(self, tag: str, category: str) -> bool:
        """Check if a tag is valid for its category"""
        normalized_tag = self._normalize_tag(tag)
        return normalized_tag in self.categories[category]

    async def normalize_tags(self, tags: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Normalize tag format and naming
        Returns normalized tags
        """
        try:
            normalized = {}
            for category, tag_list in tags.items():
                normalized[category] = [
                    self._normalize_tag(tag)
                    for tag in tag_list
                ]
            return normalized
        except Exception as e:
            self.logger.error(f"Error normalizing tags: {str(e)}")
            raise

    def _normalize_tag(self, tag: str) -> str:
        """Normalize a single tag"""
        # Convert to lowercase and replace spaces with underscores
        normalized = tag.lower().replace(' ', '_')
        # Remove any special characters except underscores
        normalized = ''.join(c for c in normalized if c.isalnum() or c == '_')
        return normalized

    async def suggest_new_tags(self, content: str) -> Set[str]:
        """
        Suggest new tag categories based on content
        Returns set of suggested new tags
        """
        try:
            # This is a placeholder for potential ML-based tag suggestion
            # For now, we'll just log that this feature is not implemented
            self.logger.info("Tag suggestion feature not yet implemented")
            return set()
        except Exception as e:
            self.logger.error(f"Error suggesting tags: {str(e)}")
            raise
