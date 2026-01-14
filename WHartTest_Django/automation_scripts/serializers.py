from rest_framework import serializers
from .models import AutomationScript, ScriptExecution, ExecutionLog, ScriptTemplate


class AutomationScriptSerializer(serializers.ModelSerializer):
    """自动化脚本序列化器"""
    
    creator_name = serializers.CharField(source='creator.username', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    script_type_display = serializers.CharField(source='get_script_type_display', read_only=True)
    
    class Meta:
        model = AutomationScript
        fields = [
            'id', 'name', 'description', 'script_type', 'script_type_display',
            'status', 'status_display', 'test_cases_content', 'yaml_content',
            'target_url', 'viewport_width', 'viewport_height',
            'ai_model', 'api_key', 'api_endpoint',
            'execution_timeout', 'retry_count',
            'creator', 'creator_name', 'project', 'project_name',
            'created_at', 'updated_at', 'generated_at'
        ]
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at']


class AutomationScriptCreateSerializer(serializers.ModelSerializer):
    """自动化脚本创建序列化器"""
    
    class Meta:
        model = AutomationScript
        fields = [
            'name', 'description', 'script_type', 'test_cases_content',
            'target_url', 'viewport_width', 'viewport_height',
            'ai_model', 'api_key', 'api_endpoint',
            'execution_timeout', 'retry_count', 'project'
        ]


class ScriptExecutionSerializer(serializers.ModelSerializer):
    """脚本执行记录序列化器"""
    
    script_name = serializers.CharField(source='script.name', read_only=True)
    executor_name = serializers.CharField(source='executor.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ScriptExecution
        fields = [
            'id', 'script', 'script_name', 'executor', 'executor_name',
            'status', 'status_display', 'execution_id',
            'exit_code', 'stdout', 'stderr',
            'report_path', 'report_url',
            'total_tests', 'passed_tests', 'failed_tests', 'execution_time',
            'created_at', 'started_at', 'completed_at'
        ]
        read_only_fields = ['id', 'executor', 'created_at']


class ExecutionLogSerializer(serializers.ModelSerializer):
    """执行日志序列化器"""
    
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    
    class Meta:
        model = ExecutionLog
        fields = [
            'id', 'execution', 'level', 'level_display', 'message',
            'timestamp', 'step_name', 'screenshot_path'
        ]
        read_only_fields = ['id', 'timestamp']


class ScriptTemplateSerializer(serializers.ModelSerializer):
    """脚本模板序列化器"""
    
    creator_name = serializers.CharField(source='creator.username', read_only=True)
    template_type_display = serializers.CharField(source='get_template_type_display', read_only=True)
    
    class Meta:
        model = ScriptTemplate
        fields = [
            'id', 'name', 'description', 'template_type', 'template_type_display',
            'yaml_template', 'test_case_template',
            'is_public', 'is_default',
            'creator', 'creator_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at']


class ScriptGenerateSerializer(serializers.Serializer):
    """脚本生成请求序列化器"""
    
    test_cases = serializers.CharField(help_text='测试用例内容')
    script_type = serializers.ChoiceField(
        choices=AutomationScript.SCRIPT_TYPE_CHOICES,
        help_text='脚本类型'
    )
    target_url = serializers.URLField(required=False, help_text='目标URL')
    ai_model = serializers.CharField(default='qwen-turbo', help_text='AI模型')


class ScriptExecuteSerializer(serializers.Serializer):
    """脚本执行请求序列化器"""
    
    execution_mode = serializers.ChoiceField(
        choices=[('single', '单个执行'), ('batch', '批量执行')],
        default='single',
        help_text='执行模式'
    )
    timeout = serializers.IntegerField(default=300, help_text='超时时间(秒)')
    retry_count = serializers.IntegerField(default=1, help_text='重试次数')