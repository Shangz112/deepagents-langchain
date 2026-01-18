from typing import TypedDict, Annotated, List
import operator
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from deepagents_core.mbse_agent.config import SILICONFLOW_BASE_URL, SILICONFLOW_API_KEY, MODEL_NAME
from deepagents_core.mbse_agent.tools.parser import parse_sysml_xmi
from deepagents_core.mbse_agent.tools.generator import generate_sysml_xmi
from deepagents_core.mbse_agent.tools.validator import validate_operation_state
from deepagents_core.mbse_agent.tools.rag import search_mbse_knowledge

SYSTEM_PROMPT = """
【角色】
你是由 DeepAgents 驱动的 MBSE 专家助手。你精通 SysML v1.0 规范，拥有读取、生成、校验 SysML 模型文件及提供流程辅助的能力。

【核心能力与工具使用规范】
1. **模型解析 (XMI Parsing)**
   - 遇到"分析模型"、"读取流程"请求时，**必须**首先调用 `parse_sysml_xmi`。
   - 不要尝试直接阅读 XML 源码，必须依赖解析工具返回的 JSON 结构。

2. **模型生成 (XMI Generation)**
   - 遇到"创建模型"、"生成 Block"请求时，**必须**调用 `generate_sysml_xmi`。
   - 在调用前，通过对话确认关键参数（如 Block 名称、属性列表）。不要凭空猜测。

3. **合规校验与流程辅助 (Compliance & Guidance)**
   - 当用户提供操作状态（JSON 格式或自然语言描述当前步骤与参数）时，**必须**调用 `validate_operation_state`。
   - 根据工具返回的 `valid` 字段判断：
     - 若 `False`：严厉指出错误原因，并引用规范条款。
     - 若 `True`：给予肯定，并根据工具返回的 `next_steps` 建议下一步操作。

4. **规范查询 (Knowledge Retrieval)**
   - 遇到不确定的 SysML 语法或流程规则，使用 `search_mbse_knowledge`。

【思维链 (Chain of Thought)】
在回答用户前，请按以下步骤思考：
1. **意图识别**: 用户是想看模型(Parse)、改模型(Generate)、查规范(RAG)还是做任务(Validate)？
2. **信息核对**: 缺少必要参数吗？(如生成模型缺属性，校验状态缺参数)。缺则追问。
3. **工具调用**: 选择最合适的工具执行。
4. **结果综合**: 将工具返回的结构化数据转换为自然语言建议。

【约束】
- 严禁臆造模型中不存在的 Block 或 Flow。
- 如果校验失败，必须明确指出违反了哪条规则（引用工具返回的 Error Message）。
- 涉及生成文件操作时，必须告知用户文件保存路径。
"""

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]

def create_mbse_agent():
    # 1. Initialize Tools
    tools = [
        parse_sysml_xmi,
        generate_sysml_xmi,
        validate_operation_state,
        search_mbse_knowledge
    ]
    
    # 2. Initialize LLM (SiliconFlow)
    llm = ChatOpenAI(
        base_url=SILICONFLOW_BASE_URL,
        api_key=SILICONFLOW_API_KEY,
        model=MODEL_NAME,
        temperature=0.1
    ).bind_tools(tools)
    
    # 3. Define Graph Nodes
    def chatbot(state: AgentState):
        messages = [
            ("system", SYSTEM_PROMPT),
        ] + state["messages"]
        response = llm.invoke(messages)
        return {"messages": [response]}

    # 4. Define Graph
    workflow = StateGraph(AgentState)
    workflow.add_node("chatbot", chatbot)
    workflow.add_node("tools", ToolNode(tools))
    
    workflow.set_entry_point("chatbot")
    
    # Conditional edge: chatbot -> tools (if tool call) OR end
    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "tools"
        return END
        
    workflow.add_conditional_edges("chatbot", should_continue)
    workflow.add_edge("tools", "chatbot")
    
    return workflow.compile()
