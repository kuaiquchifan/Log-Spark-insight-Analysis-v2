<div align="right">
  <a href="README.md"><button>中文</button></a>
</div>

# Log Analysis System (Log-Spark-insight-Analysis)
## Project Overview
This is a log analysis system built on Apache Spark for processing and analyzing large-scale HTTP access log data. The system can generate simulated logs, perform multi-dimensional analysis, and output detailed analytical reports.
## Features
### 1. Log Data Generation (`generate_logs.py`)
- Generates 100,000 simulated HTTP access logs
- Includes fields: timestamp, IP, HTTP method, path, status code, response time, user agent
- Supports customizable record count
### 2. Log Analysis (`log_analysis.py`)
Provides the following analytical capabilities:
#### Basic Statistics
- HTTP status code distribution
- Most frequently accessed API paths
- Response time metrics (average, maximum, minimum)
- Request counts by HTTP method
- User agent distribution


Advanced Analytics
- **Time Series Analysis**: Hourly and daily statistics on request volume and error rates
- **Anomaly Detection**: Identify IPs with abnormally high request volumes (based on the 3σ principle)
- **User Behavior Analysis**:
  - User access path analysis (Top 20)
  - User session analysis (Top 10)
- **Performance Bottleneck Analysis**:
  - Slowest API endpoints (Top 20)
  - Response time distribution
- **Error Analysis**:
  - Top 20 error requests
  - Error rate statistics

## Environment Requirements

### System Requirements
- Python 3.11+
- Java JDK 17 LTS
- Apache Spark 3.5.7+

### Python Dependencies
```bash
pip install pyspark
```

## Usage
1. Generate log data
```bash
python generate_logs.py
```
Output: access_logs.csv (100,000 log records)

2. Execute log analysis
```bash
python log_analysis.py
```


Advanced Analytics
- **Time Series Analysis**: Hourly and daily statistics on request volume and error rates
- **Anomaly Detection**: Identify IPs with abnormally high request volumes (based on the 3σ principle)
- **User Behavior Analysis**:
  - User access path analysis (Top 20)
  - User session analysis (Top 10)
- **Performance Bottleneck Analysis**:
  - Slowest API endpoints (Top 20)
  - Response time distribution
- **Error Analysis**:
  - Top 20 error requests
  - Error rate statistics

## Environment Requirements

### System Requirements
- Python 3.11+
- Java JDK 17 LTS
- Apache Spark 3.5.7+

### Python Dependencies
```bash
pip install pyspark
```

## Usage
1. Generate log data
```bash
python generate_logs.py
```
Output: access_logs.csv (100,000 log records)

2. Execute log analysis
```bash
python log_analysis.py
```

Automatically opens Spark Web UI (http://localhost:4040)   
Outputs analysis results to console
Generates detailed report file: analysis_results.txt

## License
This project is open source and available under the **Apache 2.0** License.

## Authors and Acknowledgments
Author: Junliang Li  
Email: 940747544@qq.com
