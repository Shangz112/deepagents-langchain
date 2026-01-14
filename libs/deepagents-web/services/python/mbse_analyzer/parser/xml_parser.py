"""
XML基础解析器模块
提供通用的XML文件解析功能
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import xmltodict
from lxml import etree
import json
import logging

logger = logging.getLogger(__name__)


class XMLParser:
    """XML解析器基类"""
    
    def __init__(self, xml_file_path: str):
        """
        初始化XML解析器
        
        Args:
            xml_file_path: XML文件路径
        """
        self.file_path = Path(xml_file_path)
        self.root = None
        self.namespaces = {}
        self.document = None
        
    def load_file(self) -> None:
        """加载XML文件"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                xml_content = file.read()
            
            # 使用lxml解析，支持命名空间
            self.document = etree.fromstring(xml_content.encode('utf-8'))
            self.root = self.document
            self._extract_namespaces()
            logger.info(f"成功加载XML文件: {self.file_path}")
            
        except Exception as e:
            logger.error(f"加载XML文件失败: {e}")
            raise
    
    def _extract_namespaces(self) -> None:
        """提取XML文档中的命名空间"""
        if self.document is None:
            return
        
        # 从根元素提取命名空间
        for key, value in self.document.nsmap.items():
            if key:
                self.namespaces[value] = f"{{{value}}}"
            else:
                self.namespaces['default'] = f"{{{value}}}"
    
    def get_namespace_prefix(self, namespace_uri: str) -> str:
        """
        根据命名空间URI获取前缀
        
        Args:
            namespace_uri: 命名空间URI
            
        Returns:
            命名空间前缀，如果没有找到则返回空字符串
        """
        for prefix, uri in self.document.nsmap.items():
            if uri == namespace_uri:
                return f"{prefix}:" if prefix else ""
        return ""
    
    def find_elements(self, xpath: str, parent=None) -> List[ET.Element]:
        """
        使用XPath查找元素
        
        Args:
            xpath: XPath表达式
            parent: 父元素，如果为None则从根元素开始
            
        Returns:
            元素列表
        """
        if parent is None:
            parent = self.root
        
        try:
            # 支持命名空间的XPath查询
            xpath_ns = self._add_namespace_to_xpath(xpath)
            elements = parent.xpath(xpath_ns, namespaces=self.document.nsmap)
            return elements
        except Exception as e:
            logger.error(f"XPath查询失败: {xpath}, 错误: {e}")
            return []
    
    def _add_namespace_to_xpath(self, xpath: str) -> str:
        """
        为XPath添加命名空间
        
        Args:
            xpath: 原始XPath
            
        Returns:
            带命名空间的XPath
        """
        # 如果XPath已经包含命名空间前缀，直接返回
        if ":" in xpath:
            return xpath
        
        # 简单处理：为XPath片段添加默认命名空间
        parts = xpath.split('/')
        result_parts = []
        
        for part in parts:
            if part and not part.startswith('@') and not part.startswith('['):
                # 为元素名添加默认命名空间
                result_parts.append(f"*[local-name()='{part}']")
            else:
                result_parts.append(part)
        
        return '/'.join(result_parts)
    
    def get_element_attributes(self, element: ET.Element) -> Dict[str, str]:
        """获取元素的所有属性"""
        attributes = {}
        if element is not None:
            for key, value in element.attrib.items():
                attributes[key] = value
        return attributes
    
    def get_element_text(self, element: ET.Element) -> str:
        """获取元素的文本内容"""
        if element is None:
            return ""
        return element.text or ""
    
    def get_child_elements(self, element: ET.Element, tag_name: Optional[str] = None) -> List[ET.Element]:
        """获取子元素"""
        if element is None:
            return []
        
        if tag_name:
            xpath = f".//*[local-name()='{tag_name}']"
            return element.xpath(xpath)
        else:
            return list(element)
    
    def get_element_by_id(self, element_id: str, id_attr: str = "id") -> Optional[ET.Element]:
        """
        根据ID属性查找元素
        
        Args:
            element_id: 元素ID
            id_attr: ID属性名
            
        Returns:
            元素或None
        """
        xpath = f"//*[@{id_attr}='{element_id}']"
        elements = self.find_elements(xpath)
        return elements[0] if elements else None
    
    def convert_to_dict(self) -> Dict[str, Any]:
        """将XML转换为Python字典"""
        if self.document is None:
            self.load_file()
        
        try:
            # 将lxml元素转换为字符串
            xml_str = etree.tostring(self.document, encoding='unicode')
            # 转换为字典
            return xmltodict.parse(xml_str, process_namespaces=True)
        except Exception as e:
            logger.error(f"XML转换为字典失败: {e}")
            return {}
    
    def convert_to_json(self, indent: int = 2) -> str:
        """将XML转换为JSON字符串"""
        xml_dict = self.convert_to_dict()
        return json.dumps(xml_dict, ensure_ascii=False, indent=indent)
    
    def extract_namespace_info(self) -> Dict[str, Any]:
        """提取命名空间信息"""
        if self.document is None:
            self.load_file()
        
        ns_info = {
            "namespaces": {},
            "schema_locations": [],
            "imports": []
        }
        
        # 提取命名空间
        if hasattr(self.document, 'nsmap'):
            ns_info["namespaces"] = {k if k else "default": v for k, v in self.document.nsmap.items()}
        
        # 查找schemaLocation
        schema_loc_xpath = "//@xsi:schemaLocation | //@schemaLocation"
        try:
            elements = self.find_elements(schema_loc_xpath)
            for elem in elements:
                if isinstance(elem, str):
                    ns_info["schema_locations"].append(elem)
        except:
            pass
        
        # 查找import元素
        import_xpath = "//import"
        try:
            imports = self.find_elements(import_xpath)
            for imp in imports:
                import_info = self.get_element_attributes(imp)
                ns_info["imports"].append(import_info)
        except:
            pass
        
        return ns_info
    
    def validate_xml(self, xsd_file_path: Optional[str] = None) -> List[str]:
        """
        验证XML文件
        
        Args:
            xsd_file_path: XSD模式文件路径（可选）
            
        Returns:
            错误消息列表
        """
        errors = []
        
        # 基本XML结构验证
        try:
            if self.document is None:
                self.load_file()
            
            # 检查根元素
            if self.root is None:
                errors.append("XML文件没有根元素")
            
            # 如果提供了XSD，进行模式验证
            if xsd_file_path and Path(xsd_file_path).exists():
                try:
                    xsd_doc = etree.parse(xsd_file_path)
                    xsd = etree.XMLSchema(xsd_doc)
                    if not xsd.validate(self.document):
                        for error in xsd.error_log:
                            errors.append(f"模式验证错误: {error.message} (行 {error.line})")
                except Exception as e:
                    errors.append(f"XSD验证失败: {e}")
            
        except Exception as e:
            errors.append(f"XML验证失败: {e}")
        
        return errors