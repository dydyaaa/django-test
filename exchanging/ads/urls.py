from django.urls import path, include
from .views import RegisterView, AdViewSet, ExchangeProposalViewSet
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'ads', AdViewSet)
router.register(r'exchange', ExchangeProposalViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', obtain_auth_token, name='login'),
]
