from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class SysMLNode(BaseModel):
    id: str
    name: str
    type: str  # e.g., "Block", "Action", "InitialNode"
    properties: Optional[List[Dict[str, str]]] = None

class SysMLActivity(BaseModel):
    id: str
    name: str
    nodes: List[SysMLNode]
    edges: List[Dict[str, str]]  # {"source": "id1", "target": "id2", "guard": "condition"}

class SysMLModel(BaseModel):
    name: str
    blocks: List[SysMLNode]
    activities: List[SysMLActivity]

class OperationContext(BaseModel):
    process_id: str          # 关联的 SysML Activity ID
    current_step_name: str   # 当前所在的节点名称
    parameters: Dict[str, Any] # 过程参数，如 {"voltage": 12.5}
    history: List[str]       # 已完成步骤 ID 列表
