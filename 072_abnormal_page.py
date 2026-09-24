import streamlit as st
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np

DATA_DIRS = {
    "abnormal": "output_abnormal_analytics",
    "further": "output_further_analytics"
}

def fmt_rt_ms(val_ms):
    try:
        v = float(val_ms)
    except Exception:
        return "—"
    if pd.isna(v):
        return "—"
    # 若 >=1000 ms 则转换为秒显示（保留1位小数），否则显示 ms（保留1位小数）
    if abs(v) >= 1000:
        return f"{v/1000:.1f} s"
    else:
        return f"{v:,.1f} ms"

def safe_to_numeric(s):
    # 将不可转为数值的、inf/-inf 显式变为 NaN，返回 Series（不做 fillna）
    return pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan)

@st.cache_data(show_spinner=False)
def read_parquet_cached(path):
    return pd.read_parquet(path)

def render_abnormal(abnormal_dir, further_dir=None):
    # --------- abnormal 模式：读取并展示三个 parquet 的总体指标 ---------
    ab_dir = Path(abnormal_dir)
    fu_dir = Path(further_dir) if further_dir else None
    print(f"Rendering abnormal page from: {fu_dir}")
    p1 = fu_dir / "01_network_traffic_overview.parquet"
    p2 = fu_dir / "02_request_method_dist.parquet"
    p3 = fu_dir / "04_ua_type_dist.parquet"

    st.header("IP 流量总体异常情况 — 概览")
    # 1) 网络流量总览表（比如 per-ip 流量）
    if p1.exists():
        try:
            df1 = pd.read_parquet(p1)
            st.subheader("网络流量总览（01_network_traffic_overview）")
            # st.dataframe(df1)

            if "total_requests" in df1.columns:
                try:
                    total_requests = int(pd.to_numeric(df1["total_requests"].iloc[0], errors="coerce"))
                except Exception:
                    total_requests = int(len(df1))
            else:
                total_requests = int(len(df1))

            err_rate = "—"
            p_err = fu_dir / "16_hourly_error_stats.parquet"
            print("Checking for error stats file:", p_err)
            if p_err.exists():
                d_err = pd.read_parquet(p_err)
                # 识别总请求列与错误列
                total_cols = ("total_requests",)
                err_cols = ("error_count",)
                tot_col = next((c for c in total_cols if c in d_err.columns), None)
                err_col = next((c for c in err_cols if c in d_err.columns), None)
                print("16_hourly_error_stats columns:", d_err.columns.tolist())
                print("detected tot_col, err_col:", tot_col, err_col)

                total_requests_sum = pd.to_numeric(d_err[tot_col], errors="coerce").fillna(0).sum()
                error_count_sum = pd.to_numeric(d_err[err_col], errors="coerce").fillna(0).sum()
                if total_requests_sum > 0:
                    err_rate = f"{(error_count_sum / total_requests_sum * 100):.2f}%"
                else:
                    err_rate = "—"


            # 计算慢请求数（来自 further 的 18_slow_requests_stats.parquet）
            slow_count = 0
            if fu_dir is not None:
                p_slow = fu_dir / "18_slow_requests_stats.parquet"
                if p_slow.exists():
                    try:
                        df_slow = pd.read_parquet(p_slow)
                        slow_count = len(df_slow)
                    except Exception:
                        slow_count = 0

            # 计算慢请求占比 A = 慢请求条数 / total_requests
            slow_pct = "—"
            try:
                if total_requests and total_requests > 0:
                    slow_pct = f"{(slow_count / total_requests * 100):.2f}%"
                else:
                    slow_pct = "—"
            except Exception:
                slow_pct = "—"

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("总请求数", f"{total_requests:,}")
            k2.metric("错误率", err_rate)
            k3.metric("慢请求数", f"{slow_count:,}")
            k4.metric("慢请求占比 (A)", slow_pct)
            
        except Exception as e:
            st.error(f"读取 {p1.name} 失败: {e}")
    else:
        st.warning(f"未找到文件: {p1}")

    # ====== 绘制按 date+hour 的慢请求占比折线图（A） ======
    # 读取慢请求明细/统计
    p_slow = fu_dir / "18_slow_requests_stats.parquet" if fu_dir is not None else None
    if p_slow is not None and p_slow.exists():
        try:
            df_slow = pd.read_parquet(p_slow)
            # 尝试识别 date 和 hour 列
            if "date" in df_slow.columns and "hour" in df_slow.columns:
                df_slow_grp = df_slow.groupby(["date", "hour"]).size().reset_index(name="slow_count")
            else:
                # 尝试识别时间戳列并拆分
                ts_col = next((c for c in ("ts", "timestamp", "time", "datetime") if c in df_slow.columns), None)
                if ts_col:
                    df_slow["_ts"] = pd.to_datetime(df_slow[ts_col], errors="coerce")
                    df_slow["date"] = df_slow["_ts"].dt.strftime("%Y-%m-%d")
                    df_slow["hour"] = df_slow["_ts"].dt.hour
                    df_slow_grp = df_slow.groupby(["date", "hour"]).size().reset_index(name="slow_count")
                else:
                    # 无法按小时聚合，退回按日期聚合（若有 date 列）
                    if "date" in df_slow.columns:
                        df_slow_grp = df_slow.groupby(["date"]).size().reset_index(name="slow_count")
                        df_slow_grp["hour"] = 0
                    else:
                        df_slow_grp = pd.DataFrame(columns=["date", "hour", "slow_count"])

            # 尝试读取每小时总请求数文件以做分母（优先）
            p_hourly = fu_dir / "16_hourly_error_stats.parquet" if fu_dir is not None else None
            if p_hourly is not None and p_hourly.exists():
                try:
                    df_hourly = pd.read_parquet(p_hourly)
                    # 识别可能的列名
                    date_col = next((c for c in ("date", "day") if c in df_hourly.columns), None)
                    hour_col = next((c for c in ("hour", "hour_of_day") if c in df_hourly.columns), None)
                    tot_col = next((c for c in ("total_requests", "total", "requests") if c in df_hourly.columns), None)
                    if date_col and hour_col and tot_col:
                        df_hourly_ren = df_hourly.rename(columns={date_col: "date", hour_col: "hour", tot_col: "total_requests"})
                        df_hourly_ren["hour"] = df_hourly_ren["hour"].astype(int)
                        merged = pd.merge(df_slow_grp, df_hourly_ren[["date", "hour", "total_requests"]], on=["date", "hour"], how="left")
                        merged["total_requests"] = merged["total_requests"].fillna(total_requests)  # 缺失时退回总体
                    else:
                        merged = df_slow_grp.copy()
                        merged["total_requests"] = total_requests
                except Exception:
                    merged = df_slow_grp.copy()
                    merged["total_requests"] = total_requests
            else:
                merged = df_slow_grp.copy()
                merged["total_requests"] = total_requests

            if not merged.empty:
                # 计算非慢请求数与占比
                merged["slow_count"] = pd.to_numeric(merged["slow_count"], errors="coerce").fillna(0)
                merged["total_requests"] = pd.to_numeric(merged["total_requests"], errors="coerce").fillna(0)
                merged["non_slow_count"] = (merged["total_requests"] - merged["slow_count"]).clip(lower=0)
                merged["slow_pct"] = merged.apply(lambda row: (row["slow_count"] / row["total_requests"] * 100)
                                                 if row["total_requests"] and row["total_requests"] > 0 else 0, axis=1)
                merged["non_slow_pct"] = merged.apply(lambda row: (row["non_slow_count"] / row["total_requests"] * 100)
                                                      if row["total_requests"] and row["total_requests"] > 0 else 0, axis=1)

                # 构造时间索引便于排序与绘图（已在上面构造）
                merged["hour"] = merged["hour"].astype(int)
                merged["datetime"] = pd.to_datetime(merged["date"], errors="coerce") + pd.to_timedelta(merged["hour"], unit="h")
                merged = merged.sort_values("datetime")

                # 绘制两条折线：慢请求占比与非慢请求占比
                df_plot = merged[["datetime", "slow_pct", "non_slow_pct"]].melt(id_vars="datetime",
                                                                              value_vars=["non_slow_pct", "slow_pct"],
                                                                              var_name="type", value_name="pct")
                df_plot["type"] = df_plot["type"].map({"non_slow_pct": "非慢请求占比", "slow_pct": "慢请求占比"})

                fig_line = px.line(df_plot, x="datetime", y="pct", color="type", markers=True,
                                   labels={"datetime": "Date Hour", "pct": "占比 (%)", "type": "类别"},
                                   title="按 date+hour 的慢/非慢请求占比")
                fig_line.update_layout(xaxis=dict(tickformat="%Y-%m-%d\n%H:%M"))
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("没有可用于绘制慢请求按小时占比的数据。")
        except Exception as e:
            st.error(f"读取慢请求数据失败: {e}")
    else:
        st.info("未找到 slow requests 文件（18_slow_requests_stats.parquet）。")




    # ====== 按 path 出现次数选出慢请求最多的 Top20 IP，并显示相关信息 ======
    p_slow = fu_dir / "18_slow_requests_stats.parquet" if fu_dir is not None else None
    if p_slow is not None and p_slow.exists():
        try:
            df_slow = pd.read_parquet(p_slow)

            # 每一行视为一次慢请求，按 ip 聚合慢请求总数
            ip_counts = df_slow.groupby("ip").size().reset_index(name="slow_count")

            # 取 top20 ip
            top_ips = ip_counts.sort_values("slow_count", ascending=False).head(20)

            # 为每个 top ip 计算该 ip 下出现次数最多的 path（url）及其次数、常见 method、region、country_name
            rows = []
            for _, r in top_ips.iterrows():
                ip = r["ip"]
                slow_count = int(r["slow_count"])
                sub = df_slow[df_slow["ip"] == ip]

                # 最多的 path 与其次数
                if "url" in sub.columns:
                    top_path_series = sub["url"].value_counts()
                    top_path = top_path_series.index[0] if not top_path_series.empty else None
                    top_path_count = int(top_path_series.iloc[0]) if not top_path_series.empty else 0
                else:
                    top_path = None
                    top_path_count = 0

                # 最常见的 method / region / country_name（若存在）
                top_method = sub["method"].mode().iloc[0] if "method" in sub.columns and not sub["method"].mode().empty else None
                top_region = sub["region"].mode().iloc[0] if "region" in sub.columns and not sub["region"].mode().empty else None
                top_country = sub["country_name"].mode().iloc[0] if "country_name" in sub.columns and not sub["country_name"].mode().empty else None

                # 最近一次出现的 date/hour 示例（若存在 date/hour）
                sample_date = sub["date"].mode().iloc[0] if "date" in sub.columns and not sub["date"].mode().empty else None
                sample_hour = int(sub["hour"].mode().iloc[0]) if "hour" in sub.columns and not sub["hour"].mode().empty else None

                rows.append({
                    "ip": ip,
                    "slow_count": slow_count,
                    "top_path": top_path,
                    "top_path_count": top_path_count,
                    "top_method": top_method,
                    "region": top_region,
                    "country_name": top_country,
                    "sample_date": sample_date,
                    "sample_hour": sample_hour
                })

            df_top20_ip = pd.DataFrame(rows)
            # 排序保险（已按 slow_count 取 top）
            df_top20_ip = df_top20_ip.sort_values("slow_count", ascending=False).reset_index(drop=True)

            st.subheader("按 path 出现次数选出的慢请求最多 Top20 IP")
            st.dataframe(df_top20_ip[["ip", "slow_count", "top_path", "top_path_count", "top_method", "region", "country_name", "sample_date", "sample_hour"]])
        except Exception as e:
            st.error(f"计算 Top20 IP 失败: {e}")
    else:
        st.info("未找到 slow requests 文件（18_slow_requests_stats.parquet），无法计算 Top20。")


    # ====== 读取并展示 high-frequency top20 IP（来自 output_abnormal_analytics/02_top20_high_freq_global_ip.parquet） ======
    p_top20 = ab_dir / "02_top20_high_freq_global_ip.parquet"
    if p_top20 is not None and p_top20.exists():
        try:
            df_top = pd.read_parquet(p_top20)

            # 尝试标准化列名
            col_map = {}
            if "ip" not in df_top.columns:
                for c in df_top.columns:
                    if "ip" in c.lower():
                        col_map["ip"] = c
                        break
            if "total_requests" not in df_top.columns:
                for c in df_top.columns:
                    if c.lower() in ("total", "count", "requests", "total_requests"):
                        col_map["total_requests"] = c
                        break
            for k, v in col_map.items():
                df_top = df_top.rename(columns={v: k})

            # 确保存在必要列
            for c in ("ip", "total_requests", "country", "country_name"):
                if c not in df_top.columns:
                    df_top[c] = None

            df_top["total_requests"] = pd.to_numeric(df_top["total_requests"], errors="coerce").fillna(0).astype(int)
            total_all = df_top["total_requests"].sum() or 1
            df_top["pct_of_total"] = df_top["total_requests"] / total_all * 100
            df_top = df_top.sort_values("total_requests", ascending=False).head(20)

            # 格式化百分比列（显示为 xx.yy%）
            df_top["pct_of_total"] = df_top["pct_of_total"].map(lambda x: f"{x:.2f}%")

            st.subheader("高频请求 Top20 IP（02_top20_high_freq_global_ip）")
            st.dataframe(df_top[["ip", "total_requests", "country", "country_name", "pct_of_total"]])
        except Exception as e:
            st.error(f"读取或处理 {p_top20.name} 失败: {e}")
    else:
        st.info("未找到文件（02_top20_high_freq_global_ip.parquet），无法展示高频 Top20。")



    # ====== 绘制 4XX / 5XX 每小时变化折线（来自 output_abnormal_analytics/08_http_abnormal_hourly_errors.parquet） ======
    p_err_hourly = ab_dir / "08_http_abnormal_hourly_errors.parquet"
    if p_err_hourly is not None and p_err_hourly.exists():
        try:
            df_err = pd.read_parquet(p_err_hourly)

            # 兼容列名（期望有 date, hour, 4xx_rate_pct, 5xx_rate_pct）
            # 允许列名包含类似 '4xx' '5xx' 或 '4xx_rate_pct' 等
            date_col = next((c for c in ("date", "day") if c in df_err.columns), None)
            hour_col = next((c for c in ("hour", "hour_of_day") if c in df_err.columns), None)
            col_4xx = next((c for c in df_err.columns if "4xx" in c.lower() and "rate" in c.lower()), None)
            col_5xx = next((c for c in df_err.columns if "5xx" in c.lower() and "rate" in c.lower()), None)

            # 若找不到 rate 列，尝试使用计数列 4xx/5xx 再计算占比（基于 total）
            if col_4xx is None and "4xx" in "".join(df_err.columns).lower():
                col_4xx = next((c for c in df_err.columns if c.lower().startswith("4xx")), None)
            if col_5xx is None and "5xx" in "".join(df_err.columns).lower():
                col_5xx = next((c for c in df_err.columns if c.lower().startswith("5xx")), None)

            if date_col is None:
                # 尝试时间戳列
                ts_col = next((c for c in ("ts", "timestamp", "time", "datetime") if c in df_err.columns), None)
                if ts_col:
                    df_err["_ts"] = pd.to_datetime(df_err[ts_col], errors="coerce")
                    df_err["date"] = df_err["_ts"].dt.strftime("%Y-%m-%d")
                    df_err["hour"] = df_err["_ts"].dt.hour
                    date_col = "date"
                    hour_col = "hour"
            if date_col is None or hour_col is None:
                st.info("无法识别 `08_http_abnormal_hourly_errors.parquet` 中的 date/hour 列，无法绘制错误折线。")
            else:
                # 确保存在数值列
                df_err[hour_col] = pd.to_numeric(df_err[hour_col], errors="coerce").fillna(0).astype(int)
                df_err[date_col] = df_err[date_col].astype(str)

                # 如果已有 rate 列（百分比或小数），标准化为百分比数值
                def to_pct_series(col):
                    s = pd.to_numeric(df_err[col], errors="coerce").copy()
                    # 如果值看起来在 0-1 之间，则乘以100
                    if s.max() <= 1.0:
                        s = s * 100
                    return s

                if col_4xx and col_5xx:
                    s4 = to_pct_series(col_4xx)
                    s5 = to_pct_series(col_5xx)
                else:
                    # 回退：用计数列 / total 计算百分比
                    total_col = next((c for c in ("total", "total_requests", "requests") if c in df_err.columns), None)
                    col_4xx_count = col_4xx if col_4xx and ("rate" not in col_4xx.lower()) else None
                    col_5xx_count = col_5xx if col_5xx and ("rate" not in col_5xx.lower()) else None
                    if total_col and (col_4xx_count or col_5xx_count):
                        s4 = (pd.to_numeric(df_err[col_4xx_count], errors="coerce").fillna(0) / pd.to_numeric(df_err[total_col], errors="coerce").replace(0, pd.NA).fillna(0)) * 100 if col_4xx_count else pd.Series(0, index=df_err.index)
                        s5 = (pd.to_numeric(df_err[col_5xx_count], errors="coerce").fillna(0) / pd.to_numeric(df_err[total_col], errors="coerce").replace(0, pd.NA).fillna(0)) * 100 if col_5xx_count else pd.Series(0, index=df_err.index)
                    else:
                        st.info("未找到可用于计算 4xx/5xx 比例的列（既无 rate 列，也无 count+total 列）。")
                        s4 = s5 = None

                if s4 is not None and s5 is not None:
                    df_plot = df_err[[date_col, hour_col]].copy()
                    df_plot["hour"] = df_plot[hour_col].astype(int)
                    df_plot["datetime"] = pd.to_datetime(df_plot[date_col], errors="coerce") + pd.to_timedelta(df_plot["hour"], unit="h")
                    df_plot = df_plot.assign(_4xx_pct=s4.values, _5xx_pct=s5.values)
                    df_plot = df_plot.sort_values("datetime").dropna(subset=["datetime"])

                    df_melt = df_plot[["datetime", "_4xx_pct", "_5xx_pct"]].melt(id_vars="datetime",
                                                                                value_vars=["_4xx_pct", "_5xx_pct"],
                                                                                var_name="type", value_name="pct")
                    df_melt["type"] = df_melt["type"].map({"_4xx_pct": "4XX 错误率 (%)", "_5xx_pct": "5XX 错误率 (%)"})

                    fig_err = px.line(df_melt, x="datetime", y="pct", color="type", markers=True,
                                    labels={"datetime": "时间", "pct": "错误率 (%)", "type": "类别"},
                                    title="每小时 4XX / 5XX 错误率变化")
                    fig_err.update_layout(xaxis=dict(tickformat="%Y-%m-%d\n%H:%M"))
                    st.plotly_chart(fig_err, use_container_width=True)
        except Exception as e:
            st.error(f"读取或绘制 {p_err_hourly.name} 失败: {e}")
    else:
        st.info("未找到文件（08_http_abnormal_hourly_errors.parquet），无法绘制 4XX/5XX 折线图。")





    # ====== 展示最容易出现 4XX/5XX 的 path（来自 output_abnormal_analytics/12_top404_paths.parquet） ======
    p_top_paths = ab_dir / "12_top404_paths.parquet"
    if p_top_paths is not None and p_top_paths.exists():
        try:
            df_paths = pd.read_parquet(p_top_paths)

            # 兼容列名：期望有 path, total, 4xx, 5xx, 可选 5xx_rate_pct
            # 尝试标准化常见列名
            col_map = {}
            for want in ("path", "total", "4xx", "5xx", "5xx_rate_pct"):
                if want in df_paths.columns:
                    continue
                # 匹配变体
                low_cols = {c.lower(): c for c in df_paths.columns}
                if want == "path":
                    candidate = next((c for k, c in low_cols.items() if "path" in k), None)
                elif want == "total":
                    candidate = next((c for k, c in low_cols.items() if k in ("total", "total_requests", "requests", "count")), None)
                elif want == "4xx":
                    candidate = next((c for k, c in low_cols.items() if k.startswith("4xx") and "rate" not in k), None)
                elif want == "5xx":
                    candidate = next((c for k, c in low_cols.items() if k.startswith("5xx") and "rate" not in k), None)
                elif want == "5xx_rate_pct":
                    candidate = next((c for k, c in low_cols.items() if "5xx" in k and "rate" in k), None)
                else:
                    candidate = None

                if candidate:
                    col_map[candidate] = want

            if col_map:
                df_paths = df_paths.rename(columns=col_map)

            # 确保关键列存在
            for c in ("path", "total", "4xx", "5xx"):
                if c not in df_paths.columns:
                    df_paths[c] = 0 if c != "path" else None

            # 转为数值并填充
            df_paths["total"] = pd.to_numeric(df_paths["total"], errors="coerce").fillna(0).astype(int)
            df_paths["4xx"] = pd.to_numeric(df_paths["4xx"], errors="coerce").fillna(0).astype(int)
            df_paths["5xx"] = pd.to_numeric(df_paths["5xx"], errors="coerce").fillna(0).astype(int)

            # 计算 4xx_rate_pct、5xx_rate_pct（若已有 5xx_rate_pct 则覆盖为标准化数值；否则计算）
            def calc_rate(count_series, total_series):
                cnt = safe_to_numeric(count_series).fillna(0)
                tot = safe_to_numeric(total_series)  # tot 中的 0/NaN 会被视为不可用分母
                safe_tot = tot.replace(0, np.nan)
                res = (cnt / safe_tot) * 100
                return res.fillna(0)

            df_paths["4xx_rate_pct"] = calc_rate(df_paths["4xx"], df_paths["total"])
            if "5xx_rate_pct" in df_paths.columns:
                # 标准化现有列为百分比数值（如果在 0-1 之间则 *100）
                tmp = pd.to_numeric(df_paths["5xx_rate_pct"], errors="coerce").fillna(0)
                if tmp.max() <= 1.0:
                    tmp = tmp * 100
                df_paths["5xx_rate_pct"] = tmp
            else:
                df_paths["5xx_rate_pct"] = calc_rate(df_paths["5xx"], df_paths["total"])

            # 选 top N（默认 50 或全部），按 total 或 4xx 排序展示最容易出现 4xx/5xx 的 path
            top_show = df_paths.sort_values(["4xx", "total"], ascending=[False, False]).head(50)
            # 格式化百分比列为 xx.yy%
            top_show = top_show.assign(
                total=top_show["total"],
                _4xx=top_show["4xx"],
                _5xx=top_show["5xx"],
                _4xx_rate=top_show["4xx_rate_pct"].map(lambda x: f"{x:.2f}%"),
                _5xx_rate=top_show["5xx_rate_pct"].map(lambda x: f"{x:.2f}%")
            )

            st.subheader("最容易出现 4XX / 5XX 的 Path（12_top404_paths）")
            st.dataframe(top_show[["path", "total", "_4xx", "_5xx", "_4xx_rate", "_5xx_rate"]].rename(columns={
                "path": "path",
                "total": "total",
                "_4xx": "4xx",
                "_5xx": "5xx",
                "_4xx_rate": "4xx_rate_pct",
                "_5xx_rate": "5xx_rate_pct"
            }))
        except Exception as e:
            st.error(f"读取或处理 {p_top_paths.name} 失败: {e}")
    else:
        st.info("未找到文件（12_top404_paths.parquet），无法展示 top paths。")



    # 在 render_abnormal 中替换原散点段为下面代码（支持交互采样/TopN）
    p_if = ab_dir / "27_ip_anomaly_scores.parquet"
    if p_if.exists():
        try:
            df_if = read_parquet_cached(p_if)
            # 转数值（并保留原 ip 列）
            for c in ("iso_score","req_per_min","total_reqs","error_rate","avg_resp_ms"):
                if c in df_if.columns:
                    df_if[c] = pd.to_numeric(df_if[c], errors="coerce").fillna(0)
            # 控制点数：用户可选抽样比例或 TopN
            max_points = st.sidebar.slider("散点最大点数", min_value=200, max_value=20000, value=2000, step=200)
            sample_mode = st.sidebar.selectbox("抽样模式", ("random_sample","top_by_iso_score","all"), index=0)
            if sample_mode == "top_by_iso_score" and "iso_score" in df_if.columns:
                df_plot = df_if.sort_values("iso_score", ascending=False).head(max_points)
            elif sample_mode == "random_sample":
                df_plot = df_if.sample(n=min(len(df_if), max_points), random_state=42)
            else:
                df_plot = df_if if len(df_if) <= max_points else df_if.sample(n=max_points, random_state=42)

            # x 轴处理
            if "req_per_min" in df_plot.columns:
                df_plot["req_per_min_log"] = np.log1p(df_plot["req_per_min"])
                x_col = "req_per_min_log"; x_label = "log(1 + req_per_min)"
            else:
                x_col = "ip_index" if "ip_index" in df_plot.columns else df_plot.index
                x_label = "ip_index"

            y_col = "iso_score" if "iso_score" in df_plot.columns else None
            color_col = "iso_label" if "iso_label" in df_plot.columns else "iso_score"

            # size 限制（避免极大值影响渲染）
            if "total_reqs" in df_plot.columns:
                df_plot["_size"] = (df_plot["total_reqs"] / (df_plot["total_reqs"].quantile(0.95) + 1)).clip(0.5, 6)
                size_col = "_size"
            else:
                size_col = None

            title = "IF 散点图：req_per_min vs iso_score（按 iso_label 着色）"
            fig = px.scatter(df_plot, x=x_col, y=y_col, color=color_col, size=size_col,
                            hover_data=["ip"] if "ip" in df_plot.columns else None,
                            labels={x_col: x_label, y_col: "iso_score", color_col: "iso_label"},
                            title=title)
            # 启用 WebGL（大数据时提升性能）
            fig.update_traces(marker=dict(opacity=0.8), selector=dict(mode="markers"))
            try:
                # 优先使用 Scattergl
                import plotly.graph_objects as go
                scatter = go.Scattergl(x=fig.data[0].x, y=fig.data[0].y, mode="markers",
                                    marker=fig.data[0].marker, text=fig.data[0].text if hasattr(fig.data[0],"text") else None)
                g = go.Figure(scatter)
                # 如果存在分组颜色，需要构建多个 trace；上面示范用于单-trace情形
                st.plotly_chart(g, use_container_width=True)
            except Exception:
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"读取或绘制 27_ip_anomaly_scores 散点图失败: {e}")
    else:
        st.info("未找到 27_ip_anomaly_scores.parquet，跳过 IF 散点图。")







    # ====== 气泡散点图：定位高危 IP（req_per_min vs error_rate，颜色=iso_label，大小=total_reqs） ======
    p_if = ab_dir / "27_ip_anomaly_scores.parquet"
    if p_if.exists():
        try:
            df_if = read_parquet_cached(p_if)

            # 保证关键列为数值
            for c in ("req_per_min", "error_rate", "total_reqs", "iso_score"):
                if c in df_if.columns:
                    df_if[c] = safe_to_numeric(df_if[c]).fillna(0)

            # 少量预处理：避免极端点影响大小，加入 log 列便于展示
            if "req_per_min" in df_if.columns:
                df_if["req_per_min_log"] = np.log1p(df_if["req_per_min"])
                x_col = "req_per_min_log"; x_label = "log(1 + req_per_min)"
            else:
                x_col = "ip_index" if "ip_index" in df_if.columns else "ip"
                x_label = x_col

            y_col = "error_rate" if "error_rate" in df_if.columns else ("errors" if "errors" in df_if.columns else None)
            color_col = "iso_label" if "iso_label" in df_if.columns else "iso_score"
            size_raw = "total_reqs" if "total_reqs" in df_if.columns else None

            # 控制点数（避免一次渲染过多）
            max_points = st.sidebar.slider("气泡图最大点数", 200, 20000, 3000, 200)
            if len(df_if) > max_points:
                # 优先展示 iso_score 高的点，再填充随机样本
                if "iso_score" in df_if.columns:
                    top_n = int(max_points * 0.3)
                    top = df_if.sort_values("iso_score", ascending=False).head(top_n)
                    rest = df_if.drop(top.index).sample(n=(max_points - top_n), random_state=42)
                    df_plot = pd.concat([top, rest])
                else:
                    df_plot = df_if.sample(n=max_points, random_state=42)
            else:
                df_plot = df_if

            # 规范化并缩放 size，避免极大点
            if size_raw and size_raw in df_plot.columns:
                q95 = df_plot[size_raw].quantile(0.95) if df_plot[size_raw].notna().any() else 1
                df_plot["_size"] = (df_plot[size_raw] / (q95 + 1)).clip(0.3, 8)
                size_col = "_size"
            else:
                size_col = None

            hover = ["ip", "ip_index", "total_reqs", "req_per_min", "error_rate", "iso_score"]
            hover = [h for h in hover if h in df_plot.columns]

            title = "气泡散点图：req_per_min vs error_rate（颜色=iso_label，大小=total_reqs）"
            fig = px.scatter(df_plot, x=x_col, y=y_col, color=color_col, size=size_col,
                            hover_data=hover, labels={x_col: x_label, y_col: "error_rate", color_col: "iso_label"},
                            title=title)

            # 尽量用 Scattergl 渲染以加速大点集
            try:
                import plotly.graph_objects as go
                traces = []
                if color_col in df_plot.columns and df_plot[color_col].nunique() > 1:
                    for lbl, sub in df_plot.groupby(color_col):
                        traces.append(go.Scattergl(
                            x=sub[x_col], y=sub[y_col],
                            mode="markers",
                            marker=dict(size=sub[size_col] if size_col else 6, opacity=0.8),
                            name=str(lbl),
                            text=sub["ip"] if "ip" in sub.columns else None,
                            hoverinfo="text+x+y"
                        ))
                    g = go.Figure(data=traces)
                else:
                    g = go.Figure(go.Scattergl(
                        x=fig.data[0].x, y=fig.data[0].y,
                        mode="markers",
                        marker=fig.data[0].marker,
                        text=fig.data[0].text if hasattr(fig.data[0], "text") else None
                    ))
                g.update_layout(title=title)
                st.plotly_chart(g, use_container_width=True)
            except Exception:
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"读取或绘制 27_ip_anomaly_scores 气泡图失败: {e}")
    else:
        st.info("未找到 27_ip_anomaly_scores.parquet，跳过气泡散点图。")



    # ====== 分组箱线图 / 小提琴图：按 iso_label 校验异常特征差异 ======
    p_if = ab_dir / "27_ip_anomaly_scores.parquet"
    if p_if.exists():
        try:
            df_if = read_parquet_cached(p_if)

            # 需要比较的指标列表（存在则使用）
            metrics = ["req_per_min", "path_diversity", "uniq_uas", "avg_resp_ms"]
            use_metrics = [m for m in metrics if m in df_if.columns]
            if not use_metrics:
                st.info("27_ip_anomaly_scores 中缺少用于比较的指标，跳过箱线/小提琴图。")
            else:
                # 清洗数值列（保留 iso_label 列）
                for c in use_metrics + ["iso_label"]:
                    if c in df_if.columns:
                        if c == "iso_label":
                            df_if[c] = df_if[c].astype(str).fillna("NA")
                        else:
                            df_if[c] = safe_to_numeric(df_if[c]).fillna(0)

                # 限制样本数以保证交互流畅
                max_rows = st.sidebar.slider("箱线/小提琴 最大样本数", 200, 5000, 2000, 200)
                if len(df_if) > max_rows:
                    # 保留各标签下的代表性样本：先按 iso_score 取 top，再随机补全
                    if "iso_score" in df_if.columns:
                        top_frac = 0.2
                        top_n = int(max_rows * top_frac)
                        top = df_if.sort_values("iso_score", ascending=False).head(top_n)
                        rest = df_if.drop(top.index).sample(n=(max_rows - top_n), random_state=42)
                        df_plot = pd.concat([top, rest])
                    else:
                        df_plot = df_if.sample(n=max_rows, random_state=42)
                else:
                    df_plot = df_if

                st.subheader("按 `iso_label` 分组的指标分布（箱线图 & 小提琴图）")

                # 绘制每个指标的箱线图与小提琴图（并列）
                for m in use_metrics:
                    col1, col2 = st.columns(2)
                    with col1:
                        fig_box = px.box(df_plot, x="iso_label", y=m, color="iso_label",
                                        points="outliers", title=f"箱线图：{m} 按 iso_label 分组",
                                        labels={"iso_label": "iso_label", m: m})
                        st.plotly_chart(fig_box, use_container_width=True)
                    with col2:
                        fig_violin = px.violin(df_plot, x="iso_label", y=m, color="iso_label",
                                            box=True, points="all",
                                            title=f"小提琴图：{m} 按 iso_label 分组",
                                            labels={"iso_label": "iso_label", m: m})
                        st.plotly_chart(fig_violin, use_container_width=True)

                # 可选：显示每组的描述性统计表，便于数值对比
                if st.checkbox("显示分组描述性统计（按 iso_label）", value=False):
                    desc = df_plot.groupby("iso_label")[use_metrics].describe().transpose()
                    st.dataframe(desc)
        except Exception as e:
            st.error(f"绘制分组箱线/小提琴图失败: {e}")
    else:
        st.info("未找到 27_ip_anomaly_scores.parquet，跳过箱线/小提琴图。")



    # ====== 二维散点图：path_diversity vs total_reqs（定向路径攻击检测） ======
    p_if = ab_dir / "27_ip_anomaly_scores.parquet"
    if p_if.exists():
        try:
            df_if = read_parquet_cached(p_if)

            # 清洗并准备列
            for c in ("path_diversity", "total_reqs", "req_per_min", "iso_score"):
                if c in df_if.columns:
                    df_if[c] = safe_to_numeric(df_if[c]).fillna(0)

            x_col = "path_diversity" if "path_diversity" in df_if.columns else ("uniq_paths" if "uniq_paths" in df_if.columns else None)
            y_col = "total_reqs" if "total_reqs" in df_if.columns else None
            size_raw = "req_per_min" if "req_per_min" in df_if.columns else None
            color_col = "iso_label" if "iso_label" in df_if.columns else "iso_score"

            if x_col is None or y_col is None:
                st.info("缺少 path_diversity 或 total_reqs 列，无法绘制定向路径攻击散点图。")
            else:
                # 控制点数
                max_points = st.sidebar.slider("路径攻击散点最大点数", 200, 20000, 3000, 200)
                if len(df_if) > max_points:
                    # 保留 iso_score 高的部分 + 随机样本
                    if "iso_score" in df_if.columns:
                        top_n = int(max_points * 0.3)
                        top = df_if.sort_values("iso_score", ascending=False).head(top_n)
                        rest = df_if.drop(top.index).sample(n=(max_points - top_n), random_state=42)
                        df_plot = pd.concat([top, rest])
                    else:
                        df_plot = df_if.sample(n=max_points, random_state=42)
                else:
                    df_plot = df_if

                # size 缩放
                if size_raw and size_raw in df_plot.columns:
                    q95 = df_plot[size_raw].quantile(0.95) if df_plot[size_raw].notna().any() else 1
                    df_plot["_size"] = (df_plot[size_raw] / (q95 + 1)).clip(0.5, 8)
                    size_col = "_size"
                else:
                    size_col = None

                hover = [c for c in ("ip", "ip_index", x_col, y_col, "req_per_min", "iso_score") if c in df_plot.columns]
                title = "定向路径攻击检测：path_diversity vs total_reqs（大小=req_per_min，色=iso_label）"

                fig = px.scatter(df_plot, x=x_col, y=y_col, color=color_col, size=size_col,
                                hover_data=hover, labels={x_col: "path_diversity", y_col: "total_reqs", color_col: "iso_label"},
                                title=title)

                # 优先用 Scattergl 分组渲染以提升性能
                try:
                    import plotly.graph_objects as go
                    traces = []
                    if color_col in df_plot.columns and df_plot[color_col].nunique() > 1:
                        for lbl, sub in df_plot.groupby(color_col):
                            traces.append(go.Scattergl(
                                x=sub[x_col], y=sub[y_col],
                                mode="markers",
                                marker=dict(size=sub[size_col] if size_col else 6, opacity=0.85),
                                name=str(lbl),
                                text=sub["ip"] if "ip" in sub.columns else None,
                                hoverinfo="text+x+y"
                            ))
                        g = go.Figure(data=traces)
                    else:
                        g = go.Figure(go.Scattergl(
                            x=fig.data[0].x, y=fig.data[0].y,
                            mode="markers",
                            marker=fig.data[0].marker,
                            text=fig.data[0].text if hasattr(fig.data[0], "text") else None
                        ))
                    g.update_layout(title=title, xaxis_title="path_diversity", yaxis_title="total_reqs")
                    st.plotly_chart(g, use_container_width=True)
                except Exception:
                    st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"绘制 path_diversity vs total_reqs 散点图失败: {e}")
    else:
        st.info("未找到 27_ip_anomaly_scores.parquet，跳过路径攻击散点图。")