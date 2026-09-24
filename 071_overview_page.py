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


def render_overview(base_dir: str):
    # --------- overview 模式：读取并展示三个 parquet 的总体指标 ---------
    base = Path(base_dir)
    print(f"Rendering overview page from: {base}")
    p1 = base / "01_network_traffic_overview.parquet"
    p2 = base / "02_request_method_dist.parquet"
    p3 = base / "04_ua_type_dist.parquet"

    st.header("IP 流量总体情况 — 概览")
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

            if "distinct_ips" in df1.columns:
                try:
                    unique_ips = int(pd.to_numeric(df1["distinct_ips"].iloc[0], errors="coerce"))
                except Exception:
                    unique_ips = int(len(df1))
            else:
                unique_ips = int(len(df1))
            

            if "distinct_paths" in df1.columns:
                try:
                    unique_paths = int(pd.to_numeric(df1["distinct_paths"].iloc[0], errors="coerce"))
                except Exception:
                    unique_paths = int(len(df1))
            else:
                unique_paths = int(len(df1))

            if "distinct_countries" in df1.columns:
                try:
                    unique_countries = int(pd.to_numeric(df1["distinct_countries"].iloc[0], errors="coerce"))
                except Exception:
                    unique_countries = int(len(df1))
            else:
                unique_countries = int(len(df1))


            time_range = "—"
            time_span_days = "—"
            if "time_span_seconds" in df1.columns:
                try:
                    total_seconds = pd.to_numeric(df1["time_span_seconds"].iloc[0], errors="coerce")
                    if not pd.isna(total_seconds):
                        time_span_days = round(total_seconds / (3600 * 24), 3)
                        time_range = f"{time_span_days} 天"
                except Exception:
                    time_range = "—"
                    time_span_days = "—"


            err_rate = "—"
            p_err = base / "16_hourly_error_stats.parquet"
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
                print(f"总请求数: {total_requests_sum}, 错误数: {error_count_sum}")
                if total_requests_sum > 0:
                    err_rate = f"{(error_count_sum / total_requests_sum * 100):.2f}%"
                else:
                    err_rate = "—"


            p95_rt = "—"
            # 优先从汇总文件读取 p95（单位 ms）
            p19 = Path(DATA_DIRS["further"]) / "19_response_summary_stats.parquet"
            try:
                if p19.exists():
                    df19 = pd.read_parquet(p19)
                    if "p95_response_time_ms" in df19.columns:
                        val = pd.to_numeric(df19["p95_response_time_ms"].iloc[0], errors="coerce")
                        if not pd.isna(val):
                            p95_rt = f"{round(float(val), 3)} ms"
                    elif "p95" in df19.columns:
                        val = pd.to_numeric(df19["p95"].iloc[0], errors="coerce")
                        if not pd.isna(val):
                            p95_rt = f"{round(float(val), 3)} ms"
            except Exception:
                p95_rt = "—"


            p50_rt = "—"
            try:
                if p19.exists():
                    df19 = pd.read_parquet(p19)
                    if "p50_response_time_ms" in df19.columns:
                        val = pd.to_numeric(df19["p50_response_time_ms"].iloc[0], errors="coerce")
                        if not pd.isna(val):
                            p50_rt = f"{round(float(val), 1)} ms"
                    elif "p50" in df19.columns:
                        val = pd.to_numeric(df19["p50"].iloc[0], errors="coerce")
                        if not pd.isna(val):
                            p50_rt = f"{round(float(val), 1)} ms"
            except Exception:
                p50_rt = "—"

            avg_rt = "—"
            try:
                if p19.exists():
                    df19 = pd.read_parquet(p19)
                    if "avg_response_time_ms" in df19.columns:
                        val = pd.to_numeric(df19["avg_response_time_ms"].iloc[0], errors="coerce")
                        if not pd.isna(val):
                            avg_rt = f"{round(float(val), 1)} ms"
                    elif "avg" in df19.columns:
                        val = pd.to_numeric(df19["avg"].iloc[0], errors="coerce")
                        if not pd.isna(val):
                            avg_rt = f"{round(float(val), 1)} ms"
            except Exception:
                avg_rt = "—"

            min_rt = "—"
            try:
                if p19.exists():
                    df19 = pd.read_parquet(p19)
                    if "min_response_time_ms" in df19.columns:
                        val = pd.to_numeric(df19["min_response_time_ms"].iloc[0], errors="coerce")
                        if not pd.isna(val):
                            min_rt = f"{round(float(val), 1)} ms"
                    elif "min" in df19.columns:
                        val = pd.to_numeric(df19["min"].iloc[0], errors="coerce")
                        if not pd.isna(val):
                            min_rt = f"{round(float(val), 1)} ms"
            except Exception:
                min_rt = "—"

            max_rt = "—"
            try:
                if p19.exists():
                    df19 = pd.read_parquet(p19)
                    if "max_response_time_ms" in df19.columns:
                        val = pd.to_numeric(df19["max_response_time_ms"].iloc[0], errors="coerce")
                        max_rt = fmt_rt_ms(val)
                    elif "max" in df19.columns:
                        val = pd.to_numeric(df19["max"].iloc[0], errors="coerce")
                        max_rt = fmt_rt_ms(val)
            except Exception:
                max_rt = "—"

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("总请求数", f"{total_requests:,}")
            k2.metric("独立 IP", str(unique_ips) if unique_ips is not None else "—")
            k3.metric("独立路径", str(unique_paths) if unique_paths is not None else "—")
            k4.metric("时间跨度", time_range)

            k5, k6, k7, k8 = st.columns(4)
            k5.metric("整体错误率", err_rate)
            k6.metric("P95 响应时间", p95_rt)
            k7.metric("P50 响应时间", p50_rt)
            k8.metric("平均响应时间", avg_rt)
            
            
            k9, k10, k11, k12 = st.columns(4)
            k9.metric("最小响应时间", min_rt)
            k10.metric("最大响应时间", max_rt)
            k11.metric("独立国家", str(unique_countries) if unique_countries is not None else "—")

            # === KPI 卡片展示（插入结束） ===

            # 若 df1 包含 ip 和 bytes/count 列，显示几个常见图表
            if "ip" in df1.columns:
                # Top 20 by bytes 或 count
                value_col = None
                for cand in ("bytes", "traffic", "count"):
                    if cand in df1.columns:
                        value_col = cand
                        break
                if value_col:
                    top = df1.sort_values(value_col, ascending=False).head(20).set_index("ip")
                    st.subheader(f"按 `{value_col}` 排名前 20 的 IP")
                    st.bar_chart(top[value_col])
        except Exception as e:
            st.error(f"读取 {p1.name} 失败: {e}")
    else:
        st.warning(f"未找到文件: {p1}")

    # 2) 请求方法分布
    if p2.exists():
        try:
            df2 = pd.read_parquet(p2)
            st.subheader("请求方法分布（02_request_method_dist）")
            # st.dataframe(df2)
            # 假设 df2 是 method/count
            if "method" in df2.columns and ("count" in df2.columns or "value" in df2.columns):
                cnt_col = "count" if "count" in df2.columns else "value"
                pie_df = df2.set_index("method")[cnt_col].dropna()
                if not pie_df.empty:
                    # 合并占比很小的扇区到 "其他"
                    frac = pie_df / pie_df.sum()
                    others_mask = frac < 0.01
                    if others_mask.any() and others_mask.sum() > 1:
                        others = pie_df[others_mask].sum()
                        pie_df = pie_df[~others_mask].copy()
                        pie_df["其他"] = others

                    import plotly.express as px
                    pie_df = df2.reset_index().rename(columns={cnt_col: "value"})[["method", "value"]].dropna()
                    fig = px.pie(pie_df, names="method", values="value", title="")
                    fig.update_traces(
                        textinfo="percent+label",
                        hovertemplate="%{label}: %{value}（%{percent}）<extra></extra>"
                    )
                    fig.update_layout(
                        height=480,  # 稍大一点
                        legend=dict(orientation="v", y=0.5, x=1.02)
                    )
                    st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"读取 {p2.name} 失败: {e}")
    else:
        st.info(f"未找到文件: {p2}")

    # 3) UA 类型分布
    if p3.exists():
        try:
            df3 = pd.read_parquet(p3)
            st.subheader("UA 类型分布（04_ua_type_dist）")
            # st.dataframe(df3)
            if "ua_type" in df3.columns and ("count" in df3.columns or "value" in df3.columns):
                cnt_col = "count" if "count" in df3.columns else "value"
                plot_df = df3[["ua_type", cnt_col]].dropna().groupby("ua_type").sum().reset_index()
                plot_df = plot_df.sort_values(cnt_col, ascending=False)

                import seaborn as sns
                import matplotlib.pyplot as plt
                plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']  # 优先尝试微软雅黑，再退回黑体
                plt.rcParams['axes.unicode_minus'] = False
                plt.figure(figsize=(8, 4))
                base_colors = ["#FF6B6B", "#FFD93D", "#6BCB77", "#4D96FF", "#9B5DE5"]
                palette = sns.color_palette(base_colors * ((len(plot_df) // len(base_colors)) + 1))[:len(plot_df)]
                sns.set_palette(palette)

                # 不传 palette 参数
                ax = sns.barplot(data=plot_df, x=cnt_col, y="ua_type")
                ax.set_xlabel("Count")
                ax.set_ylabel("UA Type")
                ax.set_title("UA 类型分布")
                for p in ax.patches:
                    width = p.get_width()
                    y = p.get_y() + p.get_height() / 2
                    ax.annotate(f'{int(width):,}',
                                xy=(width, y),
                                xytext=(-6, 0),
                                textcoords='offset points',
                                va='center',
                                ha='right',
                                color='white',
                                fontsize=9)
                plt.tight_layout()
                st.pyplot(plt.gcf(), clear_figure=True)
        except Exception as e:
            st.error(f"读取 {p3.name} 失败: {e}")
    else:
        st.info(f"未找到文件: {p3}")



    # 国家流量统计（来自 output_further_analytics/05_country_traffic_stats.parquet）
    p4 = base / "05_country_traffic_stats.parquet"
    if p4.exists():
        try:
            df4 = pd.read_parquet(p4)
            st.subheader("各国 IP 流量统计（05_country_traffic_stats）")
            # st.dataframe(df4)

            # 规范列名：期望包含 country / ip_count / requests / value 等
            country_col = None
            count_col = None
            for c in ("country", "country_name", "nation"):
                if c in df4.columns:
                    country_col = c
                    break
            for c in ("ip_count", "distinct_ips", "count", "requests", "value"):
                if c in df4.columns:
                    count_col = c
                    break

            if country_col and count_col:
                agg = df4[[country_col, count_col]].dropna()
                agg[count_col] = pd.to_numeric(agg[count_col], errors="coerce").fillna(0)
                agg = agg.groupby(country_col)[count_col].sum().reset_index().sort_values(count_col, ascending=False)
                total = agg[count_col].sum()
                agg["pct"] = (agg[count_col] / total * 100).round(2)

                # 饼图（交互 hover 显示 count 和 pct）
                pie_df = agg.copy()
                fig_pie = px.pie(pie_df, names=country_col, values=count_col)
                fig_pie.update_traces(hovertemplate="%{label}: %{value}（%{percent})<extra></extra>")
                fig_pie.update_layout(
                    height=480,  # 稍大一点
                    legend=dict(orientation="v", y=0.5, x=1.02)
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("`05_country_traffic_stats.parquet` 中未找到可识别的国家或计数列，请检查列名（例如 country, ip_count）。")
        except Exception as e:
            st.error(f"读取 {p4.name} 失败: {e}")
    else:
        st.info(f"未找到文件: {p4}")

    # URL 分类流量统计（来自 output_further_analytics/06_url_category_traffic_stats.parquet）
    p5 = base / "06_url_category_traffic_stats.parquet"
    if p5.exists():
        try:
            df5 = pd.read_parquet(p5)
            st.subheader("URL 分类流量统计（06_url_category_traffic_stats）")
            # st.dataframe(df5)

            # 识别列名
            cat_col = None
            count_col = None
            for c in ("category", "url_category", "category_name"):
                if c in df5.columns:
                    cat_col = c
                    break
            for c in ("ip_count", "distinct_ips", "count", "requests", "value"):
                if c in df5.columns:
                    count_col = c
                    break

            if cat_col and count_col:
                agg = df5[[cat_col, count_col]].dropna()
                agg[count_col] = pd.to_numeric(agg[count_col], errors="coerce").fillna(0)
                agg = agg.groupby(cat_col)[count_col].sum().reset_index().sort_values(count_col, ascending=False)
                total = agg[count_col].sum()
                agg["pct"] = (agg[count_col] / total * 100).round(2)

                # 只绘制 top N（可调整）
                topn = agg.head(20)

                import seaborn as sns
                import matplotlib.pyplot as plt
                plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
                plt.rcParams['axes.unicode_minus'] = False

                # 更鲜艳的自定义配色（按类别数量截取）
                base_colors = ["#FF6B6B", "#FFB86B", "#FFD93D", "#6BCB77", "#4D96FF", "#9B5DE5", "#FF5DA2", "#00C2A8"]
                palette = sns.color_palette(base_colors * ((len(topn) // len(base_colors)) + 1))[:len(topn)]

                plt.figure(figsize=(max(6, 0.35 * len(topn)), 6))
                order = topn[cat_col].tolist()
                ax = sns.barplot(data=topn, x=cat_col, y=count_col, order=order)
                ax.set_xlabel("URL 分类")
                ax.set_ylabel("请求数")
                ax.set_title("URL 分类流量（按请求数排序）")
                ax.tick_params(axis='x', rotation=45)  # x 标签倾斜

                # 在柱内顶部显示数值，自动根据柱高选择白色或黑色文字
                for p in ax.patches:
                    height = p.get_height()
                    x = p.get_x() + p.get_width() / 2
                    # 选择文字颜色：若柱较深则白色，否则黑色
                    facecolor = p.get_facecolor()
                    luminance = 0.299 * facecolor[0] + 0.587 * facecolor[1] + 0.114 * facecolor[2]
                    text_color = 'white' if luminance < 0.6 else 'black'
                    ax.annotate(
                        f'{int(height):,}',
                        xy=(x, height),
                        xytext=(0, -6),               # 放到柱内靠顶部的位置（向下偏移）
                        textcoords='offset points',
                        ha='center',
                        va='top',
                        color=text_color,
                        fontsize=9
                    )

                plt.tight_layout()
                st.pyplot(plt.gcf(), clear_figure=True)
            else:
                st.info("未检测到可识别的分类或计数列（例如 category, ip_count）。")
        except Exception as e:
            st.error(f"读取 {p5.name} 失败: {e}")
    else:
        st.info(f"未找到文件: {p5}")


    # HTTP 状态码分布（07_http_status_code_dist.parquet） — 表格 + Donut 图
    p6 = base / "07_http_status_code_dist.parquet"
    if p6.exists():
        try:
            df6 = pd.read_parquet(p6)
            st.subheader("HTTP 状态码分布（07_http_status_code_dist）")

            # 识别状态码与计数列
            status_col = None
            count_col = None
            for c in ("status", "status_code", "http_status"):
                if c in df6.columns:
                    status_col = c
                    break
            for c in ("count", "value", "requests", "freq"):
                if c in df6.columns:
                    count_col = c
                    break

            if status_col and count_col:
                agg = df6[[status_col, count_col]].dropna()
                agg[count_col] = pd.to_numeric(agg[count_col], errors="coerce").fillna(0)
                agg = agg.groupby(status_col)[count_col].sum().reset_index().sort_values(count_col, ascending=False)
                total = agg[count_col].sum()
                agg["pct"] = (agg[count_col] / total * 100).round(2)

                # 绘制 donut（环形图）
                import matplotlib.pyplot as plt
                plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
                plt.rcParams['axes.unicode_minus'] = False

                labels = agg[status_col].astype(str).tolist()
                sizes = agg[count_col].tolist()

                # 更鲜艳颜色序列
                colors = ["#FF6B6B", "#FFB86B", "#FFD93D", "#6BCB77", "#4D96FF", "#9B5DE5", "#FF5DA2", "#00C2A8",
                            "#8E44AD", "#E74C3C"]
                colors = (colors * ((len(labels) // len(colors)) + 1))[:len(labels)]

                fig, ax = plt.subplots(figsize=(6, 6))
                # 计算占比并标记小扇区
                total_sizes = sum(sizes)
                # 计算占比与小扇区掩码
                fracs = [s / total_sizes for s in sizes]
                small_mask = [f < 0.01 for f in fracs]

                # 先画扇区（不画任何自动文本）
                wedges, texts = ax.pie(
                    sizes,
                    labels=None,
                    colors=colors,
                    startangle=90,
                    wedgeprops=dict(width=0.55, edgecolor='w')
                )

                # 中心空白做成 donut
                centre_circle = plt.Circle((0, 0), 0.45, fc='white', linewidth=0)
                fig.gca().add_artist(centre_circle)

                # 给大扇区在内部添加百分比标签
                for i, (w, frac) in enumerate(zip(wedges, fracs)):
                    ang = (w.theta2 + w.theta1) / 2.0
                    x_text = 0.6 * np.cos(np.deg2rad(ang))
                    y_text = 0.6 * np.sin(np.deg2rad(ang))
                    pct_text = f"{frac*100:.1f}%"
                    if not small_mask[i]:
                        ax.text(x_text, y_text, pct_text, ha='center', va='center', color='white', fontsize=10, weight='bold')

                # 对小扇区在外侧显示带引线的标签（count + pct）
                # 方案：收集所有小扇区角度，按角度分组，对每组内的标签做小的角度与径向偏移，避免重叠
                small_angles = []
                for i, (w, is_small) in enumerate(zip(wedges, small_mask)):
                    if is_small:
                        # ang = (w.theta2 + w.theta1) / 2.0
                        # small_angles.append((i, ang))
                        facecolor = wedges[i].get_facecolor()

                from collections import defaultdict
                groups = defaultdict(list)
                # 按角度小数位分组，调整精度可改变分组敏感度
                for idx, ang in small_angles:
                    key = round(ang, 1)  # 以1位小数为分组依据（可调）
                    groups[key].append((idx, ang))

                # 参数：每个同角度标签之间角度间隔（度），径向偏移基数
                delta_deg = 4.0
                radial_step = 0.06

                for key, items in groups.items():
                    n = len(items)
                    for j, (i, ang) in enumerate(items):
                        # 为组内每个标签分配一个偏移，使其围绕原始角度分散
                        offset = (j - (n - 1) / 2.0) * delta_deg
                        ang_offset = ang + offset

                        # 起点（扇区外侧）略外移
                        x0 = 0.72 * np.cos(np.deg2rad(ang_offset))
                        y0 = 0.72 * np.sin(np.deg2rad(ang_offset))
                        # 文本位置更外一点，且按索引做小幅径向偏移以进一步避免纵向重叠
                        r_text = 1.05 + radial_step * (j - (n - 1) / 2.0)
                        x1 = r_text * np.cos(np.deg2rad(ang_offset))
                        y1 = r_text * np.sin(np.deg2rad(ang_offset))

                        label = f"{labels[i]}: {sizes[i]:,} ({agg['pct'].iloc[i]}%)"
                        ax.annotate(
                            label,
                            xy=(x0, y0),
                            xytext=(x1, y1),
                            ha='left' if x1 >= 0 else 'right',
                            va='center',
                            fontsize=9,
                            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.9),
                            arrowprops=dict(arrowstyle="-", connectionstyle=f"arc3,rad=0")
                        )

                # 右侧图例（保留）
                legend_labels = [f"{lab}: {cnt:,} ({pct}%)" for lab, cnt, pct in zip(labels, sizes, agg["pct"].tolist())]
                ax.legend(wedges, legend_labels, title="状态码: count (pct)", loc="center left", bbox_to_anchor=(1, 0.5), fontsize=9)

                ax.axis('equal')
                plt.tight_layout()
                st.pyplot(fig, clear_figure=True)
            else:
                st.info("`07_http_status_code_dist.parquet` 中未检测到状态码或计数列（例如 status, count）。")
        except Exception as e:
            st.error(f"读取 {p6.name} 失败: {e}")
    else:
        st.info(f"未找到文件: {p6}")



    # --- hourly traffic 折线图（来自 09_hourly_traffic_stats.parquet） ---
    
    p7 = base / "09_hourly_traffic_stats.parquet"
    if p7.exists():
        dfh = pd.read_parquet(p7)
        st.subheader("按小时的网络流量（09_hourly_traffic_stats和14_hourly_by_peak_traffic_stats）")

        # 识别列名
        date_col = None
        hour_col = None
        count_col = None
        for c in ("date", "day", "dt", "timestamp", "ts"):
            if c in dfh.columns:
                date_col = c
                break
        for c in ("hour", "hr", "h"):
            if c in dfh.columns:
                hour_col = c
                break
        for c in ("count", "requests", "value", "traffic"):
            if c in dfh.columns:
                count_col = c
                break

        if date_col is None or hour_col is None or count_col is None:
            st.info("`09_hourly_traffic_stats.parquet` 未包含可识别的 `date` / `hour` / `count` 列。")
        else:
            # 处理 date 列：只取年月日（兼容 ISO 带时区的字符串）
            # 例如 "2024-01-01T00:00:00.000Z" -> "2024-01-01"
            try:
                # 把可能的 bytes/object -> str
                s_date = dfh[date_col].astype(str)
                # 取前 10 个字符作为 YYYY-MM-DD（防护性做法）
                s_day = s_date.str.slice(0, 10)
                day_ts = pd.to_datetime(s_day, format="%Y-%m-%d", errors="coerce")

                # 处理 hour 列为整数（取整并限制 0-23）
                hr = pd.to_numeric(dfh[hour_col], errors="coerce").fillna(0).astype(int).clip(lower=0, upper=23)

                # 组合成完整时间戳：day + hour hours
                dfh["_ts"] = day_ts + pd.to_timedelta(hr, unit="h")

                # count 列数值化
                dfh[count_col] = pd.to_numeric(dfh[count_col], errors="coerce").fillna(0)

                # 丢弃无法解析的时间行
                dfh = dfh.dropna(subset=["_ts"])
                if dfh.empty:
                    st.info("解析后无可用时间数据，无法绘图。")
                else:
                    # 按小时聚合（若源已每小时则等于自身）
                    hourly = dfh.set_index("_ts").resample("h")[count_col].sum().reset_index()

                    if hourly.empty:
                        st.info("按小时聚合后无数据。")
                    else:
                        import plotly.express as px
                        # 鲜艳配色
                        color = "#FF6B6B"
                        # 尝试读取高峰定义文件（按小时标记 is_peak）
                        p_peak = base / "14_hourly_by_peak_traffic_stats.parquet"
                        peak_map = {}
                        if p_peak.exists():
                            try:
                                df_peak = pd.read_parquet(p_peak)
                                # 期望 df_peak 有 'hour' (int 0-23) 与 'is_peak' (bool 或 0/1) 列
                                if "hour" in df_peak.columns and "is_peak" in df_peak.columns:
                                    df_peak["hour"] = pd.to_numeric(df_peak["hour"], errors="coerce").fillna(-1).astype(int)
                                    df_peak["is_peak"] = df_peak["is_peak"].astype(bool)
                                    peak_map = dict(zip(df_peak["hour"].tolist(), df_peak["is_peak"].tolist()))
                            except Exception:
                                peak_map = {}

                        # 为每个时间点标记 is_peak（通过小时匹配）
                        hourly["_hour"] = hourly["_ts"].dt.hour
                        hourly["is_peak"] = hourly["_hour"].map(lambda h: bool(peak_map.get(int(h), False)))

                        import plotly.express as px
                        color_peak = "#FF6B6B"   # 高峰颜色（鲜艳）
                        color_off = "#4D96FF"    # 低峰颜色
                        fig = px.line(hourly, x="_ts", y=count_col, title="每小时流量趋势（高峰标记）",
                                    labels={"_ts": "时间（按小时）", count_col: "请求数"},
                                    template="plotly_white")
                        fig.update_traces(line=dict(width=3, color="#888888"), marker=dict(size=6), selector=dict(mode="lines"))

                        # 在线上叠加散点，用颜色区分高峰/非高峰
                        fig.add_trace(
                            px.scatter(hourly, x="_ts", y=count_col, color=hourly["is_peak"].map({True: "高峰", False: "非高峰"}),
                                    color_discrete_map={"高峰": color_peak, "非高峰": color_off}).data[0]
                        )
                        fig.add_trace(
                            px.scatter(hourly, x="_ts", y=count_col, color=hourly["is_peak"].map({True: "高峰", False: "非高峰"}),
                                    color_discrete_map={"高峰": color_peak, "非高峰": color_off}).data[1]
                        )

                        # 保证每天有主刻度
                        start_ts = hourly["_ts"].min()
                        fig.update_layout(
                            xaxis=dict(
                                rangeslider=dict(visible=True),
                                tickformat="%Y-%m-%d\n%H:00",
                                tick0=start_ts,
                                dtick=24*60*60*1000,
                                tickangle=-45,               # 倾斜刻度
                                tickfont=dict(size=10)       # 刻度字体大小
                            ),
                            legend=dict(title="标记", itemsizing="constant"),
                            height=460,
                            margin=dict(t=40, b=70, l=40, r=20)  # 底部留更多空间给倾斜标签
                        )

                        # 如果没有峰值定义，说明并在图例中显示"未提供高峰定义"
                        if not peak_map:
                            fig.update_layout(annotations=[dict(
                                x=0.99, y=0.01, xanchor="right", yanchor="bottom",
                                text="未检测到 14_hourly_by_peak_traffic_stats.parquet（未标记高峰）",
                                showarrow=False, font=dict(size=10, color="#666")
                            )])

                        st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"处理 hourly 数据失败: {e}")
    else:
        st.info(f"未找到文件: {p7}")



    # --- hourly error 折线图（来自 16_hourly_error_stats.parquet），并标记 14_hourly_by_peak_traffic_stats 的高峰 ---
    p8 = base / "16_hourly_error_stats.parquet"
    if p8.exists():
        try:
            dfe = pd.read_parquet(p8)
            st.subheader("每小时错误数（16_hourly_error_stats和14_hourly_by_peak_traffic_stats）")

            # 识别列名：date, hour, error_count
            date_col = next((c for c in ("date", "day", "dt", "timestamp", "ts") if c in dfe.columns), None)
            hour_col = next((c for c in ("hour", "hr", "h") if c in dfe.columns), None)
            err_col = next((c for c in ("error_count", "errors", "count", "err") if c in dfe.columns), None)

            if date_col is None or hour_col is None or err_col is None:
                st.info("`16_hourly_error_stats.parquet` 未包含可识别的 `date` / `hour` / `error_count` 列。")
            else:
                # 处理 date（取 YYYY-MM-DD）与 hour 合成时间戳
                s_date = dfe[date_col].astype(str).str.slice(0, 10)
                day_ts = pd.to_datetime(s_date, format="%Y-%m-%d", errors="coerce")
                hr = pd.to_numeric(dfe[hour_col], errors="coerce").fillna(0).astype(int).clip(0, 23)
                dfe["_ts"] = day_ts + pd.to_timedelta(hr, unit="h")
                dfe[err_col] = pd.to_numeric(dfe[err_col], errors="coerce").fillna(0)
                dfe = dfe.dropna(subset=["_ts"])
                if dfe.empty:
                    st.info("解析后无可用错误数据，无法绘图。")
                else:
                    # 按小时聚合 error_count（若已按小时则等于自身）
                    hourly_err = dfe.set_index("_ts").resample("h")[err_col].sum().reset_index()

                    # 读取高峰定义并按小时映射 is_peak
                    p_peak = base / "14_hourly_by_peak_traffic_stats.parquet"
                    peak_map = {}
                    if p_peak.exists():
                        try:
                            df_peak = pd.read_parquet(p_peak)
                            if "hour" in df_peak.columns and "is_peak" in df_peak.columns:
                                df_peak["hour"] = pd.to_numeric(df_peak["hour"], errors="coerce").fillna(-1).astype(int)
                                df_peak["is_peak"] = df_peak["is_peak"].astype(bool)
                                peak_map = dict(zip(df_peak["hour"].tolist(), df_peak["is_peak"].tolist()))
                        except Exception:
                            peak_map = {}

                    hourly_err["_hour"] = hourly_err["_ts"].dt.hour
                    hourly_err["is_peak"] = hourly_err["_hour"].map(lambda h: bool(peak_map.get(int(h), False)))

                    # 绘图：柱状图 + 高峰/低峰颜色区分
                    import plotly.express as px
                    color_peak = "#FF5DA2"
                    color_off = "#4D96FF"
                    # 使用 color 字段直接区分高峰/非高峰
                    hourly_err["peak_label"] = hourly_err["is_peak"].map({True: "高峰", False: "非高峰"})
                    fig = px.bar(hourly_err, x="_ts", y=err_col, color="peak_label",
                                color_discrete_map={"高峰": color_peak, "非高峰": color_off},
                                title="每小时错误数（高峰标记）",
                                labels={"_ts": "时间（按小时）", err_col: "错误数"},
                                template="plotly_white")
                    fig.update_traces(marker_line_width=0)  # 去除柱边线，显得更扁平现代
                    # X 轴每天一个主刻度并倾斜标签
                    start_ts = hourly_err["_ts"].min()
                    fig.update_layout(
                        xaxis=dict(
                            rangeslider=dict(visible=True),
                            tickformat="%Y-%m-%d\n%H:00",
                            tick0=start_ts,
                            dtick=24*60*60*1000,
                            tickangle=-45,
                            tickfont=dict(size=10)
                        ),
                        legend=dict(title="标记"),
                        height=460,
                        margin=dict(t=40, b=70, l=40, r=20)
                    )

                    if not peak_map:
                        fig.update_layout(annotations=[dict(
                            x=0.99, y=0.01, xanchor="right", yanchor="bottom",
                            text="未检测到 14_hourly_by_peak_traffic_stats.parquet（未标记高峰）",
                            showarrow=False, font=dict(size=10, color="#666")
                        )])

                    st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"读取或处理 {p8.name} 失败: {e}")
    else:
        st.info(f"未找到文件: {p8}")