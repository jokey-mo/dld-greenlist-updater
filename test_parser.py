#!/usr/bin/env python3
"""
Test script to verify HTML parsing functionality
"""

import sys
import os
sys.path.append('.')

from app import HTMLParser

def test_parsing():
    """Test the HTML parsing with the provided file"""
    html_file = "Dubai Brokers - LILIIA IBRAGIMOVA.html"
    
    if not os.path.exists(html_file):
        print(f"❌ HTML file '{html_file}' not found")
        return False
    
    print(f"📄 Testing HTML parsing with: {html_file}")
    
    try:
        brokers = HTMLParser.parse_html_file(html_file)
        print(f"✅ Successfully parsed {len(brokers)} brokers")
        
        if brokers:
            print("\n📋 Sample broker data:")
            sample = brokers[0]
            for key, value in sample.items():
                print(f"  {key}: {value}")
            
            print(f"\n📊 Statistics:")
            print(f"  Total brokers: {len(brokers)}")
            print(f"  Brokers with email: {len([b for b in brokers if b['email']])}")
            print(f"  Brokers with phone: {len([b for b in brokers if b['phone']])}")
            
            # Show unique service categories
            categories = set(b['service_category'] for b in brokers if b['service_category'])
            print(f"  Service categories: {len(categories)}")
            for cat in sorted(categories):
                print(f"    - {cat}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error parsing HTML: {e}")
        return False

if __name__ == "__main__":
    test_parsing()
