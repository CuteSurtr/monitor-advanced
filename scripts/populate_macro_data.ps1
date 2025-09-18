# Populate InfluxDB macro_data bucket with sample economic data
# Updated for current setup

# InfluxDB configuration
$CONTAINER = "influxdb"
$BUCKET = "macro_data"
$ORG = "stock_monitor"
$TOKEN = "xEoh_d1w_9u4rUmgZLCUqckVK5qGnF1FNs2_hzrrzfXQCXLJRRYPh5oqcE_T0nYmF7jqsJ-O6r2OEUVDWV-kew=="

Write-Host "Populating InfluxDB macro_data bucket with sample economic data..." -ForegroundColor Green
Write-Host "Container: $CONTAINER" -ForegroundColor Yellow
Write-Host "Bucket: $BUCKET" -ForegroundColor Yellow
Write-Host "Organization: $ORG" -ForegroundColor Yellow
Write-Host ""

function Write-DataPoint {
    param(
        [string]$Measurement,
        [hashtable]$Tags,
        [hashtable]$Fields
    )
    
    # Build the line protocol string
    $tagStr = ($Tags.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join ","
    $fieldStr = ($Fields.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join ","
    $line = "$Measurement,$tagStr $fieldStr"
    
    $cmd = "docker exec $CONTAINER influx write --bucket $BUCKET --org $ORG --token $TOKEN `"$line`""
    Invoke-Expression $cmd | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        return $true
    } else {
        Write-Host "Error writing data point: $line" -ForegroundColor Red
        return $false
    }
}

Write-Host "Generating Treasury yield curve data..." -ForegroundColor Cyan

# Generate Treasury data for the last 30 days
for ($i = 0; $i -lt 30; $i++) {
    # Treasury yields with realistic variations
    $yield10Y = 4.2 + ($i * 0.01)  # Gradual increase
    $yield2Y = 4.8 + ($i * 0.015)   # Slightly faster increase
    $yield30Y = 4.5 + ($i * 0.008)  # Slower increase
    
    # Write Treasury data
    Write-DataPoint -Measurement "treasury_yield_curve" -Tags @{"maturity"="10Y"; "security_type"="treasury"} -Fields @{"yield"=$yield10Y}
    Write-DataPoint -Measurement "treasury_yield_curve" -Tags @{"maturity"="2Y"; "security_type"="treasury"} -Fields @{"yield"=$yield2Y}
    Write-DataPoint -Measurement "treasury_yield_curve" -Tags @{"maturity"="30Y"; "security_type"="treasury"} -Fields @{"yield"=$yield30Y}
    
    if ($i % 5 -eq 0) {
        Write-Host "  Day $($i+1)/30: 10Y=$($yield10Y.ToString('F2'))%, 2Y=$($yield2Y.ToString('F2'))%, 30Y=$($yield30Y.ToString('F2'))%" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Generating economic indicators..." -ForegroundColor Cyan

# CPI data
for ($i = 0; $i -lt 30; $i++) {
    $cpiValue = 3.2 + ($i * 0.01)  # Gradual inflation increase
    Write-DataPoint -Measurement "bls_economic_data" -Tags @{"indicator"="cpi"; "category"="inflation"} -Fields @{"value"=$cpiValue}
}

# Unemployment data
for ($i = 0; $i -lt 30; $i++) {
    $unemploymentValue = 3.8 + ($i * 0.005)  # Very gradual increase
    Write-DataPoint -Measurement "bls_economic_data" -Tags @{"indicator"="unemployment_rate"; "category"="labor"} -Fields @{"value"=$unemploymentValue}
}

Write-Host "  Generated CPI and unemployment data" -ForegroundColor Gray

Write-Host ""
Write-Host "Generating energy data..." -ForegroundColor Cyan

# Oil price data
for ($i = 0; $i -lt 30; $i++) {
    $oilPrice = 75.0 + ($i * 0.5)  # Gradual price increase
    Write-DataPoint -Measurement "eia_energy_data" -Tags @{"commodity"="crude_oil"; "unit"="usd_per_barrel"} -Fields @{"value"=$oilPrice}
}

# Natural gas data
for ($i = 0; $i -lt 30; $i++) {
    $gasPrice = 2.5 + ($i * 0.1)  # Gradual price increase
    Write-DataPoint -Measurement "eia_energy_data" -Tags @{"commodity"="natural_gas"; "unit"="usd_per_mmbtu"} -Fields @{"value"=$gasPrice}
}

Write-Host "  Generated oil and natural gas data" -ForegroundColor Gray

Write-Host ""
Write-Host "Generating financial market data..." -ForegroundColor Cyan

# VIX data
for ($i = 0; $i -lt 30; $i++) {
    $vixValue = 20.0 + ($i * 0.3)  # Gradual volatility increase
    Write-DataPoint -Measurement "fred_economic_data" -Tags @{"indicator"="vix"; "category"="volatility"} -Fields @{"value"=$vixValue}
}

# Fed funds rate data (constant for now)
for ($i = 0; $i -lt 30; $i++) {
    Write-DataPoint -Measurement "fred_economic_data" -Tags @{"indicator"="fed_funds_rate"; "category"="monetary_policy"} -Fields @{"value"=5.25}
}

Write-Host "  Generated VIX and Fed funds rate data" -ForegroundColor Gray

Write-Host ""
Write-Host "Generating Treasury curve metrics..." -ForegroundColor Cyan

# Treasury curve spread data
for ($i = 0; $i -lt 30; $i++) {
    $spread10Y2Y = $i * 0.02  # Spread increases over time
    Write-DataPoint -Measurement "treasury_curve_metrics" -Tags @{"metric"="10y_2y_spread"} -Fields @{"spread"=$spread10Y2Y}
}

Write-Host "  Generated Treasury curve spread data" -ForegroundColor Gray

Write-Host ""
Write-Host "=== Sample data population complete! ===" -ForegroundColor Green
Write-Host "Bucket: $BUCKET" -ForegroundColor Yellow
Write-Host "Organization: $ORG" -ForegroundColor Yellow
Write-Host "Container: $CONTAINER" -ForegroundColor Yellow
Write-Host ""
Write-Host "Your Comprehensive Economic Dashboard should now work." -ForegroundColor Green
Write-Host "Check Grafana to see the data." -ForegroundColor Green

