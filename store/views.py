from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from .models import Category, Product, Order, OrderItem, Cart, CartItem, Profile
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from .forms import ProfileForm, UserUpdateForm



# --- Товари ---
class ProductListView(ListView):
    model = Product
    template_name = 'store/product_list.html'
    context_object_name = 'products'

class ProductDetailView(DetailView):
    model = Product
    template_name = 'store/product_detail.html'
    context_object_name = 'product'

# --- Категорії ---
class CategoryListView(ListView):
    model = Category
    template_name = 'store/category_list.html'
    context_object_name = 'categories'

class CategoryDetailView(DetailView):
    model = Category
    template_name = 'store/category_detail.html'
    context_object_name = 'category'

# --- Замовлення ---
class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    fields = ['first_name', 'last_name', 'email', 'address', 'postal_code', 'city']
    template_name = 'store/order_create.html'
    success_url = reverse_lazy('store:order_success')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

# --- Аутентифікація ---
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            return redirect('store:index')
        messages.error(request, 'Неправильний email або пароль')
    return render(request, 'store/login.html')

def register_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm = request.POST.get('confirm_password')
        if password != confirm:
            messages.error(request, 'Паролі не співпадають')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Цей email вже зареєстрований')
        else:
            user = User.objects.create_user(username=email, email=email, password=password, first_name=name)
            Profile.objects.create(user=user)
            login(request, user)
            return redirect('store:index')
        return redirect('store:register')
    return render(request, 'store/register.html')

# --- Головна ---
def index(request):
    new_products = Product.objects.order_by('-created_at')[:8]
    top_products = Product.objects.order_by('-views')[:8]
    return render(request, 'store/index.html', {
        'new_products': new_products,
        'top_products': top_products
    })

# --- Каталог ---
def catalog_view(request):
    categories = Category.objects.all()
    popular_products = Product.objects.order_by('-views')[:8]
    return render(request, 'store/catalog.html', {'categories': categories, 'popular_products': popular_products})

# --- Категорія ---
def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    categories = Category.objects.all()
    products = [p for p in Product.objects.filter(category=category) if hasattr(p.image, 'url')]
    sort = request.GET.get('sort_by', 'name')
    if sort == 'price_asc':
        products.sort(key=lambda x: x.price)
    elif sort == 'price_desc':
        products.sort(key=lambda x: -x.price)
    else:
        products.sort(key=lambda x: x.name.lower())
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = [p for p in products if p.price >= float(min_price)]
    if max_price:
        products = [p for p in products if p.price <= float(max_price)]
    paginator = Paginator(products, 12)
    page = request.GET.get('page', 1)
    try:
        products = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        products = paginator.page(1)
    return render(request, 'store/category.html', {
        'category': category,
        'products': products,
        'categories': categories,
        'sort_by': sort,
        'min_price': min_price,
        'max_price': max_price
    })

# --- Товар ---
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    product.views += 1
    product.save()
    # Переглянуті товари
    viewed = request.session.get('viewed_products', [])
    if product.id not in viewed:
        viewed.insert(0, product.id)
    request.session['viewed_products'] = viewed[:10]
    return render(request, 'store/product_detail.html', {'product': product})

# --- Кошик ---
@login_required
def cart_detail(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return render(request, 'store/cart.html', {'cart': cart})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save()
    messages.success(request, f'Товар "{product.name}" додано до кошика')
    return redirect('store:cart_detail')

@login_required
def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_object_or_404(Cart, user=request.user)
    try:
        item = CartItem.objects.get(cart=cart, product=product)
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
    except CartItem.DoesNotExist:
        pass
    return redirect('store:cart_detail')

@login_required
def clear_cart(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart.items.all().delete()
    messages.success(request, 'Кошик очищено')
    return redirect('store:cart_detail')

# --- Оформлення ---
@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    if not cart.items.exists():
        messages.warning(request, 'Ваш кошик порожній')
        return redirect('store:cart_detail')
    return render(request, 'store/checkout.html', {'cart': cart})

# --- Акаунт ---
@login_required
def account_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created')
    viewed_ids = request.session.get('viewed_products', [])
    viewed_products = Product.objects.filter(id__in=viewed_ids)
    return render(request, 'store/account.html', {'orders': orders, 'viewed_products': viewed_products})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Ви успішно вийшли з акаунту')
    return redirect('store:index')

@login_required
def clear_orders(request):
    Order.objects.filter(user=request.user).delete()
    messages.success(request, 'Всі замовлення видалені')
    return redirect('store:account')

# --- Замовлення ---
@login_required
def order_view(request):
    cart = get_object_or_404(Cart, user=request.user)
    if request.method == 'POST':
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
        for item in cart.items.all():
            OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, price=item.product.price)
        cart.items.all().delete()
        messages.success(request, 'Ваше замовлення оформлено успішно!')
        return redirect('store:order_success', order_id=order.id)
    return render(request, 'store/order.html', {'cart': cart})

@login_required
def order_success_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_success.html', {'order': order})

# --- Інфо-сторінки ---
def about_view(request):
    return render(request, 'store/about.html')

def contacts_view(request):
    return render(request, 'store/contacts.html')

@login_required
def edit_profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Профіль оновлено')
            return redirect('store:account')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)

    return render(request, 'store/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })