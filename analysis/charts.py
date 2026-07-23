import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

GRADE_COLORS = {
    "A级": "#2ecc71", "B级": "#3498db", "C级": "#f39c12",
    "D级": "#e67e22", "E级": "#e74c3c", "F级": "#95a5a6",
}

GRADE_ORDER = ["A级", "B级", "C级", "D级", "E级", "F级"]


def grade_pie(df):
    if "等级" not in df.columns:
        return None
    counts = df["等级"].value_counts().reindex(GRADE_ORDER).dropna()
    colors = [GRADE_COLORS.get(g, "#999") for g in counts.index]
    fig = px.pie(
        names=counts.index, values=counts.values,
        title="等级分布", color_discrete_sequence=colors,
        hole=0.4,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(height=350, margin=dict(t=50, b=20, l=20, r=20))
    return fig


def grade_bar(df):
    if "等级" not in df.columns:
        return None
    counts = df["等级"].value_counts().reindex(GRADE_ORDER).dropna()
    colors = [GRADE_COLORS.get(g, "#999") for g in counts.index]
    fig = px.bar(
        x=counts.index, y=counts.values,
        title="等级分布（柱状图）",
        labels={"x": "等级", "y": "企业数量"},
        color=counts.index, color_discrete_sequence=colors,
        text=counts.values,
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(height=350, showlegend=False, margin=dict(t=50, b=20, l=40, r=20))
    return fig


def path_bar(df):
    if "路径" not in df.columns:
        return None
    counts = df["路径"].value_counts().sort_values(ascending=True)
    fig = px.bar(
        x=counts.values, y=counts.index,
        title="路径分布",
        labels={"x": "企业数量", "y": "路径"},
        orientation="h",
        text=counts.values,
        color=counts.index,
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(height=max(300, len(counts) * 28), showlegend=False, margin=dict(t=50, b=20, l=60, r=40))
    return fig


def grade_path_heatmap(df):
    if "等级" not in df.columns or "路径" not in df.columns:
        return None
    ct = pd.crosstab(df["等级"], df["路径"])
    ct = ct.reindex(index=[g for g in GRADE_ORDER if g in ct.index])
    ct = ct.reindex(columns=sorted(ct.columns))

    fig = px.imshow(
        ct.values, x=ct.columns.tolist(), y=ct.index.tolist(),
        title="等级 × 路径 交叉热力图",
        labels=dict(x="路径", y="等级", color="企业数量"),
        color_continuous_scale="YlOrRd",
        text_auto=True,
    )
    fig.update_layout(height=max(300, len(ct) * 40), margin=dict(t=50, b=20, l=60, r=20))
    return fig


def score_boxplot(df):
    score_cols = ["外贸基础能力", "电商运营能力", "合作配合意愿", "产能承接配套"]
    available = [c for c in score_cols if c in df.columns]
    if not available:
        return None

    fig = go.Figure()
    for col in available:
        fig.add_trace(go.Box(y=df[col].dropna(), name=col))
    fig.update_layout(
        title="各评分维度分布",
        yaxis_title="得分",
        height=400,
        margin=dict(t=50, b=20, l=40, r=20),
    )
    return fig


def score_by_grade_boxplot(df):
    score_cols = ["外贸基础能力", "电商运营能力", "合作配合意愿", "产能承接配套"]
    available = [c for c in score_cols if c in df.columns]
    if not available or "等级" not in df.columns:
        return None

    fig = make_subplots(rows=2, cols=2, subplot_titles=available)
    for i, col in enumerate(available):
        row, c = divmod(i, 2)
        for grade in GRADE_ORDER:
            subset = df[df["等级"] == grade][col].dropna()
            if len(subset) > 0:
                fig.add_trace(
                    go.Box(y=subset.values, name=grade, marker_color=GRADE_COLORS.get(grade, "#999"), showlegend=(i == 0)),
                    row=row + 1, col=c + 1,
                )
    fig.update_layout(height=600, title="各维度评分 × 等级", margin=dict(t=80, b=20, l=40, r=20))
    return fig


def score_radar(df, scores_dict):
    categories = list(scores_dict.keys())
    values = list(scores_dict.values())
    max_vals = [25, 23, 35, 17][:len(categories)]
    percentages = [v / m * 100 if m > 0 else 0 for v, m in zip(values, max_vals)]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=percentages + [percentages[0]],
        theta=categories + [categories[0]],
        fill="toself",
        name="得分率(%)",
        line_color="#3498db",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        height=350, margin=dict(t=30, b=30),
    )
    return fig


def score_scatter_matrix(df):
    score_cols = ["外贸基础能力", "电商运营能力", "合作配合意愿", "产能承接配套", "总分"]
    available = [c for c in score_cols if c in df.columns]
    if len(available) < 3:
        return None

    fig = px.scatter_matrix(
        df[available].dropna(),
        dimensions=available,
        title="评分维度相关性矩阵",
        height=600,
    )
    fig.update_traces(diagonal_visible=True)
    fig.update_layout(margin=dict(t=50, b=20, l=20, r=20))
    return fig


def comparison_bar(datasets, metric, title):
    names = list(datasets.keys())
    values = []
    for name, df in datasets.items():
        if metric in df.columns:
            values.append(df[metric].mean())
        else:
            values.append(0)

    fig = px.bar(
        x=names, y=values,
        title=title,
        labels={"x": "地区", "y": metric},
        text=[f"{v:.1f}" for v in values],
        color=names,
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(height=350, showlegend=False, margin=dict(t=50, b=20, l=40, r=20))
    return fig


def comparison_grade_stacked(datasets):
    all_grades = GRADE_ORDER
    fig = go.Figure()
    for name, df in datasets.items():
        if "等级" not in df.columns:
            continue
        counts = df["等级"].value_counts().reindex(all_grades).fillna(0)
        total = counts.sum()
        pcts = counts / total * 100
        fig.add_trace(go.Bar(
            x=all_grades, y=pcts.values,
            name=name,
            text=[f"{v:.1f}%" for v in pcts.values],
            textposition="inside",
        ))
    fig.update_layout(
        barmode="group",
        title="各地区等级分布对比",
        xaxis_title="等级", yaxis_title="占比(%)",
        height=400, margin=dict(t=50, b=20, l=40, r=20),
    )
    return fig
