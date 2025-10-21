import uuid
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import Optional, List, Dict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra="ignore"
    )

    APP_NAME: str = "vheer-2api"
    APP_VERSION: str = "1.0.0"
    DESCRIPTION: str = "一个将 vheer.com 的文生图、图生图、图生视频功能转换为兼容 OpenAI 格式 API 的高性能代理。"

    API_MASTER_KEY: Optional[str] = "1"
    NGINX_PORT: int = 8088
    VHEER_COOKIE: Optional[str] = None

    API_REQUEST_TIMEOUT: int = 300 # 秒

    MODEL_MAPPING: Dict[str, str] = {
        "vheer-text-to-image-pro": "Pro Model",
        "vheer-text-to-image-max": "Max Model",
        "vheer-image-to-image": "Image-to-Image",
        "vheer-image-to-video": "Image-to-Video"
    }

    @model_validator(mode='after')
    def validate_settings(self) -> 'Settings':
        if not self.VHEER_COOKIE:
            raise ValueError("VHEER_COOKIE 必须在 .env 文件中设置。")
        return self

settings = Settings()