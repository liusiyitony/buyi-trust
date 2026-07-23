"""
KOL Harvester — Collect content from thought leaders, extract predictions,
auto-generate 许愿签 (wish certs), kickstart the validation pipeline.

Usage: python kol_harvester.py
Config: kol_sources.yaml (list of sources to harvest)
Output: cert.diubige.com API calls + local report
"""

import json
import time
import hashlib
import os
import sys
from datetime import datetime, timezone

# ── Config ──────────────────────────────────────────────────────────
CERT_API = os.getenv("CERT_API_URL", "http://localhost:8398/api/cert")
DEFAULT_VERIFY_DAYS = 90  # KOL predictions often need longer verification

# ── KOL Sources ─────────────────────────────────────────────────────
# Format: {name, url, category, type}
KOL_SOURCES = [
    # Financial / Investment
    {"name": "洪灏", "category": "金融预测", "type": "person",
     "sources": ["https://twitter.com/HAOHONG_CFA"]},
    {"name": "李笑来", "category": "金融预测", "type": "person",
     "sources": ["https://twitter.com/xiaolai"]},
    
    # AI / Tech
    {"name": "宝玉", "category": "AI趋势", "type": "person",
     "sources": ["https://twitter.com/dotey"]},
    
    # Crypto / Web3
    {"name": "神鱼", "category": "Web3预测", "type": "person",
     "sources": ["https://twitter.com/BitFish"]},
    
    # Macro / 宏观经济
    {"name": "任泽平", "category": "宏观预测", "type": "person",
     "sources": ["https://mp.weixin.qq.com/s?__biz=MzA3NDM4NzA4NQ=="]},
]

# ── Prediction Extraction Prompt ────────────────────────────────────
EXTRACT_PROMPT = """You are analyzing content from a thought leader/analyst. 
Extract every FORWARD-LOOKING PREDICTION or ACTIONABLE JUDGMENT from the text.
A prediction is a statement about what WILL happen, SHOULD happen, or a specific call to action with a direction.

For EACH prediction found, output a JSON object with:
- "question": what question does this prediction answer? (one sentence)
- "conclusion": the core prediction/judgment (one sentence, specific, directional)
- "confidence": estimated confidence level (0-100, based on how definitive the language is)
- "timeframe": when can this be verified? (e.g. "3 months", "end of 2026", "Q4")

Output as a JSON array. If no predictions found, return [].

Content to analyze:
---
{content}
---"""


# ── Core Harvester ──────────────────────────────────────────────────
def harvest_kol_source(source: dict) -> list[dict]:
    """
    Harvest predictions from a single KOL source.
    Returns list of prediction dicts ready for cert creation.
    """
    predictions = []
    
    for url in source.get("sources", []):
        content = fetch_content(url)
        if not content:
            continue
        
        extracted = extract_predictions(content)
        for pred in extracted:
            predictions.append({
                "provider_name": source["name"],
                "provider_id": slugify(source["name"]),
                "provider_type": source["type"],
                "category": source["category"],
                "question": pred["question"],
                "conclusion": pred["conclusion"],
                "confidence": pred.get("confidence", 50),
                "source_url": url,
                "timeframe": pred.get("timeframe", ""),
            })
    
    return predictions


def fetch_content(url: str) -> str:
    """Fetch text content from a URL. Supports Twitter, WeChat, web pages."""
    try:
        # Try curl for general web content
        import subprocess
        result = subprocess.run(
            ["curl", "-sL", "--max-time", "15", "-H", 
             "User-Agent: Mozilla/5.0 (compatible; BuyiHarvester/1.0)", url],
            capture_output=True, text=True, timeout=20
        )
        html = result.stdout
        
        if not html:
            return ""
        
        # Extract text from HTML
        from html.parser import HTMLParser
        
        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text = []
                self.skip = False
            def handle_starttag(self, tag, attrs):
                if tag in ('script', 'style', 'noscript'):
                    self.skip = True
            def handle_endtag(self, tag):
                if tag in ('script', 'style', 'noscript'):
                    self.skip = False
                if tag in ('p', 'div', 'br', 'li', 'h1', 'h2', 'h3', 'h4'):
                    self.text.append('\n')
            def handle_data(self, data):
                if not self.skip and data.strip():
                    self.text.append(data.strip())

        extractor = TextExtractor()
        extractor.feed(html)
        text = ' '.join(extractor.text)
        
        # Truncate to reasonable size
        return text[:8000]
        
    except Exception as e:
        print(f"  ⚠️ Failed to fetch {url}: {e}")
        return ""


def extract_predictions(content: str) -> list[dict]:
    """
    Use LLM to extract predictions from content.
    Falls back to keyword-based extraction if LLM unavailable.
    """
    # Try LLM extraction first
    llm_result = extract_via_llm(content)
    if llm_result:
        return llm_result
    
    # Fallback: keyword-based extraction
    return extract_via_keywords(content)


def extract_via_llm(content: str) -> list[dict] | None:
    """Use OpenAI-compatible API to extract predictions."""
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    
    if not api_key:
        return None
    
    try:
        import urllib.request
        
        payload = json.dumps({
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a prediction extraction engine. Output ONLY valid JSON array, no markdown, no explanation."},
                {"role": "user", "content": EXTRACT_PROMPT.format(content=content[:6000])}
            ],
            "temperature": 0.1,
            "max_tokens": 2000,
        }).encode()
        
        req = urllib.request.Request(
            f"{api_base}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }
        )
        
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            text = result["choices"][0]["message"]["content"]
            
            # Clean up markdown code blocks if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            
            predictions = json.loads(text.strip())
            if isinstance(predictions, list):
                return predictions
    except Exception as e:
        print(f"  LLM extraction failed: {e}")
    
    return None


