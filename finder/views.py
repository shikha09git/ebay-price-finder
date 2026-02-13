from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from decimal import Decimal

from .models import ProductImage, SearchResult, PriceSuggestion, ListingProduct
from .forms import ImageUploadForm, ManualSearchForm, SignUpForm, ListingProductForm
from .services import EbayAPIService, ImageRecognitionService, PriceSuggestionService


@login_required
def home(request):
    
    form = ImageUploadForm()
    manual_form = ManualSearchForm()
    recent_searches = ProductImage.objects.all()[:5]
    
    return render(request, 'finder/home.html', {
        'form': form,
        'manual_form': manual_form,
        'recent_searches': recent_searches,
    })


@login_required
@require_POST
def upload_image(request):
    
    form = ImageUploadForm(request.POST, request.FILES)
    
    if form.is_valid():
        product_image = form.save()
        
        recognition_service = ImageRecognitionService()
        detected_label, detected_labels, web_label = recognition_service.recognize_product(
            product_image.image.path
        )
        product_image.detected_label = detected_label
        product_image.detected_labels = ", ".join(detected_labels)
        product_image.save()

        search_keywords = web_label or detected_label
        _perform_search(product_image, search_keywords)
        
        messages.success(request, f'Image uploaded! Detected: "{detected_label}"')
        return redirect('finder:results', pk=product_image.pk)
    
    messages.error(request, 'Error uploading image. Please try again.')
    return redirect('finder:home')


@login_required
@require_POST
def manual_search(request):
    
    form = ManualSearchForm(request.POST)
    
    if form.is_valid():
        keywords = form.cleaned_data['keywords']
        
        product_image = ProductImage.objects.create(
            detected_label=keywords
        )
        
        _perform_search(product_image, keywords)
        
        messages.success(request, f'Search completed for: "{keywords}"')
        return redirect('finder:results', pk=product_image.pk)
    
    messages.error(request, 'Please enter valid search keywords.')
    return redirect('finder:home')


@login_required
def results(request, pk):
    
    product_image = get_object_or_404(ProductImage, pk=pk)
    search_results = product_image.search_results.all()
    
    try:
        price_suggestion = product_image.price_suggestion
    except PriceSuggestion.DoesNotExist:
        price_suggestion = None
    
    new_items = search_results.filter(condition__icontains='new')
    used_items = search_results.exclude(condition__icontains='new')
    
    return render(request, 'finder/results.html', {
        'product_image': product_image,
        'search_results': search_results,
        'new_items': new_items,
        'used_items': used_items,
        'price_suggestion': price_suggestion,
    })


@login_required
def refresh_search(request, pk):
    
    product_image = get_object_or_404(ProductImage, pk=pk)
    
    product_image.search_results.all().delete()
    try:
        product_image.price_suggestion.delete()
    except PriceSuggestion.DoesNotExist:
        pass
    
    keywords = product_image.detected_label or "product"
    _perform_search(product_image, keywords)
    
    messages.success(request, 'Search refreshed successfully!')
    return redirect('finder:results', pk=pk)


@login_required
def add_product(request):

    if request.method == 'POST':
        form = ListingProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, 'Demo listing saved locally (no eBay API call).')
            return redirect('finder:product_detail', pk=product.pk)
        messages.error(request, 'Please fix the errors below.')
    else:
        form = ListingProductForm()

    recent_products = ListingProduct.objects.all()[:5]

    return render(request, 'finder/add_product.html', {
        'form': form,
        'recent_products': recent_products,
    })


@login_required
def product_list(request):

    products = ListingProduct.objects.all()

    return render(request, 'finder/products.html', {
        'products': products,
    })


@login_required
def product_detail(request, pk):

    product = get_object_or_404(ListingProduct, pk=pk)

    return render(request, 'finder/product_detail.html', {
        'product': product,
    })


def _perform_search(product_image: ProductImage, keywords: str) -> None:
    
    ebay_service = EbayAPIService()
    results = ebay_service.search_products(keywords)
    
    prices = []
    
    for item in results:
        SearchResult.objects.create(
            product_image=product_image,
            title=item['title'],
            price=item['price'],
            currency=item['currency'],
            seller_name=item['seller'],
            item_url=item['item_url'],
            image_url=item['image_url'],
            condition=item['condition'],
            description=item.get('description', ''),
        )
        prices.append(item['price'])
    
    if prices:
        suggestion_data = PriceSuggestionService.calculate_suggestion(prices)
        PriceSuggestion.objects.create(
            product_image=product_image,
            **suggestion_data
        )


@login_required
def api_search(request):
    
    keywords = request.GET.get('keywords', '')
    
    if not keywords:
        return JsonResponse({'error': 'Keywords required'}, status=400)
    
    ebay_service = EbayAPIService()
    results = ebay_service.search_products(keywords)
    
    prices = [Decimal(str(float(r['price']))) for r in results]
    suggestion = PriceSuggestionService.calculate_suggestion(prices)
    
    return JsonResponse({
        'results': [
            {
                'title': r['title'],
                'description': r.get('description', ''),
                'price': float(r['price']),
                'currency': r['currency'],
                'seller': r['seller'],
                'url': r['item_url'],
                'condition': r['condition'],
            }
            for r in results
        ],
        'suggestion': {
            'min_price': float(suggestion['min_price']),
            'max_price': float(suggestion['max_price']),
            'average_price': float(suggestion['average_price']),
            'median_price': float(suggestion['median_price']),
            'suggested_price': float(suggestion['suggested_price']),
            'total_listings': suggestion['total_listings'],
        }
    })


def signup(request):
    
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('finder:home')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created. Please log in.')
            return redirect('login')
    else:
        form = SignUpForm()

    return render(request, 'registration/signup.html', {'form': form})


@require_POST
def guest_login(request):
    
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('finder:home')

    user_model = get_user_model()
    guest_user, created = user_model.objects.get_or_create(
        username='guest',
        defaults={'email': 'guest@example.com'}
    )
    if created:
        guest_user.set_unusable_password()
        guest_user.save()

    login(request, guest_user, backend='django.contrib.auth.backends.ModelBackend')
    messages.success(request, 'Logged in as guest.')
    return redirect('finder:home')
