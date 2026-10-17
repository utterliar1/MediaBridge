# 本地改动与配置层清单（相对上游 dlushu/MediaBridge v1.9.7）

本 fork 在上游基础上做了两类东西：**代码修复**（已提交为本仓库 commit）和**闭源插件的运行时补丁**（见 `patches/`）。
不包含任何账号、密码、域名或内网地址。

## 代码改动（已在 main 分支）

| commit | 文件 | 内容 |
|---|---|---|
| 修：首页库行被当条目请求详情时回 501 | `server/modules/emby/routes.js` | 首页分类行是 `mbphome_*` 伪条目，客户端点开请求详情 → 回 Views 同款 DTO，200 |
| 增强：分集列表不列未播出的集 | `server/modules/emby/service.js` | `getEpisodes` 过滤：premiereDate 晚于现在丢；无日期且在最后有日期的集之后丢；整季无日期不过滤 |

面板升级会整体替换应用目录，这两个改动以 commit 维护在本仓库，升级后需要对上游新代码重放（`git cherry-pick` 或手动）。

## 闭源插件 catpaw-resolve（只能打运行时补丁）

见 `patches/patch-catpaw.py`：网盘线路优先级排序、综艺「日期/第N期」集名按位置兜底、
`plugin.json` 的 `files.*` md5 同步。**每次插件升级后重跑**。

## 配置层（不在代码里，重建环境时照做）

- **模板**（聚合站）：timeoutSec 8 / detailTimeoutSec 25 / playTimeoutSec 40 / concurrency 10 / `matchMinScore 0.85` / `matchMaxItems 1` / `lineFilter "^(?!.*(UC|115|阿里|天翼|迅雷|PikPak|123|移动|光鸭|转码))"` —— 排除法而非白名单，避免误杀秒播线路
- **实例**：homePlugin 指向自建 home 插件（guoyu）；metaDomains=`["tmdb","hongguo"]`
- **源实例**：catpaw（秒播站）与 catpaw-resolve（网盘站）必须**分开**，后者不回落 /play
- **播放中继**：`forwardEnabled=false`（本地中继），threads 16 / chunkKB 2048
- **TMDB 插件**：只认 v4 Read Access Token（Bearer），v3 key 无效

## 自建 home 插件 guoyu

独立仓库维护（不在本仓库内）：TMDB discover 分库（按语言/类型/年窗），设置页可自定义每个库，
行数据存插件 `data/settings.json`。
