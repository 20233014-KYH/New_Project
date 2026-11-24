// 시험 8 채점기. 사용: node grade.js d1|d3 <index.html 경로> <결과 json 경로> [스크린샷 png 경로]
// d1: 심어 둔 결함 10개를 고쳤는지 + 내용이 그대로인지 / d3: "흔한 AI 모양" 지표 개수 (낮을수록 덜 흔함)
// 채점은 계산된 화면(브라우저)으로 한다. impeccable 자체 검사 규칙은 impeccable에 유리할 수 있어 쓰지 않는다.
const path = require('path');
const fs = require('fs');
const NM = process.env.NM || path.join(__dirname, 'node_modules');
const { chromium } = require(path.join(NM, 'playwright-core'));
const AXE = fs.readFileSync(path.join(NM, 'axe-core', 'axe.min.js'), 'utf8');
const [mode, file, out, shot] = process.argv.slice(2);

const D1_TEXT = ['계정 설정', '프로필', '알림', '보안', '이메일 알림 받기', '주간 요약 받기', '비밀번호 바꾸기', '탈퇴하기', '취소', '저장', '사진 바꾸기'];

(async () => {
  const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await page.goto('file:///' + path.resolve(file).replace(/\\/g, '/'), { waitUntil: 'networkidle', timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(500);
  if (shot) await page.screenshot({ path: shot, fullPage: true });
  await page.addScriptTag({ content: AXE });
  const axe = await page.evaluate(async () => {
    const r = await window.axe.run(document, { runOnly: { type: 'rule', values: ['color-contrast', 'image-alt', 'label', 'heading-order', 'target-size'] } });
    const o = {};
    r.violations.forEach(v => { o[v.id] = v.nodes.length; });
    return o;
  });
  const css = await page.evaluate(() => {
    const els = [...document.querySelectorAll('body *')].filter(e => {
      const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0;
    });
    const px = [];
    const fonts = new Set();
    let rounded = 0, shadow = 0, blocks = 0;
    const grads = [];
    for (const e of [document.documentElement, document.body, ...els]) {
      const s = getComputedStyle(e);
      for (const k of ['marginTop', 'marginBottom', 'marginLeft', 'marginRight', 'paddingTop', 'paddingBottom', 'paddingLeft', 'paddingRight', 'rowGap', 'columnGap']) {
        const v = parseFloat(s[k]);
        if (v > 0 && s[k].endsWith('px')) px.push(v);
      }
      if (e.childNodes && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) fonts.add(s.fontFamily.split(',')[0].trim().replace(/["']/g, '').toLowerCase());
      if (s.backgroundImage && s.backgroundImage.includes('gradient')) grads.push(s.backgroundImage);
      if (['DIV', 'SECTION', 'ARTICLE', 'BUTTON', 'A', 'LI', 'IMG', 'FIGURE', 'ASIDE', 'HEADER', 'FOOTER', 'NAV', 'FORM'].includes(e.tagName)) {
        blocks++;
        if (parseFloat(s.borderTopLeftRadius) > 0) rounded++;
        if (s.boxShadow && s.boxShadow !== 'none') shadow++;
      }
    }
    const targets = [...document.querySelectorAll('button, a, [role=button]')].filter(e => e.getBoundingClientRect().width > 0)
      .map(e => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), e.textContent.trim().slice(0, 20)]; });
    const text = document.body.innerText;
    return {
      px, fonts: [...fonts], grads, rounded, shadow, blocks, targets, text,
      imgs: document.querySelectorAll('img, svg[role=img]').length,
      inputs: document.querySelectorAll('input').length,
      buttons: document.querySelectorAll('button, a[role=button], [role=button]').length,
      hasSystemOnly: [...fonts].every(f => /inter|system-ui|-apple-system|segoe ui|roboto|helvetica|arial|sans-serif/.test(f)),
      // ©·®·™ 같은 기호는 빼고 진짜 이모지(🔔, ⚙️ 등)만 센다
      emoji: (text.match(/\p{Emoji_Presentation}|\p{Extended_Pictographic}️/gu) || []).length,
    };
  });
  // 키보드 초점 표시: Tab으로 옮기며 초점 받은 버튼·링크에 눈에 보이는 표시가 있는지
  const focus = [];
  for (let i = 0; i < 25; i++) {
    await page.keyboard.press('Tab');
    const f = await page.evaluate(() => {
      const e = document.activeElement;
      if (!e || e === document.body) return null;
      if (!['BUTTON', 'A'].includes(e.tagName) && e.getAttribute('role') !== 'button') return { skip: true };
      const s = getComputedStyle(e);
      const ring = (s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0) || (s.boxShadow && s.boxShadow !== 'none');
      return { tag: e.tagName, text: e.textContent.trim().slice(0, 15), ring };
    });
    if (f && !f.skip) focus.push(f);
  }
  await browser.close();

  const mult4 = css.px.filter(v => Math.abs(v / 4 - Math.round(v / 4)) < 0.13).length / Math.max(1, css.px.length);
  const purpleGrad = css.grads.some(g => (g.match(/rgba?\([^)]+\)/g) || []).some(c => {
    const [r, gg, b] = c.match(/[\d.]+/g).map(Number);
    const mx = Math.max(r, gg, b), mn = Math.min(r, gg, b);
    if (mx - mn < 40) return false;
    let h;
    if (mx === r) h = 60 * (((gg - b) / (mx - mn)) % 6); else if (mx === gg) h = 60 * ((b - r) / (mx - mn) + 2); else h = 60 * ((r - gg) / (mx - mn) + 4);
    if (h < 0) h += 360;
    return h >= 220 && h <= 320; // 파랑~보라
  }));
  let res;
  if (mode === 'd1') {
    const missing = D1_TEXT.filter(t => !css.text.includes(t));
    const checks = {
      '1 글자 대비': !axe['color-contrast'],
      '2 이미지 설명(alt)': !axe['image-alt'] && css.imgs >= 1,
      '3 키보드 초점 표시': focus.length > 0 && focus.every(f => f.ring),
      '4 입력칸 이름표(label)': !axe['label'],
      '5 제목 순서': !axe['heading-order'],
      '6 누르는 크기 44px 이상': css.targets.length > 0 && css.targets.every(([w, h]) => w >= 44 && h >= 44),
      '7 간격 4px 배수 90% 이상': mult4 >= 0.9,
      '8 글꼴 2종 이하': css.fonts.length <= 2,
      '9 이모지 아이콘 없음': css.emoji === 0,
      '10 보라 그라데이션 없음': !purpleGrad,
    };
    const contentOk = missing.length === 0 && css.inputs >= 5 && css.buttons >= 5;
    res = { mode, score: Object.values(checks).filter(Boolean).length, checks, contentOk, missing, inputs: css.inputs, buttons: css.buttons,
      detail: { axe, mult4: +mult4.toFixed(2), fonts: css.fonts, focus, smallTargets: css.targets.filter(([w, h]) => w < 44 || h < 44) } };
  } else {
    const flags = {
      'Inter·기본 글꼴만 씀': css.hasSystemOnly,
      '파랑·보라 그라데이션': purpleGrad,
      '이모지 아이콘': css.emoji > 0,
      '둥근 모서리+그림자가 대부분': css.blocks > 0 && css.rounded / css.blocks >= 0.5 && css.shadow / css.blocks >= 0.3,
    };
    res = { mode, aiLook: Object.values(flags).filter(Boolean).length, flags, a11y: axe,
      detail: { fonts: css.fonts, rounded: css.rounded, shadow: css.shadow, blocks: css.blocks, emoji: css.emoji, mult4: +mult4.toFixed(2) } };
  }
  fs.writeFileSync(out, JSON.stringify(res, null, 1));
  console.log(JSON.stringify(mode === 'd1' ? { score: res.score, contentOk: res.contentOk } : { aiLook: res.aiLook }));
})();
