import sys
import json
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Depends, Header, File, UploadFile, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.core.config import settings
from app.providers.vheer_provider import VheerProvider, BrowserManager

# --- 日志配置 ---
logger.remove()
# --- FIX: 将日志级别调整为 TRACE 以输出最详细的步骤信息 ---
logger.add(
    sys.stdout,
    level="TRACE",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True
)

# --- 全局实例 ---
browser_manager = BrowserManager()
provider = VheerProvider(browser_manager)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"应用启动中... {settings.APP_NAME} v{settings.APP_VERSION}")
    await browser_manager.start_browser()
    logger.info("服务已进入 'Headless-Browser-Proxy-Execution' 模式。")
    logger.info(f"API 服务将在 http://localhost:{settings.NGINX_PORT} 上可用")
    logger.info(f"Web UI 测试界面已启用，请访问 http://localhost:{settings.NGINX_PORT}/")
    yield
    await browser_manager.close_browser()
    logger.info("应用关闭。")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="static"), name="static")

async def verify_api_key(authorization: Optional[str] = Header(None)):
    if settings.API_MASTER_KEY and settings.API_MASTER_KEY != "1":
        if not authorization or "bearer" not in authorization.lower():
            raise HTTPException(status_code=401, detail="需要 Bearer Token 认证。")
        token = authorization.split(" ")[-1]
        if token != settings.API_MASTER_KEY:
            raise HTTPException(status_code=403, detail="无效的 API Key。")

@app.post("/v1/images/generations", dependencies=[Depends(verify_api_key)])
async def text_to_image(request: Request):
    try:
        request_data = await request.json()
        # --- ADD: 增加详细的请求载荷日志 ---
        logger.debug(f"收到 /v1/images/generations 请求，载荷: \n{json.dumps(request_data, ensure_ascii=False, indent=2)}")
        response = await provider.generate_from_text(request_data)
        # --- ADD: 增加详细的响应日志 ---
        if isinstance(response, JSONResponse):
             logger.debug(f"准备返回响应，内容: \n{json.dumps(response.body.decode('utf-8'), ensure_ascii=False, indent=2)}")
        return response
    except Exception as e:
        logger.error(f"处理文生图请求时出错: {e}", exc_info=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {e}")

@app.post("/v1/images/edits", dependencies=[Depends(verify_api_key)])
async def image_to_image(
    image: UploadFile = File(...),
    prompt: str = Form(...),
    model: str = Form("vheer-image-to-image"),
    creative_strength: int = Form(10),
    control_strength: int = Form(2)
):
    try:
        # --- ADD: 增加详细的请求载荷日志 ---
        logger.debug(f"收到 /v1/images/edits 请求: prompt='{prompt}', model='{model}', creative_strength={creative_strength}, control_strength={control_strength}, image='{image.filename}'")
        image_bytes = await image.read()
        response = await provider.generate_from_image(
            prompt=prompt,
            image_bytes=image_bytes,
            creative_strength=creative_strength,
            control_strength=control_strength
        )
        if isinstance(response, JSONResponse):
             logger.debug(f"准备返回响应，内容: \n{json.dumps(response.body.decode('utf-8'), ensure_ascii=False, indent=2)}")
        return response
    except Exception as e:
        logger.error(f"处理图生图请求时出错: {e}", exc_info=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {e}")

@app.post("/v1/video/generations", dependencies=[Depends(verify_api_key)])
async def image_to_video(
    image: UploadFile = File(...)
):
    try:
        # --- ADD: 增加详细的请求载荷日志 ---
        logger.debug(f"收到 /v1/video/generations 请求: image='{image.filename}'")
        image_bytes = await image.read()
        response = await provider.generate_video_from_image(image_bytes=image_bytes)
        if isinstance(response, JSONResponse):
             logger.debug(f"准备返回响应，内容: \n{json.dumps(response.body.decode('utf-8'), ensure_ascii=False, indent=2)}")
        return response
    except Exception as e:
        logger.error(f"处理图生视频请求时出错: {e}", exc_info=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {e}")

@app.get("/v1/models", dependencies=[Depends(verify_api_key)])
async def list_models():
    return await provider.get_models()

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_ui():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="UI 文件 (static/index.html) 未找到。")
