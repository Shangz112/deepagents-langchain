
try:
    from langchain.agents.middleware.types import ExtendedModelResponse
    print("ExtendedModelResponse found in langchain.agents.middleware.types")
except ImportError as e:
    print(f"ExtendedModelResponse NOT found: {e}")

try:
    from langchain.agents.middleware.types import ContextOverflowError
    print("ContextOverflowError found in langchain.agents.middleware.types")
except ImportError as e:
    print(f"ContextOverflowError NOT found: {e}")

try:
    import langchain_core.exceptions
    print("langchain_core.exceptions imported")
    try:
        from langchain_core.exceptions import ContextOverflowError
        print("ContextOverflowError found in langchain_core.exceptions")
    except ImportError as e:
        print(f"ContextOverflowError NOT found in langchain_core.exceptions: {e}")
except ImportError as e:
    print(f"langchain_core.exceptions NOT imported: {e}")
