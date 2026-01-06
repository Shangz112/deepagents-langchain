from lxml import etree
from deepagents_core.mbse_agent.utils.xml_helper import NS_MAP
from langchain_core.tools import tool

@tool
def parse_sysml_xmi(file_path: str) -> dict:
    """
    解析 XMI 文件，提取 Block 和 Activity 信息。
    
    Args:
        file_path: XMI 文件的绝对路径
        
    Returns:
        dict: 包含 blocks 和 activities 的字典
    """
    try:
        tree = etree.parse(file_path)
    except Exception as e:
        return {"error": f"Failed to parse XMI file: {str(e)}"}
        
    root = tree.getroot()
    
    # 1. 抓取所有 Block (Class)
    blocks = []
    # 使用 XPath 定位带有 uml:Class 类型的 packagedElement
    for elem in root.xpath('//packagedElement[@xmi:type="uml:Class"]', namespaces=NS_MAP):
        # 提取 xmi:id (注意命名空间处理)
        xmi_id = elem.get(f"{{{NS_MAP['xmi']}}}id")
        blocks.append({
            "id": xmi_id,
            "name": elem.get("name"),
            "type": "Block",
            "properties": [
                # 提取子属性
                {"name": p.get("name"), "type_ref": p.xpath("type/@xmi:idref", namespaces=NS_MAP)[0]}
                for p in elem.xpath('ownedAttribute[@xmi:type="uml:Property"]', namespaces=NS_MAP)
                if p.xpath("type/@xmi:idref", namespaces=NS_MAP)
            ]
        })
    
    # 2. 抓取所有 Activity
    activities = []
    for elem in root.xpath('//packagedElement[@xmi:type="uml:Activity"]', namespaces=NS_MAP):
        act_id = elem.get(f"{{{NS_MAP['xmi']}}}id")
        act_name = elem.get("name")
        
        nodes = []
        for node in elem.xpath('node', namespaces=NS_MAP):
            nodes.append({
                "id": node.get(f"{{{NS_MAP['xmi']}}}id"),
                "name": node.get("name"),
                "type": node.get(f"{{{NS_MAP['xmi']}}}type")
            })
            
        edges = []
        for edge in elem.xpath('edge', namespaces=NS_MAP):
            edges.append({
                "source": edge.get("source"),
                "target": edge.get("target"),
                "guard": edge.get("guard") 
            })
            
        activities.append({
            "id": act_id,
            "name": act_name,
            "nodes": nodes,
            "edges": edges
        })
        
    return {"blocks": blocks, "activities": activities}
