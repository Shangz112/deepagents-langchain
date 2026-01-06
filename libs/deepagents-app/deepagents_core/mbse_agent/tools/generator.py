import uuid
import os
from jinja2 import Environment, FileSystemLoader
from langchain_core.tools import tool
from deepagents_core.mbse_agent.config import TEMPLATE_DIR

@tool
def generate_sysml_xmi(block_name: str, properties: list, output_dir: str = "output") -> str:
    """
    基于模板生成 SysML Block 片段。
    
    Args:
        block_name: Block 名称
        properties: 属性列表，每个属性包含 {"name": "prop_name", "type_id": "type_ref"}
        output_dir: 输出目录
        
    Returns:
        str: 生成的文件路径
    """
    # 初始化 Jinja2 环境
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("block.xml.j2")
    
    # 准备数据上下文，自动生成 UUID
    context = {
        "uid": str(uuid.uuid4()),
        "name": block_name,
        "properties": [
            {
                "uid": str(uuid.uuid4()), 
                "name": p["name"], 
                "type_id": p.get("type_id", "PrimitiveTypes_String")
            } 
            for p in properties
        ]
    }
    
    # 渲染 XML 内容
    xml_content = template.render(**context)
    
    # 保存文件
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{block_name}.xmi")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(xml_content)
        
    return file_path
