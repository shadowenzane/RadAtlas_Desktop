import os
import sys
import sqlite3
import shutil

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextBrowser, QSplitter,
    QListWidget, QListWidgetItem, QTabWidget, QDialog,
    QMessageBox, QStatusBar, QFrame, QGroupBox, QSizePolicy,
    QScrollArea, QComboBox, QFileDialog, QMenu, QMenuBar,
    QAction, QCompleter, QToolBar, QSpinBox, QCheckBox
)
from PyQt5.QtCore import Qt, QSize, QStringListModel, pyqtSignal, QRect, QPoint
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QTextCursor, QPixmap, QPainter, QPen

from models import (
    init_user_db, authenticate_user, init_db, load_data,
    get_all_users, create_user, delete_user, change_password,
    rename_user, admin_change_password,
    hash_password, DATABASE, USER_DB, APP_DIR, copy_public_to_user,
    add_disease, update_disease, delete_disease,
    add_image, delete_image, get_disease, search_diseases
)

# ── 主题定义 ──────────────────────────────────────────────
THEMES = {
    '深蓝暗夜': {
        'bg': '#141416', 'bg2': '#1a1a1e', 'bg3': '#1e1e22',
        'fg': '#d9d9dc', 'fg2': '#888890', 'fg3': '#666670',
        'accent': '#3f7bf7', 'accent_hover': '#5a91ff', 'accent_press': '#2a5fd6',
        'border': '#2a2a30', 'danger': '#e64a3a', 'muted': '#3a3a40',
        'select_bg': '#2a3a5a', 'select_fg': '#5a91ff',
    },
    '极光绿': {
        'bg': '#0d1b12', 'bg2': '#122018', 'bg3': '#162a1e',
        'fg': '#d0e8d4', 'fg2': '#7aaa82', 'fg3': '#4a7a52',
        'accent': '#2ecc71', 'accent_hover': '#4ade80', 'accent_press': '#22a85a',
        'border': '#1e3a24', 'danger': '#e74c3c', 'muted': '#1e3a24',
        'select_bg': '#1a4a2a', 'select_fg': '#4ade80',
    },
    '暮光紫': {
        'bg': '#161220', 'bg2': '#1c1830', 'bg3': '#221e38',
        'fg': '#d8d0e8', 'fg2': '#9088a8', 'fg3': '#686080',
        'accent': '#9b59b6', 'accent_hover': '#b370cf', 'accent_press': '#7d3f98',
        'border': '#2e2848', 'danger': '#e74c3c', 'muted': '#2e2848',
        'select_bg': '#3a2860', 'select_fg': '#b370cf',
    },
    '暖沙': {
        'bg': '#1a1714', 'bg2': '#22201c', 'bg3': '#2a2824',
        'fg': '#e0d8cc', 'fg2': '#a09880', 'fg3': '#706850',
        'accent': '#e67e22', 'accent_hover': '#f0983a', 'accent_press': '#c06610',
        'border': '#3a3630', 'danger': '#e64a3a', 'muted': '#3a3630',
        'select_bg': '#4a3a20', 'select_fg': '#f0983a',
    },
    '浅色经典': {
        'bg': '#f5f5f8', 'bg2': '#ffffff', 'bg3': '#eeeef2',
        'fg': '#222230', 'fg2': '#666678', 'fg3': '#9999a8',
        'accent': '#3f7bf7', 'accent_hover': '#5a91ff', 'accent_press': '#2a5fd6',
        'border': '#d0d0d8', 'danger': '#e64a3a', 'muted': '#c0c0c8',
        'select_bg': '#d0e0ff', 'select_fg': '#3f7bf7',
    },
}


def build_stylesheet(t):
    """根据主题字典生成样式表"""
    return f"""
QMainWindow, QDialog {{
    background-color: {t['bg']};
}}
QWidget {{
    background-color: {t['bg']};
    color: {t['fg']};
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}}
QLabel {{
    background-color: transparent;
    color: {t['fg']};
}}
QLineEdit {{
    background-color: {t['bg2']};
    color: {t['fg']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 14px;
    selection-background-color: {t['accent']};
}}
QLineEdit:focus {{
    border-color: {t['accent']};
}}
QPushButton {{
    background-color: {t['accent']};
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: {t['accent_hover']};
}}
QPushButton:pressed {{
    background-color: {t['accent_press']};
}}
QPushButton#dangerBtn {{
    background-color: {t['danger']};
}}
QPushButton#dangerBtn:hover {{
    background-color: #f06050;
}}
QPushButton#mutedBtn {{
    background-color: {t['muted']};
}}
QPushButton#mutedBtn:hover {{
    background-color: {t['border']};
}}
QPushButton#tabBtn {{
    background-color: {t['bg2']};
    color: {t['fg2']};
    border: none;
    border-radius: 0px;
    padding: 10px 16px;
    font-weight: normal;
    border-bottom: 3px solid transparent;
}}
QPushButton#tabBtn:hover {{
    background-color: {t['bg3']};
    color: {t['fg']};
}}
QPushButton#tabBtn[active="true"] {{
    color: {t['accent']};
    border-bottom: 3px solid {t['accent']};
    font-weight: bold;
}}
QListWidget {{
    background-color: {t['bg2']};
    border: none;
    border-radius: 6px;
    outline: none;
    padding: 4px;
}}
QListWidget::item {{
    background-color: {t['bg3']};
    color: {t['fg']};
    border: none;
    border-radius: 4px;
    padding: 10px 12px;
    margin: 2px 0px;
}}
QListWidget::item:hover {{
    background-color: {t['border']};
}}
QListWidget::item:selected {{
    background-color: {t['select_bg']};
    color: {t['select_fg']};
}}
QListWidget::item:disabled {{
    color: {t['accent']};
    background-color: transparent;
    font-weight: bold;
    font-size: 12px;
    padding: 6px 12px;
}}
QTextBrowser {{
    background-color: {t['bg2']};
    color: {t['fg']};
    border: none;
    border-radius: 6px;
    padding: 12px;
    font-size: 13px;
}}
QStatusBar {{
    background-color: {t['bg2']};
    color: {t['fg2']};
    border-top: 1px solid {t['border']};
    font-size: 11px;
    padding: 4px 8px;
}}
QSplitter::handle {{
    background-color: {t['border']};
    width: 2px;
}}
QGroupBox {{
    border: 1px solid {t['border']};
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {t['accent']};
}}
QComboBox {{
    background-color: {t['bg2']};
    color: {t['fg']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    padding: 6px 12px;
}}
QComboBox::drop-down {{
    border: none;
}}
QComboBox QAbstractItemView {{
    background-color: {t['bg2']};
    color: {t['fg']};
    selection-background-color: {t['select_bg']};
}}
QMenuBar {{
    background-color: {t['bg2']};
    color: {t['fg']};
    border-bottom: 1px solid {t['border']};
}}
QMenuBar::item:selected {{
    background-color: {t['select_bg']};
}}
QMenu {{
    background-color: {t['bg2']};
    color: {t['fg']};
    border: 1px solid {t['border']};
}}
QMenu::item:selected {{
    background-color: {t['select_bg']};
}}
QScrollArea {{
    border: none;
    background-color: {t['bg']};
}}
QSpinBox {{
    background-color: {t['bg2']};
    color: {t['fg']};
    border: 1px solid {t['border']};
    border-radius: 4px;
    padding: 4px;
}}
"""


