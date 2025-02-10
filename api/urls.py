from rest_framework import generics
from .models import Membership 
from django.urls import path
from .views import (
    MembershipListCreateView, 
    MembershipRetrieveUpdateDeleteView, 
    membership_list, 
    add_member, 
    edit_member, 
    delete_member, 
    login_view, 
    logout_view, 
    register_view, 
    attendance_list, 
    check_in,
    attendance_history,
    quick_check_in,
    member_qr,
    send_qr_email
)
from .serializers import MembershipSerializer
from django.contrib.auth.decorators import login_required



urlpatterns = [
    path('members/', membership_list, name='membership_list'),
    path('members/add/', add_member, name='add_member'),
    path('members/edit/<int:member_id>/', edit_member, name='edit_member'),
    path('members/delete/<int:member_id>/', delete_member, name='delete_member'),
    path('members/qr/<str:member_id>/', member_qr, name='member_qr'),
    path('members/qr/<str:member_id>/send-email/', send_qr_email, name='send_qr_email'),
    path('api/memberships/', MembershipListCreateView.as_view(), name='membership-list-create'),
    path('api/memberships/<int:pk>/', MembershipRetrieveUpdateDeleteView.as_view(), name='membership-detail'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('attendance/', login_required(attendance_list), name='attendance_list'),
    path('attendance/check-in/', login_required(check_in), name='check_in'),
    path('attendance/history/', login_required(attendance_history), name='attendance_history'),
    path('attendance/history/<str:member_id>/', attendance_history, name='member_attendance_history'),
    path('attendance/quick-check-in/<str:member_id>/', login_required(quick_check_in), name='quick_check_in'),
]
