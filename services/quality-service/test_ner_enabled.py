#!/usr/bin/env python3
"""
Test the enabled NER extraction function
"""
import re
from typing import Dict, List
import json

def extract_ner_entities(text: str) -> Dict[str, List[str]]:
    """Extract Named Entity Recognition data: Persons, Organizations, Locations, Dates, Others"""
    if not text or len(text) < 50:
        return {
            'persons': [],
            'organizations': [],
            'locations': [],
            'dates': [],
            'others': []
        }
    
    # Clean and limit text for processing
    text = text[:3000]  # Limit for performance
    
    entities = {
        'persons': [],
        'organizations': [],
        'locations': [],
        'dates': [],
        'others': []
    }
    
    try:
        # Extract potential person names (Title + Name pattern)
        person_patterns = [
            r'\b(President|Prime Minister|Minister|CEO|Director|Pope|Doctor|Dr\.?|Mr\.?|Mrs\.?|Ms\.?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:said|announced|declared|stated|confirmed)\b',
        ]
        
        for pattern in person_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle title + name matches
                    if len(match) == 2 and match[1]:
                        name = match[1].strip()
                        if len(name) > 3 and name not in entities['persons']:
                            entities['persons'].append(name)
                    # Handle direct name matches
                    elif len(match) == 1:
                        name = match[0].strip()
                        if len(name) > 3 and name not in entities['persons']:
                            entities['persons'].append(name)
                else:
                    name = match.strip()
                    if len(name) > 3 and name not in entities['persons']:
                        entities['persons'].append(name)
        
        # Extract organizations
        org_patterns = [
            r'\b(Catholic Church|Associated Press|Reuters|CNN|BBC|Fox News|ABC News|NBC News|CBS News|Sky News|Guardian|Washington Post|New York Times)\b',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Corporation|Corp|Company|Co|Inc|Ltd|University|College|Hospital|Department|Ministry|Agency)\b',
            r'\b(NATO|EU|UN|FBI|CIA|NSA|WHO|NASA|IMF|WTO)\b',
        ]
        
        for pattern in org_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                org = match.strip()
                if len(org) > 2 and org not in entities['organizations']:
                    entities['organizations'].append(org)
        
        # Extract locations (simplified for testing)
        location_patterns = [
            r'\b(Washington|London|Paris|Berlin|Tokyo|Beijing|Moscow|Rome|Madrid|Brussels|Geneva|New York|Los Angeles|Chicago|Houston|Minneapolis|Minnesota|Dublin|Stockholm)\b',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z][a-z]+|[A-Z]{2})\b',  # City, State pattern
            r'\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # "in Location"
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    for part in match:
                        if part and len(part) > 2 and part not in entities['locations']:
                            entities['locations'].append(part)
                else:
                    location = match.strip()
                    if len(location) > 2 and location not in entities['locations']:
                        entities['locations'].append(location)
        
        # Extract dates
        date_patterns = [
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{4}-\d{2}-\d{2}\b',
            r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                date = match.strip()
                if date and date not in entities['dates']:
                    entities['dates'].append(date)
        
        # Remove duplicates and limit results
        for key in entities:
            entities[key] = list(set(entities[key]))[:10]  # Limit to 10 entities each
            
    except Exception as e:
        print(f"Error in NER extraction: {str(e)}")
        # Return empty results if extraction fails
        return {
            'persons': [],
            'organizations': [],
            'locations': [],
            'dates': [],
            'others': []
        }
    
    return entities

def test_ner_with_sample_articles():
    """Test NER with sample article content"""
    
    sample_articles = [
        {
            'title': 'Teen influencer becomes Catholic Church\'s 1st millennial saint',
            'text': 'Pope Leo XIV has declared a 15-year-old computer whiz the Catholic Church\'s first millennial saint. The announcement was made in Vatican City on September 7, 2025. Cardinal Martinez said the decision was unprecedented.'
        },
        {
            'title': 'Republican condemns Vance for despicable comments on Venezuela',
            'text': 'Vice-President JD Vance speaks to the press after paying his respects to victims of the Annunciation Catholic church shooting in Minneapolis, Minnesota, on 3 September. Photograph: Alex Wroblewski/AFP'
        },
        {
            'title': 'Sky News tracks down woman at centre of hit-and-run investigation',
            'text': 'Sky News has tracked down the woman at the centre of a hit-and-run investigation in London. The incident occurred on Tuesday near Westminster Bridge. Police confirmed the investigation is ongoing.'
        },
        {
            'title': 'President Trump doubles down on crackdowns',
            'text': 'President Trump announced new policies during a press conference in Washington DC on January 15, 2025. The Associated Press and Reuters reported on the developments. NATO officials expressed concern.'
        }
    ]
    
    print("Testing NER extraction with sample articles...\n")
    
    for i, article in enumerate(sample_articles, 1):
        print(f"--- Article {i} ---")
        print(f"Title: {article['title']}")
        print(f"Text: {article['text'][:100]}...")
        
        try:
            entities = extract_ner_entities(article['text'])
            print(f"✓ NER extraction successful!")
            
            for entity_type, entity_list in entities.items():
                if entity_list:
                    print(f"  {entity_type.title()}: {entity_list}")
                else:
                    print(f"  {entity_type.title()}: (none found)")
                    
        except Exception as e:
            print(f"✗ NER extraction failed: {e}")
        
        print()

if __name__ == "__main__":
    test_ner_with_sample_articles()
    print("NER testing complete!")