"""
SysML XML解析器模块
提供SysML模型文件的XML/XMI格式解析功能
支持SysML 1.4/1.6标准和OMG XMI规范
"""

from .sysml_parser import SysMLParser
from .models import (
    ModelElement, Relationship, Diagram,
    Block, Activity, Requirement, 
    SysMLModel, ModelValidationError
)
from .xmi_reader import XMIReader
from .xml_parser import XMLParser

__all__ = [
    'SysMLParser',
    'ModelElement', 'Relationship', 'Diagram',
    'Block', 'Activity', 'Requirement',
    'SysMLModel', 'ModelValidationError',
    'XMIReader', 'XMLParser'
]