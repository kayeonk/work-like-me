#!/usr/bin/env python3
"""work-like-me 규칙 관리 대시보드 (로컬 전용, 외부 의존성 0).

동작 모델:
- 토글(on/off)·★즐겨찾기는 **브라우저 메모리에서만** 바뀐다(초안). 디스크는 안 건드림.
- "변경 적용"을 눌러야 그때 rules.json에 저장하고 Claude/Codex 설정에 설치한다.
- 적용 전에 창을 닫으면 변경은 버려진다(파일은 마지막 적용 상태 그대로).
- 127.0.0.1 에만 바인딩. 로그/규칙을 외부로 보내지 않는다.

사용: python3 dashboard.py [--port 8765] [--target <단일 대상 override>]
"""
import argparse, json, os, subprocess, webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))          # 코드 위치(플러그인/스킬 폴더)
DATA_DIR = os.path.expanduser(os.environ.get("WORK_LIKE_ME_DATA", "~/.work-like-me"))  # 개인 데이터
RULES = os.path.join(DATA_DIR, "rules.json")

# UI 문구(크롬)는 meta.lang(ko/en)에 맞춘다. 규칙 내용·카테고리는 데이터 언어 그대로. 기본 en.
STRINGS = {
    "ko": {
        "title": "내 페르소나 관리", "active": "활성", "paused": "일시정지", "apply": "변경 적용",
        "hint": "켜고 끄거나 즐겨찾기한 내용은 아직 저장되지 않은 상태입니다. "
                "<b>변경 적용</b>을 눌러야 반영됩니다. 적용하지 않고 창을 닫으면 변경은 사라집니다.",
        "pending": "새로 반영할 내용이 있습니다",
        "applied": "반영했습니다: ", "noTarget": "반영할 대상이 없습니다",
        "js": {"dirty": "저장하지 않은 변경이 있습니다", "noChange": "반영할 변경이 없습니다.",
               "confirm": "변경한 내용을 반영합니다. 계속할까요?", "evPre": "근거 ", "evPost": "건",
               "toggleOff": "끄기(일시정지)", "toggleOn": "켜기",
               "conf": {"high": "상", "med": "중", "low": "하"},
               "src": {"induced": "대화 분석", "interview": "직접 답변", "hook": "자동 제안"}},
    },
    "en": {
        "title": "My Persona", "active": "active", "paused": "paused", "apply": "Apply changes",
        "hint": "Toggling or favoriting isn't saved yet. Click <b>Apply changes</b> to persist. "
                "Close the window without applying and changes are discarded.",
        "pending": "New signals are ready to review",
        "applied": "Applied: ", "noTarget": "No install targets",
        "js": {"dirty": "You have unsaved changes", "noChange": "No changes to apply.",
               "confirm": "Apply your changes. Continue?", "evPre": "", "evPost": " mentions",
               "toggleOff": "Pause", "toggleOn": "Enable",
               "conf": {"high": "high", "med": "med", "low": "low"},
               "src": {"induced": "from conversations", "interview": "from interview", "hook": "auto-suggested"}},
    },
}


def pick_lang(meta):
    return meta.get("lang") if meta.get("lang") in STRINGS else "en"


def load():
    return json.load(open(RULES, encoding="utf-8")) if os.path.exists(RULES) else {"meta": {}, "rules": []}


