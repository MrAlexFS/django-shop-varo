from django.http import HttpResponseRedirect
from django.db import models
from django.contrib import messages

from django.shortcuts import render

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from .models import Category, Product
from .forms import CategoryForm, ProductForm

class CategoryListView(ListView):
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

class CategoryCreateView(SuccessMessageMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'catalog/category_form.html'
    success_url = reverse_lazy('catalog:category_list')
    success_message = 'Категория "%(name)s" успешно создана'

class CategoryUpdateView(SuccessMessageMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'catalog/category_form.html'
    success_url = reverse_lazy('catalog:category_list')
    success_message = 'Категория "%(name)s" успешно обновлена'

class CategoryDeleteView(DeleteView):
    model = Category
    template_name = 'catalog/category_confirm_delete.html'
    success_url = reverse_lazy('catalog:category_list')
    success_message = 'Категория удалена'

    def delete(self, request, *args, **kwargs):
        # Проверка на наличие связанных товаров
        category = self.get_object()
        if category.products.exists():
            # Если есть товары, выводим сообщение и не удаляем
            from django.contrib import messages
            messages.error(request, 'Нельзя удалить категорию, в которой есть товары.')
            return HttpResponseRedirect(self.success_url)
        messages.success(request, self.success_message)
        return super().delete(request, *args, **kwargs)
    


class ProductListView(ListView):
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related('category')
        # Фильтрация по категории
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Поиск по названию или описанию
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                models.Q(name__icontains=query) | models.Q(description__icontains=query)
            )

        # Сортировка
        sort = self.request.GET.get('sort')
        if sort in ['price', 'name', 'created_at']:
            queryset = queryset.order_by(sort)
        elif sort == '-price':
            queryset = queryset.order_by('-price')
        # По умолчанию сортировка по имени
        else:
            queryset = queryset.order_by('name')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Передаём список категорий для фильтра
        context['categories'] = Category.objects.filter(is_active=True)
        # Сохраняем текущие параметры GET для пагинации
        context['current_category'] = self.request.GET.get('category', '')
        context['current_q'] = self.request.GET.get('q', '')
        context['current_sort'] = self.request.GET.get('sort', '')
        return context

class ProductCreateView(SuccessMessageMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'catalog/product_form.html'
    success_url = reverse_lazy('catalog:product_list')
    success_message = 'Товар "%(name)s" успешно создан'

class ProductUpdateView(SuccessMessageMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'catalog/product_form.html'
    success_url = reverse_lazy('catalog:product_list')
    success_message = 'Товар "%(name)s" успешно обновлен'

class ProductDeleteView(DeleteView):
    model = Product
    template_name = 'catalog/product_confirm_delete.html'
    success_url = reverse_lazy('catalog:product_list')
    success_message = 'Товар удален'

    def delete(self, request, *args, **kwargs):
        messages.success(request, self.success_message)
        return super().delete(request, *args, **kwargs)