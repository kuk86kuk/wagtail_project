from django.shortcuts import render
import requests
from moysklad.views import get_products
import base64
import urllib3
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Product, CartItem
from Payment_services.tbank_service import TBankService

# Отключаем предупреждения
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
def contacts(request):
    return render(request, 'home/contacts.html')

def index(request):
    return render(request, 'home/index.html')

def company(request):
    return render(request, 'home/company.html')

def delivery(request):
    return render(request, 'home/delivery.html')

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def catalog(request):
    url = "http://127.0.0.1:8000//moysklad/products/"
    response = requests.get(url, verify=False)
    if response.status_code == 200:
        products_data = response.json()
        products = products_data.get('rows', [])
        
        # Добавляем изображения для каждого продукта
        for product in products:
            product_id = product.get('id')
            images_url = product.get('images', {}).get('meta', {}).get('href')
            
            if images_url:
                # Получаем список изображений
                url = f"http://127.0.0.1:8000//moysklad/products/{product_id}/images"
                images_response = requests.get(url, verify=False)
                
                if images_response.status_code == 200:
                    images_data = images_response.json()
                    if images_data.get('rows'):
                        # Получаем первое изображение
                        first_image_meta = images_data.get('rows', [])[0].get('meta', {}).get('href')
                        id_images = extract_uuid_from_href(first_image_meta)
                        
                        if id_images:
                            # Получаем изображение в формате Base64
                            url = f"http://127.0.0.1:8000//moysklad/products/{product_id}/images/{id_images}"
                            image_response = requests.get(url, verify=False)
                            
                            if image_response.status_code == 200:
                                image_base64 = base64.b64encode(image_response.content).decode('utf-8')
                                product['image_base64'] = image_base64  # Добавляем изображение в словарь продукта
        
        # Пагинация
        paginator = Paginator(products, 6)  # Показывать по 10 товаров на странице
        page = request.GET.get('page')  # Получаем текущую страницу из GET-параметра
        
        try:
            products_page = paginator.page(page)
        except PageNotAnInteger:
            # Если страница не является целым числом, возвращаем первую страницу
            products_page = paginator.page(1)
        except EmptyPage:
            # Если страница выходит за пределы допустимого диапазона, возвращаем последнюю страницу
            products_page = paginator.page(paginator.num_pages)
        
        context = {'products': products_page}
        return render(request, 'home/catalog.html', context)
    
    return render(request, 'home/catalog.html', {'products': []})


def catalog_category(request, category):
    url = "http://127.0.0.1:8000//moysklad/products/"
    response = requests.get(url, verify=False)
    if response.status_code == 200:
        products_data = response.json()
        products = products_data.get('rows', [])
        
        # Фильтруем продукты по значению "pathName"
        filtered_products = [product for product in products if product.get('pathName') == category]
        
        # Добавляем изображения для каждого продукта
        for product in filtered_products:
            product_id = product.get('id')
            images_url = product.get('images', {}).get('meta', {}).get('href')
            
            if images_url:
                # Получаем список изображений
                url = f"http://127.0.0.1:8000//moysklad/products/{product_id}/images"
                images_response = requests.get(url, verify=False)
                
                if images_response.status_code == 200:
                    images_data = images_response.json()
                    if images_data.get('rows'):
                        # Получаем первое изображение
                        first_image_meta = images_data.get('rows', [])[0].get('meta', {}).get('href')
                        id_images = extract_uuid_from_href(first_image_meta)
                        
                        if id_images:
                            # Получаем изображение в формате Base64
                            url = f"http://127.0.0.1:8000//moysklad/products/{product_id}/images/{id_images}"
                            image_response = requests.get(url, verify=False)
                            
                            if image_response.status_code == 200:
                                image_base64 = base64.b64encode(image_response.content).decode('utf-8')
                                product['image_base64'] = image_base64  # Добавляем изображение в словарь продукта
        
        context = {'products': filtered_products}
        return render(request, 'home/catalog.html', context)
    return render(request, 'home/catalog.html', {'products': []})

