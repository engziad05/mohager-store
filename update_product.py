import sys

with open('store/templates/store/product_detail.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix thumbnail onclicks
content = content.replace(
    'onclick="changeMainImage(this, \'{{ product.image.url }}\')"',
    'onclick="changeMainImage(0)"'
)

content = content.replace(
    'onclick="changeMainImage(this, \'{{ img.image.url }}\')"',
    'onclick="changeMainImage({% if product.image %}{{ forloop.counter }}{% else %}{{ forloop.counter0 }}{% endif %})"'
)

# New JS to replace the old JS
old_js = """<script>
    // 1. تقليب الصور المصغرة
    function changeMainImage(element, src) {
        const mainImg = document.getElementById('main-product-image');
        if (!mainImg) return;
        
        mainImg.style.opacity = '0.5';
        setTimeout(() => {
            mainImg.src = src;
            mainImg.style.opacity = '1';
        }, 150);
        
        let thumbs = document.querySelectorAll('.thumb-item');
        thumbs.forEach(t => t.classList.remove('active-thumb'));
        element.classList.add('active-thumb');
    }

    // 2. وظايف الـ Lightbox (فتح وقفل الصورة)
    function openLightbox() {
        const mainImgSrc = document.getElementById('main-product-image').src;
        document.getElementById('lightboxImg').src = mainImgSrc;
        document.getElementById('imageLightbox').style.display = 'flex';
        // منع السكرول في الصفحة لما الصورة تتفتح
        document.body.style.overflow = 'hidden'; 
    }

    function closeLightbox() {
        document.getElementById('imageLightbox').style.display = 'none';
        // إرجاع السكرول للصفحة
        document.body.style.overflow = 'auto'; 
    }"""

new_js = """<script>
    // 1. نظام الصور وتقليبها بالسحب (Swipe)
    const galleryImages = [];
    {% if product.image %}galleryImages.push('{{ product.image.url }}');{% endif %}
    {% for img in extra_images %}galleryImages.push('{{ img.image.url }}');{% endfor %}
    
    let currentImgIndex = 0;

    function updateImageDisplay() {
        if (galleryImages.length === 0) return;
        
        const src = galleryImages[currentImgIndex];
        const mainImg = document.getElementById('main-product-image');
        
        if (mainImg) {
            mainImg.style.opacity = '0.5';
            setTimeout(() => {
                mainImg.src = src;
                mainImg.style.opacity = '1';
            }, 150);
        }
        
        // تحديث شاشة العرض لو مفتوحة
        const lightboxImg = document.getElementById('lightboxImg');
        if (lightboxImg && document.getElementById('imageLightbox').style.display === 'flex') {
            lightboxImg.style.opacity = '0.5';
            setTimeout(() => {
                lightboxImg.src = src;
                lightboxImg.style.opacity = '1';
            }, 150);
        }

        // تحديث الصور المصغرة
        const thumbs = document.querySelectorAll('.thumb-item');
        thumbs.forEach((t, index) => {
            if (index === currentImgIndex) {
                t.classList.add('active-thumb');
            } else {
                t.classList.remove('active-thumb');
            }
        });
    }

    function changeMainImage(index) {
        currentImgIndex = index;
        updateImageDisplay();
    }

    function showNextImage() {
        if (galleryImages.length <= 1) return;
        // في العربي (RTL)، التقليب لليسار بيعرض الصورة التالية
        currentImgIndex = (currentImgIndex + 1) % galleryImages.length;
        updateImageDisplay();
    }

    function showPrevImage() {
        if (galleryImages.length <= 1) return;
        currentImgIndex = (currentImgIndex - 1 + galleryImages.length) % galleryImages.length;
        updateImageDisplay();
    }

    // إضافة وظيفة السحب (Swipe) للموبايل
    let touchstartX = 0;
    let touchendX = 0;

    function handleSwipe() {
        // السحب لليسار يعني التالي، لليمين يعني السابق
        if (touchstartX - touchendX > 50) {
            showNextImage(); // سحب لليسار
        } else if (touchendX - touchstartX > 50) {
            showPrevImage(); // سحب لليمين
        }
    }

    const mainImgContainer = document.querySelector('.main-img-container');
    if (mainImgContainer) {
        mainImgContainer.addEventListener('touchstart', e => { touchstartX = e.changedTouches[0].screenX; }, {passive: true});
        mainImgContainer.addEventListener('touchend', e => { touchendX = e.changedTouches[0].screenX; handleSwipe(); });
    }

    const lightbox = document.getElementById('imageLightbox');
    if (lightbox) {
        lightbox.addEventListener('touchstart', e => { touchstartX = e.changedTouches[0].screenX; }, {passive: true});
        lightbox.addEventListener('touchend', e => { touchendX = e.changedTouches[0].screenX; handleSwipe(); });
    }

    // 2. وظايف الـ Lightbox (فتح وقفل الصورة)
    function openLightbox() {
        if (galleryImages.length === 0) return;
        document.getElementById('lightboxImg').src = galleryImages[currentImgIndex];
        document.getElementById('imageLightbox').style.display = 'flex';
        document.body.style.overflow = 'hidden'; 
    }

    function closeLightbox() {
        document.getElementById('imageLightbox').style.display = 'none';
        document.body.style.overflow = 'auto'; 
    }"""

content = content.replace(old_js, new_js)

with open('store/templates/store/product_detail.html', 'w', encoding='utf-8') as f:
    f.write(content)
