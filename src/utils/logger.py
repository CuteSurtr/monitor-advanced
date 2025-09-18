"""
Logging configuration for the stock monitoring system.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
import structlog
from structlog.stdlib import LoggerFactory


def setup_logging(config) -> structlog.stdlib.BoundLogger:
    """
    Setup structured logging for the application.

    Args:
        config: Configuration object containing logging settings

    Returns:
        Configured logger instance
    """

    # Create logs directory if it doesn't exist
    log_file = Path(config.logging.file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            (
                structlog.processors.JSONRenderer()
                if config.logging.format == "json"
                else structlog.dev.ConsoleRenderer()
            ),
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, config.logging.level.upper()),
    )

    # Setup file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=parse_size(config.logging.max_size),
        backupCount=config.logging.backup_count,
        encoding="utf-8",
    )

    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)

    # Create formatter
    if config.logging.format == "json":
        formatter = logging.Formatter("%(message)s")
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Get root logger and add handlers
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Create and return the main application logger
    logger = structlog.get_logger("stock_monitor")

    # Log startup information
    logger.info(
        "Logging system initialized",
        log_level=config.logging.level,
        log_format=config.logging.format,
        log_file=str(log_file),
        max_size=config.logging.max_size,
        backup_count=config.logging.backup_count,
    )

    return logger


def parse_size(size_str: str) -> int:
    """
    Parse size string (e.g., '100MB', '1GB') to bytes.

    Args:
        size_str: Size string with unit

    Returns:
        Size in bytes
    """
    size_str = size_str.upper()

    if size_str.endswith("KB"):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith("MB"):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith("GB"):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        return int(size_str)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return structlog.get_logger(name)


# Context managers for logging
class LogContext:
    """Context manager for adding context to log messages."""

    def __init__(self, logger: structlog.stdlib.BoundLogger, **context):
        self.logger = logger
        self.context = context

    def __enter__(self):
        self.logger = self.logger.bind(**self.context)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def log_execution_time(logger: structlog.stdlib.BoundLogger, operation: str):
    """
    Decorator to log execution time of functions.

    Args:
        logger: Logger instance
        operation: Operation name to log
    """
    import time
    import functools

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(
                    f"{operation} completed successfully",
                    execution_time=execution_time,
                    operation=operation,
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"{operation} failed",
                    execution_time=execution_time,
                    operation=operation,
                    error=str(e),
                    exc_info=True,
                )
                raise

        return wrapper

    return decorator


def log_api_request(logger: structlog.stdlib.BoundLogger, api_name: str, endpoint: str):
    """
    Decorator to log API requests.

    Args:
        logger: Logger instance
        api_name: Name of the API
        endpoint: API endpoint
    """
    import time
    import functools

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(
                    f"API request completed",
                    api_name=api_name,
                    endpoint=endpoint,
                    execution_time=execution_time,
                    status="success",
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"API request failed",
                    api_name=api_name,
                    endpoint=endpoint,
                    execution_time=execution_time,
                    error=str(e),
                    status="error",
                    exc_info=True,
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(
                    f"API request completed",
                    api_name=api_name,
                    endpoint=endpoint,
                    execution_time=execution_time,
                    status="success",
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"API request failed",
                    api_name=api_name,
                    endpoint=endpoint,
                    execution_time=execution_time,
                    error=str(e),
                    status="error",
                    exc_info=True,
                )
                raise

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Performance monitoring
class PerformanceLogger:
    """Logger for performance metrics."""

    def __init__(self, logger: structlog.stdlib.BoundLogger):
        self.logger = logger

    def log_memory_usage(self, component: str):
        """Log memory usage for a component."""
        import psutil

        process = psutil.Process()
        memory_info = process.memory_info()

        self.logger.info(
            "Memory usage",
            component=component,
            rss_mb=memory_info.rss / 1024 / 1024,
            vms_mb=memory_info.vms / 1024 / 1024,
            percent=process.memory_percent(),
        )

    def log_cpu_usage(self, component: str):
        """Log CPU usage for a component."""
        import psutil

        process = psutil.Process()

        self.logger.info(
            "CPU usage",
            component=component,
            cpu_percent=process.cpu_percent(),
            num_threads=process.num_threads(),
        )

    def log_database_performance(
        self, operation: str, execution_time: float, rows_affected: Optional[int] = None
    ):
        """Log database operation performance."""
        self.logger.info(
            "Database operation",
            operation=operation,
            execution_time=execution_time,
            rows_affected=rows_affected,
        )

    def log_api_performance(
        self,
        api_name: str,
        endpoint: str,
        execution_time: float,
        status_code: Optional[int] = None,
    ):
        """Log API performance metrics."""
        self.logger.info(
            "API performance",
            api_name=api_name,
            endpoint=endpoint,
            execution_time=execution_time,
            status_code=status_code,
        )
