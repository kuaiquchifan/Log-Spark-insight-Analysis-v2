from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, avg, max, min, desc, hour, to_date, to_timestamp, when, countDistinct, stddev, mean,sum as F_sum
import webbrowser
import os

# 设置环境变量
os.environ["PYSPARK_PYTHON"] = "python"
os.environ["PYSPARK_DRIVER_PYTHON"] = "python"


# 创建 Spark 会话
spark = SparkSession.builder \
    .appName("LogAnalysis") \
    .master("local[*]") \
    .config("spark.python.worker.reuse", "false") \
    .getOrCreate()

# 自动打开浏览器
webbrowser.open("http://localhost:4040")

# 读取日志数据
df = spark.read.csv("access_logs.csv", header=True, inferSchema=True)

print("=" * 50)
print("1. 日志数据概览")
print("=" * 50)
df.show(5)
print(f"总记录数: {df.count()}")

print("\n" + "=" * 50)
print("2. HTTP 状态码分布")
print("=" * 50)
df.groupBy("status_code").count().orderBy(desc("count")).show()

print("\n" + "=" * 50)
print("3. 访问最频繁的 API 路径")
print("=" * 50)
df.groupBy("path").count().orderBy(desc("count")).show()

print("\n" + "=" * 50)
print("4. 响应时间统计（毫秒）")
print("=" * 50)
df.agg(
    avg("response_time_ms").alias("平均响应时间"),
    max("response_time_ms").alias("最大响应时间"),
    min("response_time_ms").alias("最小响应时间")
).show()

print("\n" + "=" * 50)
print("5. 各 HTTP 方法的请求数")
print("=" * 50)
df.groupBy("method").count().orderBy(desc("count")).show()

print("\n" + "=" * 50)
print("6. 错误请求分析（4xx 和 5xx）")
print("=" * 50)
error_df = df.filter((col("status_code") >= 400) & (col("status_code") < 600))
print(f"错误请求总数: {error_df.count()}")
error_df.groupBy("status_code", "path").count().orderBy(desc("count")).show()

print("\n" + "=" * 50)
print("7. 访问最频繁的 IP")
print("=" * 50)
df.groupBy("ip").count().orderBy(desc("count")).limit(10).show()

print("\n" + "=" * 50)
print("8. 用户代理分布")
print("=" * 50)
df.groupBy("user_agent").count().orderBy(desc("count")).show()

print("\n" + "=" * 50)
print("9. 响应时间超过 1000ms 的请求")
print("=" * 50)
slow_requests = df.filter(col("response_time_ms") > 1000)
print(f"慢请求数: {slow_requests.count()}")
slow_requests.groupBy("path").count().orderBy(desc("count")).show()

print("\n" + "=" * 50)
print("10. 成功率统计")
print("=" * 50)
total = df.count()
success = df.filter(col("status_code") == 200).count()
print(f"成功率: {success / total * 100:.2f}%")

print("\n" + "=" * 50)
print("11. 时间序列分析 - 按小时统计请求数")
print("=" * 50)
df.withColumn("hour", hour(to_timestamp("timestamp"))) \
    .groupBy("hour").count().orderBy("hour").show(24)

print("\n" + "=" * 50)
print("12. 时间序列分析 - 按日期统计错误率")
print("=" * 50)
df.withColumn("date", to_date(to_timestamp("timestamp"))) \
    .groupBy("date").agg(
        count("*").alias("总请求"),
        F_sum(when(col("status_code") >= 400, 1).otherwise(0)).alias("错误数")
    ).orderBy("date").show()

print("\n" + "=" * 50)
print("13. 异常检测 - 异常 IP（请求数异常高）")
print("=" * 50)
ip_stats = df.groupBy("ip").agg(count("*").alias("count"))
mean_val = ip_stats.agg(mean("count")).collect()[0][0]
std_val = ip_stats.agg(stddev("count")).collect()[0][0]
threshold = mean_val + 3 * std_val

