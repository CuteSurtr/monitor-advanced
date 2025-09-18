"""
Structured logging system for Stock Market Monitor.
Provides centralized, structured logging with multiple output formats and levels.
"""

import logging
import logging.handlers
import json
import sys
import os
from typing import Dict, Any, Optional, Union
from datetime import datetime
from pathlib import Path
import structlog
from pythonjsonlogger import jsonlogger

from src.utils.config import get_config

# Global logger registry
_loggers: Dict[str, "StructuredLogger"] = {}


class StructuredLogger:
    """
    Enhanced structured logger with JSON output and context management.
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize structured logger.

        Args:
            name: Logger name (usually module name)
            config: Optional logging configuration override
        """
        self.name = name
        self.config = config or get_config().logging
        self._setup_logging()

    def _setup_logging(self):
        """Setup structured logging configuration."""
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
                self._add_context,
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        # Setup standard library logger
        self.logger = structlog.get_logger(self.name)
        self.stdlib_logger = logging.getLogger(self.name)

        # Configure handlers
        self._setup_handlers()

    def _add_context(self, logger, method_name, event_dict):
        """Add contextual information to log entries."""
        event_dict["service"] = "stock_monitor"
        event_dict["environment"] = getattr(self.config, "environment", "development")
        event_dict["version"] = "1.0.0"

        # Add request ID if available (from context)
        request_id = getattr(self, "_request_id", None)
        if request_id:
            event_dict["request_id"] = request_id

        # Add user ID if available
        user_id = getattr(self, "_user_id", None)
        if user_id:
            event_dict["user_id"] = user_id

        return event_dict

    def _setup_handlers(self):
        """Setup logging handlers for different outputs."""
        # Clear existing handlers
        self.stdlib_logger.handlers.clear()

        # Set log level
        level = getattr(logging, self.config.level.upper(), logging.INFO)
        self.stdlib_logger.setLevel(level)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        if self.config.format == "json":
            # JSON formatter for structured logging
            formatter = jsonlogger.JsonFormatter(
                "%(asctime)s %(name)s %(levelname)s %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        else:
            # Standard formatter
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        console_handler.setFormatter(formatter)
        self.stdlib_logger.addHandler(console_handler)

        # File handler (if configured)
        if hasattr(self.config, "file") and self.config.file:
            self._setup_file_handler(level, formatter)

        # Syslog handler (if configured)
        if getattr(self.config, "syslog_enabled", False):
            self._setup_syslog_handler(level, formatter)

    def _setup_file_handler(self, level, formatter):
        """Setup file logging handler with rotation."""
        log_file = Path(self.config.file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=self._parse_size(getattr(self.config, "max_size", "100MB")),
            backupCount=getattr(self.config, "backup_count", 5),
            encoding="utf-8",
        )

        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        self.stdlib_logger.addHandler(file_handler)

    def _setup_syslog_handler(self, level, formatter):
        """Setup syslog handler for system logging."""
        try:
            syslog_handler = logging.handlers.SysLogHandler(
                address=getattr(self.config, "syslog_address", "/dev/log")
            )
            syslog_handler.setLevel(level)
            syslog_handler.setFormatter(formatter)
            self.stdlib_logger.addHandler(syslog_handler)
        except Exception as e:
            # Fallback if syslog is not available
            print(f"Warning: Could not setup syslog handler: {e}")

    def _parse_size(self, size_str: str) -> int:
        """Parse size string like '100MB' to bytes."""
        size_str = size_str.upper()
        if size_str.endswith("KB"):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith("MB"):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith("GB"):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)

    def with_context(self, **kwargs) -> "StructuredLogger":
        """Create a new logger instance with additional context."""
        new_logger = StructuredLogger(self.name, self.config)
        for key, value in kwargs.items():
            setattr(new_logger, f"_{key}", value)
        return new_logger

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, **kwargs)

    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, **kwargs)


class AuditLogger:
    """
    Specialized logger for audit trails and security events.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize audit logger."""
        self.config = config or get_config().logging
        self.logger = StructuredLogger("audit", config)

    def log_user_action(
        self, user_id: str, action: str, resource: str, success: bool, **kwargs
    ):
        """Log user action for audit trail."""
        self.logger.with_context(user_id=user_id, audit_type="user_action").info(
            "User action performed",
            action=action,
            resource=resource,
            success=success,
            **kwargs,
        )

    def log_api_access(
        self,
        user_id: Optional[str],
        method: str,
        endpoint: str,
        status_code: int,
        response_time: float,
        **kwargs,
    ):
        """Log API access for monitoring."""
        level = "info" if status_code < 400 else "warning"
        getattr(
            self.logger.with_context(user_id=user_id, audit_type="api_access"), level
        )(
            "API access",
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            response_time_ms=response_time * 1000,
            **kwargs,
        )

    def log_security_event(
        self, event_type: str, severity: str, description: str, **kwargs
    ):
        """Log security events."""
        level = "critical" if severity == "HIGH" else "warning"
        getattr(self.logger.with_context(audit_type="security"), level)(
            "Security event",
            event_type=event_type,
            severity=severity,
            description=description,
            **kwargs,
        )

    def log_data_access(
        self, user_id: str, data_type: str, operation: str, record_count: int, **kwargs
    ):
        """Log data access for compliance."""
        self.logger.with_context(user_id=user_id, audit_type="data_access").info(
            "Data access",
            data_type=data_type,
            operation=operation,
            record_count=record_count,
            **kwargs,
        )


