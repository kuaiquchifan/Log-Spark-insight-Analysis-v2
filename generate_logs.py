import random
from datetime import datetime, timedelta

# 设置随机种子，确保每次生成的数据相同
random.seed(42)

# 生成模拟日志数据
log_file = "access_logs.csv"
num_records = 100000

with open(log_file, 'w', encoding='utf-8') as f:
    f.write("timestamp,ip,method,path,status_code,response_time_ms,user_agent\n")
    
    methods = ["GET", "POST", "PUT", "DELETE"]
    paths = ["/api/users", "/api/products", "/api/orders", "/home", "/login", "/logout", "/dashboard"]
    status_codes = [200, 201, 400, 401, 403, 404, 500, 502, 503]
    user_agents = ["Chrome", "Firefox", "Safari", "Edge", "Mobile"]
    
    start_time = datetime(2024, 1, 1)
    
    for i in range(num_records):
        timestamp = start_time + timedelta(seconds=random.randint(0, 86400*30))
        ip = f"192.168.{random.randint(0, 255)}.{random.randint(1, 255)}"
        method = random.choice(methods)
        path = random.choice(paths)
        status_code = random.choice(status_codes)
        response_time = random.randint(10, 5000)
        user_agent = random.choice(user_agents)
        
        f.write(f"{timestamp},{ip},{method},{path},{status_code},{response_time},{user_agent}\n")

print(f"已生成 {num_records} 条日志数据到 {log_file}")