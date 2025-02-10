from django import forms
from .models import Membership, Attendance
from django.contrib.auth.models import User
from django.utils import timezone

class MembershipForm(forms.ModelForm):
    username = forms.CharField(
        label='用戶名', 
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})  # 添加 Bootstrap 样式
    )

    class Meta:
        model = Membership
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'membership_type'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'membership_type': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 如果是编辑现有会员，设置用户名初始值
        if self.instance and self.instance.pk:
            self.fields['username'].initial = self.instance.user.username
            # 如果是编辑模式，设置用户名为只读
            self.fields['username'].widget.attrs['readonly'] = True

    def save(self, commit=True):
        username = self.cleaned_data['username']
        # 检查用户是否存在，如果不存在则创建新用户
        user, created = User.objects.get_or_create(username=username)
        
        # 同步用戶資料到 User 模型
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.save()
        
        membership = super().save(commit=False)
        membership.user = user
        
        if commit:
            membership.save()
        return membership

class AttendanceForm(forms.ModelForm):
    member_id = forms.CharField(label='會員編號')

    class Meta:
        model = Attendance
        fields = ['member_id', 'notes']

    def clean_member_id(self):
        member_id = self.cleaned_data.get('member_id')
        try:
            Membership.objects.get(member_id=member_id)
            return member_id
        except Membership.DoesNotExist:
            raise forms.ValidationError('找不到此會員編號')

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # 設置會員
        member_id = self.cleaned_data.get('member_id')
        instance.member = Membership.objects.get(member_id=member_id)
        
        # 設置日期和時間
        now = timezone.localtime()
        instance.attendance_date = now.date()
        instance.check_in_time = now.time()
        
        if commit:
            try:
                instance.save()
            except Exception as e:
                raise forms.ValidationError(f'保存記錄時發生錯誤：{str(e)}')
        
        return instance