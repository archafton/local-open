import os
import logging
import xml.etree.ElementTree as ET
from typing import Optional
from xml.etree.ElementTree import ParseError

class XMLHandler:
    def __init__(self, raw_dir: str):
        self.raw_dir = raw_dir
        self._setup_logging()

    def _setup_logging(self):
        """Set up logging configuration"""
        self.logger = logging.getLogger('xml_handler')
        self.logger.setLevel(logging.INFO)
        
        # Create handler for file logging
        file_handler = logging.FileHandler(
            os.path.join(os.path.dirname(__file__), '..', 'logs', 'xml_handler.log')
        )
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    async def validate_xml(self, xml_content: str) -> bool:
        """
        Validate XML structure
        Returns True if valid, False otherwise
        """
        try:
            ET.fromstring(xml_content)
            return True
        except ParseError as e:
            self.logger.error(f"XML validation failed: {str(e)}")
            return False

    async def parse_xml(self, xml_path: str) -> Optional[str]:
        """
        Parse XML content for AI processing
        Returns cleaned text content suitable for AI processing
        """
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Extract text content while preserving structure
            text_content = []
            
            # Process title if present
            title_elem = root.find(".//title")
            if title_elem is not None:
                text_content.append(f"TITLE: {title_elem.text.strip()}")
            
            # Process sections
            for section in root.findall(".//section"):
                # Get section number/header if available
                section_num = section.find("enum")
                section_header = section.find("header")
                
                if section_num is not None and section_header is not None:
                    text_content.append(f"\nSECTION {section_num.text}: {section_header.text}")
                
                # Process text content
                for text in section.findall(".//text"):
                    if text.text:
                        text_content.append(text.text.strip())
            
            # Join all text with proper spacing
            processed_text = "\n".join(filter(None, text_content))
            
            # Log success
            self.logger.info(f"Successfully parsed XML file: {xml_path}")
            
            return processed_text
        except Exception as e:
            self.logger.error(f"Error parsing XML file {xml_path}: {str(e)}")
            raise

    async def archive_xml(self, xml_path: str, bill_number: str) -> str:
        """
        Archive processed XML file
        Returns path to archived file
        """
        try:
            archive_dir = os.path.join(self.raw_dir, 'processed')
            if not os.path.exists(archive_dir):
                os.makedirs(archive_dir)
            
            filename = os.path.basename(xml_path)
            archive_path = os.path.join(archive_dir, filename)
            
            os.rename(xml_path, archive_path)
            self.logger.info(f"Archived XML file to {archive_path}")
            
            return archive_path
        except Exception as e:
            self.logger.error(f"Error archiving XML file: {str(e)}")
            raise
