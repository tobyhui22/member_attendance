from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import generics
from .models import Membership, Attendance
from .serializers import MembershipSerializer
from .forms import MembershipForm, AttendanceForm
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.contrib import messages
from django.utils import timezone
from datetime import date, datetime
from django.utils.dateparse import parse_date
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.http import HttpResponse, HttpResponseForbidden
import qrcode
import base64
from io import BytesIO
from django.urls import reverse
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

def login_view(request):
    """ 用戶登入 """
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('membership_list')  # 登入成功跳轉
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    """ 用戶登出 """
    logout(request)
    return redirect('login')

def register_view(request):
    """ 用戶註冊 """
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # 自動登入
            return redirect('membership_list')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

@login_required
def membership_list(request):
    """ 限制會員管理，只允許登入者訪問 """
    if not request.user.is_staff:  # 只允許管理員
        return redirect('login')
    members = Membership.objects.all()
    return render(request, 'membership.html', {'members': members})

class MembershipListCreateView(generics.ListCreateAPIView):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

class MembershipRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

@login_required
def membership_list(request):
    """ 顯示所有會員 """
    members = Membership.objects.all()
    return render(request, 'membership.html', {'members': members})

@login_required
def add_member(request):
    """ 新增會員 """
    if request.method == "POST":
        form = MembershipForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('membership_list')
    else:
        form = MembershipForm()
    return render(request, 'membership_form.html', {'form': form})

@login_required
def edit_member(request, member_id):
    """編輯會員信息"""
    member = get_object_or_404(Membership, id=member_id)  # 使用 id 查找
    
    if request.method == 'POST':
        form = MembershipForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, '會員資料更新成功')
            return redirect('membership_list')
    else:
        form = MembershipForm(instance=member)
    
    return render(request, 'membership_form.html', {
        'form': form,
        'member': member,
        'action': 'edit'
    })

@login_required
def delete_member(request, member_id):
    """ 刪除會員 """
    member = get_object_or_404(Membership, id=member_id)
    if request.method == "POST":
        member.delete()
        return redirect('membership_list')
    return render(request, 'membership_delete.html', {'member': member})

@login_required
def attendance_list(request):
    """顯示出席記錄列表"""
    try:
        # 獲取所有記錄
        attendances = Attendance.objects.all()
        
        # 處理會員編號搜索
        member_id = request.GET.get('member_id')
        if member_id:
            attendances = attendances.filter(member__member_id=member_id)
        
        # 處理日期範圍搜索
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date:
            try:
                start_date = parse_date(start_date)
                attendances = attendances.filter(attendance_date__gte=start_date)
            except ValueError:
                messages.error(request, '開始日期格式不正確')
        
        if end_date:
            try:
                end_date = parse_date(end_date)
                attendances = attendances.filter(attendance_date__lte=end_date)
            except ValueError:
                messages.error(request, '結束日期格式不正確')
        
        # 按日期和時間倒序排列
        attendances = attendances.order_by('-attendance_date', '-check_in_time')
        
        # 不需要手動處理時間格式，直接使用數據庫中的值
        return render(request, 'attendance_list.html', {
            'attendances': attendances,
        })
    except Exception as e:
        messages.error(request, f'發生錯誤：{str(e)}')
        return render(request, 'attendance_list.html', {
            'attendances': [],
        })

@login_required
def check_in(request):
    """會員簽到"""
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            try:
                member_id = form.cleaned_data['member_id']
                member = Membership.objects.get(member_id=member_id)
                
                # 檢查今天是否已經簽到
                today = timezone.localtime().date()
                existing_attendance = Attendance.objects.filter(
                    member=member,
                    attendance_date=today
                ).exists()
                
                if existing_attendance:
                    messages.warning(request, f'會員 {member_id} 今天已經簽到')
                else:
                    attendance = form.save(commit=False)
                    attendance.member = member
                    attendance.save()
                    messages.success(request, f'會員 {member_id} 簽到成功')
                
                return redirect('attendance_list')
            except Exception as e:
                messages.error(request, f'簽到時發生錯誤：{str(e)}')
        else:
            messages.error(request, '表單驗證失敗')
    else:
        form = AttendanceForm()
    
    return render(request, 'attendance_form.html', {'form': form})

