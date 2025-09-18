"""
Health checker for monitoring system components and dependencies.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import psutil
import redis
import psycopg2

from src.utils.database import DatabaseManager
from src.utils.cache import CacheManager

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Individual health check result."""

    name: str
    status: HealthStatus
    message: str
    response_time_ms: float
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "response_time_ms": self.response_time_ms,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details or {},
        }


class HealthChecker:
    """Comprehensive health checker for all system components."""

    def __init__(self, db_manager: DatabaseManager, cache_manager: CacheManager):
        """
        Initialize health checker.

        Args:
            db_manager: Database manager instance
            cache_manager: Cache manager instance
        """
        self.db_manager = db_manager
        self.cache_manager = cache_manager

        # Health check configuration
        self.check_interval = 60  # seconds
        self.timeout = 30  # seconds for each check

        # Thresholds
        self.cpu_threshold = 90  # percent
        self.memory_threshold = 90  # percent
        self.disk_threshold = 95  # percent
        self.response_time_threshold = 5000  # milliseconds

        # Health history
        self.health_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000

    async def check_all_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        start_time = datetime.utcnow()
        checks = []

        # Run all health checks concurrently
        tasks = [
            self.check_system_health(),
            self.check_database_health(),
            self.check_cache_health(),
            self.check_api_endpoints_health(),
            self.check_external_services_health(),
            self.check_disk_space_health(),
            self.check_network_health(),
        ]

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    checks.append(
                        HealthCheck(
                            name="health_check_error",
                            status=HealthStatus.UNHEALTHY,
                            message=f"Health check failed: {str(result)}",
                            response_time_ms=0,
                            timestamp=datetime.utcnow(),
                        )
                    )
                elif isinstance(result, list):
                    checks.extend(result)
                else:
                    checks.append(result)

        except Exception as e:
            logger.error(f"Error in comprehensive health check: {e}")
            checks.append(
                HealthCheck(
                    name="health_check_system_error",
                    status=HealthStatus.UNHEALTHY,
                    message=f"System error during health check: {str(e)}",
                    response_time_ms=0,
                    timestamp=datetime.utcnow(),
                )
            )

        # Calculate overall status
        overall_status = self._calculate_overall_status(checks)
        total_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        result = {
            "overall_status": overall_status.value,
            "total_checks": len(checks),
            "healthy_checks": len(
                [c for c in checks if c.status == HealthStatus.HEALTHY]
            ),
            "degraded_checks": len(
                [c for c in checks if c.status == HealthStatus.DEGRADED]
            ),
            "unhealthy_checks": len(
                [c for c in checks if c.status == HealthStatus.UNHEALTHY]
            ),
            "total_time_ms": total_time,
            "timestamp": start_time.isoformat(),
            "checks": [check.to_dict() for check in checks],
        }

        # Store in history
        self._store_health_result(result)

        return result

    async def check_system_health(self) -> List[HealthCheck]:
        """Check system resource health."""
        checks = []
        timestamp = datetime.utcnow()

        try:
            start_time = datetime.utcnow()

            # CPU check
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_status = HealthStatus.HEALTHY
            cpu_message = f"CPU usage: {cpu_percent:.1f}%"

            if cpu_percent > self.cpu_threshold:
                cpu_status = HealthStatus.UNHEALTHY
                cpu_message = f"High CPU usage: {cpu_percent:.1f}%"
            elif cpu_percent > self.cpu_threshold * 0.8:
                cpu_status = HealthStatus.DEGRADED
                cpu_message = f"Elevated CPU usage: {cpu_percent:.1f}%"

            checks.append(
                HealthCheck(
                    name="system_cpu",
                    status=cpu_status,
                    message=cpu_message,
                    response_time_ms=(datetime.utcnow() - start_time).total_seconds()
                    * 1000,
                    timestamp=timestamp,
                    details={
                        "cpu_percent": cpu_percent,
                        "threshold": self.cpu_threshold,
                    },
                )
            )

            # Memory check
            memory = psutil.virtual_memory()
            memory_status = HealthStatus.HEALTHY
            memory_message = f"Memory usage: {memory.percent:.1f}%"

            if memory.percent > self.memory_threshold:
                memory_status = HealthStatus.UNHEALTHY
                memory_message = f"High memory usage: {memory.percent:.1f}%"
            elif memory.percent > self.memory_threshold * 0.8:
                memory_status = HealthStatus.DEGRADED
                memory_message = f"Elevated memory usage: {memory.percent:.1f}%"

            checks.append(
                HealthCheck(
                    name="system_memory",
                    status=memory_status,
                    message=memory_message,
                    response_time_ms=(datetime.utcnow() - start_time).total_seconds()
                    * 1000,
                    timestamp=timestamp,
                    details={
                        "memory_percent": memory.percent,
                        "memory_available": memory.available,
                        "threshold": self.memory_threshold,
                    },
                )
            )

        except Exception as e:
            checks.append(
                HealthCheck(
                    name="system_health_error",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Error checking system health: {str(e)}",
                    response_time_ms=0,
                    timestamp=timestamp,
                )
            )

        return checks

    async def check_database_health(self) -> HealthCheck:
        """Check database connectivity and performance."""
        start_time = datetime.utcnow()

        try:
            # Test database connection
            connection_test = await self._test_database_connection()

            if connection_test["success"]:
                status = HealthStatus.HEALTHY
                message = f"Database connected (response: {connection_test['response_time_ms']:.1f}ms)"

                # Check response time
                if connection_test["response_time_ms"] > self.response_time_threshold:
                    status = HealthStatus.DEGRADED
                    message = f"Database slow response: {connection_test['response_time_ms']:.1f}ms"

            else:
                status = HealthStatus.UNHEALTHY
                message = f"Database connection failed: {connection_test['error']}"

        except Exception as e:
            status = HealthStatus.UNHEALTHY
            message = f"Database health check error: {str(e)}"
            connection_test = {"response_time_ms": 0, "error": str(e)}

        return HealthCheck(
            name="database",
            status=status,
            message=message,
            response_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
            timestamp=datetime.utcnow(),
            details=connection_test,
        )

    async def check_cache_health(self) -> HealthCheck:
        """Check cache (Redis) connectivity and performance."""
        start_time = datetime.utcnow()

        try:
            # Test cache connection
            cache_test = await self._test_cache_connection()

            if cache_test["success"]:
                status = HealthStatus.HEALTHY
                message = f"Cache connected (response: {cache_test['response_time_ms']:.1f}ms)"

                # Check response time
                if cache_test["response_time_ms"] > self.response_time_threshold:
                    status = HealthStatus.DEGRADED
                    message = (
                        f"Cache slow response: {cache_test['response_time_ms']:.1f}ms"
                    )

            else:
                status = HealthStatus.UNHEALTHY
                message = f"Cache connection failed: {cache_test['error']}"

        except Exception as e:
            status = HealthStatus.UNHEALTHY
            message = f"Cache health check error: {str(e)}"
            cache_test = {"response_time_ms": 0, "error": str(e)}

        return HealthCheck(
            name="cache",
            status=status,
            message=message,
            response_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
            timestamp=datetime.utcnow(),
            details=cache_test,
        )

    async def check_api_endpoints_health(self) -> List[HealthCheck]:
        """Check internal API endpoints."""
        checks = []
        endpoints = [
            {"name": "dashboard_api", "url": "http://localhost:8080/health"},
            {"name": "prometheus_metrics", "url": "http://localhost:9090/-/healthy"},
            {"name": "grafana", "url": "http://localhost:3000/api/health"},
        ]

        for endpoint in endpoints:
            start_time = datetime.utcnow()

            try:
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as session:
                    async with session.get(endpoint["url"]) as response:
                        response_time = (
                            datetime.utcnow() - start_time
                        ).total_seconds() * 1000

                        if response.status == 200:
                            status = HealthStatus.HEALTHY
                            message = f"Endpoint accessible (HTTP {response.status})"
                        else:
                            status = HealthStatus.DEGRADED
                            message = f"Endpoint returned HTTP {response.status}"

                        checks.append(
                            HealthCheck(
                                name=endpoint["name"],
                                status=status,
                                message=message,
                                response_time_ms=response_time,
                                timestamp=datetime.utcnow(),
                                details={
                                    "http_status": response.status,
                                    "url": endpoint["url"],
                                },
                            )
                        )

            except Exception as e:
                checks.append(
                    HealthCheck(
                        name=endpoint["name"],
                        status=HealthStatus.UNHEALTHY,
                        message=f"Endpoint unreachable: {str(e)}",
                        response_time_ms=(
                            datetime.utcnow() - start_time
                        ).total_seconds()
                        * 1000,
                        timestamp=datetime.utcnow(),
                        details={"error": str(e), "url": endpoint["url"]},
                    )
                )

        return checks

    async def check_external_services_health(self) -> List[HealthCheck]:
        """Check external API services."""
        checks = []
        # This would check actual external APIs like Alpha Vantage, Polygon, etc.
        # For now, return placeholder checks

        external_apis = ["alpha_vantage", "polygon_io", "finnhub", "news_api"]

        for api_name in external_apis:
            checks.append(
                HealthCheck(
                    name=f"external_{api_name}",
                    status=HealthStatus.UNKNOWN,
                    message="External API check not implemented",
                    response_time_ms=0,
                    timestamp=datetime.utcnow(),
                    details={"api": api_name},
                )
            )

        return checks

    async def check_disk_space_health(self) -> List[HealthCheck]:
        """Check disk space on all mounted drives."""
        checks = []

        try:
            for disk in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(disk.mountpoint)
                    percent_used = (usage.used / usage.total) * 100

                    status = HealthStatus.HEALTHY
                    message = f"Disk usage: {percent_used:.1f}%"

                    if percent_used > self.disk_threshold:
                        status = HealthStatus.UNHEALTHY
                        message = f"Critical disk usage: {percent_used:.1f}%"
                    elif percent_used > self.disk_threshold * 0.9:
                        status = HealthStatus.DEGRADED
                        message = f"High disk usage: {percent_used:.1f}%"

                    # Fix the f-string syntax error by handling the replacement separately
                    mountpoint_name = disk.mountpoint.replace("/", "_").replace(
                        "\\", "_"
                    )
                    checks.append(
                        HealthCheck(
                            name=f"disk_{mountpoint_name}",
                            status=status,
                            message=message,
                            response_time_ms=0,
                            timestamp=datetime.utcnow(),
                            details={
                                "mountpoint": disk.mountpoint,
                                "percent_used": percent_used,
                                "free_bytes": usage.free,
                                "total_bytes": usage.total,
                            },
                        )
                    )

                except PermissionError:
                    continue

        except Exception as e:
            checks.append(
                HealthCheck(
                    name="disk_check_error",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Error checking disk space: {str(e)}",
                    response_time_ms=0,
                    timestamp=datetime.utcnow(),
                )
            )

        return checks

    async def check_network_health(self) -> HealthCheck:
        """Check network connectivity."""
        start_time = datetime.utcnow()

        try:
            # Test external connectivity
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                async with session.get("https://httpbin.org/status/200") as response:
                    response_time = (
                        datetime.utcnow() - start_time
                    ).total_seconds() * 1000

                    if response.status == 200:
                        status = HealthStatus.HEALTHY
                        message = f"Network connectivity OK ({response_time:.1f}ms)"
                    else:
                        status = HealthStatus.DEGRADED
                        message = f"Network issues detected (HTTP {response.status})"

        except Exception as e:
            status = HealthStatus.UNHEALTHY
            message = f"Network connectivity failed: {str(e)}"
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return HealthCheck(
            name="network",
            status=status,
            message=message,
            response_time_ms=response_time,
            timestamp=datetime.utcnow(),
        )

    async def _test_database_connection(self) -> Dict[str, Any]:
        """Test database connection."""
        start_time = datetime.utcnow()

        try:
            # Simple query to test connection
            result = await self.db_manager.execute_query("SELECT 1")
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return {
                "success": True,
                "response_time_ms": response_time,
                "result": result,
            }

        except Exception as e:
            return {
                "success": False,
                "response_time_ms": (datetime.utcnow() - start_time).total_seconds()
                * 1000,
                "error": str(e),
            }

    async def _test_cache_connection(self) -> Dict[str, Any]:
        """Test cache connection."""
        start_time = datetime.utcnow()

        try:
            # Simple ping to test connection
            test_key = f"health_check_{int(datetime.utcnow().timestamp())}"
            await self.cache_manager.set(test_key, "test_value", ttl=10)
            result = await self.cache_manager.get(test_key)
            await self.cache_manager.delete(test_key)

            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return {
                "success": result == "test_value",
                "response_time_ms": response_time,
            }

        except Exception as e:
            return {
                "success": False,
                "response_time_ms": (datetime.utcnow() - start_time).total_seconds()
                * 1000,
                "error": str(e),
            }

    def _calculate_overall_status(self, checks: List[HealthCheck]) -> HealthStatus:
        """Calculate overall health status from individual checks."""
        if not checks:
            return HealthStatus.UNKNOWN

        unhealthy_count = len([c for c in checks if c.status == HealthStatus.UNHEALTHY])
        degraded_count = len([c for c in checks if c.status == HealthStatus.DEGRADED])

        if unhealthy_count > 0:
            return HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    def _store_health_result(self, result: Dict[str, Any]):
        """Store health check result in history."""
        self.health_history.append(result)

        # Trim history if too large
        if len(self.health_history) > self.max_history_size:
            self.health_history = self.health_history[-self.max_history_size :]

    def get_health_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get health check history."""
        return self.health_history[-limit:]

    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary statistics."""
        if not self.health_history:
            return {"error": "No health history available"}

        recent_checks = self.health_history[-10:]  # Last 10 checks

        return {
            "total_checks_recorded": len(self.health_history),
            "recent_overall_status": (
                recent_checks[-1]["overall_status"] if recent_checks else "unknown"
            ),
            "average_response_time_ms": (
                sum(c["total_time_ms"] for c in recent_checks) / len(recent_checks)
                if recent_checks
                else 0
            ),
            "uptime_percentage": (
                len([c for c in recent_checks if c["overall_status"] == "healthy"])
                / len(recent_checks)
                * 100
                if recent_checks
                else 0
            ),
        }
