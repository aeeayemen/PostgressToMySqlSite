import os
import re

input_path = 'anasDb_mysql_ready.sql'
output_path = 'anasDb_mysql_fixed.sql'

print(f"Adjusting {input_path} to avoid Primary Key collisions...")
with open(input_path, 'r', encoding='utf-8') as f_in:
    lines = f_in.readlines()

with open(output_path, 'w', encoding='utf-8', newline='\n') as f_out:
    for line in lines:
        # 1. Remove comments
        if line.strip().startswith('--'):
            continue
        
        # 2. Skip PRIMARY KEY additions (Fix for error #1068)
        # Since tables already have PKs, we don't want to try adding them again.
        if 'ADD' in line and 'PRIMARY KEY' in line:
            continue

        # 3. Fix JSON escaping
        if 'INSERT INTO d_services_serviceversion' in line:
            line = line.replace('\\n', '\\\\n').replace('\\r', '\\\\r').replace('\\t', '\\\\t')
        
        # 4. Use INSERT IGNORE for duplicates
        if line.startswith('INSERT INTO'):
            line = line.replace('INSERT INTO', 'INSERT IGNORE INTO', 1)
            
        f_out.write(line)

print(f"Modification complete. Use {output_path}. Primary Key additions have been removed to avoid #1068.")
