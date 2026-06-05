import sqlite3
import json
import hashlib
import os
import uuid
import base64

# 尝试导入 cryptography，不可用时使用备用方案
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(APP_DIR, 'radatlas.db')
USER_DB = os.path.join(APP_DIR, 'users.db')

# 加密盐值（用于密钥派生）
ENCRYPTION_SALT = b'radatlas_encryption_salt_2024'


def generate_key(password):
    """根据用户密码生成加密密钥"""
    if HAS_CRYPTOGRAPHY:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=ENCRYPTION_SALT,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password.encode('utf-8'))
        return base64.urlsafe_b64encode(key)
    else:
        # 备用方案：使用 SHA256 哈希
        key = hashlib.sha256(ENCRYPTION_SALT + password.encode('utf-8')).digest()
        return base64.urlsafe_b64encode(key)


def generate_unique_filename(original_name):
    """生成唯一的加密文件名"""
    ext = os.path.splitext(original_name)[1]
    unique_name = str(uuid.uuid4())[:16] + ext
    return unique_name


def _xor_encrypt(data, key):
    """简单的 XOR 加密（备用方案，当 cryptography 不可用时使用）"""
    key_bytes = key if isinstance(key, bytes) else key.encode('utf-8')
    result = bytearray(len(data))
    key_len = len(key_bytes)
    for i in range(len(data)):
        result[i] = data[i] ^ key_bytes[i % key_len]
    return bytes(result)


def encrypt_filename(filename, key):
    """加密文件名"""
    if HAS_CRYPTOGRAPHY:
        fernet = Fernet(key)
        encrypted = fernet.encrypt(filename.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')[:64]
    else:
        encrypted = _xor_encrypt(filename.encode('utf-8'), key)
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')[:64]


def decrypt_filename(encrypted_name, key):
    """解密文件名"""
    try:
        data = base64.urlsafe_b64decode(encrypted_name)
        if HAS_CRYPTOGRAPHY:
            fernet = Fernet(key)
            return fernet.decrypt(data).decode('utf-8')
        else:
            return _xor_encrypt(data, key).decode('utf-8')
    except Exception:
        return None


def encrypt_image(image_path, key):
    """加密图片文件"""
    if HAS_CRYPTOGRAPHY:
        fernet = Fernet(key)
        with open(image_path, 'rb') as f:
            data = f.read()
        encrypted_data = fernet.encrypt(data)
        with open(image_path, 'wb') as f:
            f.write(encrypted_data)
    else:
        with open(image_path, 'rb') as f:
            data = f.read()
        encrypted_data = _xor_encrypt(data, key)
        with open(image_path, 'wb') as f:
            f.write(encrypted_data)


def decrypt_image(image_path, key):
    """解密图片文件"""
    if HAS_CRYPTOGRAPHY:
        fernet = Fernet(key)
        with open(image_path, 'rb') as f:
            encrypted_data = f.read()
        try:
            decrypted_data = fernet.decrypt(encrypted_data)
            return decrypted_data
        except Exception:
            return None
    else:
        with open(image_path, 'rb') as f:
            encrypted_data = f.read()
        try:
            decrypted_data = _xor_encrypt(encrypted_data, key)
            return decrypted_data
        except Exception:
            return None


def encrypt_image_to_bytes(image_path, key):
    """加密图片并返回加密后的字节数据"""
    with open(image_path, 'rb') as f:
        data = f.read()
    if HAS_CRYPTOGRAPHY:
        fernet = Fernet(key)
        return fernet.encrypt(data)
    else:
        return _xor_encrypt(data, key)


def decrypt_bytes_to_image(encrypted_data, key, output_path):
    """解密字节数据并保存为图片文件"""
    if HAS_CRYPTOGRAPHY:
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted_data)
    else:
        decrypted_data = _xor_encrypt(encrypted_data, key)
    with open(output_path, 'wb') as f:
        f.write(decrypted_data)


def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def init_user_db():
    conn = sqlite3.connect(USER_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  role TEXT NOT NULL DEFAULT 'user',
                  database TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username, password, role, database) VALUES (?, ?, ?, ?)",
                  ('admin', hash_password('admin123'), 'admin', DATABASE))
    conn.commit()
    conn.close()


