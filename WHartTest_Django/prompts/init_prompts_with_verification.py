#!/usr/bin/env python
"""
重新初始化用户提示词 - 新架构（5个专项分析）
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wharttest_django.settings')
django.setup()

from prompts.models import UserPrompt
from django.contrib.auth.models import User

def main():
    try:
        # 获取用户
        user = User.objects.get(username='duanxc')
        
        # 删除现有的程序调用提示词（包括新旧类型）
        UserPrompt.objects.filter(
            user=user,
            prompt_type__in=[
                # 旧类型（已废弃）
                'document_structure', 'direct_analysis', 'global_analysis', 'module_analysis',
                # 新类型（5个专项分析）
                'completeness_analysis', 'consistency_analysis', 'testability_analysis', 
                'feasibility_analysis', 'clarity_analysis'
            ]
        ).delete()
        
        print("✅ 已清空现有程序调用提示词")
        
        # 重新创建新架构的专项分析提示词
        prompts_data = {
            'completeness_analysis': {
                'name': '完整性分析',
                'description': '专项分析需求的完整性',
                'content': """你是一位资深的需求分析专家。请深入分析完整的需求文档的完整性。

【文档内容】
{document}

【分析维度】
1. 📋 **基础信息完整性**
   - 项目背景和目标是否明确
   - 干系人识别是否完整
   - 业务术语是否定义清晰

2. 🎯 **功能需求完整性**
   - 核心功能是否全部覆盖
   - 功能描述是否详细
   - 用户场景是否完整

3. ⚙️ **非功能需求完整性**
   - 性能要求是否明确
   - 安全性要求是否覆盖
   - 可用性和兼容性是否说明

4. 🔄 **流程和接口完整性**
   - 业务流程是否完整
   - 接口定义是否清晰
   - 数据结构是否完整

【输出JSON格式】
{{
  "analysis_type": "completeness_analysis",
  "overall_score": 85,
  "summary": "完整性评估总结，说明文档的整体完整度",
  "issues": [
    {{
      "severity": "high",
      "category": "缺失功能",
      "description": "缺少用户登录功能的详细描述",
      "location": "第3章功能需求",
      "suggestion": "补充登录流程、密码规则、多端登录等详细说明"
    }}
  ],
  "strengths": ["基础信息完整", "业务流程清晰"],
  "recommendations": ["补充安全需求", "完善接口定义"]
}}"""
            },
            'consistency_analysis': {
                'name': '一致性分析',
                'description': '专项分析需求文档的内部一致性',
                'content': """你是一位资深的需求一致性分析专家。请深入分析完整的需求文档。

【文档内容】
{document}

【分析要求】
请从以下维度检查文档的内部一致性：

1. 🔗 **术语一致性**
   - 关键术语定义是否统一
   - 命名规范是否一致
   - 缩写使用是否规范

2. 📊 **数据一致性**
   - 数据实体定义是否统一
   - 数据类型是否一致
   - 数据流向是否清晰合理

3. 📋 **逻辑一致性**
   - 业务规则是否自洽
   - 流程描述是否前后一致
   - 状态定义和转换是否合理

4. 🎯 **引用一致性**
   - 内部引用是否正确
   - 章节编号是否连贯
   - 图表编号是否一致

【输出JSON格式】
{{
  "analysis_type": "consistency_analysis",
  "overall_score": 85,
  "summary": "一致性评估总结",
  "issues": [
    {{
      "severity": "high",
      "category": "术语不一致",
      "description": "用户在不同章节被称为'用户'和'客户'",
      "location": "第2.3节和第3.1节",
      "suggestion": "统一使用'用户'术语"
    }}
  ],
  "strengths": ["数据定义统一", "流程描述清晰"],
  "recommendations": ["建立术语表", "统一命名规范"]
}}"""
            },
            'testability_analysis': {
                'name': '可测性分析',
                'description': '专项分析需求的可测试性',
                'content': """你是一位资深的测试专家。请深入分析完整需求文档的可测试性。

【文档内容】
{document}

【分析维度】
1. ✅ **验收标准明确性**
   - 功能点是否有明确的验收标准
   - 性能指标是否可量化
   - 成功失败条件是否清晰

2. 🎯 **可观测性**
   - 功能结果是否可见可验证
   - 状态变化是否可追踪
   - 日志和监控是否考虑

3. 🔄 **可重复性**
   - 测试前置条件是否明确
   - 测试步骤是否可重复执行
   - 测试数据准备是否可行

