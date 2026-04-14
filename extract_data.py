import re
import os

input_path = 'anasScreenDB_mysql.sql'
output_path = 'anasScreenDB_data_only.sql'

print(f"Robustly extracting DATA ONLY from {input_path}...")

with open(input_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Header
header = [
    'SET FOREIGN_KEY_CHECKS = 0;',
    "SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';",
    'SET NAMES utf8mb4;',
    ''
]

# regex to find all INSERT statements (including multi-line)
# It starts with INSERT INTO and ends with ); followed by optional newline
insert_pattern = re.compile(r'INSERT INTO.*?\);', re.DOTALL)

matches = insert_pattern.findall(content)
print(f"Found {len(matches)} insert statements.")

with open(output_path, 'w', encoding='utf-8', newline='\n') as f_out:
    for item in header:
        f_out.write(item + '\n')
    
    for statement in matches:
        # 1. Use INSERT IGNORE
        statement = statement.replace('INSERT INTO', 'INSERT IGNORE INTO', 1)
        
        # 2. Safe Identifier Backticking
        # This regex matches 'strings' and "identifiers". 
        # It only replaces the "identifiers" part.
        def safe_backtick(text):
            # Group 1: full match (string or quoted ident)
            # Group 2: the identifier inside double quotes (if matched)
            pattern = r"('(?:[^']|'')*'|\"([a-zA-Z0-9_]+)\")"
            def replacer(match):
                if match.group(2):
                    return "`" + match.group(2) + "`"
                return match.group(1)
            return re.sub(pattern, replacer, text)
        
        statement = safe_backtick(statement)

        # 3. Convert PostgreSQL boolean literals to MySQL integers (1/0)
        # We handle this carefully to avoid affecting words inside strings
        # But since we've already handled identifiers, we can be a bit more global 
        # AS LONG AS we avoid strings. Let's use the same "safe" approach.
        def safe_booleans(text):
            pattern = r"('(?:[^']|'')*'|\btrue\b|\bfalse\b)"
            def replacer(match):
                word = match.group(0).lower()
                if word == 'true': return '1'
                if word == 'false': return '0'
                return match.group(0)
            return re.sub(pattern, replacer, text, flags=re.IGNORECASE)
            
        statement = safe_booleans(statement)

        # 4. Restore JSON quotes
        # Some sources have backticks inside JSON strings (corrupted). 
        # We find single-quoted strings and swap backticks inside them back to double quotes.
        def safe_restore_quotes(text):
            pattern = r"('(?:[^']|'')*')"
            def replacer(match):
                s = match.group(1)
                if '`' in s:
                    return s.replace('`', '"')
                return s
            return re.sub(pattern, replacer, text)
            
        statement = safe_restore_quotes(statement)
        
        # 5. Strip Timezone offsets (+03) from timestamps
        statement = re.sub(r"(\'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?)\+\d{2}\'", r"\1'", statement)
        
        # 5. Fix JSON escaping (Double backslashes inside JSON strings)
        def fix_json_esc(match):
            s = match.group(0)
            return s.replace('\\n', '\\\\n').replace('\\r', '\\\\r').replace('\\t', '\\\\t')
        
        statement = re.sub(r'\'\{.*\}\ heat\'', fix_json_esc, statement) # Wait, my previous regex was better
        statement = re.sub(r'\'\{.*\}\'', fix_json_esc, statement)
        
        f_out.write(statement + '\n')

    # Footer
    f_out.write('\nSET FOREIGN_KEY_CHECKS = 1;\n')

print(f"Success! Data-only file created: {output_path}")
