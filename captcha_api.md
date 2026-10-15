# 验证码识别接口运行说明

传入一张验证码图片地址，服务会下载图片并返回识别结果。字符颜色不固定，所以不做颜色过滤。验证码长度不固定，所以不限制返回位数。识别范围是大小写字母和数字。

## 环境

需要 Python 3.10 及以上。本仓库已有虚拟环境 `.venv`。

首次使用时，在项目根目录安装依赖：

```bash
cd /Users/sell/code/ddddocr
python3 -m venv .venv
.venv/bin/pip install -e ".[api]"
```

## 启动

```bash
cd /Users/sell/code/ddddocr
.venv/bin/python captcha_api.py
```

看到 `Uvicorn running on http://0.0.0.0:8521` 后即可调用。服务监听 `0.0.0.0:8521`，本机用 `127.0.0.1:8521`，Docker 里的 PHP 用 `host.docker.internal:8521`。第一次启动会加载模型，稍等几秒再请求。

停止服务：在运行该命令的终端按 `Ctrl+C`。

## 调用

```
GET /captcha?url=<验证码图片地址>&cookie=<可选，会话 Cookie>
POST /captcha
```

`GET` 的 `url` 必填，且必须是 `http` 或 `https` 地址。地址里如果含有 `?`、`&`、`=`，先做 URL 编码再放进参数。Lightlayer 的验证码跟登录会话绑定，只传图片地址会识别到另一张图；要么带上同一次登录的 `cookie`，要么用 `POST` 直接提交已经下载好的图片二进制。

示例：

```bash
curl -G "http://127.0.0.1:8521/captcha" \
  --data-urlencode "url=https://account.lightlayer.net/index.php?cmd=root&action=captcha" \
  --data-urlencode "cookie=SESSID4ba1=..."

curl -X POST "http://127.0.0.1:8521/captcha" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @captcha.jpg
```

成功时返回：

```json
{"captcha":"462x"}
```

## 返回状态

| 状态码 | 含义 |
|---|---|
| 200 | 识别成功，`captcha` 为识别出的字符串 |
| 400 | `url` 不是 http 或 https 地址，或 POST 的图片为空 |
| 422 | 没有传 `url` |
| 502 | 图片下载失败，或图片无法识别 |
