@echo off
echo Testing InfluxDB write and read...
echo.

REM Write a test data point
echo Writing test data...
docker exec influxdb influx write --bucket macro_data --org stock_monitor --token xEoh_d1w_9u4rUmgZLCUqckVK5qGnF1FNs2_hzrrzfXQCXLJRRYPh5oqcE_T0nYmF7jqsJ-O6r2OEUVDWV-kew== "test_measurement,test_tag=value test_field=123"

echo.
echo Test data written. Now checking if it exists...
echo.

REM Check if the data exists by listing measurements
echo Listing measurements in macro_data bucket:
docker exec influxdb influx query --token xEoh_d1w_9u4rUmgZLCUqckVK5qGnF1FNs2_hzrrzfXQCXLJRRYPh5oqcE_T0nYmF7jqsJ-O6r2OEUVDWV-kew== --org stock_monitor "from(bucket: \"macro_data\") |> range(start: -1h) |> group() |> distinct(column: _measurement)"

echo.
echo Test complete.
pause

