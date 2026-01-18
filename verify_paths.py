
import sys
import os
from pathlib import Path

# Add libs/deepagents-cli and libs/deepagents-app to sys.path
sys.path.append(r"d:\MASrepos\deepagents-langchain\libs\deepagents-cli")
sys.path.append(r"d:\MASrepos\deepagents-langchain\libs\deepagents-app")

# Mock environment variables to satisfy config requirements
os.environ["OPENAI_API_KEY"] = "sk-mock-key"
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-mock-key"
os.environ["GOOGLE_API_KEY"] = "mock-key"
os.environ["TAVILY_API_KEY"] = "tvly-mock-key"
os.environ["DEEPAGENTS_LANGSMITH_PROJECT"] = "mock-project"
os.environ["LANGSMITH_PROJECT"] = "mock-user-project"

try:
    from deepagents_cli.config import Settings as CliSettings
    cli_settings = CliSettings.from_environment()
    print(f"CLI User Dir: {cli_settings.user_deepagents_dir}")
    print(f"CLI Agent Dir (test): {cli_settings.get_agent_dir('test')}")
    print(f"CLI Skills Dir (test): {cli_settings.get_user_skills_dir('test')}")
except ImportError as e:
    print(f"CLI Import Error: {e}")
except Exception as e:
    print(f"CLI Error: {e}")

print("-" * 20)

try:
    from deepagents_core.config import Settings as AppSettings
    app_settings = AppSettings.from_environment()
    print(f"App User Dir: {app_settings.user_deepagents_dir}")
    print(f"App Agent Dir (test): {app_settings.get_agent_dir('test')}")
    print(f"App Skills Dir (test): {app_settings.get_user_skills_dir('test')}")
except ImportError as e:
    print(f"App Import Error: {e}")
except Exception as e:
    print(f"App Error: {e}")
