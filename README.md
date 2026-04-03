# -
“智医答“”是一款基于思维链推理引擎的智能语音医疗助手系统。  系统集成BERT意图识别、医疗NER实体抽取与Neo4j知识图谱，实现疾病症状、病因、预防、治疗等维度的智能问答。核心亮点包括：🎤语音输入支持、🧠思维链可视化推理、👨‍⚕️多专家会诊模式（呼吸科/心血管内科/外科/神经内科）。  经1000条真实案例测试，系统整体准确率达93.6%，平均响应时间1.2秒。用户调研显示超72%的基层用户愿意使用智能健康服务。项目响应“健康中国2030”战略，致力于为县域、乡镇及农村群体提供便捷、权威的智能健康咨询服务。
🏥 智医AI · 智能语音医疗助手
运行手册
📖 项目简介
智医AI是一款基于思维链推理引擎的智能语音医疗助手系统。系统集成了意图识别、医疗命名实体识别(NER)、知识图谱检索和临床推理功能，支持语音输入和文字问诊，提供多专家会诊模式。

核心功能
🎤 语音输入：支持中文语音识别，自动转换为文本

🧠 思维链推理：展示AI从语义解析到诊疗建议的完整推理过程

👨‍⚕️ 多专家会诊：呼吸科、心血管内科、外科、神经内科专家切换

📚 知识图谱检索：基于Neo4j图数据库的医疗知识检索

💬 智能问答：支持疾病症状、病因、预防、治疗等多维度查询

🖥️ 系统环境要求
组件	版本要求
Python	3.8 ~ 3.11
Neo4j	5.x (社区版)
Java	17 (Neo4j依赖)
浏览器	Chrome / Edge (支持语音识别)
操作系统	Windows / macOS / Linux
📦 依赖服务
本项目依赖以下三个核心服务：

服务	端口	说明
意图识别服务	60062	BERT意图识别模型
NER服务	60061	医疗命名实体识别
Neo4j图数据库	7688	医学知识图谱存储
🚀 快速开始
第一步：安装Python依赖
bash
pip install flask requests py2neo
第二步：启动Neo4j数据库
Windows (以管理员身份运行PowerShell)
powershell
cd E:\neo4j\neo4j-community-5.26.8\bin
.\neo4j install-service    # 首次需要安装服务
.\neo4j start
控制台模式（无需安装服务）
powershell
cd E:\neo4j\neo4j-community-5.26.8\bin
.\neo4j console
验证连接
浏览器访问 http://localhost:7474

用户名：neo4j

密码：abcd1234wohaomei*

第三步：启动AI服务
确保意图识别和NER服务已启动：

bash
# 意图识别服务 (端口60062)
python intent_service.py

# NER服务 (端口60061)
python ner_service.py
第四步：运行主程序
bash
python app.py
看到以下输出表示启动成功：

text
============================================================


🕊️ 智医 · 圣洁多专家医疗助手
============================================================
✅ 意图识别服务: http://127.0.0.1:60062
✅ NER服务: http://127.0.0.1:60061
✅ Neo4j数据库: 已连接
✅ 多专家会诊模式: 呼吸科 / 心血管内科 / 外科 / 神经内科
============================================================
🌐 访问地址: http://127.0.0.1:5000
📢 语音识别说明: 首次使用需点击麦克风并允许权限
============================================================
第五步：访问系统
打开浏览器访问：http://127.0.0.1:5000

🎤 语音输入配置
首次使用麦克风权限
Chrome/Edge浏览器：

访问 http://127.0.0.1:5000

点击页面上的 🎤 麦克风按钮

浏览器弹出权限请求，点击 "允许"

开始说话，系统自动识别并发送

手动设置：

点击地址栏左侧的锁图标 🔒

找到"麦克风"选项

选择"允许"

刷新页面

📁 项目文件结构
text
medical_ai/
├── app.py                    # 主程序文件
├── intent_service.py         # 意图识别服务（需自行部署）
├── ner_service.py            # NER服务（需自行部署）
├── requirements.txt          # Python依赖
├── start_neo4j.bat          # Neo4j启动脚本
└── README.md                 # 说明文档
🔧 配置说明
Neo4j连接配置
python
graph = Graph("bolt://127.0.0.1:7688", auth=("neo4j", "abcd1234wohaomei*"))
服务地址配置
python
INTENT_URL = "http://127.0.0.1:60062/service/api/bert_intent_recognize"
NER_URL = "http://127.0.0.1:60061/service/api/medical_ner"
端口配置
python
app.run(host='0.0.0.0', port=5000, debug=False)
❓ 常见问题
1. Neo4j连接失败
错误: Connection refused
解决:

powershell
cd E:\neo4j\neo4j-community-5.26.8\bin
.\neo4j start

2. 服务启动失败
错误: Neo4j service is not installed
解决: 以管理员身份运行PowerShell

powershell
.\neo4j install-service
.\neo4j start

3. 语音识别失败
原因: 浏览器未授权麦克风权限
解决:

点击地址栏麦克风图标，选择"允许"

使用Chrome或Edge浏览器

确保使用 127.0.0.1 而非 localhost


4. 意图识别服务连接失败
错误: requests.exceptions.ConnectionError
解决: 确保意图识别服务已启动在60062端口

5. Java版本问题
检查: java -version 需要Java 17
下载: https://adoptium.net/

📝 使用示例
文字问诊
text
输入: 感冒的症状有哪些
输出: 发热、咳嗽、鼻塞、流涕、咽痛...
语音问诊
点击🎤按钮

说："高血压怎么预防"

自动识别并回答

专家切换
点击上方专家卡片切换科室

呼吸科 → 肺炎、支气管炎

心血管内科 → 高血压、冠心病

外科 → 胆囊结石、阑尾炎

神经内科 → 脑卒中、头痛

🛑 停止服务
停止Neo4j
powershell
cd E:\neo4j\neo4j-community-5.26.8\bin
.\neo4j stop
停止Flask应用
按 Ctrl + C 终止

📞 技术支持
如遇到其他问题，请检查：

所有服务是否正常运行

端口是否被占用

防火墙是否阻止连接

Neo4j密码是否正确

📄 版本信息
组件	版本
Flask	2.x
py2neo	2021.2.3
Neo4j	5.26.8
Python	3.8+
祝您使用愉快！ 🕊️
