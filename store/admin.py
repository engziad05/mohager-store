from unfold.admin import ModelAdmin

from .models import HeroSlide, StoreSetting


class HeroSlideAdmin(ModelAdmin):
    list_display = ['title_ar', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['title_ar', 'subtitle_ar']


class StoreSettingAdmin(ModelAdmin):
    list_display = ['shipping_cost']
