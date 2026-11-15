"""Builds cc4_dropin.json (drop-in days from the attendance generator; slow, run once)."""
import json, os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cc_core as c
rows = [dict(date=x['date'], child_id=x['child_id'], child=x['child'], family_id=x['family_id'], room=x['room'], schedule=x['schedule'], hours=x['hours'])
        for x in c.attendance_rows() if x['extra_day'] and x['status'] == 'Present']
json.dump(rows, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cc4_dropin.json'), 'w'))
print(len(rows), rows[-1])
