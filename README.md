[![English](https://img.shields.io/badge/README-English-2ea44f?style=for-the-badge)](README.md)
[![中文](https://img.shields.io/badge/README-中文-ffb703?style=for-the-badge)](README_zh.md)

# HTTP-Log-Spark-Analysis

A distributed log analysis platform built with Apache Spark and Hadoop, designed to process and analyze large-scale HTTP access logs. The project includes simulated log generation, dimension-table construction, batch analytics, anomaly detection, and an interactive dashboard built with Streamlit.

## Overview

This project demonstrates how to build a practical data pipeline for web log analysis using big data technologies. It covers:

- Simulated HTTP log generation
- Geographic and URL category dimension tables
- Batch analytics with PySpark
- Anomaly detection for suspicious traffic and abnormal IPs
- Data visualization using Streamlit

The system is suitable for learning, experimentation, and prototyping enterprise log analytics workflows.

---

## Project Structure

```bash
HTTP-Log-Spark-Analysis
├── 01_generate_geo_dim_data.ipynb                  # Generates geographic dimension data (01_geo_dim.parquet)
├── 02_generate_url_category_dim_data.ipynb         # Generates URL/path category dimension data
├── 03_generate_http_logs_data_v2.ipynb             # Generates HTTP access log samples
├── 04_generate_anomaly_logs_empty_data.ipynb       # Generates placeholder/anomaly testing datasets
├── 05_connect_spark_and_data_analytics_v3.ipynb    # Performs basic analytics with PySpark
├── 06_connect_spark_and_abnormal_analytics_v2.ipynb # Detects abnormal activity and suspicious patterns
├── 07_data_visulisation_by_streamlit.py            # Streamlit dashboard entry point
├── 071_overview_page.py                            # Overview dashboard page
├── 072_abnormal_page.py                            # Abnormal traffic dashboard page
├── requirements.txt                                # Python dependencies
├── README.md                                       # Project documentation
└── output/                                         # Generated output files
```

## Architecture

1. Dimension Table Generation
   Builds geographic location tables
   Builds URL/category mapping tables
   Supplies structured labels and grouping keys for downstream analysis
2. Log Data Generation
   Generates simulated HTTP access logs
   Captures fields such as timestamp, IP, method, URL, status code, response time, and user-agent
3. Batch Analysis
   Reads parquet/csv data with PySpark
   Performs aggregation, grouping, ranking, and multi-dimensional statistics
   Calculates traffic trends and access behavior metrics
4. Anomaly Analysis
   Detects abnormal high-volume IP activity
   Identifies suspicious status codes and crawler-like behavior
   Applies rule-based and statistical threshold analysis for alerting
5. Visualization Layer
   Presents traffic overview and anomaly insights via Streamlit
   Provides an interactive web-based dashboard for result exploration

## System Requirements

### Local Environment

Python 3.11+
Miniconda
VMware WorkStation 16 Pro

### Virtual Machine Environment

Apache Spark 3.5.7
Hadoop 3.3.6
Ubuntu 24 LTS
PostgreSQL 16
OpenJDK 8

## Installation Guide

### Download the project and open the folder
```bash
git clone <repository-url>
cd HTTP-Log-Spark-Analysis\
```
### Create and activate a virtual environment in Miniconda
```bash
conda create -n <your-venv-name> python=3.11
conda activate <your-venv-name>
```

#### Install Python Dependencies

```Shell
pip install -r requirements.txt
```

#### Install OpenJDK 8

On Ubuntu 24 LTS, install OpenJDK 8:

```shell
sudo apt update
sudo apt install openjdk-8-jdk
```

Then configure environment variables:

```Shell
nano ~/.bashrc
```

Add the following lines:

```shell
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH
```

Reload the shell:

```shell
source ~/.bashrc
java -version
```

#### Install Hadoop 3.3.6

Download Hadoop:

```shell
cd ~
wget https://dlcdn.apache.org/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz
```

Extract the archive:

```Shell
tar -xzf hadoop-3.3.6.tar.gz
```

Move it to the /opt directory:

```Shell
sudo mv ~/hadoop-3.3.6 /opt/
```

Set ownership:

```Shell
sudo chown -R $USER:$USER /opt/hadoop-3.3.6
```

Add environment variables:

```Shell
nano ~/.bashrc
```

Add:

```shell
export HADOOP_HOME=/opt/hadoop-3.3.6
export PATH=$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH
```

Reload:

```shell
source ~/.bashrc
hadoop version
```

#### Install Apache Spark 3.5.7

Download Spark:

```Shell
cd ~
wget https://archive.apache.org/dist/spark/spark-3.5.7/spark-3.5.7-bin-hadoop3.tgz
```

Extract it:

```shell
tar -xzf
spark-3.5.7-bin-hadoop3.tgz
```

Move it into /opt:

```Shell
sudo mv ~/spark-3.5.7-bin-hadoop3 /opt/
```

Set environment variables:

```Shell
nano ~/.bashrc
```

Add:

```Shell
export SPARK_HOME=/opt/spark-3.5.7-bin-hadoop3
export PATH=$SPARK_HOME/bin:$SPARK_HOME/sbin:$PATH
```

Reload:

```Shell
source ~/.bashrc
spark-shell --version
```




## Usage

### Step 1: Generate Dimension Data

Run the following notebooks in sequence:

```
01_generate_geo_dim_data.ipynb
02_generate_url_category_dim_data.ipynb
```

These notebooks generate the geographic and URL classification dimension tables used by downstream analytics.

---

### Step 2: Generate Log Data

Run:


```
03_generate_http_logs_data_v2.ipynb
```

This creates sample HTTP log datasets that simulate real traffic patterns.

---

### Step 3: Start Hadoop

On the virtual machine, start the Hadoop services:

```shell
start-dfs.sh
start-yarn.sh
```

---

### Step 4: Create an HDFS Directory

```shell
hdfs dfs -mkdir -p /spark/httplog_analytics/
hdfs dfs -chmod g+w /spark/httplog_analytics/
```

---

### Step 5: Upload Data to HDFS

If the generated Parquet file is stored locally, for example:

```Shell
~/Desktop/output_data/
```


upload it with:

```Shell
hdfs dfs -put ~/Desktop/output_httplog_data/<filename>.parquet /spark/httplog_analytics/
```


---

### Step 6: Start Spark Connect

```Shell
$SPARK_HOME/sbin/start-connect-server.sh \
--packages org.apache.spark:spark-connect_2.12:3.5.7 \
--host 0.0.0.0 \
--port 15002
```


---

### Step 7: Run Basic Analysis

Open and run:

```
05_connect_spark_and_data_analytics_v3.ipynb
```

This notebook covers:

* Traffic statistics
* Aggregation by time and endpoint
* Top-IP and top-URL analysis
* Multi-dimensional summaries

---

### Step 8: Run Anomaly Detection

Open and run:

```Shell
06_connect_spark_and_abnormal_analytics_v2.ipynb
```

This notebook is designed to identify:

* Abnormal traffic spikes
* Suspicious IP addresses
* HTTP errors and unusual access behavior
* Potential attack or crawler patterns

---

### Step 9: Launch the Dashboard

From the project root directory, run:

```Shell
streamlit run 07_data_visulisation_by_streamlit.py
```

Then open the dashboard in a browser at:

```Shell
http://localhost:8501
```


## License

This project is open source and available under the **Apache 2.0** License.

## Authors and Acknowledgments

Author: Junliang Li   
Email: 940747544@qq.com
