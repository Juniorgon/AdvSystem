#!/usr/bin/env python3
"""
Script to update remaining foreign key columns from String to UUID in database.py
"""

import re

def update_foreign_keys():
    # Read the current file
    with open('/app/backend/database.py', 'r') as f:
        content = f.read()
    
    # Replace all remaining String foreign keys with UUID
    replacements = [
        (r'branch_id = Column\(String, ForeignKey\("branches\.id"\)', 'branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id")'),
        (r'client_id = Column\(String, ForeignKey\("clients\.id"\)', 'client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id")'),
        (r'process_id = Column\(String, ForeignKey\("processes\.id"\)', 'process_id = Column(UUID(as_uuid=True), ForeignKey("processes.id")'),
        (r'responsible_lawyer_id = Column\(String, ForeignKey\("lawyers\.id"\)', 'responsible_lawyer_id = Column(UUID(as_uuid=True), ForeignKey("lawyers.id")'),
        (r'lawyer_id = Column\(String, ForeignKey\("lawyers\.id"\)', 'lawyer_id = Column(UUID(as_uuid=True), ForeignKey("lawyers.id")'),
        (r'allowed_branch_ids = Column\(String', 'allowed_branch_ids = Column(Text')  # This should be Text for JSON
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Write back
    with open('/app/backend/database.py', 'w') as f:
        f.write(content)
    
    print("✅ All foreign keys updated to UUID")

if __name__ == "__main__":
    update_foreign_keys()