4. 🧪 **边界和异常**
   - 边界条件是否定义
   - 异常场景是否覆盖
   - 错误处理是否明确

【输出JSON格式】
{{
  "analysis_type": "testability_analysis",
  "overall_score": 85,
  "summary": "可测性评估总结，说明文档的整体可测试程度",
  "issues": [
    {{
      "severity": "high",
      "category": "验收标准模糊",
      "description": "用户搜索功能缺少响应时间等性能指标",
      "location": "第3.2节搜索功能",
      "suggestion": "补充搜索响应时间应≤2秒等量化指标"
    }}
  ],
  "strengths": ["功能描述清晰", "流程可追踪"],
  "recommendations": ["补充性能指标", "明确异常场景"]
}}"""
            },
            'feasibility_analysis': {
                'name': '可行性分析',
                'description': '专项分析需求的技术可行性',
                'content': """你是一位资深的技术架构师。请深入分析完整需求文档的技术可行性。

【文档内容】
{document}

【分析维度】
1. ⚙️ **技术实现可行性**
   - 技术栈是否成熟可用
   - 实现方案是否现实
   - 技术风险是否可控

2. 📈 **性能可行性**
   - 性能要求是否可达成
   - 并发量是否合理
   - 响应时间是否现实

3. 💰 **资源可行性**
   - 开发时间是否充足
   - 技术团队能力是否匹配
   - 成本预算是否合理

4. 🔗 **集成可行性**
   - 第三方依赖是否可用
   - 系统对接是否可行
   - 数据迁移是否现实

【输出JSON格式】
{{
  "analysis_type": "feasibility_analysis",
  "overall_score": 85,
  "summary": "可行性评估总结，说明需求实现的整体可行性",
  "issues": [
    {{
      "severity": "high",
      "category": "性能不可行",
      "description": "要求支持100万并发在线用户，但无分布式架构设计",
      "location": "第5章性能需求",
      "suggestion": "增加分布式架构设计或调整并发要求至合理范围"
    }}
  ],
  "strengths": ["技术选型合理", "实现方案清晰"],
  "recommendations": ["评估性能压力", "补充技术风险分析"]
}}"""
            },
            'clarity_analysis': {
                'name': '清晰度分析',
                'description': '专项分析需求的清晰度',
                'content': """你是一位资深的需求分析专家。请深入分析完整需求文档的清晰度。

【文档内容】
{document}

【分析维度】
1. 📝 **语言表达清晰度**
   - 用词是否准确无歧义
   - 描述是否简洁明了
   - 是否避免使用模糊词汇

2. 🎯 **需求定义清晰度**
   - 需求边界是否明确
   - 功能范围是否清晰
   - 优先级是否明确

3. 📊 **结构组织清晰度**
   - 文档结构是否合理
   - 章节划分是否清晰
   - 逻辑层次是否分明

4. 🔍 **细节描述清晰度**
   - 关键细节是否充分
   - 示例说明是否到位
   - 图表辅助是否恰当

【输出JSON格式】
{{
  "analysis_type": "clarity_analysis",
  "overall_score": 85,
  "summary": "清晰度评估总结，说明文档的整体清晰程度",
  "issues": [
    {{
      "severity": "medium",
      "category": "描述模糊",
      "description": "使用了'尽可能快'这样的模糊表述",
      "location": "第3.1节登录功能",
      "suggestion": "改为'登录响应时间应≤2秒'等明确描述"
    }}
  ],
  "strengths": ["结构清晰", "术语准确"],
  "recommendations": ["避免模糊词汇", "增加流程图"]
}}"""
            }
        }
        
        # 创建提示词
        created_count = 0
        for prompt_type, prompt_data in prompts_data.items():
            prompt = UserPrompt.objects.create(
                user=user,
                name=prompt_data['name'],
                description=prompt_data['description'],
                content=prompt_data['content'],
                prompt_type=prompt_type,
                is_active=True
            )
            created_count += 1
            print(f"✅ 创建提示词: {prompt.name} ({prompt_type})")
        
        print(f"\n🎉 成功创建 {created_count} 个新架构提示词")
        print("\n📝 新架构说明：")
        print("- 5个专项分析独立处理完整文档")
        print("- 每个分析都有200k上下文可用")
        print("- 不再基于模块拆分，而是基于分析维度")
        
    except User.DoesNotExist:
        print("❌ 用户 'duanxc' 不存在")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
