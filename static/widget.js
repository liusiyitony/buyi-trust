/**
 * 丢笔哥许愿签 — Embeddable Widget v1.0
 * 
 * Usage: Add this script tag to any page:
 *   <script src="https://cert.diubige.com/widget.js" data-wish-id="BUYI-xxxxx"></script>
 *   <div id="wish-widget"></div>
 * 
 * Auto-fetches the cert data from the API and renders a compact card.
 */

(function() {
  const script = document.currentScript;
  const certId = script.getAttribute('data-wish-id');
  const target = document.getElementById('wish-widget') || document.currentScript.parentElement;
  
  if (!certId) {
    console.warn('[丢笔哥许愿签] No data-wish-id provided');
    return;
  }

  // Fetch cert data
  fetch(`https://cert.diubige.com/api/cert/${certId}`)
    .then(r => r.json())
    .then(cert => render(cert))
    .catch(err => {
      target.innerHTML = `<div style="padding:16px;border:1px solid #c8a84e33;border-radius:12px;background:#ffffff05;text-align:center;color:#8a8570;font-size:13px;">
        🙏 许愿签加载中…<br><a href="https://cert.diubige.com/${certId}" style="color:#c8a84e;">直接查看</a>
      </div>`;
      console.error('[丢笔哥许愿签]', err);
    });

  function render(cert) {
    const statusText = {
      pending: '⏳ 待验证',
      correct: '✨ 验证准确',
      partial: '🌗 部分准确',
      incorrect: '🌧 有偏差',
    };

    const statusColor = {
      pending: '#c8a84e',
      correct: '#2ecc71',
      partial: '#f39c12',
      incorrect: '#e74c3c',
    };

    const stars = '★'.repeat(cert.verification?.valueScore || 0) + '☆'.repeat(5 - (cert.verification?.valueScore || 0));
    const status = cert.verification?.status || 'pending';

    target.innerHTML = `
      <div style="
        max-width:520px;margin:24px auto;padding:20px 24px;
        border:1px solid #c8a84e33;border-radius:14px;
        background:linear-gradient(145deg,#1a1a2e,#0f0f1a);
        font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;
        color:#e0d5c0;line-height:1.6;
      ">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
          <span style="font-size:20px;">🙏</span>
          <span style="color:#c8a84e;font-size:14px;font-family:monospace;">丢笔哥许愿签</span>
          <span style="
            margin-left:auto;padding:3px 12px;border-radius:20px;
            font-size:12px;border:1px solid ${statusColor[status]}44;
            color:${statusColor[status]};background:${statusColor[status]}11;
          ">${statusText[status]}</span>
        </div>

        <div style="margin-bottom:12px;">
          <div style="font-size:10px;color:#8a8570;letter-spacing:1px;margin-bottom:4px;">问题</div>
          <div style="font-size:14px;color:#f0ead6;">${esc(cert.service?.question || '')}</div>
        </div>

        <div style="margin-bottom:12px;">
          <div style="font-size:10px;color:#8a8570;letter-spacing:1px;margin-bottom:4px;">判断</div>
          <div style="font-size:16px;font-weight:600;color:#ffffff;">${esc(cert.service?.conclusion || '')}</div>
          ${cert.service?.confidence ? `
            <div style="font-size:12px;color:#c8a84e;margin-top:4px;">把握度：${cert.service.confidence}%</div>
          ` : ''}
        </div>

        ${cert.provider?.name && cert.provider.id !== 'self' ? `
          <div style="margin-bottom:12px;font-size:13px;color:#8a8570;">
            服务方：${esc(cert.provider.name)}
          </div>
        ` : ''}

        ${status !== 'pending' ? `
          <div style="margin-bottom:12px;font-size:13px;color:#8a8570;">
            验证：${stars}
          </div>
        ` : ''}

        <div style="display:flex;gap:10px;margin-top:16px;padding-top:14px;border-top:1px solid #ffffff08;">
          <a href="https://cert.diubige.com/${certId}" target="_blank" style="
            flex:1;padding:10px;text-align:center;border-radius:10px;
            background:#c8a84e;color:#0a0a0f;text-decoration:none;font-size:13px;font-weight:600;
          ">查看完整许愿签</a>
          <a href="https://cert.diubige.com" target="_blank" style="
            padding:10px 16px;text-align:center;border-radius:10px;
            border:1px solid #c8a84e44;color:#c8a84e;text-decoration:none;font-size:13px;
          ">我也要许愿</a>
        </div>
      </div>
    `;
  }

  function esc(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
})();