@login_required
def attendance_history(request):
    """查看出席歷史記錄"""
    try:
        # 獲取所有記錄
        attendances = Attendance.objects.all()
        
        # 處理會員編號搜索
        member_id = request.GET.get('member_id')
        if member_id:
            attendances = attendances.filter(member__member_id=member_id)
        
        # 處理日期範圍搜索
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date:
            try:
                start_date = parse_date(start_date)
                attendances = attendances.filter(attendance_date__gte=start_date)
            except ValueError:
                messages.error(request, '開始日期格式不正確')
        
        if end_date:
            try:
                end_date = parse_date(end_date)
                attendances = attendances.filter(attendance_date__lte=end_date)
            except ValueError:
                messages.error(request, '結束日期格式不正確')
        
        # 生成每日摘要數據
        daily_summary = attendances.values('attendance_date').annotate(
            total_attendance=Count('id'),
            basic_members=Count('member', filter=Q(member__membership_type='Basic')),
            premium_members=Count('member', filter=Q(member__membership_type='Premium'))
        ).order_by('-attendance_date')
        
        # 按日期和時間倒序排列詳細記錄
        attendances = attendances.order_by('-attendance_date', '-check_in_time')
        
        return render(request, 'attendance_history.html', {
            'attendances': attendances,
            'daily_summary': daily_summary,
        })
    except Exception as e:
        messages.error(request, f'發生錯誤：{str(e)}')
        return render(request, 'attendance_history.html', {
            'attendances': [],
            'daily_summary': [],
        })

@login_required
def member_attendance_history(request, member_id):
    """查看特定會員的出席歷史記錄"""
    # ... 現有代碼 ...

@login_required
def quick_check_in(request, member_id):
    """快速簽到功能"""
    # 檢查用戶是否已登入
    if not request.user.is_authenticated:
        return HttpResponse("""
            <html>
            <head>
                <meta charset="utf-8">
                <script>
                    alert('請先登入系統');
                    window.close();
                </script>
            </head>
            <body>
                <p>請先登入系統</p>
                <p>如果視窗沒有自動關閉，請手動關閉此視窗。</p>
            </body>
            </html>
        """)

    try:
        # 查找會員
        member = get_object_or_404(Membership, member_id=member_id)
        
        # 檢查今天是否已經簽到
        today = timezone.localtime().date()
        existing_attendance = Attendance.objects.filter(
            member=member,
            attendance_date=today
        ).exists()
        
        if existing_attendance:
            message = f'會員 {member_id} 今天已經簽到'
            alert_type = 'warning'
        else:
            # 創建新的出席記錄
            attendance = Attendance.objects.create(
                member=member,
                notes=f"快速簽到 (by {request.user.username})"  # 記錄是誰執行的簽到
            )
            message = f'會員 {member_id} 簽到成功'
            alert_type = 'success'
        
    except Membership.DoesNotExist:
        message = f'找不到會員編號 {member_id}'
        alert_type = 'error'
    except Exception as e:
        message = f'簽到時發生錯誤：{str(e)}'
        alert_type = 'error'
    
    # 返回帶有 JavaScript 的 HTML 響應
    html_response = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <script>
            alert('{message}');
            window.close();
        </script>
    </head>
    <body>
        <p>{message}</p>
        <p>如果視窗沒有自動關閉，請手動關閉此視窗。</p>
    </body>
    </html>
    """
    
    return HttpResponse(html_response)

@login_required
def member_qr(request, member_id):
    """顯示會員QR碼頁面"""
    member = get_object_or_404(Membership, member_id=member_id)
    
    # 生成簽到URL
    quick_check_in_url = request.build_absolute_uri(
        reverse('quick_check_in', kwargs={'member_id': member_id})
    )
    
    # 創建QR碼
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(quick_check_in_url)
    qr.make(fit=True)
    
    # 生成QR碼圖片
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 將圖片轉換為base64字符串
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_code = base64.b64encode(buffer.getvalue()).decode()
    
    return render(request, 'member_qr.html', {
        'member': member,
        'qr_code': qr_code
    })

@login_required
def send_qr_email(request, member_id):
    """發送QR碼到會員信箱"""
    if request.method == 'POST':
        try:
            member = get_object_or_404(Membership, member_id=member_id)
            
            if not member.email:
                messages.error(request, '此會員沒有電子郵件地址')
                return redirect('member_qr', member_id=member_id)
            
            # 生成QR碼
            quick_check_in_url = request.build_absolute_uri(
                reverse('quick_check_in', kwargs={'member_id': member_id})
            )
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(quick_check_in_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 將QR碼保存到臨時文件
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_image = buffer.getvalue()
            
            # 準備郵件內容
            subject = f'您的會員簽到QR碼 - {member.member_id}'
            html_content = render_to_string('email/qr_code_email.html', {
                'member': member,
                'quick_check_in_url': quick_check_in_url,
            })
            
            # 創建郵件
            email = EmailMessage(
                subject,
                html_content,
                settings.DEFAULT_FROM_EMAIL,
                [member.email]
            )
            email.content_subtype = 'html'
            email.attach(f'qr_code_{member_id}.png', qr_image, 'image/png')
            
            # 發送郵件
            email.send()
            
            messages.success(request, f'QR碼已成功發送到 {member.email}')
            
        except Exception as e:
            messages.error(request, f'發送郵件時發生錯誤：{str(e)}')
        
        return redirect('member_qr', member_id=member_id)