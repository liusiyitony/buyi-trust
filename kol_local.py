#!/usr/bin/env python3
"""
丢笔哥 KOL 采集器 — 本地版
在你的电脑上运行（能正常访问 Twitter/微博/公众号）
采集KOL的预测性判断，自动生成许愿签

用法:
  pip install requests pyyaml
  python kol_local.py

要求:
  - DEEPSEEK_API_KEY 环境变量（或创建 .env 文件）
  - 能正常访问各平台（VPN/代理）
"""

import json, requests, re, time, os, hashlib
from datetime import datetime

# ═══════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════

# 你的 cert 服务器地址
CERT_API = os.getenv("CERT_API", "https://cert.diubige.com/api/cert")

# DeepSeek API (从环境变量或 .env 文件读取)
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE = "https://api.deepseek.com/v1"

# KOL 名单 — 自由增减
KOLS = [
    # ── 金融投资 ──
    {"name": "洪灏", "platform": "twitter", "handle": "HAOHONG_CFA", "category": "金融预测"},
    {"name": "李蓓", "platform": "weibo", "handle": "1864302614", "category": "金融预测"},
    {"name": "但斌", "platform": "weibo", "handle": "danbin", "category": "金融预测"},
    
    # ── AI/科技 ──
    {"name": "宝玉", "platform": "twitter", "handle": "dotey", "category": "AI趋势"},
    {"name": "李开复", "platform": "twitter", "handle": "kaifulee", "category": "AI趋势"},
    
    # ── Web3 ──
    {"name": "神鱼", "platform": "twitter", "handle": "BitFish", "category": "Web3预测"},
    {"name": "Dovey Wan", "platform": "twitter", "handle": "DoveyWan", "category": "Web3预测"},
    
    # ── 身心灵 ──
    {"name": "武志红", "platform": "weibo", "handle": "wuzhihong", "category": "身心灵"},
    {"name": "张德芬", "platform": "weibo", "handle": "tiffanychang", "category": "身心灵"},
    {"name": "李雪", "platform": "weibo", "handle": "lixue", "category": "身心灵"},
    
    # ── 家庭教育 ──
    {"name": "尹建莉", "platform": "weibo", "handle": "yinjianli", "category": "家庭教育"},
    {"name": "王人平", "platform": "weibo", "handle": "wangrenping", "category": "家庭教育"},
]


# ═══════════════════════════════════════════════════════════
# 内容抓取
# ═══════════════════════════════════════════════════════════

def fetch_twitter(handle):
    """抓取 Twitter 用户最近推文"""
    # 通过 fxtwitter API
    try:
        r = requests.get(f"https://api.fxtwitter.com/{handle}/tweets", 
                        headers={"User-Agent": "BuyiHarvester/1.0"}, timeout=15)
        data = r.json()
        tweets = []
        for t in data.get('tweets', [])[:20]:
            text = re.sub(r'https?://\S+', '', t.get('text', ''))
            if len(text) > 20:
                tweets.append(text)
        return '\n\n'.join(tweets) if tweets else None
    except Exception as e:
        print(f"  ⚠️ Twitter抓取失败: {e}")
        return None


def fetch_weibo_rss(uid):
    """抓取微博 RSS（通过 rsshub 等中转）"""
    backends = [
        f"https://rsshub.app/weibo/user/{uid}",
        f"https://rss.shab.fun/weibo/user/{uid}",
    ]
    for url in backends:
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            if r.status_code == 200 and len(r.text) > 500:
                # Extract items
                items = re.findall(r'<description>(.*?)</description>', r.text, re.DOTALL)
                texts = []
                for item in items[:20]:
                    text = re.sub(r'<[^>]+>', '', item).strip()
                    text = re.sub(r'https?://\S+', '', text)
                    if len(text) > 15:
                        texts.append(text)
                return '\n\n'.join(texts) if texts else None
        except:
            continue
    return None


def fetch_content(kol):
    """根据平台类型抓取内容"""
    if kol['platform'] == 'twitter':
        return fetch_twitter(kol['handle'])
    elif kol['platform'] == 'weibo':
        return fetch_weibo_rss(kol['handle'])
    return None


# ═══════════════════════════════════════════════════════════
# LLM 提取预测
# ═══════════════════════════════════════════════════════════

