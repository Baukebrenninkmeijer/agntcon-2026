"""Runtime configuration and orq trace attribution."""

from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(override=True)

RunKind = Literal["interactive", "eval", "smoke"]
Interface = Literal["python", "cli", "pytest"]


class Settings(BaseSettings):
    """Configuration loaded from environment variables or ``.env``."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ANALYTICS_CHATBOT_",
        extra="ignore",
        populate_by_name=True,
    )

    orq_api_key: str | None = Field(default=None, validation_alias="ORQ_API_KEY")
    gateway_base_url: str = Field(
        default="https://api.orq.ai/v3/router",
        validation_alias="ORQ_GATEWAY_BASE_URL",
    )
    model: str = "deepseek/deepseek-v4-flash"
    database_path: Path = Path("data/analytics.duckdb")
    runs_path: Path = Path("runs")
    max_tool_steps: int = Field(default=8, ge=1, le=32)
    max_query_rows: int = Field(default=200, ge=1, le=10_000)
    query_timeout_seconds: float = Field(default=10.0, gt=0, le=300)
    dataset_version: str = "revenue-v1"
    agent_version: str = "v1"


class TraceContext(BaseModel):
    """Bounded attribution attached to every AI Gateway request."""

    model_config = ConfigDict(frozen=True)

    run_kind: RunKind = "interactive"
    evaluation_split: str = "ad_hoc"
    case_id: str = ""
    interface: Interface = "python"
    identity_id: str | None = None
    dataset_version: str = "revenue-v1"
    agent_version: str = "v1"

    def extra_body(self, thread_id: str) -> dict[str, Any]:
        """Return orq request attribution using each mechanism for one purpose."""

        body: dict[str, Any] = {
            "name": "PyData2026-AnalyticsChatbot",
            "thread": {
                "id": thread_id,
                "tags": ["pydata2026", "analytics-chatbot", self.run_kind],
            },
            "metadata": {
                "dataset_version": self.dataset_version,
                "agent_version": self.agent_version,
                "evaluation_split": self.evaluation_split,
                "case_id": self.case_id,
                "interface": self.interface,
                "run_kind": self.run_kind,
            },
        }
        if self.identity_id:
            body["identity"] = {"id": self.identity_id}
        return body
