from django.urls import path
from . import views
from test2 import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('user_login/', views.user_login, name='user_login'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('analyst_dashboard/', views.analyst_dashboard, name='analyst_dashboard'),
    path('research_dashboard/', views.research_dashboard, name='research_dashboard'),
    path('logout/', views.logout_view, name='logout'),
     
    path('add-region/', views.add_region, name='add-region'),
    # path('success/', views.success_page, name='success_page'),
    path('regions-list/', views.regions_list, name='regions-list'),
    
    
    path('upload_and_process/', views.upload_and_process, name='upload_and_process'),
    path('upload_image/', views.upload_image, name='upload_image'),
    path('region/', views.region, name='region'),
    path('download_report/<int:result_id>/', views.download_report, name='download_report'),
    
    # Password reset URLs
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
    
    # path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)