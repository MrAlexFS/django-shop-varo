from django.http import HttpResponseRedirect
from django.db import models
from django.contrib import messages
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404

from .models import Category, Product
from .forms import CategoryForm, ProductForm
from cart.forms import CartAddProductForm
from cart.cart import Cart  # импорт класса Cart


class StaffRequiredMixin(UserPassesTestMixin):
    """Миксин для ограничения доступа только персоналу (is_staff)."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff


# ==================== Административные представления (только для персонала) ====================

class CategoryListView(StaffRequiredMixin, ListView):
    model = Category
    template_name = 'catalog/category_list.html'
    context_object_name = 'categories'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(name__icontains=query)
        return queryset


class CategoryCreateView(StaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'catalog/category_form.html'
    success_url = reverse_lazy('catalog:category_list')
    success_message = 'Категория "%(name)s" успешно создана'


class CategoryUpdateView(StaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'catalog/category_form.html'
    success_url = reverse_lazy('catalog:category_list')
    success_message = 'Категория "%(name)s" успешно обновлена'


class CategoryDeleteView(StaffRequiredMixin, DeleteView):
    model = Category
    template_name = 'catalog/category_confirm_delete.html'
    success_url = reverse_lazy('catalog:category_list')
    success_message = 'Категория удалена'

    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        if category.products.exists():
            messages.error(request, 'Нельзя удалить категорию, в которой есть товары.')
            return HttpResponseRedirect(self.success_url)
        messages.success(request, self.success_message)
        return super().delete(request, *args, **kwargs)


class ProductListView(StaffRequiredMixin, ListView):
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related('category')
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                models.Q(name__icontains=query) | models.Q(description__icontains=query)
            )

        sort = self.request.GET.get('sort')
        if sort in ['price', 'name', 'created_at']:
            queryset = queryset.order_by(sort)
        elif sort == '-price':
            queryset = queryset.order_by('-price')
        else:
            queryset = queryset.order_by('name')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['current_category'] = self.request.GET.get('category', '')
        context['current_q'] = self.request.GET.get('q', '')
        context['current_sort'] = self.request.GET.get('sort', '')
        return context


class ProductCreateView(StaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'catalog/product_form.html'
    success_url = reverse_lazy('catalog:product_list')
    success_message = 'Товар "%(name)s" успешно создан'


class ProductUpdateView(StaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'catalog/product_form.html'
    success_url = reverse_lazy('catalog:product_list')
    success_message = 'Товар "%(name)s" успешно обновлен'


class ProductDeleteView(StaffRequiredMixin, DeleteView):
    model = Product
    template_name = 'catalog/product_confirm_delete.html'
    success_url = reverse_lazy('catalog:product_list')
    success_message = 'Товар удален'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)


# ==================== Публичные представления (доступны всем) ====================

class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)\
            .annotate(products_count=Count('products'))\
            .order_by('-products_count')[:6]
        context['latest_products'] = Product.objects.filter(is_active=True)\
            .order_by('-created_at')[:8]
        cart = Cart(self.request)
        context['cart_product_ids'] = [int(pid) for pid in cart.cart.keys()]
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'catalog/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = Cart(self.request)
        context['cart_product_ids'] = [int(pid) for pid in cart.cart.keys()]
        context['cart_add_form'] = CartAddProductForm()
        context['related_products'] = Product.objects.filter(
            category=self.object.category
        ).exclude(pk=self.object.pk)[:4]
        return context


class UserCatalogView(TemplateView):
    template_name = 'catalog/user_catalog.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Корневые категории (родитель = null)
        context['root_categories'] = Category.objects.filter(
            parent__isnull=True, is_active=True
        ).prefetch_related('children')
        return context


class CategoryProductsView(ListView):
    """
    Отображает товары конкретной категории. URL: /catalog/category/<slug:slug>/
    """
    model = Product
    template_name = 'catalog/category_products.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'], is_active=True)
        return Product.objects.filter(category=self.category, is_active=True).select_related('category').order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = Cart(self.request)
        context['cart_product_ids'] = [int(pid) for pid in cart.cart.keys()]
        context['category'] = self.category
        context['current_sort'] = self.request.GET.get('sort', '')
        return context