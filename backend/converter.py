import re
import os

def safe_backtick(text):
    # Group 1: full match (string or quoted ident)
    # Group 2: the identifier inside double quotes (if matched)
    pattern = r"('(?:[^']|'')*'|\"([a-zA-Z0-9_]+)\")"
    def replacer(match):
        if match.group(2):
            return "`" + match.group(2) + "`"
        return match.group(1)
    return re.sub(pattern, replacer, text)

def safe_booleans(text):
    pattern = r"('(?:[^']|'')*'|\btrue\b|\bfalse\b)"
    def replacer(match):
        word = match.group(0).lower()
        if word == 'true': return '1'
        if word == 'false': return '0'
        return match.group(0)
    return re.sub(pattern, replacer, text, flags=re.IGNORECASE)

def safe_restore_quotes(text):
    pattern = r"('(?:[^']|'')*')"
    def replacer(match):
        s = match.group(1)
        if '`' in s:
            return s.replace('`', '"')
        return s
    return re.sub(pattern, replacer, text)

def clean_sql(content):
    content = safe_backtick(content)
    content = safe_booleans(content)
    content = safe_restore_quotes(content)
    content = content.replace('INSERT INTO', 'INSERT IGNORE INTO')
    content = re.sub(r'-- TOC entry.*', '', content)
    return content

def extract_data_only(content):
    # Header for the data-only file
    header = "SET FOREIGN_KEY_CHECKS = 0;\nSET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';\nSET NAMES utf8mb4;\n\n"
    
    # Regex to find all INSERT statements
    insert_pattern = re.compile(r'INSERT INTO.*?\);', re.DOTALL)
    matches = insert_pattern.findall(content)
    
    processed_statements = []
    for statement in matches:
        # standard clean for each statement
        statement = statement.replace('INSERT INTO', 'INSERT IGNORE INTO', 1)
        statement = safe_backtick(statement)
        statement = safe_booleans(statement)
        statement = safe_restore_quotes(statement)
        # Strip Timezone offsets
        statement = re.sub(r"(\'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?)\+\d{2}\'", r"\1'", statement)
        
        # Fix JSON escaping
        def fix_json_esc(match):
            s = match.group(0)
            return s.replace('\\n', '\\\\n').replace('\\r', '\\\\r').replace('\\t', '\\\\t')
        statement = re.sub(r'\'\{.*\}\ heat\'', fix_json_esc, statement)
        statement = re.sub(r'\'\{.*\}\'', fix_json_esc, statement)
        
        processed_statements.append(statement)
    
    footer = "\nSET FOREIGN_KEY_CHECKS = 1;\n"
    return header + '\n'.join(processed_statements) + footer