# 默认主题
DARK_STYLE = build_stylesheet(THEMES['深蓝暗夜'])


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_info = None
        self.setWindowTitle('RadAtlas - 登录')
        self.setFixedSize(400, 380)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 50, 40, 30)
        layout.setSpacing(12)

        title = QLabel('RadAtlas')
        title.setFont(QFont("Microsoft YaHei", 28, QFont.Bold))
        title.setStyleSheet("color: #3f7bf7; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel('影像图鉴助手')
        subtitle.setFont(QFont("Microsoft YaHei", 12))
        subtitle.setStyleSheet("color: #666670; background: transparent;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('用户名')
        self.username_input.setFixedHeight(44)
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('密码')
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(44)
        self.password_input.returnPressed.connect(self.do_login)
        layout.addWidget(self.password_input)

        layout.addSpacing(8)

        login_btn = QPushButton('登 录')
        login_btn.setFixedHeight(44)
        login_btn.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        login_btn.clicked.connect(self.do_login)
        layout.addWidget(login_btn)

        hint = QLabel('默认管理员: admin / admin123')
        hint.setStyleSheet("color: #555560; font-size: 11px; background: transparent;")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

        layout.addStretch()

        close_btn = QPushButton('×')
        close_btn.setParent(self)
        close_btn.setGeometry(self.width() - 36, 6, 30, 30)
        close_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #666; font-size: 18px; border: none; }
            QPushButton:hover { color: #fff; background: #e64a3a; border-radius: 4px; }
        """)
        close_btn.clicked.connect(self.reject)

    def do_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, '提示', '请输入用户名和密码')
            return
        try:
            user = authenticate_user(username, password)
        except Exception as e:
            QMessageBox.critical(self, '错误', f'认证失败:\n{e}')
            return
        if user:
            self.user_info = user
            self.accept()
        else:
            QMessageBox.warning(self, '错误', '用户名或密码错误')


# ── 添加/编辑疾病对话框 ──────────────────────────────────
class DiseaseDialog(QDialog):
    FIELDS = [
        ('name_cn', '中文名 *'),
        ('name_en', '英文名'),
        ('system', '系统'),
        ('category', '分类'),
        ('clinical', '临床表现'),
        ('diagnosis', '诊断要点'),
        ('primary_img', '主要影像方法'),
        ('secondary_img', '辅助影像方法'),
        ('xray_finding', 'X线所见'),
        ('ct_finding', 'CT所见'),
        ('mri_finding', 'MRI所见'),
        ('pet_finding', 'PET所见'),
        ('report_template', '报告模板'),
        ('differential_diagnosis', '鉴别诊断'),
        ('treatment', '治疗原则'),
    ]

    def __init__(self, parent=None, disease_data=None):
        super().__init__(parent)
        self.disease_data = disease_data
        self.setWindowTitle('编辑疾病' if disease_data else '添加疾病')
        self.setMinimumSize(600, 700)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        form = QVBoxLayout(inner)
        form.setSpacing(8)

        self.inputs = {}
        for key, label in self.FIELDS:
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: bold; font-size: 12px;")
            form.addWidget(lbl)
            inp = QLineEdit()
            if disease_data:
                inp.setText(disease_data.get(key, '') or '')
            self.inputs[key] = inp
            form.addWidget(inp)

        scroll.setWidget(inner)
        layout.addWidget(scroll)

        btn_row = QHBoxLayout()
        save_btn = QPushButton('保存')
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton('取消')
        cancel_btn.setObjectName('mutedBtn')
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def get_data(self):
        return {key: inp.text().strip() for key, inp in self.inputs.items()}


# ── 用户管理对话框 ────────────────────────────────────────
class UserManageDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('用户管理')
        self.setMinimumSize(520, 550)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 用户列表
        self.user_list = QListWidget()
        self.user_list.currentItemChanged.connect(self._on_user_selected)
        self._load_users()
        layout.addWidget(QLabel('已有用户:'))
        layout.addWidget(self.user_list)

        # 操作按钮行
        op_row = QHBoxLayout()
        edit_btn = QPushButton('修改用户名/密码')
        edit_btn.clicked.connect(self._edit_user)
        op_row.addWidget(edit_btn)
        del_btn = QPushButton('删除选中用户')
        del_btn.setObjectName('dangerBtn')
        del_btn.clicked.connect(self._delete_user)
        op_row.addWidget(del_btn)
        layout.addLayout(op_row)

        layout.addSpacing(10)

        # 添加用户区
        layout.addWidget(QLabel('添加新用户:'))
        add_form = QHBoxLayout()
        self.new_username = QLineEdit()
        self.new_username.setPlaceholderText('用户名')
        add_form.addWidget(self.new_username)
        self.new_password = QLineEdit()
        self.new_password.setPlaceholderText('密码')
        self.new_password.setEchoMode(QLineEdit.Password)
        add_form.addWidget(self.new_password)
        layout.addLayout(add_form)

        role_row = QHBoxLayout()
        role_row.addWidget(QLabel('角色:'))
        self.role_combo = QComboBox()
        self.role_combo.addItems(['user', 'admin'])
        role_row.addWidget(self.role_combo)
        role_row.addStretch()
        layout.addLayout(role_row)

        db_row = QHBoxLayout()
        db_row.addWidget(QLabel('数据库:'))
        self.db_combo = QComboBox()
        self.db_combo.addItems(['含基础数据库', '空数据库'])
        db_row.addWidget(self.db_combo)
        db_row.addStretch()
        layout.addLayout(db_row)

        add_btn = QPushButton('添加用户')
        add_btn.clicked.connect(self._add_user)
        layout.addWidget(add_btn)

    def _load_users(self):
        self.user_list.clear()
        for row in get_all_users():
            uid, username, role, database, created = row
            item = QListWidgetItem(f'[{role}] {username}  (ID:{uid})')
            item.setData(Qt.UserRole, uid)
            item.setData(Qt.UserRole + 1, username)
            item.setData(Qt.UserRole + 2, role)
            self.user_list.addItem(item)

    def _on_user_selected(self, current, previous):
        pass

    def _edit_user(self):
        item = self.user_list.currentItem()
        if not item:
            QMessageBox.warning(self, '提示', '请先选择一个用户')
            return
        uid = item.data(Qt.UserRole)
        old_name = item.data(Qt.UserRole + 1)
        dlg = EditUserDialog(self, uid, old_name)
        if dlg.exec_() == QDialog.Accepted:
            self._load_users()

    def _add_user(self):
        username = self.new_username.text().strip()
        password = self.new_password.text().strip()
        if not username or not password:
            QMessageBox.warning(self, '提示', '请输入用户名和密码')
            return
        role = self.role_combo.currentText()
        use_base = self.db_combo.currentIndex() == 0
        ok, db_path = create_user(username, password, role)
        if not ok:
            QMessageBox.warning(self, '错误', '用户名已存在')
            return
        init_db(db_path)
        if use_base:
            copy_public_to_user(db_path)
        self._load_users()
        self.new_username.clear()
        self.new_password.clear()
        QMessageBox.information(self, '成功', f'用户 {username} 已创建')

    def _delete_user(self):
        item = self.user_list.currentItem()
        if not item:
            return
        uid = item.data(Qt.UserRole)
        if QMessageBox.question(self, '确认', '确定删除该用户？') == QMessageBox.Yes:
            delete_user(uid)
            self._load_users()


class EditUserDialog(QDialog):
    """修改用户名和密码"""
    def __init__(self, parent, user_id, current_username):
        super().__init__(parent)
        self.user_id = user_id
        self.current_username = current_username
        self.setWindowTitle(f'修改用户 - {current_username}')
        self.setFixedSize(400, 260)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 修改用户名
        layout.addWidget(QLabel('修改用户名:'))
        name_row = QHBoxLayout()
        self.new_name_input = QLineEdit()
        self.new_name_input.setPlaceholderText('新用户名')
        self.new_name_input.setText(current_username)
        name_row.addWidget(self.new_name_input)
        rename_btn = QPushButton('修改')
        rename_btn.clicked.connect(self._rename)
        name_row.addWidget(rename_btn)
        layout.addLayout(name_row)

        layout.addSpacing(10)

        # 修改密码
        layout.addWidget(QLabel('修改密码:'))
        self.new_pwd_input = QLineEdit()
        self.new_pwd_input.setPlaceholderText('新密码')
        self.new_pwd_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.new_pwd_input)

        self.confirm_pwd_input = QLineEdit()
        self.confirm_pwd_input.setPlaceholderText('确认新密码')
        self.confirm_pwd_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.confirm_pwd_input)

        pwd_btn = QPushButton('修改密码')
        pwd_btn.clicked.connect(self._change_pwd)
        layout.addWidget(pwd_btn)

    def _rename(self):
        new_name = self.new_name_input.text().strip()
        if not new_name:
            QMessageBox.warning(self, '提示', '用户名不能为空')
            return
        if new_name == self.current_username:
            return
        if rename_user(self.user_id, new_name):
            self.current_username = new_name
            QMessageBox.information(self, '成功', '用户名已修改')
            self.accept()
        else:
            QMessageBox.warning(self, '错误', '用户名已存在')

    def _change_pwd(self):
        new_pwd = self.new_pwd_input.text().strip()
        confirm = self.confirm_pwd_input.text().strip()
        if not new_pwd:
            QMessageBox.warning(self, '提示', '请输入新密码')
            return
        if new_pwd != confirm:
            QMessageBox.warning(self, '提示', '两次密码输入不一致')
            return
        admin_change_password(self.user_id, new_pwd)
        QMessageBox.information(self, '成功', '密码已修改')
        self.accept()


# ── 图片编辑器 ────────────────────────────────────────────
class ImageEditorDialog(QDialog):
    """图片编辑器：支持缩放、文字注释、箭头、矩形、圆形"""

    TOOLS = [
        ('pan', '移动', '拖拽移动图片'),
        ('text', '文字', '点击添加文字注释'),
        ('arrow', '箭头', '拖拽绘制箭头'),
        ('line', '直线', '拖拽绘制直线'),
        ('rect', '矩形', '拖拽绘制矩形'),
        ('circle', '圆形', '拖拽绘制圆形'),
        ('eraser', '橡皮擦', '点击删除注释'),
    ]

    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle('图片编辑器')
        self.setMinimumSize(1000, 700)
        self.image_path = image_path
        self.scale = 1.0
        self.tool = 'pan'
        self.current_theme = self._detect_theme()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 左侧工具栏 ──
        toolbar_widget = QWidget()
        toolbar_widget.setFixedWidth(72)
        toolbar_widget.setObjectName('editorToolbar')
        toolbar_layout = QVBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(6, 10, 6, 10)
        toolbar_layout.setSpacing(4)

        # 工具标题
        tool_title = QLabel('工具')
        tool_title.setAlignment(Qt.AlignCenter)
        tool_title.setStyleSheet("font-weight: bold; font-size: 12px; background: transparent;")
        toolbar_layout.addWidget(tool_title)

        self.tool_buttons = {}
        for tool_id, tool_name, tool_tip in self.TOOLS:
            btn = QPushButton(tool_name)
            btn.setFixedSize(58, 34)
            btn.setToolTip(tool_tip)
            btn.setCheckable(True)
            btn.setChecked(tool_id == 'pan')
            btn.clicked.connect(lambda checked, tid=tool_id: self._set_tool(tid))
            self.tool_buttons[tool_id] = btn
            toolbar_layout.addWidget(btn)

        toolbar_layout.addSpacing(12)

        # 缩放控制
        zoom_title = QLabel('缩放')
        zoom_title.setAlignment(Qt.AlignCenter)
        zoom_title.setStyleSheet("font-weight: bold; font-size: 12px; background: transparent;")
        toolbar_layout.addWidget(zoom_title)

        zoom_row = QHBoxLayout()
        btn_zoom_out = QPushButton('-')
        btn_zoom_out.setFixedSize(26, 26)
        btn_zoom_out.clicked.connect(self._zoom_out)
        zoom_row.addWidget(btn_zoom_out)
        self.zoom_label = QLabel('100%')
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_label.setStyleSheet("background: transparent; font-size: 11px;")
        self.zoom_label.setFixedWidth(40)
        zoom_row.addWidget(self.zoom_label)
        btn_zoom_in = QPushButton('+')
        btn_zoom_in.setFixedSize(26, 26)
        btn_zoom_in.clicked.connect(self._zoom_in)
        zoom_row.addWidget(btn_zoom_in)
        toolbar_layout.addLayout(zoom_row)

        btn_fit = QPushButton('适应')
        btn_fit.setFixedSize(58, 28)
        btn_fit.setObjectName('mutedBtn')
        btn_fit.clicked.connect(self._zoom_fit)
        toolbar_layout.addWidget(btn_fit)

        toolbar_layout.addSpacing(12)

        # 颜色选择
        color_title = QLabel('颜色')
        color_title.setAlignment(Qt.AlignCenter)
        color_title.setStyleSheet("font-weight: bold; font-size: 12px; background: transparent;")
        toolbar_layout.addWidget(color_title)

        self.color_combo = QComboBox()
        self.color_combo.addItems(['红色', '黄色', '绿色', '蓝色', '白色', '黑色'])
        self.color_combo.setFixedWidth(58)
        toolbar_layout.addWidget(self.color_combo)

        # 线宽
        width_title = QLabel('线宽')
        width_title.setAlignment(Qt.AlignCenter)
        width_title.setStyleSheet("font-weight: bold; font-size: 12px; background: transparent;")
        toolbar_layout.addWidget(width_title)
        self.line_width = QSpinBox()
        self.line_width.setRange(1, 10)
        self.line_width.setValue(2)
        self.line_width.setFixedWidth(58)
        toolbar_layout.addWidget(self.line_width)

        toolbar_layout.addStretch()

        # 操作按钮
        btn_undo = QPushButton('撤销')
        btn_undo.setObjectName('mutedBtn')
        btn_undo.setFixedSize(58, 30)
        btn_undo.clicked.connect(self._undo)
        toolbar_layout.addWidget(btn_undo)

        btn_clear = QPushButton('清空')
        btn_clear.setObjectName('mutedBtn')
        btn_clear.setFixedSize(58, 30)
        btn_clear.clicked.connect(self._clear)
        toolbar_layout.addWidget(btn_clear)

        btn_save = QPushButton('保存')
        btn_save.setFixedSize(58, 30)
        btn_save.clicked.connect(self._save)
        toolbar_layout.addWidget(btn_save)

        layout.addWidget(toolbar_widget)

        # ── 右侧画布区 ──
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)

        # 顶部信息栏
        info_bar = QLabel(f'  {os.path.basename(image_path)}  |  当前工具: 移动')
        info_bar.setFixedHeight(28)
        info_bar.setObjectName('editorInfoBar')
        self.info_bar = info_bar
        right.addWidget(info_bar)

        # 画布
        self.canvas = ImageCanvas(self)
        self.canvas.image_path = image_path
        self.canvas.load_image()
        right.addWidget(self.canvas, stretch=1)

        layout.addLayout(right, stretch=1)

        self._apply_theme()

    def _detect_theme(self):
        """从父窗口检测当前主题"""
        app = QApplication.instance()
        if app:
            ss = app.styleSheet()
            for name, t in THEMES.items():
                if t['bg'] in ss:
                    return name
        return '深蓝暗夜'

    def _apply_theme(self):
        """根据当前主题设置编辑器样式"""
        t = THEMES[self.current_theme]
        is_light = self.current_theme == '浅色经典'
        bg = t['bg']
        bg2 = t['bg2']
        fg = t['fg']
        fg2 = t['fg2']
        border = t['border']
        accent = t['accent']
        muted = t['muted']

        self.setStyleSheet(f"""
        QDialog {{ background-color: {bg}; }}
        QWidget#editorToolbar {{
            background-color: {bg2};
            border-right: 1px solid {border};
        }}
        QWidget#editorInfoBar {{
            background-color: {bg2};
            color: {fg2};
            border-bottom: 1px solid {border};
            font-size: 11px;
        }}
        QPushButton {{
            background-color: {muted};
            color: {fg};
            border: 1px solid {border};
            border-radius: 4px;
            font-size: 12px;
        }}
        QPushButton:hover {{
            background-color: {border};
        }}
        QPushButton:checked {{
            background-color: {accent};
            color: #ffffff;
            border-color: {accent};
        }}
        QPushButton#mutedBtn {{
            background-color: {muted};
        }}
        QPushButton#mutedBtn:hover {{
            background-color: {border};
        }}
        QLabel {{
            background-color: transparent;
            color: {fg};
        }}
        QComboBox {{
            background-color: {muted};
            color: {fg};
            border: 1px solid {border};
            border-radius: 4px;
            padding: 2px 4px;
            font-size: 11px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {bg2};
            color: {fg};
            selection-background-color: {accent};
        }}
        QSpinBox {{
            background-color: {muted};
            color: {fg};
            border: 1px solid {border};
            border-radius: 4px;
            padding: 2px;
            font-size: 11px;
        }}
        """)

        # 更新画布背景色
        self.canvas.bg_color = QColor(245, 245, 248) if is_light else QColor(20, 20, 22)
        self.canvas.update()

    def _get_color(self):
        """获取当前选择的注释颜色"""
        colors = {
            '红色': QColor(255, 80, 80),
            '黄色': QColor(255, 220, 50),
            '绿色': QColor(80, 220, 80),
            '蓝色': QColor(80, 140, 255),
            '白色': QColor(255, 255, 255),
            '黑色': QColor(0, 0, 0),
        }
        return colors.get(self.color_combo.currentText(), QColor(255, 80, 80))

    def _set_tool(self, tool):
        self.tool = tool
        self.canvas.tool = tool
        for tid, btn in self.tool_buttons.items():
            btn.setChecked(tid == tool)
        tool_names = {t[0]: t[1] for t in self.TOOLS}
        self.info_bar.setText(f'  {os.path.basename(self.image_path)}  |  当前工具: {tool_names.get(tool, tool)}')

    def _zoom_in(self):
        self.scale = min(self.scale * 1.25, 5.0)
        self.canvas.scale = self.scale
        self.zoom_label.setText(f'{int(self.scale * 100)}%')
        self.canvas.update()

    def _zoom_out(self):
        self.scale = max(self.scale / 1.25, 0.1)
        self.canvas.scale = self.scale
        self.zoom_label.setText(f'{int(self.scale * 100)}%')
        self.canvas.update()

    def _zoom_fit(self):
        if self.canvas.pixmap:
            cw = self.canvas.width()
            ch = self.canvas.height()
            pw = self.canvas.pixmap.width()
            ph = self.canvas.pixmap.height()
            if pw > 0 and ph > 0:
                self.scale = min(cw / pw, ch / ph) * 0.9
                self.canvas.scale = self.scale
                self.canvas.offset = QPoint(0, 0)
                self.zoom_label.setText(f'{int(self.scale * 100)}%')
                self.canvas.update()

    def _undo(self):
        if self.canvas.annotations:
            self.canvas.annotations.pop()
            self.canvas.update()

    def _clear(self):
        if self.canvas.annotations:
            if QMessageBox.question(self, '确认', '清空所有注释？') == QMessageBox.Yes:
                self.canvas.annotations.clear()
                self.canvas.update()

    def _save(self):
        self.canvas.save_annotated(self.image_path)
        self.accept()


class ImageCanvas(QWidget):
    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.image_path = None
        self.pixmap = None
        self.scale = 1.0
        self.tool = 'pan'
        self.annotations = []
        self.drawing = False
        self.draw_start = None
        self.draw_current = None
        self.offset = QPoint(0, 0)
        self.dragging = False
        self.last_pos = None
        self.bg_color = QColor(20, 20, 22)
        self.setMouseTracking(True)

    def load_image(self):
        if self.image_path and os.path.exists(self.image_path):
            self.pixmap = QPixmap(self.image_path)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), self.bg_color)

        if not self.pixmap:
            painter.end()
            return

        # 绘制图片
        scaled = self.pixmap.scaled(
            self.pixmap.size() * self.scale,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        x = (self.width() - scaled.width()) // 2 + self.offset.x()
        y = (self.height() - scaled.height()) // 2 + self.offset.y()
        painter.drawPixmap(x, y, scaled)

        # 获取当前颜色和线宽
        color = self.editor._get_color()
        line_w = self.editor.line_width.value()

        # 绘制已有注释
        for ann in self.annotations:
            atype, data = ann
            ann_color = data.get('color', color)
            ann_width = data.get('width', line_w)
            pen = QPen(ann_color, ann_width)
            painter.setPen(pen)
            if atype == 'text':
                text_color = ann_color
                painter.setPen(QPen(text_color, 1))
                font_size = max(10, int(14 * self.scale))
                painter.setFont(QFont("Microsoft YaHei", font_size, QFont.Bold))
                # 绘制文字背景（浅色主题下提高可读性）
                fm = painter.fontMetrics()
                text_rect = fm.boundingRect(data['text'])
                bg_rect = QRect(data['x'] + x - 2, data['y'] + y - text_rect.height() - 2,
                                text_rect.width() + 4, text_rect.height() + 4)
                painter.fillRect(bg_rect, QColor(0, 0, 0, 120))
                painter.drawText(data['x'] + x, data['y'] + y, data['text'])
            elif atype == 'arrow':
                self._draw_arrow(painter, data['x1'] + x, data['y1'] + y,
                                 data['x2'] + x, data['y2'] + y, ann_color, ann_width)
            elif atype == 'line':
                painter.drawLine(int(data['x1'] + x), int(data['y1'] + y),
                                 int(data['x2'] + x), int(data['y2'] + y))
            elif atype == 'rect':
                painter.drawRect(data['x'] + x, data['y'] + y, data['w'], data['h'])
            elif atype == 'circle':
                painter.drawEllipse(data['x'] + x, data['y'] + y, data['w'], data['h'])

        # 绘制当前正在绘制的图形
        if self.drawing and self.draw_start and self.draw_current:
            pen = QPen(color, line_w)
            painter.setPen(pen)
            if self.tool == 'arrow':
                self._draw_arrow(painter, self.draw_start.x(), self.draw_start.y(),
                                 self.draw_current.x(), self.draw_current.y(), color, line_w)
            elif self.tool == 'line':
                painter.drawLine(self.draw_start, self.draw_current)
            elif self.tool == 'rect':
                rx = min(self.draw_start.x(), self.draw_current.x())
                ry = min(self.draw_start.y(), self.draw_current.y())
                rw = abs(self.draw_current.x() - self.draw_start.x())
                rh = abs(self.draw_current.y() - self.draw_start.y())
                painter.drawRect(rx, ry, rw, rh)
            elif self.tool == 'circle':
                rx = min(self.draw_start.x(), self.draw_current.x())
                ry = min(self.draw_start.y(), self.draw_current.y())
                rw = abs(self.draw_current.x() - self.draw_start.x())
                rh = abs(self.draw_current.y() - self.draw_start.y())
                painter.drawEllipse(rx, ry, rw, rh)

        painter.end()

    def _draw_arrow(self, painter, x1, y1, x2, y2, color=None, width=2):
        import math
        pen = QPen(color or QColor(255, 80, 80), width)
        painter.setPen(pen)
        painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        angle = math.atan2(y2 - y1, x2 - x1)
        arrow_size = max(10, width * 5)
        p1 = QPoint(int(x2 - arrow_size * math.cos(angle - 0.4)),
                     int(y2 - arrow_size * math.sin(angle - 0.4)))
        p2 = QPoint(int(x2 - arrow_size * math.cos(angle + 0.4)),
                     int(y2 - arrow_size * math.sin(angle + 0.4)))
        from PyQt5.QtGui import QPolygon
        painter.setBrush(color or QColor(255, 80, 80))
        painter.drawPolygon(QPolygon([QPoint(int(x2), int(y2)), p1, p2]))
        painter.setBrush(Qt.NoBrush)

    def _img_coords(self, pos):
        """将屏幕坐标转换为图片相对坐标"""
        if not self.pixmap:
            return pos.x(), pos.y()
        scaled = self.pixmap.scaled(
            self.pixmap.size() * self.scale,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        x = (self.width() - scaled.width()) // 2 + self.offset.x()
        y = (self.height() - scaled.height()) // 2 + self.offset.y()
        return pos.x() - x, pos.y() - y

    def _find_annotation_at(self, img_x, img_y, threshold=15):
        """查找指定坐标附近的注释索引"""
        for i in range(len(self.annotations) - 1, -1, -1):
            atype, data = self.annotations[i]
            if atype == 'text':
                if abs(data['x'] - img_x) < 50 and abs(data['y'] - img_y) < 30:
                    return i
            elif atype in ('arrow', 'line'):
                mx = (data['x1'] + data['x2']) / 2
                my = (data['y1'] + data['y2']) / 2
                if abs(mx - img_x) < threshold * 3 and abs(my - img_y) < threshold * 3:
                    return i
            elif atype in ('rect', 'circle'):
                cx = data['x'] + data['w'] / 2
                cy = data['y'] + data['h'] / 2
                if abs(cx - img_x) < max(data['w'] / 2, threshold) and \
                   abs(cy - img_y) < max(data['h'] / 2, threshold):
                    return i
        return -1

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        if self.tool == 'pan':
            self.dragging = True
            self.last_pos = event.pos()
        elif self.tool == 'text':
            ix, iy = self._img_coords(event.pos())
            from PyQt5.QtWidgets import QInputDialog
            text, ok = QInputDialog.getText(self, '添加文字', '注释文字:')
            if ok and text:
                color = self.editor._get_color()
                self.annotations.append(('text', {
                    'x': ix, 'y': iy, 'text': text,
                    'color': color, 'width': self.editor.line_width.value()
                }))
                self.update()
        elif self.tool == 'eraser':
            ix, iy = self._img_coords(event.pos())
            idx = self._find_annotation_at(ix, iy)
            if idx >= 0:
                self.annotations.pop(idx)
                self.update()
        else:
            self.drawing = True
            self.draw_start = event.pos()
            self.draw_current = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging and self.last_pos:
            delta = event.pos() - self.last_pos
            self.offset += delta
            self.last_pos = event.pos()
            self.update()
        elif self.drawing:
            self.draw_current = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        if self.dragging:
            self.dragging = False
            self.last_pos = None
        elif self.drawing and self.draw_start and self.draw_current:
            ix1, iy1 = self._img_coords(self.draw_start)
            ix2, iy2 = self._img_coords(self.draw_current)
            color = self.editor._get_color()
            width = self.editor.line_width.value()
            if self.tool == 'arrow':
                self.annotations.append(('arrow', {
                    'x1': ix1, 'y1': iy1, 'x2': ix2, 'y2': iy2,
                    'color': color, 'width': width
                }))
            elif self.tool == 'line':
                self.annotations.append(('line', {
                    'x1': ix1, 'y1': iy1, 'x2': ix2, 'y2': iy2,
                    'color': color, 'width': width
                }))
            elif self.tool == 'rect':
                rx = min(ix1, ix2)
                ry = min(iy1, iy2)
                self.annotations.append(('rect', {
                    'x': rx, 'y': ry, 'w': abs(ix2 - ix1), 'h': abs(iy2 - iy1),
                    'color': color, 'width': width
                }))
            elif self.tool == 'circle':
                rx = min(ix1, ix2)
                ry = min(iy1, iy2)
                self.annotations.append(('circle', {
                    'x': rx, 'y': ry, 'w': abs(ix2 - ix1), 'h': abs(iy2 - iy1),
                    'color': color, 'width': width
                }))
            self.drawing = False
            self.draw_start = None
            self.draw_current = None
            self.update()

    def save_annotated(self, path):
        """保存带注释的图片"""
        if not self.pixmap:
            return
        result = QPixmap(self.pixmap.size())
        result.fill(QColor(0, 0, 0, 0))
        painter = QPainter(result)
        painter.drawPixmap(0, 0, self.pixmap)

        for ann in self.annotations:
            atype, data = ann
            color = data.get('color', QColor(255, 80, 80))
            width = data.get('width', 2)
            pen = QPen(color, width)
            painter.setPen(pen)
            if atype == 'text':
                painter.setPen(QPen(color, 1))
                painter.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
                painter.drawText(data['x'], data['y'], data['text'])
                painter.setPen(pen)
            elif atype == 'arrow':
                self._draw_arrow(painter, data['x1'], data['y1'], data['x2'], data['y2'], color, width)
            elif atype == 'line':
                painter.drawLine(int(data['x1']), int(data['y1']), int(data['x2']), int(data['y2']))
            elif atype == 'rect':
                painter.drawRect(data['x'], data['y'], data['w'], data['h'])
            elif atype == 'circle':
                painter.drawEllipse(data['x'], data['y'], data['w'], data['h'])

        painter.end()
        base, ext = os.path.splitext(path)
        save_path = base + '_annotated' + ext
        result.save(save_path)


# ── 详情面板 ──────────────────────────────────────────────
class DetailPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_disease_id = None
        self.active_db = DATABASE
        self.disease_data = None
        self.current_tab = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标签栏
        tab_bar = QHBoxLayout()
        tab_bar.setContentsMargins(0, 0, 0, 0)
        tab_bar.setSpacing(0)

        self.tab_buttons = []
        tab_names = ['临床与诊断', '标准报告模板', '影像所见与资料', '医学资料', '影像解剖图谱与资料']
        for i, name in enumerate(tab_names):
            btn = QPushButton(name)
            btn.setObjectName('tabBtn')
            btn.setProperty('active', i == 0)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=i: self.switch_tab(idx))
            self.tab_buttons.append(btn)
            tab_bar.addWidget(btn)

        layout.addLayout(tab_bar)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #2a2a30; max-height: 1px;")
        layout.addWidget(line)

        # 内容区
        self.content_browser = QTextBrowser()
        self.content_browser.setOpenExternalLinks(True)
        self.content_browser.setStyleSheet("border: none; padding: 16px;")
        layout.addWidget(self.content_browser)

        # 图片缩略图列表（仅影像所见标签页显示）
        self.thumb_list = QListWidget()
        self.thumb_list.setViewMode(QListWidget.IconMode)
        self.thumb_list.setIconSize(QSize(200, 150))
        self.thumb_list.setSpacing(8)
        self.thumb_list.setResizeMode(QListWidget.Adjust)
        self.thumb_list.setMovement(QListWidget.Static)
        self.thumb_list.itemDoubleClicked.connect(self._on_thumb_double_clicked)
        self.thumb_list.hide()
        layout.addWidget(self.thumb_list)

        # 影像操作栏（仅影像所见标签页显示）
        self.img_action_bar = QWidget()
        img_action_layout = QHBoxLayout(self.img_action_bar)
        img_action_layout.setContentsMargins(8, 4, 8, 4)
        img_action_layout.setSpacing(8)

        self.btn_open_img = QPushButton('添加图片文件')
        self.btn_open_img.setFixedHeight(32)
        self.btn_open_img.clicked.connect(self._open_image_file)
        img_action_layout.addWidget(self.btn_open_img)

        self.btn_paste_img = QPushButton('粘贴剪贴板图片')
        self.btn_paste_img.setFixedHeight(32)
        self.btn_paste_img.clicked.connect(self._paste_clipboard_image)
        img_action_layout.addWidget(self.btn_paste_img)

        img_action_layout.addStretch()
        self.img_action_bar.hide()
        layout.addWidget(self.img_action_bar)

    def switch_tab(self, idx):
        self.current_tab = idx
        for i, btn in enumerate(self.tab_buttons):
            btn.setProperty('active', i == idx)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        # 影像操作栏和缩略图列表仅在影像所见标签页显示
        is_imaging = (idx == 2)
        self.img_action_bar.setVisible(is_imaging)
        self.thumb_list.setVisible(is_imaging)
        self._refresh_content()

    def load_disease(self, disease_id, db_path):
        self.current_disease_id = disease_id
        self.active_db = db_path
        data = get_disease(db_path, disease_id)
        if data:
            self.disease_data = data
        else:
            self.disease_data = None
        self._refresh_content()

    def _open_image_file(self):
        if not self.current_disease_id:
            QMessageBox.warning(self, '提示', '请先选择一个疾病')
            return
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, '选择图片', '', 'Images (*.png *.jpg *.jpeg *.bmp *.gif)')
        if not file_paths:
            return
        img_dir = os.path.join(APP_DIR, 'images')
        os.makedirs(img_dir, exist_ok=True)
        for fp in file_paths:
            filename = os.path.basename(fp)
            dest = os.path.join(img_dir, filename)
            if os.path.exists(dest) and dest != fp:
                base, ext = os.path.splitext(filename)
                i = 1
                while os.path.exists(os.path.join(img_dir, f'{base}_{i}{ext}')):
                    i += 1
                filename = f'{base}_{i}{ext}'
                dest = os.path.join(img_dir, filename)
            if fp != dest:
                shutil.copy2(fp, dest)
            add_image(self.active_db, self.current_disease_id, filename, '', '', '', 'image')
        self._refresh_content()

    def _paste_clipboard_image(self):
        if not self.current_disease_id:
            QMessageBox.warning(self, '提示', '请先选择一个疾病')
            return
        clipboard = QApplication.clipboard()
        pixmap = clipboard.pixmap()
        if pixmap.isNull():
            QMessageBox.warning(self, '提示', '剪贴板中没有图片')
            return
        img_dir = os.path.join(APP_DIR, 'images')
        os.makedirs(img_dir, exist_ok=True)
        # 生成唯一文件名
        import time
        filename = f'paste_{int(time.time() * 1000)}.png'
        dest = os.path.join(img_dir, filename)
        while os.path.exists(dest):
            filename = f'paste_{int(time.time() * 1000)}_{os.getpid()}.png'
            dest = os.path.join(img_dir, filename)
        pixmap.save(dest, 'PNG')
        add_image(self.active_db, self.current_disease_id, filename, '', '', '', 'image')
        self._refresh_content()

    def _refresh_content(self):
        if not self.disease_data:
            self.content_browser.setHtml('<p style="color:#666;">请从左侧选择一个疾病</p>')
            return
        d = self.disease_data
        if self.current_tab == 0:
            self._show_clinical_tab(d)
        elif self.current_tab == 1:
            self._show_report_tab(d)
        elif self.current_tab == 2:
            self._show_imaging_tab(d)
        elif self.current_tab == 3:
            self._show_medical_tab()
        elif self.current_tab == 4:
            self._show_anatomy_tab()

    def _html_heading(self, text, level=2):
        colors = {1: '#3f7bf7', 2: '#5a91ff', 3: '#7aadff'}
        color = colors.get(level, '#5a91ff')
        return f'<h{level} style="color:{color}; margin-top:16px; margin-bottom:8px;">{text}</h{level}>'

    def _html_body(self, text):
        return f'<div style="color:#c8c8cc; line-height:1.8; white-space:pre-wrap;">{text}</div>'

    def _show_clinical_tab(self, d):
        html = f'''
        <h1 style="color:#3f7bf7; margin-bottom:4px;">{d.get("name_cn","")}</h1>
        <p style="color:#888890; font-style:italic; margin-top:0;">{d.get("name_en","")}</p>
        <p style="color:#888890;">系统: {d.get("system","")} &nbsp;|&nbsp; 分类: {d.get("category","")}</p>
        <hr style="border:1px solid #2a2a30;">
        {self._html_heading("临床表现")}
        {self._html_body(d.get("clinical",""))}
        {self._html_heading("诊断要点")}
        {self._html_body(d.get("diagnosis",""))}
        {self._html_heading("鉴别诊断")}
        {self._html_body(d.get("differential_diagnosis",""))}
        {self._html_heading("治疗原则")}
        {self._html_body(d.get("treatment",""))}
        '''
        self.content_browser.setHtml(html)

    def _show_report_tab(self, d):
        html = f'''
        {self._html_heading("影像报告模板")}
        {self._html_body(d.get("report_template",""))}
        '''
        self.content_browser.setHtml(html)

    def _show_imaging_tab(self, d):
        if not self.current_disease_id:
            self.content_browser.setHtml('<p style="color:#666;">请先选择疾病</p>')
            self.thumb_list.clear()
            return
        conn = sqlite3.connect(self.active_db)
        c = conn.cursor()
        c.execute("SELECT id, filename, caption, media_type FROM images WHERE disease_id=?",
                  (self.current_disease_id,))
        rows = c.fetchall()
        conn.close()

        html = f'{self._html_heading("影像所见")}'
        if d.get('xray_finding'):
            html += f'{self._html_heading("X线", 3)}{self._html_body(d["xray_finding"])}'
        if d.get('ct_finding'):
            html += f'{self._html_heading("CT", 3)}{self._html_body(d["ct_finding"])}'
        if d.get('mri_finding'):
            html += f'{self._html_heading("MRI", 3)}{self._html_body(d["mri_finding"])}'
        if d.get('pet_finding'):
            html += f'{self._html_heading("PET", 3)}{self._html_body(d["pet_finding"])}'
        html += f'<p style="color:#888890; margin-top:16px;">共 {len(rows)} 张影像（双击图片进入编辑）</p>'
        self.content_browser.setHtml(html)

        # 填充缩略图列表
        self.thumb_list.clear()
        for img_id, filename, caption, media_type in rows:
            img_path = os.path.join(APP_DIR, 'images', filename) if filename else ''
            if os.path.exists(img_path):
                pixmap = QPixmap(img_path)
                icon = QIcon(pixmap.scaled(200, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                item = QListWidgetItem(icon, caption or filename or '')
                item.setData(Qt.UserRole, img_id)
                item.setData(Qt.UserRole + 1, img_path)
                self.thumb_list.addItem(item)

    def _on_thumb_double_clicked(self, item):
        img_path = item.data(Qt.UserRole + 1)
        if img_path and os.path.exists(img_path):
            editor = ImageEditorDialog(img_path, self)
            editor.exec_()

    def _show_medical_tab(self):
        if not self.current_disease_id:
            self.content_browser.setHtml('<p style="color:#666;">请先选择疾病</p>')
            return
        conn = sqlite3.connect(self.active_db)
        c = conn.cursor()
        c.execute("SELECT title, content FROM medical_records WHERE disease_id=?",
                  (self.current_disease_id,))
        rows = c.fetchall()
        conn.close()
        if not rows:
            self.content_browser.setHtml('<p style="color:#666;">暂无医学资料</p>')
            return
        html = f'{self._html_heading("医学资料")}'
        for title, content in rows:
            html += f'{self._html_heading(title, 3)}{self._html_body(content)}'
        self.content_browser.setHtml(html)

    def _show_anatomy_tab(self):
        conn = sqlite3.connect(self.active_db)
        c = conn.cursor()
        c.execute("SELECT title, content FROM anatomy_records")
        rows = c.fetchall()
        conn.close()
        if not rows:
            self.content_browser.setHtml('<p style="color:#666;">暂无影像解剖图谱资料</p>')
            return
        html = f'{self._html_heading("影像解剖图谱与资料")}'
        for title, content in rows:
            html += f'{self._html_heading(title, 3)}{self._html_body(content)}'
        self.content_browser.setHtml(html)


# ── 主窗口 ────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self, user_info, active_db):
        super().__init__()
        self.user_info = user_info
        self.active_db = active_db
        self.current_theme = '深蓝暗夜'
        self.setWindowTitle('RadAtlas 影像图鉴助手')
        self.setMinimumSize(1000, 650)
        self.resize(1200, 750)

        # 菜单栏
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu('文件')
        add_disease_action = QAction('添加疾病', self)
        add_disease_action.triggered.connect(self.show_add_disease)
        file_menu.addAction(add_disease_action)

        edit_disease_action = QAction('编辑当前疾病', self)
        edit_disease_action.triggered.connect(self.show_edit_disease)
        file_menu.addAction(edit_disease_action)

        del_disease_action = QAction('删除当前疾病', self)
        del_disease_action.triggered.connect(self.show_delete_disease)
        file_menu.addAction(del_disease_action)

        file_menu.addSeparator()

        add_img_action = QAction('添加图片到当前疾病', self)
        add_img_action.triggered.connect(self.show_add_image)
        file_menu.addAction(add_img_action)

        file_menu.addSeparator()

        user_action = QAction('用户管理', self)
        user_action.triggered.connect(self.show_user_manage)
        file_menu.addAction(user_action)

        # 主题菜单
        theme_menu = menubar.addMenu('主题')
        for theme_name in THEMES:
            action = QAction(theme_name, self)
            action.triggered.connect(lambda checked, name=theme_name: self.switch_theme(name))
            theme_menu.addAction(action)

        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 顶部搜索栏
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(12, 8, 12, 8)
        top_bar.setSpacing(8)

        logo = QLabel('RadAtlas')
        logo.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        logo.setStyleSheet("color: #3f7bf7; background: transparent;")
        logo.setFixedWidth(100)
        top_bar.addWidget(logo)

        # 搜索框 + 自动补全
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('搜索疾病...')
        self.search_input.setFixedHeight(36)
        self.search_input.returnPressed.connect(self.do_search)
        self.search_input.textChanged.connect(self.on_search_text_changed)

        self.completer_model = QStringListModel()
        self.completer = QCompleter()
        self.completer.setModel(self.completer_model)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.activated.connect(self.on_completer_activated)
        self.search_input.setCompleter(self.completer)

        top_bar.addWidget(self.search_input, stretch=1)

        search_btn = QPushButton('搜索')
        search_btn.setFixedSize(70, 36)
        search_btn.clicked.connect(self.do_search)
        top_bar.addWidget(search_btn)

        clear_btn = QPushButton('清除')
        clear_btn.setObjectName('mutedBtn')
        clear_btn.setFixedSize(70, 36)
        clear_btn.clicked.connect(self.clear_search)
        top_bar.addWidget(clear_btn)

        top_bar.addStretch()

        user_label = QLabel(f'{user_info.get("username", "admin")}')
        user_label.setStyleSheet("color: #888890; font-size: 12px; background: transparent;")
        top_bar.addWidget(user_label)

        logout_btn = QPushButton('退出')
        logout_btn.setObjectName('dangerBtn')
        logout_btn.setFixedSize(60, 36)
        logout_btn.clicked.connect(self.do_logout)
        top_bar.addWidget(logout_btn)

        root_layout.addLayout(top_bar)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #2a2a30; max-height: 1px;")
        root_layout.addWidget(line)

        # 主内容区
        splitter = QSplitter(Qt.Horizontal)

        # 左侧疾病列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(8, 8, 4, 8)
        left_layout.setSpacing(6)

        list_header = QLabel('疾病列表')
        list_header.setStyleSheet("color: #777780; font-size: 12px; font-weight: bold; background: transparent;")
        left_layout.addWidget(list_header)

        self.disease_list = QListWidget()
        self.disease_list.currentItemChanged.connect(self.on_disease_selected)
        self.disease_list.itemDoubleClicked.connect(self.on_disease_double_clicked)
        left_layout.addWidget(self.disease_list)

        splitter.addWidget(left_panel)

        # 右侧详情面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(4, 8, 8, 8)

        self.detail = DetailPanel()
        right_layout.addWidget(self.detail)

        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 35)
        splitter.setStretchFactor(1, 65)
        splitter.setSizes([350, 650])

        root_layout.addWidget(splitter, stretch=1)

        # 状态栏
        self.statusBar().showMessage('就绪')

        # 加载疾病列表
        self.load_disease_list()
        self._update_completer()

    # ── 主题切换 ──
    def switch_theme(self, theme_name):
        if theme_name not in THEMES:
            return
        self.current_theme = theme_name
        t = THEMES[theme_name]
        QApplication.instance().setStyleSheet(build_stylesheet(t))
        # 更新调色板
        palette = QPalette()
        is_light = theme_name == '浅色经典'
        if is_light:
            palette.setColor(QPalette.Window, QColor(245, 245, 248))
            palette.setColor(QPalette.WindowText, QColor(34, 34, 48))
            palette.setColor(QPalette.Base, QColor(255, 255, 255))
            palette.setColor(QPalette.Text, QColor(34, 34, 48))
        else:
            palette.setColor(QPalette.Window, QColor(t['bg'].lstrip('#')))
            palette.setColor(QPalette.WindowText, QColor(t['fg'].lstrip('#')))
            palette.setColor(QPalette.Base, QColor(t['bg2'].lstrip('#')))
            palette.setColor(QPalette.Text, QColor(t['fg'].lstrip('#')))
        QApplication.instance().setPalette(palette)
        self.statusBar().showMessage(f'已切换主题: {theme_name}')

    # ── 搜索自动补全 ──
    def _update_completer(self):
        conn = sqlite3.connect(self.active_db)
        c = conn.cursor()
        c.execute("SELECT name_cn, name_en FROM diseases")
        rows = c.fetchall()
        conn.close()
        names = []
        for cn, en in rows:
            if cn:
                names.append(cn)
            if en:
                names.append(en)
        self.completer_model.setStringList(names)

    def on_search_text_changed(self, text):
        pass  # completer 自动处理

    def on_completer_activated(self, text):
        self.search_input.setText(text)
        self.do_search()

    # ── 疾病列表 ──
    def load_disease_list(self, search=None):
        self.disease_list.clear()
        conn = sqlite3.connect(self.active_db)
        c = conn.cursor()
        if search:
            c.execute("""SELECT id, name_cn, name_en, system FROM diseases
                         WHERE name_cn LIKE ? OR name_en LIKE ? OR clinical LIKE ?
                         OR diagnosis LIKE ? OR system LIKE ? OR category LIKE ?
                         ORDER BY system, name_cn""",
                      (f'%{search}%',) * 6)
        else:
            c.execute("SELECT id, name_cn, name_en, system FROM diseases ORDER BY system, name_cn")
        rows = c.fetchall()
        conn.close()

        if not rows:
            item = QListWidgetItem('暂无数据')
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEnabled)
            self.disease_list.addItem(item)
            return

        current_system = None
        for did, name_cn, name_en, system in rows:
            if system != current_system:
                current_system = system
                header = QListWidgetItem(f'── {system} ──')
                header.setFlags(header.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEnabled)
                header.setData(Qt.UserRole, None)
                self.disease_list.addItem(header)

            display = name_cn or name_en or f'疾病 #{did}'
            if name_en and name_cn:
                display = f'{name_cn} ({name_en})'
            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, did)
            self.disease_list.addItem(item)

    def on_disease_selected(self, current, previous):
        if current is None:
            return
        disease_id = current.data(Qt.UserRole)
        if disease_id is None:
            return
        self.detail.load_disease(disease_id, self.active_db)
        self.statusBar().showMessage(f'已选择疾病 ID: {disease_id}')

    def on_disease_double_clicked(self, item):
        self.show_edit_disease()

    # ── 添加疾病 ──
    def show_add_disease(self):
        dlg = DiseaseDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            if not data.get('name_cn'):
                QMessageBox.warning(self, '提示', '中文名为必填项')
                return
            try:
                add_disease(self.active_db, data)
                self.load_disease_list()
                self._update_completer()
                self.statusBar().showMessage(f'已添加疾病: {data["name_cn"]}')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'添加失败:\n{e}')

    # ── 编辑疾病 ──
    def show_edit_disease(self):
        item = self.disease_list.currentItem()
        if not item:
            QMessageBox.warning(self, '提示', '请先选择一个疾病')
            return
        disease_id = item.data(Qt.UserRole)
        if disease_id is None:
            return
        data = get_disease(self.active_db, disease_id)
        if not data:
            return
        dlg = DiseaseDialog(self, disease_data=data)
        if dlg.exec_() == QDialog.Accepted:
            new_data = dlg.get_data()
            try:
                update_disease(self.active_db, disease_id, new_data)
                self.load_disease_list()
                self._update_completer()
                self.detail.load_disease(disease_id, self.active_db)
                self.statusBar().showMessage(f'已更新疾病: {new_data.get("name_cn", "")}')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'更新失败:\n{e}')

    # ── 删除疾病 ──
    def show_delete_disease(self):
        item = self.disease_list.currentItem()
        if not item:
            QMessageBox.warning(self, '提示', '请先选择一个疾病')
            return
        disease_id = item.data(Qt.UserRole)
        if disease_id is None:
            return
        if QMessageBox.question(self, '确认', '确定删除该疾病及其所有关联数据？') == QMessageBox.Yes:
            try:
                delete_disease(self.active_db, disease_id)
                self.load_disease_list()
                self._update_completer()
                self.statusBar().showMessage('疾病已删除')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'删除失败:\n{e}')

    # ── 添加图片 ──
    def show_add_image(self):
        item = self.disease_list.currentItem()
        if not item:
            QMessageBox.warning(self, '提示', '请先选择一个疾病')
            return
        disease_id = item.data(Qt.UserRole)
        if disease_id is None:
            return

        file_paths, _ = QFileDialog.getOpenFileNames(self, '选择图片', '', 'Images (*.png *.jpg *.jpeg *.bmp *.gif)')
        if not file_paths:
            return

        # 确保images目录存在
        img_dir = os.path.join(APP_DIR, 'images')
        os.makedirs(img_dir, exist_ok=True)

        for fp in file_paths:
            filename = os.path.basename(fp)
            dest = os.path.join(img_dir, filename)
            # 避免重名
            if os.path.exists(dest) and dest != fp:
                base, ext = os.path.splitext(filename)
                i = 1
                while os.path.exists(os.path.join(img_dir, f'{base}_{i}{ext}')):
                    i += 1
                filename = f'{base}_{i}{ext}'
                dest = os.path.join(img_dir, filename)
            if fp != dest:
                shutil.copy2(fp, dest)
            try:
                add_image(self.active_db, disease_id, filename, '', '', '', 'image')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'添加图片失败:\n{e}')
                return

        self.detail.load_disease(disease_id, self.active_db)
        self.statusBar().showMessage(f'已添加 {len(file_paths)} 张图片')

    # ── 用户管理 ──
    def show_user_manage(self):
        if self.user_info.get('role') != 'admin':
            QMessageBox.warning(self, '提示', '仅管理员可管理用户')
            return
        dlg = UserManageDialog(self)
        dlg.exec_()

    # ── 搜索 ──
    def do_search(self):
        keyword = self.search_input.text().strip()
        self.load_disease_list(search=keyword if keyword else None)
        self.statusBar().showMessage(f'搜索: {keyword}' if keyword else '就绪')

    def clear_search(self):
        self.search_input.clear()
        self.load_disease_list()
        self.statusBar().showMessage('就绪')

    def do_logout(self):
        self.close()
        QApplication.instance().quit()


# ── 应用入口 ──────────────────────────────────────────────
class RadAtlasApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyleSheet(DARK_STYLE)
        self.app.setStyle('Fusion')

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(20, 20, 22))
        palette.setColor(QPalette.WindowText, QColor(217, 217, 220))
        palette.setColor(QPalette.Base, QColor(26, 26, 30))
        palette.setColor(QPalette.AlternateBase, QColor(30, 30, 34))
        palette.setColor(QPalette.ToolTipBase, QColor(26, 26, 30))
        palette.setColor(QPalette.ToolTipText, QColor(217, 217, 220))
        palette.setColor(QPalette.Text, QColor(217, 217, 220))
        palette.setColor(QPalette.Button, QColor(42, 42, 48))
        palette.setColor(QPalette.ButtonText, QColor(217, 217, 220))
        palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
        palette.setColor(QPalette.Highlight, QColor(63, 123, 247))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        self.app.setPalette(palette)

    def run(self):
        try:
            init_user_db()
        except Exception as e:
            QMessageBox.critical(None, '错误', f'初始化用户数据库失败:\n{e}')
            return

        login = LoginDialog()
        if login.exec_() != QDialog.Accepted:
            return

        user_info = login.user_info
        active_db = user_info.get('database') or DATABASE
        try:
            init_db(active_db)
        except Exception as e:
            QMessageBox.critical(None, '错误', f'初始化数据库失败:\n{e}')
            return

        try:
            if active_db == DATABASE:
                load_data(active_db)
        except Exception as e:
            QMessageBox.critical(None, '错误', f'加载数据失败:\n{e}')
            return

        try:
            window = MainWindow(user_info, active_db)
            window.show()
        except Exception as e:
            QMessageBox.critical(None, '错误', f'创建主窗口失败:\n{e}')
            return

        sys.exit(self.app.exec_())


if __name__ == '__main__':
    RadAtlasApp().run()
