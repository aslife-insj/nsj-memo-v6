#!/usr/bin/env python3
"""Собирает materials.json: для каждой папки презентера берёт PDF с самой свежей датой
последнего коммита. Запускается автоматически при каждой публикации сайта."""
import json, os, subprocess, sys
root = sys.argv[1] if len(sys.argv) > 1 else '.'
out = sys.argv[2] if len(sys.argv) > 2 else 'materials.json'
# --- проверка content.json: при ошибке публикация останавливается, на сайте остаётся прежняя версия ---
def fail(msg):
    print('::error file=content.json::' + msg)
    sys.exit(1)
try:
    _data = json.load(open(os.path.join(root, 'content.json'), encoding='utf8'))
except json.JSONDecodeError as e:
    fail('Ошибка в content.json: строка %d, символ %d (%s). Проверьте запятые и кавычки рядом с этим местом.' % (e.lineno, e.colno, e.msg))
except Exception as e:
    fail('Не удалось прочитать content.json: %s' % e)
_cats = set(c.get('id') for c in _data.get('categories', []))
_ids = set()
for _p in _data.get('products', []):
    _pid = _p.get('id')
    if not _pid or not _p.get('name'):
        fail('В одном из продуктов нет id или name. Проверьте блок рядом с «%s».' % (_p.get('name') or _pid or '?'))
    if _pid in _ids:
        fail('Повторяется id продукта: %s. У каждого продукта id должен быть свой.' % _pid)
    _ids.add(_pid)
    if _p.get('category') not in _cats:
        fail('У продукта «%s» неизвестная категория «%s». Допустимо: %s.' % (_pid, _p.get('category'), ', '.join(sorted(_cats))))
print('content.json: ок, продуктов %d' % len(_ids))

base = os.path.join(root, 'presenters')
best = {}
for dp, _, fs in os.walk(base):
    for f in fs:
        if not f.lower().endswith('.pdf'):
            continue
        full = os.path.join(dp, f)
        rel = os.path.relpath(full, root).replace(os.sep, '/')
        folder = os.path.relpath(dp, base).replace(os.sep, '/')
        if folder == '.':
            continue
        r = subprocess.run(['git', '-C', root, 'log', '-1', '--format=%cI', '--', rel], capture_output=True, text=True)
        when = r.stdout.strip()
        if not when:
            continue
        size = os.path.getsize(full)
        if not size:
            continue
        cur = best.get(folder)
        if not cur or (when, f) > (cur['updated'], cur['file']):
            best[folder] = {'file': rel, 'updated': when, 'size': size}
json.dump(best, open(out, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print('materials.json:', {k: (v['file'], v['updated']) for k, v in best.items()})
