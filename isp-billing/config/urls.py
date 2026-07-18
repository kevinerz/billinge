from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from tenants.views import TenantViewSet, TenantIntegrationViewSet
from subscribers.views import TenantSubscriberViewSet
from nas.views import NasViewSet
from billing.views import (
    PlatformPlanViewSet, TenantSubscriptionViewSet, PlatformInvoiceViewSet, PlatformPaymentViewSet,
    ServicePlanViewSet, SubscriberSubscriptionViewSet, SubscriberInvoiceViewSet, SubscriberPaymentViewSet,
)
from webhooks.views import PlatformPaymentWebhookView, SubscriberPaymentWebhookView
from webhooks.viewsets import PaymentGatewayEventViewSet, PaymentRefundViewSet

router = DefaultRouter()
router.register('tenants', TenantViewSet, basename='tenant')
router.register('tenant-integrations', TenantIntegrationViewSet, basename='tenant-integration')
router.register('subscribers', TenantSubscriberViewSet, basename='subscriber')
router.register('nas', NasViewSet, basename='nas')
router.register('platform-plans', PlatformPlanViewSet, basename='platform-plan')
router.register('tenant-subscriptions', TenantSubscriptionViewSet, basename='tenant-subscription')
router.register('platform-invoices', PlatformInvoiceViewSet, basename='platform-invoice')
router.register('platform-payments', PlatformPaymentViewSet, basename='platform-payment')
router.register('service-plans', ServicePlanViewSet, basename='service-plan')
router.register('subscriber-subscriptions', SubscriberSubscriptionViewSet, basename='subscriber-subscription')
router.register('subscriber-invoices', SubscriberInvoiceViewSet, basename='subscriber-invoice')
router.register('subscriber-payments', SubscriberPaymentViewSet, basename='subscriber-payment')
router.register('payment-gateway-events', PaymentGatewayEventViewSet, basename='payment-gateway-event')
router.register('payment-refunds', PaymentRefundViewSet, basename='payment-refund')

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/webhooks/platform-payments/<str:provider>/', PlatformPaymentWebhookView.as_view(), name='webhook-platform-payment'),
    path('api/webhooks/subscriber-payments/<str:tenant_slug>/<str:provider>/', SubscriberPaymentWebhookView.as_view(), name='webhook-subscriber-payment'),
    path('api/', include(router.urls)),
]