def authenticate_user(username, password):
    conn = sqlite3.connect(USER_DB)
    c = conn.cursor()
    c.execute("SELECT id, username, role, database FROM users WHERE username=? AND password=?",
              (username, hash_password(password)))
    row = c.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'username': row[1], 'role': row[2], 'database': row[3]}
    return None


def get_all_users():
    conn = sqlite3.connect(USER_DB)
    c = conn.cursor()
    c.execute("SELECT id, username, role, database, created_at FROM users ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows


def create_user(username, password, role='user', database=None):
    conn = sqlite3.connect(USER_DB)
    c = conn.cursor()
    try:
        if database is None:
            db_name = os.path.join(APP_DIR, f"user_{username}.db")
            database = db_name
        c.execute("INSERT INTO users (username, password, role, database) VALUES (?, ?, ?, ?)",
                  (username, hash_password(password), role, database))
        conn.commit()
        conn.close()
        return True, database
    except sqlite3.IntegrityError:
        conn.close()
        return False, None


def delete_user(user_id):
    conn = sqlite3.connect(USER_DB)
    c = conn.cursor()
    c.execute("SELECT database FROM users WHERE id=? AND role!='admin'", (user_id,))
    row = c.fetchone()
    if row and row[0] and os.path.exists(row[0]):
        os.remove(row[0])
    c.execute("DELETE FROM users WHERE id=? AND role!='admin'", (user_id,))
    conn.commit()
    conn.close()


def change_password(user_id, old_password, new_password):
    conn = sqlite3.connect(USER_DB)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id=? AND password=?", (user_id, hash_password(old_password)))
    if c.fetchone():
        c.execute("UPDATE users SET password=? WHERE id=?", (hash_password(new_password), user_id))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


def rename_user(user_id, new_username):
    conn = sqlite3.connect(USER_DB)
    c = conn.cursor()
    try:
        c.execute("UPDATE users SET username=? WHERE id=?", (new_username, user_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def admin_change_password(user_id, new_password):
    """管理员直接修改用户密码，无需旧密码"""
    conn = sqlite3.connect(USER_DB)
    c = conn.cursor()
    c.execute("UPDATE users SET password=? WHERE id=?", (hash_password(new_password), user_id))
    conn.commit()
    conn.close()


def init_db(db_path=None):
    if db_path is None:
        db_path = DATABASE
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS diseases
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name_cn TEXT, name_en TEXT, system TEXT, category TEXT,
                  clinical TEXT, diagnosis TEXT,
                  primary_img TEXT, secondary_img TEXT,
                  xray_finding TEXT, ct_finding TEXT, mri_finding TEXT, pet_finding TEXT,
                  report_template TEXT, differential_diagnosis TEXT, treatment TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS images
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  disease_id INTEGER, filename TEXT, image_type TEXT,
                  caption TEXT, source TEXT, media_type TEXT, annotations TEXT,
                  owner_id INTEGER, encrypted INTEGER DEFAULT 0, encryption_hash TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS medical_records
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  disease_id INTEGER, title TEXT, content TEXT,
                  image_filename TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS anatomy_records
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT, content TEXT,
                  image_filename TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    try:
        c.execute("ALTER TABLE images ADD COLUMN media_type TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE images ADD COLUMN annotations TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE images ADD COLUMN owner_id INTEGER")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE images ADD COLUMN encrypted INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE images ADD COLUMN encryption_hash TEXT")
    except sqlite3.OperationalError:
        pass
    c.execute("UPDATE images SET media_type = 'image' WHERE media_type IS NULL")
    conn.commit()
    conn.close()


def load_data(db_path=None):
    if db_path is None:
        db_path = DATABASE
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM diseases')
    if c.fetchone()[0] == 0:
        data_json = os.path.join(APP_DIR, 'data.json')
        if os.path.exists(data_json):
            with open(data_json, 'r', encoding='utf-8') as f:
                raw = f.read().strip()
            # 提取系统名（文件首行的 "xxx": 部分）
            import re
            system_match = re.match(r'"([^"]+)"\s*:', raw)
            default_system = system_match.group(1) if system_match else "未分类"
            # 用状态机提取所有疾病对象（兼容对象间缺少逗号的非标准JSON）
            diseases = []
            depth = 0
            start = -1
            for i, ch in enumerate(raw):
                if ch == '{':
                    if depth == 0:
                        start = i
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0 and start >= 0:
                        obj_str = raw[start:i+1]
                        try:
                            obj = json.loads(obj_str)
                            if 'name_cn' in obj:
                                diseases.append(obj)
                        except json.JSONDecodeError:
                            pass
                        start = -1
            # 根据category推断system
            cat_to_system = {
                '脑血管病': '头颈部', '脑肿瘤': '头颈部', '颅内感染': '头颈部',
                '脱髓鞘': '头颈部', '头颈部肿瘤': '头颈部', '眼眶疾病': '头颈部',
                '鼻窦疾病': '头颈部', '耳部疾病': '头颈部', '颈部先天性': '头颈部',
                '颈部疾病': '头颈部', '神经皮肤综合征': '头颈部',
                '肺恶性肿瘤': '胸部', '肺良性肿瘤': '胸部', '肺良性病变': '胸部',
                '肺部感染': '胸部', '气道疾病': '胸部', '间质性疾病': '胸部',
                '罕见肺病': '胸部', '罕见遗传性': '胸部', '血管疾病': '胸部',
                '纵隔肿瘤': '胸部', '纵隔疾病': '胸部', '胸膜疾病': '胸部',
                '食管疾病': '胸部', '乳腺疾病': '胸部', '胸壁疾病': '胸部',
                '肝脏肿瘤': '腹部', '肝脏良性病变': '腹部', '肝脏感染': '腹部',
                '肝脏罕见病': '腹部', '肝脏弥漫性病变': '腹部',
                '胆道疾病': '腹部', '胆道肿瘤': '腹部',
                '胰腺疾病': '腹部', '胰腺肿瘤': '腹部',
                '脾脏疾病': '腹部', '脾脏血管': '腹部',
                '胃肠道肿瘤': '腹部', '胃肠道急症': '腹部',
                '炎症性肠病': '腹部', '急腹症': '腹部',
                '腹膜后疾病': '腹部', '肾上腺疾病': '腹部', '腹膜疾病': '腹部',
                '肾脏肿瘤': '泌尿生殖', '肾脏良性肿瘤': '泌尿生殖',
                '肾脏良性病变': '泌尿生殖', '肾脏遗传病': '泌尿生殖',
                '肾脏感染': '泌尿生殖', '泌尿系统结石': '泌尿生殖',
                '肾脏血管': '泌尿生殖', '肾脏外伤': '泌尿生殖',
                '膀胱肿瘤': '泌尿生殖', '膀胱良性': '泌尿生殖',
                '膀胱炎症': '泌尿生殖', '膀胱结石': '泌尿生殖',
                '男性生殖': '泌尿生殖', '男性生殖急症': '泌尿生殖',
                '男性生殖感染': '泌尿生殖',
                '女性生殖': '泌尿生殖', '女性生殖感染': '泌尿生殖',
                '女性生殖急症': '泌尿生殖',
                '代谢性骨病': '骨骼肌肉', '骨恶性肿瘤': '骨骼肌肉',
                '骨肿瘤': '骨骼肌肉', '骨良性肿瘤': '骨骼肌肉',
                '骨肿瘤样病变': '骨骼肌肉', '骨感染': '骨骼肌肉',
                '关节感染': '骨骼肌肉', '创伤': '骨骼肌肉',
                '脊柱创伤': '骨骼肌肉', '脊柱退行性': '骨骼肌肉',
                '关节退行性': '骨骼肌肉', '自身免疫性关节炎': '骨骼肌肉',
                '脊柱关节炎': '骨骼肌肉', '晶体性关节炎': '骨骼肌肉',
                '软组织损伤': '骨骼肌肉', '膝关节损伤': '骨骼肌肉',
                '膝韧带损伤': '骨骼肌肉', '软组织肿瘤': '骨骼肌肉',
                '软组织良性': '骨骼肌肉', '骨关节': '骨骼肌肉',
                '软组织罕见病': '骨骼肌肉', '儿科骨科': '骨骼肌肉',
                '骨罕见病': '骨骼肌肉',
            }
            for d in diseases:
                cat = d.get('category', '').strip()
                system = cat_to_system.get(cat, default_system)
                if system is None:
                    for key, val in cat_to_system.items():
                        if key in cat or cat in key:
                            system = val
                            break
                if system is None:
                    system = default_system
                c.execute('''INSERT INTO diseases
                (name_cn, name_en, system, category, clinical, diagnosis,
                 primary_img, secondary_img, xray_finding, ct_finding, mri_finding, pet_finding,
                 report_template, differential_diagnosis, treatment)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (d['name_cn'], d['name_en'], system, d.get('category',''),
                 d.get('clinical',''), d.get('diagnosis',''),
                 d.get('primary_img',''), d.get('secondary_img',''),
                 d.get('xray',''), d.get('ct',''), d.get('mri',''), d.get('pet',''),
                 d.get('report',''), d.get('diff',''), d.get('treatment','')))
            conn.commit()
    conn.close()


def copy_public_to_user(user_db):
    if not os.path.exists(user_db):
        import shutil
        shutil.copy2(DATABASE, user_db)


def add_disease(db_path, disease_data):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''INSERT INTO diseases
                 (name_cn, name_en, system, category, clinical, diagnosis,
                  primary_img, secondary_img, xray_finding, ct_finding, mri_finding, pet_finding,
                  report_template, differential_diagnosis, treatment)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
              (disease_data.get('name_cn', ''), disease_data.get('name_en', ''),
               disease_data.get('system', ''), disease_data.get('category', ''),
               disease_data.get('clinical', ''), disease_data.get('diagnosis', ''),
               disease_data.get('primary_img', ''), disease_data.get('secondary_img', ''),
               disease_data.get('xray_finding', ''), disease_data.get('ct_finding', ''),
               disease_data.get('mri_finding', ''), disease_data.get('pet_finding', ''),
               disease_data.get('report_template', ''), disease_data.get('differential_diagnosis', ''),
               disease_data.get('treatment', '')))
    disease_id = c.lastrowid
    conn.commit()
    conn.close()
    return disease_id


def update_disease(db_path, disease_id, disease_data):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''UPDATE diseases SET
                 name_cn=?, name_en=?, system=?, category=?,
                 clinical=?, diagnosis=?,
                 primary_img=?, secondary_img=?,
                 xray_finding=?, ct_finding=?, mri_finding=?, pet_finding=?,
                 report_template=?, differential_diagnosis=?, treatment=?
                 WHERE id=?''',
              (disease_data.get('name_cn', ''), disease_data.get('name_en', ''),
               disease_data.get('system', ''), disease_data.get('category', ''),
               disease_data.get('clinical', ''), disease_data.get('diagnosis', ''),
               disease_data.get('primary_img', ''), disease_data.get('secondary_img', ''),
               disease_data.get('xray_finding', ''), disease_data.get('ct_finding', ''),
               disease_data.get('mri_finding', ''), disease_data.get('pet_finding', ''),
               disease_data.get('report_template', ''), disease_data.get('differential_diagnosis', ''),
               disease_data.get('treatment', ''), disease_id))
    conn.commit()
    conn.close()


def delete_disease(db_path, disease_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM images WHERE disease_id=?", (disease_id,))
    c.execute("DELETE FROM medical_records WHERE disease_id=?", (disease_id,))
    c.execute("DELETE FROM diseases WHERE id=?", (disease_id,))
    conn.commit()
    conn.close()


def add_image(db_path, disease_id, filename, image_type, caption, source, media_type, 
              owner_id=None, encrypted=False, encryption_hash=None, original_filename=None):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''INSERT INTO images
                 (disease_id, filename, image_type, caption, source, media_type,
                  owner_id, encrypted, encryption_hash, original_filename)
                 VALUES (?,?,?,?,?,?,?,?,?,?)''',
              (disease_id, filename, image_type, caption, source, media_type,
               owner_id, 1 if encrypted else 0, encryption_hash, original_filename))
    image_id = c.lastrowid
    conn.commit()
    conn.close()
    return image_id


def init_db(db_path=None):
    if db_path is None:
        db_path = DATABASE
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS diseases
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name_cn TEXT, name_en TEXT, system TEXT, category TEXT,
                  clinical TEXT, diagnosis TEXT,
                  primary_img TEXT, secondary_img TEXT,
                  xray_finding TEXT, ct_finding TEXT, mri_finding TEXT, pet_finding TEXT,
                  report_template TEXT, differential_diagnosis TEXT, treatment TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS images
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  disease_id INTEGER, filename TEXT, image_type TEXT,
                  caption TEXT, source TEXT, media_type TEXT, annotations TEXT,
                  owner_id INTEGER, encrypted INTEGER DEFAULT 0, 
                  encryption_hash TEXT, original_filename TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS medical_records
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  disease_id INTEGER, title TEXT, content TEXT,
                  image_filename TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS anatomy_records
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT, content TEXT,
                  image_filename TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    try:
        c.execute("ALTER TABLE images ADD COLUMN media_type TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE images ADD COLUMN annotations TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE images ADD COLUMN owner_id INTEGER")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE images ADD COLUMN encrypted INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE images ADD COLUMN encryption_hash TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE images ADD COLUMN original_filename TEXT")
    except sqlite3.OperationalError:
        pass
    c.execute("UPDATE images SET media_type = 'image' WHERE media_type IS NULL")
    conn.commit()
    conn.close()


def get_image_by_id(db_path, image_id):
    """获取图片信息"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''SELECT id, disease_id, filename, image_type, caption, source, 
                 media_type, owner_id, encrypted, encryption_hash, original_filename 
                 FROM images WHERE id=?''', (image_id,))
    row = c.fetchone()
    conn.close()
    if row is None:
        return None
    return {
        'id': row[0], 'disease_id': row[1], 'filename': row[2], 
        'image_type': row[3], 'caption': row[4], 'source': row[5],
        'media_type': row[6], 'owner_id': row[7], 
        'encrypted': bool(row[8]), 'encryption_hash': row[9],
        'original_filename': row[10]
    }


def update_image_encryption(db_path, image_id, encrypted, encryption_hash=None):
    """更新图片加密状态"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''UPDATE images SET encrypted=?, encryption_hash=? WHERE id=?''', 
              (1 if encrypted else 0, encryption_hash, image_id))
    conn.commit()
    conn.close()


def delete_image(db_path, image_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM images WHERE id=?", (image_id,))
    conn.commit()
    conn.close()


def get_disease(db_path, disease_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''SELECT id, name_cn, name_en, system, category, clinical, diagnosis,
                 primary_img, secondary_img, xray_finding, ct_finding, mri_finding, pet_finding,
                 report_template, differential_diagnosis, treatment
                 FROM diseases WHERE id=?''', (disease_id,))
    row = c.fetchone()
    conn.close()
    if row is None:
        return None
    return {
        'id': row[0], 'name_cn': row[1], 'name_en': row[2],
        'system': row[3], 'category': row[4], 'clinical': row[5],
        'diagnosis': row[6], 'primary_img': row[7], 'secondary_img': row[8],
        'xray_finding': row[9], 'ct_finding': row[10], 'mri_finding': row[11],
        'pet_finding': row[12], 'report_template': row[13],
        'differential_diagnosis': row[14], 'treatment': row[15]
    }


def search_diseases(db_path, keyword):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    pattern = f'%{keyword}%'
    c.execute('''SELECT id, name_cn, name_en, system FROM diseases
                 WHERE name_cn LIKE ? OR name_en LIKE ? OR system LIKE ? OR category LIKE ?''',
              (pattern, pattern, pattern, pattern))
    rows = c.fetchall()
    conn.close()
    return rows
