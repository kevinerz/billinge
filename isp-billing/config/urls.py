from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from tenants.views import TenantViewSet
from subscribers.views import TenantSubscriberViewSet
from billing.views import (
    PlatformPlanViewSet, TenantSubscriptionViewSet, PlatformInvoiceViewSet, PlatformPaymentViewSet,
    ServicePlanViewSet, SubscriberSubscriptionViewSet, SubscriberInvoiceViewSet, SubscriberPaymentViewSet,
)

router = DefaultRouter()
router.register('tenants', TenantViewSet, basename='tenant')
router.register('subscribers', TenantSubscriberViewSet, basename='subscriber')
router.register('platform-plans', PlatformPlanViewSet, basename='platform-plan')
router.register('tenant-subscriptions', TenantSubscriptionViewSet, basename='tenant-subscription')
router.register('platform-invoices', PlatformInvoiceViewSet, basename='platform-invoice')
router.register('platform-payments', PlatformPaymentViewSet, basename='platform-payment')
router.register('service-plans', ServicePlanViewSet, basename='service-plan')
router.register('subscriber-subscriptions', SubscriberSubscriptionViewSet, basename='subscriber-subscription')
router.register('subscriber-invoices', SubscriberInvoiceViewSet, basename='subscriber-invoice')
router.register('subscriber-payments', SubscriberPaymentViewSet, basename='subscriber-payment')

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include(router.urls)),
]
