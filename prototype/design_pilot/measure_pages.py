#!/usr/bin/env python3
"""디자인 판정 파일럿 2단계: 생성된 페이지를 실제로 그려서 자동 측정한다.

측정 항목은 두 곳에서 가져왔다.
  (공개 기준)  WCAG 대비, 가로 넘침, 터치 영역, 레이블·alt 등 기본 접근성
  (도구 설명서) impeccable `craft-floor.md`의 Verify/Refuse 목록, frontend-design `SKILL.md`의 금지·기본값 목록
'도구가 스스로 적은 기준을 그 도구를 쓴 결과가 실제로 지켰는가'를 본다.
출력: results.json, results.csv, screenshots/*.png
"""
import csv
import glob
import json
import os
import re
import sys

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
PAGES = os.path.join(HERE, "pages")
SHOTS = os.path.join(HERE, "screenshots")
os.makedirs(SHOTS, exist_ok=True)

JS = r"""
() => {
  const out = {};
  const parse = c => { const m = c && c.match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number);
    return {r:p[0], g:p[1], b:p[2], a:p.length>3 ? p[3] : 1}; };
  const lin = v => { v/=255; return v<=0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); };
  const lum = c => 0.2126*lin(c.r) + 0.7152*lin(c.g) + 0.0722*lin(c.b);
  const hex = c => '#' + [c.r,c.g,c.b].map(v => Math.round(v).toString(16).padStart(2,'0')).join('');
  const dist = (a,b) => Math.sqrt((a.r-b.r)**2 + (a.g-b.g)**2 + (a.b-b.b)**2);
  const visible = el => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    return r.width>0 && r.height>0 && cs.visibility!=='hidden' && cs.display!=='none' && parseFloat(cs.opacity)>0; };
  const bgOf = el => { const layers = []; let e = el;
    while (e) { const cs = getComputedStyle(e); const c = parse(cs.backgroundColor);
      if (cs.backgroundImage && cs.backgroundImage !== 'none') return null;
      if (c && c.a > 0) { layers.push(c); if (c.a >= 1) break; }
      e = e.parentElement; }
    let base = {r:255,g:255,b:255,a:1};
    for (let i = layers.length-1; i >= 0; i--) { const l = layers[i];
      base = {r:l.r*l.a+base.r*(1-l.a), g:l.g*l.a+base.g*(1-l.a), b:l.b*l.a+base.b*(1-l.a), a:1}; }
    return base; };

  const all = [...document.querySelectorAll('body *')].filter(visible);
  const textEls = all.filter(el => [...el.childNodes].some(n => n.nodeType===3 && n.textContent.trim().length>0));

  // 1) 글자 대비 (WCAG)
  let tested = 0, failed = 0, unknown = 0, minRatio = 99;
  const sizes = new Set(), families = new Set(), textColors = new Set(), weights = new Set();
  for (const el of textEls) {
    const cs = getComputedStyle(el); const fs = parseFloat(cs.fontSize); const w = parseInt(cs.fontWeight) || 400;
    sizes.add(Math.round(fs*2)/2); weights.add(w);
    families.add(cs.fontFamily.split(',')[0].replace(/["']/g,'').trim().toLowerCase());
    const fg = parse(cs.color); const bg = bgOf(el);
    if (!fg) continue;
    textColors.add(hex(fg));
    if (!bg) { unknown++; continue; }
    const f = {r:fg.r*fg.a+bg.r*(1-fg.a), g:fg.g*fg.a+bg.g*(1-fg.a), b:fg.b*fg.a+bg.b*(1-fg.a)};
    const L1 = lum(f), L2 = lum(bg); const ratio = (Math.max(L1,L2)+0.05)/(Math.min(L1,L2)+0.05);
    const large = fs >= 24 || (fs >= 18.66 && w >= 700);
    tested++; if (ratio < (large ? 3 : 4.5)) failed++; minRatio = Math.min(minRatio, ratio);
  }
  out.contrast_tested = tested; out.contrast_failed = failed; out.contrast_unknown_bg = unknown;
  out.contrast_min = tested ? Math.round(minRatio*100)/100 : null;
  out.font_sizes = sizes.size; out.font_families = families.size; out.font_weights = weights.size;
  out.text_colors = textColors.size; out.family_list = [...families];

  // 2) 간격(4px 격자)
  const sp = [];
  for (const el of all) { const cs = getComputedStyle(el);
    for (const p of ['marginTop','marginBottom','marginLeft','marginRight','paddingTop','paddingBottom','paddingLeft','paddingRight','rowGap','columnGap']) {
      const v = parseFloat(cs[p]); if (!isNaN(v) && v > 0) sp.push(Math.round(v*2)/2); } }
  const spSet = new Set(sp);
  out.spacing_values = spSet.size;
  out.spacing_on_4px = sp.length ? Math.round(100*sp.filter(v => Math.abs(v/4 - Math.round(v/4)) < 0.01).length/sp.length) : null;

  // 3) 본문 줄 길이
  let maxCh = null;
  for (const p of document.querySelectorAll('p')) { const t = p.textContent.trim(); if (t.length < 60 || !visible(p)) continue;
    const cs = getComputedStyle(p); const ch = p.getBoundingClientRect().width / (parseFloat(cs.fontSize)*0.5);
    maxCh = Math.max(maxCh||0, Math.round(ch)); }
  out.max_line_ch = maxCh;

  // 4) 가로 넘침, 터치 영역
  out.h_overflow = document.documentElement.scrollWidth > window.innerWidth + 1;
  const inter = [...document.querySelectorAll('a[href], button, input:not([type=hidden]), select, textarea, [role=button]')].filter(visible);
  out.interactive = inter.length;
  out.target_lt24 = inter.filter(e => { const r = e.getBoundingClientRect(); return Math.min(r.width, r.height) < 24; }).length;
  out.target_lt44 = inter.filter(e => { const r = e.getBoundingClientRect(); return Math.min(r.width, r.height) < 44; }).length;

  // 5) 의미 구조·접근성
  out.has_lang = !!document.documentElement.getAttribute('lang');
  out.has_main = !!document.querySelector('main, [role=main]');
  out.h1_count = document.querySelectorAll('h1').length;
  const named = el => { const id = el.id; if (id && document.querySelector('label[for="'+id+'"]')) return true;
    if (el.closest('label')) return true; if (el.getAttribute('aria-label') || el.getAttribute('aria-labelledby')) return true;
    return false; };
  const fields = [...document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([type=button]), select, textarea')];
  out.fields = fields.length; out.fields_unnamed = fields.filter(f => !named(f)).length;
  out.img_no_alt = [...document.querySelectorAll('img')].filter(i => !i.hasAttribute('alt')).length;
  out.btn_no_name = [...document.querySelectorAll('button')].filter(b => !b.textContent.trim() && !b.getAttribute('aria-label')).length;

  // 6) 상태 스타일(CSS 문서에서 찾기)
  let css = '';
  const walk = rules => { for (const r of rules) { css += r.cssText + '\n'; } };
  for (const ss of document.styleSheets) { try { walk(ss.cssRules); } catch(e) {} }
  out.css_chars = css.length;
  out.st_hover = /:hover/.test(css); out.st_focus = /:focus/.test(css); out.st_focus_visible = /:focus-visible/.test(css);
  out.st_disabled = /:disabled|\[disabled\]/.test(css); out.st_reduced_motion = /prefers-reduced-motion/.test(css);
  out.st_media = /@media[^{]*(max-width|min-width)/.test(css); out.st_vars = (css.match(/--[a-z0-9-]+\s*:/gi) || []).length;
  out.st_transition = /transition|animation/.test(css);
  out.has_error_ui = /error|invalid|danger|alert/i.test(document.body.innerHTML);

  // 7) 도구 설명서가 금지·경계한 패턴
  const emoji = /\p{Extended_Pictographic}/u;
  let eyebrow = 0, secnum = 0, gradText = 0, colorBorder = 0, hardShadow = 0, emojiIcons = 0, arrows = 0, upper = 0, gradBg = 0, nestedCards = 0;
  const radii = new Set();
  for (const h of document.querySelectorAll('h1,h2,h3')) { const p = h.previousElementSibling; if (!p || !visible(p)) continue;
    const cs = getComputedStyle(p); const t = p.textContent.trim();
    const up = cs.textTransform === 'uppercase' || (t.length>1 && t === t.toUpperCase() && /[A-Z]/.test(t));
    if (up && t.length < 40 && parseFloat(cs.fontSize) < parseFloat(getComputedStyle(h).fontSize)) eyebrow++; }
  for (const el of all) { const cs = getComputedStyle(el);
    const own = [...el.childNodes].filter(n => n.nodeType===3).map(n => n.textContent.trim()).join(' ');
    if (/^0[1-9]\s*([\/.\-—]|$)/.test(own) && own.length < 8) secnum++;
    if ((cs.webkitBackgroundClip === 'text' || cs.backgroundClip === 'text') && cs.backgroundImage !== 'none') gradText++;
    if (cs.backgroundImage && /gradient/.test(cs.backgroundImage)) gradBg++;
    for (const side of ['Left','Right']) { const w = parseFloat(cs['border'+side+'Width']);
      if (w >= 2 && cs['border'+side+'Style'] === 'solid') colorBorder++; }
    if (cs.boxShadow && cs.boxShadow !== 'none') { for (const m of cs.boxShadow.matchAll(/(-?\d+(?:\.\d+)?)px\s+(-?\d+(?:\.\d+)?)px\s+(\d+(?:\.\d+)?)px/g)) {
      if ((Math.abs(+m[1]) > 0 || Math.abs(+m[2]) > 0) && +m[3] === 0) { hardShadow++; break; } } }
    if (own && emoji.test(own) && own.length <= 12) emojiIcons++;
    if (/[→➜]/.test(own) && (el.tagName === 'BUTTON' || el.tagName === 'A')) arrows++;
    if (cs.textTransform === 'uppercase') upper++;
    const r = parseFloat(cs.borderTopLeftRadius); if (r > 0) radii.add(Math.round(r)); }
  // 같은 모양의 카드 3개 이상 (같은 부모, 같은 반경·그림자·테두리)
  let sameCards = 0;
  for (const parent of new Set(all.map(e => e.parentElement))) { if (!parent) continue;
    const kids = [...parent.children].filter(visible); const groups = {};
    for (const k of kids) { const cs = getComputedStyle(k); const rad = parseFloat(cs.borderTopLeftRadius);
      if (!(rad >= 6) || (cs.boxShadow === 'none' && !(parseFloat(cs.borderTopWidth) > 0))) continue;
      const key = [Math.round(rad), cs.boxShadow, cs.borderTopWidth].join('|'); groups[key] = (groups[key]||0) + 1; }
    for (const k in groups) if (groups[k] >= 3) sameCards++; }
  out.ap_eyebrow = eyebrow; out.ap_section_numbers = secnum; out.ap_gradient_text = gradText; out.ap_colored_side_border = colorBorder;
  out.ap_hard_shadow = hardShadow; out.ap_emoji_icons = emojiIcons; out.ap_arrow_text = arrows; out.ap_uppercase_labels = upper;
  out.ap_same_cards = sameCards; out.gradient_bg = gradBg; out.radius_values = radii.size;

  // 8) AI 기본 팔레트 징후 (frontend-design 설명서가 '기본값'이라고 지목한 것)
  const near = (c, t, d) => c && dist(c, t) < d;
  const cream = {r:244,g:241,b:234}, terra = {r:217,g:119,b:87};
  const bodyBg = parse(getComputedStyle(document.body).backgroundColor); const htmlBg = parse(getComputedStyle(document.documentElement).backgroundColor);
  const pageBg = (bodyBg && bodyBg.a > 0) ? bodyBg : htmlBg;
  out.tell_cream_bg = !!near(pageBg, cream, 14);
  out.tell_near_black_bg = !!(pageBg && pageBg.a > 0 && lum(pageBg) < 0.012);
  let terraUse = false; for (const el of all) { const cs = getComputedStyle(el);
    if (near(parse(cs.color), terra, 28) || near(parse(cs.backgroundColor), terra, 28)) { terraUse = true; break; } }
  out.tell_terracotta = terraUse;

  // 9) 전체 규모
  out.dom_elements = all.length;
  const allColors = new Set(); for (const el of all) { const cs = getComputedStyle(el);
    for (const p of ['color','backgroundColor','borderTopColor']) { const c = parse(cs[p]); if (c && c.a > 0) allColors.add(hex(c)); } }
  out.palette_colors = allColors.size;
  return out;
}
"""


