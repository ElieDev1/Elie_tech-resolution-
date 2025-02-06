import json
from django.core.management import call_command
from io import StringIO

out = StringIO()
call_command('dumpdata', stdout=out)
data = out.getvalue()

with open('db.json', 'w', encoding='utf-8') as f:
    json.dump(json.loads(data), f, ensure_ascii=False, indent=2)
