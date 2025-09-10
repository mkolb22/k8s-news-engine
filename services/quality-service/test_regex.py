#!/usr/bin/env python3
"""
Test script to verify regex patterns work correctly
"""
import re

def test_extract_key_entities():
    """Test the extract_key_entities method patterns"""
    
    # Sample text with potential problematic content
    sample_text = """
    Breaking news from Reuters and Associated Press. 
    This is a test article about Ukraine and Russia.
    Published on 2025-01-01. 
    Recommended stories below.
    Photo by Getty Images.
    (AP) contributed to this report.
    View 25 comments here.
    """
    
    print("Testing extract_key_entities patterns...")
    print(f"Sample text: {sample_text[:100]}...")
    
    # Test metadata patterns (currently commented out in main.py)
    metadata_patterns = [
        r'published on.*?\n',
        r'recommended stories.*?\n', 
        r'related stories.*?\n',
        r'image.*?getty.*?\n',
        r'photograph.*?\n',
        r'(ap|reuters|afp).*?contributed.*?\n',
        r'view.*?comments.*?\n',
        r'read more.*?\n',
        r'click here.*?\n'
    ]
    
    text = sample_text[:2000]  # Limit for performance
    
    # Test each metadata pattern individually
    for i, pattern in enumerate(metadata_patterns):
        try:
            result = re.sub(pattern, '', text, flags=re.IGNORECASE)
            print(f"✓ Pattern {i+1} works: {pattern}")
        except Exception as e:
            print(f"✗ Pattern {i+1} failed: {pattern} - Error: {e}")
    
    # Test entity extraction pattern
    try:
        pattern = r'\b([A-Z][a-z]+)\b'
        matches = re.findall(pattern, text)
        print(f"✓ Entity pattern works: Found {len(matches)} entities")
        print(f"  Entities: {matches[:5]}")  # Show first 5
    except Exception as e:
        print(f"✗ Entity pattern failed: {e}")
    
    # Test title keyword patterns
    try:
        title = "Breaking news about Ukraine and Russia conflict"
        title_words = set(re.findall(r'\b[a-z]{3,}\b', title.lower()))
        print(f"✓ Title pattern works: Found {len(title_words)} words")
        print(f"  Words: {list(title_words)}")
    except Exception as e:
        print(f"✗ Title pattern failed: {e}")

def test_problematic_text():
    """Test with text that might cause regex issues"""
    
    # Text with potential regex-breaking characters
    problematic_texts = [
        "Text with (unmatched parenthesis",
        "Text with unmatched) parenthesis",
        "Text with [brackets] and (parentheses)",
        "Text with special chars: $^*+?{}[]\\|",
        "Text with newlines\nand more\nlines",
        "Text" * 100,  # Very long text
    ]
    
    print("\nTesting with potentially problematic texts...")
    
    pattern = r'\b([A-Z][a-z]+)\b'
    
    for i, text in enumerate(problematic_texts):
        try:
            matches = re.findall(pattern, text)
            print(f"✓ Problematic text {i+1} handled successfully")
        except Exception as e:
            print(f"✗ Problematic text {i+1} failed: {e}")

if __name__ == "__main__":
    test_extract_key_entities()
    test_problematic_text()
    print("\nRegex testing complete!")