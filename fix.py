import codecs

with codecs.open('store/templates/store/index.html', 'r', 'utf-8') as f:
    content = f.read()

target = '''                    <div class="slide-image-wrapper">
                        {% if slide.image %}
                        <img src="{{ slide.image.url }}" class="main-logo-img" alt="{{ slide.title_ar }}">
                        {% endif %}
                    </div>'''

replacement = '''                    {% if slide.image %}
                    <div class="slide-image-wrapper">
                        <img src="{{ slide.image.url }}" class="main-logo-img" alt="{{ slide.title_ar }}">
                    </div>
                    {% endif %}'''

if target in content:
    content = content.replace(target, replacement)
    with codecs.open('store/templates/store/index.html', 'w', 'utf-8') as f:
        f.write(content)
    print("Success")
else:
    print("Target not found")
