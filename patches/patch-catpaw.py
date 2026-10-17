"""给 catpaw-resolve 打两个补丁（幂等，含 plugin.json md5 同步）：

1. 百度优先：expandLines 里按 百度 → 夸克 → 其他 排序
2. 综艺兜底：locateEpisode 里，当整条线路的集名都是「日期 / 第N期」这类
   与 TMDB 集号无法对应的格式时，按位置取第 N 个（否则综艺永远定位不到）

面板/插件升级后重跑一次即可。
"""
import hashlib, os, glob
import io
import json
import os
import shutil
import sys

DIR = os.path.join(os.environ.get('MB_DATA', '/data'), 'plugins', 'catpaw-resolve')
JS = os.path.join(DIR, 'index.js')
LINES = os.path.join(DIR, 'lib', 'lines.js')
PJ = os.path.join(DIR, 'plugin.json')

# ---------- 1) 百度优先（index.js）
A1 = "  detail.lines = keep;\n  detail.lineCount = keep.length;"
P1 = """  /* 优先百度：用户只要百度/夸克，且百度排最前（客户端默认播第一条版本）。
   * 夸克次之，其余（秒播/直链）最后。 */
  const rankOf = (l) => (/百度/.test(String(l.flag)) ? 0 : /夸克/.test(String(l.flag)) ? 1 : 2);
  keep.sort((a, b) => rankOf(a) - rankOf(b));

"""

src = io.open(JS, encoding='utf-8').read()
if '优先百度：用户只要百度/夸克' in src:
    print('index.js：百度优先已存在')
else:
    if A1 not in src:
        print('index.js：没找到锚点，跳过')
    else:
        if not os.path.exists(JS + '.orig'):
            shutil.copy2(JS, JS + '.orig')
            print('已备份 index.js.orig')
        io.open(JS, 'w', encoding='utf-8').write(src.replace(A1, P1 + A1, 1))
        print('index.js：百度优先已写入')

# ---------- 2) 综艺兜底（lib/lines.js）
A2 = "  return null;\n}\n\nmodule.exports = { parseLines, parseEpisodeTitle, looseEpisodeNumber, locateEpisode };"
P2 = """  /* ④ 综艺兜底：整条线路的集名都是「日期 / 第N期」这类（与 TMDB 集号对不上）时，
   * 按**位置**取第 N 个 —— 否则综艺永远定位不到（实测《毛雪汪》：源里只有 2026 年的第 140 期起，
   * TMDB 的 E1 在源里不存在）。只对这类命名生效，普通剧集不受影响。 */
  const isVariety = (line) => {
    const eps = line.episodes || [];
    if (!eps.length) return false;
    const hitCount = eps.filter((ep) => /(20\\d{6})|第\\s*\\d+\\s*期/.test(String(ep.name))).length;
    return hitCount / eps.length >= 0.5;
  };
  if (lines.some(isVariety)) {
    for (const line of lines) {
      if (!isVariety(line)) continue;
      const ep = (line.episodes || [])[e - 1];
      if (ep) return hit(line, ep, 'position');
    }
  }
  return null;
}

module.exports = { parseLines, parseEpisodeTitle, looseEpisodeNumber, locateEpisode };"""

src = io.open(LINES, encoding='utf-8').read()
if '综艺兜底' in src:
    print('lines.js：综艺兜底已存在')
else:
    if A2 not in src:
        print('lines.js：没找到锚点，跳过')
    else:
        if not os.path.exists(LINES + '.orig'):
            shutil.copy2(LINES, LINES + '.orig')
            print('已备份 lines.js.orig')
        io.open(LINES, 'w', encoding='utf-8').write(src.replace(A2, P2, 1))
        print('lines.js：综艺兜底已写入')

# ---------- 3) 同步 plugin.json 的 md5
d = json.load(open(PJ, encoding='utf-8'))
files = d.setdefault('files', {})
for rel, path in (('index.js', JS), ('lib/lines.js', LINES)):
    if os.path.exists(path):
        files[rel] = hashlib.md5(open(path, 'rb').read()).hexdigest()
json.dump(d, open(PJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('plugin.json md5 已同步:', {k: v[:8] for k, v in files.items() if k in ('index.js', 'lib/lines.js')})
