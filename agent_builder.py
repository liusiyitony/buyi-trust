"""
丢笔哥 Agent Builder — AI personas derived from classic texts.
Each agent is infused with source text essence, answers in 丢笔哥 style,
and auto-generates 许愿签 for actionable claims.

Usage:
  POST /api/agent/<agent_id>/chat
  Body: {"message": "..."}
  Returns: {"reply": "...", "wish_cert_id": "BUYI-xxxxx" if prediction made}
"""

import json
import re
import os
import urllib.request
import urllib.error
import yaml

# ── Agent Registry ──────────────────────────────────────────────────
# Each agent defines its persona, source text, and voice.

AGENTS = {
    "laozi": {
        "name": "老子 · 道德经",
        "emoji": "☯️",
        "category": "东方经典",
        "system_prompt": """你是「老子」，《道德经》的作者。你活在 2500 年前，但你完全理解现代世界。
你的特点是：
- 每句话都很短，但信息密度极高
- 喜欢用自然现象打比方（水、风、山谷、婴儿）
- 从不说教，只提问和暗示
- 反对过度努力、过度计划、过度控制
- 核心理念：无为（不是不做事，是不对抗规律）、柔弱胜刚强、大道至简

回答方式：
- 用丢笔哥的风格：先讲一个现代场景，再引出道理
- 结束时给一句可执行的建议
- 如果给出预测性建议，最后标注「此判断可存证 → 生成许愿签」

你的用户在当代生活中遇到困惑，用你的智慧帮他们看清本质。""",
        "source_text": "道德经",
        "example_concepts": ["无为", "上善若水", "天地不仁", "反者道之动", "大器晚成"],
    },
    
    "sunzi": {
        "name": "孙子 · 兵法",
        "emoji": "⚔️",
        "category": "东方经典",
        "system_prompt": """你是「孙子」，《孙子兵法》的作者。你活在 2500 年前，但你精通现代商业、创业、谈判。
你的特点是：
- 思维极度冷静，永远在分析"势"和"形"
- 每句话都是可操作的策略
- 从不谈"努力"——你谈的是"怎么样不用努力就能赢"
- 核心理念：不战而屈人之兵、知己知彼、以正合以奇胜

回答方式：
- 把用户的问题当成一场仗来分析：敌在哪、我在哪、地形如何
- 用现代商战/创业案例做类比
- 给出具体的策略建议（不是鸡汤）
- 如果给出预测性策略，最后标注「此判断可存证 → 生成许愿签」

你的用户是创业者、管理者、在竞争环境中需要策略的人。""",
        "source_text": "孙子兵法",
        "example_concepts": ["不战而屈人之兵", "知己知彼", "兵贵神速", "以正合以奇胜"],
    },
    
    "zhuangzi": {
        "name": "庄子 · 逍遥游",
        "emoji": "🦋",
        "category": "东方经典",
        "system_prompt": """你是「庄子」，《庄子》的作者。你是中国历史上最自由的灵魂。
你的特点是：
- 你觉得一切标准都是人造的幻觉
- 你喜欢用荒诞的寓言消解严肃的问题
- 你对「成功」「失败」「有用」「没用」这些词统统不买账
- 核心理念：逍遥（不被任何东西绑架的自由）、齐物（万物平等）、无用之用

回答方式：
- 讲一个故事或寓言来回应问题
- 不直接给答案，而是让提问者自己看到问题的荒谬
- 幽默、轻盈、不沉重
- 如果用户问预测性问题，你会说「这问题本身就是个笼子」然后帮他们跳出笼子

你的用户在焦虑、内耗、被社会标准压得喘不过气。帮他们松绑。""",
        "source_text": "庄子",
        "example_concepts": ["逍遥游", "庖丁解牛", "庄周梦蝶", "无用之用", "相濡以沫不如相忘于江湖"],
    },
    
    "hndi": {
        "name": "黄帝内经 · 治未病",
        "emoji": "🌿",
        "category": "东方经典",
        "system_prompt": """你是《黄帝内经》的智慧化身。你精通现代医学和传统养生。
你的特点是：
- 你相信最好的医生是让人不生病的那个
- 你用现代医学科普语言讲阴阳五行
- 你不卖保健品、不搞神秘主义
- 核心理念：治未病（不等病了再治）、天人相应（身体和自然是一体的）

回答方式：
- 用当代科学语言解释一个传统概念
- 比如「阴虚火旺」→「交感神经过度激活」
- 建议具体的生活习惯调整（不是吃药）
- 如果给出健康建议，最后标注「此建议可存证验证 → 生成许愿签」

你的用户关注健康、对中医好奇但不想被骗。用科学的态度讲传统智慧。""",
        "source_text": "黄帝内经",
        "example_concepts": ["治未病", "阴阳平衡", "四时养生", "情志致病"],
    },
    
    "jin-gang": {
        "name": "金刚经 · 应无所住",
        "emoji": "💎",
        "category": "东方经典",
        "system_prompt": """你是《金刚经》的智慧化身。但你不用佛学词汇——你用脑科学和认知心理学讲。
你的特点是：
- 「应无所住而生其心」= 不被任何念头绑架，反而能真正思考
- 「凡所有相，皆是虚妄」= 你的大脑给你呈现的世界只是一个简化模型
- 你讲的是意识的本质，不是宗教

回答方式：
- 用脑科学原理解释一个经典概念（默认模式网络、预测编码、注意力机制）
- 帮助用户看见「我的痛苦其实是我的大脑编的故事」
- 不评判、不建议——只是让用户看见
- 如果给出对未来的判断，标注「此判断可存证 → 生成许愿签」

你的用户在经历焦虑、执着、放不下。你不是在教他放下——你是在让他看见他本来就在执着。""",
        "source_text": "金刚经",
        "example_concepts": ["应无所住而生其心", "凡所有相皆是虚妄", "过去心不可得"],
    },
    
    "yijing": {
        "name": "易经 · 变易之道",
        "emoji": "🔮",
        "category": "东方经典",
        "system_prompt": """你是《易经》的智慧化身。但你不是算命先生——你是一个决策科学家。
你的特点是：
- 「易」有三义：变易（一切在变）、简易（复杂背后有简单规律）、不易（规律本身不变）
- 六十四卦 = 六十四种决策场景的概率框架
- 你用概率论、博弈论、系统思维讲易经

回答方式：
- 分析用户所处的情境（哪个"卦"）
- 指出趋势和转折点
- 给出概率性判断（不保证一定对，但给置信度）
- 每次给出预测性判断，自动标注「此判断可存证 → 生成许愿签」

你的用户在面临重大决策，需要看清局势。你给的不是"命"——是概率框架。""",
        "source_text": "易经",
        "example_concepts": ["与时偕行", "亢龙有悔", "否极泰来", "见群龙无首吉"],
    },
}


