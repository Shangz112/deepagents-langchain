import networkx as nx
from typing import List, Dict, Any
from langchain_core.tools import tool
import json

class ComplianceEngine:
    def __init__(self, activities_data: List[Dict]):
        """
        初始化流程引擎，构建有向图
        """
        self.graph = nx.DiGraph()
        for act in activities_data:
            # 添加节点
            for node in act.get('nodes', []):
                self.graph.add_node(node['id'], **node)
            # 添加边
            for edge in act.get('edges', []):
                self.graph.add_edge(edge['source'], edge['target'], guard=edge.get('guard'))
    
    def validate(self, current_step_name: str, parameters: Dict[str, Any]) -> Dict:
        """
        核心方法：校验当前状态并推荐下一步
        """
        # 1. 定位当前节点
        current_nodes = [n for n, d in self.graph.nodes(data=True) if d.get('name') == current_step_name]
        if not current_nodes:
            return {"valid": False, "reason": f"流程中未找到步骤 '{current_step_name}'"}
            
        curr_id = current_nodes[0]
        
        # 2. 合规性检查 (示例：检查参数约束)
        # 实际项目中应解析 ConstraintBlock
        if current_step_name == "电压测试" and parameters.get("voltage", 0) > 50:
             return {
                 "valid": False, 
                 "reason": "违反约束: 电压必须 <= 50V",
                 "suggestion": "请调整电压参数后重试"
             }

        # 3. 预测下一步
        next_steps = []
        for successor in self.graph.successors(curr_id):
            edge_data = self.graph.get_edge_data(curr_id, successor)
            target_node = self.graph.nodes[successor]
            
            # 处理分支条件
            guard = edge_data.get('guard')
            if guard:
                next_steps.append(f"{target_node.get('name')} (需满足: {guard})")
            else:
                next_steps.append(target_node.get('name'))
                
        return {
            "valid": True,
            "current_node": current_step_name,
            "next_steps": next_steps
        }

# Global engine instance placeholder
_engine_instance = None

@tool
def validate_operation_state(current_step_name: str, parameters: str) -> dict:
    """
    校验当前操作状态并提供下一步建议。
    
    Args:
        current_step_name: 当前步骤名称
        parameters: JSON 格式的参数字符串
        
    Returns:
        dict: 校验结果和建议
    """
    global _engine_instance
    if _engine_instance is None:
        # Mocking data for now as we don't have a persistent XMI loaded state in this simple tool
        mock_activities = [{
            "nodes": [
                {"id": "1", "name": "需求分析"},
                {"id": "2", "name": "电压测试"},
                {"id": "3", "name": "发布"}
            ],
            "edges": [
                {"source": "1", "target": "2"},
                {"source": "2", "target": "3", "guard": "voltage<=50"}
            ]
        }]
        _engine_instance = ComplianceEngine(mock_activities)
        
    try:
        params = json.loads(parameters)
    except:
        return {"valid": False, "reason": "Parameters must be valid JSON"}
        
    return _engine_instance.validate(current_step_name, params)
