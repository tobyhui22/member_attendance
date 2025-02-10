import sys
import requests
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QMessageBox, QLineEdit, QLabel, QHBoxLayout, QDialog, QFormLayout

# Django API URL
API_URL = "http://127.0.0.1:8000/api/memberships/"

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("登入")
        layout = QFormLayout()

        self.usernameInput = QLineEdit()
        self.passwordInput = QLineEdit()
        self.passwordInput.setEchoMode(QLineEdit.EchoMode.Password)
        self.loginButton = QPushButton("登入")

        layout.addRow("用戶名:", self.usernameInput)
        layout.addRow("密碼:", self.passwordInput)
        layout.addRow(self.loginButton)

        self.loginButton.clicked.connect(self.login)
        self.setLayout(layout)

    def login(self):
        username = self.usernameInput.text()
        password = self.passwordInput.text()
        
        response = requests.post(
            "http://127.0.0.1:8000/api/login/",
            data={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            self.accept()
        else:
            QMessageBox.warning(self, "錯誤", "登入失敗")

class MembershipApp(QWidget):
    def __init__(self):
        super().__init__()
        self.session = requests.Session()  # 添加 session 來保持登入狀態
        if not self.show_login():
            sys.exit()
        self.initUI()

    def show_login(self):
        dialog = LoginDialog()
        return dialog.exec() == QDialog.DialogCode.Accepted

    def initUI(self):
        self.setWindowTitle("會員管理系統")
        self.setGeometry(100, 100, 400, 500)
        layout = QVBoxLayout()

        # 會員列表
        self.listWidget = QListWidget()
        layout.addWidget(self.listWidget)

        # 會員姓名輸入框
        self.nameInput = QLineEdit()
        self.nameInput.setPlaceholderText("輸入會員名稱")
        layout.addWidget(self.nameInput)

        # 按鈕區塊
        buttonLayout = QHBoxLayout()
        self.loadButton = QPushButton("刷新")
        self.addButton = QPushButton("新增會員")
        self.deleteButton = QPushButton("刪除選中會員")
        buttonLayout.addWidget(self.loadButton)
        buttonLayout.addWidget(self.addButton)
        buttonLayout.addWidget(self.deleteButton)

        layout.addLayout(buttonLayout)
        self.setLayout(layout)

        # 綁定按鈕事件
        self.loadButton.clicked.connect(self.load_members)
        self.addButton.clicked.connect(self.add_member)
        self.deleteButton.clicked.connect(self.delete_member)

        self.load_members()  # 啟動時載入會員

    def load_members(self):
        """ 加載會員列表 """
        self.listWidget.clear()
        try:
            response = self.session.get(API_URL)
            if response.status_code == 200:
                members = response.json()
                for member in members:
                    # 現在顯示用戶名和會員類型
                    self.listWidget.addItem(f"{member['id']}: {member['username']} - {member['membership_type']}")
            else:
                QMessageBox.warning(self, "錯誤", "無法獲取會員列表")
        except requests.exceptions.RequestException:
            QMessageBox.warning(self, "錯誤", "無法連接到伺服器")

    def add_member(self):
        """ 新增會員 """
        name = self.nameInput.text().strip()
        if not name:
            QMessageBox.warning(self, "錯誤", "請輸入會員名稱")
            return
        
        # 這裡需要使用者 ID，假設 user_id = 1（實際應該用登入用戶）
        new_member = {
            "user": 1,  # 測試用的 user_id
            "membership_type": "Basic"
        }
        response = self.session.post(API_URL, json=new_member)
        if response.status_code == 201:
            QMessageBox.information(self, "成功", "會員新增成功")
            self.load_members()
        else:
            QMessageBox.warning(self, "錯誤", "新增會員失敗")

    def delete_member(self):
        """ 刪除選中的會員 """
        selected_item = self.listWidget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "錯誤", "請選擇一個會員")
            return
        
        member_id = selected_item.text().split(":")[0]  # 取得 ID
        response = self.session.delete(f"{API_URL}{member_id}/")
        if response.status_code == 204:
            QMessageBox.information(self, "成功", "會員刪除成功")
            self.load_members()
        else:
            QMessageBox.warning(self, "錯誤", "刪除會員失敗")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MembershipApp()
    window.show()
    sys.exit(app.exec())