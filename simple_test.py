#!/usr/bin/env python3
"""
Simple test to check if the HTML parsing works
"""

from bs4 import BeautifulSoup
import os

def test_simple():
    html_file = "Dubai Brokers - LILIIA IBRAGIMOVA.html"
    
    if not os.path.exists(html_file):
        print(f"❌ HTML file '{html_file}' not found")
        print("Files in current directory:")
        for f in os.listdir('.'):
            if f.endswith('.html'):
                print(f"  📄 {f}")
        return
    
    print(f"📄 Found HTML file: {html_file}")
    
    with open(html_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    print(f"📊 File size: {len(content)} characters")
    
    soup = BeautifulSoup(content, 'html.parser')
    print(f"🔍 HTML parsed successfully")
    
    # Find table
    table = soup.find('table', class_='table-striped')
    if table:
        print("✅ Found table with class 'table-striped'")
        tbody = table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
            print(f"📋 Found {len(rows)} rows in table")
            
            if rows:
                # Show first row data
                cells = rows[0].find_all('td')
                print(f"📝 First row has {len(cells)} cells:")
                for i, cell in enumerate(cells[:8]):  # First 8 cells
                    text = cell.get_text().strip()
                    print(f"  Cell {i}: {text[:50]}...")
        else:
            print("❌ No tbody found in table")
    else:
        print("❌ No table with class 'table-striped' found")
        # Try to find any table
        tables = soup.find_all('table')
        print(f"Found {len(tables)} tables total")

if __name__ == "__main__":
    test_simple()
