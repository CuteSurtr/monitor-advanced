@echo off
echo Testing InfluxDB write and read...
echo.

if "%INFLUXDB_TOKEN%"=="" (
    echo ERROR: INFLUXDB_TOKEN environment variable is not set.
    exit /b 1
)

REM Write a test data point
echo Writing test data...
docker exec influxdb influx write --bucket macro_data --org stock_monitor --token %INFLUXDB_TOKEN% "test_measurement,test_tag=value test_field=123"

echo.
echo Test data written. Now checking if it exists...
echo.

REM Check if the data exists by listing measurements
echo Listing measurements in macro_data bucket:
docker exec influxdb influx query --token %INFLUXDB_TOKEN% --org stock_monitor "from(bucket: \"macro_data\") |> range(start: -1h) |> group() |> distinct(column: _measurement)"

echo.
echo Test complete.
pause
