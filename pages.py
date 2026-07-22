"""
Buyi Trust Protocol — Pages
Served at https://cert.diubige.com/

Language: 许愿/还愿/灵验 (wish/vow/verify)
Designed for non-technical users in Chinese metaphysical context.
"""

import json
import os
import sys
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
  <meta property="og:title" content="🙏 许愿签 · {{ cert.id }}">
  <meta property="og:description" content="{{ cert.client.displayName }}所求：{{ cert.service.question[:60] }}… 卦象已出，天书记录">
  <meta property="og:type" content="website">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      background: #0a0a0f;
      color: #e0d5c0;
      display: flex; justify-content: center; align-items: flex-start;
      min-height: 100vh; padding: 20px;
    }
    .wish-card {
      max-width: 480px; width: 100%;
      background: linear-gradient(145deg, #1a1a2e 0%, #0f0f1a 100%);
      border: 1px solid #c8a84e33;
      border-radius: 16px;
      padding: 32px 24px;
      box-shadow: 0 0 60px #c8a84e15;
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
    .section-value .lingli { color: #c8a84e; font-weight: 600; }
    
    .status-badge {
      display: inline-flex; align-items: center; gap: 6px;
      padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 500;
    }
    .status-pending { background: #c8a84e22; color: #c8a84e; }
    .status-correct { background: #2ecc7122; color: #2ecc71; }
    .status-partial { background: #f39c1222; color: #f39c12; }
    .status-incorrect { background: #e74c3c22; color: #e74c3c; }
    
    .tianshu-section {
      margin-top: 24px; padding: 16px;
      background: #ffffff05; border-radius: 12px;
    }
    .tianshu-row {
      display: flex; align-items: center; gap: 8px;
      padding: 6px 0; font-size: 13px; font-family: monospace; color: #8a8570;
    }
    .tianshu-row .label { color: #c8a84e; min-width: 70px; }
    .tianshu-row .hash { word-break: break-all; font-size: 11px; }
    
    .share-bar { margin-top: 24px; display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }
    .btn {
      padding: 10px 20px; border: 1px solid #c8a84e44; border-radius: 10px;
      background: transparent; color: #c8a84e; font-size: 14px;
      cursor: pointer; transition: all 0.2s;
    }
    .btn:hover { background: #c8a84e15; }
    .btn.primary { background: #c8a84e; color: #0a0a0f; border-color: #c8a84e; }
    .btn.primary:hover { background: #d4b85c; }
    
    .return-link {
      display: block; text-align: center; margin-top: 20px; padding: 14px;
      background: #c8a84e12; border-radius: 12px; color: #c8a84e;
      text-decoration: none; font-size: 14px; border: 1px dashed #c8a84e33;
    }
    .return-link:hover { background: #c8a84e22; }
    
    .nudge-text {
      margin-top: 16px; padding: 12px; text-align: center;
      background: #c8a84e08; border-radius: 10px; font-size: 13px; color: #8a8570; line-height: 1.6;
    }
  </style>
</head>
<body>
<div class="wish-card">
  <div class="wish-header">
    <div class="wish-id">🙏 {{ cert.id }}</div>
    <div class="wish-badge">
      {% if cert.verification.status == "pending" %}⏳ 待还愿
      {% elif cert.verification.status == "correct" %}✨ 灵验了
      {% elif cert.verification.status == "partial" %}🌗 部分灵验
      {% else %}🌧 未灵{% endif %}
    </div>
  </div>
  
  <div class="wish-section">
    <div class="section-label">解签人</div>
    <div class="section-value">{{ cert.provider.name }}</div>
  </div>
  
  <div class="wish-section">
    <div class="section-label">香客</div>
    <div class="section-value">{{ cert.client.displayName }}</div>
  </div>
  
  <div class="wish-section">
    <div class="section-label">所求之事</div>
    <div class="section-value">{{ cert.service.category }}</div>
  </div>
  
  <div class="wish-section">
    <div class="section-label">卦象所示</div>
    <div class="section-value highlight">{{ cert.service.conclusion }}</div>
    {% if cert.service.confidence %}
    <div class="section-value" style="margin-top:4px;">
      灵力：<span class="lingli">{{ cert.service.confidence }}%</span>
    </div>
    {% endif %}
  </div>
  
  <div class="wish-section">
    <div class="section-label">还愿状态</div>
    <span class="status-badge status-{{ cert.verification.status }}">
      {% if cert.verification.status == "pending" %}⏳ 等待香客回来还愿
      {% elif cert.verification.status == "correct" %}✨ 灵验了！卦象应验
      {% elif cert.verification.status == "partial" %}🌗 部分灵验
      {% else %}🌧 未灵{% endif %}
    </span>
    {% if cert.verification.valueScore %}
    <div class="section-value" style="margin-top:8px;font-size:14px;">
      灵力值：{% for i in range(cert.verification.valueScore) %}★{% endfor %}{% for i in range(5 - cert.verification.valueScore) %}☆{% endfor %}
    </div>
    {% endif %}
  </div>
  
  <div class="tianshu-section">
    <div class="tianshu-row">
      <span class="label">📜 天书印记</span>
      <span class="hash">{{ cert.proof.certHash[:32] }}…</span>
    </div>
    <div class="tianshu-row">
      <span class="label">🔍 天书查证</span>
      <a href="https://basescan.org" target="_blank" style="color:#c8a84e;text-decoration:none;font-size:11px;">Base链上公开可查 · 自行核对</a>
    </div>
    <div class="tianshu-row">
      <span class="label">⏰ 许愿日</span>
      <span>{{ cert.createdAt[:10] }}</span>
    </div>
  </div>
  
  <a class="return-link" href="/{{ cert.id }}/verify">
    {% if cert.verification.status == "pending" %}
    🙏 回来还愿——灵不灵，都算数
    {% else %}
    📊 查看完整许愿履历
    {% endif %}
  </a>
  
  <div class="nudge-text">
    {% if cert.verification.status == "pending" %}
    卦已出了。30天后，无论结果如何——<br>灵了来还愿，不灵来说话。好的坏的，天书都记着。
    {% else %}
    此卦已还。天书记录，不可篡改。
    {% endif %}
  </div>
  
  <div class="share-bar">
    <button class="btn" onclick="share('copy')">📋 复制链接</button>
    <button class="btn primary" onclick="share('wechat')">📤 分享许愿签</button>
  </div>
</div>

<script>
function share(platform) {
  const url = window.location.href;
  if (platform === 'copy') {
    navigator.clipboard.writeText(url).then(() => alert('链接已复制'));
  } else if (platform === 'wechat') {
    navigator.clipboard.writeText('🙏 我在丢笔哥许了个愿，卦象已出——\\n' + url + '\\n\\n📜 天书记录，不可篡改。30天后回来还愿。');
    alert('许愿签已复制，打开微信粘贴即可分享');
  }
}
</script>
</body>
</html>'''


# ═══════════════════════════════════════════════════════════════════
# 灵验榜 — cert.diubige.com/leaderboard
# ═══════════════════════════════════════════════════════════════════

LEADERBOARD_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🏆 灵验榜 · 丢笔哥</title>
  <meta property="og:title" content="丢笔哥灵验榜 — 许愿还愿，天书记录">
  <meta property="og:description" content="谁是真的灵？天书记录不骗人。看灵力值，看还愿率。">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      background: #0a0a0f; color: #e0d5c0; line-height: 1.7;
    }
    .container { max-width: 680px; margin: 0 auto; padding: 40px 20px; }
    
    .hero { text-align: center; padding: 40px 0; border-bottom: 1px solid #c8a84e22; }
    .hero h1 { font-size: 28px; color: #ffffff; }
    .hero .gold { color: #c8a84e; }
    .hero p { font-size: 14px; color: #8a8570; margin-top: 8px; }
    
    .rank-card {
      display: flex; align-items: center; gap: 16px;
      padding: 16px; margin: 12px 0; border-radius: 14px;
      background: #ffffff05; border: 1px solid #ffffff06;
    }
    .rank-card.gold { border-color: #c8a84e44; background: #c8a84e08; }
    .rank-num { font-size: 24px; font-weight: 700; min-width: 36px; text-align: center; }
    .rank-num.g1 { color: #FFD700; } .rank-num.g2 { color: #C0C0C0; } .rank-num.g3 { color: #CD7F32; }
    .rank-num.other { color: #555; }
    
    .rank-info { flex: 1; }
    .rank-name { font-size: 16px; font-weight: 600; color: #ffffff; }
    .rank-stats { font-size: 12px; color: #8a8570; margin-top: 4px; }
    .rank-stats span { margin-right: 16px; }
    
    .rank-score { text-align: right; }
    .rank-score .lingli { font-size: 22px; font-weight: 700; color: #c8a84e; }
    .rank-score .rate { font-size: 12px; color: #8a8570; }
    .rank-score .rate.good { color: #2ecc71; }
    
    .empty-state { text-align: center; padding: 60px 0; color: #555; }
    .empty-state .icon { font-size: 48px; margin-bottom: 16px; }
    
    .footer { text-align: center; padding: 40px 0; color: #555; font-size: 12px; }
    .footer a { color: #c8a84e; text-decoration: none; }
    
    .nav { text-align: center; padding: 20px 0; }
    .nav a { color: #c8a84e; text-decoration: none; margin: 0 16px; font-size: 14px; }
  </style>
</head>
<body>
<div class="container">
  <div class="hero">
    <h1>🏆 丢笔哥<span class="gold">灵验榜</span></h1>
    <p>许愿还愿，天书记录。谁是真的灵，数据说话。</p>
  </div>
  
  <div class="nav">
    <a href="/">🏠 首页</a>
    <a href="/leaderboard">🏆 灵验榜</a>
    <a href="/BUYI-20260722-31535">🙏 看一份许愿签</a>
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
          <span>许愿 {{ p.total }} 次</span>
          <span>还愿 {{ p.verified }} 次</span>
        </div>
      </div>
      <div class="rank-score">
        <div class="lingli">{{ p.score }}</div>
        <div class="rate {% if p.rate is not none and p.rate >= 70 %}good{% endif %}">{% if p.rate is not none %}{{ p.rate }}% 灵验{% else %}待积累{% endif %}</div>
      </div>
    </div>
    {% endfor %}
  {% else %}
    <div class="empty-state">
      <div class="icon">🙏</div>
      <p>灵验榜刚刚开启</p>
      <p style="font-size:13px;margin-top:8px;">多许几个愿，多还几次愿，榜单就出来了。</p>
    </div>
  {% endif %}
  
  <div class="footer">
    <p>灵验榜数据来自 Base 链上公开存证 · <a href="https://cert.diubige.com">cert.diubige.com</a></p>
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
  <title>丢笔哥许愿签 — 许愿还愿，天书记录</title>
  <meta property="og:title" content="丢笔哥许愿签">
  <meta property="og:description" content="许愿还愿，天书记录。卦出了不怕验证，灵不灵都算数。">
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
    <p class="subtitle">许愿还愿，天书记录。<br>卦出了不怕验证——灵不灵，都算数。</p>
    
    <div class="badge-row">
      <div class="badge"><div class="icon">📜</div><div class="label">天书记录</div></div>
      <div class="badge"><div class="icon">👁</div><div class="label">全量公开</div></div>
      <div class="badge"><div class="icon">⛓</div><div class="label">Base链存证</div></div>
      <div class="badge"><div class="icon">🏆</div><div class="label">灵验榜</div></div>
    </div>
    
    <div class="nav-links">
      <a href="/leaderboard">🏆 灵验榜</a>
    </div>
  </div>

  <div class="section" style="text-align:center;">
    <h2>🙏 查许愿签</h2>
    <p style="font-size:13px;color:#8a8570;margin-bottom:16px;">输入许愿签编号，查看卦象与还愿记录</p>
    <form class="search-bar" onsubmit="search(event)">
      <input type="text" id="certSearch" placeholder="BUYI-20260722-XXXXX" autocomplete="off">
      <button type="submit">查看</button>
    </form>
  </div>

  <div class="section">
    <h2>📖 许愿 → 还愿，三步走</h2>
    <div class="flow">
      <div class="flow-step"><span class="arrow">1️⃣</span><br>你来问卦<br>大师/AI解签</div>
      <div class="flow-step"><span class="arrow">2️⃣</span><br>许愿签生成<br>天书记录</div>
      <div class="flow-step"><span class="arrow">3️⃣</span><br>分享许愿签<br>给朋友看</div>
      <div class="flow-step"><span class="arrow">4️⃣</span><br>时间到了<br>回来还愿</div>
      <div class="flow-step"><span class="arrow">5️⃣</span><br>灵验值更新<br>灵验榜刷新</div>
    </div>
  </div>

  <div class="highlight-box">
    <p>灵了来还愿，不灵来说话。<br><span class="big">好的坏的，天书都记着。</span></p>
  </div>

  <div class="section">
    <h2>🔐 为什么天书记录不可篡改</h2>
    <p style="font-size:13px;color:#8a8570;">
      每份许愿签的印记都写在 Base 链上（Coinbase L2），公开可查。<br>
      我们想改改不了。想删删不掉。服务器挂了，链上记录还在。<br><br>
      代码开源：<a href="https://github.com/liusiyitony/buyi-trust" target="_blank" style="color:#c8a84e;">github.com/liusiyitony/buyi-trust</a><br>
      Base链合约：0x4200…0021（<a href="https://basescan.org/address/0x4200000000000000000000000000000000000021" target="_blank" style="color:#c8a84e;">BaseScan可查</a>）
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
    <p>Buyi Trust Protocol · <a href="https://cert.diubige.com">cert.diubige.com</a></p>
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
    """Render the leaderboard page."""
    db = get_db()
    rows = db.execute("""
        SELECT provider_id, provider_name, 
               COUNT(*) as total,
               SUM(CASE WHEN status != 'pending' THEN 1 ELSE 0 END) as verified,
               SUM(CASE WHEN status = 'correct' THEN 1 ELSE 0 END) as correct,
               ROUND(AVG(value_score), 1) as avg_score
        FROM certificates
        GROUP BY provider_id
        ORDER BY avg_score DESC, total DESC
        LIMIT 20
    """).fetchall()
    
    leaders = []
    for r in rows:
        rate = round(r['correct'] / r['verified'] * 100, 1) if r['verified'] > 0 else None
        leaders.append({
            'name': r['provider_name'],
            'total': r['total'],
            'verified': r['verified'],
            'score': f"{r['avg_score']:.1f}" if r['avg_score'] else "—",
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
