"""
اختبار إرسال البريد
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.mail import EmailMultiAlternatives
from django.conf import settings

print(f"البريد المُرسِل: {settings.DEFAULT_FROM_EMAIL}")
print(f"البريد المالك: {settings.STORE_OWNER_EMAIL}")
print(f"Backend المستخدم: {settings.EMAIL_BACKEND}")
print(f"API Key موجود: {'نعم' if settings.ANYMAIL.get('BREVO_API_KEY') else 'لا'}")
print()

try:
    msg = EmailMultiAlternatives(
        subject="✓ اختبار البريد من مُهاجر",
        body="هذا اختبار لإرسال البريد",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=["ziad045@gmail.com"],
    )
    msg.attach_alternative("<h1>✓ اختبار البريد</h1><p>تم الإرسال بنجاح!</p>", "text/html")
    result = msg.send()
    print(f"✅ تم إرسال البريد بنجاح! (النتيجة: {result})")
except Exception as e:
    print(f"❌ خطأ في إرسال البريد:")
    print(f"نوع الخطأ: {type(e).__name__}")
    print(f"رسالة الخطأ: {str(e)}")
    import traceback
    traceback.print_exc()
