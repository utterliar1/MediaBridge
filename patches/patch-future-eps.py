"""面板补丁：分集列表里不列「未播出」的集（幂等，可重复运行）。

规则两条：
  1. premiereDate 晚于现在 → 丢掉
  2. 末尾没有 premiereDate 的占位集（TMDB 会给未播集建空条目）→ 丢掉
     （判据：它排在本季最后一个**有日期**的集之后；整季都没日期时不动）

面板升级会替换 /data/app/<版本>/ → 升级后重跑本脚本。
"""
import io, os, glob
import os
import re
import shutil
import sys

APP = os.environ.get('MB_DATA', '/data') + '/app'
JS = None
for name in sorted(os.listdir(APP), reverse=True):
    p = os.path.join(APP, name, 'server', 'modules', 'emby', 'service.js')
    if os.path.exists(p):
        JS = p
        break
if not JS:
    print('找不到 service.js')
    sys.exit(1)
print('目标：', JS)

NEW = """  const items = (look.item.episodes || [])
    .filter((e) => Number.isFinite(e.episodeNumber))
    /* 未播出的集不列：
     *   ① premiereDate 晚于现在 → 丢掉（客户端点开是空壳）
     *   ② 末尾没有 premiereDate 的占位集（TMDB 会给未播集建空条目）→ 丢掉
     * 整季都没有日期时按 ① 无从判断，就原样保留。 */
    .filter((e, _i, arr) => {
      const t = Date.parse(e.premiereDate || '');
      if (Number.isFinite(t)) return t <= Date.now();
      const dated = arr.filter((x) => Number.isFinite(Date.parse(x.premiereDate || '')));
      if (!dated.length) return true;
      const lastDated = Math.max(...dated.map((x) => x.episodeNumber));
      return e.episodeNumber <= lastDated;
    })"""

src = io.open(JS, encoding='utf-8').read()

# 先把可能存在的旧补丁还原
if '未播出的集不列' in src and os.path.exists(JS + '.orig'):
    shutil.copy2(JS + '.orig', JS)
    src = io.open(JS, encoding='utf-8').read()
    print('已还原旧补丁')

ANCHOR = """  const items = (look.item.episodes || [])
    .filter((e) => Number.isFinite(e.episodeNumber))"""

if NEW in src:
    print('已是最新补丁，跳过')
    sys.exit(0)
if ANCHOR not in src:
    print('没找到锚点，未修改')
    sys.exit(1)
if not os.path.exists(JS + '.orig'):
    shutil.copy2(JS, JS + '.orig')
    print('已备份 service.js.orig')
io.open(JS, 'w', encoding='utf-8').write(src.replace(ANCHOR, NEW, 1))
print('补丁已写入')
