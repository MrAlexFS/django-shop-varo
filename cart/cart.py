from decimal import Decimal
from django.conf import settings
from catalog.models import Product


class Cart(object):
    """
    Класс корзины, хранящийся в сессии.
    """

    def __init__(self, request):
        """Инициализация корзины: получаем или создаём пустую корзину в сессии."""
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, update_quantity=False):
        """
        Добавить продукт в корзину или обновить его количество.
        product – экземпляр Product
        quantity – количество (по умолчанию 1)
        update_quantity – если True, устанавливает указанное количество,
                          иначе добавляет quantity к существующему.
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0, 'price': str(product.price)}
        if update_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def save(self):
        """Сохраняет корзину в сессии."""
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

    def remove(self, product):
        """Удаляет товар из корзины."""
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        """Перебирает товары в корзине и подгружает объекты Product."""
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        for product in products:
            self.cart[str(product.id)]['product'] = product

        for item in self.cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """Возвращает общее количество товаров в корзине (сумму quantity)."""
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """Возвращает общую стоимость корзины."""
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        """Очищает корзину."""
        del self.session[settings.CART_SESSION_ID]
        self.session.modified = True