def save(d):
    os.makedirs(os.path.dirname(RULES), exist_ok=True)
    json.dump(d, open(RULES, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def default_targets():
    """설치 대상: Claude 전역 항상, Codex는 ~/.codex 있을 때만."""
    t = [os.path.expanduser("~/.claude/CLAUDE.md")]
    if os.path.isdir(os.path.expanduser("~/.codex")):
        t.append(os.path.expanduser("~/.codex/AGENTS.md"))
    return t


def target_name(path):
    if "CLAUDE" in path:
        return "Claude"
    if "codex" in path.lower() or "AGENTS" in path:
        return "Codex"
    return os.path.basename(path)


def apply_all(targets):
    """활성 규칙을 컴파일해 각 대상에 설치. 적용된 대상 이름 리스트 반환."""
    done = []
    for t in targets:
        r = subprocess.run(["python3", os.path.join(HERE, "install.py"),
                            "--from-rules", "--target", t, "--apply"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            done.append(target_name(t))
    return done


PAGE = """<!doctype html><html lang={{LANG}}><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>work-like-me</title>
<style>
:root{color-scheme:light dark}
body{font:15px/1.5 -apple-system,system-ui,sans-serif;max-width:900px;margin:0 auto;padding:24px;
 background:Canvas;color:CanvasText}
h1{font-size:20px;margin:0 0 4px}.sub{opacity:.6;font-size:13px;margin-bottom:16px}
.bar{display:flex;gap:8px;align-items:center;margin:12px 0 8px;flex-wrap:wrap}
.badge{background:#0000000f;border-radius:20px;padding:4px 12px;font-size:12px}
.pending{background:#e8830022;color:#c26a00}
.dirty{font-size:12px;font-weight:600;color:#e0830a}
button{font:inherit;border:1px solid #8884;background:Canvas;color:CanvasText;border-radius:8px;
 padding:6px 12px;cursor:pointer}button:hover{border-color:#888}
.apply{background:#2d6cdf;color:#fff;border-color:#2d6cdf}
.apply.need{background:#e0830a;border-color:#e0830a;animation:pulse 1.2s infinite}
@keyframes pulse{50%{opacity:.55}}
h2{font-size:14px;text-transform:uppercase;letter-spacing:.04em;opacity:.55;margin:22px 0 8px}
.card{border:1px solid #8883;border-radius:12px;padding:12px 14px;margin:8px 0;display:flex;gap:12px}
.card.off{opacity:.4}
.card .main{flex:1}.title{font-weight:600}.title .star{cursor:pointer;color:#e0a400}
.text{font-size:13.5px;opacity:.85;margin-top:3px}
.meta{font-size:12px;opacity:.55;margin-top:5px}
.conf-high{color:#1a8a3a}.conf-med{color:#b98600}.conf-low{color:#b04a4a}
.toggle{align-self:center;padding:12px 10px;cursor:pointer}
.switch{width:52px;height:30px;border-radius:20px;background:#8884;position:relative;transition:.15s}
.switch.on{background:#2d9d5a}.knob{position:absolute;top:3px;left:3px;width:24px;height:24px;border-radius:50%;
 background:#fff;transition:.15s;box-shadow:0 1px 3px #0003}.switch.on .knob{left:25px}
.hint{font-size:12px;opacity:.6;margin:0 0 16px}
</style></head><body>
<h1>{{TITLE}}</h1>
<div class=sub>__IDENTITY__</div>
<div class=bar>
 <span class=badge>{{ACTIVE}} <b id=cEn>0</b> · {{PAUSED}} <b id=cOff>0</b> · ★<b id=cFav>0</b></span>
 __PENDING__
 <span id=dirty class=dirty></span>
 <button id=applyBtn class=apply onclick=apply()>{{APPLY}}</button>
</div>
<div class=hint>{{HINT}}</div>
<div id=list></div>
<script>
let data=null, orig=null;
const L={{L_JSON}};
const SRC=L.src;
// 확신도 값(상/중/하 또는 high/med/low)을 canonical로 정규화 → 색상·라벨 언어 대응
function canon(c){return ({상:'high',high:'high',중:'med',med:'med',medium:'med',하:'low',low:'low'})[c]||''}
function snap(){return JSON.stringify(data.rules.map(r=>[r.id, r.enabled!==false, !!r.favorite]))}
function isDirty(){return snap()!==orig}
async function load(){data=await (await fetch('/rules.json')).json(); orig=snap(); render(); refreshDirty()}
function counts(){cEn.textContent=data.rules.filter(r=>r.enabled!==false).length;
 cOff.textContent=data.rules.filter(r=>r.enabled===false).length;
 cFav.textContent=data.rules.filter(r=>r.favorite).length}
function refreshDirty(){const b=document.getElementById('applyBtn'),d=document.getElementById('dirty');
 if(isDirty()){b.classList.add('need');d.textContent=L.dirty;}
 else{b.classList.remove('need');d.textContent='';}}
function render(){
 counts();const cats={};data.rules.forEach(r=>(cats[r.category||'기타']=cats[r.category||'기타']||[]).push(r));
 const HINT=['절대규칙','가치관','판단','검증','소통','상황별'];
 const order=[...HINT.filter(c=>cats[c]), ...Object.keys(cats).filter(c=>!HINT.includes(c))];
 const el=document.getElementById('list');el.innerHTML='';
 order.forEach(c=>{
  const h=document.createElement('h2');h.textContent=c;el.appendChild(h);
  cats[c].sort((a,b)=>(b.favorite?1:0)-(a.favorite?1:0)).forEach(r=>{
   const on=r.enabled!==false;
   const d=document.createElement('div');d.className='card'+(on?'':' off');
   d.innerHTML=`<div class=main><div class=title>
     <span class=star onclick="fav('${r.id}')">${r.favorite?'★':'☆'}</span> ${r.title}
     ${(cf=>cf?`<span class="conf-${cf}">·${L.conf[cf]}</span>`:'')(canon(r.confidence))}</div>
     <div class=text>${r.text}</div>
     <div class=meta>${L.evPre}${r.evidence?.count??0}${L.evPost} · ${SRC[r.source]||''}</div></div>
     <div class=toggle onclick="tog('${r.id}')" title="${on?L.toggleOff:L.toggleOn}"><div class="switch ${on?'on':''}"><div class=knob></div></div></div>`;
   el.appendChild(d);
  });
 });
}
// 메모리에서만 변경 (디스크 안 건드림)
function tog(id){const r=data.rules.find(x=>x.id===id); r.enabled=(r.enabled===false); render(); refreshDirty()}
function fav(id){const r=data.rules.find(x=>x.id===id); r.favorite=!r.favorite; render(); refreshDirty()}
async function apply(){
 if(!isDirty()){alert(L.noChange);return}
 if(!confirm(L.confirm))return;
 const states={}; data.rules.forEach(r=>states[r.id]={enabled:r.enabled!==false,favorite:!!r.favorite});
 const res=await (await fetch('/apply',{method:'POST',headers:{'Content-Type':'application/json'},
   body:JSON.stringify({states})})).text();
 orig=snap(); refreshDirty(); alert(res);
}
window.addEventListener('beforeunload', e=>{ if(isDirty()){e.preventDefault(); e.returnValue='';} });
load();
</script></body></html>"""


class H(BaseHTTPRequestHandler):
    targets = default_targets()

    def _send(self, body, ctype="text/html; charset=utf-8", code=200):
        b = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path == "/rules.json":
            self._send(json.dumps(load(), ensure_ascii=False), "application/json")
            return
        d = load()
        s = STRINGS[pick_lang(d.get("meta", {}))]
        flag = os.path.join(DATA_DIR, ".pending", "flag")
        pend = f'<span class="badge pending">{s["pending"]}</span>' if os.path.exists(flag) else ""
        ident = (d.get("meta", {}).get("identity", "") or "")[:120]
        page = (PAGE
                .replace("{{LANG}}", pick_lang(d.get("meta", {})))
                .replace("{{TITLE}}", s["title"])
                .replace("{{ACTIVE}}", s["active"])
                .replace("{{PAUSED}}", s["paused"])
                .replace("{{APPLY}}", s["apply"])
                .replace("{{HINT}}", s["hint"])
                .replace("{{L_JSON}}", json.dumps(s["js"], ensure_ascii=False))
                .replace("__IDENTITY__", ident)
                .replace("__PENDING__", pend))
        self._send(page)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n).decode("utf-8") if n else "{}"
        if self.path == "/apply":
            try:
                states = json.loads(raw).get("states", {})
            except Exception:
                states = {}
            d = load()
            for r in d["rules"]:
                s = states.get(r["id"])
                if s is not None:
                    r["enabled"] = bool(s.get("enabled", True))
                    r["favorite"] = bool(s.get("favorite", False))
            save(d)  # 적용할 때만 디스크에 저장
            s = STRINGS[pick_lang(d.get("meta", {}))]
            done = apply_all(H.targets)
            self._send((s["applied"] + ", ".join(done)) if done else s["noTarget"], "text/plain")
        else:
            self._send("not found", "text/plain", 404)

    def log_message(self, *a):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--target", default="", help="단일 대상 override (기본: Claude + Codex 자동)")
    a = ap.parse_args()
    H.targets = [os.path.expanduser(a.target)] if a.target else default_targets()
    url = f"http://127.0.0.1:{a.port}/"
    print(f"work-like-me 대시보드: {url}  (적용 대상: {', '.join(target_name(t) for t in H.targets)})  (Ctrl+C 종료)")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    HTTPServer(("127.0.0.1", a.port), H).serve_forever()


if __name__ == "__main__":
    main()
