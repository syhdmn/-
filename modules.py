# -*- coding:utf-8 -*-
import os
import re
import json
import requests
import random
from py2neo import Graph

from nlu.sklearn_Classification.clf_model import CLFModel
from utils.json_utils import dump_user_dialogue_context,load_user_dialogue_context
from config import *

# 正确的 Neo4j 连接配置
print("正在连接 Neo4j...")
graph = Graph("bolt://127.0.0.1:7688", auth=("neo4j", "abcd1234wohaomei*"))
print("✅ Neo4j 连接成功")

clf_model = CLFModel('./nlu/sklearn_Classification/model_file/')

def intent_classifier(text):
    url = 'http://127.0.0.1:60062/service/api/bert_intent_recognize'
    data = {"text":text}
    headers = {'Content-Type':'application/json;charset=utf8'}
    try:
        reponse = requests.post(url,data=json.dumps(data),headers=headers, timeout=5)
        if reponse.status_code == 200:
            reponse = json.loads(reponse.text)
            return reponse['data']
    except Exception as e:
        print(f"意图识别错误: {e}")
    return {"name": "其他", "confidence": 0.3}

def slot_recognizer(text):
    url = 'http://127.0.0.1:60061/service/api/medical_ner'
    data = {"text_list":[text]}
    headers = {'Content-Type':'application/json;charset=utf8'}
    try:
        reponse = requests.post(url,data=json.dumps(data),headers=headers, timeout=5)
        if reponse.status_code == 200:
            reponse = json.loads(reponse.text)
            return reponse['data']
    except Exception as e:
        print(f"NER识别错误: {e}")
    return []

def entity_link(mention,etype):
    return mention

def classifier(text):
    return clf_model.predict(text)

def neo4j_searcher(cql_list):
    ress = ""
    try:
        if isinstance(cql_list,list):
            for cql in cql_list:
                rst = []
                data = graph.run(cql).data()
                if not data:
                    continue
                for d in data:
                    d = list(d.values())
                    if isinstance(d[0],list):
                        rst.extend(d[0])
                    else:
                        rst.extend(d)
                data = "、".join([str(i) for i in rst])
                ress += data+"\n"
        else:
            data = graph.run(cql_list).data()
            if not data:
                return ress
            rst = []
            for d in data:
                d = list(d.values())
                if isinstance(d[0],list):
                    rst.extend(d[0])
                else:
                    rst.extend(d)
            data = "、".join([str(i) for i in rst])
            ress += data
    except Exception as e:
        print(f"查询错误: {e}")
        return "数据库查询出错"
    
    return ress

def semantic_parser(text,user):
    intent_rst = intent_classifier(text)
    slot_rst = slot_recognizer(text)
    if intent_rst.get("name")=="其他":
        return semantic_slot.get("unrecognized")

    slot_info = semantic_slot.get(intent_rst.get("name"))
    if not slot_info:
        return semantic_slot.get("unrecognized")

    slots = slot_info.get("slot_list", [])
    slot_values = {}
    for slot in slots:
        slot_values[slot] = None
        for ent_info in slot_rst:
            for e in ent_info.get("entities", []):
                if slot.lower() == e.get('type', '').lower():
                    slot_values[slot] = entity_link(e.get('word',''), e.get('type',''))

    last_slot_values = load_user_dialogue_context(user).get("slot_values", {})
    for k in slot_values.keys():
        if slot_values[k] is None:
            slot_values[k] = last_slot_values.get(k,None)
        
    slot_info["slot_values"] = slot_values

    conf = intent_rst.get("confidence", 0)
    if conf >= intent_threshold_config["accept"]:
        slot_info["intent_strategy"] = "accept"
    elif conf >= intent_threshold_config["deny"]:
        slot_info["intent_strategy"] = "clarify"
    else:
        slot_info["intent_strategy"] = "deny"

    return slot_info

def get_answer(slot_info):
    cql_template = slot_info.get("cql_template")
    reply_template = slot_info.get("reply_template")
    ask_template = slot_info.get("ask_template")
    slot_values = slot_info.get("slot_values")
    strategy = slot_info.get("intent_strategy")

    if not slot_values:
        return slot_info

    if strategy == "accept":
        cql = []
        if isinstance(cql_template,list):
            for cqlt in cql_template:
                try:
                    cql.append(cqlt.format(**slot_values))
                except:
                    cql.append(cqlt)
        else:
            try:
                cql = cql_template.format(**slot_values)
            except:
                cql = cql_template
        answer = neo4j_searcher(cql)
        if not answer or answer == "":
            slot_info["replay_answer"] = "唔~我装满知识的大脑此刻很贫瘠"
        else:
            pattern = reply_template.format(**slot_values)
            slot_info["replay_answer"] = pattern + answer
    elif strategy == "clarify":
        pattern = ask_template.format(**slot_values)
        slot_info["replay_answer"] = pattern
        cql = []
        if isinstance(cql_template,list):
            for cqlt in cql_template:
                try:
                    cql.append(cqlt.format(**slot_values))
                except:
                    cql.append(cqlt)
        else:
            try:
                cql = cql_template.format(**slot_values)
            except:
                cql = cql_template
        answer = neo4j_searcher(cql)
        if not answer:
            slot_info["replay_answer"] = "唔~我装满知识的大脑此刻很贫瘠"
        else:
            pattern = reply_template.format(**slot_values)
            slot_info["choice_answer"] = pattern + answer
    elif strategy == "deny":
        slot_info["replay_answer"] = slot_info.get("deny_response", "抱歉，我不太明白")
    
    return slot_info

def gossip_robot(intent):
    return random.choice(gossip_corpus.get(intent, ["你好"]))

def medical_robot(text,user):
    semantic_slot = semantic_parser(text,user)
    answer = get_answer(semantic_slot)
    return answer
