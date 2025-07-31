#!/usr/bin/env python3
"""
Initialize the database and process the initial HTML file
"""

import os
from app import app, db, BrokerService

def initialize_database():
    """Initialize the database and process the existing HTML file"""
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created")
        
        # Check if we have the HTML file
        html_file = "Dubai Brokers - LILIIA IBRAGIMOVA.html"
        if os.path.exists(html_file):
            print(f"📄 Processing initial HTML file: {html_file}")
            
            try:
                result = BrokerService.process_html_upload(html_file)
                print(f"✅ Successfully processed HTML file:")
                print(f"   📊 Total processed: {result['total_processed']}")
                print(f"   🆕 New brokers: {result['new_count']}")
                print(f"   🔄 Updated brokers: {result['updated_count']}")
                
                # Show some sample new brokers
                if result['new_brokers']:
                    print("\n📋 Sample new brokers:")
                    for i, broker in enumerate(result['new_brokers'][:5]):
                        print(f"   {i+1}. {broker.name} - {broker.email}")
                    
                    if len(result['new_brokers']) > 5:
                        print(f"   ... and {len(result['new_brokers']) - 5} more")
                
            except Exception as e:
                print(f"❌ Error processing HTML file: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"⚠️  HTML file not found: {html_file}")
            print("   You can upload HTML files using the web interface")

if __name__ == "__main__":
    initialize_database()
