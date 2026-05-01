from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Check project root first (../  relative to backend/), then local backend/.env
    model_config = SettingsConfigDict(
        env_file=[str(Path(__file__).parent.parent.parent / ".env"), ".env"],
        extra="ignore",
    )

    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "llama3"

    deviantart_client_id: str = ""
    deviantart_client_secret: str = ""

    freesound_api_key: str = ""

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    data_dir: Path = Path(__file__).parent / "data"

    auto_save_interval: int = 5
    max_context_turns: int = 50

    @property
    def saves_dir(self) -> Path:
        return self.data_dir / "saves"

    @property
    def characters_dir(self) -> Path:
        return self.data_dir / "characters"

    @property
    def stories_dir(self) -> Path:
        return self.data_dir / "stories"

    @property
    def srd_dir(self) -> Path:
        return self.data_dir / "srd"

    @property
    def audio_cache_dir(self) -> Path:
        return self.data_dir / "audio_cache"

    @property
    def settings_file(self) -> Path:
        return self.data_dir / "settings.json"


settings = Settings()
