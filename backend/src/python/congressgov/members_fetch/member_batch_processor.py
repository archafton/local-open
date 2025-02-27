#!/usr/bin/env python3
"""
Batch processor for members - for processing large volumes of members
or filling in missing data. Supports batched operations and parallel processing.
"""

import os
import json
import argparse
import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set

# Import utilities
from congressgov.utils.logging_config import setup_logging
from congressgov.utils.api import APIClient
from congressgov.utils.database import get_db_connection, with_db_transaction
from congressgov.utils.file_storage import cleanup_old_files

# Import our other member processors
from member_detail_processor import MemberDetailProcessor
from member_enrichment import MemberEnrichment

# Set up logging
logger = setup_logging(__name__)

# API configuration
BASE_API_URL = "https://api.congress.gov/v3"
MAX_WORKERS = 4  # Maximum number of concurrent workers for parallel processing

def get_current_members() -> List[Tuple[int, str]]:
    """Get all current members from the database."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, bioguide_id 
                FROM members 
                WHERE current_member = true
                ORDER BY last_updated ASC NULLS FIRST
            """)
            return [(row[0], row[1]) for row in cur.fetchall()]

def get_members_by_chamber(chamber: str, limit: int = None) -> List[Tuple[int, str]]:
    """Get members by chamber (senate or house)."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT id, bioguide_id 
                FROM members 
                WHERE chamber = %s AND current_member = true
                ORDER BY last_updated ASC NULLS FIRST
            """
            params = [chamber]
            
            if limit:
                query += " LIMIT %s"
                params.append(limit)
                
            cur.execute(query, params)
            return [(row[0], row[1]) for row in cur.fetchall()]

