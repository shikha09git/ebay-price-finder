from django.contrib import admin
from .models import ProductImage, SearchResult, PriceSuggestion


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'detected_label', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['detected_label']


@admin.register(SearchResult)
class SearchResultAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'seller_name', 'condition', 'searched_at']
    list_filter = ['condition', 'searched_at']
    search_fields = ['title', 'seller_name']


@admin.register(PriceSuggestion)
class PriceSuggestionAdmin(admin.ModelAdmin):
    list_display = ['product_image', 'suggested_price', 'min_price', 'max_price', 'total_listings']
    list_filter = ['created_at']
