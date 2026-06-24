"""AI 大模型配置和调用模块"""
import json
import os
import re
import hashlib
import hmac
import datetime
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_config.json')

# 支持的大模型提供商
PROVIDERS = {
    'deepseek': {
        'name': 'DeepSeek',
        'api_url': 'https://api.deepseek.com/v1/chat/completions',
        'api_type': 'chat_completions',
        'models': ['deepseek-chat', 'deepseek-reasoner'],
    },
    'doubao': {
        'name': '豆包(火山引擎)',
        'api_url': 'https://ark.cn-beijing.volces.com/api/v3/responses',
        'api_type': 'responses',
        'models': [
            'doubao-seed-2-0-pro-260215', 'doubao-seed-2-0-lite-260215',
            'doubao-seed-2-0-mini-260215', 'doubao-seed-2-0-code-preview-260215',
            'doubao-seed-character',
            'doubao-seed-1-6-250715', 'doubao-seed-1-6-lite-250715',
            'doubao-seed-1-6-flash-250715',
            'doubao-1-5-pro-32k', 'doubao-1-5-lite-32k',
        ],
        'note': '也可填入火山方舟的Endpoint ID（如 ep-xxxxxxxx）',
    },
    'openai': {
        'name': 'OpenAI',
        'api_url': 'https://api.openai.com/v1/chat/completions',
        'api_type': 'chat_completions',
        'models': ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'],
    },
    'zhipu': {
        'name': '智谱AI',
        'api_url': 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
        'api_type': 'chat_completions',
        'models': ['glm-4-plus', 'glm-4-flash', 'glm-4'],
    },
    'qwen': {
        'name': '通义千问',
        'api_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
        'api_type': 'chat_completions',
        'models': ['qwen-max', 'qwen-plus', 'qwen-turbo'],
    },
}

# 知识库提供商
KNOWLEDGE_PROVIDERS = {
    'tencent': {
        'name': '腾讯IMA知识库',
        'api_url': 'https://ima.qq.com/openapi',
        'description': '腾讯IMA个人知识库(OpenAPI)',
    },
    'volcengine': {
        'name': '火山方舟知识库',
        'api_url': 'https://api-knowledgebase.mlp.cn-beijing.volces.com/api/knowledge/collection/search_knowledge',
        'description': '火山引擎方舟知识库服务',
    },
    'notebooklm': {
        'name': 'Google NotebookLM',
        'api_url': 'https://generativelanguage.googleapis.com/v1beta',
        'description': 'Google Gemini File Search 知识库',
    },
}

# 医学影像诊断知识库检索提示词
KB_QUERY_TEMPLATE = """检查类型：{exam_type}
关键征象：{keywords}
疑似疾病：{diseases}

请从知识库中检索以下内容：
1. 上述疾病的影像学表现和诊断标准
2. 鉴别诊断要点
3. 相关病理生理特征
4. 临床治疗方案
5. 标准影像报告模板"""

# 影像诊断查询 prompt
DIAGNOSIS_PROMPT = """你是一个资深医学影像诊断专家。根据以下信息，给出最有可能的3-5条影像诊断。

检查类型：{exam_type}
关键征象/关键字：{keywords}

请严格按照以下JSON格式返回，不要包含任何其他文字说明：
[
  {{
    "disease_name": "疾病名称",
    "confidence": "高/中/低",
    "imaging_findings": "影像学表现（详细描述该疾病在此检查类型下的典型影像表现）",
    "report_template": "标准报告模板（完整的影像诊断报告格式）",
    "differential_diagnosis": "鉴别诊断（需鉴别的疾病及鉴别要点）",
    "clinical_manifestation": "临床表现（症状、体征等）",
    "pathophysiology": "病理生理及症状学特征",
    "treatment": "临床治疗方法"
  }}
]

请返回纯JSON数组，不要有markdown代码块标记：
"""