print(f"平均请求数: {mean_val:.2f}")
print(f"标准差: {std_val:.2f}")
print(f"异常阈值 (平均 + 3*标准差): {threshold:.2f}")
print("\n异常 IP 列表:")

anomaly_ips = ip_stats.filter(col("count") > threshold).orderBy(desc("count"))
anomaly_ips.show()

print("\n" + "=" * 50)
print("14. 用户行为分析 - 用户访问路径分析（Top 20）")
print("=" * 50)
df.groupBy("ip", "path").agg(count("*").alias("访问次数")) \
    .orderBy(desc("访问次数")).limit(20).show()

print("\n" + "=" * 50)
print("15. 用户行为分析 - 用户会话分析（Top 10）")
print("=" * 50)
df.groupBy("ip").agg(
    count("*").alias("总请求数"),
    countDistinct("path").alias("访问路径数"),
    avg("response_time_ms").alias("平均响应时间")
).orderBy(desc("总请求数")).limit(10).show()

print("\n" + "=" * 50)
print("16. 性能瓶颈分析 - 最慢的 API")
print("=" * 50)
df.groupBy("path", "method").agg(
    avg("response_time_ms").alias("平均响应时间"),
    max("response_time_ms").alias("最大响应时间"),
    count("*").alias("请求数")
).orderBy(desc("平均响应时间")).show()

print("\n" + "=" * 50)
print("17. 性能瓶颈分析 - 响应时间分布")
print("=" * 50)
df.select("response_time_ms").describe().show()

# ============ 保存结果到单个 TXT 文件 ============

print("\n" + "=" * 50)
print("保存分析结果到文件")
print("=" * 50)

output_file = "analysis_results.txt"

