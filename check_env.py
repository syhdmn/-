import sys
print("=" * 60)
print("医疗问答系统 - 环境验证")
print("=" * 60)

print(f"Python版本: {sys.version}")

packages = [
    ('tensorflow', 'TensorFlow'),
    ('flask', 'Flask'),
    ('requests', 'Requests'),
    ('gevent', 'Gevent'),
    ('jieba', 'jieba'),
    ('gensim', 'Gensim'),
    ('py2neo', 'py2neo'),
    ('itchat', 'itchat'),
    ('numpy', 'NumPy'),
    ('pandas', 'Pandas'),
    ('sklearn', 'scikit-learn'),
    ('tqdm', 'tqdm'),
    ('matplotlib', 'Matplotlib')
]

print("\n已安装的包:")
print("-" * 60)

for pkg, name in packages:
    try:
        module = __import__(pkg)
        version = getattr(module, '__version__', '已安装')
        print(f"✓ {name:15} : {version}")
    except ImportError:
        print(f"✗ {name:15} : 未安装")

print("\n" + "=" * 60)
print("环境配置完成！")
print("=" * 60)
