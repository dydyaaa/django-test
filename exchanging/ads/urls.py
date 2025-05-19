from django.urls import path, include
from .views import RegisterView, AdViewSet, ExchangeProposalViewSet, CustomLoginView
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'ads', AdViewSet)
router.register(r'exchange', ExchangeProposalViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
]
