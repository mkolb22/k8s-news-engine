#!/usr/bin/env python3
"""
Test the full extract_key_entities method as implemented in main.py
"""
import re
from typing import Set

def extract_key_entities(text: str) -> Set[str]:
    """Extract key entities from article text - matches the current implementation"""
    if not text or len(text) < 50:
        return set()
    
    # Clean text first - remove obvious metadata (same as publisher)
    text = text[:2000]  # Limit for performance
    
    # Temporarily disable metadata patterns to isolate regex issue
    # metadata_patterns = [
    #     r'published on.*?\n',
    #     r'recommended stories.*?\n', 
    #     r'related stories.*?\n',
    #     r'image.*?getty.*?\n',
    #     r'photograph.*?\n',
    #     r'(ap|reuters|afp).*?contributed.*?\n',
    #     r'view.*?comments.*?\n',
    #     r'read more.*?\n',
    #     r'click here.*?\n'
    # ]
    
    # for pattern in metadata_patterns:
    #     try:
    #         text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    #     except Exception as e:
    #         print(f"Error in metadata pattern '{pattern}': {str(e)}")
    #         continue
    
    entities = set()
    
    # Extract proper nouns (single words only)
    pattern = r'\b([A-Z][a-z]+)\b'
    matches = re.findall(pattern, text)
    
    # Same comprehensive non-entities list as publisher
    non_entities = {
        'The', 'This', 'That', 'These', 'Those', 'There', 'Here', 'When', 'Where',
        'What', 'Who', 'Why', 'How', 'Monday', 'Tuesday', 'Wednesday', 'Thursday',
        'Friday', 'Saturday', 'Sunday', 'January', 'February', 'March', 'April',
        'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December',
        'New', 'First', 'Last', 'Next', 'Previous', 'Other', 'Another', 'Some', 'Many',
        'Most', 'Few', 'All', 'Both', 'Each', 'Every', 'Any', 'Several', 'Following',
        'According', 'However', 'Meanwhile', 'Moreover', 'Furthermore', 'Therefore',
        'Published On', 'Recommended Stories', 'Related Stories', 'Associated Press',
        'View', 'Comments', 'Share', 'Tweet', 'Facebook', 'Instagram', 'Twitter',
        'Getty', 'Images', 'Photo', 'Picture', 'Video', 'Audio', 'More', 'News',
        'Story', 'Article', 'Report', 'Update', 'Breaking', 'Live', 'Latest',
        'Today', 'Yesterday', 'Tomorrow', 'Now', 'Then', 'Soon', 'Later', 'Before',
        'After', 'During', 'While', 'Since', 'Until', 'Through', 'From', 'For',
        'At', 'In', 'On', 'By', 'With', 'Without', 'About', 'Against', 'Between',
        'Among', 'Through', 'During', 'Before', 'After', 'Above', 'Below', 'Up',
        'Down', 'Out', 'Off', 'Over', 'Under', 'Again', 'Further', 'Then', 'Once'
    }
    
    for match in matches:
        if match not in non_entities and len(match) > 3:
            entities.add(match.lower())
    
    return entities

def test_with_sample_texts():
    """Test with various sample texts"""
    
    sample_texts = [
        # Normal article text
        """
        Breaking news from Washington today. President Biden announced new policies regarding Ukraine and Russia. 
        The European Union has responded positively to these developments. NATO officials are meeting in Brussels.
        Published on January 1, 2025. Recommended stories below.
        """,
        
        # Text with potential regex issues
        """
        Article about (unmatched parenthesis in text. This contains special characters like $100 and 50% rates.
        Companies like Apple and Microsoft are involved. The CEO said "We're committed to innovation."
        View 25 comments here. Photo by Getty Images.
        """,
        
        # Text with problematic patterns
        """
        (AP) WASHINGTON - The Associated Press contributed to this report about ongoing investigations.
        Published on December 15, 2024. Related stories can be found below.
        Click here to read more about this developing story.
        """,
        
        # Very short text
        "Short text",
        
        # Empty text
        "",
        
        # Text with lots of metadata
        """
        Breaking: Major development
        Published on 2025-01-01 by Reuters
        Recommended stories:
        - Story 1
        - Story 2
        Related stories here
        Image courtesy of Getty Images
        Photograph by John Doe
        (AP) contributed to this report
        View 100 comments below
        Read more about this topic
        Click here for updates
        """
    ]
    
    print("Testing extract_key_entities with various sample texts...")
    
    for i, text in enumerate(sample_texts, 1):
        print(f"\n--- Test {i} ---")
        print(f"Text preview: {text[:100].strip()}...")
        
        try:
            entities = extract_key_entities(text)
            print(f"✓ Success: Found {len(entities)} entities")
            if entities:
                print(f"  Entities: {sorted(list(entities)[:10])}")  # Show first 10
        except Exception as e:
            print(f"✗ Failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_with_sample_texts()
    print("\nFull method testing complete!")