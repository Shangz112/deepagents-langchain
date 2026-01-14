
import sys
import os
import importlib

print("Checking magic_pdf...")
try:
    import magic_pdf
    print(f"magic_pdf imported: {magic_pdf.__file__}")
    print(f"dir(magic_pdf): {dir(magic_pdf)}")
except ImportError as e:
    print(f"magic_pdf import failed: {e}")

try:
    from magic_pdf.pipe.UNIPipe import UNIPipe
    print("magic_pdf.pipe.UNIPipe: OK")
except ImportError as e:
    print(f"magic_pdf.pipe.UNIPipe failed: {e}")

try:
    import milvus_lite
    print(f"milvus_lite imported: {milvus_lite.__file__}")
except ImportError as e:
    print(f"milvus_lite import failed: {e}")

from pymilvus import MilvusClient
try:
    client = MilvusClient("test_milvus_2.db")
    print("Milvus Lite: OK")
except Exception as e:
    print(f"Milvus Lite: FAILED ({e})")
