import asyncio
import time
import json
from typing import Dict, Any, Optional
from pathlib import Path
import tempfile

from loguru import logger
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright, Browser, Page, BrowserContext, TimeoutError as PlaywrightTimeoutError

from app.core.config import settings

class BrowserManager:
    """管理 Playwright 浏览器实例和并发锁。"""
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.lock = asyncio.Lock()

    async def start_browser(self):
        logger.info("正在启动 Playwright 浏览器...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        
        cookies = []
        if settings.VHEER_COOKIE:
            cookie_parts = settings.VHEER_COOKIE.split(';')
            for part in cookie_parts:
                if '=' in part:
                    name, value = part.strip().split('=', 1)
                    cookies.append({"name": name, "value": value, "domain": ".vheer.com", "path": "/"})
        
        self.context = await self.browser.new_context()
        if cookies:
            await self.context.add_cookies(cookies)
            logger.success("浏览器启动并已设置 Cookie。")
        else:
            logger.warning("VHEER_COOKIE 未设置，浏览器未加载任何 Cookie。")

    async def new_page(self) -> Page:
        if not self.context:
            raise RuntimeError("浏览器上下文未初始化。")
        return await self.context.new_page()

    async def close_browser(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("浏览器已关闭。")


class VheerProvider:
    def __init__(self, browser_manager: BrowserManager):
        self.browser_manager = browser_manager

    async def _execute_in_browser(self, task_coro):
        """带锁执行浏览器任务的通用包装器。"""
        async with self.browser_manager.lock:
            page = None
            try:
                result = await asyncio.wait_for(task_coro(), timeout=settings.API_REQUEST_TIMEOUT + 120)
                return result
            except asyncio.TimeoutError:
                logger.error(f"浏览器任务因总超时而失败（超过 {settings.API_REQUEST_TIMEOUT + 120} 秒）。")
                raise HTTPException(status_code=504, detail="上游服务响应超时。")
            except PlaywrightTimeoutError as e:
                logger.error(f"Playwright 操作超时: {e}", exc_info=True)
                raise HTTPException(status_code=502, detail=f"与上游服务交互超时: {e}")
            except Exception as e:
                logger.error(f"浏览器任务执行时发生未知错误: {e}", exc_info=True)
                raise HTTPException(status_code=502, detail=f"与上游服务交互时出错: {e}")

    async def _create_page_with_logging(self) -> Page:
        """创建一个新页面并附加详细的网络日志记录器。"""
        page = await self.browser_manager.new_page()
        logger.debug("--- [网络日志记录器已激活] ---")
        
        async def log_request(request):
            if "data:image" not in request.url and "google" not in request.url and "ezoic" not in request.url and "quantserve" not in request.url:
                post_data = request.post_data or "N/A"
                logger.trace(f"==> [请求] {request.method} {request.url} | 载荷: {post_data[:300]}")

        async def log_response(response):
            if "data:image" not in response.url and "google" not in response.url and "ezoic" not in response.url and "quantserve" not in response.url:
                status = response.status
                try:
                    body = await response.text()
                    log_body = body[:500].strip() + "..." if len(body) > 500 else body.strip()
                except Exception:
                    log_body = "[二进制或无法解析的响应体]"
                logger.trace(f"<== [响应] {status} {response.url} | 响应体: {log_body}")

        page.on("request", lambda req: asyncio.create_task(log_request(req)))
        page.on("response", lambda res: asyncio.create_task(log_response(res)))
        return page

    async def _wait_for_result_url(self, page: Page, target_url_prefix: str, media_suffix: tuple) -> str:
        """
        最终决战方案：通过监听网络响应来获取结果URL。
        这个方法结合了两种策略：
        1. 主要策略：监听发往 vheer.com/app/... 的 POST 请求响应，解析其中的 JSON 数据，寻找成功状态和下载链接。
        2. 后备策略：监听对最终媒体文件（.jpg, .mp4）的直接请求。
        """
        result_future = asyncio.Future()
        
        async def handle_response(response):
            # 主要策略：捕获包含成功状态的JSON响应
            if response.url.startswith(target_url_prefix) and response.request.method == "POST":
                try:
                    text = await response.text()
                    # 响应可能是多行，我们需要找到包含JSON的部分
                    for line in text.splitlines():
                        if '"message":"Success"' in line and '"status":"success"' in line:
                            json_start = line.find('{')
                            if json_start != -1:
                                json_text = line[json_start:]
                                data = json.loads(json_text)
                                download_urls = data.get("data", {}).get("downloadUrls")
                                if download_urls and not result_future.done():
                                    logger.success(f"【主要方案】拦截成功! 从JSON心跳包中提取到URL: {download_urls[0]}")
                                    result_future.set_result(download_urls[0])
                                    return
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass  # 忽略解析失败或结构不符的响应

            # 后备策略：捕获对媒体文件的直接请求
            if "access.vheer.com/results/" in response.url and response.url.endswith(media_suffix) and not result_future.done():
                logger.success(f"【后备方案】拦截成功! 监听到最终媒体文件URL: {response.url}")
                result_future.set_result(response.url)

        page.on("response", lambda res: asyncio.create_task(handle_response(res)))
        
        logger.info("正在等待结果URL... (将持续检查，最长5分钟)")
        try:
            # 我们在这里等待，而不是在页面上寻找元素
            result_url = await asyncio.wait_for(result_future, timeout=settings.API_REQUEST_TIMEOUT)
            return result_url
        except asyncio.TimeoutError:
            logger.error("在指定时间内未能通过网络监听捕获到任何有效的结果URL。")
            raise

    async def generate_from_text(self, request_data: Dict[str, Any]) -> JSONResponse:
        async def task():
            page = await self._create_page_with_logging()
            try:
                prompt = request_data.get("prompt")
                size = request_data.get("size", "1:1")
                
                logger.debug(">>> [START] 浏览器任务: 文生图")
                await page.goto("https://vheer.com/app/text-to-image", wait_until="networkidle")
                logger.debug("步骤 1/4: 页面导航完成。")

                prompt_selector = 'textarea[placeholder*="Steampunk flying bicycle"]'
                await page.wait_for_selector(prompt_selector, timeout=30000)
                await page.fill(prompt_selector, prompt)
                logger.debug("步骤 2/4: 提示词已填入。")

                aspect_ratio_dropdown_selector = 'button#hs-dropdown-hover-event'
                aspect_ratio_option_selector = f'div.hs-dropdown-menu div.p-1 div:has-text("{size}")'
                await page.click(aspect_ratio_dropdown_selector)
                await page.click(aspect_ratio_option_selector)
                logger.debug(f"步骤 3/4: 图片比例 '{size}' 已选择。")

                await page.click('button:has-text("Generate")')
                logger.debug("步骤 4/4: 'Generate' 按钮已点击，开始监听网络以捕获结果...")

                result_url = await self._wait_for_result_url(page, "https://vheer.com/app/text-to-image", (".jpg", ".png", ".webp"))
                
                response_data = {"created": int(time.time()), "data": [{"url": result_url}]}
                logger.success("<<< [SUCCESS] 浏览器任务: 文生图已完成。")
                return JSONResponse(content=response_data)
            finally:
                if page and not page.is_closed(): await page.close()
        return await self._execute_in_browser(task)

    async def generate_from_image(self, prompt: str, image_bytes: bytes, creative_strength: int, control_strength: int) -> JSONResponse:
        async def task():
            page = await self._create_page_with_logging()
            try:
                logger.debug(">>> [START] 浏览器任务: 图生图")
                await page.goto("https://vheer.com/app/image-to-image", wait_until="networkidle")
                logger.debug("步骤 1/6: 页面导航完成。")

                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                    tmp_file.write(image_bytes)
                    tmp_file_path = tmp_file.name
                
                await page.set_input_files('input[type="file"]', tmp_file_path)
                logger.debug("步骤 2/6: 图片已提交上传。")
                
                processing_overlay_selector = 'div:has-text("Processing...")'
                await page.wait_for_selector(processing_overlay_selector, state='hidden', timeout=60000)
                logger.debug("步骤 3/6: 图片处理完成。")

                prompt_selector = 'div:has-text("Positive prompts") >> textarea'
                await page.wait_for_selector(prompt_selector, timeout=30000)
                await page.fill(prompt_selector, prompt)
                logger.debug("步骤 4/6: 提示词已填入。")

                await page.evaluate(f"document.getElementById('creative-strength').value = {creative_strength}; document.getElementById('creative-strength').dispatchEvent(new Event('input', {{ 'bubbles': true }}));")
                await page.evaluate(f"document.getElementById('control-strength').value = {control_strength}; document.getElementById('control-strength').dispatchEvent(new Event('input', {{ 'bubbles': true }}));")
                logger.debug("步骤 5/6: 滑块值设置完成。")
                
                await page.click('button:has-text("Generate")')
                logger.debug("步骤 6/6: 'Generate' 按钮已点击，开始监听网络以捕获结果...")

                result_url = await self._wait_for_result_url(page, "https://vheer.com/app/image-to-image", (".jpg", ".png", ".webp"))

                Path(tmp_file_path).unlink()
                response_data = {"created": int(time.time()), "data": [{"url": result_url}]}
                logger.success("<<< [SUCCESS] 浏览器任务: 图生图已完成。")
                return JSONResponse(content=response_data)
            finally:
                if page and not page.is_closed(): await page.close()
        return await self._execute_in_browser(task)

    async def generate_video_from_image(self, image_bytes: bytes) -> JSONResponse:
        async def task():
            page = await self._create_page_with_logging()
            try:
                logger.debug(">>> [START] 浏览器任务: 图生视频")
                await page.goto("https://vheer.com/app/image-to-video", wait_until="networkidle")
                logger.debug("步骤 1/3: 页面导航完成。")

                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                    tmp_file.write(image_bytes)
                    tmp_file_path = tmp_file.name

                await page.set_input_files('input[type="file"]', tmp_file_path)
                logger.debug("步骤 2/3: 图片上传完成。")

                await page.click('button:has-text("Generate")')
                logger.debug("步骤 3/3: 'Generate' 按钮已点击，开始监听网络以捕获结果...")

                result_url = await self._wait_for_result_url(page, "https://vheer.com/app/image-to-video", (".mp4",))

                Path(tmp_file_path).unlink()
                response_data = {"created": int(time.time()), "data": [{"url": result_url}]}
                logger.success("<<< [SUCCESS] 浏览器任务: 图生视频已完成。")
                return JSONResponse(content=response_data)
            finally:
                if page and not page.is_closed(): await page.close()
        return await self._execute_in_browser(task)

    async def get_models(self) -> JSONResponse:
        model_list = {
            "object": "list",
            "data": [{"id": name, "object": "model", "created": int(time.time()), "owned_by": "vheer-2api"} for name in settings.MODEL_MAPPING.keys()]
        }
        return JSONResponse(content=model_list)
