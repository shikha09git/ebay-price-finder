from django import forms
from .models import ProductImage


class ImageUploadForm(forms.ModelForm):
    """Form for uploading product images."""
    
    class Meta:
        model = ProductImage
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            })
        }
    
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            if image.size > 10 * 1024 * 1024:
                raise forms.ValidationError("Image file too large (max 10MB)")
            
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            ext = image.name.lower().split('.')[-1]
            if f'.{ext}' not in valid_extensions:
                raise forms.ValidationError(
                    f"Unsupported file type. Allowed: {', '.join(valid_extensions)}"
                )
        return image


class ManualSearchForm(forms.Form):
    """Form for manual keyword search."""
    keywords = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter product keywords (e.g., "Mobil 1 Synthetic Oil 5W-30")',
        })
    )
