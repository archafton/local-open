import os
import sys
import time
import asyncio
from typing import Dict, Optional
from datetime import datetime

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from backend.src.python.congressgov.bill_summary.db_handler import DatabaseHandler
from backend.src.python.congressgov.bill_summary.congress_api import CongressAPI
from backend.src.python.congressgov.bill_summary.xml_handler import XMLHandler
from backend.src.python.congressgov.bill_summary.ai_processor_factory import AIProcessorFactory
from backend.src.python.congressgov.bill_summary.tag_processor import TagProcessor
from backend.src.python.congressgov.bill_summary.logger import ProcessLogger

class BillTextProcessor:
    def __init__(self):
        self.db = DatabaseHandler()
        self.congress_api = CongressAPI()
        self.xml_handler = XMLHandler(
            os.path.join(os.path.dirname(__file__), '..', 'bill_fetch', 'raw')
        )
        self.ai_processor = AIProcessorFactory.create_processor()
        self.tag_processor = TagProcessor()
        self.logger = ProcessLogger()

    async def process_single_bill(self, bill_id: int) -> bool:
        """Process a single bill"""
        try:
            # 1. Fetch bill data
            bill_data = await self.db.get_bill_data(bill_id)
            if not bill_data:
                self.logger.log_error('DataError', f'Bill {bill_id} not found')
                return False

            self.logger.log_processing_start(bill_id, bill_data['bill_number'])

            # 2. Get text versions
            versions = await self.congress_api.fetch_bill_text_versions(
                bill_data['congress'],
                bill_data['bill_number'][:2],  # Extract bill type (HR, S, etc.)
                bill_data['bill_number'][2:]   # Extract bill number
            )

            # 3. Extract links
            text_link = await self.congress_api.extract_latest_text_link(versions)
            law_link = await self.congress_api.extract_law_link(versions)

            # 4. Update links in database
            await self.db.update_bill_links(bill_id, text_link, law_link)
            self.logger.log_success(bill_data['bill_number'], 'link update')

            if not text_link:
                self.logger.log_warning(f'No text link available for bill {bill_data["bill_number"]}')
                return False

            # 5. Download and process XML
            xml_path = await self.congress_api.download_xml(text_link, bill_data['bill_number'])
            bill_text = await self.xml_handler.parse_xml(xml_path)
            
            if not bill_text:
                self.logger.log_error('XMLError', f'Failed to extract text from XML for bill {bill_data["bill_number"]}')
                return False

            # 6. Generate AI summary
            summary = await self.ai_processor.generate_summary(bill_text)
            self.logger.log_success(bill_data['bill_number'], 'summary generation')

            # 7. Extract and process tags
            raw_tags = await self.ai_processor.extract_tags(
                bill_text,
                ['policy_areas', 'affected_groups', 'key_topics']
            )
            normalized_tags = await self.tag_processor.normalize_tags(raw_tags)
            validated_tags = await self.tag_processor.validate_tags(normalized_tags)
            self.logger.log_success(bill_data['bill_number'], 'tag processing')

            # 8. Update database
            await self.db.update_bill_summary(bill_id, summary)
            await self.db.update_bill_tags(bill_id, validated_tags)
            self.logger.log_success(bill_data['bill_number'], 'database update')

            # 9. Archive processed XML
            await self.xml_handler.archive_xml(xml_path, bill_data['bill_number'])
            
            # Log metrics
            self.logger.log_metrics({
                'bill_id': bill_id,
                'bill_number': bill_data['bill_number'],
                'processing_time': time.time(),
                'summary_length': len(summary) if summary else 0,
                'tag_count': sum(len(tags) for tags in validated_tags.values())
            })

            return True

        except Exception as e:
            self.logger.log_error('ProcessingError', str(e))
            return False

    async def process_pending_bills(self, limit: int = 10):
        """Process all pending bills"""
        try:
            bills = await self.db.get_bills_without_text()
            processed_count = 0
            failed_count = 0

            for bill in bills[:limit]:
                success = await self.process_single_bill(bill['id'])
                if success:
                    processed_count += 1
                else:
                    failed_count += 1

            self.logger.log_info(
                f"Completed processing batch. "
                f"Successful: {processed_count}, Failed: {failed_count}"
            )

        except Exception as e:
            self.logger.log_error('BatchProcessingError', str(e))
            raise

async def main():
    """Main entry point for bill text processing"""
    processor = BillTextProcessor()
    await processor.process_pending_bills()

if __name__ == "__main__":
    asyncio.run(main())
