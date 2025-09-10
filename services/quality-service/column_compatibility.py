#!/usr/bin/env python3
"""
Database Column Compatibility Layer

Provides consistent outlet_name access across tables with different column schemas.
Handles the mapping between logical outlet_name and physical database columns.
"""

from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Define the actual physical column names for each table
# This maps logical 'outlet_name' to the actual database column
TABLE_COLUMN_MAPPING = {
    # Tables that use 'outlet' column (TEXT)
    'articles': 'outlet',
    'rss_feeds': 'outlet', 
    'outlet_reputation_scores': 'outlet',
    
    # Tables that use 'outlet_name' column (VARCHAR)
    'news_agency_reputation_metrics': 'outlet_name',
    'outlet_authority': 'outlet_name'
}

def get_outlet_column_for_table(table_name: str) -> str:
    """
    Get the actual database column name for outlet_name concept in a specific table.
    
    Args:
        table_name: Name of the database table
        
    Returns:
        The actual column name to use in SQL queries for this table
    """
    column = TABLE_COLUMN_MAPPING.get(table_name, 'outlet_name')  # Default to outlet_name
    logger.debug(f"Table {table_name} uses column '{column}' for outlet concept")
    return column

def build_standardized_query(base_query: str, table_aliases: Dict[str, str] = None) -> str:
    """
    Convert a query that uses logical 'outlet_name' references to use actual database columns.
    
    Args:
        base_query: SQL query using logical outlet_name references
        table_aliases: Dictionary mapping table aliases to table names
        
    Returns:
        Modified query with correct physical column names
        
    Example:
        Input:  "SELECT a.outlet_name FROM articles a"
        Output: "SELECT a.outlet FROM articles a"
    """
    if table_aliases is None:
        table_aliases = {}
    
    # For now, return the original query since our current queries already use correct columns
    # This function is prepared for future query standardization
    return base_query

def get_standardized_select_clause(table_name: str, alias: str = None) -> str:
    """
    Generate a standardized SELECT clause for outlet_name concept.
    
    Args:
        table_name: Database table name
        alias: Optional table alias
        
    Returns:
        SQL fragment like "a.outlet AS outlet_name" or "outlet_name"
    """
    physical_column = get_outlet_column_for_table(table_name)
    
    if alias:
        if physical_column == 'outlet_name':
            return f"{alias}.outlet_name"
        else:
            return f"{alias}.{physical_column} AS outlet_name"
    else:
        if physical_column == 'outlet_name':
            return "outlet_name"
        else:
            return f"{physical_column} AS outlet_name"

def get_standardized_where_clause(table_name: str, alias: str = None, 
                                 value_placeholder: str = "%s") -> str:
    """
    Generate a standardized WHERE clause for outlet_name filtering.
    
    Args:
        table_name: Database table name
        alias: Optional table alias
        value_placeholder: SQL placeholder for the value
        
    Returns:
        SQL fragment like "a.outlet = %s" or "outlet_name = %s"
    """
    physical_column = get_outlet_column_for_table(table_name)
    
    if alias:
        return f"{alias}.{physical_column} = {value_placeholder}"
    else:
        return f"{physical_column} = {value_placeholder}"

def get_standardized_join_condition(left_table: str, left_alias: str,
                                   right_table: str, right_alias: str) -> str:
    """
    Generate a standardized JOIN condition between tables on outlet_name concept.
    
    Args:
        left_table: Name of left table in join
        left_alias: Alias for left table
        right_table: Name of right table in join
        right_alias: Alias for right table
        
    Returns:
        SQL fragment like "a.outlet = b.outlet_name"
    """
    left_column = get_outlet_column_for_table(left_table)
    right_column = get_outlet_column_for_table(right_table)
    
    return f"{left_alias}.{left_column} = {right_alias}.{right_column}"

# Convenience functions for common table combinations

def get_articles_to_reputation_join() -> str:
    """Standard join condition: articles to news_agency_reputation_metrics"""
    return get_standardized_join_condition('articles', 'a', 'news_agency_reputation_metrics', 'narm')

def get_rss_feeds_to_reputation_join() -> str:
    """Standard join condition: rss_feeds to news_agency_reputation_metrics"""
    return get_standardized_join_condition('rss_feeds', 'rf', 'news_agency_reputation_metrics', 'narm')

def get_articles_outlet_select() -> str:
    """Standard SELECT clause for articles outlet_name"""
    return get_standardized_select_clause('articles', 'a')

def get_reputation_outlet_select() -> str:
    """Standard SELECT clause for reputation metrics outlet_name"""
    return get_standardized_select_clause('news_agency_reputation_metrics', 'narm')

# Query validation helpers

def validate_query_compatibility(query: str) -> List[str]:
    """
    Validate that a query uses compatible column references.
    
    Args:
        query: SQL query to validate
        
    Returns:
        List of warnings/issues found
    """
    issues = []
    
    # Check for hardcoded column names that might be inconsistent
    if 'a.outlet_name' in query and 'FROM articles' in query:
        issues.append("Query uses 'a.outlet_name' but articles table uses 'outlet' column")
    
    if 'rf.outlet_name' in query and 'FROM rss_feeds' in query:
        issues.append("Query uses 'rf.outlet_name' but rss_feeds table uses 'outlet' column")
        
    return issues

if __name__ == "__main__":
    # Test the compatibility functions
    logging.basicConfig(level=logging.DEBUG)
    
    print("🧪 Testing Column Compatibility Functions")
    print("=" * 50)
    
    # Test column mapping
    for table in TABLE_COLUMN_MAPPING:
        column = get_outlet_column_for_table(table)
        print(f"{table:30} → {column}")
    
    print("\n📋 Testing SELECT clauses:")
    print(f"Articles:    {get_standardized_select_clause('articles', 'a')}")
    print(f"RSS Feeds:   {get_standardized_select_clause('rss_feeds', 'rf')}")
    print(f"Reputation:  {get_standardized_select_clause('news_agency_reputation_metrics', 'narm')}")
    
    print("\n🔗 Testing JOIN conditions:")
    print(f"Articles→Reputation: {get_articles_to_reputation_join()}")
    print(f"RSS→Reputation:      {get_rss_feeds_to_reputation_join()}")
    
    print("\n✅ Column compatibility layer ready!")