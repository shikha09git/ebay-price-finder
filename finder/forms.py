from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import ProductImage, ListingProduct


class ImageUploadForm(forms.ModelForm):
    
    
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
   
    keywords = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter product keywords (e.g., "Mobil 1 Synthetic Oil 5W-30")',
        })
    )


class SignUpForm(UserCreationForm):
    

    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'you@example.com',
    }))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class ListingProductForm(forms.ModelForm):

    class Meta:
        model = ListingProduct
        fields = ['title', 'price', 'quantity', 'condition', 'category_id', 'image']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Apple AirPods Pro (2nd Gen)',
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
            }),
            'condition': forms.Select(attrs={
                'class': 'form-select',
            }),
            'category_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 15032',
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and image.size > 10 * 1024 * 1024:
            raise forms.ValidationError("Image file too large (max 10MB)")
        return image
