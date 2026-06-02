from unfold.admin import ModelAdmin, TabularInline
from django import forms

from .models import Category, Product, ProductImage, ProductVariant, ProductColor


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        raw_val = self.data.get(self.add_prefix('product_color'))
        
        if raw_val and str(raw_val).startswith('new_'):
            if 'product_color' in self._errors:
                del self._errors['product_color']
            cleaned_data['product_color'] = None
            
        return cleaned_data


class ProductColorInline(TabularInline):
    model = ProductColor
    extra = 1


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1
    form = ProductImageForm


class ProductVariantInline(TabularInline):
    model = ProductVariant
    extra = 1


class ProductAdmin(ModelAdmin):
    list_display = ['name_en', 'category', 'base_price', 'compare_at_price', 'discount_percent_display', 'stock_summary', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name_ar', 'name_en']
    list_select_related = ['category']
    readonly_fields = ['discount_percent_display']
    
    class Media:
        js = ('js/admin_product_v4.js',)
        
    fieldsets = (
        ('Product details', {
            'fields': ('category', 'name_ar', 'name_en', 'description_ar', 'description_en', 'image', 'is_active')
        }),
        ('Pricing', {
            'fields': ('base_price', 'compare_at_price', 'discount_percent_display'),
            'description': 'Base price is the final selling price. Original price is shown as crossed-out when it is higher than base price.',
        }),
    )
    inlines = [ProductVariantInline, ProductColorInline, ProductImageInline]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        
        print_formset = None
        image_formset = None
        
        for fs in formsets:
            if fs.model == ProductColor:
                print_formset = fs
            elif fs.model == ProductImage:
                image_formset = fs
                
        if print_formset and image_formset:
            print_map = {}
            for print_form in print_formset.forms:
                if print_form.instance and print_form.instance.pk:
                    print_map[print_form.prefix] = print_form.instance
                    
            for image_form in image_formset.forms:
                if image_form.instance and image_form.instance.pk:
                    raw_val = request.POST.get(image_form.add_prefix('product_color'))
                    if raw_val and str(raw_val).startswith('new_'):
                        print_prefix = str(raw_val).replace('new_', '')
                        if print_prefix in print_map:
                            image_form.instance.product_color = print_map[print_prefix]
                            image_form.instance.save()

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category').prefetch_related('variants')

    def stock_summary(self, obj):
        total_stock = sum(variant.stock for variant in obj.variants.all())
        return total_stock

    stock_summary.short_description = 'Stock'

    def discount_percent_display(self, obj):
        if not obj or not obj.has_discount:
            return 'No discount'
        return f'{obj.discount_percent}%'

    discount_percent_display.short_description = 'Discount'


class CategoryAdmin(ModelAdmin):
    list_display = ['name_en', 'name_ar', 'is_active']
    search_fields = ['name_ar', 'name_en', 'slug']
    prepopulated_fields = {'slug': ('name_en',)}
