import os
import sys
import json
import math
import sqlite3
import shutil
import requests

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextBrowser, QSplitter,
    QListWidget, QListWidgetItem, QTabWidget, QDialog,
    QMessageBox, QStatusBar, QFrame, QGroupBox, QSizePolicy,
    QScrollArea, QComboBox, QFileDialog, QMenu, QMenuBar,
    QAction, QCompleter, QToolBar, QSpinBox, QCheckBox,
    QInputDialog, QSlider, QGridLayout
)
from PyQt5.QtCore import Qt, QSize, QStringListModel, pyqtSignal, QRect, QPoint, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QTextCursor, QPixmap, QPainter, QPen, QPolygon, QBrush

from models import (
    init_user_db, authenticate_user, init_db, load_data,
    get_all_users, create_user, delete_user, change_password,
    rename_user, admin_change_password,
    hash_password, DATABASE, USER_DB, APP_DIR, copy_public_to_user,
    add_disease, update_disease, delete_disease,
    add_image, delete_image, get_disease, search_diseases
)
from ai_helper import load_config, save_config, call_ai, PROVIDERS

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


# ── AI配置对话框 ──────────────────────────────────────────
class AIConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('AI 大模型配置')
        self.setFixedSize(480, 360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        config = load_config()

        # 提供商选择
        provider_row = QHBoxLayout()
        provider_row.addWidget(QLabel('AI提供商:'))
        self.provider_combo = QComboBox()
        for pid, pinfo in PROVIDERS.items():
            self.provider_combo.addItem(pinfo['name'], pid)
        # 设置当前选中
        idx = list(PROVIDERS.keys()).index(config.get('provider', 'deepseek'))
        self.provider_combo.setCurrentIndex(idx)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        provider_row.addWidget(self.provider_combo)
        provider_row.addStretch()
        layout.addLayout(provider_row)

        # 模型选择
        model_row = QHBoxLayout()
        model_row.addWidget(QLabel('模型:'))
        self.model_combo = QComboBox()
        self._update_models()
        # 设置当前模型
        cur_model = config.get('model', '')
        for i in range(self.model_combo.count()):
            if self.model_combo.itemText(i) == cur_model:
                self.model_combo.setCurrentIndex(i)
                break
        model_row.addWidget(self.model_combo)
        model_row.addStretch()
        layout.addLayout(model_row)

        # API Key
        layout.addWidget(QLabel('API Key:'))
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setText(config.get('api_key', ''))
        self.api_key_input.setPlaceholderText('输入你的API Key')
        layout.addWidget(self.api_key_input)

        # 自定义API地址
        layout.addWidget(QLabel('自定义API地址（可选，留空使用默认）:'))
        self.custom_url_input = QLineEdit()
        self.custom_url_input.setText(config.get('custom_api_url', ''))
        self.custom_url_input.setPlaceholderText('https://...')
        layout.addWidget(self.custom_url_input)

        layout.addSpacing(10)

        # 按钮
        btn_row = QHBoxLayout()
        save_btn = QPushButton('保存')
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton('取消')
        cancel_btn.setObjectName('mutedBtn')
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _on_provider_changed(self, idx):
        self._update_models()

    def _update_models(self):
        self.model_combo.clear()
        pid = self.provider_combo.currentData()
        if pid and pid in PROVIDERS:
            for model in PROVIDERS[pid]['models']:
                self.model_combo.addItem(model)

    def _save(self):
        config = {
            'provider': self.provider_combo.currentData() or 'deepseek',
            'model': self.model_combo.currentText() or 'deepseek-chat',
            'api_key': self.api_key_input.text().strip(),
            'custom_api_url': self.custom_url_input.text().strip(),
        }
        save_config(config)
        QMessageBox.information(self, '成功', 'AI配置已保存')
        self.accept()


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

        # AI 填充按钮行
        ai_row = QHBoxLayout()
        self.ai_fill_btn = QPushButton('AI 一键填充')
        self.ai_fill_btn.clicked.connect(self._ai_fill)
        ai_row.addWidget(self.ai_fill_btn)

        self.ai_status = QLabel('')
        self.ai_status.setStyleSheet("color: #888890; font-size: 11px; background: transparent;")
        ai_row.addWidget(self.ai_status)
        ai_row.addStretch()
        layout.addLayout(ai_row)

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

    def _ai_fill(self):
        name_cn = self.inputs['name_cn'].text().strip()
        if not name_cn:
            QMessageBox.warning(self, '提示', '请先输入疾病中文名')
            return
        config = load_config()
        if not config.get('api_key'):
            ret = QMessageBox.question(self, '未配置AI',
                '尚未配置AI大模型API，是否现在配置？')
            if ret == QMessageBox.Yes:
                dlg = AIConfigDialog(self)
                if dlg.exec_() != QDialog.Accepted:
                    return
                config = load_config()
            else:
                return

        self.ai_fill_btn.setEnabled(False)
        self.ai_status.setText('正在查询AI，请稍候...')
        QApplication.processEvents()

        try:
            result = call_ai(name_cn, config)
            # 填充字段
            filled = 0
            for key, _ in self.FIELDS:
                val = result.get(key, '').strip() if isinstance(result.get(key), str) else ''
                if val and not self.inputs[key].text().strip():
                    self.inputs[key].setText(val)
                    filled += 1
                elif val:
                    # 如果已有内容，也覆盖（AI结果更完整）
                    self.inputs[key].setText(val)
                    filled += 1
            self.ai_status.setText(f'AI填充完成，已填入 {filled} 个字段')
        except ValueError as e:
            QMessageBox.warning(self, '配置错误', str(e))
            self.ai_status.setText('填充失败：未配置API Key')
        except requests.exceptions.Timeout:
            QMessageBox.warning(self, '超时', 'AI请求超时，请检查网络连接')
            self.ai_status.setText('填充失败：请求超时')
        except requests.exceptions.ConnectionError:
            QMessageBox.warning(self, '连接错误', '无法连接AI服务，请检查网络和API地址')
            self.ai_status.setText('填充失败：连接错误')
        except json.JSONDecodeError:
            QMessageBox.warning(self, '解析错误', 'AI返回的数据格式异常，请重试')
            self.ai_status.setText('填充失败：数据格式异常')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'AI填充失败:\n{e}')
            self.ai_status.setText('填充失败')
        finally:
            self.ai_fill_btn.setEnabled(True)

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


