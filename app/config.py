from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "Binary Audit Platform"
    api_prefix: str = "/api/v1"

    data_dir: Path = Field(default=ROOT_DIR / "data", alias="DATA_DIR")
    upload_dir: Path = Field(default=ROOT_DIR / "data" / "uploads", alias="UPLOAD_DIR")
    audit_dir: Path = Field(default=ROOT_DIR / "data" / "audits", alias="AUDIT_DIR")
    artifact_meta_dir: Path = Field(default=ROOT_DIR / "data" / "artifacts", alias="ARTIFACT_META_DIR")
    runtime_dir: Path = Field(default=ROOT_DIR / "data" / "runtime", alias="RUNTIME_DIR")
    frontend_dir: Path = Field(default=ROOT_DIR / "frontend", alias="FRONTEND_DIR")
    progress_log_path: Path = Field(default=ROOT_DIR / "docs" / "PROGRESS.md", alias="PROGRESS_LOG_PATH")
    skill_data_dir: Path = Field(default=ROOT_DIR / "data" / "skills", alias="SKILL_DATA_DIR")
    knowledge_deleted_path: Path = Field(
        default=ROOT_DIR / "data" / "knowledge" / "deleted_entries.json",
        alias="KNOWLEDGE_DELETED_PATH",
    )
    env_file_path: Path = Field(default=ROOT_DIR / ".env", alias="ENV_FILE_PATH")

    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")
    llm_base_url: str = Field(default="https://api.deepseek.com", alias="LLM_BASE_URL")
    manager_regular_model: str | None = Field(default=None, alias="MANAGER_REGULAR_MODEL")
    manager_hard_model: str | None = Field(default=None, alias="MANAGER_HARD_MODEL")
    disabled_tool_ids_raw: str = Field(default="afl_showmap_probe", alias="DISABLED_TOOL_IDS")

    enable_docker_runtime: bool = Field(default=False, alias="ENABLE_DOCKER_RUNTIME")
    subagent_docker_image: str = Field(default="binary-audit-subagent:latest", alias="SUBAGENT_DOCKER_IMAGE")
    subagent_docker_network_mode: str = Field(default="auto", alias="SUBAGENT_DOCKER_NETWORK_MODE")
    host_workspace_dir: Path = Field(default=ROOT_DIR, alias="HOST_WORKSPACE_DIR")

    max_parallel_subagents: int = Field(default=4, alias="MAX_PARALLEL_SUBAGENTS")
    loop_threshold: int = Field(default=3, alias="LOOP_THRESHOLD")
    note_recall_threshold: int = Field(default=3, alias="NOTE_RECALL_THRESHOLD")
    round_reset_threshold: int = Field(default=100, alias="ROUND_RESET_THRESHOLD")
    agent_discussion_max_rounds: int = Field(default=6, alias="AGENT_DISCUSSION_MAX_ROUNDS")
    agent_coordination_timeout_seconds: float = Field(default=0.35, alias="AGENT_COORDINATION_TIMEOUT_SECONDS")
    llm_timeout_seconds: int = Field(default=120, alias="LLM_TIMEOUT_SECONDS")
    llm_max_retries: int = Field(default=3, alias="LLM_MAX_RETRIES")
    llm_retry_base_delay_seconds: float = Field(default=0.8, alias="LLM_RETRY_BASE_DELAY_SECONDS")
    context_length: int = Field(default=500000, alias="CONTEXT_LENGTH")
    context_compress_model: str | None = Field(default=None, alias="CONTEXT_COMPRESS_MODEL")
    context_compression_ratio: float = Field(default=0.5, alias="CONTEXT_COMPRESSION_RATIO")
    tool_output_limit: int = Field(default=12000, alias="TOOL_OUTPUT_LIMIT")
    tool_timeout_seconds: int = Field(default=30, alias="TOOL_TIMEOUT_SECONDS")
    ida_headless_path: Path | None = Field(default=None, alias="IDA_HEADLESS_PATH")
    host_ida_install_dir: Path | None = Field(default=None, alias="HOST_IDA_INSTALL_DIR")
    host_ida_user_dir: Path | None = Field(default=Path.home() / ".idapro", alias="HOST_IDA_USER_DIR")
    container_ida_path: str = Field(default="/opt/ida/idat", alias="CONTAINER_IDA_PATH")
    container_ida_user_dir: str = Field(default="/root/.idapro", alias="CONTAINER_IDA_USER_DIR")
    rootfs_elf_tool_dir: Path | None = Field(default=Path.home() / "rootfs_elf", alias="ROOTFS_ELF_TOOL_DIR")
    container_rootfs_elf_tool_dir: str = Field(default="/opt/rootfs_elf", alias="CONTAINER_ROOTFS_ELF_TOOL_DIR")
    pwn_skill_zip_path: Path | None = Field(
        default=Path.home() / "ctf-pwn-skill-with-kb-2026-04-30.zip",
        alias="PWN_SKILL_ZIP_PATH",
    )
    pwn_skill_dirname: str = Field(default="ctf-pwn", alias="PWN_SKILL_DIRNAME")

    @model_validator(mode="after")
    def normalize_paths(self) -> "Settings":
        path_fields = (
            "data_dir",
            "upload_dir",
            "audit_dir",
            "artifact_meta_dir",
            "runtime_dir",
            "frontend_dir",
            "progress_log_path",
            "skill_data_dir",
            "knowledge_deleted_path",
            "env_file_path",
            "host_workspace_dir",
        )
        for field_name in path_fields:
            value = getattr(self, field_name)
            if not value.is_absolute():
                setattr(self, field_name, ROOT_DIR / value)
        if self.ida_headless_path is not None and not self.ida_headless_path.is_absolute():
            self.ida_headless_path = ROOT_DIR / self.ida_headless_path
        if self.host_ida_install_dir is not None and not self.host_ida_install_dir.is_absolute():
            self.host_ida_install_dir = ROOT_DIR / self.host_ida_install_dir
        if self.host_ida_user_dir is not None and not self.host_ida_user_dir.is_absolute():
            self.host_ida_user_dir = ROOT_DIR / self.host_ida_user_dir
        if self.rootfs_elf_tool_dir is not None and not self.rootfs_elf_tool_dir.is_absolute():
            self.rootfs_elf_tool_dir = ROOT_DIR / self.rootfs_elf_tool_dir
        if self.pwn_skill_zip_path is not None and not self.pwn_skill_zip_path.is_absolute():
            self.pwn_skill_zip_path = ROOT_DIR / self.pwn_skill_zip_path
        if self.pwn_skill_zip_path is not None and not self.pwn_skill_zip_path.exists():
            fallback_candidates = (
                Path.home() / "pwnskill.zip",
                Path.home() / "ctf-pwn-skill-with-kb-2026-04-30.zip",
            )
            for candidate in fallback_candidates:
                if candidate.exists():
                    self.pwn_skill_zip_path = candidate
                    break
        return self

    @property
    def deepseek_api_key(self) -> str | None:
        return self.llm_api_key

    @deepseek_api_key.setter
    def deepseek_api_key(self, value: str | None) -> None:
        object.__setattr__(self, "llm_api_key", value)

    @property
    def deepseek_base_url(self) -> str:
        return self.llm_base_url

    @deepseek_base_url.setter
    def deepseek_base_url(self, value: str) -> None:
        object.__setattr__(self, "llm_base_url", value)

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_llm_env(cls, data):
        if not isinstance(data, dict):
            return data
        copied = dict(data)
        if "deepseek_api_key" in copied:
            copied["llm_api_key"] = copied["deepseek_api_key"]
            copied["LLM_API_KEY"] = copied["deepseek_api_key"]
            if "deepseek_base_url" not in copied:
                copied["llm_base_url"] = "https://api.deepseek.com"
                copied["LLM_BASE_URL"] = "https://api.deepseek.com"
        elif "DEEPSEEK_API_KEY" in copied and "llm_api_key" not in copied and "LLM_API_KEY" not in copied:
            copied["llm_api_key"] = copied["DEEPSEEK_API_KEY"]
            copied["LLM_API_KEY"] = copied["DEEPSEEK_API_KEY"]
        elif "deepseek_api_key" not in copied and "llm_api_key" not in copied and "LLM_API_KEY" not in copied and copied.get("DEEPSEEK_API_KEY"):
            copied["llm_api_key"] = copied["DEEPSEEK_API_KEY"]
            copied["LLM_API_KEY"] = copied["DEEPSEEK_API_KEY"]

        if "deepseek_base_url" in copied:
            copied["llm_base_url"] = copied["deepseek_base_url"]
            copied["LLM_BASE_URL"] = copied["deepseek_base_url"]
        elif "DEEPSEEK_BASE_URL" in copied and "llm_base_url" not in copied and "LLM_BASE_URL" not in copied:
            copied["llm_base_url"] = copied["DEEPSEEK_BASE_URL"]
            copied["LLM_BASE_URL"] = copied["DEEPSEEK_BASE_URL"]
        elif "deepseek_base_url" not in copied and "llm_base_url" not in copied and "LLM_BASE_URL" not in copied and copied.get("DEEPSEEK_BASE_URL"):
            copied["llm_base_url"] = copied["DEEPSEEK_BASE_URL"]
            copied["LLM_BASE_URL"] = copied["DEEPSEEK_BASE_URL"]
        return copied


def ensure_directories(settings: Settings) -> None:
    for path in (
        settings.data_dir,
        settings.upload_dir,
        settings.audit_dir,
        settings.artifact_meta_dir,
        settings.runtime_dir,
        settings.frontend_dir,
        settings.skill_data_dir,
        settings.progress_log_path.parent,
        settings.knowledge_deleted_path.parent,
        settings.env_file_path.parent,
    ):
        path.mkdir(parents=True, exist_ok=True)


def parse_tool_id_csv(raw_value: str | None) -> set[str]:
    if not raw_value:
        return set()
    return {
        item.strip()
        for chunk in str(raw_value).replace("\n", ",").split(",")
        for item in [chunk.strip()]
        if item
    }


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    ensure_directories(settings)
    return settings