# 知识库查询 prompt
KB_DIAGNOSIS_PROMPT = """你是一个资深医学影像诊断专家，请结合知识库中的信息，根据以下检查类型和关键征象给出最有可能的3-5条影像诊断。

检查类型：{exam_type}
关键征象/关键字：{keywords}

请严格按照以下JSON格式返回，不要包含任何其他文字说明：
[
  {{
    "disease_name": "疾病名称",
    "confidence": "高/中/低",
    "imaging_findings": "影像学表现",
    "report_template": "标准报告模板",
    "differential_diagnosis": "鉴别诊断",
    "clinical_manifestation": "临床表现",
    "pathophysiology": "病理生理及症状学特征",
    "treatment": "临床治疗方法"
  }}
]

请返回纯JSON数组，不要有markdown代码块标记：
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


def load_multi_config():
    """加载多模型配置（支持配置多个API）"""
    config = load_config()
    # 兼容旧配置格式
    providers = config.get('providers', [])
    if not providers:
        # 从单配置迁移
        single = {
            'provider': config.get('provider', 'deepseek'),
            'model': config.get('model', 'deepseek-chat'),
            'api_key': config.get('api_key', ''),
            'custom_api_url': config.get('custom_api_url', ''),
            'enabled': bool(config.get('api_key', '')),
        }
        providers = [single]
    return providers


def save_config(config):
    """保存AI配置"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def test_llm_connection(provider, model, api_key, custom_url='', timeout=15):
    """测试LLM联通性

    Args:
        provider: 提供商ID (deepseek/doubao/qwen/...)
        model: 模型名称
        api_key: API密钥
        custom_url: 自定义API URL
        timeout: 超时秒数

    Returns:
        dict: {'success': bool, 'message': str}
    """
    if not api_key:
        return {'success': False, 'message': 'API Key 为空'}

    if custom_url:
        api_url = custom_url
        api_type = 'chat_completions'
    elif provider in PROVIDERS:
        api_url = PROVIDERS[provider]['api_url']
        api_type = PROVIDERS[provider].get('api_type', 'chat_completions')
    else:
        return {'success': False, 'message': f'未知提供商: {provider}'}

    try:
        messages = [
            {'role': 'user', 'content': '请回复"连接成功"四个字'}
        ]
        reply = _call_llm(api_url, api_key, model, messages, api_type=api_type, timeout=timeout)
        if reply and len(reply) > 0:
            return {'success': True, 'message': f'连接成功，模型回复: {reply[:50]}'}
        else:
            return {'success': False, 'message': '连接成功但返回为空'}
    except requests.exceptions.Timeout:
        return {'success': False, 'message': '连接超时，请检查网络或API地址'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'message': '无法连接服务器，请检查网络或API地址'}
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else '未知'
        error_text = ''
        try:
            error_data = e.response.json()
            error_text = error_data.get('error', {}).get('message', '') or str(error_data)[:100]
        except Exception:
            error_text = e.response.text[:100] if e.response else ''
        return {'success': False, 'message': f'HTTP {status_code}: {error_text}'}
    except Exception as e:
        return {'success': False, 'message': f'错误: {str(e)}'}


def test_kb_connection(kb_config, timeout=15):
    """测试知识库联通性

    Args:
        kb_config: 知识库配置 {'type': ..., 'api_key': ..., ...}
        timeout: 超时秒数

    Returns:
        dict: {'success': bool, 'message': str}
    """
    kb_type = kb_config.get('type', 'tencent')
    api_key = kb_config.get('api_key', '')

    # 火山方舟可能使用AK/SK而非API Key
    if kb_type == 'volcengine':
        access_key = kb_config.get('access_key', '') or kb_config.get('ak', '')
        secret_key = kb_config.get('secret_key', '') or kb_config.get('sk', '')
        if not api_key and not (access_key and secret_key):
            return {'success': False, 'message': 'API Key 或 Access Key/Secret Key 为空'}
    elif not api_key:
        return {'success': False, 'message': 'API Key 为空'}

    kb_name = KNOWLEDGE_PROVIDERS.get(kb_type, {}).get('name', kb_type)

    try:
        if kb_type == 'tencent':
            # 腾讯IMA：使用搜索笔记测试联通性
            client_id = kb_config.get('api_key', '')
            api_key_secret = kb_config.get('secret_key', '')
            if not client_id or not api_key_secret:
                return {'success': False, 'message': 'IMA Client ID 和 API Key 均不能为空'}

            try:
                context, docs = _query_tencent_kb(kb_config, '测试', '影像诊断测试')
                return {'success': True, 'message': f'{kb_name}连接成功，返回{len(docs)}条笔记'}
            except Exception as e:
                return {'success': False, 'message': f'{kb_name}错误: {str(e)}'}

        elif kb_type == 'volcengine':
            # 火山方舟：使用 search_knowledge 或 Responses API 测试
            try:
                context, docs = _query_volcengine_kb(kb_config, '测试', '影像诊断测试')
                return {'success': True, 'message': f'{kb_name}连接成功，返回{len(docs)}条文档'}
            except Exception as e:
                return {'success': False, 'message': f'{kb_name}错误: {str(e)}'}

        elif kb_type == 'notebooklm':
            # Gemini File Search：使用 generateContent 测试
            api_url = kb_config.get('api_url', KNOWLEDGE_PROVIDERS['notebooklm']['api_url'])
            headers = {
                'Content-Type': 'application/json',
                'x-goog-api-key': api_key,
            }
            payload = {
                'contents': [{'role': 'user', 'parts': [{'text': 'Hello'}]}],
                'tools': [{'google_search': {}}],
                'generationConfig': {'temperature': 0.2},
            }
            endpoint = f'{api_url}/models/gemini-2.5-flash:generateContent'
            resp = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get('candidates', [])
            return {'success': True, 'message': f'{kb_name}连接成功，返回{len(candidates)}个候选结果'}

        else:
            return {'success': False, 'message': f'未知知识库类型: {kb_type}'}

    except requests.exceptions.Timeout:
        return {'success': False, 'message': f'{kb_name}连接超时，请检查网络'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'message': f'{kb_name}无法连接服务器，请检查网络'}
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else '未知'
        error_text = ''
        try:
            error_data = e.response.json()
            error_text = error_data.get('error', {}).get('message', '') or str(error_data)[:100]
        except Exception:
            error_text = e.response.text[:100] if e.response else ''
        return {'success': False, 'message': f'{kb_name} HTTP {status_code}: {error_text}'}
    except Exception as e:
        return {'success': False, 'message': f'{kb_name}错误: {str(e)}'}


