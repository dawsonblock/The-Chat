from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    database_url: str = 'sqlite:///./storage/postgres/operator_one.db'
    session_secret: str = 'dev-session-secret'
    artifacts_dir: str = './storage/artifacts/data'
    service_token: str = 'dev-internal-token'
    cors_origins: str = 'http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080'
    openai_proxy_api_key: str = 'dev-openai-proxy-key'
    llm_backend: str = 'heuristic'
    local_llm_base_url: str = 'http://127.0.0.1:11434/v1'
    local_llm_model: str = 'llama3.2'
    local_llm_api_key: str = ''
    local_llm_timeout_seconds: float = 120.0
    run_timeout_seconds: float = 600.0
    worker_poll_interval_seconds: float = 0.35
    intake_allow_private_hosts: bool = False
    intake_allow_domains: str = ''
    intake_deny_domains: str = 'localhost,127.0.0.1,::1,0.0.0.0'
    intake_connect_timeout: float = 10.0
    intake_read_timeout: float = 30.0
    intake_max_redirects: int = 8


settings = Settings()