class PerformanceLogger:
    """
    Specialized logger for performance monitoring.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize performance logger."""
        self.config = config or get_config().logging
        self.logger = StructuredLogger("performance", config)

    def log_operation_timing(
        self, operation: str, duration: float, success: bool, **kwargs
    ):
        """Log operation timing."""
        level = "info" if success else "warning"
        getattr(self.logger.with_context(metric_type="timing"), level)(
            "Operation timing",
            operation=operation,
            duration_ms=duration * 1000,
            success=success,
            **kwargs,
        )

    def log_resource_usage(
        self,
        resource_type: str,
        usage: float,
        threshold: Optional[float] = None,
        **kwargs,
    ):
        """Log resource usage metrics."""
        level = "warning" if threshold and usage > threshold else "info"
        getattr(self.logger.with_context(metric_type="resource_usage"), level)(
            "Resource usage",
            resource_type=resource_type,
            usage=usage,
            threshold=threshold,
            **kwargs,
        )

    def log_database_query(
        self, query_type: str, duration: float, rows_affected: int, **kwargs
    ):
        """Log database query performance."""
        level = "warning" if duration > 1.0 else "debug"
        getattr(self.logger.with_context(metric_type="database"), level)(
            "Database query",
            query_type=query_type,
            duration_ms=duration * 1000,
            rows_affected=rows_affected,
            **kwargs,
        )


class BusinessLogger:
    """
    Specialized logger for business events and metrics.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize business logger."""
        self.config = config or get_config().logging
        self.logger = StructuredLogger("business", config)

    def log_trade_execution(
        self,
        portfolio_id: str,
        symbol: str,
        trade_type: str,
        quantity: float,
        price: float,
        **kwargs,
    ):
        """Log trade execution."""
        self.logger.with_context(
            event_type="trade_execution", portfolio_id=portfolio_id
        ).info(
            "Trade executed",
            symbol=symbol,
            trade_type=trade_type,
            quantity=quantity,
            price=price,
            total_value=quantity * price,
            **kwargs,
        )

    def log_alert_triggered(
        self, alert_type: str, symbol: str, severity: str, **kwargs
    ):
        """Log alert triggers."""
        level = "critical" if severity == "HIGH" else "warning"
        getattr(self.logger.with_context(event_type="alert_triggered"), level)(
            "Alert triggered",
            alert_type=alert_type,
            symbol=symbol,
            severity=severity,
            **kwargs,
        )

    def log_portfolio_rebalance(self, portfolio_id: str, trades: list, **kwargs):
        """Log portfolio rebalancing."""
        self.logger.with_context(
            event_type="portfolio_rebalance", portfolio_id=portfolio_id
        ).info("Portfolio rebalanced", trade_count=len(trades), trades=trades, **kwargs)


# Global logger instances
_audit_logger: Optional[AuditLogger] = None
_performance_logger: Optional[PerformanceLogger] = None
_business_logger: Optional[BusinessLogger] = None


def get_logger(name: str) -> StructuredLogger:
    """
    Get or create a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        StructuredLogger instance
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name)

    return _loggers[name]


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    global _audit_logger

    if _audit_logger is None:
        _audit_logger = AuditLogger()

    return _audit_logger


def get_performance_logger() -> PerformanceLogger:
    """Get global performance logger instance."""
    global _performance_logger

    if _performance_logger is None:
        _performance_logger = PerformanceLogger()

    return _performance_logger


def get_business_logger() -> BusinessLogger:
    """Get global business logger instance."""
    global _business_logger

    if _business_logger is None:
        _business_logger = BusinessLogger()

    return _business_logger


def setup_logging(config: Optional[Dict[str, Any]] = None):
    """
    Setup global logging configuration.

    Args:
        config: Optional logging configuration
    """
    # This function can be called during application startup
    # to ensure all loggers are properly configured
    if config:
        # Update global configuration
        pass

    # Initialize all logger types
    get_logger("stock_monitor")
    get_audit_logger()
    get_performance_logger()
    get_business_logger()


# Context manager for request tracing
class LoggingContext:
    """Context manager for adding request/operation context to logs."""

    def __init__(self, **context):
        """Initialize with context variables."""
        self.context = context
        self.previous_context = {}

    def __enter__(self):
        """Enter context and set logging context."""
        # Store previous context and set new context
        for key, value in self.context.items():
            self.previous_context[key] = globals().get(f"_current_{key}")
            globals()[f"_current_{key}"] = value
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and restore previous context."""
        # Restore previous context
        for key, value in self.previous_context.items():
            if value is None:
                globals().pop(f"_current_{key}", None)
            else:
                globals()[f"_current_{key}"] = value
