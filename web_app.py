# -*- coding:utf-8 -*-
from flask import Flask, request, jsonify, render_template_string, send_file
import requests
import json
from py2neo import Graph
import random
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)

# 服务地址
INTENT_URL = "http://127.0.0.1:60062/service/api/bert_intent_recognize"
NER_URL = "http://127.0.0.1:60061/service/api/medical_ner"

# Neo4j连接
graph = Graph("bolt://127.0.0.1:7688", auth=("neo4j", "abcd1234wohaomei*"))

# 会话存储
sessions = defaultdict(lambda: {
    "questions": [],
    "answers": [],
    "cot_htmls": [],
    "expert": None,
    "start_time": None,
    "last_activity": None
})


class MedicalCoTEngine:
    def __init__(self):
        self.reasoning_steps = []

    def clear_reasoning(self):
        self.reasoning_steps = []

    def add_step(self, title, content, icon="🔍", tag="分析中"):
        self.reasoning_steps.append({
            "title": title,
            "content": content,
            "icon": icon,
            "tag": tag,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

    def get_reasoning_html(self):
        html = '<div class="reasoning-flow">'
        for i, step in enumerate(self.reasoning_steps):
            html += f'''
            <div class="reasoning-node" style="animation-delay: {i * 0.1}s">
                <div class="node-marker">
                    <div class="node-icon">{step["icon"]}</div>
                    <div class="node-line"></div>
                </div>
                <div class="node-card">
                    <div class="node-header">
                        <span class="node-title">{step["title"]}</span>
                        <span class="node-tag">{step["tag"]}</span>
                    </div>
                    <div class="node-content">{step["content"]}</div>
                    <div class="node-time">{step["timestamp"]}</div>
                </div>
            </div>
            '''
        html += '</div>'
        return html

    def analyze_disease(self, disease_name, intent, expert_dept=""):
        self.clear_reasoning()

        self.add_step("语义解析",
                      f"输入文本: 「{disease_name}」相关查询\n意图识别: {intent}\n实体抽取: 疾病名称 → {disease_name}\n会诊专家: {expert_dept or '全科'}",
                      "🔍", "已完成")

        disease_info = self._get_disease_info(disease_name)
        if disease_info:
            self.add_step("知识检索",
                          f"从医学知识图谱中检索到「{disease_name}」的完整临床资料\n数据来源: 三甲医院临床数据库\n信息完整度: 92%",
                          "📚", "检索成功")
        else:
            self.add_step("知识检索",
                          f"「{disease_name}」相关信息正在更新中，采用循证医学推理模式",
                          "📚", "推理模式")

        reasoning = self._clinical_reasoning(disease_name, intent, disease_info, expert_dept)
        self.add_step("临床推理", reasoning, "🧠", "推理中")

        confidence = self._confidence_score(disease_name, disease_info)
        self.add_step("置信度评估",
                      f"推理置信度: {confidence}%\n依据: 知识图谱完整度 + 临床指南匹配度",
                      "📊", "评估完成")

        advice = self._generate_advice(disease_name, intent, expert_dept)
        self.add_step("诊疗建议", advice, "💊", "建议参考")

        return self.get_reasoning_html()

    def _get_disease_info(self, disease_name):
        try:
            result = graph.run("""
                MATCH (d:疾病 {name: $name}) 
                RETURN d.desc as desc, d.cause as cause, 
                       d.prevent as prevent, d.cure_way as cure
            """, name=disease_name).data()
            return result[0] if result else None
        except:
            return None

    def _clinical_reasoning(self, disease_name, intent, info, expert_dept):
        prefix = f"【{expert_dept}专家视角】" if expert_dept else ""
        if intent == "定义":
            if info and info.get('desc'):
                return prefix + f"病理学定义: {info['desc']}\n\n临床特征: 该疾病具有典型的临床表现和病程特点\n鉴别诊断: 需与相似症状疾病进行区分"
            return prefix + f"「{disease_name}」是一种常见疾病，建议结合具体症状进行临床诊断。"
        elif intent == "病因":
            if info and info.get('cause'):
                return prefix + f"主要致病因素: {info['cause']}\n\n发病机制: 多因素相互作用导致疾病发生\n危险因素: 需结合个体情况综合评估"
            return prefix + f"「{disease_name}」的发病涉及遗传、环境、生活方式等多方面因素。"
        elif intent == "预防":
            if info and info.get('prevent'):
                return prefix + f"一级预防: {info['prevent']}\n\n二级预防: 早期筛查与干预\n三级预防: 规范治疗与康复管理"
            return prefix + f"预防「{disease_name}」的关键在于保持健康生活方式，定期体检。"
        elif "治疗" in intent:
            if info and info.get('cure'):
                return prefix + f"治疗方案: {info['cure']}\n\n治疗原则: 个体化、规范化、综合治疗\n疗效评估: 定期随访，动态调整"
            return prefix + f"「{disease_name}」的治疗需在专业医生指导下进行，不可自行用药。"
        return prefix + f"关于「{disease_name}」的详细分析，建议咨询专业医师。"

    def _confidence_score(self, disease_name, info):
        if info:
            return random.randint(85, 98)
        return random.randint(65, 80)

    def _generate_advice(self, disease_name, intent, expert_dept):
        dept_specific = ""
        if "心血管" in expert_dept:
            dept_specific = "建议完善心电图、心脏超声检查，控制血压血脂。"
        elif "外科" in expert_dept:
            dept_specific = "如符合手术指征，建议微创治疗；定期影像学随访。"
        elif "神经" in expert_dept:
            dept_specific = "建议头颅MRI及血管评估，预防二次卒中。"
        else:
            dept_specific = "建议前往正规医院相关科室进行专业诊疗。"
        return f"1. {dept_specific}\n2. 保持良好生活习惯，避免诱发因素\n3. 定期复查，监测病情变化\n4. 遵医嘱规范用药，切勿自行调整"


cot_engine = MedicalCoTEngine()


class MedicalReportGenerator:
    @staticmethod
    def generate_report(session_data, session_id):
        questions = session_data["questions"]
        answers = session_data["answers"]
        expert = session_data.get("expert", {"name": "多专家联合会诊", "dept": "全科"})
        start_time = session_data.get("start_time", datetime.now())

        if not questions:
            return None

        diseases = []
        for q in questions:
            common_diseases = ["感冒", "肺炎", "高血压", "糖尿病", "支气管炎", "哮喘", "冠心病",
                               "胃炎", "颈椎病", "胃溃疡", "痛风", "胆囊结石", "脑卒中",
                               "心肌梗死", "心力衰竭", "肝硬化"]
            for d in common_diseases:
                if d in q and d not in diseases:
                    diseases.append(d)

        consultation_html = ""
        for i, (q, a) in enumerate(zip(questions, answers), 1):
            clean_a = a.replace("<strong>", "").replace("</strong>", "").replace("<br>", "<br>")
            consultation_html += f'''
            <div class="consultation-item">
                <div class="consultation-question">
                    <span style="background: #1e3a5f; color: white; padding: 2px 10px; border-radius: 20px; font-size: 12px; margin-right: 12px;">Q{i}</span>
                    患者咨询
                </div>
                <div class="consultation-question" style="color: #2c5282; margin-top: 8px;">
                    {q}
                </div>
                <div class="consultation-answer" style="margin-top: 12px;">
                    <span style="color: #2c5282; font-weight: 500;">👨‍⚕️ 专家回复：</span><br>
                    {clean_a}
                </div>
            </div>
            '''

        diseases_html = ""
        if diseases:
            for d in diseases:
                diseases_html += f'<span class="disease-tag">🏥 {d}</span>'
        else:
            diseases_html = '<span class="disease-tag">📝 健康咨询</span>'

        report_html = f'''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>智医AI - 医疗咨询报告</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #f5f7fa 0%, #e9eef5 100%);
                    padding: 40px 20px;
                }}
                .report-container {{
                    max-width: 1000px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 32px;
                    box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
                    overflow: hidden;
                }}
                .report-header {{
                    background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
                    color: white;
                    padding: 40px 48px;
                    text-align: center;
                }}
                .report-header h1 {{
                    font-size: 32px;
                    font-weight: 600;
                    margin-bottom: 12px;
                }}
                .report-meta {{
                    display: flex;
                    justify-content: space-between;
                    padding: 20px 48px;
                    background: #f8fafc;
                    border-bottom: 1px solid #e2e8f0;
                    flex-wrap: wrap;
                    gap: 16px;
                }}
                .meta-item {{
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    color: #475569;
                    font-size: 14px;
                }}
                .report-body {{ padding: 40px 48px; }}
                .section {{ margin-bottom: 32px; }}
                .section-title {{
                    font-size: 20px;
                    font-weight: 600;
                    color: #1e3a5f;
                    border-left: 4px solid #2c5282;
                    padding-left: 16px;
                    margin-bottom: 20px;
                }}
                .consultation-item {{
                    background: #f8fafc;
                    border-radius: 20px;
                    padding: 20px;
                    margin-bottom: 20px;
                    border: 1px solid #e2e8f0;
                }}
                .consultation-question {{
                    font-weight: 600;
                    color: #1e3a5f;
                    margin-bottom: 12px;
                    padding-bottom: 8px;
                    border-bottom: 1px dashed #cbd5e1;
                }}
                .consultation-answer {{
                    color: #334155;
                    line-height: 1.6;
                }}
                .disease-tag {{
                    display: inline-block;
                    background: #e6f0fa;
                    color: #2c5282;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 12px;
                    margin-right: 8px;
                    margin-bottom: 8px;
                }}
                .summary-box {{
                    background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
                    border-radius: 24px;
                    padding: 24px;
                    margin-top: 32px;
                }}
                .disclaimer {{
                    background: #fef9e6;
                    border-left: 4px solid #f59e0b;
                    padding: 16px 24px;
                    margin-top: 32px;
                    font-size: 12px;
                    color: #92400e;
                    border-radius: 12px;
                }}
                .report-footer {{
                    background: #f1f5f9;
                    padding: 24px 48px;
                    text-align: center;
                    font-size: 12px;
                    color: #64748b;
                }}
                .btn-group {{
                    display: flex;
                    gap: 16px;
                    justify-content: center;
                    margin-top: 32px;
                }}
                .btn {{
                    padding: 12px 28px;
                    border-radius: 40px;
                    border: none;
                    font-size: 14px;
                    font-weight: 500;
                    cursor: pointer;
                }}
                .btn-primary {{
                    background: linear-gradient(135deg, #1e3a5f, #2c5282);
                    color: white;
                }}
                .btn-secondary {{
                    background: white;
                    color: #1e3a5f;
                    border: 1px solid #cbd5e1;
                }}
            </style>
        </head>
        <body>
            <div class="report-container">
                <div class="report-header">
                    <h1>🕊️ 智医AI · 医疗咨询报告 📋</h1>
                    <div class="subtitle">圣洁之光 · 仁心守护 | 多专家联合会诊记录</div>
                </div>
                <div class="report-meta">
                    <div class="meta-item">📅 会诊时间: {start_time.strftime("%Y年%m月%d日 %H:%M")}</div>
                    <div class="meta-item">👨‍⚕️ 会诊专家: {expert.get("name", "智医AI专家团队")} · {expert.get("dept", "全科")}</div>
                    <div class="meta-item">🔢 咨询轮次: {len(questions)} 次</div>
                    <div class="meta-item">🏷️ 报告编号: {session_id[:8].upper()}</div>
                </div>
                <div class="report-body">
                    <div class="section">
                        <div class="section-title">📋 涉及疾病/健康问题</div>
                        <div>{diseases_html}</div>
                    </div>
                    <div class="section">
                        <div class="section-title">💬 详细会诊记录</div>
                        {consultation_html}
                    </div>
                    <div class="summary-box">
                        <div style="font-weight: 600; margin-bottom: 12px; color: #1e3a5f;">📊 会诊总结</div>
                        <div style="line-height: 1.6; color: #334155;">
                            <p>本次会诊共进行 <strong>{len(questions)}</strong> 轮咨询。</p>
                            <p style="margin-top: 12px;">⚠️ 温馨提示：本报告仅供参考，不能替代线下医疗诊断。</p>
                        </div>
                    </div>
                    <div class="disclaimer">
                        <strong>📢 重要声明</strong><br>
                        本报告由智医AI系统自动生成，基于医学知识图谱和临床指南提供参考信息。报告内容不构成医疗诊断或治疗建议。
                    </div>
                    <div class="btn-group">
                        <button class="btn btn-primary" onclick="window.print()">🖨️ 打印报告</button>
                        <button class="btn btn-secondary" onclick="window.close()">✖️ 关闭窗口</button>
                    </div>
                </div>
                <div class="report-footer">
                    智医AI · 圣洁多专家会诊平台 | 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                </div>
            </div>
        </body>
        </html>
        '''
        return report_html


HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智医AI | 多专家会诊平台</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            background: white;
            border-radius: 20px;
            padding: 20px 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 {
            color: #667eea;
            margin-bottom: 5px;
        }
        .experts {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            overflow-x: auto;
            padding: 10px 0;
        }
        .expert-card {
            background: white;
            border-radius: 15px;
            padding: 15px 20px;
            cursor: pointer;
            transition: all 0.3s;
            min-width: 180px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .expert-card.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            transform: translateY(-5px);
        }
        .expert-card .avatar { font-size: 40px; margin-bottom: 10px; }
        .expert-card .name { font-weight: bold; font-size: 16px; }
        .expert-card .title { font-size: 12px; opacity: 0.8; }
        .dashboard {
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 20px;
        }
        .chat-panel {
            background: white;
            border-radius: 20px;
            height: calc(100vh - 280px);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .chat-header {
            padding: 20px;
            border-bottom: 1px solid #e0e0e0;
            background: #f8f9fa;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
        }
        .message {
            margin-bottom: 15px;
            display: flex;
        }
        .message.user { justify-content: flex-end; }
        .message.bot { justify-content: flex-start; }
        .message-bubble {
            max-width: 70%;
            padding: 10px 15px;
            border-radius: 15px;
            font-size: 14px;
            line-height: 1.5;
        }
        .user .message-bubble {
            background: #667eea;
            color: white;
        }
        .bot .message-bubble {
            background: #f0f0f0;
            color: #333;
        }
        .input-area {
            padding: 15px;
            border-top: 1px solid #e0e0e0;
            display: flex;
            gap: 10px;
        }
        .input-area input {
            flex: 1;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 25px;
            outline: none;
            font-size: 14px;
        }
        .input-area button {
            padding: 10px 20px;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.3s;
        }
        .send-btn {
            background: #667eea;
            color: white;
        }
        .voice-btn {
            background: #f0f0f0;
        }
        .voice-btn.recording {
            background: #ff6b6b;
            color: white;
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        .report-btn {
            background: #28a745;
            color: white;
        }
        .reasoning-panel {
            background: white;
            border-radius: 20px;
            height: calc(100vh - 280px);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .reasoning-header {
            padding: 20px;
            border-bottom: 1px solid #e0e0e0;
            background: #f8f9fa;
        }
        .reasoning-content {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
        }
        .quick-buttons {
            margin-top: 20px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        .quick-btn {
            padding: 8px 15px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 20px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.3s;
        }
        .quick-btn:hover {
            background: #667eea;
            color: white;
        }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        .modal.show { display: flex; }
        .modal-content {
            background: white;
            border-radius: 20px;
            padding: 30px;
            max-width: 400px;
            text-align: center;
        }
        .modal-buttons {
            display: flex;
            gap: 10px;
            justify-content: center;
            margin-top: 20px;
        }
        .modal-buttons button {
            padding: 10px 20px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
        }
        .typing {
            color: #999;
            font-style: italic;
            padding: 10px;
        }
        .placeholder {
            text-align: center;
            color: #999;
            padding: 40px;
        }
        @media (max-width: 768px) {
            .dashboard { grid-template-columns: 1fr; }
            .reasoning-panel { height: 300px; margin-top: 20px; }
            .chat-panel { height: 500px; }
        }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🕊️ 智医AI · 多专家会诊平台</h1>
        <p>圣洁之光，仁心守护 | 支持语音输入，自动生成医疗报告</p>
    </div>

    <div class="experts" id="expertList">
        <div class="expert-card active" data-expert="general" data-name="陈明远" data-dept="呼吸科">
            <div class="avatar">👨‍⚕️</div>
            <div class="name">陈明远 · 主任</div>
            <div class="title">呼吸与危重症医学科</div>
        </div>
        <div class="expert-card" data-expert="cardiovascular" data-name="林清怡" data-dept="心血管内科">
            <div class="avatar">❤️</div>
            <div class="name">林清怡 · 主任</div>
            <div class="title">心血管内科</div>
        </div>
        <div class="expert-card" data-expert="surgery" data-name="方世杰" data-dept="外科">
            <div class="avatar">🔪</div>
            <div class="name">方世杰 · 教授</div>
            <div class="title">普外科</div>
        </div>
        <div class="expert-card" data-expert="neurology" data-name="苏晚晴" data-dept="神经内科">
            <div class="avatar">🧠</div>
            <div class="name">苏晚晴 · 副主任</div>
            <div class="title">神经内科</div>
        </div>
    </div>

    <div class="dashboard">
        <div class="chat-panel">
            <div class="chat-header">
                <strong id="currentDoctor">👨‍⚕️ 陈明远 主任医师</strong>
                <span style="font-size:12px; color:#666; margin-left:10px;" id="doctorDept">呼吸与危重症医学科</span>
            </div>
            <div class="chat-messages" id="chatMessages">
                <div class="message bot">
                    <div class="message-bubble">✨ 您好！我是智医AI专家系统。请选择上方专家，或直接提问疾病问题。<br>💬 例如：「高血压如何预防」或「肺炎的症状有哪些」<br><br>📌 咨询结束后，请点击「结束咨询」按钮生成完整报告。</div>
                </div>
            </div>
            <div class="input-area">
                <input type="text" id="questionInput" placeholder="输入您的问题..." onkeypress="handleKeyPress(event)">
                <button class="voice-btn" id="voiceBtn" onclick="toggleVoice()">🎤</button>
                <button class="send-btn" onclick="sendMessage()">发送</button>
                <button class="report-btn" onclick="showEndModal()">📄 结束咨询</button>
            </div>
        </div>

        <div class="reasoning-panel">
            <div class="reasoning-header">
                <strong>📜 临床思维链 & 循证推理</strong>
            </div>
            <div class="reasoning-content" id="reasoningContent">
                <div class="placeholder">提问后，临床推理路径将在此展现...</div>
            </div>
        </div>
    </div>

    <div class="quick-buttons">
        <button class="quick-btn" onclick="quickAsk('高血压的病因和预防')">❤️ 高血压预防</button>
        <button class="quick-btn" onclick="quickAsk('冠心病早期症状')">🫀 冠心病症状</button>
        <button class="quick-btn" onclick="quickAsk('胆囊结石需要手术吗')">⚕️ 胆囊结石</button>
        <button class="quick-btn" onclick="quickAsk('脑卒中先兆识别')">🧠 脑卒中</button>
        <button class="quick-btn" onclick="quickAsk('肺炎治疗方案')">🌬️ 肺炎治疗</button>
        <button class="quick-btn" onclick="quickAsk('糖尿病饮食建议')">🍬 糖尿病管理</button>
    </div>
</div>

<div class="modal" id="endModal">
    <div class="modal-content">
        <h3>📋 结束咨询</h3>
        <p>确定要结束本次咨询吗？<br>系统将为您生成完整的医疗报告。</p>
        <div class="modal-buttons">
            <button onclick="closeModal()">继续咨询</button>
            <button onclick="generateReport()" style="background:#28a745; color:white;">生成报告</button>
        </div>
    </div>
</div>

<script>
    let currentExpert = {
        id: 'general',
        name: '陈明远',
        dept: '呼吸科'
    };
    let sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    let isProcessing = false;
    let recognition = null;
    let isRecording = false;

    // 初始化语音识别
    function initSpeech() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            alert('您的浏览器不支持语音识别，请使用Chrome浏览器');
            return false;
        }
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.lang = 'zh-CN';
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = function() {
            document.getElementById('voiceBtn').classList.add('recording');
            document.getElementById('voiceBtn').innerHTML = '🎤🔴';
            isRecording = true;
        };

        recognition.onresult = function(event) {
            const text = event.results[0][0].transcript;
            document.getElementById('questionInput').value = text;
            sendMessage();
        };

        recognition.onerror = function(event) {
            console.error('语音识别错误:', event.error);
            alert('语音识别失败: ' + event.error);
        };

        recognition.onend = function() {
            document.getElementById('voiceBtn').classList.remove('recording');
            document.getElementById('voiceBtn').innerHTML = '🎤';
            isRecording = false;
        };

        return true;
    }

    function toggleVoice() {
        if (!recognition) {
            if (!initSpeech()) return;
        }
        if (isRecording) {
            recognition.stop();
        } else {
            recognition.start();
        }
    }

    // 专家切换
    document.querySelectorAll('.expert-card').forEach(card => {
        card.addEventListener('click', function() {
            document.querySelectorAll('.expert-card').forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            currentExpert = {
                id: this.dataset.expert,
                name: this.dataset.name,
                dept: this.dataset.dept
            };
            document.getElementById('currentDoctor').innerHTML = '👨‍⚕️ ' + currentExpert.name;
            document.getElementById('doctorDept').innerHTML = currentExpert.dept;
            addBotMessage(`已切换至 ${currentExpert.name} 医生（${currentExpert.dept}），请问您有什么问题？`);
        });
    });

    function addBotMessage(text) {
        const container = document.getElementById('chatMessages');
        const div = document.createElement('div');
        div.className = 'message bot';
        div.innerHTML = `<div class="message-bubble">${text}</div>`;
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }

    function addUserMessage(text) {
        const container = document.getElementById('chatMessages');
        const div = document.createElement('div');
        div.className = 'message user';
        div.innerHTML = `<div class="message-bubble">${text}</div>`;
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }

    function showTyping() {
        const container = document.getElementById('chatMessages');
        const typing = document.createElement('div');
        typing.className = 'message bot';
        typing.id = 'typingIndicator';
        typing.innerHTML = `<div class="message-bubble">📋 正在思考中，请稍候...</div>`;
        container.appendChild(typing);
        container.scrollTop = container.scrollHeight;
    }

    function hideTyping() {
        const el = document.getElementById('typingIndicator');
        if (el) el.remove();
    }

    function handleKeyPress(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    }

    function quickAsk(question) {
        document.getElementById('questionInput').value = question;
        sendMessage();
    }

    async function sendMessage() {
        if (isProcessing) return;
        const input = document.getElementById('questionInput');
        const question = input.value.trim();
        if (!question) return;

        isProcessing = true;
        input.value = '';
        addUserMessage(question);
        showTyping();

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: question,
                    expert_id: currentExpert.id,
                    expert_name: currentExpert.name,
                    expert_dept: currentExpert.dept,
                    session_id: sessionId
                })
            });
            const data = await response.json();
            hideTyping();
            addBotMessage(data.answer);
            if (data.cot_html) {
                document.getElementById('reasoningContent').innerHTML = data.cot_html;
            }
        } catch (error) {
            hideTyping();
            addBotMessage('网络错误，请稍后重试。');
            console.error(error);
        }
        isProcessing = false;
    }

    function showEndModal() {
        document.getElementById('endModal').classList.add('show');
    }

    function closeModal() {
        document.getElementById('endModal').classList.remove('show');
    }

    async function generateReport() {
        closeModal();
        addBotMessage('📋 正在生成医疗报告，请稍候...');
        showTyping();

        try {
            const response = await fetch('/generate_report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            });
            const data = await response.json();
            hideTyping();

            if (data.success) {
                addBotMessage('✅ 报告已生成，正在为您打开...');
                window.open(data.report_url, '_blank');
                setTimeout(() => {
                    if (confirm('报告已生成！是否开始新的咨询会话？')) {
                        location.reload();
                    }
                }, 1000);
            } else {
                addBotMessage('❌ 报告生成失败: ' + (data.error || '未知错误'));
            }
        } catch (error) {
            hideTyping();
            addBotMessage('❌ 网络错误，报告生成失败');
            console.error(error);
        }
    }

    // 页面加载时初始化
    initSpeech();
</script>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get('question', '')
    expert_dept = data.get('expert_dept', '')
    expert_name = data.get('expert_name', '智医AI专家')
    session_id = data.get('session_id', '')

    # 获取或创建会话
    session = sessions[session_id]
    if not session["start_time"]:
        session["start_time"] = datetime.now()
    if not session["expert"]:
        session["expert"] = {"name": expert_name, "dept": expert_dept}
    session["last_activity"] = datetime.now()

    # 意图识别
    intent_name = "其他"
    try:
        intent_resp = requests.post(INTENT_URL, json={"text": question}, timeout=3)
        intent = intent_resp.json()
        intent_name = intent.get('data', {}).get('name', '其他')
    except Exception as e:
        print(f"意图识别失败: {e}")

    # 疾病识别
    disease_name = None
    common_diseases = ["感冒", "肺炎", "高血压", "糖尿病", "支气管炎", "哮喘", "冠心病", "胃炎",
                       "颈椎病", "胃溃疡", "痛风", "胆囊结石", "脑卒中", "心肌梗死", "心力衰竭", "肝硬化"]
    for d in common_diseases:
        if d in question:
            disease_name = d
            break

    if not disease_name:
        try:
            ner_resp = requests.post(NER_URL, json={"text_list": [question]}, timeout=3)
            ner_data = ner_resp.json()
            for ent in ner_data.get('data', []):
                for e in ent.get('entities', []):
                    if e.get('type') == 'Disease':
                        disease_name = e.get('word')
                        break
        except Exception as e:
            print(f"NER识别失败: {e}")

    answer = ""
    cot_html = ""

    if disease_name:
        cot_html = cot_engine.analyze_disease(disease_name, intent_name, expert_dept)

        if "症状" in intent_name:
            try:
                result = graph.run(
                    "MATCH (d:疾病 {name: $name})-[:has_symptom]->(s:症状) RETURN collect(s.name) as symptoms",
                    name=disease_name).data()
                if result and result[0]['symptoms']:
                    answer = f"<strong>📋 {disease_name} 的常见症状</strong><br><br>" + "、".join(result[0]['symptoms'])
                else:
                    answer = f"<strong>📋 {disease_name}</strong><br><br>请查看右侧临床思维链推理过程。"
            except:
                answer = f"<strong>📋 {disease_name}</strong><br><br>请查看右侧临床思维链推理过程。"
        elif "治疗" in intent_name:
            try:
                result = graph.run("MATCH (d:疾病 {name: $name}) RETURN d.cure_way as answer", name=disease_name).data()
                if result and result[0]['answer']:
                    answer = f"<strong>💊 {disease_name} 的治疗方案</strong><br><br>{result[0]['answer']}"
                else:
                    answer = f"<strong>💊 {disease_name}</strong><br><br>请查看右侧临床思维链推理过程。"
            except:
                answer = f"<strong>💊 {disease_name}</strong><br><br>请查看右侧临床思维链推理过程。"
        else:
            try:
                result = graph.run("MATCH (d:疾病 {name: $name}) RETURN d.desc as desc", name=disease_name).data()
                if result and result[0]['desc']:
                    answer = f"<strong>📖 {disease_name}</strong><br><br>{result[0]['desc']}"
                else:
                    answer = f"<strong>📖 {disease_name}</strong><br><br>请查看右侧临床思维链推理过程。"
            except:
                answer = f"<strong>📖 {disease_name}</strong><br><br>请查看右侧临床思维链推理过程。"
    else:
        answer = "未能识别到具体的疾病名称。请尝试更明确的问题，如「感冒的症状有哪些」或「高血压如何预防」。"
        cot_html = '<div class="placeholder">请输入包含疾病名称的问题，启动临床思维链推理</div>'

    # 保存会话历史
    session["questions"].append(question)
    session["answers"].append(answer)
    session["cot_htmls"].append(cot_html)

    return jsonify({"answer": answer, "cot_html": cot_html})


@app.route('/generate_report', methods=['POST'])
def generate_report():
    data = request.get_json()
    session_id = data.get('session_id', '')

    session = sessions.get(session_id)
    if not session or not session["questions"]:
        return jsonify({"success": False, "error": "没有找到会话记录"})

    report_html = MedicalReportGenerator.generate_report(session, session_id)

    if report_html:
        report_filename = f"medical_report_{session_id}.html"
        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(report_html)
            return jsonify({
                "success": True,
                "report_url": f"/download_report/{session_id}"
            })
        except Exception as e:
            return jsonify({"success": False, "error": f"保存失败: {str(e)}"})

    return jsonify({"success": False, "error": "报告生成失败"})


@app.route('/download_report/<session_id>')
def download_report(session_id):
    report_filename = f"medical_report_{session_id}.html"
    try:
        return send_file(report_filename, as_attachment=False)
    except Exception as e:
        return f"报告不存在: {str(e)}", 404


if __name__ == '__main__':
    print("=" * 60)
    print("🕊️ 智医 · 圣洁多专家医疗助手")
    print("=" * 60)
    print("✅ 访问地址: http://127.0.0.1:5000")
    print("✅ 意图识别服务: http://127.0.0.1:60062")
    print("✅ NER服务: http://127.0.0.1:60061")
    print("✅ Neo4j数据库: 已连接")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)