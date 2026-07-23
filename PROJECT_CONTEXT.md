# 跨境电商智能分析Agent - 项目说明

## 项目概述
Streamlit本地Web工具，支持4种模式：计算得分等级、划分路径、得分+路径、已有数据分析。
无API依赖，零成本运行。

## 启动方式
- 双击 `启动分析工具.bat` 或 `安装并启动.bat`
- 或命令行: `streamlit run app.py --server.headless true --server.port 8501`
- 浏览器访问 http://localhost:8501

## 依赖
streamlit pandas openpyxl python-docx plotly matplotlib

## 项目结构
```
D:\smart_agent\
├── app.py                          # Streamlit主入口，4种模式选择
├── config.py                       # 常量：GRADE_ORDER, PATH_NAMES, SCORE_DIMENSIONS
├── 启动分析工具.bat                  # 一键启动
├── 安装并启动.bat                    # 一键安装依赖+启动
│
├── core/
│   ├── column_detector.py          # 已有数据的列智能识别（"已有得分等级和路径"模式用）
│   ├── questionnaire_detector.py   # 原始问卷字段识别+compute_scores_for_dataframe()
│   ├── path_calculator.py          # detect_path_columns() + 主干/子路径计算
│   └── data_loader.py              # handle_file_upload() + standardize_data()
│
├── utils/
│   ├── normalize.py                # normalize(), normalize_yes_no/number/sku/moq/percent/count
│   ├── scoring_rules.py            # 16个评分字段FIELD_MAPPING + 7个score_*函数 + calculate_scores()
│   └── path_rules.py               # explain_path()原始规则说明
│
├── analysis/
│   ├── charts.py                   # Plotly图表函数
│   ├── overview.py                 # 数据总览（指标卡+图表+可搜索数据表）
│   ├── enterprise.py               # 企业查询（搜索+筛选+详情卡片+雷达图+排名）
│   └── comparison.py               # 跨地区横向对比
│
├── export/
│   └── report_generator.py         # Word报告（宋体+Times New Roman）
│
└── output/                         # 报告输出目录
```

## 关键设计决策

### handle_file_upload() 的 mode 参数
- "划分路径"/"得分等级+路径"/"计算得分和等级" → 直接返回原始df，不做列标准化
- "已有得分等级和路径" → 调用column_detector.detect_columns() + standardize_data()
- 原因：column_detector会把"想要做跨境电商的方向?"错误匹配成ecommerce_ops，standardize_data会丢掉客户画像等列

### 评分函数关键点
- score_export_amount: 用regex提取范围下界（如"10-49.9万美元"→"10"），再replace万→0000
- score_ecommerce_sales: 用正则`(^|[^0-9])0([^0-9]|$)`匹配独立的"0"，避免"10万美元"中的0被误判
- normalize(): FULLWIDTH_MAP全角转半角，CONNECTOR_MAP转连接符，去逗号去斜杠

### 路径检测关键点
- path_calculator.py的PATH_DIRECTION_FIELDS有8个字段的关键词
- determine_main_path()用方向意图+客户画像判断主干路径A-F
- determine_sub_path()根据SKU/MOQ/研发/产品类型等判断子路径
- sub_A: normalize_sku()判断<=10且研发+产品图都是yes→A1，否则A2
- sub_B: normalize_moq()<5000→B1，否则B2

### 字体设置（report_generator.py）
- 汉字: 宋体 (SimSun)
- 英文: Times New Roman
- 通过docx.oxml.ns.qn设置w:rFonts的w:eastAsia属性
- 标题22pt，一级标题14pt，正文10.5pt，表头10pt，表格内容9pt

## 规则文档
- `E:\跨境电商暑期项目-出海路径\企业出海路径及划分规则0720.docx` — 路径规则
- `E:\跨境电商暑期项目-出海路径\企业等级评分机制（更新版）.docx` — 评分规则
- `E:\跨境电商暑期项目-出海路径\第一二阶段电子问卷(修改版)0720.docx` — 问卷参考

## 测试数据
- `E:\跨境电商暑期项目-出海路径\沧州\沧州市第一阶段等级结果及第二阶段路径结果-新.xlsx` — 323行，已有得分（Mode 4）
- `E:\跨境电商暑期项目-出海路径\大名\大名重点制造业企业跨境路径表.xlsx` — 13行，第二阶段问卷（Mode 2划分路径）

## 新对话续接提示
如果需要在新对话中继续开发，把此文件内容发给AI即可。
