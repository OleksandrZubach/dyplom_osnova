from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.index, name='index'),  # Головна сторінка
    path('catalog/', views.catalog_view, name='catalog'),  # Всі категорії (каталог)
    path('catalog/<slug:slug>/', views.category_detail, name='category_detail'),  # Товари в категорії
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),  # Сторінка продукту

    # Кошик
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),

    # Замовлення
    path('checkout/', views.checkout, name='checkout'),
    path('order/', views.order_view, name='order'),
    path('order/success/<int:order_id>/', views.order_success_view, name='order_success'),

    # Акаунт
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('account/', views.account_view, name='account'),
    path('logout/', views.logout_view, name='logout'),

    # Інформаційні сторінки
    path('about/', views.about_view, name='about'),
    path('contacts/', views.contacts_view, name='contacts'),
    path('account/clear-orders/', views.clear_orders, name='clear_orders'),
    path('account/edit/', views.edit_profile_view, name='edit_profile'),



]
