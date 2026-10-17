import io, os, shutil, sys

# 数据目录（容器内是 /data；宿主机是绑定目录）。可用环境变量 MB_DATA 覆盖，再指定版本目录。
import glob as _g
_root = os.environ.get('MB_DATA', '/data')
_cand = sorted(_g.glob(os.path.join(_root, 'app', '*', 'server', 'modules', 'emby', 'routes.js')), reverse=True)
P = _cand[0] if _cand else os.path.join(_root, 'app', 'current', 'server', 'modules', 'emby', 'routes.js')
NEEDLE = "    if (!metaBridge.parseItemId(params.itemId)) return notImplemented(req, res, { pathname, query });"

PATCH = """    /* 首页行（mbphome_*）不是「条目」，但客户端（如 RodelPlayer）会把它当媒体库点开并请求详情 ——
     * 这里回「库里那一行」本身的 DTO（与 Views 里同一份形状），客户端随后用 ParentId 列内容。 */
    if (String(params.itemId || '').startsWith('mbphome_')) {
      const views = service.getViews();
      const hit = ((views && views.body && views.body.Items) || []).find((x) => x.Id === params.itemId);
      if (hit) {
        log.logResult(req, `首页库详情 Users/…/Items/${params.itemId}`, { status: 200 }, q);
        return sendJson(res, 200, hit);
      }
    }

"""

src = io.open(P, encoding='utf-8').read()
if 'mbphome_' in src and '首页库详情' in src:
    print('已经打过补丁，跳过')
    sys.exit(0)

if NEEDLE not in src:
    print('没找到锚点，未修改')
    sys.exit(1)

if not os.path.exists(P + '.orig'):
    shutil.copy2(P, P + '.orig')
    print('已备份 routes.js.orig')

src = src.replace(NEEDLE, PATCH + NEEDLE, 1)
io.open(P, 'w', encoding='utf-8').write(src)
print('补丁已写入')
