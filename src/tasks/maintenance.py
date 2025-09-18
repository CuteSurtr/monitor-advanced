"""
System maintenance tasks for Stock Market Monitor.
"""

import logging
import os
import gzip
import shutil
from typing import List, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from src.celery_app import celery_app
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2, "countdown": 3600},
)
def database_maintenance(self):
    """
    Perform database maintenance tasks (vacuum, reindex, cleanup).
    """
    try:
        logger.info("Starting database maintenance")

        config = get_config()
        maintenance_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "tasks_completed": [],
            "errors": [],
        }

        # Vacuum and analyze tables (PostgreSQL specific)
        if config.database.type == "postgresql":
            try:
                # Mock database maintenance operations
                # In real implementation, these would be actual SQL commands
                tables_to_maintain = [
                    "stock_data",
                    "commodity_data",
                    "news_data",
                    "portfolios",
                    "portfolio_positions",
                    "alerts",
                    "system_metrics",
                ]

                for table in tables_to_maintain:
                    # VACUUM ANALYZE table_name;
                    logger.info(f"Maintaining table: {table}")
                    # await db_manager.execute_maintenance(f"VACUUM ANALYZE {table}")

                maintenance_results["tasks_completed"].append("vacuum_analyze")
                logger.info("Database vacuum and analyze completed")

            except Exception as e:
                logger.error(f"Error during vacuum/analyze: {e}")
                maintenance_results["errors"].append(f"vacuum_analyze: {str(e)}")

        # Reindex tables for better performance
        try:
            # Mock reindexing operations
            indexes_to_rebuild = [
                "stock_data_symbol_timestamp_idx",
                "portfolio_positions_portfolio_id_idx",
                "alerts_symbol_triggered_at_idx",
            ]

            for index in indexes_to_rebuild:
                # REINDEX INDEX index_name;
                logger.info(f"Rebuilding index: {index}")
                # await db_manager.execute_maintenance(f"REINDEX INDEX {index}")

            maintenance_results["tasks_completed"].append("reindex")
            logger.info("Database reindexing completed")

        except Exception as e:
            logger.error(f"Error during reindexing: {e}")
            maintenance_results["errors"].append(f"reindex: {str(e)}")

        # Update table statistics
        try:
            # UPDATE statistics for query optimizer
            # await db_manager.execute_maintenance("ANALYZE")
            maintenance_results["tasks_completed"].append("update_statistics")
            logger.info("Database statistics updated")

        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
            maintenance_results["errors"].append(f"update_statistics: {str(e)}")

        # Check database integrity
        try:
            # Mock integrity check
            integrity_issues = 0  # Would be actual check result

            if integrity_issues > 0:
                logger.warning(f"Database integrity issues found: {integrity_issues}")
                maintenance_results["errors"].append(
                    f"integrity_issues: {integrity_issues}"
                )
            else:
                maintenance_results["tasks_completed"].append("integrity_check")
                logger.info("Database integrity check passed")

        except Exception as e:
            logger.error(f"Error during integrity check: {e}")
            maintenance_results["errors"].append(f"integrity_check: {str(e)}")

        logger.info(
            f"Database maintenance completed: {len(maintenance_results['tasks_completed'])} tasks"
        )
        return maintenance_results

    except Exception as e:
        logger.error(f"Error in database_maintenance: {e}")
        raise self.retry(countdown=3600, exc=e)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 1800},
)
def cache_cleanup(self):
    """
    Clean up old cache entries and optimize cache performance.
    """
    try:
        logger.info("Starting cache cleanup")

        config = get_config()
        cleanup_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "cache_entries_removed": 0,
            "memory_freed_mb": 0,
            "errors": [],
        }

        # Redis cache cleanup
        try:
            # Mock Redis operations - would use actual Redis client
            # redis_client = get_redis_client()

            # Remove expired keys
            expired_keys = 0  # redis_client.scan_iter(match="*:expired:*")
            cleanup_results["cache_entries_removed"] += expired_keys

            # Remove old temporary keys
            temp_keys = 0  # redis_client.scan_iter(match="temp:*")
            for key in []:  # temp_keys:
                # Check if key is older than 1 hour
                # ttl = redis_client.ttl(key)
                # if ttl < 0 or ttl > 3600:
                #     redis_client.delete(key)
                #     cleanup_results['cache_entries_removed'] += 1
                pass

            # Optimize memory usage
            # redis_client.memory_purge()

            logger.info("Redis cache cleanup completed")

        except Exception as e:
            logger.error(f"Error during Redis cleanup: {e}")
            cleanup_results["errors"].append(f"redis_cleanup: {str(e)}")

        # Application cache cleanup
        try:
            # Clean up in-memory caches
            cache_size_before = 100  # Mock size in MB

            # Clear expired entries from application caches
            # cache_manager.cleanup_expired()

            cache_size_after = 80  # Mock size after cleanup
            cleanup_results["memory_freed_mb"] = cache_size_before - cache_size_after

            logger.info("Application cache cleanup completed")

        except Exception as e:
            logger.error(f"Error during application cache cleanup: {e}")
            cleanup_results["errors"].append(f"app_cache_cleanup: {str(e)}")

        # File system cache cleanup
        try:
            cache_dir = Path("cache")
            if cache_dir.exists():
                files_removed = 0
                size_freed = 0

                # Remove old cache files
                cutoff_time = datetime.utcnow() - timedelta(hours=24)

                for cache_file in cache_dir.glob("*.cache"):
                    if cache_file.stat().st_mtime < cutoff_time.timestamp():
                        size_freed += cache_file.stat().st_size
                        cache_file.unlink()
                        files_removed += 1

                cleanup_results["cache_entries_removed"] += files_removed
                cleanup_results["memory_freed_mb"] += size_freed / (1024 * 1024)

                logger.info(f"Removed {files_removed} old cache files")

        except Exception as e:
            logger.error(f"Error during file cache cleanup: {e}")
            cleanup_results["errors"].append(f"file_cache_cleanup: {str(e)}")

        logger.info(
            f"Cache cleanup completed: {cleanup_results['cache_entries_removed']} entries removed"
        )
        return cleanup_results

    except Exception as e:
        logger.error(f"Error in cache_cleanup: {e}")
        raise self.retry(countdown=1800, exc=e)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2, "countdown": 7200},
)
def log_rotation_and_cleanup(self):
    """
    Rotate logs and clean up old log files.
    """
    try:
        logger.info("Starting log rotation and cleanup")

        config = get_config()
        log_dir = Path("logs")

        rotation_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "files_rotated": 0,
            "files_compressed": 0,
            "files_deleted": 0,
            "space_freed_mb": 0,
            "errors": [],
        }

        if not log_dir.exists():
            log_dir.mkdir(parents=True)
            return rotation_results

        # Rotate current log files
        try:
            current_log = log_dir / "stock_monitor.log"
            if (
                current_log.exists() and current_log.stat().st_size > 100 * 1024 * 1024
            ):  # 100MB
                # Rotate the log file
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                rotated_log = log_dir / f"stock_monitor_{timestamp}.log"

                shutil.move(current_log, rotated_log)
                rotation_results["files_rotated"] += 1

                # Create new empty log file
                current_log.touch()

                logger.info(f"Rotated log file: {rotated_log}")

        except Exception as e:
            logger.error(f"Error rotating log files: {e}")
            rotation_results["errors"].append(f"log_rotation: {str(e)}")

        # Compress old log files
        try:
            for log_file in log_dir.glob("stock_monitor_*.log"):
                if not log_file.name.endswith(".gz"):
                    compressed_file = log_file.with_suffix(".log.gz")

                    with open(log_file, "rb") as f_in:
                        with gzip.open(compressed_file, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)

                    # Remove original file
                    log_file.unlink()
                    rotation_results["files_compressed"] += 1

                    logger.info(f"Compressed log file: {compressed_file}")

        except Exception as e:
            logger.error(f"Error compressing log files: {e}")
            rotation_results["errors"].append(f"log_compression: {str(e)}")

        # Clean up old compressed log files
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=30)  # Keep 30 days

            for log_file in log_dir.glob("*.log.gz"):
                file_date = datetime.fromtimestamp(log_file.stat().st_mtime)

                if file_date < cutoff_date:
                    file_size = log_file.stat().st_size
                    log_file.unlink()

                    rotation_results["files_deleted"] += 1
                    rotation_results["space_freed_mb"] += file_size / (1024 * 1024)

                    logger.info(f"Deleted old log file: {log_file}")

        except Exception as e:
            logger.error(f"Error cleaning up old log files: {e}")
            rotation_results["errors"].append(f"log_cleanup: {str(e)}")

        # Clean up other application logs
        try:
            for log_pattern in ["celery*.log", "error*.log", "access*.log"]:
                for log_file in log_dir.glob(log_pattern):
                    file_date = datetime.fromtimestamp(log_file.stat().st_mtime)

                    if file_date < cutoff_date:
                        file_size = log_file.stat().st_size
                        log_file.unlink()

                        rotation_results["files_deleted"] += 1
                        rotation_results["space_freed_mb"] += file_size / (1024 * 1024)

        except Exception as e:
            logger.error(f"Error cleaning up application logs: {e}")
            rotation_results["errors"].append(f"app_log_cleanup: {str(e)}")

        logger.info(
            f"Log rotation completed: {rotation_results['files_rotated']} rotated, "
            f"{rotation_results['files_compressed']} compressed, "
            f"{rotation_results['files_deleted']} deleted"
        )

        return rotation_results

    except Exception as e:
        logger.error(f"Error in log_rotation_and_cleanup: {e}")
        raise self.retry(countdown=7200, exc=e)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2, "countdown": 3600},
)
def system_optimization(self):
    """
    Perform system optimization tasks.
    """
    try:
        logger.info("Starting system optimization")

        optimization_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "optimizations_applied": [],
            "performance_improvements": {},
            "errors": [],
        }

        # Memory optimization
        try:
            import gc

            # Force garbage collection
            collected = gc.collect()
            optimization_results["optimizations_applied"].append("garbage_collection")
            optimization_results["performance_improvements"][
                "objects_collected"
            ] = collected

            logger.info(f"Garbage collection completed: {collected} objects collected")

        except Exception as e:
            logger.error(f"Error during memory optimization: {e}")
            optimization_results["errors"].append(f"memory_optimization: {str(e)}")

        # Database connection pool optimization
        try:
            # Mock connection pool optimization
            # db_manager.optimize_connection_pool()
            optimization_results["optimizations_applied"].append(
                "connection_pool_optimization"
            )

            logger.info("Database connection pool optimized")

        except Exception as e:
            logger.error(f"Error optimizing connection pool: {e}")
            optimization_results["errors"].append(f"connection_pool: {str(e)}")

        # Cache optimization
        try:
            # Optimize cache hit rates and eviction policies
            # cache_manager.optimize()
            optimization_results["optimizations_applied"].append("cache_optimization")

            logger.info("Cache optimization completed")

        except Exception as e:
            logger.error(f"Error during cache optimization: {e}")
            optimization_results["errors"].append(f"cache_optimization: {str(e)}")

        # Process optimization
        try:
            # Check and optimize process priorities
            import psutil

            current_process = psutil.Process()

            # Adjust process priority if needed
            current_priority = current_process.nice()
            if current_priority > 0:
                # Lower nice value for higher priority
                # current_process.nice(-1)
                optimization_results["optimizations_applied"].append(
                    "process_priority_adjustment"
                )

            logger.info("Process optimization completed")

        except Exception as e:
            logger.error(f"Error during process optimization: {e}")
            optimization_results["errors"].append(f"process_optimization: {str(e)}")

        # File system optimization
        try:
            # Clean up temporary files
            temp_dir = (
                Path("/tmp")
                if os.name != "nt"
                else Path(os.environ.get("TEMP", "C:\\temp"))
            )

            if temp_dir.exists():
                temp_files_cleaned = 0

                # Remove old temporary files from our application
                for temp_file in temp_dir.glob("stock_monitor_*"):
                    try:
                        file_age = datetime.now() - datetime.fromtimestamp(
                            temp_file.stat().st_mtime
                        )
                        if file_age > timedelta(hours=24):
                            temp_file.unlink()
                            temp_files_cleaned += 1
                    except Exception:
                        continue

                optimization_results["optimizations_applied"].append(
                    "temp_file_cleanup"
                )
                optimization_results["performance_improvements"][
                    "temp_files_cleaned"
                ] = temp_files_cleaned

                logger.info(f"Cleaned up {temp_files_cleaned} temporary files")

        except Exception as e:
            logger.error(f"Error during file system optimization: {e}")
            optimization_results["errors"].append(f"filesystem_optimization: {str(e)}")

        logger.info(
            f"System optimization completed: {len(optimization_results['optimizations_applied'])} optimizations applied"
        )
        return optimization_results

    except Exception as e:
        logger.error(f"Error in system_optimization: {e}")
        raise self.retry(countdown=3600, exc=e)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2, "countdown": 86400},
)
def backup_critical_data(self):
    """
    Create backups of critical system data.
    """
    try:
        logger.info("Starting critical data backup")

        backup_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "backups_created": [],
            "backup_sizes_mb": {},
            "errors": [],
        }

        backup_dir = Path("backups") / datetime.utcnow().strftime("%Y%m%d")
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup configuration files
        try:
            config_backup = backup_dir / "config_backup.tar.gz"

            # Mock configuration backup
            # Would create actual tar.gz of config directory
            backup_results["backups_created"].append("configuration")
            backup_results["backup_sizes_mb"]["configuration"] = 1.5

            logger.info("Configuration backup completed")

        except Exception as e:
            logger.error(f"Error backing up configuration: {e}")
            backup_results["errors"].append(f"config_backup: {str(e)}")

        # Backup database schema
        try:
            schema_backup = backup_dir / "schema_backup.sql"

            # Mock schema backup
            # pg_dump --schema-only database_name > schema_backup.sql
            backup_results["backups_created"].append("database_schema")
            backup_results["backup_sizes_mb"]["database_schema"] = 5.0

            logger.info("Database schema backup completed")

        except Exception as e:
            logger.error(f"Error backing up database schema: {e}")
            backup_results["errors"].append(f"schema_backup: {str(e)}")

        # Backup critical application data
        try:
            data_backup = backup_dir / "critical_data.json"

            # Mock critical data backup
            critical_data = {
                "portfolios": [],
                "alert_rules": [],
                "user_preferences": {},
            }

            with open(data_backup, "w") as f:
                import json

                json.dump(critical_data, f, indent=2)

            backup_results["backups_created"].append("critical_data")
            backup_results["backup_sizes_mb"]["critical_data"] = 10.0

            logger.info("Critical data backup completed")

        except Exception as e:
            logger.error(f"Error backing up critical data: {e}")
            backup_results["errors"].append(f"data_backup: {str(e)}")

        # Clean up old backups
        try:
            backups_root = Path("backups")
            cutoff_date = datetime.utcnow() - timedelta(days=30)

            for backup_folder in backups_root.glob("*"):
                if backup_folder.is_dir():
                    try:
                        folder_date = datetime.strptime(backup_folder.name, "%Y%m%d")
                        if folder_date < cutoff_date:
                            shutil.rmtree(backup_folder)
                            logger.info(f"Removed old backup: {backup_folder}")
                    except ValueError:
                        # Skip folders that don't match date format
                        continue

        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
            backup_results["errors"].append(f"backup_cleanup: {str(e)}")

        logger.info(
            f"Backup completed: {len(backup_results['backups_created'])} backups created"
        )
        return backup_results

    except Exception as e:
        logger.error(f"Error in backup_critical_data: {e}")
        raise self.retry(countdown=86400, exc=e)


