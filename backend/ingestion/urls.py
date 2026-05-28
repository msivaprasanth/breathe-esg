from django.urls import path
from . import views

urlpatterns = [
    # Upload
    path('upload/', views.UploadView.as_view(), name='upload'),

    # Review
    path('review/', views.ReviewListView.as_view(), name='review-list'),
    path('review/<uuid:pk>/', views.ReviewDetailView.as_view(), name='review-detail'),
    path('review/<uuid:pk>/edit/', views.EditRecordView.as_view(), name='review-edit'),

    # Actions
    path('approve/', views.ApproveView.as_view(), name='approve'),
    path('reject/', views.RejectView.as_view(), name='reject'),

    # Dashboard
    path('dashboard/', views.DashboardMetricsView.as_view(), name='dashboard'),

    # Batches
    path('batches/', views.BatchListView.as_view(), name='batch-list'),

    # Tenant
    path('tenant/', views.TenantInfoView.as_view(), name='tenant-info'),
]