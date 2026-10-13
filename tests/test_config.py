from about_rag.config import Settings

def test_default_paths_point_to_existing_files():
    settings = Settings(_env_file=None)
    assert settings.knowledge_base_path.exists()
    assert settings.system_prompt_path.exists()

def test_env_var_overrides_default(monkeypatch):
    monkeypatch.setenv("ABOUT_RAG_LOG_LEVEL", "DEBUG")
    assert Settings(_env_file=None).log_level == "DEBUG"

def test_api_key_is_hidden_in_repr(monkeypatch):
    monkeypatch.setenv("ABOUT_RAG_LLM_API_KEY", "super-secret")
    settings = Settings(_env_file=None)
    assert "super-secret" not in repr(settings)
    assert settings.llm_api_key is not None
    assert settings.llm_api_key.get_secret_value() == "super-secret"