"""
LangGraph Checkpointer 工厂模块

根据 DATABASE_TYPE 环境变量自动选择合适的 Checkpointer：
- sqlite: 使用 SqliteSaver/AsyncSqliteSaver（默认，本地开发）
- postgres: 使用 PostgresSaver/AsyncPostgresSaver（生产环境）
"""
import os
from contextlib import asynccontextmanager, contextmanager
from typing import Optional
from django.conf import settings


def get_database_type() -> str:
    """获取数据库类型配置（每次调用时读取，确保环境变量已加载）"""
    return os.environ.get('DATABASE_TYPE', 'postgres')


def get_db_connection_string() -> str:
    """获取数据库连接字符串"""
    database_type = get_database_type()
    if database_type == 'postgres':
        user = os.environ.get('POSTGRES_USER', 'postgres')
        password = os.environ.get('POSTGRES_PASSWORD', 'postgres')
        host = os.environ.get('POSTGRES_HOST', 'localhost')
        port = os.environ.get('POSTGRES_PORT', '5432')
        db = os.environ.get('POSTGRES_DB', 'wharttest')
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    else:
        return os.path.join(str(settings.BASE_DIR), "chat_history.sqlite")


def get_sqlite_path() -> str:
    """获取 SQLite 文件路径（仅用于 SQLite 模式的文件存在性检查）"""
    return os.path.join(str(settings.BASE_DIR), "chat_history.sqlite")


@asynccontextmanager
async def get_async_checkpointer():
    """
    获取异步 Checkpointer 的上下文管理器
    
    用法:
        async with get_async_checkpointer() as checkpointer:
            # 使用 checkpointer
    """
    conn_string = get_db_connection_string()
    
    if get_database_type() == 'postgres':
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
            await checkpointer.setup()
            yield checkpointer
    else:
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        async with AsyncSqliteSaver.from_conn_string(conn_string) as checkpointer:
            yield checkpointer


@contextmanager
def get_sync_checkpointer():
    """
    获取同步 Checkpointer 的上下文管理器
    
    用法:
        with get_sync_checkpointer() as checkpointer:
            # 使用 checkpointer
    """
    conn_string = get_db_connection_string()
    
    if get_database_type() == 'postgres':
        from langgraph.checkpoint.postgres import PostgresSaver
        with PostgresSaver.from_conn_string(conn_string) as checkpointer:
            checkpointer.setup()
            yield checkpointer
    else:
        from langgraph.checkpoint.sqlite import SqliteSaver
        with SqliteSaver.from_conn_string(conn_string) as checkpointer:
            yield checkpointer


def delete_checkpoints_by_thread_id(thread_id: str) -> int:
    """
    根据 thread_id 删除 checkpoints
    
    返回删除的记录数
    """
    if get_database_type() == 'postgres':
        import psycopg2
        conn_string = get_db_connection_string()
        try:
            conn = psycopg2.connect(conn_string)
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM checkpoints WHERE thread_id = %s", (thread_id,))
                deleted_count = cursor.rowcount
                conn.commit()
                return deleted_count
            finally:
                conn.close()
        except psycopg2.errors.UndefinedTable:
            return 0
        except Exception:
            return 0
    else:
        import sqlite3
        db_path = get_sqlite_path()
        if not os.path.exists(db_path):
            return 0
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
        finally:
            conn.close()


def delete_checkpoints_batch(thread_ids: list) -> int:
    """
    批量删除多个 thread_id 的 checkpoints
    
    返回删除的总记录数
    """
    if not thread_ids:
        return 0
    
    if get_database_type() == 'postgres':
        import psycopg2
        conn_string = get_db_connection_string()
        try:
            conn = psycopg2.connect(conn_string)
            try:
                cursor = conn.cursor()
                # PostgreSQL 使用 ANY 语法
                cursor.execute("DELETE FROM checkpoints WHERE thread_id = ANY(%s)", (thread_ids,))
                deleted_count = cursor.rowcount
                conn.commit()
                return deleted_count
            finally:
                conn.close()
        except psycopg2.errors.UndefinedTable:
            return 0
        except Exception:
            return 0
    else:
        import sqlite3
        db_path = get_sqlite_path()
        if not os.path.exists(db_path):
            return 0
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            # SQLite 使用 IN 语法
            placeholders = ','.join('?' * len(thread_ids))
            cursor.execute(f"DELETE FROM checkpoints WHERE thread_id IN ({placeholders})", thread_ids)
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
        finally:
            conn.close()


def check_history_exists() -> bool:
    """
    检查聊天历史存储是否存在（SQLite 文件或 PostgreSQL 表）
    """
    if get_database_type() == 'postgres':
        import psycopg2
        conn_string = get_db_connection_string()
        try:
            conn = psycopg2.connect(conn_string)
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'checkpoints')")
                result = cursor.fetchone()
                return result[0] if result else False
            finally:
                conn.close()
        except Exception:
            return False
    else:
        db_path = get_sqlite_path()
        return os.path.exists(db_path)


def get_thread_ids_by_prefix(prefix: str) -> list:
    """
    根据前缀查询所有匹配的 thread_id
    
    返回 thread_id 列表
    """
    if get_database_type() == 'postgres':
        import psycopg2
        conn_string = get_db_connection_string()
        try:
            conn = psycopg2.connect(conn_string)
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT thread_id FROM checkpoints WHERE thread_id LIKE %s", (prefix + '%',))
                rows = cursor.fetchall()
                return [row[0] for row in rows]
            finally:
                conn.close()
        except psycopg2.errors.UndefinedTable:
            # checkpoints 表不存在，返回空列表
            return []
        except Exception:
            return []
    else:
        import sqlite3
        db_path = get_sqlite_path()
        if not os.path.exists(db_path):
            return []
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT thread_id FROM checkpoints WHERE thread_id LIKE ?", (prefix + '%',))
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        finally:
            conn.close()
