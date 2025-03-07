#!/usr/bin/env python3
"""
Batch processor for bills - for processing large volumes of historical bills
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
from congressgov.utils.bill_utils import parse_bill_number

# Import our other bill processors
from bill_detail_processor import BillProcessor
from bill_validation import check_missing_details, check_missing_enrichment, is_historical_bill

# Set up logging
logger = setup_logging(__name__)

# API configuration
BASE_API_URL = "https://api.congress.gov/v3"
MAX_WORKERS = 4  # Maximum number of concurrent workers for parallel processing
HISTORICAL_CONGRESS_RANGE = range(6, 43)  # 6th-42nd Congresses (1799-1873)

def get_bills_by_congress(congress: str, limit: int = None) -> List[str]:
    """Get all bill numbers for a specific congress."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT bill_number 
                FROM bills 
                WHERE congress = %s 
                ORDER BY bill_number
            """
            params = [congress]
            
            if limit:
                query += " LIMIT %s"
                params.append(limit)
                
            cur.execute(query, params)
            return [row[0] for row in cur.fetchall()]

def get_bills_by_status(status: str, limit: int = None) -> List[Tuple[str, str]]:
    """Get all bill numbers with a specific normalized status."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT bill_number, congress 
                FROM bills 
                WHERE normalized_status = %s 
                ORDER BY introduced_date DESC
            """
            params = [status]
            
            if limit:
                query += " LIMIT %s"
                params.append(limit)
                
            cur.execute(query, params)
            return [(row[0], row[1]) for row in cur.fetchall()]

def get_bills_missing_data(data_type: str, limit: int = None, exclude_historical: bool = False) -> List[Tuple[str, str]]:
    """Get bills missing specific data."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            query = ""
            
            # Base condition for excluding historical bills if requested
            historical_condition = ""
            if exclude_historical:
                historical_condition = " AND (congress::int < 6 OR congress::int > 42)"
            
            if data_type == 'text_versions':
                query = f"""
                    SELECT bill_number, congress 
                    FROM bills 
                    WHERE (text_versions IS NULL OR text_versions = '[]'::jsonb){historical_condition}
                    ORDER BY introduced_date DESC
                """
            elif data_type == 'summary':
                query = f"""
                    SELECT bill_number, congress 
                    FROM bills 
                    WHERE summary IS NULL{historical_condition}
                    ORDER BY introduced_date DESC
                """
            elif data_type == 'actions':
                query = f"""
                    SELECT b.bill_number, b.congress 
                    FROM bills b 
                    LEFT JOIN bill_actions ba ON UPPER(b.bill_number) = UPPER(ba.bill_number) 
                    WHERE 1=1{historical_condition}
                    GROUP BY b.bill_number, b.congress 
                    HAVING COUNT(ba.id) = 0 
                    ORDER BY b.introduced_date DESC
                """
            elif data_type == 'cosponsors':
                query = f"""
                    SELECT b.bill_number, b.congress 
                    FROM bills b 
                    LEFT JOIN bill_cosponsors bc ON UPPER(b.bill_number) = UPPER(bc.bill_number) 
                    WHERE b.sponsor_id IS NOT NULL{historical_condition}
                    GROUP BY b.bill_number, b.congress 
                    HAVING COUNT(bc.id) = 0 
                    ORDER BY b.introduced_date DESC
                """
            else:
                raise ValueError(f"Unknown data type: {data_type}")
            
            if limit:
                query += f" LIMIT {limit}"
                
            cur.execute(query)
            return [(row[0], row[1]) for row in cur.fetchall()]

def get_historical_bills(limit: int = None) -> List[Tuple[str, str, str]]:
    """Get bills from historical Congresses (6th-42nd)."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT bill_number, congress
                FROM bills
                WHERE congress::int >= 6 AND congress::int <= 42
                ORDER BY congress, bill_number
            """
            
            if limit:
                query += f" LIMIT {limit}"
                
            cur.execute(query)
            results = []
            for bill_number, congress in cur.fetchall():
                bill_type, bill_num = parse_bill_number(bill_number)
                results.append((congress, bill_type, bill_num))
            
            return results

