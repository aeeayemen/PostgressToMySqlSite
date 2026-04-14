import re
import os
import sys

def fix_sql_content(content):
    # Safe Identifier Backticking: protects single-quoted strings
    def safe_backtick(text):
        pattern = r"('(?:[^']|'')*'|\"([a-zA-Z0-9_]+)\")"
        def replacer(match):
            if match.group(2):
                return "`" + match.group(2) + "`"
            return match.group(1)
        return re.sub(pattern, replacer, text)

    # Safe Boolean Conversion: protects single-quoted strings
    def safe_booleans(text):
        pattern = r"('(?:[^']|'')*'|\btrue\b|\bfalse\b)"
        def replacer(match):
            word = match.group(0).lower()
            if word == 'true': return '1'
            if word == 'false': return '0'
            return match.group(0)
        return re.sub(pattern, replacer, text, flags=re.IGNORECASE)

    # Safe Restoration: fix corrupted JSON strings that have backticks instead of double quotes
    def safe_restore_quotes(text):
        pattern = r"('(?:[^']|'')*')"
        def replacer(match):
            s = match.group(1)
            if '`' in s:
                return s.replace('`', '"')
            return s
        return re.sub(pattern, replacer, text)

    content = safe_backtick(content)
    content = safe_booleans(content)
    content = safe_restore_quotes(content)
    
    # Ensure INSERT IGNORE
    content = content.replace('INSERT INTO', 'INSERT IGNORE INTO')
    
    # Remove TOC metadata
    content = re.sub(r'-- TOC entry.*', '', content)
    
    return content

def process_file(input_file, output_file):
    print(f"Processing {input_file} -> {output_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = f.read()
    
    fixed_data = fix_sql_content(data)
    
    with open(output_file, 'w', encoding='utf-8', newline='\n') as f:
        f.write(fixed_data)
    print("Done.")

if __name__ == "__main__":
    # If arguments are provided, use them. Otherwise use defaults.
    if len(sys.argv) > 2:
        process_file(sys.argv[1], sys.argv[2])
    else:
        # Default behavior: fix the main files
        process_file('anasDb_mysql.sql', 'anasDb_mysql_fixed.sql')
        process_file('anasScreenDB_mysql.sql', 'anasScreenDB_mysql_fixed.sql')
