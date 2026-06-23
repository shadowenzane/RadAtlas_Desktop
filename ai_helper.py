"""AI 大模型配置和调用模块"""
import json
import os
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
        'name': '腾讯知识库',
        'api_url': 'https://lke.cloud.tencent.com/v1/knowledge/query',
        'description': '腾讯云大模型知识引擎',
    },
    'volcengine': {
        'name': '火山方舟知识库',
        'api_url': 'https://ark.cn-beijing.volces.com/api/v3/knowledge/query',
        'description': '火山引擎方舟知识库服务',
    },
    'notebooklm': {
        'name': 'Google NotebookLM',
        'api_url': 'https://generativelanguage.googleapis.com/v1beta',
        'description': 'Google NotebookLM 知识库（基于 Gemini API）',
    },
}

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

    if not api_key:
        return {'success': False, 'message': 'API Key 为空'}

    kb_name = KNOWLEDGE_PROVIDERS.get(kb_type, {}).get('name', kb_type)

    try:
        if kb_type == 'tencent':
            bot_id = kb_config.get('bot_id', '')
            if not bot_id:
                return {'success': False, 'message': '腾讯知识库 BotId 为空'}
            api_url = kb_config.get('api_url', KNOWLEDGE_PROVIDERS['tencent']['api_url'])
            headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'}
            payload = {'BotId': bot_id, 'Query': '测试', 'TopK': 1}
            resp = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            records = data.get('Records', [])
            return {'success': True, 'message': f'{kb_name}连接成功，返回{len(records)}条记录'}

        elif kb_type == 'volcengine':
            endpoint_id = kb_config.get('endpoint_id', '')
            if not endpoint_id:
                return {'success': False, 'message': '火山方舟 EndpointId 为空'}
            api_url = kb_config.get('api_url', KNOWLEDGE_PROVIDERS['volcengine']['api_url'])
            headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'}
            payload = {
                'model': endpoint_id,
                'messages': [{'role': 'user', 'content': '测试'}],
            }
            collection_name = kb_config.get('collection_name', '')
            if collection_name:
                payload['knowledge'] = {'collection_name': collection_name}
            resp = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            return {'success': True, 'message': f'{kb_name}连接成功，返回内容: {content[:50]}'}

        elif kb_type == 'notebooklm':
            api_url = kb_config.get('api_url', KNOWLEDGE_PROVIDERS['notebooklm']['api_url'])
            corpus_id = kb_config.get('corpus_id', '')
            headers = {'Content-Type': 'application/json'}
            payload = {
                'contents': [{'parts': [{'text': 'Hello'}]}],
            }
            if corpus_id:
                payload['tools'] = [{'retrieval': {'source': {'corpus': f'corpora/{corpus_id}'}}}]
            else:
                payload['tools'] = [{'google_search': {}}]
            endpoint = f'{api_url}/models/gemini-2.0-flash:generateContent?key={api_key}'
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


def call_diagnosis_multi(exam_type, keywords, selected_providers=None, use_knowledge_base=None):
    """并行调用多个大模型获取影像诊断结果

    流程：
    1. 并行调用各LLM获取诊断结果（不使用知识库）
    2. 从所有成功结果中提取匹配度最高的1-3个疾病名
    3. 用这些疾病名查询知识库，获取文档快照
    4. 将知识库文档附加到结果中

    Args:
        exam_type: 检查类型 (CT/X-Ray/MRI/PET-CT)
        keywords: 关键字
        selected_providers: 选中的提供商配置列表
        use_knowledge_base: 知识库配置

    Returns:
        dict: {provider_name: {'success': bool, 'data': [...], 'error': str, 'kb_docs': [...]}}
    """
    if not selected_providers:
        providers = load_multi_config()
        selected_providers = [p for p in providers if p.get('enabled') and p.get('api_key')]

    if not selected_providers:
        raise ValueError('没有可用的AI配置，请先在AI配置中设置API Key')

    results = {}

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

    # 第二阶段：从成功结果中提取top 1-3疾病名，查询知识库
    if use_knowledge_base and use_knowledge_base.get('api_key'):
        # 收集所有成功结果中的疾病名（按置信度排序取前3）
        disease_entries = []
        for result in results.values():
            if result.get('success') and result.get('data'):
                for item in result['data']:
                    disease_name = item.get('disease_name', '')
                    confidence = item.get('confidence', '')
                    if disease_name:
                        disease_entries.append((disease_name, confidence))

        # 按置信度排序：高 > 中 > 低
        conf_order = {'高': 0, '中': 1, '低': 2}
        disease_entries.sort(key=lambda x: conf_order.get(x[1], 3))

        # 去重取前3个疾病名
        seen_names = set()
        top_diseases = []
        for name, _ in disease_entries:
            if name not in seen_names:
                seen_names.add(name)
                top_diseases.append(name)
            if len(top_diseases) >= 3:
                break

        if top_diseases:
            # 用疾病名查询知识库
            kb_query = f'{exam_type} {keywords} ' + ' '.join(top_diseases)
            kb_error = ''
            kb_docs = []
            try:
                kb_context, kb_docs = _query_knowledge_base(
                    use_knowledge_base, exam_type, kb_query
                )
            except Exception as e:
                kb_error = str(e)

            # 将知识库文档或错误信息附加到所有成功的结果中
            for name, result in results.items():
                if result.get('success'):
                    if kb_docs:
                        result['kb_docs'] = kb_docs
                    if kb_error:
                        result['kb_error'] = kb_error

    return results


