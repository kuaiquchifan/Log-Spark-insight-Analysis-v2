<div align="right">
  <a href="README_EN.md"><button>English</button></a>
</div>

# 日志分析系统 (Log-Spark-insight-Analysis)
## 项目概述

这是一个基于 Apache Spark 的日志分析系统，用于处理和分析大规模 HTTP 访问日志数据。系统可以生成模拟日志、执行多维度分析，并输出详细的分析报告。

## 功能特性

### 1. 日志数据生成 (`generate_logs.py`)
- 生成 100,000 条模拟 HTTP 访问日志
- 包含字段：时间戳、IP、HTTP 方法、路径、状态码、响应时间、用户代理
- 支持自定义记录数量

### 2. 日志分析 (`log_analysis.py`)
提供以下分析功能：

#### 基础统计
- HTTP 状态码分布
- 访问最频繁的 API 路径
- 响应时间统计（平均、最大、最小）
- 各 HTTP 方法的请求数
- 用户代理分布

#### 高级分析
- **时间序列分析**：按小时、按日期统计请求数和错误率
- **异常检测**：识别请求数异常高的 IP（基于 3σ 原则）
- **用户行为分析**：
  - 用户访问路径分析（Top 20）
  - 用户会话分析（Top 10）
- **性能瓶颈分析**：
  - 最慢的 API 端点（Top 20）
  - 响应时间分布
- **错误分析**：
  - 错误请求分析（Top 20）
  - 错误率统计

## 环境要求

### 系统要求
- Python 3.11+
- Java JDK 17 LTS
- Apache Spark 3.5.7+

### Python 依赖
```bash
pip install pyspark
```

## 使用方法
1. 生成日志数据
```bash
python generate_logs.py
```
输出：access_logs.csv（100,000 条日志记录）

2. 执行日志分析
```bash
python log_analysis.py
```

自动打开 Spark Web UI（http://localhost:4040）
输出分析结果到控制台
生成详细报告文件：analysis_results.txt

## 许可协议
本项目采用开源模式，遵循 **Apache 2.0** 许可协议。

## 作者与鸣谢
作者：Junliang Li 
邮箱：940747544@qq.com


