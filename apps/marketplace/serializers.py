from rest_framework import serializers
from apps.marketplace.models import Category, Store, Product, Cart, CartItem


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category"""
    icon_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'icon', 'icon_url', 'is_featured']
    
    def get_icon_url(self, obj):
        """Get full URL for icon"""
        if obj.icon:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.icon.url)
            return obj.icon.url
        return None


class StoreSerializer(serializers.ModelSerializer):
    """Serializer for Store"""
    logo_url = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Store
        fields = ['id', 'name', 'slug', 'description', 'owner_name', 'logo', 'logo_url', 
                  'cover_image', 'cover_image_url',
                  'address', 'phone_number', 'email', 'rating', 'total_sales', 'is_verified']
    
    def get_logo_url(self, obj):
        """Get full URL for logo"""
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None
    
    def get_cover_image_url(self, obj):
        """Get full URL for cover image"""
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product"""
    store_name = serializers.CharField(source='store.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    images = serializers.SerializerMethodField()
    primary_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'store_name', 'category_name', 'name', 'slug', 'description',
                  'short_description', 'price', 'compare_at_price', 'sku',
                  'stock_quantity', 'weight_kg', 'dimensions',
                  'is_available', 'is_featured', 'rating', 'total_sales', 
                  'images', 'primary_image_url']
    
    def get_images(self, obj):
        """Get full URLs for all product images"""
        request = self.context.get('request')
        images = obj.images or []
        
        if not images:
            return []
        
        absolute_urls = []
        for image_path in images:
            if image_path:
                if request:
                    # If it's already a full URL, return as is
                    if image_path.startswith('http'):
                        absolute_urls.append(image_path)
                    else:
                        absolute_urls.append(request.build_absolute_uri(image_path))
                else:
                    absolute_urls.append(image_path)
        return absolute_urls
    
    def get_primary_image_url(self, obj):
        """Get full URL for primary image (first image in array)"""
        images = self.get_images(obj)
        return images[0] if images else None


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for Cart Item"""
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'subtotal']
    
    def create(self, validated_data):
        cart = self.context['cart']
        product_id = validated_data.pop('product_id')
        
        try:
            product = Product.objects.get(id=product_id, is_active=True, is_available=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError({'product_id': 'Product not found or unavailable.'})
        
        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': validated_data['quantity']}
        )
        
        if not created:
            cart_item.quantity += validated_data['quantity']
            cart_item.save()
        
        return cart_item


class CartSerializer(serializers.ModelSerializer):
    """Serializer for Cart"""
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_items', 'total_amount']


class CheckoutSerializer(serializers.Serializer):
    """Serializer for checkout process"""
    payment_method = serializers.ChoiceField(choices=['PAYSTACK', 'CASH'], default='PAYSTACK')
    
    def validate(self, attrs):
        return attrs

