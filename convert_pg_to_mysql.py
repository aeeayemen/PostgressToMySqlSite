#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys

def clean_pg_header(content):
    """
    Remove PostgreSQL pg_dump header/footer lines and SET commands.
    """
    lines = content.splitlines(keepends=True)
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('--'):
            if any(phrase in stripped.lower() for phrase in [
                'postgresql database dump',
                'dumped from database version',
                'dumped by pg_dump version',
                'started on',
                'completed on',
                'toc entry',
                'name: public; type: schema',
                'name: ',
                'schema: -; owner: -'
            ]):
                continue
            cleaned_lines.append(line)
            continue
        if stripped.upper().startswith('SET '):
            continue
        if re.match(r'^SELECT pg_catalog\.set_config', stripped, re.IGNORECASE):
            continue
        if line.rstrip().endswith('\\'):
            line = line.rstrip()[:-1] + '\n'
        cleaned_lines.append(line)
    return ''.join(cleaned_lines)

def fix_sql_file(input_path, output_path):
    with open(input_path, 'r', encoding='utf8') as f:
        content = f.read()

    # Remove PostgreSQL headers and SET commands
    content = clean_pg_header(content)

    # Remove "public." schema prefix from table names
    content = re.sub(r'\bpublic\.', '', content)

    # Fix CREATE TABLE statements
    def fix_create_table(match):
        table_def = match.group(0)

        # PostgreSQL → MySQL type mapping (including "with time zone")
        type_map = {
            r'\bboolean\b': 'TINYINT(1)',
            r'\btext\b': 'TEXT',
            r'\bcharacter varying\b': 'VARCHAR',
            r'\btimestamp(?:\([0-9]+\))? with time zone\b': 'DATETIME',
            r'\btimestamp(?:\([0-9]+\))? without time zone\b': 'DATETIME',
            r'\btimestamp\b': 'DATETIME',
            r'\btime with time zone\b': 'TIME',
            r'\btime without time zone\b': 'TIME',
            r'\buuid\b': 'VARCHAR(36)',
            r'\binet\b': 'VARCHAR(45)',
            r'\bbytea\b': 'BLOB',
            r'\bserial\b': 'INT AUTO_INCREMENT',
            r'\bbigserial\b': 'BIGINT AUTO_INCREMENT',
        }
        for pg_type, mysql_type in type_map.items():
            table_def = re.sub(pg_type, mysql_type, table_def, flags=re.IGNORECASE)

        # Add length to VARCHAR if missing
        table_def = re.sub(r'\bVARCHAR\b(?!\s*\()', 'VARCHAR(255)', table_def, flags=re.IGNORECASE)

        # Replace double-quoted identifiers with backticks
        table_def = re.sub(r'"([^"]+)"', r'`\1`', table_def)

        # Remove PostgreSQL CHECK constraints (MySQL may not support them inline)
        # This regex removes CONSTRAINT ... CHECK ( ... ) lines
        table_def = re.sub(r',\s*CONSTRAINT\s+[a-zA-Z_][a-zA-Z0-9_]*\s+CHECK\s*\([^)]*\)', '', table_def, flags=re.IGNORECASE)
        # Also remove standalone CHECK constraints without CONSTRAINT name
        table_def = re.sub(r',\s*CHECK\s*\([^)]*\)', '', table_def, flags=re.IGNORECASE)

        # Safely remove the trailing ');' at the end of the CREATE statement
        table_def = re.sub(r'\);$', '\n);', table_def, flags=re.MULTILINE)

        return table_def

    content = re.sub(
        r'CREATE TABLE\s+`?\w+`?\s*\(.*?\);\s*',
        fix_create_table,
        content,
        flags=re.DOTALL | re.IGNORECASE
    )

    # Fix INSERT statements (reserved words, timezones, JSON)
    reserved_words = {'order', 'group', 'user', 'table', 'key', 'select',
                      'insert', 'update', 'delete', 'from', 'where', 'limit'}

    def fix_insert_block(block):
        parts = re.split(r'\s+VALUES\s+', block, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) != 2:
            return block
        columns_part, values_part = parts
        for word in reserved_words:
            columns_part = re.sub(f'"{word}"', f'`{word}`', columns_part, flags=re.IGNORECASE)
        # Remove timezone from timestamps
        values_part = re.sub(r"('\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(\.\d+)?\+\d{2}(:\d{2})?'", r"\1'", values_part)
        # Fix JSON quotes
        def fix_json_quotes(match):
            val = match.group(0)
            if val.startswith("'{") or val.startswith("'["):
                return val.replace("`", '"')
            return val
        values_part = re.sub(r"'(?:[^'\\]|\\.)*'", fix_json_quotes, values_part)
        return columns_part + ' VALUES ' + values_part

    content = re.sub(
        r'INSERT\s+INTO\s+.*?VALUES\s+.*?(?=;|\nINSERT|\Z)',
        lambda m: fix_insert_block(m.group(0)),
        content,
        flags=re.DOTALL | re.IGNORECASE
    )

    with open(output_path, 'w', encoding='utf8') as f:
        f.write(content)

    print(f"✅ Conversion completed: {input_path} → {output_path}")

if __name__ == "__main__":
    DEFAULT_INPUT = 'C:/Users/user3/Desktop/Abood/anasDB.sql'
    DEFAULT_OUTPUT = 'C:/Users/user3/Desktop/Abood/tomysql/anasDb_mysql.sql'

    if len(sys.argv) == 3:
        input_file, output_file = sys.argv[1], sys.argv[2]
    elif len(sys.argv) == 2:
        input_file, output_file = sys.argv[1], DEFAULT_OUTPUT
        print(f"Using default output: {output_file}")
    else:
        print(f"Using default paths:\nInput : {DEFAULT_INPUT}\nOutput: {DEFAULT_OUTPUT}")
        input_file, output_file = DEFAULT_INPUT, DEFAULT_OUTPUT

    fix_sql_file(input_file, output_file)


