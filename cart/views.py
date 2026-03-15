from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from catalog.models import Product
from .cart import Cart
from .forms import CartAddProductForm

from django.http import JsonResponse

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required



@require_POST
def cart_add(request, product_id):
    """Добавление товара в корзину (обработка POST-запроса)."""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(product=product,
                 quantity=cd['quantity'],
                 update_quantity=cd['update'])
    return redirect('cart:cart_detail')


def cart_remove(request, product_id):
    """Удаление товара из корзины."""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart:cart_detail')


def cart_detail(request):
    cart = Cart(request)
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(initial={'quantity': item['quantity'], 'update': True})
    return render(request, 'cart/detail.html', {'cart': cart})


@require_POST
def cart_toggle(request):
    """Переключает состояние товара в корзине: добавляет или удаляет."""
    cart = Cart(request)
    product_id = request.POST.get('product_id')
    if not product_id:
        return JsonResponse({'error': 'Product ID required'}, status=400)

    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

    # Проверяем, есть ли товар в корзине
    if str(product_id) in cart.cart:
        cart.remove(product)
        status = 'removed'
    else:
        cart.add(product=product, quantity=1, update_quantity=False)
        status = 'added'

    return JsonResponse({
        'status': status,
        'cart_total': len(cart),  # общее количество товаров
        'product_id': product_id
    })