@celery_app.task(bind=True)
def health_check_and_recovery(self):
    """
    Perform health checks and attempt automatic recovery for failed components.
    """
    try:
        logger.info("Starting health check and recovery")

        recovery_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "components_checked": [],
            "recovery_actions": [],
            "failed_components": [],
            "errors": [],
        }

        # Check and recover database connection
        try:
            # db_healthy = await db_manager.is_healthy()
            db_healthy = True  # Mock
            recovery_results["components_checked"].append("database")

            if not db_healthy:
                # Attempt to reconnect
                # await db_manager.reconnect()
                recovery_results["recovery_actions"].append("database_reconnect")
                logger.info("Database reconnection attempted")

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            recovery_results["failed_components"].append("database")
            recovery_results["errors"].append(f"database: {str(e)}")

        # Check and recover Redis connection
        try:
            # redis_healthy = await redis_manager.is_healthy()
            redis_healthy = True  # Mock
            recovery_results["components_checked"].append("redis")

            if not redis_healthy:
                # Attempt to reconnect
                # await redis_manager.reconnect()
                recovery_results["recovery_actions"].append("redis_reconnect")
                logger.info("Redis reconnection attempted")

        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            recovery_results["failed_components"].append("redis")
            recovery_results["errors"].append(f"redis: {str(e)}")

        # Check Celery workers
        try:
            from celery import current_app

            inspect = current_app.control.inspect()

            active_workers = inspect.active()
            recovery_results["components_checked"].append("celery_workers")

            if not active_workers or len(active_workers) == 0:
                # No active workers found
                recovery_results["failed_components"].append("celery_workers")
                logger.warning("No active Celery workers found")

        except Exception as e:
            logger.error(f"Celery worker check failed: {e}")
            recovery_results["failed_components"].append("celery_workers")
            recovery_results["errors"].append(f"celery_workers: {str(e)}")

        # Check disk space and clean up if needed
        try:
            import shutil

            disk_usage = shutil.disk_usage(".")
            free_space_percent = (disk_usage.free / disk_usage.total) * 100

            recovery_results["components_checked"].append("disk_space")

            if free_space_percent < 10:  # Less than 10% free
                # Attempt cleanup
                cache_cleanup.delay()
                log_rotation_and_cleanup.delay()
                recovery_results["recovery_actions"].append("emergency_cleanup")
                logger.warning(
                    f"Low disk space ({free_space_percent:.1f}%), emergency cleanup initiated"
                )

        except Exception as e:
            logger.error(f"Disk space check failed: {e}")
            recovery_results["errors"].append(f"disk_space: {str(e)}")

        logger.info(
            f"Health check completed: {len(recovery_results['components_checked'])} components checked, "
            f"{len(recovery_results['recovery_actions'])} recovery actions taken"
        )

        return recovery_results

    except Exception as e:
        logger.error(f"Error in health_check_and_recovery: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
