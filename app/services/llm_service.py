"""
大语言模型服务
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.security import filter_sensitive_content

class LLMService:
    """大语言模型服务"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.llm_model
        self.max_tokens = settings.max_tokens
        self.temperature = settings.temperature
    
    async def generate_route_plan(
        self, 
        user_input: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """生成路线规划"""
        
        # 构建提示词
        prompt = self._build_route_prompt(user_input, context)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # 解析响应
            content = response.choices[0].message.content
            filtered_content = filter_sensitive_content(content)
            
            # 尝试解析JSON格式的响应
            try:
                result = json.loads(filtered_content)
            except json.JSONDecodeError:
                # 如果不是JSON格式，返回文本格式
                result = {
                    "type": "text",
                    "content": filtered_content,
                    "suggestions": self._extract_suggestions(filtered_content)
                }
            
            return result
            
        except Exception as e:
            return {
                "error": f"生成路线规划时出错: {str(e)}",
                "type": "error"
            }
    
    async def optimize_route(
        self,
        current_route: Dict[str, Any],
        feedback: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """优化路线"""
        
        prompt = f"""
        请根据以下反馈优化旅游路线：
        
        当前路线：
        {json.dumps(current_route, ensure_ascii=False, indent=2)}
        
        用户反馈：
        {feedback}
        
        约束条件：
        {json.dumps(constraints or {}, ensure_ascii=False, indent=2)}
        
        请提供优化建议和调整后的路线规划。
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的旅游路线规划专家，擅长根据用户反馈优化路线。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content
            filtered_content = filter_sensitive_content(content)
            
            return {
                "type": "optimization",
                "content": filtered_content,
                "original_route": current_route
            }
            
        except Exception as e:
            return {
                "error": f"优化路线时出错: {str(e)}",
                "type": "error"
            }
    
    async def explain_recommendation(
        self,
        attraction_id: int,
        route_context: Dict[str, Any]
    ) -> str:
        """解释推荐理由"""
        
        prompt = f"""
        请解释为什么推荐这个景点：
        
        景点ID: {attraction_id}
        路线上下文: {json.dumps(route_context, ensure_ascii=False, indent=2)}
        
        请从以下角度解释推荐理由：
        1. 与用户兴趣的匹配度
        2. 时间安排的合理性
        3. 地理位置的优势
        4. 特殊活动或优惠
        5. 其他用户的评价
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的旅游顾问，擅长解释景点推荐的理由。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            return filter_sensitive_content(content)
            
        except Exception as e:
            return f"生成解释时出错: {str(e)}"
    
    def _build_route_prompt(self, user_input: Dict[str, Any], context: Optional[Dict[str, Any]]) -> str:
        """构建路线规划提示词"""
        
        prompt_parts = [
            "请根据以下信息生成详细的旅游路线规划：",
            "",
            "用户需求：",
            f"• 目的地: {user_input.get('destination', '未指定')}",
            f"• 出发时间: {user_input.get('start_date', '未指定')}",
            f"• 结束时间: {user_input.get('end_date', '未指定')}",
            f"• 预算: {user_input.get('budget', '未指定')}",
            f"• 旅行人数: {user_input.get('travelers', '未指定')}",
            f"• 旅行风格: {user_input.get('travel_style', '未指定')}",
            f"• 兴趣标签: {', '.join(user_input.get('interests', []))}",
            f"• 特殊要求: {user_input.get('special_requirements', '无')}",
        ]
        
        if context:
            prompt_parts.extend([
                "",
                "历史信息：",
                f"• 用户偏好: {context.get('preferences', '无')}",
                f"• 历史路线: {context.get('history', '无')}",
                f"• 反馈记录: {context.get('feedback', '无')}",
            ])
        
        prompt_parts.extend([
            "",
            "请提供：",
            "1. 详细的每日行程安排",
            "2. 推荐的景点和活动",
            "3. 交通路线建议",
            "4. 住宿推荐",
            "5. 餐饮建议",
            "6. 费用估算",
            "7. 注意事项和贴士",
            "",
            "请以JSON格式返回结果，包含以下字段：",
            "- title: 路线标题",
            "- description: 路线描述",
            "- days: 每日行程数组",
            "- total_budget: 总预算估算",
            "- highlights: 亮点推荐",
            "- tips: 实用贴士"
        ])
        
        return "\n".join(prompt_parts)
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """
        你是一个专业的AI旅游路线规划智能体，具有以下特点：
        
        1. 专业能力：
        - 深度了解中国各地的旅游景点和文化
        - 熟悉交通路线和时间安排
        - 了解不同季节和天气对旅游的影响
        - 掌握预算规划和费用控制
        
        2. 服务理念：
        - 以用户需求为中心，提供个性化服务
        - 语言友好亲切，专业且幽默
        - 注重用户体验和满意度
        - 提供实用、可操作的建议
        
        3. 输出要求：
        - 提供详细、准确的路线规划
        - 包含时间、地点、费用等关键信息
        - 考虑实际可行性和安全性
        - 给出合理的解释和推荐理由
        
        4. 安全原则：
        - 避免推荐危险或不合适的景点
        - 确保路线符合法律法规
        - 保护用户隐私和安全
        """
    
    def _extract_suggestions(self, content: str) -> List[str]:
        """从内容中提取建议"""
        suggestions = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                suggestions.append(line[1:].strip())
            elif '建议' in line or '推荐' in line:
                suggestions.append(line)
        
        return suggestions[:5]  # 最多返回5个建议