def extract_predictions(content, name):
    """用 DeepSeek 从内容中提取预测性判断"""
    if not DEEPSEEK_KEY:
        # 没有 Key → 用关键词兜底
        preds = []
        for m in re.finditer(r'(?:预计|预测|判断|认为|将是|将[会在]|一定|肯定|必然)[^。！？\n]{15,100}', content):
            preds.append({
                "question": f"{name}的判断",
                "conclusion": m.group().strip(),
                "confidence": 60,
                "timeframe": "",
            })
        return preds[:10]

    prompt = f"""这些是 {name} 的内容。提取所有前瞻性预测或可验证的判断。
预测 = 关于未来会怎样、应该怎样的具体陈述。不提取对过去的描述。

内容:
{content[:5000]}

对于每个预测，输出:
- "question": 这个预测回答什么问题
- "conclusion": 具体的预测内容（一句话，可引用）
- "confidence": 语气确定程度 0-100
- "timeframe": 可验证时间（如果有）

只输出 JSON 数组。没有预测就输出 []。"""

    try:
        r = requests.post(
            f"{DEEPSEEK_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"},
            json={
                "model": "deepseek-v4-flash",
                "messages": [
                    {"role": "system", "content": "你只输出 JSON 数组，没有其他文字。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1, "max_tokens": 3000,
            },
            timeout=90,
        )
        text = r.json()["choices"][0]["message"]["content"].strip()
        if text.startswith("```"): text = text.split("```")[1]
        if text.startswith("json"): text = text[4:]
        return json.loads(text)
    except Exception as e:
        print(f"  ⚠️ LLM提取失败: {e}")
        return []


# ═══════════════════════════════════════════════════════════
# 创建许愿签
# ═══════════════════════════════════════════════════════════

def create_cert(pred, kol):
    """通过 API 创建许愿签"""
    payload = {
        "provider_name": kol['name'],
        "provider_id": re.sub(r'[^\w\u4e00-\u9fff]', '-', kol['name'].lower())[:32],
        "provider_type": "person",
        "category": kol['category'],
        "service_type": "predictive",
        "question": pred['question'],
        "conclusion": pred['conclusion'],
        "confidence": min(100, max(0, int(pred.get('confidence', 60)))),
        "client_name": "KOL采集",
        "detail": f"来源: {kol['platform']}/{kol.get('handle','')}\n验证: {pred.get('timeframe','')}",
    }

    try:
        r = requests.post(CERT_API, json=payload, timeout=15)
        return r.json()
    except Exception as e:
        print(f"  ❌ 创建失败: {e}")
        return None


# ═══════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════

def main(kols=None):
    if kols is None:
        kols = KOLS
    
    report = {"timestamp": datetime.now().isoformat(), "results": []}
    total = 0
    
    for kol in kols:
        print(f"\n{'─'*40}")
        print(f"🔍 {kol['name']} ({kol['category']})")
        
        content = fetch_content(kol)
        if not content:
            print(f"  → 无内容")
            continue
        
        print(f"  → 抓取到 {len(content)} 字，提取预测...")
        preds = extract_predictions(content, kol['name'])
        
        if not preds:
            print(f"  → 未发现预测")
            continue
        
        print(f"  → 发现 {len(preds)} 条预测:")
        for pred in preds[:5]:
            result = create_cert(pred, kol)
            if result:
                cid = result.get('cert_id', '?')
                print(f"    📜 {cid}: {pred['conclusion'][:60]}...")
                report['results'].append({
                    "kol": kol['name'],
                    "cert_id": cid,
                    "conclusion": pred['conclusion'],
                    "url": f"https://cert.diubige.com/{cid}",
                })
                total += 1
            time.sleep(0.5)
    
    print(f"\n{'='*50}")
    print(f"✅ 共创建 {total} 条许愿签")
    print(f"   查看: https://cert.diubige.com/leaderboard")
    
    # 保存报告
    with open("kol_harvest_report.json", "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"   报告: kol_harvest_report.json")


if __name__ == "__main__":
    # 尝试从 .env 读取
    try:
        with open(".env") as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    k, v = line.strip().split('=', 1)
                    os.environ[k] = v
    except FileNotFoundError:
        pass
    
    if not DEEPSEEK_KEY:
        # 试试从环境变量兜底
        DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    
    if DEEPSEEK_KEY:
        print(f"✅ DeepSeek API: {DEEPSEEK_KEY[:8]}...{DEEPSEEK_KEY[-4:]}")
    else:
        print("⚠️ 未设置 DEEPSEEK_API_KEY，将使用关键词提取（质量较低）")
        print("   设置方法: export DEEPSEEK_API_KEY=sk-xxx")
        print("   或在 .env 文件中写: DEEPSEEK_API_KEY=sk-xxx")
    
    main()