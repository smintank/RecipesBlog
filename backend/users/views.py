from django.shortcuts import render, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.serializer import SubscribeSerializer
from users.models import Subscription, User

# Create your views here.
UNSUB_ERR_MSG = 'Нельзя отписаться, вы не подписаны!'


class SubscriptionListView(generics.ListAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscribeSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)


class SubscribeView(generics.CreateAPIView, generics.DestroyAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscribeSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        request.data['user'] = self.request.user.id
        request.data['subscription'] = get_object_or_404(
            User, id=self.kwargs.get('pk')).id
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        subscription = get_object_or_404(User, id=self.kwargs.get('pk')).id
        instance = self.queryset.filter(user=request.user.id,
                                        subscription=subscription)
        if not instance:
            return Response({'error': UNSUB_ERR_MSG},
                            status=status.HTTP_400_BAD_REQUEST)
        self.perform_destroy(instance.first())
        return Response(status=status.HTTP_204_NO_CONTENT)
