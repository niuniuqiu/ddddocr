#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""传入验证码图片地址，GET 识别后返回结果。"""

import threading
import urllib.request
from contextlib import asynccontextmanager
from urllib.parse import urlparse

import ddddocr
import uvicorn
from fastapi import FastAPI, HTTPException, Query

ALPHANUM = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

_lock = threading.Lock()
_default_ocr: ddddocr.DdddOcr | None = None
_beta_ocr: ddddocr.DdddOcr | None = None


def _is_subsequence(short: str, long: str) -> bool:
    it = iter(long)
    return all(char in it for char in short)


def _merge(default_text: str, beta_text: str) -> str:
    """长度不固定：一边只是另一边漏字时，保留更完整的那条。"""
    if default_text == beta_text:
        return default_text
    if len(default_text) >= len(beta_text) and _is_subsequence(beta_text, default_text):
        return default_text
    if len(beta_text) > len(default_text) and _is_subsequence(default_text, beta_text):
        return beta_text
    return default_text


def _fetch_image(url: str) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("url 需要是 http 或 https 图片地址")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        data = response.read()
    if not data:
        raise RuntimeError("验证码图片为空")
    return data


def _recognize(image: bytes) -> str:
    with _lock:
        default_text = _default_ocr.classification(image)
        beta_text = _beta_ocr.classification(image)
    return _merge(default_text, beta_text)


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    global _default_ocr, _beta_ocr
    _default_ocr = ddddocr.DdddOcr(show_ad=False)
    _beta_ocr = ddddocr.DdddOcr(beta=True, show_ad=False)
    # 只限制字符种类，不限制长度；颜色每次都变，不做颜色过滤
    _default_ocr.set_ranges(ALPHANUM)
    _beta_ocr.set_ranges(ALPHANUM)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Captcha OCR", lifespan=_lifespan)

    @app.get("/captcha")
    def get_captcha(
        url: str = Query(..., description="验证码图片地址"),
    ) -> dict[str, str]:
        try:
            image = _fetch_image(url)
            captcha = _recognize(image)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"识别失败: {exc}") from exc
        return {"captcha": captcha}

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8521)
