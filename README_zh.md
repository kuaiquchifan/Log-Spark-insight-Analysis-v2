[![English](https://img.shields.io/badge/README-English-2ea44f?style=for-the-badge)](README.md)
[![中文](https://img.shields.io/badge/README-中文-ffb703?style=for-the-badge)](README_zh.md)

# 网络日志分析系统 (Log-Spark-Insight-Analysis-v2)

## 项目概述

这是一个基于 Apache Spark + Hadoop 的日志分析系统，用于处理和分析大规模 HTTP 访问日志数据。系统可以生成模拟日志、维表构建、批量与异常分析、执行多维度分析，并输出详细的steamlit分析报告。

## 项目结构和功能特性

```bash
Log-Spark-Insight-Analysis-v2
├── 01_generate_geo_dim_data.ipynb 				# 生成地理维表（01_geo_dim.parquet），包含国家代码、名称、地区、大洲及风险标记。
├── 02_generate_url_category_dim_data.ipynb 	# 生成 URL/路径类别维表（parquet/csv），用于为日志路径打标签或分组。 
├── 03_generate_http_logs_data_v2.ipynb  		# 生成更丰富的 HTTP 日志样例（含时间、IP、方法、路径、状态码、响应时长、user-agent 等），保存到 output。
├── 04_generate_anomaly_logs_empty_data.ipynb 	# 生成用于异常分析的占位/空数据集与示例异常记录格式（便于开发与调试异常检测流程）。
├── 05_connect_spark_and_data_analytics_v3.ipynb # 使用 PySpark 读取维表与日志并进行基础统计、分组聚合与指标计算
├── 06_connect_spark_and_abnormal_analytics_v2.ipynb # 基于规则/阈值/统计方法检测异常流量或异常 IP。并且包含更多特征工程、聚合粒度与示例阈值调优。
├── 07_data_visulisation_by_streamlit.py  			#使用 Streamlit 展示分析结果的交互式界面
├── 071_overview_page.py							#流量总体情况的介绍
├── 072_abnormal_page.py							#流量异常情况的介绍
├── requirements.txt 								#环境依赖信息
└── README.md										# 解释文档
```

## 架构说明

1. 维表生成模块

* 生成地理位置维表
* 生成 URL 分类维表
* 为后续日志分析提供标签和分组字段

2. 日志数据生成模块

* 生成模拟 HTTP 访问日志
* 记录时间、IP、方法、URL、状态码、响应时长、User-Agent 等字段

3. 批量分析模块

* 使用 PySpark 读取 parquet/csv 数据
* 执行多维度统计、分组聚合、TOP N 排名、流量趋势分析

4. 异常分析模块

* 检测高访问量异常 IP
* 检测异常状态码、爬虫行为、响应异常等模式
* 结合规则和统计阈值进行告警分析

5. 可视化展示模块

* 通过 Streamlit 输出流量总览和异常页面
* 支持交互式查看分析结果

## 环境要求

### 物理机系统要求

- Python 3.11+
- Miniconda
- VMware WorkStation 16 pro

### 虚拟机系统要求

- Apache Spark 3.5.7
- Hadoop 3.3.6
- Ubuntu 24 LTS
- PostgreSQL 16
- OpenJDK 8

### 物理机的环境配置步骤：

### 下载项目并且打开文件夹

```bash
git clone <repository-url>
cd Log-Spark-Insight-Analysis-v2\
```

### 在miniconda创建并激活虚拟环境

```bash
conda create -n <your-venv-name> python=3.11
conda activate <your-venv-name>
```

### 安装依赖
```bash
pip install -r requirement.txt
```



### 虚拟机的环境配置步骤：

### 安装OpenJDK 8

下载并安装openjdk 8的包

```Shell
sudo apt install openjdk-8-jdk
```

设置并生效环境变量

```Shell
nano ~/.bashrc
source ~/.bashrc
```

在文件末尾加入：

```Shell
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=JAVA_HOME/bin:JAVAHOME/bin:PATH
```

### 安装 Hadoop 3.3.6

切换到根目录，下载Hadoop压缩包

```Shell
cd ~
wget https://dlcdn.apache.org/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz
```

在桌面解压

```Shell
tar -xzf hadoop-3.3.6.tar.gz
```

把桌面的解压文件夹移动到opt里面

```Shell
sudo mv ~/桌面/hadoop-3.3.6  /opt/
```

设置文件夹归属

```Shell
sudo chown -R USER:USER:USER /usr/local/hadoop
```

检查一下权限

```Shell
ls -ld /opt/hadoop-3.3.6
```

设置并生效Hadoop环境变量

```Shell
nano ~/.bashrc
source ~/.bashrc
```

### 安装 Apache Spark 3.5.7

切换到根目录，下载Apache Spark压缩包

```Shell
cd ~
wget https://archive.apache.org/dist/spark/spark-3.5.7/spark-3.5.7-bin-hadoop3.tgz
```

在桌面解压

```Shell
tar -xzf
spark-3.5.7-bin-hadoop3.tgz
```

把桌面的解压文件夹移动到opt里面

```Shell
sudo mv ~/桌面/spark-3.5.7-bin-hadoop3 /opt/
```

设置并生效spark环境变量

```Shell
nano ~/.bashrc
source ~/.bashrc
```

## 使用方法

1. 生成维表数据（先运行）：

* 在 Jupyter 中打开并运行 `01-generate_geo_dim_data.ipynb`
* 运行 `02_generate_url_category_dim_data.ipynb`

输出：600,000 条日志记录

2. 生成日志数据：

* 运行 `03_generate_http_logs_data_v2.ipynb`
* 执行日志分析

3. 在虚拟机上，启动 Hadoop

启动 HDFS：

```Shell
start-dfs.sh
```

然后启动 YARN：

```Shell
start-yarn.sh
```

4. 创建hdfs文件夹

```Shell
hdfs dfs -mkdir -p /spark/httplog_analytics/
hdfs dfs -chmod g+w /spark/httplog_analytics/
```

5. 上传Parquet到虚拟机的hdfs中

例如你的本地文件如果在：

```Shell
~/桌面/output_data/
```

那么：

```Shell
hdfs dfs -put ~/桌面/output_httplog_data/<xxxxxx>.parquet  /spark/httplog_analytics/
```

6. 使用spark connect 启动 apache spark

```Shell
$SPARK_HOME/sbin/start-connect-server.sh \
--packages org.apache.spark:spark-connect_2.12:3.5.7 \
--host 0.0.0.0 \
--port 15002
```

7. 基础分析：

* 运行 `05_connect_spark_and_data_analytics_v3.ipynb`

8. 异常分析：

* 运行 `06_connect_spark_and_abnormal_analytics_v2.ipynb`

9. 数据可视化：

* 在项目根目录运行 Streamlit 脚本：
* ```Python
  streamlit run 07_data_visulisation_by_streamlit.py
  ```

## 许可协议

本项目为开源项目，遵循 **Apache 2.0** 许可协议。

## 作者与致谢

Author: Junliang Li
Email: 940747544@qq.com
