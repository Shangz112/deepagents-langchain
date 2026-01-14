"""
SysML数据模型定义模块
定义SysML模型的核心数据类型和结构
"""

from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
from datetime import datetime


class ModelValidationError(Exception):
    """模型验证错误异常"""
    pass


class ElementType(str, Enum):
    """SysML元素类型枚举"""
    BLOCK = "Block"
    PART = "Part"
    ACTIVITY = "Activity"
    STATE = "State"
    REQUIREMENT = "Requirement"
    CONSTRAINT_BLOCK = "ConstraintBlock"
    VALUE_TYPE = "ValueType"
    INTERFACE = "Interface"
    SIGNAL = "Signal"
    ENUMERATION = "Enumeration"
    PACKAGE = "Package"
    MODEL = "Model"
    ACTOR = "Actor"
    USE_CASE = "UseCase"


class RelationshipType(str, Enum):
    """关系类型枚举"""
    ASSOCIATION = "Association"
    AGGREGATION = "Aggregation"
    COMPOSITION = "Composition"
    GENERALIZATION = "Generalization"
    DEPENDENCY = "Dependency"
    REALIZATION = "Realization"
    FLOW = "Flow"
    CONNECTOR = "Connector"
    PART = "Part"
    REFERENCE = "Reference"


class DiagramType(str, Enum):
    """图表类型枚举"""
    BLOCK_DEFINITION = "BlockDefinitionDiagram"
    INTERNAL_BLOCK = "InternalBlockDiagram"
    ACTIVITY = "ActivityDiagram"
    SEQUENCE = "SequenceDiagram"
    STATE_MACHINE = "StateMachineDiagram"
    USE_CASE = "UseCaseDiagram"
    REQUIREMENT = "RequirementDiagram"
    PACKAGE = "PackageDiagram"


class Property(BaseModel):
    """属性模型"""
    name: str
    type: str
    value: Optional[Any] = None
    visibility: str = "public"
    is_derived: bool = False
    is_read_only: bool = False
    multiplicity: str = "1"
    default_value: Optional[Any] = None
    description: Optional[str] = None


class Operation(BaseModel):
    """操作模型"""
    name: str
    parameters: List[Dict[str, str]] = []
    return_type: Optional[str] = None
    visibility: str = "public"
    is_abstract: bool = False
    description: Optional[str] = None


class ModelElement(BaseModel):
    """模型元素基类"""
    id: str
    name: str
    type: ElementType
    stereotype: Optional[str] = None
    properties: Dict[str, Property] = Field(default_factory=dict)
    operations: List[Operation] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    relationships: List[str] = Field(default_factory=list)  # 关系ID列表
    parent_id: Optional[str] = None
    namespace: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    modified_at: datetime = Field(default_factory=datetime.now)
    
    @validator('id')
    def validate_id_format(cls, v):
        if not v or not v.strip():
            raise ValueError("元素ID不能为空")
        return v.strip()
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("元素名称不能为空")
        return v.strip()


class Block(ModelElement):
    """块元素"""
    type: ElementType = ElementType.BLOCK
    is_abstract: bool = False
    parts: Dict[str, str] = Field(default_factory=dict)  # part_name: part_type_id
    references: Dict[str, str] = Field(default_factory=dict)  # ref_name: ref_type_id
    value_properties: Dict[str, str] = Field(default_factory=dict)  # 值属性
    constraint_properties: Dict[str, str] = Field(default_factory=dict)  # 约束属性


class Activity(ModelElement):
    """活动元素"""
    type: ElementType = ElementType.ACTIVITY
    is_abstract: bool = False
    nodes: List[str] = Field(default_factory=list)  # 节点ID列表
    edges: List[str] = Field(default_factory=list)  # 边ID列表
    parameters: List[Dict[str, Any]] = Field(default_factory=list)  # 参数列表
    preconditions: List[str] = Field(default_factory=list)  # 前置条件
    postconditions: List[str] = Field(default_factory=list)  # 后置条件


class Requirement(ModelElement):
    """需求元素"""
    type: ElementType = ElementType.REQUIREMENT
    text: str
    source: Optional[str] = None
    risk_level: Optional[str] = None  # 风险级别
    priority: Optional[str] = None  # 优先级
    status: str = "Proposed"
    verification_method: Optional[str] = None  # 验证方法
    verified_by: Optional[str] = None  # 验证者
    derived_from: List[str] = Field(default_factory=list)  # 派生自的需求ID列表
    satisfied_by: List[str] = Field(default_factory=list)  # 满足需求的元素ID列表
    
    @validator('text')
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError("需求文本不能为空")
        return v.strip()


