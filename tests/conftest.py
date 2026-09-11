import pytest

# The real workspace project id lives only in the ignored .env. Tests pin a fake so the suite
# neither depends on a developer's environment nor reproduces the identifier in the tree.
TEST_PROJECT_ID = "00000000-0000-4000-8000-000000000000"


@pytest.fixture(autouse=True)
def fake_project_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ORQ_PROJECT_ID", TEST_PROJECT_ID)