# ── 图像浏览窗口 ──────────────────────────────────────────
class ImageViewerDialog(QDialog):
    """图像浏览窗口：缩放/平移/翻页，双击进入编辑模式"""

    def __init__(self, image_paths, current_index=0, parent=None):
        super().__init__(parent)
        self.setWindowTitle('图像浏览')
        self.setMinimumSize(900, 650)
        self.image_paths = image_paths  # list of (img_id, img_path)
        self.current_index = current_index
        self.scale = 1.0
        self.current_theme = self._detect_theme()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部工具栏
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(8, 6, 8, 6)
        top_bar.setSpacing(6)

        btn_prev = QPushButton('< 上一张')
        btn_prev.setFixedHeight(32)
        btn_prev.setFont(QFont("SimSun", 10))
        btn_prev.clicked.connect(self._prev_image)
        top_bar.addWidget(btn_prev)

        self.page_label = QLabel()
        self.page_label.setFont(QFont("SimSun", 9))
        self.page_label.setStyleSheet("background: transparent; font-size: 9px;")
        top_bar.addWidget(self.page_label)

        btn_next = QPushButton('下一张 >')
        btn_next.setFixedHeight(32)
        btn_next.setFont(QFont("SimSun", 10))
        btn_next.clicked.connect(self._next_image)
        top_bar.addWidget(btn_next)

        top_bar.addSpacing(20)

        btn_zoom_out = QPushButton('-')
        btn_zoom_out.setFixedSize(32, 32)
        btn_zoom_out.setFont(QFont("SimSun", 10))
        btn_zoom_out.clicked.connect(self._zoom_out)
        top_bar.addWidget(btn_zoom_out)

        self.zoom_label = QLabel('100%')
        self.zoom_label.setFixedWidth(50)
        self.zoom_label.setFont(QFont("SimSun", 9))
        self.zoom_label.setStyleSheet("background: transparent; font-size: 9px;")
        top_bar.addWidget(self.zoom_label)

        btn_zoom_in = QPushButton('+')
        btn_zoom_in.setFixedSize(32, 32)
        btn_zoom_in.setFont(QFont("SimSun", 10))
        btn_zoom_in.clicked.connect(self._zoom_in)
        top_bar.addWidget(btn_zoom_in)

        btn_fit = QPushButton('适应')
        btn_fit.setObjectName('mutedBtn')
        btn_fit.setFixedSize(50, 32)
        btn_fit.setFont(QFont("SimSun", 10))
        btn_fit.clicked.connect(self._zoom_fit)
        top_bar.addWidget(btn_fit)

        btn_orig = QPushButton('1:1')
        btn_orig.setObjectName('mutedBtn')
        btn_orig.setFixedSize(40, 32)
        btn_orig.setFont(QFont("SimSun", 10))
        btn_orig.clicked.connect(self._zoom_original)
        top_bar.addWidget(btn_orig)

        top_bar.addStretch()

        btn_edit = QPushButton('编辑图片')
        btn_edit.setFixedHeight(32)
        btn_edit.setFont(QFont("SimSun", 10))
        btn_edit.clicked.connect(self._enter_edit)
        top_bar.addWidget(btn_edit)

        btn_close = QPushButton('关闭')
        btn_close.setObjectName('mutedBtn')
        btn_close.setFixedSize(60, 32)
        btn_close.setFont(QFont("SimSun", 10))
        btn_close.clicked.connect(self.reject)
        top_bar.addWidget(btn_close)

        layout.addLayout(top_bar)

        # 画布
        self.viewer_canvas = _ViewerCanvas(self)
        layout.addWidget(self.viewer_canvas, stretch=1)

        # 底部提示
        hint = QLabel('  双击图片进入编辑模式  |  滚轮缩放  |  拖拽平移')
        hint.setFixedHeight(24)
        hint.setFont(QFont("SimSun", 9))
        hint.setObjectName('editorInfoBar')
        layout.addWidget(hint)

        self._apply_theme()
        self._load_current()

    def _detect_theme(self):
        app = QApplication.instance()
        if app:
            ss = app.styleSheet()
            for name, t in THEMES.items():
                if t['bg'] in ss:
                    return name
        return '深蓝暗夜'

    def _apply_theme(self):
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
        QWidget#editorInfoBar {{
            background-color: {bg2}; color: {fg2};
            border-top: 1px solid {border}; font-size: 9px;
            font-family: "SimSun";
        }}
        QPushButton {{
            background-color: {muted}; color: {fg};
            border: 1px solid {border}; border-radius: 4px; font-size: 10px;
            font-family: "SimSun";
        }}
        QPushButton:hover {{ background-color: {border}; }}
        QPushButton#mutedBtn {{ background-color: {muted}; }}
        QPushButton#mutedBtn:hover {{ background-color: {border}; }}
        QLabel {{ background-color: transparent; color: {fg}; font-family: "SimSun"; }}
        """)
        self.viewer_canvas.bg_color = QColor(245, 245, 248) if is_light else QColor(20, 20, 22)
        self.viewer_canvas.update()

    def _load_current(self):
        if 0 <= self.current_index < len(self.image_paths):
            _, img_path = self.image_paths[self.current_index]
            self.viewer_canvas.load_image(img_path)
            self.page_label.setText(f' {self.current_index + 1} / {len(self.image_paths)} ')
            self.zoom_label.setText('100%')
            self.scale = 1.0
            self.viewer_canvas.scale = 1.0
            self.viewer_canvas.offset = QPoint(0, 0)
            self.viewer_canvas.update()

    def _prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self._load_current()

    def _next_image(self):
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self._load_current()

    def _zoom_in(self):
        self.scale = min(self.scale * 1.25, 5.0)
        self.viewer_canvas.scale = self.scale
        self.zoom_label.setText(f'{int(self.scale * 100)}%')
        self.viewer_canvas.update()

    def _zoom_out(self):
        self.scale = max(self.scale / 1.25, 0.1)
        self.viewer_canvas.scale = self.scale
        self.zoom_label.setText(f'{int(self.scale * 100)}%')
        self.viewer_canvas.update()

    def _zoom_fit(self):
        if self.viewer_canvas.pixmap:
            cw = self.viewer_canvas.width()
            ch = self.viewer_canvas.height()
            pw = self.viewer_canvas.pixmap.width()
            ph = self.viewer_canvas.pixmap.height()
            if pw > 0 and ph > 0:
                self.scale = min(cw / pw, ch / ph) * 0.9
                self.viewer_canvas.scale = self.scale
                self.viewer_canvas.offset = QPoint(0, 0)
                self.zoom_label.setText(f'{int(self.scale * 100)}%')
                self.viewer_canvas.update()

    def _zoom_original(self):
        self.scale = 1.0
        self.viewer_canvas.scale = 1.0
        self.viewer_canvas.offset = QPoint(0, 0)
        self.zoom_label.setText('100%')
        self.viewer_canvas.update()

    def _enter_edit(self):
        self._open_editor()

    def _open_editor(self):
        if 0 <= self.current_index < len(self.image_paths):
            _, img_path = self.image_paths[self.current_index]
            if os.path.exists(img_path):
                editor = ImageEditorDialog(img_path, self)
                editor.exec_()
                # 编辑后重新加载
                self.viewer_canvas.load_image(img_path)


class _ViewerCanvas(QWidget):
    """浏览画布：支持缩放/平移/双击"""
    def __init__(self, viewer, parent=None):
        super().__init__(parent)
        self.viewer = viewer
        self.pixmap = None
        self.image_path = None
        self.scale = 1.0
        self.offset = QPoint(0, 0)
        self.dragging = False
        self.last_pos = None
        self.bg_color = QColor(20, 20, 22)
        self.setMouseTracking(True)

    def load_image(self, path):
        self.image_path = path
        if path and os.path.exists(path):
            self.pixmap = QPixmap(path)
            # 自动适应
            QTimer.singleShot(50, self.viewer._zoom_fit)
        else:
            self.pixmap = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), self.bg_color)
        if not self.pixmap:
            painter.setPen(QColor(100, 100, 100))
            painter.setFont(QFont("Microsoft YaHei", 14))
            painter.drawText(self.rect(), Qt.AlignCenter, '无图片')
            painter.end()
            return
        scaled = self.pixmap.scaled(
            self.pixmap.size() * self.scale,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        x = (self.width() - scaled.width()) // 2 + self.offset.x()
        y = (self.height() - scaled.height()) // 2 + self.offset.y()
        painter.drawPixmap(x, y, scaled)
        painter.end()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.viewer._zoom_in()
        else:
            self.viewer._zoom_out()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.last_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self.dragging and self.last_pos:
            delta = event.pos() - self.last_pos
            self.offset += delta
            self.last_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.last_pos = None
            self.setCursor(Qt.ArrowCursor)

    def mouseDoubleClickEvent(self, event):
        self.viewer._open_editor()


# ── 图片编辑器 ────────────────────────────────────────────

# 预定义颜色
_ANNOTATION_COLORS = [
    QColor(255, 80, 80),   # 红
    QColor(255, 220, 50),  # 黄
    QColor(80, 220, 80),   # 绿
    QColor(80, 140, 255),  # 蓝
    QColor(255, 255, 255), # 白
    QColor(0, 0, 0),       # 黑
]


class _ToolButton(QWidget):
    """浮动工具栏中的图标按钮"""
    clicked = pyqtSignal()

    def __init__(self, tool_id, parent=None):
        super().__init__(parent)
        self.tool_id = tool_id
        self.setFixedSize(36, 36)
        self._hover = False
        self._selected = False
        self.setCursor(Qt.PointingHandCursor)

    def set_selected(self, sel):
        self._selected = sel
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        r = self.rect()
        # 背景
        if self._selected:
            painter.fillRect(r, QColor(63, 123, 247, 180))
        elif self._hover:
            painter.fillRect(r, QColor(255, 255, 255, 30))
        # 绘制图标
        painter.setPen(QPen(QColor(220, 220, 225), 2))
        cx, cy = r.center().x(), r.center().y()
        tid = self.tool_id
        if tid == 'select':
            # 光标箭头
            pts = [QPoint(cx - 6, cy - 8), QPoint(cx - 6, cy + 6),
                   QPoint(cx - 2, cy + 2), QPoint(cx + 2, cy + 8),
                   QPoint(cx + 4, cy + 6), QPoint(cx, cy + 0),
                   QPoint(cx + 6, cy + 0)]
            painter.drawPolyline(QPolygon(pts))
        elif tid == 'pan':
            # 四向箭头
            painter.drawLine(cx, cy - 8, cx, cy + 8)
            painter.drawLine(cx - 8, cy, cx + 8, cy)
            for dx, dy in [(0, -8), (0, 8), (-8, 0), (8, 0)]:
                ex, ey = cx + dx, cy + dy
                if dx != 0:
                    painter.drawLine(ex, ey, ex - (2 if dx > 0 else -2), ey - 3)
                    painter.drawLine(ex, ey, ex - (2 if dx > 0 else -2), ey + 3)
                else:
                    painter.drawLine(ex, ey, ex - 3, ey - (2 if dy > 0 else -2))
                    painter.drawLine(ex, ey, ex + 3, ey - (2 if dy > 0 else -2))
        elif tid == 'text':
            painter.setFont(QFont("SimSun", 16, QFont.Bold))
            painter.drawText(r, Qt.AlignCenter, 'T')
        elif tid == 'arrow':
            painter.drawLine(cx - 7, cy + 7, cx + 5, cy - 5)
            pts = [QPoint(cx + 5, cy - 5), QPoint(cx + 1, cy - 3), QPoint(cx + 3, cy - 1)]
            painter.setBrush(QColor(220, 220, 225))
            painter.drawPolygon(QPolygon(pts))
            painter.setBrush(Qt.NoBrush)
        elif tid == 'line':
            painter.drawLine(cx - 8, cy + 8, cx + 8, cy - 8)
        elif tid == 'rect':
            painter.drawRect(cx - 8, cy - 6, 16, 12)
        elif tid == 'circle':
            painter.drawEllipse(cx - 7, cy - 7, 14, 14)
        elif tid == 'measure':
            painter.drawLine(cx - 8, cy + 4, cx + 8, cy - 4)
            painter.setBrush(QColor(220, 220, 225))
            painter.drawEllipse(QPoint(cx - 8, cy + 4), 2, 2)
            painter.drawEllipse(QPoint(cx + 8, cy - 4), 2, 2)
            painter.setBrush(Qt.NoBrush)
        elif tid == 'eraser':
            painter.drawRect(cx - 6, cy - 2, 12, 10)
            pts = [QPoint(cx - 6, cy - 2), QPoint(cx - 2, cy - 8), QPoint(cx + 6, cy - 8), QPoint(cx + 6, cy - 2)]
            painter.drawPolygon(QPolygon(pts))
        painter.end()

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()


class _FloatingToolbar(QWidget):
    """浮动可拖拽工具栏"""
    tool_changed = pyqtSignal(str)
    color_changed = pyqtSignal(QColor)
    line_width_changed = pyqtSignal(int)
    action_triggered = pyqtSignal(str)  # undo/clear/save/back/zoom_in/zoom_out/zoom_fit/zoom_orig

    TOOLS = ['select', 'pan', 'text', 'arrow', 'line', 'rect', 'circle', 'measure', 'eraser']
    LINE_WIDTHS = [1, 3, 5]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_tool = 'pan'
        self.current_color_idx = 0
        self.current_width_idx = 1
        self._drag_pos = None
        self.zoom_pct = 100

        self.setFixedWidth(52)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self.setCursor(Qt.ArrowCursor)

        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)

        # 工具按钮
        self.tool_btns = {}
        for tid in self.TOOLS:
            btn = _ToolButton(tid, self)
            btn.clicked.connect(lambda t=tid: self._on_tool(t))
            self.tool_btns[tid] = btn
            layout.addWidget(btn, alignment=Qt.AlignCenter)

        layout.addSpacing(4)

        # 缩放
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setFixedHeight(1)
        sep1.setStyleSheet("background-color: rgba(255,255,255,30);")
        layout.addWidget(sep1)

        zoom_row = QHBoxLayout()
        zoom_row.setSpacing(2)
        btn_zo = QPushButton('-')
        btn_zo.setFixedSize(20, 20)
        btn_zo.setFont(QFont("SimSun", 10))
        btn_zo.clicked.connect(lambda: self.action_triggered.emit('zoom_out'))
        zoom_row.addWidget(btn_zo)
        self.zoom_label = QLabel('100%')
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_label.setFont(QFont("SimSun", 8))
        self.zoom_label.setStyleSheet("color: #ccc; background: transparent;")
        self.zoom_label.setFixedWidth(32)
        zoom_row.addWidget(self.zoom_label)
        btn_zi = QPushButton('+')
        btn_zi.setFixedSize(20, 20)
        btn_zi.setFont(QFont("SimSun", 10))
        btn_zi.clicked.connect(lambda: self.action_triggered.emit('zoom_in'))
        zoom_row.addWidget(btn_zi)
        layout.addLayout(zoom_row)

        layout.addSpacing(2)

        # 颜色选择
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFixedHeight(1)
        sep2.setStyleSheet("background-color: rgba(255,255,255,30);")
        layout.addWidget(sep2)

        color_grid = QGridLayout()
        color_grid.setSpacing(2)
        self.color_btns = []
        for i, c in enumerate(_ANNOTATION_COLORS):
            btn = QPushButton()
            btn.setFixedSize(14, 14)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(
                f"background-color: {c.name()}; border: 2px solid "
                f"{'#3f7bf7' if i == 0 else '#555'}; border-radius: 7px;"
            )
            btn.clicked.connect(lambda idx=i: self._on_color(idx))
            self.color_btns.append(btn)
            color_grid.addWidget(btn, i // 3, i % 3)
        layout.addLayout(color_grid)

        layout.addSpacing(2)

        # 线宽
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.HLine)
        sep3.setFixedHeight(1)
        sep3.setStyleSheet("background-color: rgba(255,255,255,30);")
        layout.addWidget(sep3)

        width_row = QHBoxLayout()
        width_row.setSpacing(2)
        self.width_btns = []
        for i, w in enumerate(self.LINE_WIDTHS):
            btn = QPushButton()
            btn.setFixedSize(14, 14)
            btn.setCursor(Qt.PointingHandCursor)
            border = '#3f7bf7' if i == self.current_width_idx else '#555'
            btn.setStyleSheet(
                f"background-color: #888; border: 2px solid {border}; border-radius: 3px;"
            )
            btn.clicked.connect(lambda idx=i: self._on_width(idx))
            self.width_btns.append(btn)
            width_row.addWidget(btn)
        layout.addLayout(width_row)

        layout.addSpacing(4)

        # 操作按钮
        sep4 = QFrame()
        sep4.setFrameShape(QFrame.HLine)
        sep4.setFixedHeight(1)
        sep4.setStyleSheet("background-color: rgba(255,255,255,30);")
        layout.addWidget(sep4)

        action_icons = [
            ('undo', '↩'), ('clear', '✕'), ('save', '✓'), ('back', '←'),
        ]
        self.action_btns = {}
        for aid, icon in action_icons:
            btn = QPushButton(icon)
            btn.setFixedSize(36, 24)
            btn.setFont(QFont("SimSun", 10))
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda a=aid: self.action_triggered.emit(a))
            self.action_btns[aid] = btn
            layout.addWidget(btn, alignment=Qt.AlignCenter)

        layout.addStretch()
        self.tool_btns['pan'].set_selected(True)

    def _on_tool(self, tid):
        self.current_tool = tid
        for k, btn in self.tool_btns.items():
            btn.set_selected(k == tid)
        self.tool_changed.emit(tid)

    def _on_color(self, idx):
        self.current_color_idx = idx
        for i, btn in enumerate(self.color_btns):
            border = '#3f7bf7' if i == idx else '#555'
            c = _ANNOTATION_COLORS[i]
            btn.setStyleSheet(
                f"background-color: {c.name()}; border: 2px solid {border}; border-radius: 7px;"
            )
        self.color_changed.emit(_ANNOTATION_COLORS[idx])

    def _on_width(self, idx):
        self.current_width_idx = idx
        for i, btn in enumerate(self.width_btns):
            border = '#3f7bf7' if i == idx else '#555'
            btn.setStyleSheet(
                f"background-color: #888; border: 2px solid {border}; border-radius: 3px;"
            )
        self.line_width_changed.emit(self.LINE_WIDTHS[idx])

    def set_zoom_pct(self, pct):
        self.zoom_pct = pct
        self.zoom_label.setText(f'{pct}%')

    def get_color(self):
        return _ANNOTATION_COLORS[self.current_color_idx]

    def get_line_width(self):
        return self.LINE_WIDTHS[self.current_width_idx]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(30, 30, 35, 210))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.pos()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            delta = event.pos() - self._drag_pos
            self.move(self.pos() + delta)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


class _PropertyPanel(QWidget):
    """选中注释时的属性面板"""
    color_changed = pyqtSignal(QColor)
    bg_color_changed = pyqtSignal(object)  # QColor or None
    opacity_changed = pyqtSignal(int)
    rotation_changed = pyqtSignal(float)
    delete_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(140)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        title = QLabel('属性')
        title.setFont(QFont("SimSun", 9, QFont.Bold))
        title.setStyleSheet("color: #ccc; background: transparent;")
        layout.addWidget(title)

        # 颜色
        cl = QLabel('颜色')
        cl.setFont(QFont("SimSun", 8))
        cl.setStyleSheet("color: #aaa; background: transparent;")
        layout.addWidget(cl)
        color_row = QHBoxLayout()
        color_row.setSpacing(2)
        self.color_btns = []
        for i, c in enumerate(_ANNOTATION_COLORS):
            btn = QPushButton()
            btn.setFixedSize(14, 14)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"background-color: {c.name()}; border: 1px solid #555; border-radius: 7px;")
            btn.clicked.connect(lambda idx=i: self.color_changed.emit(_ANNOTATION_COLORS[idx]))
            self.color_btns.append(btn)
            color_row.addWidget(btn)
        layout.addLayout(color_row)

        # 背景颜色
        bgl = QLabel('背景色')
        bgl.setFont(QFont("SimSun", 8))
        bgl.setStyleSheet("color: #aaa; background: transparent;")
        layout.addWidget(bgl)
        bg_row = QHBoxLayout()
        bg_row.setSpacing(2)
        self.bg_btns = []
        for i, c in enumerate(_ANNOTATION_COLORS):
            btn = QPushButton()
            btn.setFixedSize(14, 14)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"background-color: {c.name()}; border: 1px solid #555; border-radius: 7px;")
            btn.clicked.connect(lambda idx=i: self.bg_color_changed.emit(_ANNOTATION_COLORS[idx]))
            self.bg_btns.append(btn)
            bg_row.addWidget(btn)
        # 无背景色按钮
        btn_none = QPushButton('无')
        btn_none.setFixedSize(14, 14)
        btn_none.setFont(QFont("SimSun", 7))
        btn_none.setCursor(Qt.PointingHandCursor)
        btn_none.setStyleSheet("background-color: transparent; border: 1px solid #555; border-radius: 7px; color: #aaa;")
        btn_none.clicked.connect(lambda: self.bg_color_changed.emit(None))
        bg_row.addWidget(btn_none)
        layout.addLayout(bg_row)

        # 透明度
        ol = QLabel('透明度')
        ol.setFont(QFont("SimSun", 8))
        ol.setStyleSheet("color: #aaa; background: transparent;")
        layout.addWidget(ol)
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(55)
        self.opacity_slider.valueChanged.connect(lambda v: self.opacity_changed.emit(v))
        layout.addWidget(self.opacity_slider)

        # 旋转
        rl = QLabel('旋转')
        rl.setFont(QFont("SimSun", 8))
        rl.setStyleSheet("color: #aaa; background: transparent;")
        layout.addWidget(rl)
        self.rotation_input = QSpinBox()
        self.rotation_input.setRange(0, 360)
        self.rotation_input.setValue(0)
        self.rotation_input.setFont(QFont("SimSun", 9))
        self.rotation_input.setSuffix('°')
        self.rotation_input.valueChanged.connect(lambda v: self.rotation_changed.emit(float(v)))
        layout.addWidget(self.rotation_input)

        # 删除
        del_btn = QPushButton('删除')
        del_btn.setFont(QFont("SimSun", 9))
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.clicked.connect(self.delete_requested.emit)
        layout.addWidget(del_btn)

    def set_annotation(self, data):
        """根据注释数据更新面板"""
        self.rotation_input.blockSignals(True)
        self.opacity_slider.blockSignals(True)
        self.rotation_input.setValue(int(data.get('rotation', 0)))
        bg_opacity = data.get('bg_opacity', 140)
        self.opacity_slider.setValue(int(bg_opacity * 100 / 255))
        self.rotation_input.blockSignals(False)
        self.opacity_slider.blockSignals(False)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(30, 30, 35, 220))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)
        painter.end()


class ImageEditorDialog(QDialog):
    """图片编辑器：浮动工具栏 + 选择/变换系统"""

    TOOL_SHORTCUTS = {
        Qt.Key_V: 'pan', Qt.Key_T: 'text', Qt.Key_A: 'arrow',
        Qt.Key_L: 'line', Qt.Key_R: 'rect', Qt.Key_C: 'circle',
        Qt.Key_M: 'measure', Qt.Key_E: 'eraser', Qt.Key_S: 'select',
    }

    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle('图片编辑器')
        self.setMinimumSize(1050, 720)
        self.image_path = image_path
        self.scale = 1.0
        self.tool = 'pan'
        self.current_theme = self._detect_theme()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 信息栏
        info_bar = QLabel(f'  {os.path.basename(image_path)}  |  当前工具: 移动  |  Esc返回浏览')
        info_bar.setFixedHeight(26)
        info_bar.setObjectName('editorInfoBar')
        info_bar.setFont(QFont("SimSun", 9))
        self.info_bar = info_bar
        layout.addWidget(info_bar)

        # 画布容器（用于叠放浮动工具栏和属性面板）
        self.canvas_container = QWidget()
        container_layout = QVBoxLayout(self.canvas_container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        self.canvas = _EditorCanvas(self)
        self.canvas.image_path = image_path
        self.canvas.load_image()
        container_layout.addWidget(self.canvas)

        # 浮动工具栏
        self.toolbar = _FloatingToolbar(self.canvas_container)
        self.toolbar.move(10, 10)
        self.toolbar.show()
        self.toolbar.tool_changed.connect(self._set_tool)
        self.toolbar.color_changed.connect(self._on_color_changed)
        self.toolbar.line_width_changed.connect(self._on_width_changed)
        self.toolbar.action_triggered.connect(self._on_action)

        # 属性面板
        self.prop_panel = _PropertyPanel(self.canvas_container)
        self.prop_panel.move(70, 10)
        self.prop_panel.color_changed.connect(self._on_prop_color)
        self.prop_panel.bg_color_changed.connect(self._on_prop_bg_color)
        self.prop_panel.opacity_changed.connect(self._on_prop_opacity)
        self.prop_panel.rotation_changed.connect(self._on_prop_rotation)
        self.prop_panel.delete_requested.connect(self._on_prop_delete)

        layout.addWidget(self.canvas_container, stretch=1)

        self._apply_theme()

    def keyPressEvent(self, event):
        key = event.key()
        if key in self.TOOL_SHORTCUTS:
            self._set_tool(self.TOOL_SHORTCUTS[key])
        elif key == Qt.Key_Escape:
            self.accept()
        elif key == Qt.Key_Z and event.modifiers() & Qt.ControlModifier:
            self._undo()
        elif key == Qt.Key_Y and event.modifiers() & Qt.ControlModifier:
            self._save()
        elif key == Qt.Key_Plus or key == Qt.Key_Equal:
            self._zoom_in()
        elif key == Qt.Key_Minus:
            self._zoom_out()
        elif key == Qt.Key_0 and event.modifiers() & Qt.ControlModifier:
            self._zoom_fit()
        elif key == Qt.Key_Delete:
            self._delete_selected()
        else:
            super().keyPressEvent(event)

    def _detect_theme(self):
        app = QApplication.instance()
        if app:
            ss = app.styleSheet()
            for name, t in THEMES.items():
                if t['bg'] in ss:
                    return name
        return '深蓝暗夜'

    def _apply_theme(self):
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
        QWidget#editorInfoBar {{
            background-color: {bg2}; color: {fg2};
            border-bottom: 1px solid {border}; font-size: 9px;
            font-family: "SimSun";
        }}
        QPushButton {{
            background-color: {muted}; color: {fg};
            border: 1px solid {border}; border-radius: 4px; font-size: 10px;
            font-family: "SimSun";
        }}
        QPushButton:hover {{ background-color: {border}; }}
        QLabel {{ background-color: transparent; color: {fg}; }}
        QSpinBox {{
            background-color: {muted}; color: {fg};
            border: 1px solid {border}; border-radius: 4px;
            padding: 2px; font-size: 9px;
        }}
        QSlider::groove:horizontal {{
            background: {muted}; height: 6px; border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {accent}; width: 12px; margin: -3px 0;
            border-radius: 6px;
        }}
        """)
        self.canvas.bg_color = QColor(245, 245, 248) if is_light else QColor(20, 20, 22)
        self.canvas.update()

    def _get_color(self):
        return self.toolbar.get_color()

    def _get_line_width(self):
        return self.toolbar.get_line_width()

    def _set_tool(self, tool):
        self.tool = tool
        self.canvas.tool = tool
        tool_names = {
            'select': '选择', 'pan': '移动', 'text': '文字',
            'arrow': '箭头', 'line': '直线', 'rect': '矩形',
            'circle': '圆形', 'measure': '测量', 'eraser': '橡皮擦',
        }
        self.info_bar.setText(
            f'  {os.path.basename(self.image_path)}  |  '
            f'当前工具: {tool_names.get(tool, tool)}  |  Esc返回浏览')

    def _on_color_changed(self, color):
        pass  # 颜色已存储在 toolbar 中

    def _on_width_changed(self, width):
        pass

    def _on_action(self, action):
        if action == 'undo':
            self._undo()
        elif action == 'clear':
            self._clear()
        elif action == 'save':
            self._save()
        elif action == 'back':
            self.accept()
        elif action == 'zoom_in':
            self._zoom_in()
        elif action == 'zoom_out':
            self._zoom_out()
        elif action == 'zoom_fit':
            self._zoom_fit()
        elif action == 'zoom_orig':
            self._zoom_original()

    def _zoom_in(self):
        self.scale = min(self.scale * 1.25, 5.0)
        self.canvas.scale = self.scale
        self.toolbar.set_zoom_pct(int(self.scale * 100))
        self.canvas.update()

    def _zoom_out(self):
        self.scale = max(self.scale / 1.25, 0.1)
        self.canvas.scale = self.scale
        self.toolbar.set_zoom_pct(int(self.scale * 100))
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
                self.toolbar.set_zoom_pct(int(self.scale * 100))
                self.canvas.update()

    def _zoom_original(self):
        self.scale = 1.0
        self.canvas.scale = 1.0
        self.canvas.offset = QPoint(0, 0)
        self.toolbar.set_zoom_pct(100)
        self.canvas.update()

    def _undo(self):
        if self.canvas.annotations:
            self.canvas.annotations.pop()
            self.canvas.selected_index = -1
            self.prop_panel.hide()
            self.canvas.update()

    def _clear(self):
        if self.canvas.annotations:
            if QMessageBox.question(self, '确认', '清空所有注释？') == QMessageBox.Yes:
                self.canvas.annotations.clear()
                self.canvas.selected_index = -1
                self.prop_panel.hide()
                self.canvas.update()

    def _save(self):
        self.canvas.save_annotated(self.image_path)
        self.accept()

    def _delete_selected(self):
        if 0 <= self.canvas.selected_index < len(self.canvas.annotations):
            self.canvas.annotations.pop(self.canvas.selected_index)
            self.canvas.selected_index = -1
            self.prop_panel.hide()
            self.canvas.update()

    # 属性面板回调
    def _on_prop_color(self, color):
        idx = self.canvas.selected_index
        if 0 <= idx < len(self.canvas.annotations):
            self.canvas.annotations[idx][1]['color'] = color
            self.canvas.update()

    def _on_prop_bg_color(self, color):
        idx = self.canvas.selected_index
        if 0 <= idx < len(self.canvas.annotations):
            self.canvas.annotations[idx][1]['bg_color'] = color
            self.canvas.update()

    def _on_prop_opacity(self, val):
        idx = self.canvas.selected_index
        if 0 <= idx < len(self.canvas.annotations):
            self.canvas.annotations[idx][1]['bg_opacity'] = int(val * 255 / 100)
            self.canvas.update()

    def _on_prop_rotation(self, deg):
        idx = self.canvas.selected_index
        if 0 <= idx < len(self.canvas.annotations):
            self.canvas.annotations[idx][1]['rotation'] = deg
            self._update_anchor(idx)
            self.canvas.update()

    def _on_prop_delete(self):
        self._delete_selected()

    def _update_anchor(self, idx):
        """更新注释的旋转/缩放锚点为中心"""
        atype, data = self.canvas.annotations[idx]
        cx, cy = self.canvas._get_annotation_center(data)
        data['anchor_x'] = cx
        data['anchor_y'] = cy

    def show_property_panel(self, data):
        self.prop_panel.set_annotation(data)
        self.prop_panel.show()
        self.prop_panel.raise_()

    def hide_property_panel(self):
        self.prop_panel.hide()