class Relationship(BaseModel):
    """关系模型"""
    id: str
    name: Optional[str] = None
    type: RelationshipType
    source_id: str
    target_id: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    multiplicity_source: str = "1"
    multiplicity_target: str = "1"
    role_source: Optional[str] = None
    role_target: Optional[str] = None
    description: Optional[str] = None
    
    @validator('id')
    def validate_id(cls, v):
        if not v or not v.strip():
            raise ValueError("关系ID不能为空")
        return v.strip()
    
    @validator('source_id', 'target_id')
    def validate_end_ids(cls, v):
        if not v or not v.strip():
            raise ValueError("关系端点ID不能为空")
        return v.strip()


class Diagram(BaseModel):
    """图表模型"""
    id: str
    name: str
    type: DiagramType
    elements: Dict[str, Dict[str, Any]] = Field(default_factory=dict)  # 元素ID:布局信息
    background_color: str = "#FFFFFF"
    line_color: str = "#000000"
    text_color: str = "#000000"
    font_family: str = "Arial"
    font_size: int = 12
    zoom_level: float = 1.0
    description: Optional[str] = None
    
    @validator('id')
    def validate_id(cls, v):
        if not v or not v.strip():
            raise ValueError("图表ID不能为空")
        return v.strip()
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("图表名称不能为空")
        return v.strip()
    
    def get_element_positions(self, element_id: str) -> Optional[Dict[str, float]]:
        """获取元素在图表中的位置信息"""
        element_info = self.elements.get(element_id)
        if element_info:
            return {
                'x': element_info.get('x', 0),
                'y': element_info.get('y', 0),
                'width': element_info.get('width', 100),
                'height': element_info.get('height', 50)
            }
        return None


class SysMLModel(BaseModel):
    """SysML模型容器"""
    id: str
    name: str
    version: str = "1.0.0"
    created_at: datetime = Field(default_factory=datetime.now)
    modified_at: datetime = Field(default_factory=datetime.now)
    
    # 模型内容
    elements: Dict[str, ModelElement] = Field(default_factory=dict)
    relationships: Dict[str, Relationship] = Field(default_factory=dict)
    diagrams: Dict[str, Diagram] = Field(default_factory=dict)
    
    # 元数据
    author: Optional[str] = None
    organization: Optional[str] = None
    description: Optional[str] = None
    namespace: Optional[str] = None
    profile: Optional[str] = None  # 使用的profile
    
    class Config:
        arbitrary_types_allowed = True
    
    def add_element(self, element: ModelElement) -> None:
        """添加元素到模型"""
        if element.id in self.elements:
            raise ModelValidationError(f"元素ID '{element.id}' 已存在")
        self.elements[element.id] = element
        self.modified_at = datetime.now()
    
    def add_relationship(self, relationship: Relationship) -> None:
        """添加关系到模型"""
        if relationship.id in self.relationships:
            raise ModelValidationError(f"关系ID '{relationship.id}' 已存在")
        # 验证端点存在性
        if relationship.source_id not in self.elements:
            raise ModelValidationError(f"源元素ID '{relationship.source_id}' 不存在")
        if relationship.target_id not in self.elements:
            raise ModelValidationError(f"目标元素ID '{relationship.target_id}' 不存在")
        
        self.relationships[relationship.id] = relationship
        self.modified_at = datetime.now()
        
        # 更新元素的关联关系
        source_element = self.elements[relationship.source_id]
        target_element = self.elements[relationship.target_id]
        source_element.relationships.append(relationship.id)
        target_element.relationships.append(relationship.id)
    
    def add_diagram(self, diagram: Diagram) -> None:
        """添加图表到模型"""
        if diagram.id in self.diagrams:
            raise ModelValidationError(f"图表ID '{diagram.id}' 已存在")
        self.diagrams[diagram.id] = diagram
        self.modified_at = datetime.now()
    
    def get_element_relationships(self, element_id: str) -> List[Relationship]:
        """获取元素的所有关系"""
        element = self.elements.get(element_id)
        if not element:
            return []
        
        relationships = []
        for rel_id in element.relationships:
            if rel_id in self.relationships:
                relationships.append(self.relationships[rel_id])
        
        return relationships
    
    def validate_model(self) -> List[str]:
        """验证模型一致性，返回错误消息列表"""
        errors = []
        
        # 验证所有关系的端点存在性
        for rel_id, relationship in self.relationships.items():
            if relationship.source_id not in self.elements:
                errors.append(f"关系 '{rel_id}' 的源元素ID '{relationship.source_id}' 不存在")
            if relationship.target_id not in self.elements:
                errors.append(f"关系 '{rel_id}' 的目标元素ID '{relationship.target_id}' 不存在")
        
        # 验证图表中的元素存在性
        for diagram_id, diagram in self.diagrams.items():
            for element_id in diagram.elements.keys():
                if element_id not in self.elements:
                    errors.append(f"图表 '{diagram_id}' 中的元素ID '{element_id}' 不存在")
        
        return errors