from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta, date, datetime
from django.utils import timezone

# 會員類型選項
MEMBERSHIP_TYPES = [
    ('Basic', 'Basic'),
    ('Premium', 'Premium'),
]

class Membership(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # 會員關聯 Django User
    membership_type = models.CharField(
        max_length=20, 
        choices=MEMBERSHIP_TYPES, 
        default='Basic'
    )
    start_date = models.DateField(auto_now_add=True)  # 會員開始日期
    
    # 修改字段定義，允許為空
    first_name = models.CharField(max_length=30, verbose_name="名字", blank=True, null=True)
    last_name = models.CharField(max_length=30, verbose_name="姓氏", blank=True, null=True)
    email = models.EmailField(verbose_name="電子郵件", blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="電話號碼")
    member_id = models.CharField(max_length=4, unique=True, verbose_name="會員編號")

    def save(self, *args, **kwargs):
        # 如果是新建會員且沒有會員編號，則自動生成
        if not self.member_id:
            # 獲取最後一個有效的會員編號
            last_member = Membership.objects.exclude(member_id__isnull=True).order_by('-member_id').first()
            if last_member and last_member.member_id:
                # 如果存在會員且有有效的會員編號，則在最後一個會員編號基礎上加1
                try:
                    last_id = int(last_member.member_id)
                    new_id = str(last_id + 1)
                except (ValueError, TypeError):
                    # 如果轉換失敗，從1001開始
                    new_id = '1001'
            else:
                # 如果沒有會員或沒有有效的會員編號，從1001開始
                new_id = '1001'
            self.member_id = new_id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.member_id} - {self.last_name or ''}{self.first_name or ''}"

    class Meta:
        ordering = ['member_id']  # 按會員編號排序
        verbose_name = "會員"
        verbose_name_plural = "會員"

class Attendance(models.Model):
    member = models.ForeignKey(Membership, on_delete=models.CASCADE)
    attendance_date = models.DateField(auto_now_add=True)  # 自動設置為當前日期
    check_in_time = models.TimeField(auto_now_add=True)   # 自動設置為當前時間
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-attendance_date', '-check_in_time']
        # 確保同一會員在同一天只能簽到一次
        unique_together = ['member', 'attendance_date']
        verbose_name = "出席記錄"
        verbose_name_plural = "出席記錄"

    def __str__(self):
        return f"{self.member.member_id} - {self.attendance_date}"

    def save(self, *args, **kwargs):
        if not self.pk:  # 只在創建新記錄時設置時間
            now = timezone.localtime()
            self.attendance_date = now.date()
            self.check_in_time = now.time()
        super().save(*args, **kwargs)

