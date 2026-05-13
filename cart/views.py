from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from store.models import Cart, CartItem, ProductVariant
from .serializers import CartSerializer, CartItemSerializer


class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add(self, request):
        variant_id = request.data.get('variant_id')
        quantity = int(request.data.get('quantity', 1))

        variant = ProductVariant.objects.filter(id=variant_id).first()
        if not variant:
            return Response({'detail': 'Invalid variant.'}, status=status.HTTP_400_BAD_REQUEST)

        if variant.stock <= 0 or quantity > variant.stock:
            return Response({'detail': 'Insufficient stock.'}, status=status.HTTP_400_BAD_REQUEST)

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, variant=variant, product=variant.product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()
        return Response(CartItemSerializer(cart_item).data)

    @action(detail=True, methods=['post'])
    def update_quantity(self, request, pk=None):
        cart_item = CartItem.objects.filter(id=pk, cart__user=request.user).first()
        if not cart_item:
            return Response({'detail': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)

        quantity = int(request.data.get('quantity', cart_item.quantity))
        if quantity < 1:
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if quantity > cart_item.variant.stock:
            return Response({'detail': 'Not enough stock.'}, status=status.HTTP_400_BAD_REQUEST)

        cart_item.quantity = quantity
        cart_item.save()
        return Response(CartItemSerializer(cart_item).data)

    @action(detail=True, methods=['delete'])
    def remove(self, request, pk=None):
        cart_item = CartItem.objects.filter(id=pk, cart__user=request.user).first()
        if cart_item:
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'detail': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)
