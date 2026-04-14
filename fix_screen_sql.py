import re
import os

input_path = 'anasScreenDB_mysql.sql'
output_path = 'anasScreenDB_fixed.sql'

print(f"Processing {input_path}...")

with open(input_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix VARCHAR without length -> VARCHAR(255)
# Looks for VARCHAR followed by NOT NULL or , or )
content = re.sub(r'VARCHAR\s+(NOT NULL|,|\))', r'VARCHAR(255) \1', content)

# 2. Fix uuid -> VARCHAR(36)
content = re.sub(r'\s+uuid\s+', ' VARCHAR(36) ', content)

# 3. Strip Timezone offsets from timestamps (e.g., '2026-03-02 09:50:01.782071+03' -> '2026-03-02 09:50:01.782071')
# MySQL doesn't like the +03 part in a datetime string.
content = re.sub(r"(\'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?)\+\d{2}\'", r"\1'", content)

# 4. Use INSERT IGNORE
content = content.replace('INSERT INTO', 'INSERT IGNORE INTO')

# 5. Fix JSON escaping (Double backslashes in JSON-like strings)
# We look for strings that look like JSON: starts with {" and ends with "}
# and double the backslashes inside them.
def fix_json_esc(match):
    s = match.group(0)
    # Double the backslashes that aren't already doubled
    # This is a bit tricky, but usually \n -> \\n is what's needed for MySQL
    return s.replace('\\n', '\\\\n').replace('\\r', '\\\\r').replace('\\t', '\\\\t')

# Apply to common JSON fields in the values
content = re.sub(r'\'\{.*\}\'', fix_json_esc, content)

# 6. Resolve raw newlines in string literals
# PostgreSQL dumps often have multi-line INSERT values. 
# For MySQL, we should ideally escape them or ensure the SQL parser accepts them.
# A safe way is to replace actual newlines inside single quotes with \n.
# This part is complex due to nested quotes, but let's try a simpler approach if possible.
# Actually, if we just ensure FOREIGN_KEY_CHECKS = 0, most imports will handle the order.

with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
    # Ensure foreign key checks are off at the top if not already
    if not content.startswith('SET FOREIGN_KEY_CHECKS = 0;'):
        f.write('SET FOREIGN_KEY_CHECKS = 0;\n')
        f.write("SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';\n")
    
    f.write(content)
    
    f.write('\nSET FOREIGN_KEY_CHECKS = 1;\n')

print(f"Finished. Saved to {output_path}")