def extract_via_keywords(content: str) -> list[dict]:
    """
    Fallback: extract predictions using keyword patterns.
    Looks for: 将会/预计/我认为/预测/判断/一定/不会/会/年底/Q*/明年...
    """
    import re
    
    predictions = []
    prediction_keywords = [
        r'(?:我?(?:预计|预测|判断|认为|觉得|估计|相信))[^。！？\n]{10,80}',
        r'(?:将(?:会|在|于))[^。！？\n]{10,80}',
        r'(?:一定|肯定|必[然定]|绝[对不])[^。！？\n]{10,80}',
        r'(?:Q[1-4]|今[年明后]|下[个季月年周]|年底?|明年)[^。！？\n]{10,80}',
        r'(?:突破|跌破|涨[到破]|跌[到破]|反弹|回调|见顶|触底)[^。！？\n]{10,60}',
    ]
    
    for pattern in prediction_keywords:
        matches = re.findall(pattern, content)
        for match in matches[:3]:  # Max 3 per pattern
            clean = match.strip('，！？。 ')
            if len(clean) < 10:
                continue
            predictions.append({
                "question": f"关于{clean[:20]}...的判断",
                "conclusion": clean[:120],
                "confidence": 60,
                "timeframe": "",
            })
    
    return predictions[:10]  # Max 10 predictions total


def create_cert(pred: dict) -> dict | None:
    """Create a 许愿签 via the cert API."""
    try:
        import urllib.request
        
        payload = json.dumps({
            "provider_name": pred["provider_name"],
            "provider_id": pred["provider_id"],
            "provider_type": pred["provider_type"],
            "category": pred["category"],
            "service_type": "predictive",
            "question": pred["question"],
            "conclusion": pred["conclusion"],
            "confidence": pred.get("confidence", 50),
            "client_name": "KOL内容采集",
            "detail": f"来源: {pred.get('source_url', '')}\n验证窗口: {pred.get('timeframe', '')}",
        }).encode()
        
        req = urllib.request.Request(
            CERT_API,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            return result
    except Exception as e:
        print(f"  ❌ Cert creation failed: {e}")
        return None


# ── Utilities ───────────────────────────────────────────────────────
def slugify(name: str) -> str:
    """Convert a name to a safe provider_id."""
    import re
    # Keep only alphanumeric and Chinese chars
    slug = re.sub(r'[^\w\u4e00-\u9fff]', '-', name.lower())
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug[:32] or hashlib.md5(name.encode()).hexdigest()[:8]


# ── Main ────────────────────────────────────────────────────────────
def run_harvest(sources: list[dict] = None, dry_run: bool = False):
    """
    Run the full harvest pipeline.
    
    Args:
        sources: List of KOL source dicts. Defaults to KOL_SOURCES.
        dry_run: If True, extract predictions but don't create certs.
    
    Returns:
        Report dict with summary and all predictions.
    """
    if sources is None:
        sources = KOL_SOURCES
    
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sources_processed": 0,
        "predictions_found": 0,
        "certs_created": 0,
        "results": [],
    }
    
    for source in sources:
        print(f"\n🔍 {source['name']} ({source['category']})")
        predictions = harvest_kol_source(source)
        report["sources_processed"] += 1
        
        if not predictions:
            print(f"  → No predictions found")
            continue
        
        print(f"  → Found {len(predictions)} predictions")
        report["predictions_found"] += len(predictions)
        
        for pred in predictions:
            result = {
                "source": source["name"],
                "category": source["category"],
                "question": pred["question"],
                "conclusion": pred["conclusion"],
                "confidence": pred["confidence"],
                "timeframe": pred.get("timeframe", ""),
            }
            
            if not dry_run:
                cert = create_cert(pred)
                if cert:
                    result["cert_id"] = cert.get("cert_id")
                    result["cert_url"] = f"https://cert.diubige.com/{cert.get('cert_id')}"
                    report["certs_created"] += 1
                    print(f"    📜 {cert.get('cert_id')}: {pred['conclusion'][:50]}...")
            
            report["results"].append(result)
            time.sleep(0.5)  # Rate limit
    
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="KOL Harvester — Collect predictions from thought leaders")
    parser.add_argument("--dry-run", action="store_true", help="Extract predictions without creating certs")
    parser.add_argument("--source", type=str, help="Harvest a single source by name")
    parser.add_argument("--output", type=str, default="harvest_report.json", help="Output report path")
    parser.add_argument("--add-kol", type=str, help="Add a KOL: name,category,type,url")
    args = parser.parse_args()
    
    sources = KOL_SOURCES
    
    if args.source:
        sources = [s for s in KOL_SOURCES if args.source.lower() in s["name"].lower()]
        if not sources:
            print(f"No KOL found matching '{args.source}'")
            print(f"Available: {[s['name'] for s in KOL_SOURCES]}")
            sys.exit(1)
    
    if args.add_kol:
        parts = args.add_kol.split(",", 3)
        if len(parts) >= 4:
            sources = [{
                "name": parts[0].strip(),
                "category": parts[1].strip(),
                "type": parts[2].strip(),
                "sources": [parts[3].strip()],
            }]
    
    report = run_harvest(sources, dry_run=args.dry_run)
    
    # Save report
    with open(args.output, "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"📊 HARVEST REPORT")
    print(f"   Sources:     {report['sources_processed']}")
    print(f"   Predictions: {report['predictions_found']}")
    print(f"   Certs:       {report['certs_created']}")
    print(f"   Report:      {args.output}")
    print(f"{'='*60}")
