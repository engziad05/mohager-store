import io
import sys

try:
    with io.open('store/templates/store/index.html', 'r', encoding='utf-8') as f:
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
        with io.open('store/templates/store/index.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Success")
    else:
        # try line by line modification as fallback
        lines = content.split('\n')
        for i in range(len(lines)):
            if '<div class="slide-image-wrapper">' in lines[i] and '{% if slide.image %}' in lines[i+1]:
                lines[i] = lines[i].replace('<div class="slide-image-wrapper">', '{% if slide.image %}\n                    <div class="slide-image-wrapper">')
                lines[i+1] = ''
                lines[i+3] = ''
                lines[i+4] = lines[i+4].replace('</div>', '</div>\n                    {% endif %}')
                with io.open('store/templates/store/index.html', 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                print("Success line by line")
                sys.exit(0)
        print("Target not found")
except Exception as e:
    print(str(e))