def main():
    files = sorted(glob.glob(os.path.join(PAGES, "*.html")))
    results = []
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)
        for f in files:
            name = os.path.splitext(os.path.basename(f))[0]
            task, cond, rep = name.split("_")
            rec = {"file": name, "task": task, "cond": cond, "rep": int(rep)}
            for label, w, h in (("d", 1280, 800), ("m", 375, 800)):
                pg = b.new_page(viewport={"width": w, "height": h})
                pg.goto("file:///" + f.replace("\\", "/"))
                pg.wait_for_timeout(400)
                m = pg.evaluate(JS)
                pg.screenshot(path=os.path.join(SHOTS, f"{name}_{label}.png"), full_page=True)
                pg.close()
                for k, v in m.items():
                    if label == "m" and k in ("h_overflow", "target_lt24", "target_lt44", "interactive"):
                        rec["m_" + k] = v
                    elif label == "d":
                        rec[k] = v
            results.append(rec)
            print("측정", name, flush=True)
        b.close()
    json.dump(results, open(os.path.join(HERE, "results.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    keys = list(results[0].keys()) if results else []
    with open(os.path.join(HERE, "results.csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in results:
            w.writerow({k: (",".join(v) if isinstance(v, list) else v) for k, v in r.items()})
    print("완료", len(results), "개")


if __name__ == "__main__":
    main()
