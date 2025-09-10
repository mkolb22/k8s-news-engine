#!/usr/bin/env python3
"""
Test NER extraction with actual article content from database
"""
import re
from typing import Dict, List

def extract_ner_entities(text: str) -> Dict[str, List[str]]:
    """Extract Named Entity Recognition data - same implementation as main.py"""
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
        return {
            'persons': [],
            'organizations': [],
            'locations': [],
            'dates': [],
            'others': []
        }
    
    return entities

def test_with_actual_content():
    """Test with actual article content from database"""
    
    # This is the actual content from article ID 667
    actual_text = """Zerohedge DebatesZeroHedge ReadsAlt-MarketAntiWar.comBitcoin MagazineBombthrowerBULLIONSTARCapitalist ExploitsChristophe BarraudDollar CollapseDr. Housing BubbleFinancial RevolutionistForexLiveGains Pains & CapitalGefiraGMG ResearchGold CoreImplode-ExplodeInsider PaperLibertarian InstituteLiberty BlitzkriegMax KeiserMises InstituteMish TalkNewsquawkOf Two MindsOil PriceOpen The BooksPeter SchiffPortfolio ArmorQTR's Fringe FinanceSafehavenSlope of HopeSpotGammaTF Metals ReportThe Automatic EarthT"""
    
    # Let's also test with a more typical news article
    typical_news = """President Biden announced new policies today in Washington during a press conference with NATO officials. The Associated Press reported that Secretary of State Johnson confirmed the decision. The meeting took place on Monday, January 15, 2025, at the White House in Washington DC."""
    
    print("Testing NER with actual Zerohedge article content:")
    print(f"Text: {actual_text[:200]}...")
    entities = extract_ner_entities(actual_text)
    print("Extracted entities:")
    for entity_type, entity_list in entities.items():
        if entity_list:
            print(f"  {entity_type.title()}: {entity_list}")
        else:
            print(f"  {entity_type.title()}: (none found)")
    
    print("\n" + "="*60)
    print("Testing NER with typical news article content:")
    print(f"Text: {typical_news}")
    entities = extract_ner_entities(typical_news)
    print("Extracted entities:")
    for entity_type, entity_list in entities.items():
        if entity_list:
            print(f"  {entity_type.title()}: {entity_list}")
        else:
            print(f"  {entity_type.title()}: (none found)")

if __name__ == "__main__":
    test_with_actual_content()