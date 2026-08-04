from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('templates'))
source = env.loader.get_source(env, 'index.html')[0]
start = source.find('{% if tasks %}')
end = source.find('{% endfor %}') + len('{% endfor %}')
print(source[start:end])
