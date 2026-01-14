from django.contrib import admin
from .models import AutomationScript, ScriptExecution, ExecutionLog, ScriptTemplate


@admin.register(AutomationScript)
class AutomationScriptAdmin(admin.ModelAdmin):
    list_display = ['name', 'script_type', 'status', 'creator', 'project', 'created_at']
    list_filter = ['script_type', 'status', 'created_at']
    search_fields = ['name', 'description', 'creator__username']
    readonly_fields = ['id', 'created_at', 'updated_at', 'generated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'description', 'script_type', 'status', 'project', 'creator')
        }),
        ('测试内容', {
            'fields': ('test_cases_content', 'yaml_content')
        }),
        ('配置信息', {
            'fields': ('target_url', 'viewport_width', 'viewport_height', 'ai_model', 'api_key', 'api_endpoint')
        }),
        ('执行配置', {
            'fields': ('execution_timeout', 'retry_count')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at', 'generated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ScriptExecution)
class ScriptExecutionAdmin(admin.ModelAdmin):
    list_display = ['execution_id', 'script', 'status', 'executor', 'created_at', 'execution_time']
    list_filter = ['status', 'created_at']
    search_fields = ['execution_id', 'script__name', 'executor__username']
    readonly_fields = ['id', 'created_at', 'started_at', 'completed_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('script', 'executor', 'status', 'execution_id')
        }),
        ('执行结果', {
            'fields': ('exit_code', 'stdout', 'stderr', 'report_path', 'report_url')
        }),
        ('统计信息', {
            'fields': ('total_tests', 'passed_tests', 'failed_tests', 'execution_time')
        }),
        ('时间信息', {
            'fields': ('created_at', 'started_at', 'completed_at')
        })
    )


@admin.register(ExecutionLog)
class ExecutionLogAdmin(admin.ModelAdmin):
    list_display = ['execution', 'level', 'message', 'timestamp']
    list_filter = ['level', 'timestamp']
    search_fields = ['execution__execution_id', 'message']
    readonly_fields = ['id', 'timestamp']


@admin.register(ScriptTemplate)
class ScriptTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'is_public', 'is_default', 'creator', 'created_at']
    list_filter = ['template_type', 'is_public', 'is_default', 'created_at']
    search_fields = ['name', 'description', 'creator__username']
    readonly_fields = ['id', 'created_at', 'updated_at']