def catalog_id(request, product_id):
    context = {}  
    url = f"http://127.0.0.1:8000//moysklad/products/{product_id}/"
    response = requests.get(url, verify=False)
    if response.status_code == 200:
        product_data = response.json()
        context["product"] = product_data
        images_url = product_data.get('images', {}).get('meta', {})
        images_url = images_url.get('href')
        if images_url:
            # для получения id_images
            url = f"http://127.0.0.1:8000//moysklad/products/{product_id}/images"
            images_response = requests.get(url, verify=False)
            
            product_data = images_response.json()
            if product_data.get('rows'):
                product_data = product_data.get('rows', [])[0].get('meta', {}).get('href')
                id_images = extract_uuid_from_href(product_data)
            
                # # изображения
                url = f"http://127.0.0.1:8000//moysklad/products/{product_id}/images/{id_images}"
                images_response = requests.get(url, verify=False)
                import base64
                image_base64 = base64.b64encode(images_response.content).decode('utf-8')
                context["img"] = image_base64  # Сохраняем Base64-строку в контекст
        # Передаем данные в шаблон
        return render(request, 'home/product_detail.html', context)
    return render(request, 'home/product_detail.html', {'product': None})

def extract_uuid_from_href(href):
    import re
    # Регулярное выражение для поиска UUID
    match = re.search(r'/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/?$', href)
    if match:
        return match.group(1)  # Возвращаем UUID
    return None

def contacts(request):
    return render(request, 'home/contacts.html')










def view_cart(request):
    """
    Представление для отображения корзины.
    """
    cart_items = CartItem.objects.filter(user=request.user)
    total_amount = sum(item.total_price for item in cart_items)
    return render(request, "home/view_cart.html", {
        "cart_items": cart_items,
        "total_amount": total_amount,
    })
import logging

logger = logging.getLogger(__name__)

def checkout(request):
    if request.method == "POST":
        # Получаем корзину из сессии
        cart = request.session.get('cart', {})
        
        # Проверяем, есть ли товары в корзине
        if not cart:
            return JsonResponse({"error": "Корзина пуста"}, status=400)
        
        # Рассчитываем общую сумму заказа
        total_amount = sum(item['price'] * item['quantity'] for item in cart.values())

        # Данные для оплаты
        payment_data = {
            "payment_id": f"123",  # Уникальный ID заказа
            "account_number": "12345678900987654321",  # Номер счета отправителя
            "amount": float(total_amount),  # Сумма заказа
            "purpose": f"Оплата заказа от {request.user.username}",  # Назначение платежа
        }

        # Отправка данных на http://localhost:8000/Payment_services/create-payment/
        payment_url = "http://localhost:8000/Payment_services/create-payment/"
        headers = {"Content-Type": "application/json"}
        response = requests.post(payment_url, json=payment_data, headers=headers)
        logger.error(f"Ответ от API Т-Банка: {response.text}")
        # Обработка ответа
        if response.status_code == 201:  # Успешный платеж
            # Очистка корзины после успешной оплаты
            request.session['cart'] = {}
            return JsonResponse({"message": "Платеж успешно создан", "redirect_url": response.json().get("redirect_url")}, status=200)
        else:
            return JsonResponse({"error": "Ошибка при выполнении платежа", "details": response.json()}, status=500)
    else:
        return JsonResponse({"error": "Метод не поддерживается"}, status=405)

def add_to_cart(request, product_id):
    context = {}  
    url = f"http://127.0.0.1:8000//moysklad/products/{product_id}/"
    response = requests.get(url, verify=False)
    if response.status_code == 200:
        product_data = response.json()
        context["product"] = product_data
    print(context)
    
    
    # Добавляем товар в корзину (в сессии)
    cart = request.session.get('cart', {})
    
    cart_item = cart.get(product_id)
   
    if cart_item:
        cart_item['quantity'] += 1
    else:
        # Используем динамическое имя из JSON
        product_name = context["product"].get("name", f"Товар {product_id}")
        product_price = context["product"].get("salePrices", [{}])[0].get("value", 100.00)  # Берем цену напрямую
        
        cart[product_id] = {
            'id': product_id,
            'name': product_name,  # Динамическое имя из JSON
            'price': product_price,  # Цена из API
            'quantity': 1,
        }
    print(cart_item)
    request.session['cart'] = cart
    return redirect('view_cart')



def view_cart(request):
    cart = request.session.get('cart', {})
    
    # Преобразуем корзину в список товаров для отображения
    cart_items = []
    total_amount = 0
    for item_id, item in cart.items():
        item['total_price'] = item['price'] * item['quantity']  # Рассчитываем итоговую стоимость
        cart_items.append(item)
        total_amount += item['total_price']  # Суммируем итоговую стоимость
    
    # Передаем данные в шаблон
    return render(request, 'home/cart.html', {
        'cart_items': cart_items,  # Передаем список товаров
        'total_amount': total_amount,  # Передаем итоговую сумму
    })

from django.shortcuts import render, get_object_or_404

def product_detail(request, product_id):
    """
    Представление для отображения деталей товара.
    """
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'home/product_detail.html', {'product': product})