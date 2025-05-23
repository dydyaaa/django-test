from rest_framework import generics, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.filters import SearchFilter
from .serializers import UserSerializer, AdSerializer, ExchangeProposalSerializer
from .models import Ad, ExchangeProposal
from .permissions import IsOwnerOrReadOnly
from django.db.models import Q
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi


class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Имя пользователя (4-150 символов, только буквы, цифры и @/./+/-/_)',
                    maxLength=150,
                    minLength=4
                ),
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Электронная почта',
                    format='email'
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Пароль (не менее 8 символов)',
                    minLength=6
                ),
            },
            required=['username', 'email', 'password'],
        ),
        security=[]
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            'token': token.key
        }, status=status.HTTP_201_CREATED)
        

class CustomLoginView(ObtainAuthToken):
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(security=[])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    

class AdViewSet(viewsets.ModelViewSet):
    queryset = Ad.objects.all().order_by('-created_at')
    serializer_class = AdSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ['get', 'post', 'delete', 'patch']
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['category', 'condition']
    search_fields = ['^title', '^description']

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'category', openapi.IN_QUERY, description="Фильтр по категории", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'search', openapi.IN_QUERY, description="Поиск по названию или описанию", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'page', openapi.IN_QUERY, description="Номер страницы", type=openapi.TYPE_INTEGER
            ),
        ],
        security=[]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    def perform_update(self, serializer):
        ad = self.get_object()
        if ad.user != self.request.user:
            raise PermissionDenied('Вы не можете редактировать чужое объявление!')
        serializer.save()
        
    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied('Вы не можете удалить чужое объявление!')
        instance.delete()
        
class ExchangeProposalViewSet(viewsets.ModelViewSet):
    queryset = ExchangeProposal.objects.all()
    serializer_class = ExchangeProposalSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    http_method_names = ['get', 'post', 'delete', 'patch']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']
    pagination_class = None
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'status', 
                openapi.IN_QUERY, 
                description="Фильтр по статусу (pending, accepted, rejected)", 
                type=openapi.TYPE_STRING,
                enum=['pending', 'accepted', 'rejected']
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return ExchangeProposal.objects.filter(
                Q(ad_sender__user=user) | Q(ad_receiver__user=user)
            )
        return ExchangeProposal.objects.none()

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'ad_sender_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER, 
                    description='ID объявления отправителя'
                ),
                'ad_receiver_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER, 
                    description='ID объявления получателя'
                ),
                'comment': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Комментарий к предложению',
                    nullable=True
                ),
            },
            required=['ad_sender_id', 'ad_receiver_id'],
            example={
                'ad_sender_id': 1,
                'ad_receiver_id': 2,
                'comment': 'Хочу обменять книгу на ноутбук'
            }
        )
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save()
        
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Статус предложения',
                    enum=['accepted', 'rejected']
                ),
            },
            required=['status'],
            example={
                'status': 'accepted'
            }
        )
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def perform_update(self, serializer):
        if 'status' not in self.request.data:
            raise PermissionDenied("Можно обновлять только поле 'status'.")
        
        status_value = self.request.data.get('status')
        
        if status_value == 'accepted':
            with transaction.atomic():
                proposal = self.get_object()
                ad_sender = proposal.ad_sender
                ad_receiver = proposal.ad_receiver
                serializer.save()
                ad_sender.delete()
                ad_receiver.delete()
        else:
            serializer.save()
            
    def perform_destroy(self, instance):
        instance.delete()
        