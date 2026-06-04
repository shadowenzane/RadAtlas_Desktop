"""AI 大模型配置和调用模块"""
import json
import os
import requests

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_config.json')

# 支持的大模型提供商
PROVIDERS = {
    'deepseek': {
        'name': 'DeepSeek',
        'api_url': 'https://api.deepseek.com/v1/chat/completions',
        'models': ['deepseek-chat', 'deepseek-reasoner'],
    },
    'doubao': {
        'name': '豆包(火山引擎)',
        'api_url': 'https://ark.cn-beijing.volces.com/api/v3/chat/completions',
        'models': ['doubao-pro-32k', 'doubao-pro-128k', 'doubao-lite-32k'],
    },
    'openai': {
        'name': 'OpenAI',
        'api_url': 'https://api.openai.com/v1/chat/completions',
        'models': ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'],
    },
    'zhipu': {
        'name': '智谱AI',
        'api_url': 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
        'models': ['glm-4-plus', 'glm-4-flash', 'glm-4'],
    },
    'qwen': {
        'name': '通义千问',
        'api_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
        'models': ['qwen-max', 'qwen-plus', 'qwen-turbo'],
    },
}

# 疾病信息提取的 prompt 模板
DISEASE_PROMPT = """你是一个专业的医学影像学助手。请根据疾病名称"{disease_name}"，提供以下字段的详细信息。
请严格按照JSON格式返回，不要包含任何其他文字说明。字段说明：
- name_cn: 中文名
- name_en: 英文名
- system: 所属系统（头颈部/胸部/腹部/泌尿生殖/骨骼肌肉）
- category: 分类
- clinical: 临床表现（详细描述）
- diagnosis: 诊断要点
- primary_img: 主要影像检查方法
- secondary_img: 辅助影像检查方法
- xray_finding: X线所见
- ct_finding: CT所见
- mri_finding: MRI所见
- pet_finding: PET所见
- report_template: 影像报告模板
- differential_diagnosis: 鉴别诊断
- treatment: 治疗原则

请返回纯JSON，不要有markdown代码块标记：
"""


def load_config():
    """加载AI配置"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'provider': 'deepseek',
        'model': 'deepseek-chat',
        'api_key': '',
        'custom_api_url': '',
    }


def save_config(config):
    """保存AI配置"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def call_ai(disease_name, config=None):
    """调用大模型获取疾病信息，返回字段字典"""
    if config is None:
        config = load_config()

    api_key = config.get('api_key', '')
    if not api_key:
        raise ValueError('未配置API Key，请在AI配置中设置')

    provider = config.get('provider', 'deepseek')
    model = config.get('model', '')
    custom_url = config.get('custom_api_url', '')

    # 确定API URL
    if custom_url:
        api_url = custom_url
    elif provider in PROVIDERS:
        api_url = PROVIDERS[provider]['api_url']
    else:
        raise ValueError(f'未知的AI提供商: {provider}')

    # 构建请求
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }

    prompt = DISEASE_PROMPT.format(disease_name=disease_name)

    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': '你是一个专业的医学影像学助手，擅长提供疾病的影像学表现和诊断信息。请始终以纯JSON格式回复，不要包含markdown代码块标记。'},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.3,
        'max_tokens': 4000,
    }

    resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()

    data = resp.json()
    content = data['choices'][0]['message']['content'].strip()

    # 清理可能的markdown代码块标记
    if content.startswith('```'):
        lines = content.split('\n')
        content = '\n'.join(lines[1:])
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()

    result = json.loads(content)
    return result
