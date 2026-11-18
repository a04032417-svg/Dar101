#!/usr/bin/env python3
"""mkshop.py <x> <handle> <plan_id> <pages> <img_urls_json> -> /home/claude/work/<x>/shop_input.json (English Shopify productSet input)"""
import sys, json, html
x, handle, plan, pages, imgs = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], json.loads(open(sys.argv[5]).read())
C = json.load(open(f'/home/claude/work/copy/{x}/en.json')); e = html.escape
fix = lambda s: s.replace('{pages}', pages).replace('can not', 'cannot').replace('Standard .xlsx', 'Standard xlsx')
desc = fix(C['description']); h = ''
for block in desc.split('\n\n'):
    lines = block.split('\n')
    if lines[0].startswith('What you get'):
        h += '<p><strong>What you get:</strong></p><ul>' + ''.join(f'<li>{e(l.lstrip("✓ ").strip())}</li>' for l in lines[1:]) + '</ul>'
    else:
        h += f'<p>{e(block)}</p>'
h += '<p><strong>What it does for you</strong></p><ul>' + ''.join(f'<li>{e(fix(f))}</li>' for f in C['features']) + '</ul>'
h += ''.join(f'<p><strong>{e(q["q"])}</strong><br>{e(fix(q["a"]))}</p>' for q in C['faq'])
out = {"title": C['seo_title'], "handle": handle, "vendor": "Dar Templates", "status": "ACTIVE", "productType": "Digital download", "category": "gid://shopify/TaxonomyCategory/so-2-4", "descriptionHtml": h,
       "seo": {"title": C['seo_title'], "description": C['seo_description']}, "tags": C['tags'],
       "productOptions": [{"name": "Title", "values": [{"name": "Default Title"}]}],
       "variants": [{"optionValues": [{"optionName": "Title", "name": "Default Title"}], "price": __import__("os").environ.get("PRICE","17.00")}],
       "metafields": [{"namespace": "custom", "key": "whop_url", "type": "url", "value": f"https://whop.com/checkout/{plan}"}],
       "files": [{"originalSource": u, "alt": f"{C['name']} {i+1}", "contentType": "IMAGE"} for i, u in enumerate(imgs)]}
json.dump(out, open(f'/home/claude/work/{x}/shop_input.json', 'w'), ensure_ascii=False)
print(len(h), 'compatible' in h.lower(), out['title'])
