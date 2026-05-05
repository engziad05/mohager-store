from django import forms
from allauth.account.forms import SignupForm
# ضيف دي فوق مع الـ imports
from .models import SavedAddress

class CustomSignupForm(SignupForm):
    # حقل الاسم
    name = forms.CharField(max_length=50, label='الاسم', widget=forms.TextInput(attrs={'placeholder': 'أدخل اسمك'}))

    def save(self, request):
        # بنحفظ المستخدم بالطريقة العادية
        user = super(CustomSignupForm, self).save(request)
        # بناخد الاسم اللي كتبه ونحطه في الـ first_name
        user.first_name = self.cleaned_data['name']
        user.save()
        return user

# ركز هنا: الدالة دي بره الكلاس خالص (لازقة في الحيطة على الشمال)
def custom_user_display(user):
    # والسطر ده واخد Tab (مسافة) لجوه
    return user.first_name or user.email
class SavedAddressForm(forms.ModelForm):
    class Meta:
        model = SavedAddress
        exclude = ['user'] # استبعدنا اليوزر عشان هنحطه إحنا برمجياً في الـ View
        
    def __init__(self, *args, **kwargs):
        super(SavedAddressForm, self).__init__(*args, **kwargs)
        # اللوب دي عشان تدي كل الحقول كلاس CSS يخلي شكلها شيك ومتناسق مع الموقع
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['style'] = 'width: 100%; padding: 10px; margin-bottom: 15px; background: #222; border: 1px solid #444; color: #fff; border-radius: 5px;'