with open(output_file, "w", encoding="utf-8") as f:
    f.write("=" * 50 + "\n")
    f.write("日志分析结果汇总\n")
    f.write("=" * 50 + "\n\n")
    
    # 1. 按小时统计
    f.write("1. 按小时统计请求数\n")
    f.write("-" * 50 + "\n")
    hourly = df.withColumn("hour", hour(to_timestamp("timestamp"))) \
        .groupBy("hour").count().orderBy("hour")
    for row in hourly.collect():
        f.write(f"小时 {row['hour']:02d}: {row['count']} 请求\n")
    f.write("\n")
    
    # 2. 按日期统计错误率
    f.write("2. 按日期统计错误率\n")
    f.write("-" * 50 + "\n")
    daily = df.withColumn("date", to_date(to_timestamp("timestamp"))) \
        .groupBy("date").agg(
            count("*").alias("总请求"),
            F_sum(when(col("status_code") >= 400, 1).otherwise(0)).alias("错误数")
        ).orderBy("date")
    for row in daily.collect():
        error_rate = (row['错误数'] / row['总请求'] * 100) if row['总请求'] > 0 else 0
        f.write(f"{row['date']}: 总请求 {row['总请求']}, 错误数 {row['错误数']}, 错误率 {error_rate:.2f}%\n")
    f.write("\n")
    
    # 3. 异常 IP
    f.write("3. 异常 IP（请求数异常高）\n")
    f.write("-" * 50 + "\n")
    ip_stats = df.groupBy("ip").agg(count("*").alias("count"))
    mean_val = ip_stats.agg(mean("count")).collect()[0][0]
    std_val = ip_stats.agg(stddev("count")).collect()[0][0]
    threshold = mean_val + 3 * std_val
    f.write(f"平均请求数: {mean_val:.2f}\n")
    f.write(f"标准差: {std_val:.2f}\n")
    f.write(f"异常阈值 (平均 + 3*标准差): {threshold:.2f}\n\n")
    
    anomaly_ips = ip_stats.filter(col("count") > threshold).orderBy(desc("count"))
    for row in anomaly_ips.collect():
        f.write(f"IP: {row['ip']}, 请求数: {row['count']}\n")
    f.write("\n")
    
    # 4. 用户访问路径 Top 20
    f.write("4. 用户访问路径分析（Top 20）\n")
    f.write("-" * 50 + "\n")
    user_paths = df.groupBy("ip", "path").agg(count("*").alias("访问次数")) \
        .orderBy(desc("访问次数")).limit(20)
    for row in user_paths.collect():
        f.write(f"IP: {row['ip']}, 路径: {row['path']}, 访问次数: {row['访问次数']}\n")
    f.write("\n")
    
    # 5. 用户会话分析 Top 10
    f.write("5. 用户会话分析（Top 10）\n")
    f.write("-" * 50 + "\n")
    sessions = df.groupBy("ip").agg(
        count("*").alias("总请求数"),
        countDistinct("path").alias("访问路径数"),
        avg("response_time_ms").alias("平均响应时间")
    ).orderBy(desc("总请求数")).limit(10)
    for row in sessions.collect():
        f.write(f"IP: {row['ip']}, 总请求: {row['总请求数']}, 路径数: {row['访问路径数']}, 平均响应时间: {row['平均响应时间']:.2f}ms\n")
    f.write("\n")
    
    # 6. 最慢的 API Top 20
    f.write("6. 性能瓶颈分析 - 最慢的 API（Top 20）\n")
    f.write("-" * 50 + "\n")
    slow_apis = df.groupBy("path", "method").agg(
        avg("response_time_ms").alias("平均响应时间"),
        max("response_time_ms").alias("最大响应时间"),
        count("*").alias("请求数")
    ).orderBy(desc("平均响应时间")).limit(20)
    for row in slow_apis.collect():
        f.write(f"路径: {row['path']}, 方法: {row['method']}, 平均响应时间: {row['平均响应时间']:.2f}ms, 最大: {row['最大响应时间']}ms, 请求数: {row['请求数']}\n")
    f.write("\n")
    
    # 7. 错误请求分析 Top 20
    f.write("7. 错误请求分析（Top 20）\n")
    f.write("-" * 50 + "\n")
    error_df = df.filter((col("status_code") >= 400) & (col("status_code") < 600))
    errors = error_df.groupBy("status_code", "path").count().orderBy(desc("count")).limit(20)
    for row in errors.collect():
        f.write(f"状态码: {row['status_code']}, 路径: {row['path']}, 次数: {row['count']}\n")
    f.write("\n")
    
    # 8. HTTP 状态码分布
    f.write("8. HTTP 状态码分布\n")
    f.write("-" * 50 + "\n")
    status_dist = df.groupBy("status_code").count().orderBy(desc("count"))
    for row in status_dist.collect():
        f.write(f"状态码 {row['status_code']}: {row['count']} 次\n")
    f.write("\n")
    
    # 9. 总体统计
    f.write("9. 总体统计\n")
    f.write("-" * 50 + "\n")
    total = df.count()
    success = df.filter(col("status_code") == 200).count()
    f.write(f"总请求数: {total}\n")
    f.write(f"成功请求数: {success}\n")
    f.write(f"成功率: {success / total * 100:.2f}%\n")
    f.write(f"错误请求数: {error_df.count()}\n")
    f.write(f"错误率: {error_df.count() / total * 100:.2f}%\n\n")
    
    # 10. 响应时间统计
    f.write("10. 响应时间统计（毫秒）\n")
    f.write("-" * 50 + "\n")
    stats = df.agg(
        avg("response_time_ms").alias("平均"),
        max("response_time_ms").alias("最大"),
        min("response_time_ms").alias("最小")
    ).collect()[0]
    f.write(f"平均响应时间: {stats['平均']:.2f}ms\n")
    f.write(f"最大响应时间: {stats['最大']}ms\n")
    f.write(f"最小响应时间: {stats['最小']}ms\n")

print(f"✓ 已保存: {output_file}")


input("按 Enter 键关闭程序...")
spark.stop()