# patches/ —— 本地运行时补丁存档

面板本体与插件的**升级会覆盖运行目录**（面板是 `/data/app/<版本>/`，插件是重新解包的目录），
所以持续生效的改动以幂等脚本形式保存在这里，升级后重跑即可。

```bash
# 路径约定：容器数据目录。宿主机上是绑定目录（如 NAS 上的 docker/media-bridge/data）。
# 不在默认位置时用环境变量指定：
export MB_DATA=/vol1/1000/docker/media-bridge/data

python3 patches/patch-homeview.py     # 面板：修复首页分类点开 501（main 分支已含同款代码改动，仅老版本需要）
python3 patches/patch-future-eps.py   # 面板：分集列表不列未播出的集（main 分支已含同款代码改动，仅老版本需要）
python3 patches/patch-catpaw.py      # 插件 catpaw-resolve（闭源产物，只能打补丁）
```

三个脚本均为幂等：重复执行安全；面板脚本会先还原 `.orig` 备份再打最新版补丁。

## patch-catpaw.py 的改动内容

1. **网盘线路优先级**：`lib/lines.js` 的 `expandLines()` 对解析出的线路排序
   （目标网盘 → 备选 → 其他），让客户端默认列表第一项是想要的主网盘。
2. **综艺定位兜底**：`lib/lines.js` 的 `locateEpisode()` 末尾追加第 ④ 条规则 ——
   整条线路 ≥50% 的集名形如「YYYYMMDD」或「第N期」时，按**位置**取第 N 个
   （`matchedBy: 'position'`）。普通剧集不受影响。
   限制：位置匹配 ≠ 内容匹配，且源站只留最近若干期时，超出范围的集仍无版本。
3. **md5 同步**：上述文件改动后同步更新 `plugin.json` 的 `files.*` 校验值，
   否则插件启动校验失败、状态变 `broken`。