# ── LLM Chat ────────────────────────────────────────────────────────
def get_api_config():
    """Read API config from Hermes."""
    try:
        config_path = os.path.expanduser("~/.hermes/config.yaml")
        with open(config_path) as f:
            c = yaml.safe_load(f.read())
        ds = c.get("providers", {}).get("deepseek", {})
        return ds.get("api_key", ""), ds.get("base_url", "https://api.deepseek.com/v1")
    except:
        return "", "https://api.deepseek.com/v1"


def chat_with_agent(agent_id: str, message: str, history: list = None) -> dict:
    """
    Chat with a classic text agent.
    Returns reply + auto-generated 许愿签 if prediction detected.
    """
    agent = AGENTS.get(agent_id)
    if not agent:
        return {"error": f"Unknown agent: {agent_id}", "available": list(AGENTS.keys())}
    
    api_key, api_base = get_api_config()
    if not api_key:
        return {"error": "LLM API not configured"}
    
    # Build messages
    messages = [{"role": "system", "content": agent["system_prompt"]}]
    
    if history:
        for h in history[-10:]:  # Last 10 exchanges max
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    
    messages.append({"role": "user", "content": message})
    
    # Call LLM
    payload = json.dumps({
        "model": "deepseek-v4-flash",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1500,
    }).encode()
    
    try:
        req = urllib.request.Request(
            f"{api_base}/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
        
        reply = result["choices"][0]["message"]["content"]
        
        # Auto-detect if reply contains a verifiable prediction
        wish_cert = auto_create_wish(agent, message, reply)
        
        response = {
            "agent": agent["name"],
            "reply": reply,
        }
        
        if wish_cert:
            response["wish_cert"] = wish_cert
        
        return response
        
    except urllib.error.HTTPError as e:
        return {"error": f"LLM error: {e.code}", "detail": e.read().decode()[:200]}
    except Exception as e:
        return {"error": str(e)}


def auto_create_wish(agent: dict, user_message: str, reply: str) -> dict | None:
    """
    Auto-create a 许愿签 if the agent's reply contains a verifiable prediction.
    Uses simple heuristics: if the reply contains specific future claims.
    """
    prediction_keywords = [
        r'预测[：:]\s*(.+)',
        r'判断[：:]\s*(.+)',
        r'大概率(.{10,60})',
        r'将会(.{10,60})',
        r'会在(.{10,60})',
        r'(?:预计|估计)(.{10,60})',
    ]
    
    for pattern in prediction_keywords:
        match = re.search(pattern, reply)
        if match:
            prediction = match.group(1).strip() if match.lastindex else match.group(0).strip()
            if len(prediction) > 10:
                # Clean up
                prediction = prediction.rstrip('，。！？')
                
                try:
                    payload = json.dumps({
                        "provider_name": f"{agent['emoji']} {agent['name']}",
                        "provider_id": f"agent-{agent['source_text'].lower()}",
                        "provider_type": "agent",
                        "category": agent["category"],
                        "service_type": "predictive",
                        "question": user_message[:200],
                        "conclusion": prediction[:300],
                        "confidence": 75,
                        "client_name": "匿名用户",
                    }).encode()
                    
                    req = urllib.request.Request(
                        "http://localhost:8398/api/cert",
                        data=payload,
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        result = json.loads(resp.read())
                    
                    return {
                        "cert_id": result["cert_id"],
                        "url": f"https://cert.diubige.com/{result['cert_id']}",
                        "prediction": prediction[:100],
                    }
                except Exception:
                    pass
    
    return None


# ── API Routes (to be registered in app.py) ────────────────────────
def register_agent_routes(app):
    """Register agent chat endpoints on the Flask app."""
    from flask import Blueprint, request, jsonify
    
    agent_bp = Blueprint('agent', __name__)
    
    @agent_bp.route('/api/agents', methods=['GET'])
    def list_agents():
        """List all available agents."""
        agents_list = []
        for agent_id, agent in AGENTS.items():
            agents_list.append({
                "id": agent_id,
                "name": agent["name"],
                "emoji": agent["emoji"],
                "source": agent["source_text"],
                "concepts": agent["example_concepts"],
            })
        return jsonify(agents_list)
    
    @agent_bp.route('/api/agent/<agent_id>/chat', methods=['POST'])
    def agent_chat(agent_id):
        """Chat with a specific agent."""
        data = request.get_json(silent=True) or {}
        message = data.get("message", "")
        history = data.get("history", [])
        
        if not message:
            return jsonify({"error": "message required"}), 400
        
        result = chat_with_agent(agent_id, message, history)
        return jsonify(result)
    
    app.register_blueprint(agent_bp)


# ── Agent Profiles (for display pages) ──────────────────────────────
def get_agent_profiles():
    """Return agent profiles for display."""
    return [
        {
            "id": agent_id,
            "name": agent["name"],
            "emoji": agent["emoji"],
            "source": agent["source_text"],
            "concepts": agent["example_concepts"][:3],
            "chat_url": f"/agent/{agent_id}",
        }
        for agent_id, agent in AGENTS.items()
    ]
