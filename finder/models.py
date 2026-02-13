from django.db import models
import os


def upload_to(instance, filename):
    return os.path.join('uploads', filename)


class ProductImage(models.Model):
    
    image = models.ImageField(upload_to=upload_to, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    detected_label = models.CharField(max_length=255, blank=True)
    detected_labels = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Image {self.id} - {self.detected_label or 'Unknown'}"


class SearchResult(models.Model):
    
    product_image = models.ForeignKey(
        ProductImage, 
        on_delete=models.CASCADE, 
        related_name='search_results'
    )
    title = models.CharField(max_length=500)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    seller_name = models.CharField(max_length=255, blank=True)
    item_url = models.URLField(max_length=1000)
    image_url = models.URLField(max_length=1000, blank=True)
    condition = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    searched_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['price']
    
    def __str__(self):
        return f"{self.title[:50]} - ${self.price}"


class PriceSuggestion(models.Model):
    
    product_image = models.OneToOneField(
        ProductImage,
        on_delete=models.CASCADE,
        related_name='price_suggestion'
    )
    min_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_price = models.DecimalField(max_digits=10, decimal_places=2)
    suggested_price = models.DecimalField(max_digits=10, decimal_places=2)
    average_price = models.DecimalField(max_digits=10, decimal_places=2)
    median_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_listings = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Suggestion: ${self.suggested_price}"


class ListingProduct(models.Model):

    CONDITION_NEW = 'new'
    CONDITION_USED = 'used'
    CONDITION_REFURBISHED = 'refurbished'
    CONDITION_OPEN_BOX = 'open_box'

    CONDITION_CHOICES = [
        (CONDITION_NEW, 'New'),
        (CONDITION_USED, 'Used'),
        (CONDITION_REFURBISHED, 'Refurbished'),
        (CONDITION_OPEN_BOX, 'Open Box'),
    ]

    title = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    category_id = models.CharField(max_length=32)
    image = models.ImageField(upload_to=upload_to, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} (${self.price})"