def _query_knowledge_base(kb_config, exam_type, keywords):
    """查询知识库获取参考信息，返回 (上下文文本, 文档快照列表)

    Returns:
        tuple: (context_str, doc_snapshots)
            context_str: 拼接的文本上下文，用于传给LLM
            doc_snapshots: 文档快照列表，每个元素为 dict:
                {'doc_name': str, 'page': str, 'snippet': str, 'url': str, 'source': str}
    """
    kb_type = kb_config.get('type', 'tencent')
    api_key = kb_config.get('api_key', '')

    if not api_key:
        return '', []

    try:
        if kb_type == 'tencent':
            return _query_tencent_kb(kb_config, exam_type, keywords)
        elif kb_type == 'volcengine':
            return _query_volcengine_kb(kb_config, exam_type, keywords)
        elif kb_type == 'notebooklm':
            return _query_notebooklm_kb(kb_config, exam_type, keywords)
    except Exception:
        return '', []
    return '', []


def _query_tencent_kb(kb_config, exam_type, keywords):
    """查询腾讯知识库，返回 (上下文文本, 文档快照列表)"""
    api_url = kb_config.get('api_url', KNOWLEDGE_PROVIDERS['tencent']['api_url'])
    api_key = kb_config.get('api_key', '')
    bot_id = kb_config.get('bot_id', '')  # 腾讯知识库应用ID

    if not bot_id:
        return '', []

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }
    payload = {
        'BotId': bot_id,
        'Query': f'{exam_type} {keywords}',
        'TopK': 5,
    }
    resp = requests.post(api_url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # 提取知识库返回的文本和文档快照信息
    records = data.get('Records', [])
    doc_snapshots = []
    context_parts = []

    for r in records:
        content = r.get('Content', '')
        if not content:
            continue
        context_parts.append(content)

        # 提取文档快照信息
        doc_name = r.get('DocName', '') or r.get('FileName', '') or r.get('Title', '未知文档')
        page = str(r.get('Page', '') or r.get('PageNum', '') or '')
        url = r.get('Url', '') or r.get('DocUrl', '') or r.get('ReferenceLink', '')
        snippet = content[:200] + ('...' if len(content) > 200 else '')

        doc_snapshots.append({
            'doc_name': doc_name,
            'page': page,
            'snippet': snippet,
            'url': url,
            'source': '腾讯知识库',
        })

    context = '\n'.join(context_parts) if context_parts else data.get('Answer', '')
    return context, doc_snapshots


def _query_volcengine_kb(kb_config, exam_type, keywords):
    """查询火山方舟知识库，返回 (上下文文本, 文档快照列表)"""
    api_url = kb_config.get('api_url', KNOWLEDGE_PROVIDERS['volcengine']['api_url'])
    api_key = kb_config.get('api_key', '')
    endpoint_id = kb_config.get('endpoint_id', '')  # 火山方舟推理接入点ID
    collection_name = kb_config.get('collection_name', '')  # 知识库集合名称

    if not endpoint_id:
        return '', []

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }
    payload = {
        'model': endpoint_id,
        'messages': [
            {'role': 'user', 'content': f'请根据知识库信息回答：{exam_type}检查中，{keywords}的影像诊断有哪些？'}
        ],
    }
    if collection_name:
        payload['knowledge'] = {'collection_name': collection_name}

    resp = requests.post(api_url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # 提取文档快照信息
    doc_snapshots = []
    context = data.get('choices', [{}])[0].get('message', {}).get('content', '')

    # 火山方舟知识库返回的引用信息
    citations = data.get('choices', [{}])[0].get('metadata', {}).get('citations', [])
    if not citations:
        # 尝试从其他字段提取引用
        citations = data.get('citations', []) or data.get('references', [])

    for c in citations:
        doc_name = c.get('doc_name', '') or c.get('title', '') or c.get('filename', '未知文档')
        page = str(c.get('page', '') or c.get('page_num', '') or '')
        url = c.get('url', '') or c.get('doc_url', '') or c.get('reference_link', '')
        snippet = c.get('content', '') or c.get('snippet', '') or c.get('text', '')
        if snippet:
            snippet = snippet[:200] + ('...' if len(snippet) > 200 else '')

        doc_snapshots.append({
            'doc_name': doc_name,
            'page': page,
            'snippet': snippet,
            'url': url,
            'source': '火山方舟知识库',
        })

    # 如果没有提取到引用信息，但上下文非空，创建一个通用快照
    if not doc_snapshots and context:
        doc_snapshots.append({
            'doc_name': '知识库查询结果',
            'page': '',
            'snippet': context[:200] + ('...' if len(context) > 200 else ''),
            'url': '',
            'source': '火山方舟知识库',
        })

    return context, doc_snapshots


def _query_notebooklm_kb(kb_config, exam_type, keywords):
    """查询 Google NotebookLM 知识库（基于 Gemini API + Corpus），返回 (上下文文本, 文档快照列表)

    使用 Google Gemini API 的 grounding 功能查询 NotebookLM 语料库。
    需要 API Key 和 Corpus ID（NotebookLM 笔记本ID）。
    """
    api_url = kb_config.get('api_url', KNOWLEDGE_PROVIDERS['notebooklm']['api_url'])
    api_key = kb_config.get('api_key', '')
    corpus_id = kb_config.get('corpus_id', '')  # NotebookLM 笔记本/语料库ID

    if not api_key:
        return '', []

    headers = {
        'Content-Type': 'application/json',
    }

    query_text = f'{exam_type}检查中，{keywords}的影像诊断有哪些？请详细说明。'

    # 使用 Gemini API 的 grounded generation 查询
    # 方式1：如果有 corpus_id，使用 Corpus 作为 grounding 数据源
    if corpus_id:
        payload = {
            'contents': [
                {
                    'parts': [{'text': query_text}]
                }
            ],
            'tools': [
                {
                    'retrieval': {
                        'source': {
                            'corpus': f'corpora/{corpus_id}'
                        }
                    }
                }
            ],
        }
        endpoint = f'{api_url}/models/gemini-2.0-flash:generateContent?key={api_key}'
    else:
        # 方式2：无 corpus_id，使用 Google Search grounding
        payload = {
            'contents': [
                {
                    'parts': [{'text': query_text}]
                }
            ],
            'tools': [
                {
                    'google_search': {}
                }
            ],
        }
        endpoint = f'{api_url}/models/gemini-2.0-flash:generateContent?key={api_key}'

    resp = requests.post(endpoint, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    # 提取文本内容
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
            # Web 引用
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
            # Retrieval 引用（Corpus 文档）
            retrieval_ref = chunk.get('retrievedContext', {})
            if retrieval_ref:
                doc_name = retrieval_ref.get('title', '') or retrieval_ref.get('uri', '文档引用')
                url = retrieval_ref.get('uri', '')
                snippet = retrieval_ref.get('text', '')[:200] + ('...' if len(retrieval_ref.get('text', '')) > 200 else '')
                doc_snapshots.append({
                    'doc_name': doc_name,
                    'page': '',
                    'snippet': snippet,
                    'url': url,
                    'source': 'Google NotebookLM',
                })

    context = '\n'.join(context_parts)

    # 如果没有提取到引用，但上下文非空，创建通用快照
    if not doc_snapshots and context:
        doc_snapshots.append({
            'doc_name': 'NotebookLM 查询结果',
            'page': '',
            'snippet': context[:200] + ('...' if len(context) > 200 else ''),
            'url': '',
            'source': 'Google NotebookLM',
        })

    return context, doc_snapshots
