from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from .models import Category, Product, Order, OrderItem, Cart, CartItem
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

# Create your views here.

class ProductListView(ListView):
    model = Product
    template_name = 'store/product_list.html'
    context_object_name = 'products'

class ProductDetailView(DetailView):
    model = Product
    template_name = 'store/product_detail.html'
    context_object_name = 'product'

class CategoryListView(ListView):
    model = Category
    template_name = 'store/category_list.html'
    context_object_name = 'categories'

class CategoryDetailView(DetailView):
    model = Category
    template_name = 'store/category_detail.html'
    context_object_name = 'category'

class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    fields = ['first_name', 'last_name', 'email', 'address', 'postal_code', 'city']
    template_name = 'store/order_create.html'
    success_url = reverse_lazy('store:order_success')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('store:index')
        else:
            messages.error(request, 'Неправильний email або пароль')
    return render(request, 'store/login.html')

def register_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, 'Паролі не співпадають')
            return redirect('store:register')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Цей email вже зареєстрований')
            return redirect('store:register')
            
        user = User.objects.create_user(username=email, email=email, password=password, first_name=name)
        login(request, user)
        return redirect('store:index')
        
    return render(request, 'store/register.html')

def index(request):
    new_products = Product.objects.order_by('-created_at')[:8]
    top_products = Product.objects.order_by('-views')[:8]
    return render(request, 'store/index.html', {
        'new_products': new_products,
        'top_products': top_products
    })

def category_list(request):
    categories = Category.objects.all()
    products = Product.objects.all()
    return render(request, 'store/category_list.html', {
        'categories': categories,
        'products': products
    })

def category_detail(request, slug):
    try:
        # Отримуємо категорію
        category = get_object_or_404(Category, slug=slug)
        print(f"Found category: {category.name}")
        
        # Отримуємо всі категорії для сайдбару
        categories = Category.objects.all()
        print(f"Found {categories.count()} categories for sidebar")
        
        # Отримуємо товари категорії без зображень
        products = Product.objects.filter(category=category).defer('image')
        print(f"Found {products.count()} products in category")
        
        # Сортування
        sort_by = request.GET.get('sort_by', 'name')
        print(f"Sorting by: {sort_by}")
        
        if sort_by == 'price_asc':
            products = products.order_by('price')
        elif sort_by == 'price_desc':
            products = products.order_by('-price')
        elif sort_by == 'name':
            products = products.order_by('name')
        
        # Фільтрація за ціною
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        print(f"Price filter: min={min_price}, max={max_price}")
        
        if min_price:
            try:
                min_price = float(min_price)
                products = products.filter(price__gte=min_price)
            except ValueError:
                print("Invalid min_price value")
        
        if max_price:
            try:
                max_price = float(max_price)
                products = products.filter(price__lte=max_price)
            except ValueError:
                print("Invalid max_price value")
        
        # Пагінація
        page = request.GET.get('page', 1)
        paginator = Paginator(products, 12)  # 12 товарів на сторінку
        print(f"Creating paginator with {products.count()} products")
        
        try:
            products = paginator.page(page)
            print(f"Current page: {page}, total pages: {paginator.num_pages}")
        except PageNotAnInteger:
            print("Invalid page number, using first page")
            products = paginator.page(1)
        except EmptyPage:
            print("Page out of range, using last page")
            products = paginator.page(paginator.num_pages)
        
        return render(request, 'store/category.html', {
            'category': category,
            'products': products,
            'categories': categories,
            'sort_by': sort_by,
            'min_price': min_price,
            'max_price': max_price
        })
    except Exception as e:
        # Логуємо помилку
        print(f"Error in category_detail: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(traceback.format_exc())
        # Повертаємо сторінку з помилкою
        return render(request, 'store/error.html', {
            'error_message': f'Помилка при завантаженні категорії: {str(e)}'
        })

def product_detail(request, slug):
    product = Product.objects.get(slug=slug)
    product.views += 1
    product.save()
    return render(request, 'store/product_detail.html', {'product': product})

@login_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'store/cart.html', {'cart': cart})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f'Товар "{product.name}" додано до корзини')
    return redirect('store:cart_detail')

@login_required
def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_object_or_404(Cart, user=request.user)
    
    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except CartItem.DoesNotExist:
        pass
    
    return redirect('store:cart_detail')

@login_required
def clear_cart(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart.items.all().delete()
    messages.success(request, 'Корзина очищена')
    return redirect('store:cart_detail')

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    if not cart.items.exists():
        messages.warning(request, 'Ваша корзина порожня')
        return redirect('store:cart_detail')
    
    # Тут буде логіка оформлення замовлення
    return render(request, 'store/checkout.html', {'cart': cart})

@login_required
def account_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created')
    return render(request, 'store/account.html', {'orders': orders})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Ви успішно вийшли з облікового запису')
    return redirect('store:index')

@login_required
def clear_orders(request):
    Order.objects.filter(user=request.user).delete()
    messages.success(request, 'Всі ваші замовлення були видалені')
    return redirect('store:account')

def catalog_view(request):
    categories = Category.objects.all()
    popular_products = Product.objects.order_by('-views')[:8]
    
    return render(request, 'store/catalog.html', {
        'categories': categories,
        'popular_products': popular_products
    })

@login_required
def order_view(request):
    cart = get_object_or_404(Cart, user=request.user)
    
    if request.method == 'POST':
        # Створюємо нове замовлення
        order = Order.objects.create(
            user=request.user,
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            delivery_method=request.POST.get('delivery_method'),
            payment_method=request.POST.get('payment_method'),
            total_price=cart.total_price
        )
        
        # Додаємо товари до замовлення
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
        
        # Очищаємо кошик
        cart.items.all().delete()
        
        messages.success(request, 'Ваше замовлення успішно оформлено!')
        return redirect('store:order_success', order_id=order.id)
    
    return render(request, 'store/order.html', {'cart': cart})

@login_required
def order_success_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_success.html', {'order': order})

def about_view(request):
    return render(request, 'store/about.html')

def contacts_view(request):
    return render(request, 'store/contacts.html')