class _EditorCanvas(QWidget):
    """编辑画布：支持选择、旋转、缩放等多种标注变换"""
    HANDLE_SIZE = 8
    ROTATE_HANDLE_DIST = 20

    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.image_path = None
        self.pixmap = None
        self.scale = 1.0
        self.tool = 'pan'
        self.annotations = []
        self.selected_index = -1
        self.drawing = False
        self.draw_start = None
        self.draw_current = None
        self.offset = QPoint(0, 0)
        self.dragging = False
        self.last_pos = None
        self.bg_color = QColor(20, 20, 22)
        self._drag_handle = -1  # -1=none, 0-7=resize, 8=rotate
        self._drag_start_pos = None
        self._drag_start_data = None
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

    def load_image(self):
        if self.image_path and os.path.exists(self.image_path):
            self.pixmap = QPixmap(self.image_path)
            self.update()

    def _img_offset(self):
        """返回图片在画布上的偏移量 (x, y)"""
        if not self.pixmap:
            return 0, 0
        scaled = self.pixmap.scaled(
            self.pixmap.size() * self.scale,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        x = (self.width() - scaled.width()) // 2 + self.offset.x()
        y = (self.height() - scaled.height()) // 2 + self.offset.y()
        return x, y

    def _img_coords(self, pos):
        """将画布坐标转换为图片坐标"""
        x, y = self._img_offset()
        return pos.x() - x, pos.y() - y

    def _to_screen(self, img_x, img_y):
        """将图片坐标转换为画布坐标"""
        x, y = self._img_offset()
        return img_x + x, img_y + y

    @staticmethod
    def _get_annotation_center(data):
        """获取注释的中心点（图片坐标）"""
        if 'x' in data and 'w' in data:
            return data['x'] + data['w'] / 2, data['y'] + data['h'] / 2
        elif 'x1' in data:
            return (data['x1'] + data['x2']) / 2, (data['y1'] + data['y2']) / 2
        elif 'x' in data and 'y' in data:
            return data['x'], data['y']
        return 0, 0

    @staticmethod
    def _get_annotation_bbox(data):
        """获取注释的边界框 (x, y, w, h) 图片坐标"""
        if 'x' in data and 'w' in data:
            return data['x'], data['y'], data['w'], data['h']
        elif 'x1' in data:
            x = min(data['x1'], data['x2'])
            y = min(data['y1'], data['y2'])
            w = abs(data['x2'] - data['x1'])
            h = abs(data['y2'] - data['y1'])
            return x, y, w, h
        elif 'x' in data and 'y' in data:
            return data['x'] - 20, data['y'] - 20, 40, 40
        return 0, 0, 0, 0

    def _reverse_rotate_point(self, px, py, data):
        """将画布坐标点逆旋转到注释的局部坐标系"""
        rotation = data.get('rotation', 0)
        if rotation == 0:
            return px, py
        cx, cy = data.get('anchor_x', 0), data.get('anchor_y', 0)
        sx, sy = self._to_screen(cx, cy)
        dx = px - sx
        dy = py - sy
        angle = -rotation * math.pi / 180
        rx = dx * math.cos(angle) - dy * math.sin(angle) + sx
        ry = dx * math.sin(angle) + dy * math.cos(angle) + sy
        return rx, ry

    def _get_handles(self, data):
        """获取选中注释的8个缩放手柄和1个旋转手柄位置（画布坐标）"""
        bx, by, bw, bh = self._get_annotation_bbox(data)
        sx, sy = self._to_screen(bx, by)
        sw, sh = bw * self.scale, bh * self.scale
        hs = self.HANDLE_SIZE
        # 8个缩放手柄: TL, T, TR, R, BR, B, BL, L
        positions = [
            (sx, sy), (sx + sw / 2, sy), (sx + sw, sy),
            (sx + sw, sy + sh / 2), (sx + sw, sy + sh),
            (sx + sw / 2, sy + sh), (sx, sy + sh), (sx, sy + sh / 2),
        ]
        # 旋转手柄
        rot_pos = (sx + sw / 2, sy - self.ROTATE_HANDLE_DIST)
        return positions, rot_pos

    def _hit_handle(self, pos, data):
        """检测点击了哪个手柄，返回 -1=无, 0-7=缩放, 8=旋转"""
        positions, rot_pos = self._get_handles(data)
        hs = self.HANDLE_SIZE
        for i, (hx, hy) in enumerate(positions):
            if abs(pos.x() - hx) <= hs and abs(pos.y() - hy) <= hs:
                return i
        rx, ry = rot_pos
        if abs(pos.x() - rx) <= hs and abs(pos.y() - ry) <= hs:
            return 8
        return -1

    def _find_annotation_at(self, img_x, img_y, threshold=15):
        """查找点击位置对应的注释索引（考虑旋转）"""
        for i in range(len(self.annotations) - 1, -1, -1):
            atype, data = self.annotations[i]
            rotation = data.get('rotation', 0)
            # 逆旋转点击点
            if rotation != 0:
                cx, cy = data.get('anchor_x', 0), data.get('anchor_y', 0)
                dx = img_x - cx
                dy = img_y - cy
                angle = -rotation * math.pi / 180
                rx = dx * math.cos(angle) - dy * math.sin(angle) + cx
                ry = dx * math.sin(angle) + dy * math.cos(angle) + cy
            else:
                rx, ry = img_x, img_y

            if atype == 'text':
                if abs(data['x'] - rx) < 50 and abs(data['y'] - ry) < 30:
                    return i
            elif atype in ('arrow', 'line', 'measure'):
                mx = (data['x1'] + data['x2']) / 2
                my = (data['y1'] + data['y2']) / 2
                if abs(mx - rx) < threshold * 3 and abs(my - ry) < threshold * 3:
                    return i
            elif atype in ('rect', 'circle'):
                cx_a = data['x'] + data['w'] / 2
                cy_a = data['y'] + data['h'] / 2
                if abs(cx_a - rx) < max(data['w'] / 2, threshold) and \
                   abs(cy_a - ry) < max(data['h'] / 2, threshold):
                    return i
        return -1

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), self.bg_color)

        if not self.pixmap:
            painter.end()
            return

        scaled = self.pixmap.scaled(
            self.pixmap.size() * self.scale,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        x, y = self._img_offset()
        painter.drawPixmap(x, y, scaled)

        color = self.editor._get_color()
        line_w = self.editor._get_line_width()

        # 绘制已有注释
        for ann_idx, ann in enumerate(self.annotations):
            atype, data = ann
            ann_color = data.get('color', color)
            ann_width = data.get('width', line_w)
            rotation = data.get('rotation', 0)
            anchor_x = data.get('anchor_x', 0)
            anchor_y = data.get('anchor_y', 0)

            if rotation != 0:
                sx, sy = self._to_screen(anchor_x, anchor_y)
                painter.save()
                painter.translate(sx, sy)
                painter.rotate(rotation)
                painter.translate(-sx, -sy)

            pen = QPen(ann_color, ann_width)
            painter.setPen(pen)

            if atype == 'text':
                painter.setPen(QPen(ann_color, 1))
                font_size = max(10, int(14 * self.scale))
                painter.setFont(QFont("SimSun", font_size, QFont.Bold))
                fm = painter.fontMetrics()
                text_rect = fm.boundingRect(data['text'])
                scr_x, scr_y = self._to_screen(data['x'], data['y'])
                bg_color = data.get('bg_color')
                bg_opacity = data.get('bg_opacity', 140)
                bg_rect = QRect(scr_x - 2, scr_y - text_rect.height() - 2,
                                text_rect.width() + 4, text_rect.height() + 4)
                if bg_color:
                    painter.fillRect(bg_rect, QColor(bg_color.red(), bg_color.green(), bg_color.blue(), bg_opacity))
                else:
                    painter.fillRect(bg_rect, QColor(0, 0, 0, bg_opacity))
                painter.setPen(QPen(ann_color, 1))
                painter.drawText(scr_x, scr_y, data['text'])
            elif atype == 'arrow':
                sx1, sy1 = self._to_screen(data['x1'], data['y1'])
                sx2, sy2 = self._to_screen(data['x2'], data['y2'])
                self._draw_arrow(painter, sx1, sy1, sx2, sy2, ann_color, ann_width)
            elif atype == 'line':
                sx1, sy1 = self._to_screen(data['x1'], data['y1'])
                sx2, sy2 = self._to_screen(data['x2'], data['y2'])
                painter.drawLine(int(sx1), int(sy1), int(sx2), int(sy2))
            elif atype == 'rect':
                sx, sy = self._to_screen(data['x'], data['y'])
                sw, sh = data['w'] * self.scale, data['h'] * self.scale
                painter.setBrush(QColor(ann_color.red(), ann_color.green(), ann_color.blue(), 30))
                painter.drawRect(QRectF(sx, sy, sw, sh))
                painter.setBrush(Qt.NoBrush)
            elif atype == 'circle':
                sx, sy = self._to_screen(data['x'], data['y'])
                sw, sh = data['w'] * self.scale, data['h'] * self.scale
                painter.setBrush(QColor(ann_color.red(), ann_color.green(), ann_color.blue(), 30))
                painter.drawEllipse(QRectF(sx, sy, sw, sh))
                painter.setBrush(Qt.NoBrush)
            elif atype == 'measure':
                sx1, sy1 = self._to_screen(data['x1'], data['y1'])
                sx2, sy2 = self._to_screen(data['x2'], data['y2'])
                painter.drawLine(int(sx1), int(sy1), int(sx2), int(sy2))
                painter.setBrush(ann_color)
                painter.drawEllipse(QPoint(int(sx1), int(sy1)), 3, 3)
                painter.drawEllipse(QPoint(int(sx2), int(sy2)), 3, 3)
                painter.setBrush(Qt.NoBrush)
                dist = data.get('distance', '')
                if dist:
                    mx = (sx1 + sx2) / 2
                    my = (sy1 + sy2) / 2 - 8
                    painter.setFont(QFont("SimSun", max(9, int(11 * self.scale)), QFont.Bold))
                    painter.setPen(QPen(ann_color, 1))
                    fm = painter.fontMetrics()
                    tr = fm.boundingRect(dist)
                    painter.fillRect(QRect(mx - 2, my - tr.height() - 2, tr.width() + 4, tr.height() + 4),
                                     QColor(0, 0, 0, 160))
                    painter.drawText(int(mx), int(my), dist)

            if rotation != 0:
                painter.restore()

        # 绘制选中注释的选择框和手柄
        if 0 <= self.selected_index < len(self.annotations):
            atype, data = self.annotations[self.selected_index]
            rotation = data.get('rotation', 0)
            anchor_x = data.get('anchor_x', 0)
            anchor_y = data.get('anchor_y', 0)

            if rotation != 0:
                sx, sy = self._to_screen(anchor_x, anchor_y)
                painter.save()
                painter.translate(sx, sy)
                painter.rotate(rotation)
                painter.translate(-sx, -sy)

            bx, by, bw, bh = self._get_annotation_bbox(data)
            sbx, sby = self._to_screen(bx, by)
            sbw, sbh = bw * self.scale, bh * self.scale

            # 虚线边框
            pen = QPen(QColor(63, 123, 247), 1, Qt.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(QRectF(sbx - 2, sby - 2, sbw + 4, sbh + 4))

            # 缩放手柄
            positions, rot_pos = self._get_handles(data)
            hs = self.HANDLE_SIZE
            painter.setPen(QPen(QColor(63, 123, 247), 1))
            painter.setBrush(QColor(240, 240, 245))
            for hx, hy in positions:
                painter.drawRect(QRectF(hx - hs / 2, hy - hs / 2, hs, hs))

            # 旋转手柄
            rx, ry = rot_pos
            painter.setBrush(QColor(63, 123, 247))
            painter.drawEllipse(QPointF(rx, ry), hs / 2, hs / 2)
            # 连接线
            painter.setPen(QPen(QColor(63, 123, 247), 1, Qt.DashLine))
            top_center_x = sbx + sbw / 2
            top_center_y = sby
            painter.drawLine(int(top_center_x), int(top_center_y), int(rx), int(ry))

            if rotation != 0:
                painter.restore()

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
                painter.setBrush(QColor(color.red(), color.green(), color.blue(), 30))
                painter.drawRect(rx, ry, rw, rh)
                painter.setBrush(Qt.NoBrush)
            elif self.tool == 'circle':
                rx = min(self.draw_start.x(), self.draw_current.x())
                ry = min(self.draw_start.y(), self.draw_current.y())
                rw = abs(self.draw_current.x() - self.draw_start.x())
                rh = abs(self.draw_current.y() - self.draw_start.y())
                painter.setBrush(QColor(color.red(), color.green(), color.blue(), 30))
                painter.drawEllipse(rx, ry, rw, rh)
                painter.setBrush(Qt.NoBrush)
            elif self.tool == 'measure':
                painter.drawLine(self.draw_start, self.draw_current)
                painter.setBrush(color)
                painter.drawEllipse(self.draw_start, 3, 3)
                painter.drawEllipse(self.draw_current, 3, 3)
                painter.setBrush(Qt.NoBrush)
                dx = abs(self.draw_current.x() - self.draw_start.x()) / self.scale
                dy = abs(self.draw_current.y() - self.draw_start.y()) / self.scale
                dist_px = (dx ** 2 + dy ** 2) ** 0.5
                painter.setFont(QFont("SimSun", 11, QFont.Bold))
                painter.setPen(QPen(color, 1))
                mx = (self.draw_start.x() + self.draw_current.x()) / 2
                my = (self.draw_start.y() + self.draw_current.y()) / 2 - 8
                painter.drawText(int(mx), int(my), f'{dist_px:.1f}px')

        painter.end()

    def _draw_arrow(self, painter, x1, y1, x2, y2, color=None, width=2):
        pen = QPen(color or QColor(255, 80, 80), width)
        painter.setPen(pen)
        painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        angle = math.atan2(y2 - y1, x2 - x1)
        arrow_size = max(10, width * 5)
        p1 = QPoint(int(x2 - arrow_size * math.cos(angle - 0.4)),
                     int(y2 - arrow_size * math.sin(angle - 0.4)))
        p2 = QPoint(int(x2 - arrow_size * math.cos(angle + 0.4)),
                     int(y2 - arrow_size * math.sin(angle + 0.4)))
        painter.setBrush(color or QColor(255, 80, 80))
        painter.drawPolygon(QPolygon([QPoint(int(x2), int(y2)), p1, p2]))
        painter.setBrush(Qt.NoBrush)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.editor._zoom_in()
        else:
            self.editor._zoom_out()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        # 选择工具
        if self.tool == 'select':
            # 先检查是否点击了选中注释的手柄
            if 0 <= self.selected_index < len(self.annotations):
                _, sel_data = self.annotations[self.selected_index]
                handle = self._hit_handle(event.pos(), sel_data)
                if handle >= 0:
                    self._drag_handle = handle
                    self._drag_start_pos = event.pos()
                    self._drag_start_data = dict(sel_data)
                    return

            # 检查是否点击了某个注释
            img_x, img_y = self._img_coords(event.pos())
            idx = self._find_annotation_at(img_x, img_y)
            if idx >= 0:
                self.selected_index = idx
                self.editor.show_property_panel(self.annotations[idx][1])
            else:
                self.selected_index = -1
                self.editor.hide_property_panel()
            self.update()
            return

        if self.tool == 'pan':
            self.dragging = True
            self.last_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        elif self.tool == 'text':
            ix, iy = self._img_coords(event.pos())
            text, ok = QInputDialog.getText(self, '添加文字', '注释文字:')
            if ok and text:
                color = self.editor._get_color()
                width = self.editor._get_line_width()
                self.annotations.append(('text', {
                    'x': ix, 'y': iy, 'text': text,
                    'color': color, 'width': width,
                    'rotation': 0, 'scale_x': 1.0, 'scale_y': 1.0,
                    'bg_color': None, 'bg_opacity': 140,
                    'anchor_x': ix, 'anchor_y': iy,
                }))
                self.selected_index = len(self.annotations) - 1
                self.editor.show_property_panel(self.annotations[-1][1])
                self.update()
        elif self.tool == 'eraser':
            ix, iy = self._img_coords(event.pos())
            idx = self._find_annotation_at(ix, iy)
            if idx >= 0:
                self.annotations.pop(idx)
                if self.selected_index == idx:
                    self.selected_index = -1
                    self.editor.hide_property_panel()
                elif self.selected_index > idx:
                    self.selected_index -= 1
                self.update()
        else:
            self.drawing = True
            self.draw_start = event.pos()
            self.draw_current = event.pos()

    def mouseMoveEvent(self, event):
        # 拖拽手柄
        if self._drag_handle >= 0 and self._drag_start_pos:
            pos = event.pos()
            if self._drag_handle == 8:
                # 旋转手柄
                _, data = self.annotations[self.selected_index]
                anchor_x = data.get('anchor_x', 0)
                anchor_y = data.get('anchor_y', 0)
                sx, sy = self._to_screen(anchor_x, anchor_y)
                angle = math.atan2(pos.y() - sy, pos.x() - sx)
                deg = math.degrees(angle) + 90  # 0度朝上
                if deg < 0:
                    deg += 360
                data['rotation'] = deg % 360
                # 更新属性面板
                self.editor.prop_panel.rotation_input.blockSignals(True)
                self.editor.prop_panel.rotation_input.setValue(int(deg % 360))
                self.editor.prop_panel.rotation_input.blockSignals(False)
            else:
                # 缩放手柄
                self._resize_annotation(pos)
            self.update()
            return

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

        # 结束手柄拖拽
        if self._drag_handle >= 0:
            self._drag_handle = -1
            self._drag_start_pos = None
            self._drag_start_data = None
            return

        if self.dragging:
            self.dragging = False
            self.last_pos = None
            self.setCursor(Qt.ArrowCursor)
        elif self.drawing and self.draw_start and self.draw_current:
            ix1, iy1 = self._img_coords(self.draw_start)
            ix2, iy2 = self._img_coords(self.draw_current)
            color = self.editor._get_color()
            width = self.editor._get_line_width()
            base_props = {
                'color': color, 'width': width,
                'rotation': 0, 'scale_x': 1.0, 'scale_y': 1.0,
                'bg_color': None, 'bg_opacity': 140,
            }
            if self.tool == 'arrow':
                base_props.update({'x1': ix1, 'y1': iy1, 'x2': ix2, 'y2': iy2})
                base_props['anchor_x'] = (ix1 + ix2) / 2
                base_props['anchor_y'] = (iy1 + iy2) / 2
                self.annotations.append(('arrow', base_props))
            elif self.tool == 'line':
                base_props.update({'x1': ix1, 'y1': iy1, 'x2': ix2, 'y2': iy2})
                base_props['anchor_x'] = (ix1 + ix2) / 2
                base_props['anchor_y'] = (iy1 + iy2) / 2
                self.annotations.append(('line', base_props))
            elif self.tool == 'rect':
                rx = min(ix1, ix2)
                ry = min(iy1, iy2)
                base_props.update({'x': rx, 'y': ry, 'w': abs(ix2 - ix1), 'h': abs(iy2 - iy1)})
                base_props['anchor_x'] = rx + abs(ix2 - ix1) / 2
                base_props['anchor_y'] = ry + abs(iy2 - iy1) / 2
                self.annotations.append(('rect', base_props))
            elif self.tool == 'circle':
                rx = min(ix1, ix2)
                ry = min(iy1, iy2)
                base_props.update({'x': rx, 'y': ry, 'w': abs(ix2 - ix1), 'h': abs(iy2 - iy1)})
                base_props['anchor_x'] = rx + abs(ix2 - ix1) / 2
                base_props['anchor_y'] = ry + abs(iy2 - iy1) / 2
                self.annotations.append(('circle', base_props))
            elif self.tool == 'measure':
                dx = abs(ix2 - ix1)
                dy = abs(iy2 - iy1)
                dist = (dx ** 2 + dy ** 2) ** 0.5
                base_props.update({
                    'x1': ix1, 'y1': iy1, 'x2': ix2, 'y2': iy2,
                    'distance': f'{dist:.1f}px',
                })
                base_props['anchor_x'] = (ix1 + ix2) / 2
                base_props['anchor_y'] = (iy1 + iy2) / 2
                self.annotations.append(('measure', base_props))

            # 自动选中新创建的注释
            self.selected_index = len(self.annotations) - 1
            self.editor.show_property_panel(self.annotations[-1][1])

            self.drawing = False
            self.draw_start = None
            self.draw_current = None
            self.update()

    def _resize_annotation(self, pos):
        """根据拖拽的缩放手柄调整注释大小"""
        if self.selected_index < 0 or not self._drag_start_data:
            return
        atype, data = self.annotations[self.selected_index]
        sd = self._drag_start_data
        handle = self._drag_handle

        # 计算鼠标移动的图片坐标偏移
        img_x, img_y = self._img_coords(pos)
        start_img_x = self._drag_start_pos.x() - self._img_offset()[0]
        start_img_y = self._drag_start_pos.y() - self._img_offset()[1]
        dx_img = img_x - start_img_x
        dy_img = img_y - start_img_y

        if 'w' in sd:
            # rect/circle 类型
            x, y, w, h = sd['x'], sd['y'], sd['w'], sd['h']
            if handle == 0:  # TL
                data['x'] = x + dx_img
                data['y'] = y + dy_img
                data['w'] = w - dx_img
                data['h'] = h - dy_img
            elif handle == 1:  # T
                data['y'] = y + dy_img
                data['h'] = h - dy_img
            elif handle == 2:  # TR
                data['y'] = y + dy_img
                data['w'] = w + dx_img
                data['h'] = h - dy_img
            elif handle == 3:  # R
                data['w'] = w + dx_img
            elif handle == 4:  # BR
                data['w'] = w + dx_img
                data['h'] = h + dy_img
            elif handle == 5:  # B
                data['h'] = h + dy_img
            elif handle == 6:  # BL
                data['x'] = x + dx_img
                data['w'] = w - dx_img
                data['h'] = h + dy_img
            elif handle == 7:  # L
                data['x'] = x + dx_img
                data['w'] = w - dx_img
            # 确保宽高不为负
            if data['w'] < 5:
                data['w'] = 5
            if data['h'] < 5:
                data['h'] = 5
            # 更新锚点
            data['anchor_x'] = data['x'] + data['w'] / 2
            data['anchor_y'] = data['y'] + data['h'] / 2
        elif 'x1' in sd:
            # arrow/line/measure 类型
            x1, y1, x2, y2 = sd['x1'], sd['y1'], sd['x2'], sd['y2']
            if handle in (0, 6, 7):  # 左侧手柄影响起点
                data['x1'] = x1 + dx_img
                data['y1'] = y1 + dy_img
            if handle in (2, 3, 4):  # 右侧手柄影响终点
                data['x2'] = x2 + dx_img
                data['y2'] = y2 + dy_img
            if handle == 1:  # 上中
                data['y1'] = y1 + dy_img
            if handle == 5:  # 下中
                data['y2'] = y2 + dy_img
            data['anchor_x'] = (data['x1'] + data['x2']) / 2
            data['anchor_y'] = (data['y1'] + data['y2']) / 2

    def save_annotated(self, path):
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
            rotation = data.get('rotation', 0)
            anchor_x = data.get('anchor_x', 0)
            anchor_y = data.get('anchor_y', 0)

            if rotation != 0:
                painter.save()
                painter.translate(anchor_x, anchor_y)
                painter.rotate(rotation)
                painter.translate(-anchor_x, -anchor_y)

            pen = QPen(color, width)
            painter.setPen(pen)
            if atype == 'text':
                painter.setPen(QPen(color, 1))
                painter.setFont(QFont("SimSun", 14, QFont.Bold))
                bg_color = data.get('bg_color')
                bg_opacity = data.get('bg_opacity', 140)
                fm = painter.fontMetrics()
                text_rect = fm.boundingRect(data['text'])
                bg_rect = QRect(data['x'] - 2, data['y'] - text_rect.height() - 2,
                                text_rect.width() + 4, text_rect.height() + 4)
                if bg_color:
                    painter.fillRect(bg_rect, QColor(bg_color.red(), bg_color.green(), bg_color.blue(), bg_opacity))
                else:
                    painter.fillRect(bg_rect, QColor(0, 0, 0, bg_opacity))
                painter.setPen(QPen(color, 1))
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
            elif atype == 'measure':
                painter.drawLine(int(data['x1']), int(data['y1']), int(data['x2']), int(data['y2']))
                painter.setBrush(color)
                painter.drawEllipse(QPoint(int(data['x1']), int(data['y1'])), 3, 3)
                painter.drawEllipse(QPoint(int(data['x2']), int(data['y2'])), 3, 3)
                painter.setBrush(Qt.NoBrush)
                dist = data.get('distance', '')
                if dist:
                    painter.setFont(QFont("SimSun", 11, QFont.Bold))
                    mx = (data['x1'] + data['x2']) / 2
                    my = (data['y1'] + data['y2']) / 2 - 8
                    painter.drawText(int(mx), int(my), dist)

            if rotation != 0:
                painter.restore()

        painter.end()
        base, ext = os.path.splitext(path)
        save_path = base + '_annotated' + ext
        result.save(save_path)


# ── 内联图片控件（支持悬停缩放与双击浏览） ─────────────────
class _ImageLabel(QWidget):
    """内联图片控件：悬停时滚轮缩放，双击打开 ImageViewerDialog"""
    double_clicked = pyqtSignal(int, str)  # img_id, img_path

    def __init__(self, pixmap, img_id=0, img_path='', max_width=400, parent=None):
        super().__init__(parent)
        self._pixmap = pixmap
        self.img_id = img_id
        self.img_path = img_path
        self._max_width = max_width
        self._scale = 1.0
        self._hover = False
        self._anim_timer = QTimer(self)
        self._anim_timer.setSingleShot(True)
        self._anim_timer.timeout.connect(self._animate_zoom)
        self._target_scale = 1.0
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self._update_size()

    def _update_size(self):
        if self._pixmap.isNull():
            self.setFixedSize(0, 0)
            return
        w = min(self._pixmap.width(), self._max_width)
        ratio = w / self._pixmap.width()
        h = int(self._pixmap.height() * ratio * self._scale)
        w = int(w * self._scale)
        self.setFixedSize(w, h)
        self.update()

    def paintEvent(self, event):
        if self._pixmap.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        w = min(self._pixmap.width(), self._max_width)
        scaled = self._pixmap.scaled(w, int(w * self._pixmap.height() / self._pixmap.width()),
                                      Qt.KeepAspectRatio, Qt.SmoothTransformation)
        if self._scale != 1.0:
            scaled = scaled.scaled(int(scaled.width() * self._scale),
                                   int(scaled.height() * self._scale),
                                   Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)
        # 悬停时绘制蓝色边框
        if self._hover:
            pen = QPen(QColor(63, 123, 247, 160), 2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(1, 1, self.width() - 2, self.height() - 2)
        painter.end()

    def wheelEvent(self, event):
        if not self._hover:
            event.ignore()
            return
        delta = event.angleDelta().y()
        if delta > 0:
            self._target_scale = min(self._scale * 1.1, 3.0)
        else:
            self._target_scale = max(self._scale / 1.1, 1.0)
        self._animate_zoom()
        event.accept()

    def _animate_zoom(self):
        step = 0.05 if self._target_scale > self._scale else -0.05
        new_scale = self._scale + step
        if (step > 0 and new_scale >= self._target_scale) or \
           (step < 0 and new_scale <= self._target_scale):
            self._scale = self._target_scale
        else:
            self._scale = new_scale
            self._anim_timer.start(16)
        self._update_size()

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        if self._scale > 1.0:
            self._target_scale = 1.0
            self._animate_zoom()
        else:
            self.update()
        super().leaveEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self.img_id, self.img_path)


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

        # 内容区：可滚动页面容器
        self.page_scroll = QScrollArea()
        self.page_scroll.setWidgetResizable(True)
        self.page_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.page_container = QWidget()
        self.page_layout = QVBoxLayout(self.page_container)
        self.page_layout.setContentsMargins(16, 16, 16, 16)
        self.page_layout.setSpacing(8)
        self.page_layout.addStretch()
        self.page_scroll.setWidget(self.page_container)
        self.page_scroll.hide()
        layout.addWidget(self.page_scroll)

        # 文本浏览器（非影像标签页使用）
        self.content_browser = QTextBrowser()
        self.content_browser.setOpenExternalLinks(True)
        self.content_browser.setStyleSheet("border: none; padding: 16px;")
        layout.addWidget(self.content_browser)

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

        # 存储当前影像页面的图片列表（用于双击浏览）
        self._current_image_list = []

    def switch_tab(self, idx):
        self.current_tab = idx
        for i, btn in enumerate(self.tab_buttons):
            btn.setProperty('active', i == idx)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        # 影像操作栏和页面滚动区仅在影像所见标签页显示
        is_imaging = (idx == 2)
        self.img_action_bar.setVisible(is_imaging)
        self.page_scroll.setVisible(is_imaging)
        self.content_browser.setVisible(not is_imaging)
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
        # 清除页面容器中的旧内容
        while self.page_layout.count():
            item = self.page_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._current_image_list = []

        if not self.current_disease_id:
            lbl = QLabel('请先选择疾病')
            lbl.setStyleSheet("color: #666; padding: 16px;")
            self.page_layout.insertWidget(self.page_layout.count() - 1, lbl)
            return

        conn = sqlite3.connect(self.active_db)
        c = conn.cursor()
        c.execute("SELECT id, filename, caption, media_type FROM images WHERE disease_id=?",
                  (self.current_disease_id,))
        rows = c.fetchall()
        conn.close()

        # 收集所有图片路径（用于双击浏览）
        for img_id, filename, caption, media_type in rows:
            img_path = os.path.join(APP_DIR, 'images', filename) if filename else ''
            if img_path and os.path.exists(img_path):
                self._current_image_list.append((img_id, img_path))

        # 辅助方法：添加标题
        def add_heading(text, level=2):
            colors = {1: '#3f7bf7', 2: '#5a91ff', 3: '#7aadff'}
            color = colors.get(level, '#5a91ff')
            sizes = {1: '20px', 2: '16px', 3: '14px'}
            size = sizes.get(level, '14px')
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color: {color}; font-size: {size}; font-weight: bold; margin-top: 12px; margin-bottom: 4px;")
            self.page_layout.insertWidget(self.page_layout.count() - 1, lbl)

        # 辅助方法：添加正文
        def add_body(text):
            if not text:
                return
            lbl = QLabel(text)
            lbl.setWordWrap(True)
            lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            lbl.setStyleSheet("color: #c8c8cc; line-height: 1.8; font-size: 13px; margin-bottom: 4px;")
            self.page_layout.insertWidget(self.page_layout.count() - 1, lbl)

        # 辅助方法：添加内联图片
        def add_image(img_id, filename, caption):
            img_path = os.path.join(APP_DIR, 'images', filename) if filename else ''
            if not os.path.exists(img_path):
                return
            pixmap = QPixmap(img_path)
            if pixmap.isNull():
                return
            img_label = _ImageLabel(pixmap, img_id=img_id, img_path=img_path, max_width=400)
            img_label.double_clicked.connect(self._on_image_double_clicked)
            self.page_layout.insertWidget(self.page_layout.count() - 1, img_label)
            # 图片说明
            if caption:
                cap_lbl = QLabel(caption)
                cap_lbl.setStyleSheet("color: #888890; font-size: 11px; margin-bottom: 8px;")
                cap_lbl.setAlignment(Qt.AlignCenter)
                self.page_layout.insertWidget(self.page_layout.count() - 1, cap_lbl)

        # 渲染页面内容
        add_heading("影像所见")

        if d.get('xray_finding'):
            add_heading("X线", 3)
            add_body(d['xray_finding'])
            for img_id, filename, caption, mt in rows:
                if mt == 'xray':
                    add_image(img_id, filename, caption)

        if d.get('ct_finding'):
            add_heading("CT", 3)
            add_body(d['ct_finding'])
            for img_id, filename, caption, mt in rows:
                if mt == 'ct':
                    add_image(img_id, filename, caption)

        if d.get('mri_finding'):
            add_heading("MRI", 3)
            add_body(d['mri_finding'])
            for img_id, filename, caption, mt in rows:
                if mt == 'mri':
                    add_image(img_id, filename, caption)

        if d.get('pet_finding'):
            add_heading("PET", 3)
            add_body(d['pet_finding'])
            for img_id, filename, caption, mt in rows:
                if mt == 'pet':
                    add_image(img_id, filename, caption)

        # 未分类的图片（media_type 为 'image' 或其他）
        uncategorized = [(iid, fn, cap, mt) for iid, fn, cap, mt in rows
                         if mt not in ('xray', 'ct', 'mri', 'pet')]
        if uncategorized:
            add_heading("影像资料", 3)
            for img_id, filename, caption, mt in uncategorized:
                add_image(img_id, filename, caption)

        # 底部提示
        tip = QLabel(f'共 {len(rows)} 张影像（悬停滚轮缩放，双击图片进入浏览）')
        tip.setStyleSheet("color: #888890; font-size: 11px; margin-top: 12px;")
        self.page_layout.insertWidget(self.page_layout.count() - 1, tip)

    def _on_image_double_clicked(self, img_id, img_path):
        """内联图片双击：打开 ImageViewerDialog"""
        if not self._current_image_list:
            return
        current_idx = 0
        for i, (iid, ipath) in enumerate(self._current_image_list):
            if iid == img_id and ipath == img_path:
                current_idx = i
                break
        viewer = ImageViewerDialog(self._current_image_list, current_idx, self)
        viewer.exec_()

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

        file_menu.addSeparator()

        ai_config_action = QAction('AI 配置', self)
        ai_config_action.triggered.connect(self.show_ai_config)
        file_menu.addAction(ai_config_action)

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

    def show_ai_config(self):
        dlg = AIConfigDialog(self)
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
