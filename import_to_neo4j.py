from py2neo import Graph
import time

print("=" * 60)
print("医疗知识图谱数据导入工具")
print("=" * 60)

# 连接Neo4j
# 注意：你的Neo4j HTTP端口是7475，Bolt端口是7688
graph = Graph("bolt://127.0.0.1:7688", auth=("neo4j", "abcd1234wohaomei*"))

# 测试连接
try:
    result = graph.run("RETURN 1 as test").data()
    print("✅ Neo4j连接成功！")
except Exception as e:
    print(f"❌ 连接失败: {e}")
    print("请确保Neo4j已启动，密码正确")
    exit()

# 清空现有数据（可选，谨慎使用）
# confirm = input("是否清空现有数据？(y/n): ")
# if confirm == 'y':
#     graph.run("MATCH (n) DETACH DELETE n")
#     print("已清空所有数据")

print("\n开始导入数据...\n")

# 导入疾病数据
diseases = [
    {"name": "感冒", "desc": "上呼吸道感染，由病毒引起", "cause": "病毒感染", "prevent": "勤洗手、戴口罩", "cure_way": "多休息、多喝水"},
    {"name": "肺炎", "desc": "肺部感染性炎症", "cause": "细菌或病毒感染", "prevent": "接种疫苗", "cure_way": "抗生素治疗"},
    {"name": "流感", "desc": "流行性感冒，传染性强", "cause": "流感病毒", "prevent": "接种流感疫苗", "cure_way": "抗病毒药物"},
    {"name": "支气管炎", "desc": "支气管黏膜炎症", "cause": "病毒或细菌感染", "prevent": "戒烟", "cure_way": "止咳化痰药物"},
    {"name": "哮喘", "desc": "慢性气道炎症", "cause": "过敏原", "prevent": "避免过敏原", "cure_way": "吸入激素"},
    {"name": "高血压", "desc": "血压持续升高", "cause": "遗传、饮食不当", "prevent": "低盐饮食、规律运动", "cure_way": "降压药物治疗"},
    {"name": "冠心病", "desc": "冠状动脉粥样硬化", "cause": "高血压、高血脂", "prevent": "控制血压血脂", "cure_way": "药物或支架治疗"},
    {"name": "糖尿病", "desc": "代谢性疾病", "cause": "胰岛素分泌不足", "prevent": "健康饮食、规律运动", "cure_way": "降糖药或胰岛素"},
    {"name": "胃炎", "desc": "胃黏膜炎症", "cause": "幽门螺杆菌感染", "prevent": "规律饮食", "cure_way": "抗幽门螺杆菌治疗"},
    {"name": "颈椎病", "desc": "颈椎退行性变", "cause": "长期低头", "prevent": "正确姿势", "cure_way": "物理治疗"},
]

for d in diseases:
    graph.run("""
        MERGE (d:疾病 {name: $name})
        SET d.desc = $desc, d.cause = $cause, 
            d.prevent = $prevent, d.cure_way = $cure_way
    """, name=d["name"], desc=d["desc"], cause=d["cause"],
        prevent=d["prevent"], cure_way=d["cure_way"])
    print(f"✅ 导入疾病: {d['name']}")

# 导入症状
symptoms = ["发烧", "咳嗽", "头痛", "乏力", "胸痛", "心悸", "鼻塞", "咽痛", "腹痛", "恶心"]
for sym in symptoms:
    graph.run("MERGE (s:症状 {name: $name})", name=sym)
print(f"✅ 导入 {len(symptoms)} 种症状")

# 导入科室
departments = ["呼吸内科", "心血管内科", "内分泌科", "消化内科", "骨科"]
for dept in departments:
    graph.run("MERGE (d:科室 {name: $name})", name=dept)
print(f"✅ 导入 {len(departments)} 个科室")

# 创建症状关系
symptom_rels = [
    ("感冒", "发烧"), ("感冒", "咳嗽"), ("感冒", "乏力"),
    ("肺炎", "发烧"), ("肺炎", "咳嗽"), ("肺炎", "胸痛"),
    ("流感", "发烧"), ("流感", "咳嗽"), ("流感", "头痛"),
    ("高血压", "头痛"), ("高血压", "心悸"),
    ("冠心病", "胸痛"), ("冠心病", "心悸"),
    ("胃炎", "腹痛"), ("胃炎", "恶心"),
]

for disease, symptom in symptom_rels:
    graph.run("""
        MATCH (d:疾病 {name: $disease})
        MATCH (s:症状 {name: $symptom})
        MERGE (d)-[:has_symptom]->(s)
    """, disease=disease, symptom=symptom)
print(f"✅ 创建 {len(symptom_rels)} 条症状关系")

# 创建科室关系
dept_rels = [
    ("感冒", "呼吸内科"), ("肺炎", "呼吸内科"), ("流感", "呼吸内科"), ("支气管炎", "呼吸内科"),
    ("高血压", "心血管内科"), ("冠心病", "心血管内科"),
    ("糖尿病", "内分泌科"),
    ("胃炎", "消化内科"),
    ("颈椎病", "骨科"),
]

for disease, dept in dept_rels:
    graph.run("""
        MATCH (d:疾病 {name: $disease})
        MATCH (dept:科室 {name: $dept})
        MERGE (d)-[:cure_department]->(dept)
    """, disease=disease, dept=dept)
print(f"✅ 创建 {len(dept_rels)} 条科室关系")

# 验证导入结果
print("\n" + "=" * 60)
print("导入完成！数据统计：")
print("=" * 60)

result = graph.run("MATCH (d:疾病) RETURN count(d) as count").data()
print(f"疾病数量: {result[0]['count']}")

result = graph.run("MATCH (s:症状) RETURN count(s) as count").data()
print(f"症状数量: {result[0]['count']}")

result = graph.run("MATCH (dept:科室) RETURN count(dept) as count").data()
print(f"科室数量: {result[0]['count']}")

result = graph.run("MATCH ()-[r:has_symptom]->() RETURN count(r) as count").data()
print(f"症状关系: {result[0]['count']}")

result = graph.run("MATCH ()-[r:cure_department]->() RETURN count(r) as count").data()
print(f"科室关系: {result[0]['count']}")

print("\n✅ 数据库导入完成！")
print("现在可以运行 web_app.py 进行问答测试了")