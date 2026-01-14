import os
import asyncio
import logging
from django.http import HttpResponse, Http404, FileResponse
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from wharttest_django.viewsets import BaseModelViewSet
from projects.models import Project

from .models import AutomationScript, ScriptExecution, ExecutionLog, ScriptTemplate
from .serializers import (
    AutomationScriptSerializer, AutomationScriptCreateSerializer,
    ScriptExecutionSerializer, ExecutionLogSerializer, ScriptTemplateSerializer,
    ScriptGenerateSerializer, ScriptExecuteSerializer
)
from .services import AutomationScriptService

logger = logging.getLogger(__name__)


class AutomationScriptViewSet(BaseModelViewSet):
    """自动化脚本视图集"""
    
    queryset = AutomationScript.objects.all()
    serializer_class = AutomationScriptSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['script_type', 'status', 'project']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AutomationScriptCreateSerializer
        return AutomationScriptSerializer
    
    def get_queryset(self):
        """获取当前用户有权限的脚本"""
        queryset = super().get_queryset()
        # 只返回用户有权限访问的项目的脚本
        if hasattr(self.request.user, 'project_permissions'):
            accessible_projects = self.request.user.project_permissions.values_list('project_id', flat=True)
            queryset = queryset.filter(project_id__in=accessible_projects)
        return queryset
    
    def perform_create(self, serializer):
        """创建脚本"""
        try:
            # 获取项目
            project_id = serializer.validated_data.get('project')
            if isinstance(project_id, Project):
                project = project_id
            else:
                project = Project.objects.get(id=project_id)
            
            # 创建脚本
            script = AutomationScriptService.create_script(
                data=serializer.validated_data,
                creator=self.request.user,
                project=project
            )
            
            serializer.instance = script
            
        except Exception as e:
            logger.error(f"创建脚本失败: {str(e)}")
            raise
    
    @action(detail=True, methods=['post'])
    def generate_yaml(self, request, pk=None):
        """生成YAML脚本"""
        try:
            script = self.get_object()
            
            # 检查权限
            if script.creator != request.user:
                return Response(
                    {'error': '只有脚本创建者可以生成脚本'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # 检查状态
            if script.status not in ['draft', 'failed']:
                return Response(
                    {'error': f'脚本状态不允许重新生成: {script.status}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 生成脚本
            script = AutomationScriptService.generate_yaml_script(script)
            
            serializer = self.get_serializer(script)
            return Response({
                'message': 'YAML脚本生成成功',
                'script': serializer.data
            })
            
        except Exception as e:
            logger.error(f"生成YAML脚本失败: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """执行脚本"""
        try:
            script = self.get_object()
            
            # 验证请求数据
            serializer = ScriptExecuteSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # 检查脚本状态
            if script.status not in ['generated', 'ready', 'completed']:
                return Response(
                    {'error': f'脚本状态不允许执行: {script.status}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 异步执行脚本
            def run_script():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    execution = loop.run_until_complete(
                        AutomationScriptService.execute_script(script, request.user)
                    )
                    loop.close()
                except Exception as e:
                    logger.error(f"异步执行脚本失败: {str(e)}")
            
            import threading
            thread = threading.Thread(target=run_script)
            thread.daemon = True
            thread.start()
            
            return Response({
                'message': '脚本执行已开始，请稍后查看执行记录',
                'script_id': script.id
            })
            
        except Exception as e:
            logger.error(f"执行脚本失败: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        """获取脚本执行记录"""
        try:
            script = self.get_object()
            executions = script.executions.all().order_by('-created_at')
            
            # 分页
            page = self.paginate_queryset(executions)
            if page is not None:
                serializer = ScriptExecutionSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = ScriptExecutionSerializer(executions, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"获取执行记录失败: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def download_yaml(self, request, pk=None):
        """下载YAML脚本"""
        try:
            script = self.get_object()
            
            if not script.yaml_content:
                return Response(
                    {'error': '脚本未生成'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 创建响应
            response = HttpResponse(
                script.yaml_content,
                content_type='application/x-yaml'
            )
            response['Content-Disposition'] = f'attachment; filename="{script.name}.yaml"'
            
            return response
            
        except Exception as e:
            logger.error(f"下载YAML脚本失败: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ScriptExecutionViewSet(BaseModelViewSet):
    """脚本执行记录视图集"""
    
    queryset = ScriptExecution.objects.all()
    serializer_class = ScriptExecutionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['script', 'status', 'executor']
    ordering_fields = ['created_at', 'started_at', 'completed_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """获取当前用户有权限的执行记录"""
        queryset = super().get_queryset()
        # 只返回用户有权限访问的项目的执行记录
        if hasattr(self.request.user, 'project_permissions'):
            accessible_projects = self.request.user.project_permissions.values_list('project_id', flat=True)
            queryset = queryset.filter(script__project_id__in=accessible_projects)
        return queryset
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """获取执行日志"""
        try:
            execution = self.get_object()
            logs = execution.logs.all().order_by('timestamp')
            
            # 分页
            page = self.paginate_queryset(logs)
            if page is not None:
                serializer = ExecutionLogSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = ExecutionLogSerializer(logs, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"获取执行日志失败: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """停止执行"""
        try:
            execution = self.get_object()
            
            if execution.status != 'running':
                return Response(
                    {'error': '只能停止正在运行的执行'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 调用服务停止执行
            AutomationScriptService.stop_execution(execution)
            
            return Response({'message': '执行已停止'})
            
        except Exception as e:
            logger.error(f"停止执行失败: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def screenshots(self, request, pk=None):
        """获取执行截图"""
        try:
            execution = self.get_object()
            
            # 获取截图文件列表
            screenshots = AutomationScriptService.get_execution_screenshots(execution)
            
            return Response(screenshots)
            
        except Exception as e:
            logger.error(f"获取截图失败: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def rerun(self, request, pk=None):
        """重新执行脚本"""
        try:
            execution = self.get_object()
            
            # 创建新的执行记录
            new_execution = AutomationScriptService.rerun_script(execution, request.user)
            
            serializer = self.get_serializer(new_execution)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"重新执行失败: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """分享报告"""
        try:
            execution = self.get_object()
            
            # 生成分享链接
            share_url = AutomationScriptService.generate_share_url(execution)
            
            return Response({'share_url': share_url})
            
        except Exception as e:
            logger.error(f"分享报告失败: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """获取执行统计"""
        try:
            project_id = request.query_params.get('project_id')
            date_range = request.query_params.getlist('date_range')
            
            stats = AutomationScriptService.get_execution_stats(
                project_id=project_id,
                date_range=date_range,
                user=request.user
            )
            
            return Response(stats)
            
        except Exception as e:
            logger.error(f"获取统计数据失败: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """导出执行报告"""
        try:
            # 获取筛选参数
            filters = {
                'script_name': request.query_params.get('script_name'),
                'status': request.query_params.get('status'),
                'project_id': request.query_params.get('project_id'),
                'date_start': request.query_params.get('date_start'),
                'date_end': request.query_params.get('date_end'),
            }
            
            # 导出Excel文件
            excel_file = AutomationScriptService.export_execution_reports(filters, request.user)
            
            response = HttpResponse(
                excel_file,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="execution_reports_{timezone.now().strftime("%Y%m%d")}.xlsx"'
            
            return response
            
        except Exception as e:
            logger.error(f"导出报告失败: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def compare(self, request):
        """对比报告"""
        try:
            base_report_id = request.data.get('base_report_id')
            compare_report_id = request.data.get('compare_report_id')
            
            if not base_report_id or not compare_report_id:
                return Response(
                    {'error': '请提供要对比的报告ID'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 获取报告
            base_execution = self.get_queryset().get(id=base_report_id)
            compare_execution = self.get_queryset().get(id=compare_report_id)
            
            # 执行对比
            comparison_result = AutomationScriptService.compare_executions(
                base_execution, 
                compare_execution
            )
            
            return Response(comparison_result)
            
        except ScriptExecution.DoesNotExist:
            return Response(
                {'error': '报告不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"对比报告失败: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        """获取测试报告"""
        try:
            execution = self.get_object()
            
            if not execution.report_path or not os.path.exists(execution.report_path):
                return Response(
                    {'error': '报告文件不存在'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 获取请求的文件路径
            file_path = request.GET.get('path', 'index.html')
            full_path = os.path.join(execution.report_path, file_path)
            
            # 安全检查
            if not full_path.startswith(execution.report_path):
                return Response(
                    {'error': '非法的文件路径'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not os.path.exists(full_path):
                raise Http404("文件不存在")
            
            # 返回文件
            return FileResponse(
                open(full_path, 'rb'),
                content_type=self._get_content_type(file_path)
            )
            
        except Exception as e:
            logger.error(f"获取测试报告失败: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_content_type(self, file_path: str) -> str:
        """获取文件内容类型"""
        ext = os.path.splitext(file_path)[1].lower()
        content_types = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
        }
        return content_types.get(ext, 'application/octet-stream')
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消执行"""
        try:
            execution = self.get_object()
            
            if execution.status not in ['pending', 'running']:
                return Response(
                    {'error': f'执行状态不允许取消: {execution.status}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 更新状态
            execution.status = 'cancelled'
            execution.completed_at = timezone.now()
            execution.save()
            
            # 记录日志
            ExecutionLog.objects.create(
                execution=execution,
                level='info',
                message='执行已被用户取消'
            )
            
            return Response({'message': '执行已取消'})
            
        except Exception as e:
            logger.error(f"取消执行失败: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ScriptTemplateViewSet(BaseModelViewSet):
    """脚本模板视图集"""
    
    queryset = ScriptTemplate.objects.all()
    serializer_class = ScriptTemplateSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['template_type', 'is_public', 'is_default']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """获取模板列表"""
        queryset = super().get_queryset()
        # 只返回公开模板或用户自己创建的模板
        return queryset.filter(
            models.Q(is_public=True) | models.Q(creator=self.request.user)
        )
    
    def perform_create(self, serializer):
        """创建模板"""
        serializer.save(creator=self.request.user)
    
    @action(detail=False, methods=['get'])
    def default_templates(self, request):
        """获取默认模板"""
        templates = self.queryset.filter(is_default=True, is_public=True)
        serializer = self.get_serializer(templates, many=True)
        return Response(serializer.data)