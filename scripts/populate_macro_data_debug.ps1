# Debug version of macro data population script
# This will test each data point individually and show detailed output

# InfluxDB configuration
$CONTAINER = "influxdb"
$BUCKET = "macro_data"
$ORG = "stock_monitor"
$TOKEN = "xEoh_d1w_9u4rUmgZLCUqckVK5qGnF1FNs2_hzrrzfXQCXLJRRYPh5oqcE_T0nYmF7jqsJ-O6r2OEUVDWV-kew=="

Write-Host "=== DEBUG MODE: Testing InfluxDB data population ===" -ForegroundColor Green
Write-Host "Container: $CONTAINER" -ForegroundColor Yellow
Write-Host "Bucket: $BUCKET" -ForegroundColor Yellow
Write-Host "Organization: $ORG" -ForegroundColor Yellow
Write-Host ""

# Test 1: Simple write
Write-Host "Test 1: Writing simple test data point..." -ForegroundColor Cyan
$testCmd = "docker exec $CONTAINER influx write --bucket $BUCKET --org $ORG --token $TOKEN `"test_debug,test_tag=debug test_value=999`""
Write-Host "Command: $testCmd" -ForegroundColor Gray
$result = Invoke-Expression $testCmd
Write-Host "Exit code: $LASTEXITCODE" -ForegroundColor Yellow
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Test 1 PASSED" -ForegroundColor Green
} else {
    Write-Host "✗ Test 1 FAILED" -ForegroundColor Red
}

Write-Host ""

# Test 2: Treasury data point
Write-Host "Test 2: Writing Treasury yield data point..." -ForegroundColor Cyan
$treasuryCmd = "docker exec $CONTAINER influx write --bucket $BUCKET --org $ORG --token $TOKEN `"treasury_yield_curve,maturity=10Y,security_type=treasury yield=4.25`""
Write-Host "Command: $treasuryCmd" -ForegroundColor Gray
$result = Invoke-Expression $treasuryCmd
Write-Host "Exit code: $LASTEXITCODE" -ForegroundColor Yellow
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Test 2 PASSED" -ForegroundColor Green
} else {
    Write-Host "✗ Test 2 FAILED" -ForegroundColor Red
}

Write-Host ""

# Test 3: CPI data point
Write-Host "Test 3: Writing CPI data point..." -ForegroundColor Cyan
$cpiCmd = "docker exec $CONTAINER influx write --bucket $BUCKET --org $ORG --token $TOKEN `"bls_economic_data,indicator=cpi,category=inflation value=3.25`""
Write-Host "Command: $cpiCmd" -ForegroundColor Gray
$result = Invoke-Expression $cpiCmd
Write-Host "Exit code: $LASTEXITCODE" -ForegroundColor Yellow
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Test 3 PASSED" -ForegroundColor Green
} else {
    Write-Host "✗ Test 3 FAILED" -ForegroundColor Red
}

Write-Host ""

# Test 4: VIX data point
Write-Host "Test 4: Writing VIX data point..." -ForegroundColor Cyan
$vixCmd = "docker exec $CONTAINER influx write --bucket $BUCKET --org $ORG --token $TOKEN `"fred_economic_data,indicator=vix,category=volatility value=20.5`""
Write-Host "Command: $vixCmd" -ForegroundColor Gray
$result = Invoke-Expression $vixCmd
Write-Host "Exit code: $LASTEXITCODE" -ForegroundColor Yellow
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Test 4 PASSED" -ForegroundColor Green
} else {
    Write-Host "✗ Test 4 FAILED" -ForegroundColor Red
}

Write-Host ""

# Test 5: Check if data exists
Write-Host "Test 5: Checking if data exists in bucket..." -ForegroundColor Cyan
Write-Host "This will show all measurements in the macro_data bucket:"
Write-Host ""

# Try to list measurements (this might fail due to PowerShell quoting issues)
try {
    $listCmd = "docker exec $CONTAINER influx query --token $TOKEN --org $ORG `"from(bucket: `"`"macro_data`"`") |> range(start: -1h) |> group() |> distinct(column: _measurement)`""
    Write-Host "Command: $listCmd" -ForegroundColor Gray
    $result = Invoke-Expression $listCmd
    Write-Host "Result: $result" -ForegroundColor Yellow
} catch {
    Write-Host "Error listing measurements: $_" -ForegroundColor Red
    Write-Host "This is likely due to PowerShell quoting issues with the Flux query" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== DEBUG TESTING COMPLETE ===" -ForegroundColor Green
Write-Host "Check the results above to see which tests passed/failed" -ForegroundColor Yellow
Write-Host ""
Write-Host "If all tests passed, the issue might be with the dashboard queries" -ForegroundColor Cyan
Write-Host "If tests failed, there's an issue with the InfluxDB connection or data format" -ForegroundColor Red

