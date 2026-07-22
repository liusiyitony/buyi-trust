"""
Buyi Trust Protocol — Certificate Share Page
Served at https://cert.diubige.com/<cert_id>

Dark + gold design, mobile-first, WeChat/Twitter share optimized.
"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flask import Blueprint, request, render_template_string
from db import get_db

page_bp = Blueprint('pages', __name__)

CERT_PAGE_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>📜 {{ cert.id }} — 决策证书</title>
  <meta property="og:title" content="{{ cert.id }} — 决策证书 · 不思议">
  <meta property="og:description" content="{{ cert.client.displayName }}的{{ cert.service.category }}决策，已于链上存证">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      background: #0a0a0f;
      color: #e0d5c0;
      display: flex; justify-content: center; align-items: flex-start;
      min-height: 100vh; padding: 20px;
    }
    .cert-card {
      max-width: 480px; width: 100%;
      background: linear-gradient(145deg, #1a1a2e 0%, #0f0f1a 100%);
      border: 1px solid #c8a84e33;
      border-radius: 16px;
      padding: 32px 24px;
      box-shadow: 0 0 60px #c8a84e15;
    }
    .cert-header {
      text-align: center; margin-bottom: 28px;
    }
    .cert-id {
      font-size: 14px; color: #c8a84e; font-family: monospace;
      letter-spacing: 1px;
    }
    .cert-badge {
      display: inline-block; margin-top: 8px; padding: 4px 14px;
      border: 1px solid #c8a84e66; border-radius: 20px;
      font-size: 12px; color: #c8a84e;
    }
    .cert-section {
      padding: 16px 0; border-bottom: 1px solid #ffffff0a;
    }
    .cert-section:last-child { border-bottom: none; }
    .section-label {
      font-size: 10px; text-transform: uppercase; letter-spacing: 2px;
      color: #8a8570; margin-bottom: 8px;
    }
    .section-value {
      font-size: 16px; color: #f0ead6; line-height: 1.5;
    }
    .section-value.highlight {
      font-size: 20px; font-weight: 600; color: #ffffff;
    }
    .section-value .confidence { color: #c8a84e; font-weight: 600; }
    
    .verification-status {
      display: inline-flex; align-items: center; gap: 6px;
      padding: 6px 14px; border-radius: 20px;
      font-size: 13px; font-weight: 500;
    }
    .status-pending { background: #c8a84e22; color: #c8a84e; }
    .status-correct { background: #2ecc7122; color: #2ecc71; }
    .status-partial { background: #f39c1222; color: #f39c12; }
    .status-incorrect { background: #e74c3c22; color: #e74c3c; }
    
    .proof-section {
      margin-top: 24px; padding: 16px;
      background: #ffffff05; border-radius: 12px;
    }
    .proof-row {
      display: flex; align-items: center; gap: 8px;
      padding: 6px 0; font-size: 13px; font-family: monospace;
      color: #8a8570;
    }
    .proof-row .label { color: #c8a84e; min-width: 70px; }
    .proof-row .hash { word-break: break-all; font-size: 11px; }
    
    .share-bar {
      margin-top: 24px; display: flex; gap: 10px;
      justify-content: center;
    }
    .btn {
      padding: 10px 20px; border: 1px solid #c8a84e44; border-radius: 10px;
      background: transparent; color: #c8a84e; font-size: 14px;
      cursor: pointer; transition: all 0.2s;
    }
    .btn:hover { background: #c8a84e15; }
    .btn.primary { background: #c8a84e; color: #0a0a0f; border-color: #c8a84e; }
    .btn.primary:hover { background: #d4b85c; }
    
    .verify-link {
      display: block; text-align: center; margin-top: 20px;
      padding: 14px; background: #c8a84e12; border-radius: 12px;
      color: #c8a84e; text-decoration: none; font-size: 14px;
      border: 1px dashed #c8a84e33;
    }
    .verify-link:hover { background: #c8a84e22; }
  </style>
</head>
<body>
<div class="cert-card">
  <div class="cert-header">
    <div class="cert-id">📜 {{ cert.id }}</div>
    <div class="cert-badge">{% if cert.verification.status == "pending" %}⏳ 待验证{% elif cert.verification.status == "correct" %}✅ 已验证{% endif %}</div>
  </div>
  
  <div class="cert-section">
    <div class="section-label">服务方</div>
    <div class="section-value">{{ cert.provider.name }}</div>
  </div>
  
  <div class="cert-section">
    <div class="section-label">客户</div>
    <div class="section-value">{{ cert.client.displayName }}</div>
  </div>
  
  <div class="cert-section">
    <div class="section-label">服务类型</div>
    <div class="section-value">{{ cert.service.category }}</div>
  </div>
  
  <div class="cert-section">
    <div class="section-label">核心结论</div>
    <div class="section-value highlight">{{ cert.service.conclusion }}</div>
    {% if cert.service.confidence %}
    <div class="section-value" style="margin-top:4px;">
      置信度：<span class="confidence">{{ cert.service.confidence }}%</span>
    </div>
    {% endif %}
  </div>
  
  <div class="cert-section">
    <div class="section-label">验证状态</div>
    <span class="verification-status status-{{ cert.verification.status }}">
      {% if cert.verification.status == "pending" %}⏳ 待客户验证{% elif cert.verification.status == "correct" %}✅ 判断准确{% elif cert.verification.status == "partial" %}⚠️ 部分准确{% else %}❌ 不准确{% endif %}
    </span>
    {% if cert.verification.valueScore %}
    <div class="section-value" style="margin-top:8px;font-size:14px;">
      价值评分：{% for i in range(cert.verification.valueScore) %}★{% endfor %}{% for i in range(5 - cert.verification.valueScore) %}☆{% endfor %}
    </div>
    {% endif %}
  </div>
  
  <div class="proof-section">
    <div class="proof-row">
      <span class="label">🔗 证书Hash</span>
      <span class="hash">{{ cert.proof.certHash[:32] }}...</span>
    </div>
    {% if cert.proof.easUid %}
    <div class="proof-row">
      <span class="label">⛓ EAS UID</span>
      <span class="hash">{{ cert.proof.easUid[:32] }}...</span>
    </div>
    {% endif %}
    <div class="proof-row">
      <span class="label">🔍 直接查链</span>
      <a href="https://basescan.org" target="_blank" style="color:#c8a84e;text-decoration:none;font-size:11px;">BaseScan → 搜EAS合约查attestation → 自己核对Hash</a>
    </div>
    <div class="proof-row">
      <span class="label">⏰ 创建时间</span>
      <span>{{ cert.createdAt[:10] }}</span>
    </div>
  </div>
  
  <a class="verify-link" href="/{{ cert.id }}/verify">
    {% if cert.verification.status == "pending" %}
    ✍️ 验证本次决策结果
    {% else %}
    📊 查看完整决策履历
    {% endif %}
  </a>
  
  <div class="share-bar">
    <button class="btn" onclick="share('copy')">📋 复制链接</button>
    <button class="btn primary" onclick="share('wechat')">💬 分享微信</button>
  </div>
</div>

<script>
function share(platform) {
  const url = window.location.href;
  if (platform === 'copy') {
    navigator.clipboard.writeText(url).then(() => alert('链接已复制'));
  } else if (platform === 'wechat') {
    navigator.clipboard.writeText(url + '\\n\\n📜 我的决策证书 — 链上存证，不可篡改');
    alert('链接和文案已复制，打开微信粘贴即可分享');
  }
}
</script>
</body>
</html>'''


@page_bp.route('/<cert_id>')
def cert_page(cert_id):
    """Render the certificate share page."""
    if cert_id == '' or cert_id == '/':
        return render_template_string(TRUST_PAGE_TEMPLATE)
    
    db = get_db()
    row = db.execute(
        "SELECT cert_json FROM certificates WHERE cert_id = ?", (cert_id,)
    ).fetchone()
    
    if not row:
        return "证书未找到", 404
    
    cert = json.loads(row["cert_json"])
    return render_template_string(CERT_PAGE_TEMPLATE, cert=cert)


# ═══════════════════════════════════════════════════════════════════
# Trust Landing Page — / (homepage)
# ═══════════════════════════════════════════════════════════════════

TRUST_PAGE_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>丢笔哥链上声誉验证 — 信任数学，不信任我们</title>
  <meta property="og:title" content="丢笔哥链上声誉验证">
  <meta property="og:description" content="你不需要信任我们，只需要信任数学。每份决策证书都在Base链上存证，不可篡改，公开可查。">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      background: #0a0a0f;
      color: #e0d5c0;
      line-height: 1.7;
    }
    .container { max-width: 680px; margin: 0 auto; padding: 40px 20px; }
    
    .hero {
      text-align: center; padding: 60px 0 40px;
      border-bottom: 1px solid #c8a84e22;
    }
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
      background: #ffffff03; border-radius: 14px;
      border: 1px solid #ffffff06;
    }
    .section h2 { font-size: 18px; color: #c8a84e; margin-bottom: 16px; }
    .section h3 { font-size: 15px; color: #ffffff; margin: 16px 0 8px; }
    
    .trust-layer {
      display: flex; gap: 14px; align-items: flex-start;
      padding: 16px 0; border-bottom: 1px solid #ffffff08;
    }
    .trust-layer:last-child { border-bottom: none; }
    .trust-layer .num {
      min-width: 36px; height: 36px; border-radius: 50%;
      background: #c8a84e22; color: #c8a84e; font-weight: 700;
      display: flex; align-items: center; justify-content: center;
      font-size: 14px;
    }
    .trust-layer .body h4 { font-size: 15px; color: #ffffff; margin-bottom: 4px; }
    .trust-layer .body p { font-size: 13px; color: #8a8570; }
    
    .highlight-box {
      margin: 24px 0; padding: 20px; border-radius: 12px;
      background: linear-gradient(135deg, #c8a84e10, #c8a84e05);
      border: 1px solid #c8a84e22;
    }
    .highlight-box p { font-size: 14px; text-align: center; color: #f0ead6; }
    .highlight-box .big { font-size: 20px; font-weight: 700; color: #c8a84e; }
    
    .code-block {
      margin: 12px 0; padding: 14px; border-radius: 10px;
      background: #00000044; font-family: monospace; font-size: 12px;
      color: #8a8570; word-break: break-all;
      border: 1px solid #ffffff08;
    }
    .code-block .key { color: #c8a84e; }
    
    .search-bar {
      display: flex; gap: 8px; max-width: 420px; margin: 0 auto;
    }
    .search-bar input {
      flex: 1; padding: 12px 16px; border-radius: 12px;
      border: 1px solid #c8a84e33; background: #ffffff08;
      color: #e0d5c0; font-size: 14px; outline: none;
    }
    .search-bar input:focus { border-color: #c8a84e; }
    .search-bar button {
      padding: 12px 20px; border-radius: 12px; border: none;
      background: #c8a84e; color: #0a0a0f; font-size: 14px; font-weight: 600;
      cursor: pointer;
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
  </style>
</head>
<body>
<div class="container">

  <!-- Hero -->
  <div class="hero">
    <h1>丢笔哥<span class="gold">链上声誉验证</span></h1>
    <p class="subtitle">你不需要信任我们，只需要信任数学。<br>每份决策证书都在 Base 链上存证，不可篡改，公开可查。</p>
    
    <div class="badge-row">
      <div class="badge">
        <div class="icon">🔒</div>
        <div class="label">不可篡改</div>
      </div>
      <div class="badge">
        <div class="icon">📊</div>
        <div class="label">全量透明</div>
      </div>
      <div class="badge">
        <div class="icon">⛓</div>
        <div class="label">Base链EAS</div>
      </div>
      <div class="badge">
        <div class="icon">🧠</div>
        <div class="label">三维验证</div>
      </div>
    </div>
  </div>

  <!-- 查验证书 -->
  <div class="section" style="text-align:center;">
    <h2>🔍 查验证书</h2>
    <p style="font-size:13px;color:#8a8570;margin-bottom:16px;">输入证书ID，验证任何一次决策记录</p>
    <form class="search-bar" onsubmit="search(event)">
      <input type="text" id="certSearch" placeholder="BUYI-20260722-XXXXX" autocomplete="off">
      <button type="submit">查询</button>
    </form>
  </div>

  <!-- 五层公信力 -->
  <div class="section">
    <h2>🏛️ 五层公信力保障</h2>
    
    <div class="trust-layer">
      <div class="num">①</div>
      <div class="body">
        <h4>代码开源</h4>
        <p>协议合约、服务端代码全部开源。任何人都可以审查代码里有没有"后门"。任何人都可以自己跑一个验证节点。</p>
        <div class="code-block">
          <span class="key">GitHub:</span> github.com/liusiyitony/buyi-trust
        </div>
      </div>
    </div>
    
    <div class="trust-layer">
      <div class="num">②</div>
      <div class="body">
        <h4>数据在链上，不在我们手里</h4>
        <p>所有核心数据写入 Base 链（EAS 协议），不是我们数据库。我们想删也删不掉，想改也改不了。我们的服务器挂了，链上数据还在。任何人都可以绕过我们的网站直接查链。</p>
        <div class="code-block">
          <span class="key">EAS 合约 (Base):</span> 0x4200000000000000000000000000000000000021<br>
          <span class="key">BaseScan:</span> <a href="https://basescan.org/address/0x4200000000000000000000000000000000000021" target="_blank" style="color:#c8a84e;">basescan.org</a>
        </div>
      </div>
    </div>
    
    <div class="trust-layer">
      <div class="num">③</div>
      <div class="body">
        <h4>买卖双方共同签名</h4>
        <p>每条记录需要服务方签名（证明提供了服务）和客户签名（证明确实消费了）。单方面无法造假记录。虚假记录 → 对方不签名 → 上不了链。</p>
      </div>
    </div>
    
    <div class="trust-layer">
      <div class="num">④</div>
      <div class="body">
        <h4>香港持牌实体运营</h4>
        <p>有法律主体可追溯，不是匿名项目。接受监管，合规运营。</p>
      </div>
    </div>
    
    <div class="trust-layer">
      <div class="num">⑤</div>
      <div class="body">
        <h4>时间积累</h4>
        <p>第一天：没人信你。第一个月：100条存证。第六个月：3000条存证，数据自己说话。第一年：5万条存证。信任不是宣称的，是积累出来的。</p>
      </div>
    </div>
  </div>

  <!-- 核心区别 -->
  <div class="highlight-box">
    <p>传统信任：<br><span class="big">"你信我就对了"</span></p>
    <p style="margin-top:16px;">我们的信任：<br><span class="big">"不需要信我——SHA256 Hash 你自己验证"</span></p>
  </div>

  <!-- 如何验证 -->
  <div class="section">
    <h2>📖 3分钟看懂链上验证</h2>
    <div class="flow">
      <div class="flow-step"><span class="arrow">1️⃣</span><br>你提问<br>AI/大师回应</div>
      <div class="flow-step"><span class="arrow">2️⃣</span><br>证书Hash<br>上Base链存证</div>
      <div class="flow-step"><span class="arrow">3️⃣</span><br>分享证书<br>到朋友圈/群</div>
      <div class="flow-step"><span class="arrow">4️⃣</span><br>30天后<br>验证结果</div>
      <div class="flow-step"><span class="arrow">5️⃣</span><br>你的验证<br>影响声誉分</div>
    </div>
    
    <h3>即使你不信任这个网站</h3>
    <p style="font-size:13px;color:#8a8570;">
      拿到证书ID → 打开 <a href="https://basescan.org" target="_blank" style="color:#c8a84e;">BaseScan</a> → 
      搜索 EAS 合约地址 → 找到 attestation 记录 → 自己核对 Hash。<br>
      不需要我们的网站，不需要信我们。你只需要信数学。
    </p>
  </div>

  <!-- 权威背书 -->
  <div class="section" style="text-align:center;">
    <h2>权威技术背书</h2>
    <div class="badge-row">
      <div class="badge">
        <div class="icon">🔵</div>
        <div class="label">Base (Coinbase)</div>
      </div>
      <div class="badge">
        <div class="icon">Ξ</div>
        <div class="label">EAS (Ethereum基金会)</div>
      </div>
      <div class="badge">
        <div class="icon">🔐</div>
        <div class="label">SHA256 (NIST)</div>
      </div>
      <div class="badge">
        <div class="icon">🇭🇰</div>
        <div class="label">香港持牌实体</div>
      </div>
    </div>
  </div>

  <!-- 国内版 -->
  <div class="section">
    <h2>🇨🇳 国内用户</h2>
    <p style="font-size:13px;color:#8a8570;">
      不用链、不用 VPN、不用 MetaMask。<br>
      每次服务生成 SHA256 Hash → 发布到公众号定时文章（不可撤回）→ 任何人可以对 Hash 验证。<br>
      公众号文章是腾讯的数据库，不是我们的——你改不了已发布的文章。<br>
      不需要区块链，达到同样的"不可篡改"效果。
    </p>
  </div>

  <div style="text-align:center; padding:30px 0;">
    <a href="/BUYI-20260722-15142" class="cta">👀 看一份真实证书</a>
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


@page_bp.route('/')
def trust_page():
    """Render the trust landing page."""
    return render_template_string(TRUST_PAGE_TEMPLATE)
