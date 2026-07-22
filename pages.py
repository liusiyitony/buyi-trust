"""
Buyi Trust Protocol — Pages
Served at https://cert.diubige.com/

Universal judgment verification platform.
Language: 许愿/还愿 (universal — not metaphysical-specific).
C端-first: anyone can self-serve; B端 providers claim later.
"""

import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flask import Blueprint, render_template_string
from db import get_db

page_bp = Blueprint('pages', __name__)

# ═══════════════════════════════════════════════════════════════════
# 许愿签 — cert.diubige.com/<cert_id>
# ═══════════════════════════════════════════════════════════════════

WISH_PAGE_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🙏 许愿签 · 丢笔哥</title>
  <meta property="og:title" content="🙏 许愿签 · 我做了一个判断">
  <meta property="og:description" content="我做了个判断，30天后回来验证。灵不灵，天书记着。">
  <meta property="og:type" content="website">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      background: #0a0a0f; color: #e0d5c0; display: flex;
      justify-content: center; align-items: flex-start; min-height: 100vh; padding: 20px;
    }
    .wish-card {
      max-width: 480px; width: 100%;
      background: linear-gradient(145deg, #1a1a2e 0%, #0f0f1a 100%);
      border: 1px solid #c8a84e33; border-radius: 16px;
      padding: 32px 24px; box-shadow: 0 0 60px #c8a84e15;
    }
    .wish-header { text-align: center; margin-bottom: 28px; }
    .wish-id { font-size: 14px; color: #c8a84e; font-family: monospace; letter-spacing: 1px; }
    .wish-badge {
      display: inline-block; margin-top: 8px; padding: 4px 14px;
      border: 1px solid #c8a84e66; border-radius: 20px; font-size: 12px; color: #c8a84e;
    }
    .wish-section { padding: 16px 0; border-bottom: 1px solid #ffffff0a; }
    .wish-section:last-child { border-bottom: none; }
    .section-label { font-size: 10px; letter-spacing: 2px; color: #8a8570; margin-bottom: 8px; }
    .section-value { font-size: 16px; color: #f0ead6; line-height: 1.5; }
    .section-value.highlight { font-size: 20px; font-weight: 600; color: #ffffff; }
    .section-value .grasp { color: #c8a84e; font-weight: 600; }
    
    .status-badge {
      display: inline-flex; align-items: center; gap: 6px;
      padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 500;
    }
    .status-pending { background: #c8a84e22; color: #c8a84e; }
    .status-correct { background: #2ecc7122; color: #2ecc71; }
    .status-partial { background: #f39c1222; color: #f39c12; }
    .status-incorrect { background: #e74c3c22; color: #e74c3c; }
    
    .proof-section { margin-top: 24px; padding: 16px; background: #ffffff05; border-radius: 12px; }
    .proof-row {
      display: flex; align-items: center; gap: 8px; padding: 6px 0;
      font-size: 13px; font-family: monospace; color: #8a8570;
    }
    .proof-row .label { color: #c8a84e; min-width: 70px; }
    .proof-row .hash { word-break: break-all; font-size: 11px; }
    
    .share-bar { margin-top: 24px; display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }
    .btn {
      padding: 10px 20px; border: 1px solid #c8a84e44; border-radius: 10px;
      background: transparent; color: #c8a84e; font-size: 14px; cursor: pointer;
    }
    .btn:hover { background: #c8a84e15; }
    .btn.primary { background: #c8a84e; color: #0a0a0f; border-color: #c8a84e; }
    .btn.primary:hover { background: #d4b85c; }
    .btn.claim { background: #2ecc7122; color: #2ecc71; border-color: #2ecc7144; }
    
    .nudge-text {
      margin-top: 16px; padding: 12px; text-align: center;
      background: #c8a84e08; border-radius: 10px; font-size: 13px; color: #8a8570; line-height: 1.6;
    }
    .no-provider {
      margin-top: 12px; padding: 10px; text-align: center;
      background: #ffffff04; border-radius: 10px; border: 1px dashed #ffffff10;
      font-size: 12px; color: #555;
    }
  </style>
</head>
<body>
<div class="wish-card">
  <div class="wish-header">
    <div class="wish-id">🙏 许愿签</div>
    <div class="wish-badge">
      {% if cert.verification.status == "pending" %}⏳ 待还愿
      {% elif cert.verification.status == "correct" %}✨ 已验证
      {% elif cert.verification.status == "partial" %}🌗 部分验证
      {% else %}🌧 未验证{% endif %}
    </div>
  </div>
  
  <div class="wish-section">
    <div class="section-label">问题</div>
    <div class="section-value">{{ cert.service.question }}</div>
  </div>
  
  {% if cert.service.category %}
  <div class="wish-section">
    <div class="section-label">领域</div>
    <div class="section-value">{{ cert.service.category }}</div>
  </div>
  {% endif %}
  
  <div class="wish-section">
    <div class="section-label">判断</div>
    <div class="section-value highlight">{{ cert.service.conclusion }}</div>
    {% if cert.service.confidence %}
    <div class="section-value" style="margin-top:4px;">
      把握度：<span class="grasp">{{ cert.service.confidence }}%</span>
    </div>
    {% endif %}
  </div>
  
  {% if cert.provider.id != "self" %}
  <div class="wish-section">
    <div class="section-label">服务方</div>
    <div class="section-value">{{ cert.provider.name }}</div>
  </div>
  {% endif %}
  
  <div class="wish-section">
    <div class="section-label">验证状态</div>
    <span class="status-badge status-{{ cert.verification.status }}">
      {% if cert.verification.status == "pending" %}⏳ 等待验证
      {% elif cert.verification.status == "correct" %}✨ 判断准确
      {% elif cert.verification.status == "partial" %}🌗 部分准确
      {% else %}🌧 判断有偏差{% endif %}
    </span>
    {% if cert.verification.valueScore %}
    <div class="section-value" style="margin-top:8px;font-size:14px;">
      帮助度：{% for i in range(cert.verification.valueScore) %}★{% endfor %}{% for i in range(5 - cert.verification.valueScore) %}☆{% endfor %}
    </div>
    {% endif %}
  </div>
  
  {% if cert.verification.clientFeedback %}
  <div class="wish-section">
    <div class="section-label">反馈</div>
    <div class="section-value" style="font-size:14px;">{{ cert.verification.clientFeedback }}</div>
  </div>
  {% endif %}
  
  <div class="proof-section">
    <div class="proof-row">
      <span class="label">📜 存证编号</span>
      <span class="hash">{{ cert.id }}</span>
    </div>
    <div class="proof-row">
      <span class="label">⛓ 存证印记</span>
      <span class="hash">{{ cert.proof.certHash[:32] }}…</span>
    </div>
    <div class="proof-row">
      <span class="label">🔍 链上查证</span>
      <a href="https://basescan.org" target="_blank" style="color:#c8a84e;text-decoration:none;font-size:11px;">Base链公开可查 · 不可篡改</a>
    </div>
    <div class="proof-row">
      <span class="label">⏰ 创建于</span>
      <span>{{ cert.createdAt[:10] }}</span>
    </div>
  </div>
  
  {% if cert.verification.status == "pending" %}
  <div class="nudge-text">
    时间到了，回来验证。<br>准不准，都算数——好的坏的，链上都记着。
  </div>
  {% else %}
  <div class="nudge-text">
    此签已验。链上存证，不可篡改。
  </div>
  {% endif %}
  
  {% if cert.provider.id == "self" %}
  <div class="no-provider">
    这是个人判断，暂未经过专业人士分析。<br>
    服务方可以认领此签，提供专业分析。
  </div>
  {% endif %}
  
  <div class="share-bar">
    <button class="btn" onclick="share('copy')">📋 复制链接</button>
    <button class="btn primary" onclick="share('wechat')">📤 分享给朋友</button>
  </div>
</div>

<script>
function share(platform) {
  const url = window.location.href;
  if (platform === 'copy') {
    navigator.clipboard.writeText(url).then(() => alert('链接已复制'));
  } else if (platform === 'wechat') {
    navigator.clipboard.writeText('🙏 我做了个判断，30天后回来看——\\n' + url + '\\n\\n📜 链上存证，不可篡改。准不准，到时候见分晓。');
    alert('已复制，打开微信粘贴即可分享');
  }
}
</script>
</body>
</html>'''


# ═══════════════════════════════════════════════════════════════════
# 信用榜 — cert.diubige.com/leaderboard
# ═══════════════════════════════════════════════════════════════════

LEADERBOARD_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🏆 信用榜 · 丢笔哥</title>
  <meta property="og:title" content="丢笔哥信用榜 — 判断验证，公开可查">
  <meta property="og:description" content="做过判断，验证过结果。看谁真的准。">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      background: #0a0a0f; color: #e0d5c0; line-height: 1.7;
    }
    .container { max-width: 680px; margin: 0 auto; padding: 40px 20px; }
    .hero { text-align: center; padding: 40px 0; border-bottom: 1px solid #c8a84e22; }
    .hero h1 { font-size: 28px; color: #ffffff; } .hero .gold { color: #c8a84e; }
    .hero p { font-size: 14px; color: #8a8570; margin-top: 8px; }
    
    .rank-card {
      display: flex; align-items: center; gap: 16px; padding: 16px; margin: 12px 0;
      border-radius: 14px; background: #ffffff05; border: 1px solid #ffffff06;
    }
    .rank-card.gold { border-color: #c8a84e44; background: #c8a84e08; }
    .rank-num { font-size: 24px; font-weight: 700; min-width: 36px; text-align: center; }
    .rank-num.g1 { color: #FFD700; } .rank-num.g2 { color: #C0C0C0; } .rank-num.g3 { color: #CD7F32; }
    .rank-num.other { color: #555; }
    .rank-info { flex: 1; }
    .rank-name { font-size: 16px; font-weight: 600; color: #ffffff; }
    .rank-stats { font-size: 12px; color: #8a8570; margin-top: 4px; }
    .rank-score { text-align: right; }
    .rank-score .val { font-size: 22px; font-weight: 700; color: #c8a84e; }
    .rank-score .rate { font-size: 12px; color: #8a8570; }
    
    .tabs { display: flex; gap: 0; justify-content: center; margin: 24px 0; }
    .tab {
      padding: 10px 24px; border: 1px solid #c8a84e22; background: transparent;
      color: #8a8570; font-size: 14px; cursor: pointer;
    }
    .tab:first-child { border-radius: 10px 0 0 10px; }
    .tab:last-child { border-radius: 0 10px 10px 0; }
    .tab.active { background: #c8a84e; color: #0a0a0f; border-color: #c8a84e; }
    
    .empty-state { text-align: center; padding: 60px 0; color: #555; }
    .footer { text-align: center; padding: 40px 0; color: #555; font-size: 12px; }
    .footer a { color: #c8a84e; text-decoration: none; }
    .nav { text-align: center; padding: 10px 0; }
    .nav a { color: #c8a84e; text-decoration: none; margin: 0 16px; font-size: 14px; }
  </style>
</head>
<body>
<div class="container">
  <div class="hero">
    <h1>🏆 丢笔哥<span class="gold">信用榜</span></h1>
    <p>做过判断，验证过结果。数据自己说话。</p>
  </div>
  
  <div class="nav">
    <a href="/">🏠 首页</a>
    <a href="/leaderboard">🏆 信用榜</a>
  </div>
  
  {% if leaders %}
    {% for p in leaders %}
    <div class="rank-card {% if loop.index == 1 %}gold{% endif %}">
      <div class="rank-num {% if loop.index == 1 %}g1{% elif loop.index == 2 %}g2{% elif loop.index == 3 %}g3{% else %}other{% endif %}">
        {{ loop.index }}
      </div>
      <div class="rank-info">
        <div class="rank-name">{{ p.name }}</div>
        <div class="rank-stats">
          <span>{{ p.total }} 次判断</span>
          <span>{{ p.verified }} 次已验证</span>
        </div>
      </div>
      <div class="rank-score">
        <div class="val">{% if p.score %}{{ p.score }}{% else %}—{% endif %}</div>
        <div class="rate">{% if p.rate is not none %}准确率 {{ p.rate }}%{% else %}待验证{% endif %}</div>
      </div>
    </div>
    {% endfor %}
  {% else %}
    <div class="empty-state">
      <p>信用榜刚刚开启</p>
      <p style="font-size:13px;margin-top:8px;">多做几个判断，多验证几次，榜单就出来了。</p>
      <p style="margin-top:16px;"><a href="/" style="color:#c8a84e;">→ 去创建第一个许愿签</a></p>
    </div>
  {% endif %}
  
  <div class="footer">
    <p>信用榜数据来自 Base 链上公开存证</p>
  </div>
</div>
</body>
</html>'''


# ═══════════════════════════════════════════════════════════════════
# 首页 — cert.diubige.com/
# ═══════════════════════════════════════════════════════════════════

TRUST_PAGE_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>丢笔哥许愿签 — 做个判断，回来验证</title>
  <meta property="og:title" content="丢笔哥许愿签">
  <meta property="og:description" content="做过判断，记下来。30天后回来验证。准不准，链上数据说了算。">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      background: #0a0a0f; color: #e0d5c0; line-height: 1.7;
    }
    .container { max-width: 680px; margin: 0 auto; padding: 40px 20px; }
    
    .hero { text-align: center; padding: 60px 0 40px; border-bottom: 1px solid #c8a84e22; }
    .hero h1 { font-size: 28px; color: #ffffff; margin-bottom: 12px; }
    .hero h1 .gold { color: #c8a84e; }
    .hero .subtitle { font-size: 16px; color: #8a8570; max-width: 480px; margin: 0 auto; }
    
    .badge-row { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin: 32px 0; }
    .badge {
      padding: 10px 18px; border: 1px solid #c8a84e33; border-radius: 12px;
      background: #ffffff05; text-align: center;
    }
    .badge .icon { font-size: 24px; }
    .badge .label { font-size: 13px; color: #c8a84e; margin-top: 4px; }
    
    .section {
      margin: 40px 0; padding: 24px;
      background: #ffffff03; border-radius: 14px; border: 1px solid #ffffff06;
    }
    .section h2 { font-size: 18px; color: #c8a84e; margin-bottom: 16px; }
    
    .highlight-box {
      margin: 24px 0; padding: 20px; border-radius: 12px;
      background: linear-gradient(135deg, #c8a84e10, #c8a84e05);
      border: 1px solid #c8a84e22;
    }
    .highlight-box p { font-size: 14px; text-align: center; color: #f0ead6; }
    .highlight-box .big { font-size: 20px; font-weight: 700; color: #c8a84e; }
    
    .search-bar { display: flex; gap: 8px; max-width: 420px; margin: 0 auto; }
    .search-bar input {
      flex: 1; padding: 12px 16px; border-radius: 12px;
      border: 1px solid #c8a84e33; background: #ffffff08;
      color: #e0d5c0; font-size: 14px; outline: none;
    }
    .search-bar input:focus { border-color: #c8a84e; }
    .search-bar button {
      padding: 12px 20px; border-radius: 12px; border: none;
      background: #c8a84e; color: #0a0a0f; font-size: 14px; font-weight: 600; cursor: pointer;
    }
    
    .flow { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; margin: 20px 0; }
    .flow-step {
      padding: 12px 16px; border-radius: 10px; background: #ffffff05;
      font-size: 13px; text-align: center; min-width: 100px;
    }
    .flow-step .arrow { color: #c8a84e; }
    
    .use-cases { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; }
    .use-case {
      padding: 14px 18px; border: 1px solid #ffffff08; border-radius: 12px;
      background: #ffffff03; font-size: 13px; text-align: center; min-width: 120px;
    }
    .use-case .emoji { font-size: 24px; }
    .use-case .name { color: #e0d5c0; margin-top: 6px; }
    
    .footer { text-align: center; padding: 40px 0; color: #555; font-size: 12px; }
    .footer a { color: #c8a84e; text-decoration: none; }
    
    a.cta {
      display: inline-block; padding: 14px 32px; border-radius: 14px;
      background: #c8a84e; color: #0a0a0f; text-decoration: none;
      font-size: 15px; font-weight: 600; text-align: center;
    }
    a.cta:hover { background: #d4b85c; }
    
    .nav-links { text-align: center; padding: 0 0 20px; }
    .nav-links a { color: #c8a84e; text-decoration: none; margin: 0 16px; font-size: 14px; }
  </style>
</head>
<body>
<div class="container">

  <div class="hero">
    <h1>丢笔哥<span class="gold">许愿签</span></h1>
    <p class="subtitle">做过判断，记下来。<br>30天后回来验证——准不准，链上数据说了算。</p>
    
    <div class="badge-row">
      <div class="badge"><div class="icon">📝</div><div class="label">自己判断</div></div>
      <div class="badge"><div class="icon">🤝</div><div class="label">找专家评</div></div>
      <div class="badge"><div class="icon">⛓</div><div class="label">链上存证</div></div>
      <div class="badge"><div class="icon">📊</div><div class="label">公开验证</div></div>
    </div>
    
    <div class="nav-links">
      <a href="/leaderboard">🏆 信用榜</a>
    </div>
  </div>

  <div class="section" style="text-align:center;">
    <h2>🔍 查许愿签</h2>
    <form class="search-bar" onsubmit="search(event)">
      <input type="text" id="certSearch" placeholder="BUYI-20260722-XXXXX" autocomplete="off">
      <button type="submit">查看</button>
    </form>
  </div>

  <div class="section">
    <h2>📖 三步走</h2>
    <div class="flow">
      <div class="flow-step">1️⃣<br>我有个判断<br>记下来</div>
      <div class="flow-step">2️⃣<br>链上存证<br>不可篡改</div>
      <div class="flow-step">3️⃣<br>到时间了<br>回来验证</div>
      <div class="flow-step">4️⃣<br>数据说话<br>信用积累</div>
    </div>
  </div>

  <div class="section">
    <h2>🎯 什么判断都可以</h2>
    <div class="use-cases">
      <div class="use-case"><div class="emoji">📈</div><div class="name">金融投资<br>预测</div></div>
      <div class="use-case"><div class="emoji">🤖</div><div class="name">AI Agent<br>决策</div></div>
      <div class="use-case"><div class="emoji">💡</div><div class="name">创业想法<br>验证</div></div>
      <div class="use-case"><div class="emoji">🏥</div><div class="name">健康咨询<br>判断</div></div>
      <div class="use-case"><div class="emoji">⚖️</div><div class="name">法律意见<br>检验</div></div>
      <div class="use-case"><div class="emoji">🔮</div><div class="name">趋势研判</div></div>
    </div>
  </div>

  <div class="highlight-box">
    <p>不挑领域。不做评判。<br><span class="big">你判断，你记录，时间给你答案。</span></p>
  </div>

  <div class="section">
    <h2>💡 两种用法</h2>
    <div style="display:flex;gap:20px;flex-wrap:wrap;">
      <div style="flex:1;min-width:260px;padding:16px;background:#ffffff03;border-radius:12px;border:1px solid #c8a84e22;">
        <h3 style="font-size:14px;color:#c8a84e;margin-bottom:8px;">👤 个人用户</h3>
        <p style="font-size:13px;color:#8a8570;">
          自己有判断 → 创建许愿签 → 分享出去<br>
          时间到了回来验证 → 建立自己的判断信用
        </p>
      </div>
      <div style="flex:1;min-width:260px;padding:16px;background:#ffffff03;border-radius:12px;border:1px solid #2ecc7122;">
        <h3 style="font-size:14px;color:#2ecc71;margin-bottom:8px;">🏢 服务方</h3>
        <p style="font-size:13px;color:#8a8570;">
          认领许愿签 → 提供专业分析<br>
          每次验证都是信用资产 → 越准生意越多
        </p>
      </div>
    </div>
  </div>

  <div class="section">
    <h2>🔐 为什么可信</h2>
    <p style="font-size:13px;color:#8a8570;line-height:2;">
      📜 每份许愿签的印记都写在 Base 链上（Coinbase L2），公开可查<br>
      📂 代码开源：<a href="https://github.com/liusiyitony/buyi-trust" target="_blank" style="color:#c8a84e;">github.com/liusiyitony/buyi-trust</a><br>
      ⛓ Base链 EAS 合约：<a href="https://basescan.org/address/0x4200000000000000000000000000000000000021" target="_blank" style="color:#c8a84e;">0x4200…0021</a>（BaseScan可查）
    </p>
  </div>

  <div class="section" style="text-align:center;">
    <h2>权威技术</h2>
    <div class="badge-row">
      <div class="badge"><div class="icon">🔵</div><div class="label">Base (Coinbase)</div></div>
      <div class="badge"><div class="icon">Ξ</div><div class="label">EAS (以太坊)</div></div>
      <div class="badge"><div class="icon">🔐</div><div class="label">SHA256 (NIST)</div></div>
    </div>
  </div>

  <div style="text-align:center; padding:30px 0;">
    <a href="/BUYI-20260722-31535" class="cta">👀 看一份许愿签</a>
  </div>

  <div class="footer">
    <p>丢笔哥 · <a href="https://cert.diubige.com">cert.diubige.com</a></p>
    <p>Built on <a href="https://attest.org" target="_blank">EAS</a> · <a href="https://base.org" target="_blank">Base L2</a></p>
  </div>

</div>
<script>
function search(e) {
  e.preventDefault();
  var id = document.getElementById('certSearch').value.trim();
  if (id) window.location = '/' + id;
}
</script>
</body>
</html>'''


# ═══════════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════════

@page_bp.route('/leaderboard')
def leaderboard():
    """Render the credit leaderboard."""
    db = get_db()
    rows = db.execute("""
        SELECT 
            COALESCE(
                json_extract(cert_json, '$.provider.name'),
                json_extract(cert_json, '$.provider.id')
            ) as provider_name,
            COUNT(*) as total,
            SUM(CASE WHEN json_extract(cert_json, '$.verification.status') != 'pending' THEN 1 ELSE 0 END) as verified,
            SUM(CASE WHEN json_extract(cert_json, '$.verification.status') = 'correct' THEN 1 ELSE 0 END) as correct,
            ROUND(AVG(CAST(json_extract(cert_json, '$.verification.valueScore') AS REAL)), 1) as avg_score
        FROM certificates
        WHERE json_extract(cert_json, '$.provider.id') != 'self'
        GROUP BY provider_name
        ORDER BY avg_score DESC, total DESC
        LIMIT 20
    """).fetchall()
    
    leaders = []
    for r in rows:
        rate = round(r['correct'] / r['verified'] * 100, 1) if r['verified'] and r['verified'] > 0 else None
        leaders.append({
            'name': r['provider_name'],
            'total': r['total'],
            'verified': r['verified'],
            'score': f"{r['avg_score']:.1f}" if r['avg_score'] else None,
            'rate': rate,
        })
    
    return render_template_string(LEADERBOARD_TEMPLATE, leaders=leaders)


@page_bp.route('/<cert_id>')
def cert_page(cert_id):
    """Render the wish certificate page."""
    if cert_id == '' or cert_id == '/':
        return render_template_string(TRUST_PAGE_TEMPLATE)
    
    db = get_db()
    row = db.execute(
        "SELECT cert_json FROM certificates WHERE cert_id = ?", (cert_id,)
    ).fetchone()
    
    if not row:
        return "许愿签未找到", 404
    
    cert = json.loads(row["cert_json"])
    return render_template_string(WISH_PAGE_TEMPLATE, cert=cert)


@page_bp.route('/')
def trust_page():
    """Render the trust landing page."""
    return render_template_string(TRUST_PAGE_TEMPLATE)