def _call_llm(api_url, api_key, model, messages, api_type='chat_completions', timeout=90):
    """调用单个LLM API，返回原始文本

    Args:
        api_url: API地址
        api_key: API密钥
        model: 模型名称
        messages: 消息列表 [{'role': 'system'|'user'|'assistant', 'content': str}, ...]
        api_type: API类型 - 'chat_completions' (OpenAI兼容) 或 'responses' (豆包Responses API)
        timeout: 超时秒数
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }

    if api_type == 'responses':
        # 豆包 Responses API 格式
        # 将 messages 转换为 input 格式
        input_items = []
        for msg in messages:
            if msg['role'] == 'system':
                # system 消息作为 instructions 参数
                continue
            content_parts = []
            if isinstance(msg['content'], str):
                content_parts.append({
                    'type': 'input_text',
                    'text': msg['content'],
                })
            else:
                content_parts = msg['content']
            input_items.append({
                'role': msg['role'],
                'content': content_parts,
            })

        # 提取 system 消息作为 instructions
        instructions = ''
        for msg in messages:
            if msg['role'] == 'system':
                instructions = msg['content']
                break

        payload = {
            'model': model,
            'input': input_items,
        }
        if instructions:
            payload['instructions'] = instructions
    else:
        # OpenAI Chat Completions 兼容格式
        payload = {
            'model': model,
            'messages': messages,
            'temperature': 0.3,
            'max_tokens': 4000,
        }

    resp = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    if api_type == 'responses':
        # 豆包 Responses API 返回格式
        # 响应结构: {"output": [...{"type": "message", "content": [...{"type": "output_text", "text": "..."}]}]}
        output_list = data.get('output', [])
        text_parts = []
        for item in output_list:
            if item.get('type') == 'message':
                for c in item.get('content', []):
                    if c.get('type') == 'output_text':
                        text_parts.append(c.get('text', ''))
        return '\n'.join(text_parts).strip()
    else:
        return data['choices'][0]['message']['content'].strip()


def _parse_json_response(content):
    """解析LLM返回的JSON，清理markdown标记"""
    if content.startswith('```'):
        lines = content.split('\n')
        content = '\n'.join(lines[1:])
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
    return json.loads(content)


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

    if custom_url:
        api_url = custom_url
        api_type = 'chat_completions'
    elif provider in PROVIDERS:
        api_url = PROVIDERS[provider]['api_url']
        api_type = PROVIDERS[provider].get('api_type', 'chat_completions')
    else:
        raise ValueError(f'未知的AI提供商: {provider}')

    prompt = DISEASE_PROMPT.format(disease_name=disease_name)
    messages = [
        {'role': 'system', 'content': '你是一个专业的医学影像学助手，擅长提供疾病的影像学表现和诊断信息。请始终以纯JSON格式回复，不要包含markdown代码块标记。'},
        {'role': 'user', 'content': prompt}
    ]
    content = _call_llm(api_url, api_key, model, messages, api_type=api_type)
    return _parse_json_response(content)


def _sanitize_disease_name(name):
    """清理疾病名，去除英文字母和括号内的内容，只保留中文名用于知识库检索

    例如："肺癌（adenocarcinoma）" → "肺癌"
          "COVID-19肺炎" → "肺炎"
          "肺结节(AAA)" → "肺结节"
    """
    # 去除括号及括号内的内容（中英文括号）
    cleaned = re.sub(r'[（(][^）)]*[）)]', '', name)
    # 去除英文字母和连字符
    cleaned = re.sub(r'[a-zA-Z\-]', '', cleaned)
    # 去除多余空格和首尾标点
    cleaned = re.sub(r'\s+', '', cleaned)
    cleaned = cleaned.strip(' ··--—–')
    # 如果清理后为空，回退到原始名称
    return cleaned if cleaned else name


def call_diagnosis_multi(exam_type, keywords, selected_providers=None, use_knowledge_base=None):
    """并行调用多个大模型获取影像诊断结果

    流程：
    1. 若选择大模型：并行调用各LLM获取诊断结果（不使用知识库）
       从所有成功结果中提取匹配度最高的1-3个疾病名
       对每个疾病【分别】查询知识库，获取文档快照
    2. 若未选择大模型但配置了知识库：直接用关键字查询知识库

    Args:
        exam_type: 检查类型 (CT/X-Ray/MRI/PET-CT)
        keywords: 关键字
        selected_providers: 选中的提供商配置列表（可为空，为空时直接检索知识库）
        use_knowledge_base: 知识库配置

    Returns:
        dict: {provider_name: {'success': bool, 'data': [...], 'error': str}}
              特殊键 '_kb_groups': [{'disease': str, 'docs': [...], 'error': str}, ...]  按疾病分别检索的知识库结果
              特殊键 '_kb_error': str  整体知识库错误信息（若有）
    """
    if not selected_providers:
        providers = load_multi_config()
        selected_providers = [p for p in providers if p.get('enabled') and p.get('api_key')]

    results = {}

    # ===== 直接知识库检索模式（未选择大模型）=====
    if not selected_providers:
        if not (use_knowledge_base and use_knowledge_base.get('api_key')):
            raise ValueError('没有可用的AI配置，请先选择大模型或配置知识库')
        kb_groups = []
        overall_kb_error = ''
        try:
            kb_query = KB_QUERY_TEMPLATE.format(
                exam_type=exam_type,
                keywords=keywords,
                diseases=keywords
            )
            kb_context, kb_docs = _query_knowledge_base(
                use_knowledge_base, exam_type, kb_query
            )
            kb_groups.append({'disease': keywords, 'docs': kb_docs, 'error': ''})
        except Exception as e:
            overall_kb_error = str(e)
            kb_groups.append({'disease': keywords, 'docs': [], 'error': overall_kb_error})
        results['_kb_groups'] = kb_groups
        results['_kb_error'] = overall_kb_error
        return results

    def _query_one(provider_config):
        """查询单个大模型（第一阶段：不使用知识库）"""
        name = PROVIDERS.get(provider_config['provider'], {}).get('name', provider_config['provider'])
        try:
            api_key = provider_config.get('api_key', '')
            model = provider_config.get('model', '')
            custom_url = provider_config.get('custom_api_url', '')

            if custom_url:
                api_url = custom_url
                api_type = 'chat_completions'
            elif provider_config['provider'] in PROVIDERS:
                api_url = PROVIDERS[provider_config['provider']]['api_url']
                api_type = PROVIDERS[provider_config['provider']].get('api_type', 'chat_completions')
            else:
                return name, {'success': False, 'data': [], 'error': f'未知提供商: {provider_config["provider"]}', 'kb_docs': []}

            prompt = DIAGNOSIS_PROMPT.format(exam_type=exam_type, keywords=keywords)
            messages = [
                {'role': 'system', 'content': '你是一个资深医学影像诊断专家。请始终以纯JSON数组格式回复，不要包含markdown代码块标记。'},
                {'role': 'user', 'content': prompt}
            ]
            content = _call_llm(api_url, api_key, model, messages, api_type=api_type)
            data = _parse_json_response(content)
            if isinstance(data, dict):
                data = [data]
            return name, {'success': True, 'data': data, 'error': '', 'kb_docs': []}
        except Exception as e:
            return name, {'success': False, 'data': [], 'error': str(e), 'kb_docs': []}

    # 第一阶段：并行调用LLM获取诊断结果
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(_query_one, pc): pc for pc in selected_providers}
        for future in as_completed(futures):
            try:
                name, result = future.result()
                results[name] = result
            except Exception as e:
                pc = futures[future]
                name = PROVIDERS.get(pc['provider'], {}).get('name', pc['provider'])
                results[name] = {'success': False, 'data': [], 'error': str(e), 'kb_docs': []}

    # 第二阶段：对top 1-3疾病【分别】查询知识库
    if use_knowledge_base and use_knowledge_base.get('api_key'):
        # 收集所有成功结果中的疾病名（按置信度排序取前3）
        disease_entries = []
        for result in results.values():
            if isinstance(result, dict) and result.get('success') and result.get('data'):
                for item in result['data']:
                    disease_name = item.get('disease_name', '')
                    confidence = item.get('confidence', '')
                    if disease_name:
                        disease_entries.append((disease_name, confidence))

        # 按置信度排序：高 > 中 > 低
        conf_order = {'高': 0, '中': 1, '低': 2}
        disease_entries.sort(key=lambda x: conf_order.get(x[1], 3))

        # 去重取前3个疾病名（清理英文字母和括号等特殊字符，只用中文名检索）
        seen_names = set()
        top_diseases = []
        for name, _ in disease_entries:
            clean_name = _sanitize_disease_name(name)
            if clean_name and clean_name not in seen_names:
                seen_names.add(clean_name)
                top_diseases.append(clean_name)
            if len(top_diseases) >= 3:
                break

        # 对每个疾病分别查询知识库
        kb_groups = []
        overall_kb_error = ''
        for disease_name in top_diseases:
            kb_query = KB_QUERY_TEMPLATE.format(
                exam_type=exam_type,
                keywords=keywords,
                diseases=disease_name
            )
            try:
                kb_context, kb_docs = _query_knowledge_base(
                    use_knowledge_base, exam_type, kb_query
                )
                kb_groups.append({'disease': disease_name, 'docs': kb_docs, 'error': ''})
            except Exception as e:
                err_msg = str(e)
                kb_groups.append({'disease': disease_name, 'docs': [], 'error': err_msg})
                if not overall_kb_error:
                    overall_kb_error = err_msg

        results['_kb_groups'] = kb_groups
        results['_kb_error'] = overall_kb_error

    return results


def _query_knowledge_base(kb_config, exam_type, keywords):
    """查询知识库获取参考信息，返回 (上下文文本, 文档快照列表)

    异常会向上抛出，由调用方捕获处理。

    Returns:
        tuple: (context_str, doc_snapshots)
    """
    kb_type = kb_config.get('type', 'tencent')
    api_key = kb_config.get('api_key', '')

    if not api_key:
        raise ValueError('知识库 API Key 为空')

    if kb_type == 'tencent':
        return _query_tencent_kb(kb_config, exam_type, keywords)
    elif kb_type == 'volcengine':
        return _query_volcengine_kb(kb_config, exam_type, keywords)
    elif kb_type == 'notebooklm':
        return _query_notebooklm_kb(kb_config, exam_type, keywords)
    else:
        raise ValueError(f'未知知识库类型: {kb_type}')


def _volc_sign_request(method, path, ak, sk, body, host, service='air', region='cn-beijing'):
    """生成火山引擎 HMAC-SHA256 签名请求头

    火山方舟知识库 search_knowledge API 要求 HMAC-SHA256 签名认证，
    不能使用 Bearer Token。此函数实现 SignerV4 签名算法。

    Args:
        method: HTTP方法 (POST/GET)
        path: API路径 (如 /api/knowledge/collection/search_knowledge)
        ak: Access Key ID
        sk: Secret Access Key
        body: 请求体字符串 (JSON)
        host: API主机名
        service: 服务名 (知识库为 'air')
        region: 区域 (中国区为 'cn-beijing')

    Returns:
        dict: 包含签名信息的完整请求头
    """
    now = datetime.datetime.utcnow()
    x_date = now.strftime('%Y%m%dT%H%M%SZ')
    short_date = now.strftime('%Y%m%d')

    # 计算请求体哈希
    body_bytes = body.encode('utf-8') if isinstance(body, str) else body
    payload_hash = hashlib.sha256(body_bytes).hexdigest()

    # 规范化请求头
    content_type = 'application/json'
    canonical_headers = (
        f'content-type:{content_type}\n'
        f'host:{host}\n'
        f'x-content-sha256:{payload_hash}\n'
        f'x-date:{x_date}\n'
    )
    signed_headers = 'content-type;host;x-content-sha256;x-date'

    # 构建规范化请求
    canonical_request = (
        f'{method}\n{path}\n\n{canonical_headers}\n{signed_headers}\n{payload_hash}'
    )

    # 签名范围
    credential_scope = f'{short_date}/{region}/{service}/request'

    # 待签名字符串
    hashed_canonical_request = hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
    string_to_sign = (
        f'HMAC-SHA256\n{x_date}\n{credential_scope}\n{hashed_canonical_request}'
    )

    # 派生签名密钥: VOLC+SK → date → region → service → request
    k_date = hmac.new(('VOLC' + sk).encode('utf-8'), short_date.encode('utf-8'), hashlib.sha256).digest()
    k_region = hmac.new(k_date, region.encode('utf-8'), hashlib.sha256).digest()
    k_service = hmac.new(k_region, service.encode('utf-8'), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, b'request', hashlib.sha256).digest()

    # 计算签名
    signature = hmac.new(k_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

    # 构建Authorization头
    authorization = (
        f'HMAC-SHA256 Credential={ak}/{credential_scope}, '
        f'SignedHeaders={signed_headers}, Signature={signature}'
    )

    return {
        'Content-Type': content_type,
        'Host': host,
        'X-Content-Sha256': payload_hash,
        'X-Date': x_date,
        'Authorization': authorization,
    }


def _query_tencent_kb(kb_config, exam_type, keywords):
    """查询腾讯IMA个人知识库，返回 (上下文文本, 文档快照列表)

    使用 IMA OpenAPI 搜索笔记并获取内容。
    认证方式: ima-openapi-clientid + ima-openapi-apikey 请求头。

    多策略检索提高命中率：
    1. 按标题精确搜索疾病名
    2. 按正文搜索疾病名
    3. 按正文搜索"检查类型+疾病名"组合
    """
    api_url = kb_config.get('api_url', KNOWLEDGE_PROVIDERS['tencent']['api_url'])
    client_id = kb_config.get('api_key', '') or kb_config.get('client_id', '')
    api_key = kb_config.get('secret_key', '') or kb_config.get('api_key_secret', '')

    if not client_id or not api_key:
        raise ValueError('腾讯IMA需要 Client ID 和 API Key，请在知识库配置中填写')

    headers = {
        'Content-Type': 'application/json',
        'ima-openapi-clientid': client_id,
        'ima-openapi-apikey': api_key,
    }

    # 从关键词中提取搜索词（去掉模板前缀）
    search_query = keywords
    if '疑似疾病' in keywords:
        lines = keywords.split('\n')
        for line in lines:
            if '疑似疾病' in line:
                search_query = line.split('：', 1)[-1].strip() if '：' in line else line.split(':', 1)[-1].strip()
                break

    search_url = f'{api_url}/note/v1/search_note_book'

    def _ima_search(search_type, query_text, start=0, end=20):
        """执行IMA搜索，返回docs列表"""
        payload = {
            'search_type': search_type,
            'query_info': {'title': query_text} if search_type == 0 else {'content': query_text},
            'start': start,
            'end': end,
        }
        r = requests.post(search_url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        d = r.json()
        if d.get('error_code', 0) != 0:
            raise ValueError(f'IMA API错误 [{d.get("error_code")}]: {d.get("error_msg", "未知错误")}')
        return d.get('data', {}).get('docs', [])

    # 多策略搜索：标题 → 正文 → 组合查询
    docs = _ima_search(0, search_query)  # 策略1: 按标题搜索
    if not docs:
        docs = _ima_search(1, search_query)  # 策略2: 按正文搜索
    if not docs and exam_type:
        # 策略3: 用"检查类型+搜索词"组合搜索
        combo_query = f'{exam_type} {search_query}'
        docs = _ima_search(1, combo_query)
    if not docs:
        # 策略4: 提取搜索词中的核心词（去掉修饰语）
        core_words = re.sub(r'[的了吗呢吧]', '', search_query).strip()
        if core_words and core_words != search_query:
            docs = _ima_search(1, core_words)

    doc_snapshots = []
    context_parts = []

    # 获取每篇笔记的详细内容
    doc_url = f'{api_url}/note/v1/get_doc_content'
    for doc in docs[:8]:  # 增加到8篇
        doc_info = doc.get('doc', {}).get('basic_info', {})
        doc_id = doc_info.get('docid', '')
        title = doc_info.get('title', '未知文档')
        summary = doc_info.get('summary', '')

        if not doc_id:
            continue

        snippet = ''
        try:
            doc_payload = {'doc_id': doc_id, 'target_content_format': 1}  # Markdown格式
            doc_resp = requests.post(doc_url, headers=headers, json=doc_payload, timeout=15)
            doc_resp.raise_for_status()
            doc_data = doc_resp.json()

            if doc_data.get('error_code', 0) == 0:
                content = doc_data.get('data', {}).get('content', '')
                if content:
                    context_parts.append(f'【{title}】\n{content}')
                    snippet = content[:300] + ('...' if len(content) > 300 else '')
                elif summary:
                    context_parts.append(f'【{title}】\n{summary}')
                    snippet = summary[:300] + ('...' if len(summary) > 300 else '')
            elif summary:
                context_parts.append(f'【{title}】\n{summary}')
                snippet = summary[:300] + ('...' if len(summary) > 300 else '')
        except Exception:
            if summary:
                context_parts.append(f'【{title}】\n{summary}')
                snippet = summary[:300] + ('...' if len(summary) > 300 else '')

        if snippet:
            doc_snapshots.append({
                'doc_name': title,
                'page': '',
                'snippet': snippet,
                'url': f'ima://note/{doc_id}',
                'source': '腾讯IMA知识库',
            })

    context = '\n\n'.join(context_parts)
    if not context:
        raise ValueError(f'IMA知识库未找到与"{search_query}"相关的内容')

    return context, doc_snapshots


def _query_volcengine_kb(kb_config, exam_type, keywords):
    """查询火山方舟知识库，返回 (上下文文本, 文档快照列表)

    自动选择检索模式：
    1. search_knowledge API（需AK/SK + Resource ID或集合名称）— HMAC-SHA256签名认证，混合检索+重排序
    2. Responses API + knowledge_search 工具（需API Key + Endpoint ID）— Bearer认证，旗舰版知识库
    """
    api_key = kb_config.get('api_key', '')
    access_key = kb_config.get('access_key', '') or kb_config.get('ak', '')
    secret_key = kb_config.get('secret_key', '') or kb_config.get('sk', '')
    endpoint_id = kb_config.get('endpoint_id', '')
    collection_name = kb_config.get('collection_name', '')
    resource_id = kb_config.get('resource_id', '')

    # 判断可用模式
    can_search = bool(access_key and secret_key and (resource_id or collection_name))
    can_responses = bool(api_key and endpoint_id)

    if can_search:
        return _query_volcengine_search_kb(kb_config, exam_type, keywords)
    elif can_responses:
        return _query_volcengine_responses_kb(kb_config, exam_type, keywords)
    else:
        raise ValueError(
            '火山方舟知识库配置不完整。需要以下任一组合：\n'
            '1. search_knowledge模式：Access Key + Secret Key + (Resource ID 或 集合名称)\n'
            '2. Responses API模式：API Key + 旗舰版知识库ID(Endpoint ID)'
        )


def _query_volcengine_search_kb(kb_config, exam_type, keywords):
    """使用 search_knowledge API 查询火山方舟知识库（HMAC-SHA256签名认证）

    混合检索 + 重排序 + 上下文扩散，检索精度高。
    """
    access_key = kb_config.get('access_key', '') or kb_config.get('ak', '')
    secret_key = kb_config.get('secret_key', '') or kb_config.get('sk', '')
    collection_name = kb_config.get('collection_name', '')
    resource_id = kb_config.get('resource_id', '')

    host = 'api-knowledgebase.mlp.cn-beijing.volces.com'
    path = '/api/knowledge/collection/search_knowledge'
    url = f'https://{host}{path}'

    # 构建检索请求 - 优化参数提高命中率
    payload = {
        'query': keywords,
        'limit': 5,
        'query_param': {
            'dense_weight': 0.6,  # 偏向语义检索，适合医学术语匹配
        },
        'post_processing': {
            'rerank_switch': True,       # 开启重排序
            'retrieve_count': 25,        # 进入重排的候选数量
            'chunk_diffusion_count': 1,  # 返回上下文相邻切片
            'chunk_group': True,         # 文本聚合排序，保持语序
            'rerank_model': 'm3-v2-rerank',
            'rerank_only_chunk': False,  # 根据title+内容一起计算排序分
            'get_attachment_link': True,
        },
    }

    if resource_id:
        payload['resource_id'] = resource_id
    if collection_name:
        payload['name'] = collection_name
        payload['project'] = 'default'

    body = json.dumps(payload, ensure_ascii=False)

    # 生成HMAC-SHA256签名请求头
    headers = _volc_sign_request('POST', path, access_key, secret_key, body, host)

    resp = requests.post(url, headers=headers, data=body.encode('utf-8'), timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # 解析检索结果（响应格式: data.result_list）
    doc_snapshots = []
    context_parts = []

    result_list = data.get('data', {}).get('result_list', [])
    if not result_list:
        result_list = data.get('result_list', []) or data.get('chunks', []) or data.get('documents', [])

    for c in result_list:
        content = c.get('content', '') or c.get('text', '') or c.get('chunk_content', '')
        if not content:
            continue
        context_parts.append(content)

        doc_name = (c.get('chunk_title', '') or c.get('doc_name', '') or
                    c.get('title', '') or c.get('filename', '') or '未知文档')
        page = str(c.get('chunk_id', '') or c.get('page', '') or c.get('page_num', ''))
        doc_url = c.get('attachment_link', '') or c.get('url', '') or c.get('doc_url', '')
        snippet = content[:300] + ('...' if len(content) > 300 else '')

        doc_snapshots.append({
            'doc_name': doc_name,
            'page': page,
            'snippet': snippet,
            'url': doc_url,
            'source': '火山方舟知识库',
        })

    context = '\n'.join(context_parts)
    if not context:
        raise ValueError(f'火山方舟知识库返回空结果，原始响应: {json.dumps(data, ensure_ascii=False)[:300]}')

    return context, doc_snapshots


def _query_volcengine_responses_kb(kb_config, exam_type, keywords):
    """使用火山方舟 Responses API + knowledge_search 工具查询知识库

    适用于旗舰版知识库，通过 endpoint_id (knowledge_resource_id) 调用。
    """
    api_key = kb_config.get('api_key', '')
    endpoint_id = kb_config.get('endpoint_id', '')

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
        'ark-beta-knowledge-search': 'true',
    }

    payload = {
        'model': 'doubao-seed-1-6-251015',
        'stream': False,
        'thinking': {'type': 'disabled'},
        'tools': [
            {
                'type': 'knowledge_search',
                'knowledge_resource_id': endpoint_id,
                'limit': 5,
                'ranking_options': {
                    'get_attachment_link': True,
                },
            }
        ],
        'input': [
            {
                'role': 'user',
                'content': [{'type': 'input_text', 'text': keywords}]
            }
        ],
        'max_tool_calls': 1,
    }

    url = 'https://ark.cn-beijing.volces.com/api/v3/responses'
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    doc_snapshots = []
    context_parts = []

    # 从 output 中提取文本
    output_list = data.get('output', [])
    for item in output_list:
        if item.get('type') == 'message':
            for c in item.get('content', []):
                if c.get('type') == 'output_text':
                    context_parts.append(c.get('text', ''))
        # 从 tool_call 结果中提取检索到的文档
        if item.get('type') == 'tool_call':
            for c in item.get('content', []):
                if c.get('type') == 'knowledge_search_result':
                    results = c.get('results', [])
                    for r in results:
                        doc_name = r.get('title', '') or r.get('doc_name', '未知文档')
                        content = r.get('content', '') or r.get('text', '')
                        url = r.get('url', '') or r.get('attachment_link', '')
                        snippet = content[:200] + ('...' if len(content) > 200 else '') if content else ''
                        if content:
                            context_parts.append(content)
                        doc_snapshots.append({
                            'doc_name': doc_name,
                            'page': '',
                            'snippet': snippet,
                            'url': url,
                            'source': '火山方舟知识库',
                        })

    context = '\n'.join(context_parts)
    if not context:
        raise ValueError(f'火山方舟知识库(Responses API)返回空结果，原始响应: {json.dumps(data, ensure_ascii=False)[:200]}')

    return context, doc_snapshots


def _query_notebooklm_kb(kb_config, exam_type, keywords):
    """查询 Google Gemini File Search 知识库，返回 (上下文文本, 文档快照列表)

    使用 Gemini API 的 fileSearch 工具进行检索。
    支持两种模式：
    1. 有 file_search_store：使用 File Search Store 检索自有文档
    2. 无 file_search_store：使用 Google Search grounding 检索网络信息
    """
    api_url = kb_config.get('api_url', KNOWLEDGE_PROVIDERS['notebooklm']['api_url'])
    api_key = kb_config.get('api_key', '')
    # 兼容旧配置：corpus_id -> file_search_store
    file_search_store = kb_config.get('file_search_store', '') or kb_config.get('corpus_id', '')

    if not api_key:
        raise ValueError('Gemini API Key 为空')

    # 使用 x-goog-api-key 头认证（Google 官方推荐方式）
    headers = {
        'Content-Type': 'application/json',
        'x-goog-api-key': api_key,
    }

    # 构建医学专用检索提示词
    query_text = f'作为医学影像诊断专家，请根据知识库检索以下问题：\n{keywords}'

    # 使用 gemini-2.5-flash 模型（性价比最佳，支持 File Search）
    model = 'gemini-2.5-flash'

    payload = {
        'contents': [
            {
                'role': 'user',
                'parts': [{'text': query_text}]
            }
        ],
        'generationConfig': {
            'temperature': 0.2,  # 事实性查询使用低温度
        },
    }

    if file_search_store:
        # 模式1：使用 File Search Store 检索自有文档
        store_name = file_search_store
        if not store_name.startswith('fileSearchStores/'):
            store_name = f'fileSearchStores/{file_search_store}'
        payload['tools'] = [
            {
                'fileSearch': {
                    'fileSearchStores': [store_name]
                }
            }
        ]
    else:
        # 模式2：使用 Google Search grounding 检索网络
        payload['tools'] = [{'google_search': {}}]

    endpoint = f'{api_url}/models/{model}:generateContent'

    resp = requests.post(endpoint, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    doc_snapshots = []
    context_parts = []

    candidates = data.get('candidates', [])
    for candidate in candidates:
        content = candidate.get('content', {})
        parts = content.get('parts', [])
        for part in parts:
            text = part.get('text', '')
            if text:
                context_parts.append(text)

    # 提取 grounding metadata（引用来源）
    for candidate in candidates:
        grounding_meta = candidate.get('groundingMetadata', {})

        # 从 grounding chunks 提取引用
        chunks = grounding_meta.get('groundingChunks', [])
        for chunk in chunks:
            # Web 引用 (Google Search)
            web_ref = chunk.get('web', {})
            if web_ref:
                doc_name = web_ref.get('title', '') or web_ref.get('uri', 'Web引用')
                url = web_ref.get('uri', '')
                doc_snapshots.append({
                    'doc_name': doc_name,
                    'page': '',
                    'snippet': '',
                    'url': url,
                    'source': 'Google NotebookLM',
                })
            # File Search 引用
            file_ref = chunk.get('retrievedContext', {}) or chunk.get('fileSearch', {})
            if file_ref:
                doc_name = file_ref.get('title', '') or file_ref.get('displayName', '') or file_ref.get('uri', '文档引用')
                url = file_ref.get('uri', '')
                snippet = file_ref.get('text', '')[:200] + ('...' if len(file_ref.get('text', '')) > 200 else '') if file_ref.get('text') else ''
                doc_snapshots.append({
                    'doc_name': doc_name,
                    'page': '',
                    'snippet': snippet,
                    'url': url,
                    'source': 'Google NotebookLM',
                })

        # 从 grounding supports 提取更精确的引用片段
        supports = grounding_meta.get('groundingSupports', [])
        for support in supports:
            chunk_refs = support.get('groundingChunkIndices', [])
            for idx in chunk_refs:
                if idx < len(doc_snapshots):
                    text_seg = support.get('segment', {}).get('text', '')
                    if text_seg and not doc_snapshots[idx].get('snippet'):
                        doc_snapshots[idx]['snippet'] = text_seg[:200] + ('...' if len(text_seg) > 200 else '')

    context = '\n'.join(context_parts)
    if not context:
        raise ValueError(f'Gemini File Search 返回空结果，原始响应: {json.dumps(data, ensure_ascii=False)[:200]}')

    # 如果没有提取到引用，但上下文非空，创建通用快照
    if not doc_snapshots and context:
        doc_snapshots.append({
            'doc_name': 'Gemini 查询结果',
            'page': '',
            'snippet': context[:200] + ('...' if len(context) > 200 else ''),
            'url': '',
            'source': 'Google NotebookLM',
        })

    return context, doc_snapshots
