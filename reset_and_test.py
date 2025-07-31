#!/usr/bin/env python3
"""
Reset scr    print("✅ Python cache cleared")
    
    # Verify reset
    print("\n🔍 Verification:")
    if not os.path.exists('clients.db') and not os.path.exists('instance/clients.db'):
        print("   ✅ No database files found")
    else:
        remaining_dbs = []
        if os.path.exists('clients.db'):
            remaining_dbs.append('clients.db')
        if os.path.exists('instance/clients.db'):
            remaining_dbs.append('instance/clients.db')
        print(f"   ⚠️ Database files still exist: {', '.join(remaining_dbs)}")
    
    upload_files = os.listdir('uploads') if os.path.exists('uploads') else []
    if not upload_files:
        print("   ✅ Uploads directory is empty")
    else:
        print(f"   ⚠️ Files still in uploads: {len(upload_files)} files")
    
    print("\n🎯 Application reset complete!")
    print("📊 Expected behavior after first upload:")
    print("   - Total Clients = Number of unique records in HTML")
    print("   - New Clients = Same as Total Clients (all should be new)")
    print("   - Duplicates within same file should be skipped")
    print("\n🚀 You can now run the application and test with your HTML file")lear all data and test the duplicate detection fix
"""
import os
import sys

def reset_application():
    print("🗑️ Resetting application data...")
    
    # Stop any running Flask processes
    os.system("pkill -f 'python app.py' 2>/dev/null || true")
    print("🛑 Stopped running Flask processes")
    
    # Remove database (check both locations)
    database_paths = ['clients.db', 'instance/clients.db']
    database_removed = False
    
    for db_path in database_paths:
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"✅ Database cleared: {db_path}")
            database_removed = True
    
    if not database_removed:
        print("ℹ️ No database found to remove")
    
    # Clear uploads
    if os.path.exists('uploads'):
        os.system("rm -rf uploads/*")
        print("✅ Uploads directory cleared")
    os.makedirs('uploads', exist_ok=True)
    
    # Clear Python cache
    os.system("find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true")
    os.system("find . -name '*.pyc' -delete")
    print("✅ Python cache cleared")
    
    print("\n🎯 Application reset complete!")
    print("📊 Expected behavior after first upload:")
    print("   - Total Clients = Number of unique records in HTML")
    print("   - New Clients = Same as Total Clients (all should be new)")
    print("   - Duplicates within same file should be skipped")
    print("\n🚀 You can now run the application and test with your HTML file")

if __name__ == "__main__":
    reset_application()