def process_bill_batch(bills: List[Tuple[str, str, str]], batch_size: int = 10, 
                      parallel: bool = False, historical_mode: bool = False) -> Dict[str, int]:
    """
    Process a batch of bills, optionally in parallel.
    
    Args:
        bills: List of tuples (congress, bill_type, bill_number)
        batch_size: Number of bills to process in each batch
        parallel: Whether to process bills in parallel
        historical_mode: Whether to use specialized processing for historical bills
        
    Returns:
        Dictionary with processing statistics
    """
    api_client = APIClient(BASE_API_URL)
    processor = BillProcessor(api_client)
    
    stats = {
        "total": len(bills),
        "processed": 0,
        "success": 0,
        "failed": 0,
        "historical": 0
    }
    
    # Process bills in batches
    for i in range(0, len(bills), batch_size):
        batch = bills[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(len(bills)-1)//batch_size + 1} ({len(batch)} bills)")
        
        if parallel and len(batch) > 1:
            # Process batch in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(batch))) as executor:
                futures = {}
                for congress, bill_type, bill_number in batch:
                    future = executor.submit(processor.process_bill, congress, bill_type, bill_number)
                    futures[future] = (congress, bill_type, bill_number)
                
                for future in concurrent.futures.as_completed(futures):
                    congress, bill_type, bill_number = futures[future]
                    bill_is_historical = is_historical_bill(congress)
                    
                    try:
                        result = future.result()
                        stats["processed"] += 1
                        
                        if bill_is_historical:
                            stats["historical"] += 1
                        
                        if result["status"] == "success":
                            stats["success"] += 1
                            if bill_is_historical:
                                logger.info(f"Successfully processed historical bill {bill_type}{bill_number} (Congress: {congress})")
                            else:
                                logger.info(f"Successfully processed bill {bill_type}{bill_number}")
                        else:
                            stats["failed"] += 1
                            error_msg = result.get('error', 'Unknown error')
                            
                            # For historical bills, some errors are expected
                            if bill_is_historical and historical_mode:
                                if "sponsors" in error_msg or "cosponsors" in error_msg or "summaries" in error_msg:
                                    logger.warning(f"Expected limitation for historical bill {bill_type}{bill_number} (Congress: {congress}): {error_msg}")
                                else:
                                    logger.error(f"Failed to process historical bill {bill_type}{bill_number} (Congress: {congress}): {error_msg}")
                            else:
                                logger.error(f"Failed to process bill {bill_type}{bill_number}: {error_msg}")
                            
                    except Exception as e:
                        stats["processed"] += 1
                        stats["failed"] += 1
                        
                        if bill_is_historical:
                            stats["historical"] += 1
                            logger.error(f"Error processing historical bill {bill_type}{bill_number} (Congress: {congress}): {str(e)}")
                        else:
                            logger.error(f"Error processing bill {bill_type}{bill_number}: {str(e)}")
        else:
            # Process batch sequentially
            for congress, bill_type, bill_number in batch:
                bill_is_historical = is_historical_bill(congress)
                
                try:
                    result = processor.process_bill(congress, bill_type, bill_number)
                    stats["processed"] += 1
                    
                    if bill_is_historical:
                        stats["historical"] += 1
                    
                    if result["status"] == "success":
                        stats["success"] += 1
                        if bill_is_historical:
                            logger.info(f"Successfully processed historical bill {bill_type}{bill_number} (Congress: {congress})")
                    else:
                        stats["failed"] += 1
                        error_msg = result.get('error', 'Unknown error')
                        
                        # For historical bills, some errors are expected
                        if bill_is_historical and historical_mode:
                            if "sponsors" in error_msg or "cosponsors" in error_msg or "summaries" in error_msg:
                                logger.warning(f"Expected limitation for historical bill {bill_type}{bill_number} (Congress: {congress}): {error_msg}")
                            else:
                                logger.error(f"Failed to process historical bill {bill_type}{bill_number} (Congress: {congress}): {error_msg}")
                        else:
                            logger.error(f"Failed to process bill {bill_type}{bill_number}: {error_msg}")
                        
                except Exception as e:
                    stats["processed"] += 1
                    stats["failed"] += 1
                    
                    if bill_is_historical:
                        stats["historical"] += 1
                        logger.error(f"Error processing historical bill {bill_type}{bill_number} (Congress: {congress}): {str(e)}")
                    else:
                        logger.error(f"Error processing bill {bill_type}{bill_number}: {str(e)}")
        
        logger.info(f"Batch complete. Progress: {stats['processed']}/{stats['total']} bills processed.")
    
    return stats

def validate_and_get_missing_bills(limit: int = None, exclude_historical: bool = False) -> List[Tuple[str, str, str]]:
    """Run validation and return bills needing processing."""
    missing_details = check_missing_details()
    missing_enrichment = check_missing_enrichment()
    
    bills_needing_processing = set()
    
    # Add bills missing details
    for category_name, category in missing_details.items():
        if category_name == 'historical_bills':
            continue  # Skip the historical bills list
            
        for bill_number, congress in category:
            if exclude_historical and is_historical_bill(congress):
                continue
                
            bill_type, bill_num = parse_bill_number(bill_number)
            bills_needing_processing.add((congress, bill_type, bill_num))
    
    # Add bills missing enrichment
    for category in missing_enrichment.values():
        for bill_number, congress in category:
            if exclude_historical and is_historical_bill(congress):
                continue
                
            bill_type, bill_num = parse_bill_number(bill_number)
            bills_needing_processing.add((congress, bill_type, bill_num))
    
    # Convert to list and apply limit if needed
    result = list(bills_needing_processing)
    if limit and len(result) > limit:
        result = result[:limit]
    
    return result

def main():
    parser = argparse.ArgumentParser(description='Batch processor for Congress.gov bill data')
    parser.add_argument('--congress', help='Process all bills from a specific Congress')
    parser.add_argument('--status', help='Process bills with a specific status (e.g., "Introduced", "In Committee")')
    parser.add_argument('--missing', choices=['text_versions', 'summary', 'actions', 'cosponsors', 'all'], 
                        help='Process bills missing specific data')
    parser.add_argument('--batch-size', type=int, default=10, help='Number of bills to process in each batch')
    parser.add_argument('--limit', type=int, help='Maximum number of bills to process')
    parser.add_argument('--parallel', action='store_true', help='Process bills in parallel')
    parser.add_argument('--validate', action='store_true', help='Run validation and process missing bills')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without actually processing')
    parser.add_argument('--historical', action='store_true', 
                        help='Enable specialized processing for historical bills (6th-42nd Congresses)')
    parser.add_argument('--exclude-historical', action='store_true',
                        help='Exclude historical bills from processing')
    args = parser.parse_args()
    
    try:
        bills_to_process = []
        
        if args.historical and args.exclude_historical:
            logger.error("Cannot use both --historical and --exclude-historical flags")
            return
        
        if args.validate:
            # Run validation and get bills needing processing
            logger.info("Running validation to find bills needing processing")
            bills_to_process = validate_and_get_missing_bills(args.limit, args.exclude_historical)
            logger.info(f"Found {len(bills_to_process)} bills needing processing")
            
        elif args.historical and not args.congress:
            # Get all historical bills (6th-42nd Congresses)
            logger.info("Fetching historical bills (6th-42nd Congresses)")
            bills_to_process = get_historical_bills(args.limit)
            logger.info(f"Found {len(bills_to_process)} historical bills")
            
        elif args.congress:
            # Check if this is a historical Congress
            try:
                congress_num = int(args.congress)
                is_historical = 6 <= congress_num <= 42
                if is_historical:
                    logger.info(f"Processing historical Congress: {args.congress} ({1799 + (congress_num - 6) * 2}-{1801 + (congress_num - 6) * 2})")
            except ValueError:
                is_historical = False
            
            # Get all bills from a specific Congress
            bill_numbers = get_bills_by_congress(args.congress, args.limit)
            for bill_number in bill_numbers:
                bill_type, bill_num = parse_bill_number(bill_number)
                bills_to_process.append((args.congress, bill_type, bill_num))
                
        elif args.status:
            # Get bills with a specific status
            bill_tuples = get_bills_by_status(args.status, args.limit)
            for bill_number, congress in bill_tuples:
                if args.exclude_historical and is_historical_bill(congress):
                    continue
                bill_type, bill_num = parse_bill_number(bill_number)
                bills_to_process.append((congress, bill_type, bill_num))
                
        elif args.missing:
            # Get bills missing specific data
            if args.missing == 'all':
                # Get bills missing any type of data
                for data_type in ['text_versions', 'summary', 'actions', 'cosponsors']:
                    bill_tuples = get_bills_missing_data(data_type, args.limit, args.exclude_historical)
                    for bill_number, congress in bill_tuples:
                        bill_type, bill_num = parse_bill_number(bill_number)
                        bills_to_process.append((congress, bill_type, bill_num))
                        
                # Remove duplicates
                bills_to_process = list(set(bills_to_process))
                
                # Apply limit if specified
                if args.limit and len(bills_to_process) > args.limit:
                    bills_to_process = bills_to_process[:args.limit]
            else:
                # Get bills missing a specific type of data
                bill_tuples = get_bills_missing_data(args.missing, args.limit, args.exclude_historical)
                for bill_number, congress in bill_tuples:
                    bill_type, bill_num = parse_bill_number(bill_number)
                    bills_to_process.append((congress, bill_type, bill_num))
        
        if not bills_to_process:
            logger.warning("No bills found to process based on the given criteria")
            return
        
        # Count historical bills
        historical_count = sum(1 for congress, _, _ in bills_to_process if is_historical_bill(congress))
        modern_count = len(bills_to_process) - historical_count
        
        logger.info(f"Found {len(bills_to_process)} bills to process ({historical_count} historical, {modern_count} modern)")
        
        if args.dry_run:
            logger.info("Dry run - would process the following bills:")
            for congress, bill_type, bill_number in bills_to_process:
                historical_note = " (HISTORICAL)" if is_historical_bill(congress) else ""
                logger.info(f"  {congress} {bill_type}{bill_number}{historical_note}")
            return
        
        # Process bills in batches
        logger.info(f"Processing {len(bills_to_process)} bills in batches of {args.batch_size}")
        logger.info(f"Parallel processing: {'Enabled' if args.parallel else 'Disabled'}")
        logger.info(f"Historical mode: {'Enabled' if args.historical else 'Disabled'}")
        
        stats = process_bill_batch(bills_to_process, args.batch_size, args.parallel, args.historical)
        
        logger.info("Batch processing complete")
        logger.info(f"Total bills: {stats['total']}")
        logger.info(f"Successfully processed: {stats['success']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info(f"Historical bills processed: {stats['historical']}")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
