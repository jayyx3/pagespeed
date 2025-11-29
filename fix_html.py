#!/usr/bin/env python3
"""Fix HTML issues: remove duplicate preload tags, empty noscript tags, and fix typos"""

import re

# Read the HTML file
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

print(f"Original size: {len(html)} bytes")

# Fix 1: Change as_="image" to as="image" (fix typo)
html = html.replace('as_="image"', 'as="image"')
html = html.replace('as_="style"', 'as="style"')
print("✓ Fixed as_ attribute typos")

# Fix 2: Remove duplicate preload tags for the Christmas SVG
# Keep only ONE preload tag for the LCP image
pattern = r'(<link as="image" href="images/gamcore-christmas-2024-chimney-blonde\.svg" rel="preload"/>)+'
html = re.sub(pattern, r'\1', html)
print("✓ Removed duplicate LCP preload tags")

# Fix 3: Remove all empty <noscript></noscript> tags
html = html.replace('<noscript></noscript>', '')
print("✓ Removed empty noscript tags")

# Fix 4: Remove the leftover PNG file cleanup (we'll do that separately)

# Write the cleaned HTML
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Final size: {len(html)} bytes")
print(f"Savings: {len(html) - len(open('index.html', 'r', encoding='utf-8').read())} bytes")
