from unfold.admin import ModelAdmin, TabularInline
from django import forms
from django.contrib import admin

from .models import Category, Product, ProductImage, ProductColor, GlobalColor, MasterStock, MasterStockVariant
from django.db.models import Sum, OuterRef, Subquery, IntegerField
from django.db.models.functions import Coalesce


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'product_color' in self.fields:
            if self.instance and hasattr(self.instance, 'product_id') and self.instance.product_id:
                qs = ProductColor.objects.filter(product_id=self.instance.product_id)
            else:
                qs = ProductColor.objects.none()
            
            if self.is_bound:
                raw_val = self.data.get(self.add_prefix('product_color'))
                if raw_val and str(raw_val).isdigit():
                    qs = ProductColor.objects.filter(id=raw_val) | qs
                    
            self.fields['product_color'].queryset = qs

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


class MasterStockVariantInline(TabularInline):
    model = MasterStockVariant
    extra = 1

class GlobalColorAdmin(ModelAdmin):
    list_display = ['name_ar', 'name_en', 'color_code']
    search_fields = ['name_ar', 'name_en']

class MasterStockAdmin(ModelAdmin):
    list_display = ['category', 'color']
    list_filter = ['category', 'color']
    inlines = [MasterStockVariantInline]


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
    inlines = [ProductColorInline, ProductImageInline]

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
        qs = super().get_queryset(request).select_related('category')
        qs = qs.prefetch_related('colors__global_color')
        return qs

    def stock_summary(self, obj):
        color_ids = [c.global_color_id for c in obj.colors.all() if c.global_color_id]
        if not color_ids:
            return 0
            
        total = MasterStockVariant.objects.filter(
            master_stock__category_id=obj.category_id,
            master_stock__color_id__in=color_ids
        ).aggregate(total=Sum('stock'))['total']
        
        return total or 0

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
