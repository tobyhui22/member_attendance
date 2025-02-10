from django.contrib import admin
from .models import Membership, Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('attendance_date', 'member', 'check_in_time', 'notes')
    list_filter = ('attendance_date', 'member__membership_type')
    search_fields = ('member__member_id', 'member__first_name', 'member__last_name')
    date_hierarchy = 'attendance_date'
    ordering = ('-attendance_date', '-check_in_time')

    def get_member_name(self, obj):
        return f"{obj.member.last_name}{obj.member.first_name}"
    get_member_name.short_description = '會員姓名'

    def get_member_type(self, obj):
        return obj.member.get_membership_type_display()
    get_member_type.short_description = '會員類型'

    fieldsets = (
        ('基本信息', {
            'fields': ('member', 'attendance_date', 'check_in_time')
        }),
        ('其他信息', {
            'fields': ('notes',)
        }),
    )

# 如果 Membership 還沒有註冊，也一併註冊
@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('member_id', 'last_name', 'first_name', 'membership_type', 'email', 'phone')
    list_filter = ('membership_type',)
    search_fields = ('member_id', 'first_name', 'last_name', 'email', 'phone')