def get_members_missing_data(data_type: str, limit: int = None) -> List[Tuple[int, str]]:
    """Get members missing specific data."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            query = ""
            
            if data_type == 'details':
                query = """
                    SELECT id, bioguide_id 
                    FROM members 
                    WHERE direct_order_name IS NULL
                       OR birth_year IS NULL
                    ORDER BY last_updated ASC NULLS FIRST
                """
            elif data_type == 'leadership':
                query = """
                    SELECT m.id, m.bioguide_id 
                    FROM members m
                    LEFT JOIN member_leadership ml ON m.id = ml.member_id
                    WHERE m.leadership_role IS NOT NULL AND ml.id IS NULL
                    ORDER BY m.last_updated ASC NULLS FIRST
                """
            elif data_type == 'party_history':
                query = """
                    SELECT m.id, m.bioguide_id 
                    FROM members m
                    LEFT JOIN member_party_history mph ON m.id = mph.member_id
                    GROUP BY m.id, m.bioguide_id
                    HAVING COUNT(mph.id) = 0
                    ORDER BY m.last_updated ASC NULLS FIRST
                """
            elif data_type == 'bio':
                query = """
                    SELECT id, bioguide_id 
                    FROM members 
                    WHERE profile_text IS NULL
                       OR bio_directory IS NULL
                    ORDER BY last_updated ASC NULLS FIRST
                """
            elif data_type == 'legislation':
                query = """
                    SELECT m.id, m.bioguide_id 
                    FROM members m
                    LEFT JOIN sponsored_legislation sl ON m.id = sl.member_id
                    WHERE m.current_member = true
                    GROUP BY m.id, m.bioguide_id
                    HAVING COUNT(sl.id) = 0
                    ORDER BY m.last_updated ASC NULLS FIRST
                """
            else:
                raise ValueError(f"Unknown data type: {data_type}")
            
            if limit:
                query += f" LIMIT {limit}"
                
            cur.execute(query)
            return [(row[0], row[1]) for row in cur.fetchall()]

def process_member_batch(members: List[Tuple[int, str]], process_type: str, 
                       batch_size: int = 10, parallel: bool = False) -> Dict[str, int]:
    """
    Process a batch of members, optionally in parallel.
    
    Args:
        members: List of tuples (member_id, bioguide_id)
        process_type: Type of processing ('details', 'enrichment', 'bio')
        batch_size: Number of members to process in each batch
        parallel: Whether to process members in parallel
        
    Returns:
        Dictionary with processing statistics
    """
    api_client = APIClient(BASE_API_URL)
    
    if process_type == 'details':
        processor = MemberDetailProcessor(api_client)
    elif process_type == 'enrichment':
        processor = MemberEnrichment(api_client)
    else:
        # For 'bio' we would need to import and initialize MemberBioProcessor
        # But we'll skip implementing that here
        raise ValueError(f"Unsupported process type: {process_type}")
    
    stats = {
        "total": len(members),
        "processed": 0,
        "success": 0,
        "failed": 0
    }
    
    # Process members in batches
    for i in range(0, len(members), batch_size):
        batch = members[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(len(members)-1)//batch_size + 1} ({len(batch)} members)")
        
        if parallel and len(batch) > 1:
            # Process batch in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(batch))) as executor:
                futures = {}
                for member_id, bioguide_id in batch:
                    if process_type == 'details':
                        future = executor.submit(processor.process_member, bioguide_id)
                    elif process_type == 'enrichment':
                        future = executor.submit(processor.process_member, bioguide_id)
                    # Add other process types as needed
                    
                    futures[future] = (member_id, bioguide_id)
                
                for future in concurrent.futures.as_completed(futures):
                    member_id, bioguide_id = futures[future]
                    try:
                        result = future.result()
                        stats["processed"] += 1
                        
                        if result["status"] == "success":
                            stats["success"] += 1
                            logger.info(f"Successfully processed member {bioguide_id}")
                        else:
                            stats["failed"] += 1
                            logger.error(f"Failed to process member {bioguide_id}: {result.get('error', 'Unknown error')}")
                            
                    except Exception as e:
                        stats["processed"] += 1
                        stats["failed"] += 1
                        logger.error(f"Error processing member {bioguide_id}: {str(e)}")
        else:
            # Process batch sequentially
            for member_id, bioguide_id in batch:
                try:
                    if process_type == 'details':
                        result = processor.process_member(bioguide_id)
                    elif process_type == 'enrichment':
                        result = processor.process_member(bioguide_id)
                    # Add other process types as needed
                    
                    stats["processed"] += 1
                    
                    if result["status"] == "success":
                        stats["success"] += 1
                        logger.info(f"Successfully processed member {bioguide_id}")
                    else:
                        stats["failed"] += 1
                        logger.error(f"Failed to process member {bioguide_id}: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    stats["processed"] += 1
                    stats["failed"] += 1
                    logger.error(f"Error processing member {bioguide_id}: {str(e)}")
        
        logger.info(f"Batch complete. Progress: {stats['processed']}/{stats['total']} members processed.")
    
    return stats

def main():
    parser = argparse.ArgumentParser(description='Batch processor for members')
    parser.add_argument('--process-type', choices=['details', 'enrichment', 'bio'], 
                      default='details', help='Type of processing to perform')
    parser.add_argument('--chamber', choices=['senate', 'house'], 
                      help='Process members from a specific chamber')
    parser.add_argument('--missing', choices=['details', 'leadership', 'party_history', 'bio', 'legislation'], 
                      help='Process members missing specific data')
    parser.add_argument('--batch-size', type=int, default=10, help='Number of members to process in each batch')
    parser.add_argument('--limit', type=int, help='Maximum number of members to process')
    parser.add_argument('--parallel', action='store_true', help='Process members in parallel')
    parser.add_argument('--validate', action='store_true', help='Validate data before processing')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without actually processing')
    args = parser.parse_args()
    
    try:
        members_to_process = []
        
        if args.chamber:
            # Get members from a specific chamber
            members_to_process = get_members_by_chamber(args.chamber, args.limit)
            logger.info(f"Found {len(members_to_process)} members in the {args.chamber}")
            
        elif args.missing:
            # Get members missing specific data
            members_to_process = get_members_missing_data(args.missing, args.limit)
            logger.info(f"Found {len(members_to_process)} members missing {args.missing} data")
            
        else:
            # Get all current members
            members_to_process = get_current_members()
            if args.limit and len(members_to_process) > args.limit:
                members_to_process = members_to_process[:args.limit]
            logger.info(f"Found {len(members_to_process)} current members")
        
        if not members_to_process:
            logger.warning("No members found to process based on the given criteria")
            return
        
        if args.dry_run:
            logger.info("Dry run - would process the following members:")
            for member_id, bioguide_id in members_to_process:
                logger.info(f"  {bioguide_id} (ID: {member_id})")
            return
        
        # Process members in batches
        logger.info(f"Processing {len(members_to_process)} members in batches of {args.batch_size}")
        logger.info(f"Process type: {args.process_type}")
        logger.info(f"Parallel processing: {'Enabled' if args.parallel else 'Disabled'}")
        
        stats = process_member_batch(members_to_process, args.process_type, args.batch_size, args.parallel)
        
        logger.info("Batch processing complete")
        logger.info(f"Total members: {stats['total']}")
        logger.info(f"Successfully processed: {stats['success']}")
        logger.info(f"Failed: {stats['failed']}")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()