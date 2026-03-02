# Django Shop - Varo

Онлайн-магазин на Django для изучения GitFlow и командной разработки.

## Технологии

- Python 3.13+
- Django 5.0
- SQLite (для разработки) / PostgreSQL (опционально)
- Poetry для управления зависимостями
- GitFlow для организации веток

## Структура веток

- `main` — стабильная production версия
- `develop` — основная ветка разработки
- `test` — ветка для тестирования перед релизом
- `feature/*` — ветки для новых функций
- `hotfix/*` — ветки для срочных исправлений

## Установка и запуск

### 1. Клонировать репозиторий

```bash
git clone https://github.com/ваш-логин/django-shop-varo.git
cd django-shop-varo
git checkout develop