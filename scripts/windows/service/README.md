# Windows Service Configuration

This directory contains scripts for running the Stock Monitor as a Windows service.

## Overview

Running as a Windows service provides:
- **Automatic startup** when Windows boots
- **Background operation** without user login
- **Automatic restart** if the service crashes
- **Service management** through Windows Service Manager
- **System integration** with Windows logging and monitoring

## Prerequisites

1. **NSSM (Non-Sucking Service Manager)**
   - Download from: https://nssm.cc/download
   - Extract `nssm.exe` to this directory (`scripts/windows/service/`)
   - Choose the correct architecture (win32 or win64)

2. **Administrator Privileges**
   - All service operations require Administrator rights
   - Right-click scripts and "Run as administrator"

3. **Completed Installation**
   - Python virtual environment must be set up
   - Dependencies must be installed
   - Configuration file must exist

## Quick Start

### Method 1: Interactive Management (Recommended)

```batch
# Run the service manager (as Administrator)
scripts\windows\service\manage_service.bat
```

This provides an interactive menu for all service operations.

### Method 2: Direct Installation

```batch
# Install service (as Administrator)
scripts\windows\service\install_service.bat

# Start service
net start StockMonitor

# Stop service
net stop StockMonitor

# Uninstall service
scripts\windows\service\uninstall_service.bat
```

## Files Description

- **`install_service.bat`** - Installs the service with NSSM
- **`uninstall_service.bat`** - Removes the service completely
- **`manage_service.bat`** - Interactive service management menu
- **`README.md`** - This documentation file

## Service Configuration

### Service Details
- **Service Name**: `StockMonitor`
- **Display Name**: `24/7 Stock Market Monitor`
- **Startup Type**: Automatic
- **Account**: Local System
- **Working Directory**: Application root directory

### Automatic Configuration
The installation script automatically configures:
- **Executable**: `venv\Scripts\python.exe`
- **Arguments**: `src\main.py`
- **Working Directory**: Application root
- **Environment Variables**: `PYTHONPATH`, `CONFIG_PATH`
- **Log Files**: stdout and stderr redirection
- **Restart Policy**: Automatic restart on failure

### Log Files
- **Standard Output**: `logs\service_stdout.log`
- **Standard Error**: `logs\service_stderr.log`
- **Application Log**: `logs\stock_monitor.log`

## Service Management

### Using Windows Services Console

1. Open `services.msc`
2. Find "24/7 Stock Market Monitor"
3. Right-click for options:
   - Start/Stop/Restart
   - Properties for configuration
   - Recovery options for failure handling

### Using Command Line

```batch
# Service status
sc query StockMonitor

# Start service
sc start StockMonitor
# or
net start StockMonitor

# Stop service
sc stop StockMonitor
# or
net stop StockMonitor

# Service configuration
sc qc StockMonitor

# Delete service (after stopping)
sc delete StockMonitor
```

### Using NSSM Directly

```batch
# Edit service configuration
nssm edit StockMonitor

# Service status
nssm status StockMonitor

# Start/stop service
nssm start StockMonitor
nssm stop StockMonitor

# Remove service
nssm remove StockMonitor confirm
```

## Configuration Options

### Environment Variables
The service is configured with these environment variables:
- `PYTHONPATH`: Application root directory
- `CONFIG_PATH`: Path to configuration file

### Startup Configuration
```batch
# Set service to start automatically
nssm set StockMonitor Start SERVICE_AUTO_START

# Set service to start manually
nssm set StockMonitor Start SERVICE_DEMAND_START

# Delay startup (useful for dependencies)
nssm set StockMonitor AppStopMethodSkip 0
nssm set StockMonitor AppRestartDelay 30000
```

### Failure Recovery
```batch
# Restart on failure
nssm set StockMonitor AppExit Default Restart

# Exit on clean shutdown
nssm set StockMonitor AppExit 0 Exit

# Throttle rapid restarts
nssm set StockMonitor AppThrottle 10000
```

## Troubleshooting

### Service Won't Start

1. **Check Prerequisites**
   ```batch
   # Verify Python environment
   venv\Scripts\python.exe --version
   
   # Test application manually
   venv\Scripts\activate.bat
   python src\main.py
   ```

2. **Check Configuration**
   ```batch
   # Verify config file exists
   dir config\config.yaml
   
   # Test configuration
   python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"
   ```

3. **Check Dependencies**
   ```batch
   # Check database connectivity
   # Check Redis connectivity
   # Verify API keys
   ```

### Service Starts But Application Fails

1. **Check Logs**
   ```batch
   # View service logs
   type logs\service_stdout.log
   type logs\service_stderr.log
   
   # View application logs
   type logs\stock_monitor.log
   ```

2. **Check Permissions**
   - Ensure service account has read/write access to application directory
   - Check network connectivity for API access
   - Verify database permissions

3. **Check Dependencies**
   - Ensure PostgreSQL service is running
   - Ensure Redis service is running
   - Check firewall settings

### Performance Issues

1. **Resource Limits**
   ```batch
   # Monitor service resource usage
   tasklist /fi "imagename eq python.exe" /fo table
   
   # Check memory usage
   typeperf "\Process(python)\Working Set" -sc 1
   ```

2. **Configuration Tuning**
   - Adjust `max_workers` in config
   - Modify memory limits
   - Tune database connection pools

### Service Management Issues

1. **Permission Denied**
   - Ensure running as Administrator
   - Check User Account Control (UAC) settings

2. **Service Already Exists**
   ```batch
   # Force remove existing service
   sc stop StockMonitor
   sc delete StockMonitor
   # Then reinstall
   ```

3. **NSSM Not Found**
   - Download NSSM from official website
   - Extract to correct directory
   - Use appropriate architecture (32-bit or 64-bit)

## Advanced Configuration

### Custom Service Account

By default, the service runs as Local System. To use a custom account:

```batch
# Set custom account (requires password)
nssm set StockMonitor ObjectName "DOMAIN\username" "password"

# Or use built-in accounts
nssm set StockMonitor ObjectName "NT AUTHORITY\NetworkService"
nssm set StockMonitor ObjectName "NT AUTHORITY\LocalService"
```

### Resource Limits

```batch
# Set CPU priority
nssm set StockMonitor AppPriority NORMAL_PRIORITY_CLASS

# Set working set limits (memory)
nssm set StockMonitor AppAffinity All
```

### Custom Arguments

```batch
# Add command line arguments
nssm set StockMonitor AppParameters src\main.py --config=config\production.yaml

# Set additional environment variables
nssm set StockMonitor AppEnvironmentExtra ENVIRONMENT=production
```

## Security Considerations

1. **Service Account**
   - Use least privilege principle
   - Consider dedicated service account
   - Avoid running as Administrator

2. **File Permissions**
   - Restrict access to configuration files
   - Secure log file directories
   - Protect Python virtual environment

3. **Network Security**
   - Configure firewall rules
   - Use HTTPS for web interfaces
   - Secure API key storage

## Monitoring and Maintenance

### Health Checks
- Service status monitoring
- Application health endpoints
- Resource usage monitoring
- Log file monitoring

### Maintenance Tasks
- Regular log rotation
- Configuration backups
- Update management
- Performance optimization

### Alerting
- Service failure notifications
- Performance threshold alerts
- Security event monitoring
- Capacity planning alerts

## Support

For additional help:
1. Check application logs in `logs/` directory
2. Review Windows Event Viewer
3. Consult the main documentation in `docs/`
4. Check NSSM documentation at https://nssm.cc/usage