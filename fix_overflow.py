import sys

def replace_in_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in replacements:
        content = content.replace(old, new)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

base_replacements = [
    ('width: 100vw !important;', 'width: 100% !important;'),
    ('width: 100vw;', 'width: 100%;'),
    ('margin-left: calc(-20px); /* يكسر الـ padding بتاع main */', 'margin-left: 0;'),
    ('margin-right: calc(-20px);', 'margin-right: 0;'),
    ('width: calc(100% + 40px);', 'width: 100%;')
]

replace_in_file('templates/base.html', base_replacements)

product_detail_replacements = [
    ('width: 100vw;', 'width: 100%;')
]

replace_in_file('store/templates/store/product_detail.html', product_detail_replacements)

print("CSS Fixed successfully!")
