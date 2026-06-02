import io

try:
    with io.open('store/templates/store/index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix before pseudo-element
    target1 = '''    .slide-image-wrapper::before {
        content: '';
        position: absolute;
        width: 480px;
        height: 480px;
        border: 1px solid rgba(201, 167, 92, 0.3);
        border-radius: 50%;
        z-index: 1;
        box-shadow: inset 0 0 40px rgba(201, 167, 92, 0.05);
    }'''
    replacement1 = '''    .slide-image-wrapper::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 480px;
        height: 480px;
        border: 1px solid rgba(201, 167, 92, 0.3);
        border-radius: 50%;
        z-index: 1;
        box-shadow: inset 0 0 40px rgba(201, 167, 92, 0.05);
    }'''

    # Fix after pseudo-element
    target2 = '''    .slide-image-wrapper::after {
        content: '';
        position: absolute;
        width: 360px;
        height: 360px;
        border: 1px solid rgba(201, 167, 92, 0.15);
        border-radius: 50%;
        z-index: 1;
    }'''
    replacement2 = '''    .slide-image-wrapper::after {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 360px;
        height: 360px;
        border: 1px solid rgba(201, 167, 92, 0.15);
        border-radius: 50%;
        z-index: 1;
    }'''

    # Fix mobile styling
    target3 = '''        .slide-image-wrapper {
            max-width: 100%;
        }'''
    replacement3 = '''        .slide-image-wrapper {
            max-width: 100%;
            transform: none;
            margin-top: 40px;
        }'''

    content = content.replace(target1, replacement1)
    content = content.replace(target2, replacement2)
    content = content.replace(target3, replacement3)

    with io.open('store/templates/store/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Success")
except Exception as e:
    print(str(e))
