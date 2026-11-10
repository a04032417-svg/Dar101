"""Classroom teacher spec v1 (2026-11-10): weighted gradebook, attendance, missing work, behavior, parent contacts with
ready messages, lesson plan, classroom spending and reimbursement, field trips with permission slips. English; i18n later."""
import json, random
R = random.Random(20261110)
L = lambda key, label, vals: {"key": key, "label": label, "values": [{"key": k, "label": v} for k, v in vals]}
LV = lambda l, k: "{list:%s.%s}" % (l, k)
LOOK = lambda tcol, key, ref: "IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),\"\")" % (tcol, ref, key)
D30 = '">="&({today}-29)'
MONTH0 = '">="&(EOMONTH({today},-1)+1)'

settings = [
    {"key": "school", "label": "School name", "type": "text", "default": "Your School"},
    {"key": "teacher", "label": "Teacher name", "type": "text", "default": "Your Name"},
    {"key": "class_name", "label": "Class or subject", "type": "text", "default": "Grade 7 Science"},
    {"key": "w_homework", "label": "Weight of homework in the term grade %", "type": "pct", "default": 0.2},
    {"key": "w_quiz", "label": "Weight of quizzes in the term grade %", "type": "pct", "default": 0.25},
    {"key": "w_project", "label": "Weight of projects in the term grade %", "type": "pct", "default": 0.2},
    {"key": "w_exam", "label": "Weight of tests and exams in the term grade %", "type": "pct", "default": 0.35},
    {"key": "grade_a", "label": "Lowest term average for grade A", "type": "pct", "default": 0.9},
    {"key": "grade_b", "label": "Lowest term average for grade B", "type": "pct", "default": 0.8},
    {"key": "grade_c", "label": "Lowest term average for grade C", "type": "pct", "default": 0.7},
    {"key": "grade_d", "label": "Lowest term average for grade D", "type": "pct", "default": 0.6},
    {"key": "risk_mark", "label": "Term average below which a student is at risk", "type": "pct", "default": 0.65},
    {"key": "absence_alert", "label": "Absences in 30 days that put a student at risk", "type": "int", "default": 3},
    {"key": "missing_alert", "label": "Missing assignments that put a student at risk", "type": "int", "default": 2},
]
lists = [
    L("category", "Assessment Type", [("homework", "Homework"), ("quiz", "Quiz"), ("project", "Project"), ("exam", "Test or exam")]),
    L("att_status", "Attendance", [("present", "Present"), ("late", "Late"), ("absent", "Absent"), ("excused", "Excused absence")]),
    L("sub_status", "Submission", [("submitted", "Submitted"), ("late", "Submitted late"), ("missing", "Missing"), ("excused", "Excused")]),
    L("grade", "Grade", [("ga", "A"), ("gb", "B"), ("gc", "C"), ("gd", "D"), ("gf", "F")]),
    L("behavior", "Note Type", [("positive", "Positive"), ("minor", "Minor issue"), ("major", "Serious issue")]),
    L("contact_way", "Contact Way", [("call", "Phone call"), ("whatsapp", "WhatsApp"), ("email", "E-mail"), ("meeting", "Meeting"), ("note", "Note home")]),
    L("contact_reason", "Reason", [("absence", "Absence"), ("missing", "Missing work"), ("behavior", "Behavior"), ("praise", "Praise"), ("progress", "Progress"), ("meeting", "Meeting request")]),
    L("relation", "Relation", [("mother", "Mother"), ("father", "Father"), ("guardian", "Guardian")]),
    L("support", "Support Plan", [("none", "None"), ("extra_time", "Extra time"), ("seating", "Front seating"), ("reading", "Reading support"), ("language", "Language support"), ("other", "Other plan")]),
    L("lesson_status", "Lesson Status", [("planned", "Planned"), ("taught", "Taught"), ("moved", "Moved")]),
    L("exp_cat", "Spending Type", [("supplies", "Classroom supplies"), ("books", "Books"), ("printing", "Printing"), ("prizes", "Rewards and prizes"), ("tech", "Tech and apps"), ("trip", "Trips and events"), ("other", "Other")]),
    L("yes_no", "Yes / No", [("yes", "Yes"), ("no", "No")]),
    L("alert_level", "Alert", [("ok", "OK"), ("at_risk", "At risk"), ("due", "Due soon"), ("missing", "Missing work"), ("follow", "Follow up"), ("owed", "To be repaid")]),
]
AL = lambda k: LV("alert_level", k)

# ---------------------------------------------------------------- demo data: one class of 24 students, the last ten weeks of a term
FIRST = ["Emma", "Noah", "Olivia", "Liam", "Ava", "Lucas", "Mia", "Adam", "Sofia", "Omar", "Hana", "Leo", "Zara", "Yusuf", "Chloe", "Daniel",
         "Layla", "Ethan", "Nora", "Samir", "Grace", "Ali", "Maya", "Jack"]
LAST = ["Walker", "Haddad", "Brooks", "Moreno", "Kim", "Schmidt", "Rossi", "Khan", "Novak", "Silva", "Tanaka", "Okafor", "Dubois", "Yilmaz", "Evans",
        "Costa", "Rahman", "Baker", "Jensen", "Nasser", "Patel", "Hassan", "Lopez", "Reid"]
GFIRST = ["Sarah", "Michael", "Laura", "David", "Anna", "Peter", "Julia", "Karim", "Elena", "Tariq", "Mei", "John", "Amira", "Mehmet", "Rachel", "Carlos",
          "Fatima", "Mark", "Ingrid", "Rami", "Priya", "Samira", "Isabel", "Paul"]
SUP = ["none"] * 17 + ["extra_time", "reading", "seating", "language", "extra_time", "other", "reading"]
ABILITY = [0.93, 0.71, 0.88, 0.62, 0.95, 0.79, 0.84, 0.58, 0.9, 0.74, 0.97, 0.68, 0.86, 0.77, 0.81, 0.55, 0.91, 0.73, 0.87, 0.66, 0.94, 0.7, 0.83, 0.76]
students = []
for i in range(24):
    sid = f"S-{101 + i}"
    students.append({"st_id": sid, "name": f"{FIRST[i]} {LAST[i]}", "guardian": f"{GFIRST[i]} {LAST[i]}", "relation": R.choice(["mother", "mother", "father", "guardian"]),
                     "phone": f"+1 555 01{10 + i:02d}", "email": f"{GFIRST[i].lower()}.{LAST[i].lower()}@example.com", "support": SUP[i],
                     "notes": "Allergic to peanuts" if i == 5 else "Needs glasses for the board" if i == 11 else ""})
ASG = [("Cells: label the diagram", "homework", -66, -62, 10), ("Quiz 1: cells and organisms", "quiz", -60, -59, 20), ("Microscope lab report", "project", -58, -50, 30),
       ("Food chains worksheet", "homework", -52, -48, 10), ("Quiz 2: ecosystems", "quiz", -46, -45, 20), ("Unit test: living things", "exam", -44, -40, 50),
       ("Energy vocabulary", "homework", -38, -34, 10), ("Quiz 3: forms of energy", "quiz", -32, -31, 20), ("Renewable energy poster", "project", -36, -24, 40),
       ("Circuits practice", "homework", -27, -23, 10), ("Quiz 4: electricity", "quiz", -20, -19, 20), ("Midterm exam", "exam", -17, -14, 80),
       ("Forces reading questions", "homework", -12, -8, 10), ("Quiz 5: forces and motion", "quiz", -6, -5, 20), ("Bridge building project", "project", -9, 6, 40),
       ("Unit test: forces", "exam", 1, 9, 50)]
assignments = [{"as_id": f"A-{201 + k}", "title": t, "category": c, "set": f"today{s:+d}", "due": f"today{d:+d}", "max": m,
                "standard": ["LS1.A", "LS1.A", "LS1.A", "LS2.B", "LS2.B", "LS1-LS2", "PS3.A", "PS3.A", "PS3.D", "PS3.B", "PS3.B", "PS3", "PS2.A", "PS2.A", "ETS1.B", "PS2"][k]}
               for k, (t, c, s, d, m) in enumerate(ASG)]
scores = []
for a, (t, c, s, d, m) in zip(assignments, ASG):
    if d >= 0: continue
    for i, st in enumerate(students):
        ab = ABILITY[i]; r = R.random()
        miss = 0.13 if ab < 0.65 else 0.06 if ab < 0.8 else 0.015
        if r < miss: status, pts = "missing", ""
        elif r < miss + 0.012: status, pts = "excused", ""
        else:
            status = "late" if R.random() < (0.1 if ab < 0.75 else 0.03) else "submitted"
            pts = max(0, min(m, round(m * min(1.0, R.gauss(ab, 0.07)) * 2) / 2))
        scores.append({"student": st["st_id"], "assignment": a["as_id"], "status": status, "points": pts,
                       "comment": "Great reasoning" if status == "submitted" and pts == m and R.random() < 0.3 else "Show your working" if pts != "" and pts < 0.6 * m and R.random() < 0.5 else ""})
attendance = []
for d in range(-28, 0):
    if d % 7 in (2, 3): continue
    for i, st in enumerate(students):
        r = R.random(); pa = 0.10 if ABILITY[i] < 0.65 else 0.035
        status = "absent" if r < pa else "excused" if r < pa + 0.012 else "late" if r < pa + 0.05 else "present"
        attendance.append({"date": f"today{d:+d}", "student": st["st_id"], "status": status,
                           "note": "Doctor's appointment" if status == "excused" else "Bus late" if status == "late" and R.random() < 0.3 else ""})
BEH = [("positive", "Helped a classmate with the lab", "Praised in class"), ("positive", "Excellent questions during the lesson", "Merit point"),
       ("minor", "Talking during the test instructions", "Reminder"), ("minor", "Phone out in class", "Phone kept until the end of the day"),
       ("positive", "Led the group project well", "Note home"), ("major", "Pushed another student", "Referred to the head of year"),
       ("minor", "No homework three times", "Lunch catch-up session"), ("positive", "Most improved this month", "Certificate")]
behavior = []
for k in range(30):
    b = BEH[k % len(BEH)] if k % 5 else BEH[0]; st = students[(k * 7) % 24]
    behavior.append({"date": f"today-{60 - 2 * k}", "student": st["st_id"], "type": b[0], "note": b[1], "action": b[2]})
CON = [("missing", "whatsapp", "Asked to help with two missing homework tasks", 7), ("absence", "call", "Three absences, family visit abroad", 0),
       ("praise", "whatsapp", "Shared the poster score", 0), ("behavior", "meeting", "Met about the incident in the corridor", 14),
       ("progress", "email", "Sent the midterm progress report", 0), ("meeting", "note", "Invited to the parents' evening", 10)]
contacts = []
for k in range(22):
    c = CON[k % len(CON)]; st = students[(k * 5 + 3) % 24]; d = -56 + k * 2 + (k % 3)
    contacts.append({"date": f"today{d:+d}", "student": st["st_id"], "way": c[1], "reason": c[0], "summary": c[2],
                     "follow_up": f"today{d + c[3]:+d}" if c[3] else "", "done": "yes" if c[3] and d + c[3] < -3 else "no" if c[3] else ""})
TOP = [("Cells and organisms", "Name the parts of a cell"), ("Ecosystems", "Explain a food chain"), ("Energy", "Compare forms of energy"),
       ("Electricity", "Build a simple circuit"), ("Forces", "Measure force with a spring scale"), ("Motion", "Calculate speed"), ("Bridges", "Test a bridge design")]
lessons = []
for k, d in enumerate([x for x in range(-30, 12) if x % 7 not in (2, 3)][::1]):
    t = TOP[min(len(TOP) - 1, (k * len(TOP)) // 30)]
    lessons.append({"date": f"today{d:+d}", "period": f"Period {1 + k % 3}", "topic": t[0], "objective": t[1],
                    "materials": ["Slides and worksheet", "Microscopes", "Batteries, bulbs and wires", "Spring scales", "Laptops", "Card, tape and weights"][k % 6],
                    "homework": "Worksheet" if k % 3 == 0 else "", "status": "taught" if d < 0 else "planned" if k % 9 else "moved"})
lessons = lessons[:30]
EXP = [("supplies", "Markers, glue and card", 34.5, "yes"), ("books", "Science readers for the library corner", 48, "no"), ("printing", "Colour printing for the lab booklet", 22, "yes"),
       ("prizes", "Stickers and merit prizes", 18, "no"), ("supplies", "Batteries and bulbs for the circuits lesson", 41.8, "yes"), ("tech", "Quiz app subscription (month)", 12, "yes"),
       ("supplies", "Craft sticks and tape for the bridge project", 27.4, "yes"), ("prizes", "Certificates and frames", 16, "no"), ("trip", "Snacks for the science museum trip", 35, "yes"),
       ("printing", "Permission slips and trip booklet", 9.5, "yes"), ("books", "Guided reading set", 39, "no"), ("supplies", "Spring scales (2 extra)", 23, "yes"),
       ("supplies", "Seeds, soil and pots for the plant study", 19.9, "yes"), ("tech", "Quiz app subscription (month)", 12, "yes"), ("other", "Tissues and hand sanitiser", 14.5, "no"),
       ("supplies", "Safety goggles (6 pairs)", 31, "yes"), ("printing", "Revision booklets", 26, "yes"), ("prizes", "End-of-term prizes", 28, "no"),
       ("tech", "Quiz app subscription (month)", 12, "yes"), ("supplies", "Magnets and iron filings", 17.6, "yes"), ("books", "Lab notebooks", 33, "yes"),
       ("trip", "Planetarium tickets top-up", 40, "yes"), ("supplies", "Poster paper and paint", 21.3, "yes"), ("other", "Cleaning wipes for the lab", 11, "no")]
expenses = []
for k, (c, it, a, rb) in enumerate(EXP):
    d = -300 + k * 13
    expenses.append((f"today{d:+d}", c, it, a, rb, "yes" if rb == "yes" and d < -45 else "no"))
expenses = [{"date": d, "category": c, "item": it, "amount": a, "reimbursable": rb, "reimbursed": rd} for d, c, it, a, rb, rd in expenses]
TRIP = [("Welcome evening for families", -250, "School hall", 0), ("Nature walk in the park", -220, "City park", 0), ("Planetarium visit", -190, "City Planetarium", 9),
        ("Recycling plant tour", -160, "Green Recycling Centre", 4), ("Parents' evening", -130, "Classroom", 0), ("Zoo field study", -100, "City Zoo", 11),
        ("Science week workshops", -70, "School labs", 0), ("Water treatment visit", -40, "Water Works", 3), ("Science museum visit", 18, "City Science Museum", 12),
        ("Botanical garden field study", 46, "Botanical Garden", 6), ("Science fair", 60, "School hall", 0), ("End-of-year class picnic", 80, "Lakeside park", 5)]
trips = [{"ev_id": f"T-{1 + k:02d}", "title": t, "date": f"today{d:+d}", "place": pl, "cost": c, "slip_due": f"today{d - 10:+d}", "plan_start": f"today{d - 21:+d}"} for k, (t, d, pl, c) in enumerate(TRIP)]

# ---------------------------------------------------------------- tables
def cat_avg(cat): return "IFERROR(AVERAGEIFS({range:scores.pct},{range:scores.student},{col:st_id},{range:scores.category},%s),\"\")" % LV("category", cat)
W = [("hw", "w_homework"), ("quiz", "w_quiz"), ("project", "w_project"), ("exam", "w_exam")]
TERM = "IFERROR((" + "+".join("IF(ISNUMBER({col:%s}),{col:%s}*{set:%s},0)" % (c, c, w) for c, w in W) + ")/(" + "+".join("IF(ISNUMBER({col:%s}),{set:%s},0)" % (c, w) for c, w in W) + "),\"\")"
GRADE = "IF({col:term}=\"\",\"\",IF({col:term}>={set:grade_a},%s,IF({col:term}>={set:grade_b},%s,IF({col:term}>={set:grade_c},%s,IF({col:term}>={set:grade_d},%s,%s)))))" % tuple(LV("grade", "g" + g) for g in "abcdf")
ATT30 = "IFERROR((COUNTIFS({range:attendance.student},{col:st_id},{range:attendance.status},%s,{range:attendance.date},%s)+COUNTIFS({range:attendance.student},{col:st_id},{range:attendance.status},%s,{range:attendance.date},%s))/COUNTIFS({range:attendance.student},{col:st_id},{range:attendance.date},%s),\"\")" % (LV("att_status", "present"), D30, LV("att_status", "late"), D30, D30)
tables = [
 {"key": "students", "sheet": "Students", "title": "Students", "hint": "One row per student, with the parent or guardian to contact. Averages, grade and alerts fill in from the other sheets.", "rows": 200,
  "columns": [{"key": "st_id", "label": "Student ID", "type": "text", "width": 10}, {"key": "name", "label": "Student", "type": "text", "width": 22, "required": True},
              {"key": "guardian", "label": "Parent or guardian", "type": "text", "width": 20}, {"key": "relation", "label": "Relation", "type": "list", "list": "relation", "width": 11},
              {"key": "phone", "label": "Phone (with country code)", "type": "text", "width": 17}, {"key": "email", "label": "E-mail", "type": "text", "width": 24},
              {"key": "support", "label": "Support plan", "type": "list", "list": "support", "width": 15}, {"key": "notes", "label": "Notes (health, seating)", "type": "text", "width": 24},
              {"key": "att30", "label": "Attendance (30 days)", "type": "calc", "format": "pct", "formula": ATT30, "width": 12, "visual": "up"},
              {"key": "abs30", "label": "Absences (30 days)", "type": "calc", "format": "int", "width": 11,
               "formula": "COUNTIFS({range:attendance.student},{col:st_id},{range:attendance.status},%s,{range:attendance.date},%s)" % (LV("att_status", "absent"), D30)},
              {"key": "missing", "label": "Missing work", "type": "calc", "format": "int", "width": 10, "formula": "COUNTIFS({range:scores.student},{col:st_id},{range:scores.status},%s)" % LV("sub_status", "missing")},
              {"key": "hw", "label": "Homework average", "type": "calc", "format": "pct", "formula": cat_avg("homework"), "width": 11},
              {"key": "quiz", "label": "Quiz average", "type": "calc", "format": "pct", "formula": cat_avg("quiz"), "width": 10},
              {"key": "project", "label": "Project average", "type": "calc", "format": "pct", "formula": cat_avg("project"), "width": 10},
              {"key": "exam", "label": "Test average", "type": "calc", "format": "pct", "formula": cat_avg("exam"), "width": 10},
              {"key": "term", "label": "Term average", "type": "calc", "format": "pct", "formula": TERM, "width": 11, "visual": "up"},
              {"key": "grade", "label": "Grade", "type": "calc", "format": "text", "formula": GRADE, "width": 8},
              {"key": "positives", "label": "Positive notes", "type": "calc", "format": "int", "width": 10, "formula": "COUNTIFS({range:behavior.student},{col:st_id},{range:behavior.type},%s)" % LV("behavior", "positive")},
              {"key": "last_contact", "label": "Last parent contact", "type": "calc", "format": "date", "width": 13,
               "formula": "IF(MAXIFS({range:contacts.date},{range:contacts.student},{col:st_id})=0,\"\",MAXIFS({range:contacts.date},{range:contacts.student},{col:st_id}))"},
              {"key": "flag", "label": "Alert", "type": "calc", "format": "text", "width": 11,
               "formula": "IF({col:name}=\"\",\"\",IF(OR(AND(ISNUMBER({col:term}),{col:term}<{set:risk_mark}),{col:abs30}>={set:absence_alert},{col:missing}>={set:missing_alert}),%s,%s))" % (AL("at_risk"), AL("ok"))}],
  "alerts": [{"column": "flag", "when": "= " + AL("at_risk"), "style": "bad"}, {"column": "abs30", "when": ">= {set:absence_alert}", "style": "warn"},
             {"column": "missing", "when": ">= {set:missing_alert}", "style": "warn"}, {"column": "term", "when": "< {set:risk_mark}", "style": "bad"}],
  "demo": students},
 {"key": "assignments", "sheet": "Assignments", "title": "Assignments", "hint": "Every homework, quiz, project and test, with its maximum points. Hand-in counts and the class average fill in from Scores.", "rows": 300,
  "columns": [{"key": "as_id", "label": "Assignment ID", "type": "text", "width": 12}, {"key": "title", "label": "Assignment", "type": "text", "width": 30, "required": True},
              {"key": "category", "label": "Type", "type": "list", "list": "category", "width": 13}, {"key": "set", "label": "Set on", "type": "date", "width": 12},
              {"key": "due", "label": "Due", "type": "date", "width": 12}, {"key": "max", "label": "Maximum points", "type": "num", "width": 11},
              {"key": "standard", "label": "Standard or unit", "type": "text", "width": 13},
              {"key": "handed", "label": "Handed in", "type": "calc", "format": "int", "width": 10,
               "formula": "COUNTIFS({range:scores.assignment},{col:as_id},{range:scores.status},%s)+COUNTIFS({range:scores.assignment},{col:as_id},{range:scores.status},%s)" % (LV("sub_status", "submitted"), LV("sub_status", "late"))},
              {"key": "missing", "label": "Missing", "type": "calc", "format": "int", "width": 9, "formula": "COUNTIFS({range:scores.assignment},{col:as_id},{range:scores.status},%s)" % LV("sub_status", "missing")},
              {"key": "avg", "label": "Class average", "type": "calc", "format": "pct", "width": 11, "formula": "IFERROR(AVERAGEIFS({range:scores.pct},{range:scores.assignment},{col:as_id}),\"\")", "visual": "up"},
              {"key": "days", "label": "Days to due date", "type": "calc", "format": "int", "width": 11, "formula": "IF({col:due}=\"\",\"\",{col:due}-{today})"},
              {"key": "flag", "label": "Alert", "type": "calc", "format": "text", "width": 12,
               "formula": "IF({col:title}=\"\",\"\",IF(AND(ISNUMBER({col:days}),{col:days}>=0,{col:days}<=7),%s,IF({col:missing}>0,%s,%s)))" % (AL("due"), AL("missing"), AL("ok"))}],
  "alerts": [{"column": "flag", "when": "= " + AL("due"), "style": "warn"}, {"column": "missing", "when": "> 0", "style": "warn"}],
  "demo": assignments},
 {"key": "scores", "sheet": "Scores", "title": "Scores", "hint": "One row per student per assignment. A missing piece of work counts as zero; an excused one is left out of the averages.", "rows": 3000,
  "columns": [{"key": "student", "label": "Student ID", "type": "ref", "ref": "students.st_id", "width": 11, "required": True},
              {"key": "assignment", "label": "Assignment ID", "type": "ref", "ref": "assignments.as_id", "width": 12},
              {"key": "status", "label": "Submission", "type": "list", "list": "sub_status", "width": 14}, {"key": "points", "label": "Points", "type": "num", "width": 9},
              {"key": "comment", "label": "Feedback", "type": "text", "width": 24},
              {"key": "s_name", "label": "Student", "type": "calc", "format": "text", "width": 20, "formula": LOOK("students.name", "students.st_id", "student")},
              {"key": "a_title", "label": "Assignment", "type": "calc", "format": "text", "width": 26, "formula": LOOK("assignments.title", "assignments.as_id", "assignment")},
              {"key": "category", "label": "Type", "type": "calc", "format": "text", "width": 12, "formula": LOOK("assignments.category", "assignments.as_id", "assignment")},
              {"key": "max", "label": "Out of", "type": "calc", "format": "num", "width": 8, "formula": LOOK("assignments.max", "assignments.as_id", "assignment")},
              {"key": "pct", "label": "Score %", "type": "calc", "format": "pct", "width": 9, "visual": "up",
               "formula": "IF({col:status}=%s,\"\",IF({col:status}=%s,0,IF(OR({col:points}=\"\",{col:max}=\"\",{col:max}=0),\"\",{col:points}/{col:max})))" % (LV("sub_status", "excused"), LV("sub_status", "missing"))}],
  "alerts": [{"column": "status", "when": "= " + LV("sub_status", "missing"), "style": "bad"}, {"column": "pct", "when": "< {set:grade_d}", "style": "warn"}],
  "demo": scores},
 {"key": "attendance", "sheet": "Attendance", "title": "Attendance", "hint": "One row per student per school day. Absences and lates of the last 30 days show on Students and the dashboard.", "rows": 3000,
  "columns": [{"key": "date", "label": "Date", "type": "date", "width": 12, "required": True}, {"key": "student", "label": "Student ID", "type": "ref", "ref": "students.st_id", "width": 11},
              {"key": "status", "label": "Attendance", "type": "list", "list": "att_status", "width": 15}, {"key": "note", "label": "Note", "type": "text", "width": 22},
              {"key": "s_name", "label": "Student", "type": "calc", "format": "text", "width": 20, "formula": LOOK("students.name", "students.st_id", "student")},
              {"key": "absent_n", "label": "Absent", "type": "calc", "format": "int", "width": 8, "formula": "IF({col:status}=%s,1,0)" % LV("att_status", "absent")},
              {"key": "late_n", "label": "Late", "type": "calc", "format": "int", "width": 7, "formula": "IF({col:status}=%s,1,0)" % LV("att_status", "late")}],
  "alerts": [{"column": "status", "when": "= " + LV("att_status", "absent"), "style": "bad"}, {"column": "status", "when": "= " + LV("att_status", "late"), "style": "warn"}],
  "demo": attendance},
 {"key": "behavior", "sheet": "Behavior Log", "title": "Behavior log", "hint": "Positive notes as well as issues, with what you did about them.", "rows": 1000,
  "columns": [{"key": "date", "label": "Date", "type": "date", "width": 12, "required": True}, {"key": "student", "label": "Student ID", "type": "ref", "ref": "students.st_id", "width": 11},
              {"key": "type", "label": "Type", "type": "list", "list": "behavior", "width": 14}, {"key": "note", "label": "What happened", "type": "text", "width": 34},
              {"key": "action", "label": "Action taken", "type": "text", "width": 26},
              {"key": "s_name", "label": "Student", "type": "calc", "format": "text", "width": 20, "formula": LOOK("students.name", "students.st_id", "student")}],
  "alerts": [{"column": "type", "when": "= " + LV("behavior", "major"), "style": "bad"}, {"column": "type", "when": "= " + LV("behavior", "positive"), "style": "good"}],
  "demo": behavior},
 {"key": "contacts", "sheet": "Parent Contacts", "title": "Parent contacts", "hint": "Every call, message or meeting with a family, and the date to follow up.", "rows": 1000,
  "columns": [{"key": "date", "label": "Date", "type": "date", "width": 12, "required": True}, {"key": "student", "label": "Student ID", "type": "ref", "ref": "students.st_id", "width": 11},
              {"key": "way", "label": "Contact way", "type": "list", "list": "contact_way", "width": 13}, {"key": "reason", "label": "Reason", "type": "list", "list": "contact_reason", "width": 15},
              {"key": "summary", "label": "Summary", "type": "text", "width": 34}, {"key": "follow_up", "label": "Follow up on", "type": "date", "width": 12},
              {"key": "done", "label": "Follow-up done", "type": "list", "list": "yes_no", "width": 10},
              {"key": "s_name", "label": "Student", "type": "calc", "format": "text", "width": 20, "formula": LOOK("students.name", "students.st_id", "student")},
              {"key": "guardian", "label": "Parent or guardian", "type": "calc", "format": "text", "width": 20, "formula": LOOK("students.guardian", "students.st_id", "student")},
              {"key": "flag", "label": "Alert", "type": "calc", "format": "text", "width": 11,
               "formula": "IF(OR({col:follow_up}=\"\",{col:done}=%s),\"\",IF({col:follow_up}<={today}+2,%s,%s))" % (LV("yes_no", "yes"), AL("follow"), AL("ok"))}],
  "alerts": [{"column": "flag", "when": "= " + AL("follow"), "style": "warn"}],
  "demo": contacts},
 {"key": "lessons", "sheet": "Lesson Plan", "title": "Lesson plan", "hint": "Plan each lesson: topic, objective, materials and homework. Mark it taught or moved.", "rows": 500,
  "columns": [{"key": "date", "label": "Date", "type": "date", "width": 12, "required": True}, {"key": "period", "label": "Period", "type": "text", "width": 10},
              {"key": "topic", "label": "Topic", "type": "text", "width": 22}, {"key": "objective", "label": "Learning objective", "type": "text", "width": 30},
              {"key": "materials", "label": "Materials", "type": "text", "width": 24}, {"key": "homework", "label": "Homework set", "type": "text", "width": 14},
              {"key": "status", "label": "Status", "type": "list", "list": "lesson_status", "width": 11},
              {"key": "days", "label": "Days from today", "type": "calc", "format": "int", "width": 10, "formula": "IF({col:date}=\"\",\"\",{col:date}-{today})"}],
  "alerts": [{"column": "status", "when": "= " + LV("lesson_status", "moved"), "style": "warn"}, {"column": "days", "when": "= 0", "style": "good"}],
  "demo": lessons},
 {"key": "expenses", "sheet": "Classroom Spending", "title": "Classroom spending", "hint": "What you pay for the class out of your own pocket, and what the school still owes you.", "rows": 500,
  "columns": [{"key": "date", "label": "Date", "type": "date", "width": 12, "required": True}, {"key": "category", "label": "Type", "type": "list", "list": "exp_cat", "width": 17},
              {"key": "item", "label": "What you bought", "type": "text", "width": 32}, {"key": "amount", "label": "Amount", "type": "money", "width": 11},
              {"key": "reimbursable", "label": "School repays it", "type": "list", "list": "yes_no", "width": 11}, {"key": "reimbursed", "label": "Repaid", "type": "list", "list": "yes_no", "width": 9},
              {"key": "owed", "label": "Still owed to you", "type": "calc", "format": "money", "width": 12,
               "formula": "IF(AND({col:reimbursable}=%s,{col:reimbursed}<>%s),{col:amount},0)" % (LV("yes_no", "yes"), LV("yes_no", "yes"))},
              {"key": "flag", "label": "Alert", "type": "calc", "format": "text", "width": 12, "formula": "IF({col:owed}>0,%s,\"\")" % AL("owed")}],
  "alerts": [{"column": "flag", "when": "= " + AL("owed"), "style": "warn"}],
  "demo": expenses},
 {"key": "trips", "sheet": "Trips & Events", "title": "Trips and events", "hint": "Field trips and class events. The permission slip and the trip checklist are filled from this sheet.", "rows": 50,
  "columns": [{"key": "ev_id", "label": "Trip ID", "type": "text", "width": 9}, {"key": "title", "label": "Trip or event", "type": "text", "width": 28, "required": True},
              {"key": "date", "label": "Date", "type": "date", "width": 12}, {"key": "place", "label": "Place", "type": "text", "width": 22},
              {"key": "cost", "label": "Cost per student", "type": "money", "width": 11}, {"key": "slip_due", "label": "Slips due back", "type": "date", "width": 12},
              {"key": "plan_start", "label": "Start planning on", "type": "date", "width": 13},
              {"key": "days", "label": "Days to go", "type": "calc", "format": "int", "width": 9, "formula": "IF({col:date}=\"\",\"\",{col:date}-{today})"}],
  "alerts": [{"column": "slip_due", "when": "< {today}", "style": "warn"}],
  "demo": trips},
]

dashboard = {"title": "Class Dashboard", "kpis": [
    {"label": "Students", "formula": "COUNTA({range:students.name})", "format": "int"},
    {"label": "Class average", "formula": "IFERROR(AVERAGE({range:students.term}),\"\")", "format": "pct"},
    {"label": "Students at risk", "formula": "COUNTIFS({range:students.flag},%s)" % AL("at_risk"), "format": "int"},
    {"label": "Attendance, last 30 days", "format": "pct", "formula": "IFERROR((COUNTIFS({range:attendance.status},%s,{range:attendance.date},%s)+COUNTIFS({range:attendance.status},%s,{range:attendance.date},%s))/COUNTIFS({range:attendance.date},%s),\"\")" % (LV("att_status", "present"), D30, LV("att_status", "late"), D30, D30)},
    {"label": "Absences, last 30 days", "formula": "COUNTIFS({range:attendance.status},%s,{range:attendance.date},%s)" % (LV("att_status", "absent"), D30), "format": "int"},
    {"label": "Missing assignments", "formula": "COUNTIFS({range:scores.status},%s)" % LV("sub_status", "missing"), "format": "int"},
    {"label": "Work handed in but not marked", "formula": "COUNTIFS({range:scores.status},%s,{range:scores.points},\"\")+COUNTIFS({range:scores.status},%s,{range:scores.points},\"\")" % (LV("sub_status", "submitted"), LV("sub_status", "late")), "format": "int"},
    {"label": "Assignments due in 7 days", "formula": "COUNTIFS({range:assignments.due},\">=\"&{today},{range:assignments.due},\"<=\"&({today}+7))", "format": "int"},
    {"label": "Lessons planned for the next 7 days", "formula": "COUNTIFS({range:lessons.date},\">=\"&{today},{range:lessons.date},\"<=\"&({today}+7))", "format": "int"},
    {"label": "Parent contacts this month", "formula": "COUNTIFS({range:contacts.date},%s)" % MONTH0, "format": "int"},
    {"label": "Follow-ups due", "formula": "COUNTIFS({range:contacts.flag},%s)" % AL("follow"), "format": "int"},
    {"label": "Positive notes, last 30 days", "formula": "COUNTIFS({range:behavior.type},%s,{range:behavior.date},%s)" % (LV("behavior", "positive"), D30), "format": "int"},
    {"label": "Issues, last 30 days", "formula": "COUNTIFS({range:behavior.type},%s,{range:behavior.date},%s)+COUNTIFS({range:behavior.type},%s,{range:behavior.date},%s)" % (LV("behavior", "minor"), D30, LV("behavior", "major"), D30), "format": "int"},
    {"label": "Students with a support plan", "formula": "COUNTA({range:students.support})-COUNTIFS({range:students.support},%s)" % LV("support", "none"), "format": "int"},
    {"label": "Your classroom spending this year", "formula": "SUMIFS({range:expenses.amount},{range:expenses.date},\">=\"&DATE(YEAR({today}),1,1))", "format": "money"},
    {"label": "Still owed to you by the school", "formula": "SUM({range:expenses.owed})", "format": "money"}],
  "monthly": {"title": "Absences and lates by month", "date": "attendance.date", "series": [{"label": "Absences", "sum": "attendance.absent_n"}, {"label": "Lates", "sum": "attendance.late_n"}]},
  "breakdowns": [{"title": "Submissions by status", "by": "scores.status", "value": "scores.points", "agg": "count"},
                 {"title": "Parent contacts by reason", "by": "contacts.reason", "value": "contacts.date", "agg": "count"},
                 {"title": "Behavior notes by type", "by": "behavior.type", "value": "behavior.date", "agg": "count"},
                 {"title": "Spending by type", "by": "expenses.category", "value": "expenses.amount", "agg": "sum"}]}

forms = [{"key": "progress", "sheet": "Progress Report", "title": "Progress report", "pick": "students.st_id",
          "fields": [{"label": "Student", "value": "students.name"}, {"label": "Parent or guardian", "value": "students.guardian"},
                     {"label": "Attendance, last 30 days", "value": "students.att30"}, {"label": "Absences, last 30 days", "value": "students.abs30"},
                     {"label": "Homework average", "value": "students.hw"}, {"label": "Quiz average", "value": "students.quiz"},
                     {"label": "Project average", "value": "students.project"}, {"label": "Test average", "value": "students.exam"},
                     {"label": "Term average", "value": "students.term"}, {"label": "Grade", "value": "students.grade"},
                     {"label": "Missing assignments", "value": "students.missing"}, {"label": "Positive notes", "value": "students.positives"}],
          "lines": {"from": "scores", "match": "scores.student", "columns": ["a_title", "category", "status", "points", "max", "pct"], "max": 30}}]

tools = [
 {"key": "final_needed", "sheet": "Final Score Needed", "title": "Score needed on the final", "hint": "Enter the student's average so far, how much the final counts and the grade they want.",
  "inputs": [{"key": "current", "label": "Average so far", "type": "pct", "default": 0.72}, {"key": "final_w", "label": "Weight of the final in the grade", "type": "pct", "default": 0.3},
             {"key": "target", "label": "Term average the student wants", "type": "pct", "default": 0.8}],
  "outputs": [{"label": "Score needed on the final", "format": "pct", "formula": "IFERROR(({in:target}-{in:current}*(1-{in:final_w}))/{in:final_w},\"\")"},
              {"label": "Reachable with 100% or less", "format": "text", "formula": "IF(IFERROR(({in:target}-{in:current}*(1-{in:final_w}))/{in:final_w},2)>1,%s,%s)" % (LV("yes_no", "no"), LV("yes_no", "yes"))},
              {"label": "Term average with a perfect final", "format": "pct", "formula": "{in:current}*(1-{in:final_w})+{in:final_w}"}]},
 {"key": "curve", "sheet": "Grade Curve", "title": "Curve a test", "hint": "Scale scores so the top score of the class becomes the score you choose.",
  "inputs": [{"key": "raw", "label": "Student's score %", "type": "pct", "default": 0.62}, {"key": "top", "label": "Top score in the class %", "type": "pct", "default": 0.86},
             {"key": "new_top", "label": "Top score after the curve %", "type": "pct", "default": 1}],
  "outputs": [{"label": "Curved score", "format": "pct", "formula": "IFERROR(MIN(1,{in:raw}*{in:new_top}/{in:top}),\"\")"},
              {"label": "Points added (percentage points)", "format": "pct", "formula": "IFERROR(MIN(1,{in:raw}*{in:new_top}/{in:top})-{in:raw},\"\")"}]},
 {"key": "marking", "sheet": "Marking Time", "title": "Marking time planner", "hint": "How long a pile of marking will take, and how much per day until you hand it back.",
  "inputs": [{"key": "papers", "label": "Pieces of work to mark", "type": "int", "default": 28}, {"key": "minutes", "label": "Minutes per piece", "type": "num", "default": 6},
             {"key": "days", "label": "Days until you hand them back", "type": "int", "default": 3}],
  "outputs": [{"label": "Total marking time (hours)", "format": "num", "formula": "ROUND({in:papers}*{in:minutes}/60,1)"},
              {"label": "Pieces to mark per day", "format": "int", "formula": "IFERROR(ROUNDUP({in:papers}/{in:days},0),\"\")"},
              {"label": "Minutes per day", "format": "int", "formula": "IFERROR(ROUND({in:papers}*{in:minutes}/{in:days},0),\"\")"}]},
]
messages = [
 {"key": "absence", "moment": "Absence", "table": "students", "phone": "students.phone", "text": "Hello {guardian}, {name} was absent from class today. Absences in the last 30 days: {abs30}. Please let me know if there is anything I should know."},
 {"key": "missing", "moment": "Missing work", "table": "students", "phone": "students.phone", "text": "Hello {guardian}, {name} has {missing} missing assignments in my class. Could you help with handing them in this week? Thank you."},
 {"key": "praise", "moment": "Good news", "table": "students", "phone": "students.phone", "text": "Hello {guardian}, some good news: {name} has worked really well in class this week. I wanted you to know."},
 {"key": "meeting", "moment": "Meeting request", "table": "students", "phone": "students.phone", "text": "Hello {guardian}, I would like to meet you to talk about how {name} is doing in class. Which day suits you?"},
 {"key": "grade", "moment": "Grade update", "table": "students", "phone": "students.phone", "text": "Hello {guardian}, {name}'s grade in my class is {grade} so far this term. I will send the full progress report soon."},
]
documents = [
 {"key": "meeting_letter", "sheet": "Meeting Letter", "title": "Invitation to a parent meeting", "pick": "students.st_id",
  "paragraphs": ["Dear {col:students.guardian},", "I would like to meet you to talk about how {col:students.name} is doing in class.",
                 "In the last 30 days {col:students.name} was absent {col:students.abs30} times and has {col:students.missing} missing assignments. The current grade is {col:students.grade}.",
                 "Please reply with a day and time that suits you. Thank you for your support."],
  "sign": ["Teacher", "Parent or guardian"], "note": "Sample wording: change it to fit your school's rules."},
 {"key": "permission", "sheet": "Permission Slip", "title": "Trip permission slip", "pick": "trips.ev_id",
  "paragraphs": ["Our class is going on a trip: {col:trips.title}.", "Date: {col:trips.date}. Place: {col:trips.place}. Cost per student: {col:trips.cost}.",
                 "Please sign and return this slip by {col:trips.slip_due}.", "I give permission for my child, ____________________, to take part in this trip."],
  "sign": ["Parent or guardian", "Teacher"], "note": "Sample wording: add your school's own safety and medical questions."},
]
checklists = [
 {"key": "trip_plan", "title": "Field trip", "table": "trips", "start": "trips.plan_start",
  "steps": [{"label": "Get approval from the school", "days": 0}, {"label": "Book transport and tickets", "days": 2}, {"label": "Send permission slips home", "days": 5},
            {"label": "Collect slips, payments and medical notes", "days": 12}, {"label": "Arrange supervising adults", "days": 14},
            {"label": "Share the plan and emergency contacts", "days": 18}, {"label": "Trip day: count the students before leaving and returning", "days": 21}]},
 {"key": "project_plan", "title": "Class project", "table": "assignments", "start": "assignments.set",
  "steps": [{"label": "Share the brief and the marking rubric", "days": 0}, {"label": "Check every group has a plan", "days": 3}, {"label": "Mid-project check-in", "days": 7},
            {"label": "Feedback on drafts", "days": 10}, {"label": "Final work handed in", "days": 14}, {"label": "Marks and feedback returned", "days": 20}]},
]
insights = {"filters": [{"label": "Assessment type", "list": "category"}],
  "gauges": [{"title": "Work handed in", "num": {"agg": "count", "table": "scores", "where": [{"column": "status", "op": "<>", "value": LV("sub_status", "missing")}]}, "den": {"agg": "count", "table": "scores"}},
             {"title": "Present at school", "num": {"agg": "count", "table": "attendance", "where": [{"column": "status", "op": "<>", "value": LV("att_status", "absent")}]}, "den": {"agg": "count", "table": "attendance"}},
             {"title": "Spending repaid", "num": {"agg": "sum", "table": "expenses", "value": "expenses.amount", "where": [{"column": "reimbursed", "op": "=", "value": LV("yes_no", "yes")}]}, "den": {"agg": "sum", "table": "expenses", "value": "expenses.amount"}}],
  "charts": [{"title": "Absences by month", "type": "column", "by": "month", "series": [{"agg": "count", "table": "attendance", "date": "attendance.date", "where": [{"column": "status", "op": "=", "value": LV("att_status", "absent")}], "label": "Absences"}]},
             {"title": "Class average by assignment type", "type": "bar", "by": "assignments.category", "series": [{"agg": "avg", "table": "assignments", "value": "assignments.avg", "label": "Class average"}]},
             {"title": "Submissions by status", "type": "doughnut", "by": "scores.status", "series": [{"agg": "count", "table": "scores", "label": "Submissions"}]},
             {"title": "Parent contacts by reason", "type": "bar", "by": "contacts.reason", "series": [{"agg": "count", "table": "contacts", "label": "Contacts"}]},
             {"title": "Behavior notes by type", "type": "pie", "by": "behavior.type", "series": [{"agg": "count", "table": "behavior", "label": "Notes"}]},
             {"title": "Classroom spending by month", "type": "column", "by": "month", "series": [{"agg": "sum", "table": "expenses", "value": "expenses.amount", "date": "expenses.date", "label": "Spending"}]}]}
signature = [
 {"name": "Weighted gradebook", "why": "homework, quizzes, projects and tests each count with your own weights, and the term grade follows your A-F scale", "where": "Students"},
 {"name": "At-risk alert", "why": "a student with a low average, too many absences or missing work is flagged before the report card", "where": "Students"},
 {"name": "Missing work tracker", "why": "every missing piece of work counts as zero and shows per student and per assignment", "where": "Scores"},
 {"name": "Attendance and lates", "why": "30-day attendance rate per student and absences by month", "where": "Attendance"},
 {"name": "Parent messages", "why": "ready WhatsApp messages for absence, missing work, good news, meetings and grades", "where": "Students"},
 {"name": "Printable progress report", "why": "averages by type, grade, attendance and every assignment of one student on one page", "where": "Progress Report"},
 {"name": "Score needed on the final", "why": "tells a student exactly what they need on the final to reach a grade", "where": "Final Score Needed"},
 {"name": "Classroom spending", "why": "what you paid from your own pocket and what the school still owes you", "where": "Classroom Spending"},
 {"name": "Trip permission slip", "why": "a slip filled from the trip details, plus a field-trip checklist with due dates", "where": "Permission Slip"},
 {"name": "Lesson plan", "why": "topic, objective, materials and homework for every lesson", "where": "Lesson Plan"}]
competitors = [
 {"what": "a typical gradebook template", "lacks": "no attendance, no parent contacts and no messages; missing work is not counted"},
 {"what": "a printable lesson planner", "lacks": "no grades, no averages and nothing that updates from your data"},
 {"what": "a free attendance sheet", "lacks": "no 30-day rate, no alerts and no link to grades or families"},
 {"what": "school management software", "lacks": "costs a subscription and is set up for the school, not for your own class"}]
guide = ["Open the Start sheet and type your school, your name, the class and the weight of each assessment type in the yellow cells.",
         "Set your grade scale (the lowest average for A, B, C and D) and the alerts for averages, absences and missing work.",
         "List your students on the Students sheet with a parent or guardian and a phone number with the country code.",
         "Add each homework, quiz, project and test on the Assignments sheet with its maximum points.",
         "Enter scores on the Scores sheet, one row per student per assignment. Mark missing or excused work in the Submission column.",
         "Take attendance on the Attendance sheet: one row per student per day.",
         "Log positive notes and issues on the Behavior Log, and every call or message on Parent Contacts.",
         "Plan your lessons on the Lesson Plan sheet and mark them taught or moved.",
         "Record what you buy for the class on Classroom Spending to see what the school owes you.",
         "Check the Class Dashboard and the Charts every week, and send a ready message from the Students sheet.",
         "Print the Progress Report, the Meeting Letter or the Permission Slip by choosing a student or a trip at the top of the sheet."]
listing = {"title": "Teacher Excel Template: Gradebook, Attendance, Lesson Plan, Parent Contacts, Missing Work Tracker, 15 Languages",
           "headline": "Teacher gradebook in Excel: weighted grades, attendance, parent messages",
           "tags": ["teacher planner", "gradebook excel", "teacher gradebook", "attendance tracker", "lesson plan", "classroom planner",
                    "grade calculator", "teacher binder", "student tracker", "parent contact log", "behavior tracker", "teacher template", "school planner"],
           "features": ["Weighted gradebook with your own A-F scale", "Attendance with 30-day rate and alerts", "Missing work counted and tracked per student",
                        "At-risk students flagged automatically", "Ready WhatsApp messages to parents", "Printable progress report",
                        "Score needed on the final and grade curve calculators", "Lesson plan, behavior log and parent contact log",
                        "Classroom spending and what the school owes you", "Trip permission slip and field-trip checklist"],
           "description": ("Run your class from one Excel workbook: a weighted gradebook, attendance, missing work, behavior notes, parent contacts, lesson plans "
                           "and your own classroom spending, with every average, grade and alert worked out for you.\n\n"
                           "Most teachers keep grades in one file, attendance on paper and parent calls in their head. Missing work slips through until the report "
                           "card, and nobody adds up what you spend on the class. ClassMark puts it all in one place.\n\n"
                           "WHAT IT DOES\n• Weighted term grade from homework, quizzes, projects and tests, with your own weights and A-F scale\n"
                           "• Missing work counts as zero and excused work is left out\n• Attendance rate and absences of the last 30 days for every student\n"
                           "• Students at risk flagged when the average, the absences or the missing work cross your limits\n"
                           "• Ready WhatsApp messages for an absence, missing work, good news, a meeting or a grade update\n"
                           "• Printable progress report with every assignment of one student, a meeting letter and a trip permission slip\n"
                           "• Score needed on the final, grade curve and marking time calculators\n• Lesson plan, behavior log and parent contact log with follow-up dates\n"
                           "• Classroom spending and what the school still owes you\n• Dashboard and charts: class average, attendance, missing work, contacts and spending\n\n"
                           "YOU RECEIVE a ZIP with the workbook in 15 languages and an English copy filled with sample data. Standard .xlsx files for Microsoft Excel "
                           "and LibreOffice. No macros, no subscription. Licence for one teacher.")}

# ---------------------------------------------------------------- v2 (owner 2026-11-10: «الخدمات لا تكفي، زدها إلى الضعف بطريقة إبداعية»)
T = {t["key"]: t for t in tables}
def col(t, k): return next(c for c in T[t]["columns"] if c["key"] == k)
def ins_after(t, after, new):
    cs = T[t]["columns"]; i = next(j for j, c in enumerate(cs) if c["key"] == after); cs[i + 1:i + 1] = new
settings += [{"key": "late_penalty", "label": "Share of the points taken off late work", "type": "pct", "default": 0.1},
             {"key": "retake_cap", "label": "Highest score a retake can earn", "type": "pct", "default": 0.85},
             {"key": "drop_alert", "label": "Fall in the 30-day average that triggers a warning", "type": "pct", "default": 0.08},
             {"key": "reading_goal", "label": "Reading minutes each student should log per month", "type": "int", "default": 300}]
lists += [L("area", "Support Area", [("reading", "Reading"), ("maths", "Maths"), ("behavior", "Behavior"), ("attendance", "Attendance"), ("language", "Language"), ("wellbeing", "Wellbeing")]),
          L("iv_status", "Plan Status", [("active", "Active"), ("met", "Goal met"), ("changed", "Changed"), ("stopped", "Stopped")]),
          L("loan_type", "Item Type", [("book", "Book"), ("device", "Laptop or tablet"), ("calculator", "Calculator"), ("kit", "Lab or sports kit"), ("other", "Other")]),
          L("conf_status", "Meeting Status", [("booked", "Booked"), ("held", "Held"), ("missed", "Missed"), ("moved", "Moved")]),
          L("event_type", "Calendar Type", [("trip", "Trip"), ("event", "Class event"), ("meeting", "Staff meeting"), ("duty", "Duty"), ("deadline", "Deadline"), ("training", "Training")])]
next(l for l in lists if l["key"] == "alert_level")["values"] += [{"key": "falling", "label": "Falling"}, {"key": "review", "label": "Review due"}, {"key": "overdue", "label": "Overdue"}]

# scores: late penalty and retakes (the better score counts, capped)
ins_after("scores", "points", [{"key": "retake", "label": "Retake points", "type": "num", "width": 9}])
ins_after("scores", "max", [{"key": "due", "label": "Due", "type": "calc", "format": "date", "width": 11, "formula": LOOK("assignments.due", "assignments.as_id", "assignment")},
                            {"key": "standard", "label": "Standard", "type": "calc", "format": "text", "width": 10, "formula": LOOK("assignments.standard", "assignments.as_id", "assignment")}])
RT = "IF({col:retake}=\"\",0,MIN({col:retake},{set:retake_cap}*{col:max}))"
col("scores", "pct")["formula"] = ("IF({col:status}=%s,\"\",IF(OR({col:max}=\"\",{col:max}=0),\"\",IF({col:status}=%s,%s/{col:max},IF({col:points}=\"\",\"\","
                                   "MAX(IF({col:status}=%s,{col:points}*(1-{set:late_penalty}),{col:points}),%s)/{col:max}))))") % (
                                   LV("sub_status", "excused"), LV("sub_status", "missing"), RT, LV("sub_status", "late"), RT)
T["scores"]["hint"] = "One row per student per assignment. Late work loses your penalty, missing work counts as zero, a retake counts when it is better (up to your cap) and excused work is left out."
for k, sc in enumerate(scores):
    if sc["points"] != "" and sc["points"] < 0.6 * next(a["max"] for a in assignments if a["as_id"] == sc["assignment"]) and k % 3 == 0:
        sc["retake"] = round(next(a["max"] for a in assignments if a["as_id"] == sc["assignment"]) * 0.78)
# behavior: merit points
ins_after("behavior", "type", [{"key": "points", "label": "Merit points", "type": "int", "width": 9}])
for b in behavior: b["points"] = {"positive": 2, "minor": -1, "major": -3}[b["type"]]
# lessons: an id, a resource link
T["lessons"]["columns"].insert(0, {"key": "ls_id", "label": "Lesson ID", "type": "text", "width": 9})
ins_after("lessons", "homework", [{"key": "link", "label": "Slides or resource link", "type": "link", "width": 22}])
for k, l in enumerate(lessons): l["ls_id"] = f"L-{301 + k}"; l["link"] = f"https://example.com/science/lesson-{301 + k}"
# students: handed-in rate, 30-day average, trend, merit, reading, open plans, report-card comment
S30 = "IFERROR(AVERAGEIFS({range:scores.pct},{range:scores.student},{col:st_id},{range:scores.due},%s),\"\")" % D30
ins_after("students", "grade", [
 {"key": "handed", "label": "Work handed in", "type": "calc", "format": "pct", "width": 10, "visual": "up",
  "formula": "IFERROR((COUNTIFS({range:scores.student},{col:st_id},{range:scores.status},%s)+COUNTIFS({range:scores.student},{col:st_id},{range:scores.status},%s))/(COUNTIFS({range:scores.student},{col:st_id})-COUNTIFS({range:scores.student},{col:st_id},{range:scores.status},%s)),\"\")" % (LV("sub_status", "submitted"), LV("sub_status", "late"), LV("sub_status", "excused"))},
 {"key": "recent", "label": "Average, last 30 days", "type": "calc", "format": "pct", "width": 11, "formula": S30},
 {"key": "trend", "label": "Trend", "type": "calc", "format": "text", "width": 10,
  "formula": "IF(AND(ISNUMBER({col:recent}),ISNUMBER({col:term})),IF({col:recent}<{col:term}-{set:drop_alert},%s,\"\"),\"\")" % AL("falling")},
 {"key": "merit", "label": "Merit points", "type": "calc", "format": "int", "width": 9, "formula": "SUMIFS({range:behavior.points},{range:behavior.student},{col:st_id})"},
 {"key": "reading_month", "label": "Reading minutes this month", "type": "calc", "format": "int", "width": 11,
  "formula": "SUMIFS({range:reading.minutes},{range:reading.student},{col:st_id},{range:reading.date},%s)" % MONTH0},
 {"key": "plans", "label": "Open support plans", "type": "calc", "format": "int", "width": 10,
  "formula": "COUNTIFS({range:interventions.student},{col:st_id},{range:interventions.status},%s)" % LV("iv_status", "active")},
 {"key": "comment", "label": "Report card comment", "type": "calc", "format": "text", "width": 40,
  "formula": "IFERROR(INDEX({range:comments.text},MATCH({col:grade},{range:comments.grade},0)),\"\")"}])
T["students"]["alerts"] += [{"column": "trend", "when": "= " + AL("falling"), "style": "bad"}, {"column": "reading_month", "when": "< {set:reading_goal}", "style": "warn"}]
# calendar: trips become one sheet for trips, events, meetings, duties and deadlines
T["trips"]["sheet"] = "Calendar"; T["trips"]["title"] = "Trips, events, meetings and duties"
T["trips"]["hint"] = "Everything with a date: trips, class events, staff meetings, duties and deadlines. Trips use the cost and slip columns."
ins_after("trips", "title", [{"key": "type", "label": "Type", "type": "list", "list": "event_type", "width": 13}])
col("trips", "ev_id")["label"] = "Item ID"; col("trips", "title")["label"] = "What"
for t in trips: t["type"] = "event" if t["cost"] == 0 and "evening" in t["title"].lower() or "fair" in t["title"].lower() or "week" in t["title"].lower() else "trip"
EXTRA = [("Lunch duty, playground", "duty", -3), ("Staff meeting", "meeting", 2), ("Report cards due", "deadline", 9), ("First aid training", "training", 12),
         ("Lunch duty, playground", "duty", 4), ("Department meeting", "meeting", 16), ("Exam papers to the office", "deadline", 5), ("Lunch duty, playground", "duty", 11),
         ("Staff meeting", "meeting", 30), ("Coursework marks deadline", "deadline", 24), ("Bus duty", "duty", 1), ("Safeguarding training", "training", -12)]
for k, (t, ty, d) in enumerate(EXTRA):
    trips.append({"ev_id": f"T-{13 + k:02d}", "title": t, "type": ty, "date": f"today{d:+d}", "place": "School", "cost": "", "slip_due": "", "plan_start": ""})
trips.sort(key=lambda r: int(r["date"][5:]))
# new sheets
iv = []
AREA = {"reading": ("Read 20 minutes a day and retell the story", "Daily guided reading with a partner"), "maths": ("Solve two-step problems without help", "Small-group practice twice a week"),
        "behavior": ("No more than one reminder per lesson", "Seat near the front and a daily check-in"), "attendance": ("Attendance above 95%", "Call home on the first absence"),
        "language": ("Use science words in full sentences", "Word bank and sentence starters"), "wellbeing": ("Talk to a trusted adult once a week", "Weekly check-in with the counsellor")}
for k, i in enumerate([1, 3, 7, 9, 11, 15, 17, 19, 20, 23, 5, 13]):
    ar = ["reading", "maths", "behavior", "attendance", "language", "wellbeing"][k % 6]; st = students[i]; d = -80 + k * 6
    iv.append({"iv_id": f"P-{11 + k}", "student": st["st_id"], "start": f"today{d:+d}", "area": ar, "goal": AREA[ar][0], "strategy": AREA[ar][1],
               "review": f"today{d + 42:+d}", "status": "met" if k in (0, 4) else "changed" if k == 7 else "active", "progress": ["Steady progress", "Small steps forward", "Needs more time", "Goal almost reached"][k % 4]})
reading = []
BOOKS = ["Wonder", "Holes", "The Wild Robot", "Hatchet", "A Boy Called Christmas", "The Explorer", "Coraline", "Kensuke's Kingdom", "Matilda", "The Iron Man", "Charlotte's Web", "Percy Jackson"]
for i, st in enumerate(students):
    for j in range(7):
        d = -62 + j * 9 + (i % 4)
        if d >= 0: continue
        reading.append({"date": f"today{d:+d}", "student": st["st_id"], "book": BOOKS[(i + j // 3) % len(BOOKS)], "pages": 10 + (i * 7 + j * 3) % 25,
                        "minutes": round(ABILITY[i] * 110 + (j % 3) * 15), "level": ["Level M", "Level N", "Level P", "Level R"][i % 4]})
loans = []
ITEMS = [("Science encyclopedia", "book"), ("Class laptop 07", "device"), ("Scientific calculator", "calculator"), ("Microscope kit", "kit"), ("Novel: Holes", "book"),
         ("Tablet 03", "device"), ("Graphing calculator", "calculator"), ("Football and cones", "kit"), ("Atlas", "book"), ("Class laptop 12", "device"),
         ("Novel: Wonder", "book"), ("Magnet kit", "kit"), ("Dictionary", "book"), ("Tablet 05", "device")]
for k, (it, ty) in enumerate(ITEMS):
    st = students[(k * 5 + 2) % 24]; o = -40 + k * 3
    loans.append({"ln_id": f"B-{41 + k}", "item": it, "type": ty, "student": st["st_id"], "out": f"today{o:+d}", "due": f"today{o + 14:+d}",
                  "returned": f"today{o + 10:+d}" if k % 3 == 0 and o + 10 < 0 else ""})
conferences = []
for k in range(16):
    st = students[(k * 3 + 1) % 24]; d = -30 + k * 3
    conferences.append({"cf_id": f"M-{51 + k}", "student": st["st_id"], "booked": f"today{d - 7:+d}", "date": f"today{d:+d}", "time": ["15:30", "15:45", "16:00", "16:15", "16:30"][k % 5],
                        "with": ["Mother", "Father", "Both parents", "Guardian"][k % 4], "status": "held" if d < 0 and k % 5 else "missed" if d < 0 else "booked",
                        "notes": "Agreed a reading plan" if d < 0 and k % 5 else ""})
comments = [{"grade": "ga", "text": "An excellent term: careful, curious and always ready to help others."},
            {"grade": "gb", "text": "A strong term with good effort. Keep checking your work to reach the top grade."},
            {"grade": "gc", "text": "Steady progress. Hand in every piece of work on time to move up a grade."},
            {"grade": "gd", "text": "Some good moments, but missing work is holding you back. Let's make a plan together."},
            {"grade": "gf", "text": "This term was difficult. We will meet with your family to agree how to catch up."},
            {"grade": "ga", "text": "Outstanding results and leadership in group work."}, {"grade": "gb", "text": "Good understanding; take more care with explanations."},
            {"grade": "gc", "text": "You can do more: ask for help early when something is unclear."}, {"grade": "gd", "text": "Attend every lesson and use the catch-up sessions."},
            {"grade": "gf", "text": "Let's work with your family on a support plan for next term."}]
PH = lambda t: [{"key": "s_name", "label": "Student", "type": "calc", "format": "text", "width": 20, "formula": LOOK("students.name", "students.st_id", "student")},
                {"key": "guardian", "label": "Parent or guardian", "type": "calc", "format": "text", "width": 20, "formula": LOOK("students.guardian", "students.st_id", "student")},
                {"key": "phone", "label": "Phone", "type": "calc", "format": "text", "width": 16, "formula": LOOK("students.phone", "students.st_id", "student")}]
tables += [
 {"key": "interventions", "sheet": "Support Plans", "title": "Support plans", "hint": "Extra help for a student: the goal, what you do, the review date and how it is going.", "rows": 300,
  "columns": [{"key": "iv_id", "label": "Plan ID", "type": "text", "width": 9}, {"key": "student", "label": "Student ID", "type": "ref", "ref": "students.st_id", "width": 11, "required": True},
              {"key": "start", "label": "Started", "type": "date", "width": 12}, {"key": "area", "label": "Area", "type": "list", "list": "area", "width": 12},
              {"key": "goal", "label": "Goal", "type": "text", "width": 30}, {"key": "strategy", "label": "What you do", "type": "text", "width": 30},
              {"key": "review", "label": "Review on", "type": "date", "width": 12}, {"key": "status", "label": "Status", "type": "list", "list": "iv_status", "width": 11},
              {"key": "progress", "label": "Progress", "type": "text", "width": 22}] + PH("interventions") + [
              {"key": "flag", "label": "Alert", "type": "calc", "format": "text", "width": 11,
               "formula": "IF(OR({col:review}=\"\",{col:status}<>%s),\"\",IF({col:review}<{today},%s,IF({col:review}-{today}<=7,%s,%s)))" % (LV("iv_status", "active"), AL("overdue"), AL("review"), AL("ok"))}],
  "alerts": [{"column": "flag", "when": "= " + AL("overdue"), "style": "bad"}, {"column": "flag", "when": "= " + AL("review"), "style": "warn"}, {"column": "status", "when": "= " + LV("iv_status", "met"), "style": "good"}],
  "demo": iv},
 {"key": "reading", "sheet": "Reading Log", "title": "Reading log", "hint": "Books, pages and minutes each student reads. The monthly total is compared with your goal.", "rows": 3000,
  "columns": [{"key": "date", "label": "Date", "type": "date", "width": 12, "required": True}, {"key": "student", "label": "Student ID", "type": "ref", "ref": "students.st_id", "width": 11},
              {"key": "book", "label": "Book", "type": "text", "width": 24}, {"key": "pages", "label": "Pages", "type": "int", "width": 8}, {"key": "minutes", "label": "Minutes", "type": "int", "width": 9},
              {"key": "level", "label": "Reading level", "type": "text", "width": 11},
              {"key": "s_name", "label": "Student", "type": "calc", "format": "text", "width": 20, "formula": LOOK("students.name", "students.st_id", "student")}],
  "alerts": [], "demo": reading},
 {"key": "loans", "sheet": "Loans", "title": "Books and equipment lent", "hint": "What a student borrowed from the class, when it is due back, and a reminder message when it is late.", "rows": 500,
  "columns": [{"key": "ln_id", "label": "Loan ID", "type": "text", "width": 9}, {"key": "item", "label": "Item", "type": "text", "width": 24, "required": True},
              {"key": "type", "label": "Type", "type": "list", "list": "loan_type", "width": 15}, {"key": "student", "label": "Student ID", "type": "ref", "ref": "students.st_id", "width": 11},
              {"key": "out", "label": "Lent on", "type": "date", "width": 12}, {"key": "due", "label": "Due back", "type": "date", "width": 12}, {"key": "returned", "label": "Returned on", "type": "date", "width": 12}] + PH("loans") + [
              {"key": "flag", "label": "Alert", "type": "calc", "format": "text", "width": 10,
               "formula": "IF(OR({col:item}=\"\",{col:returned}<>\"\",{col:due}=\"\"),\"\",IF({col:due}<{today},%s,%s))" % (AL("overdue"), AL("ok"))}],
  "alerts": [{"column": "flag", "when": "= " + AL("overdue"), "style": "bad"}], "demo": loans},
 {"key": "conferences", "sheet": "Parent Meetings", "title": "Parent meetings", "hint": "Book parent-teacher meetings, send the reminder and keep what you agreed.", "rows": 300,
  "columns": [{"key": "cf_id", "label": "Meeting ID", "type": "text", "width": 10}, {"key": "student", "label": "Student ID", "type": "ref", "ref": "students.st_id", "width": 11, "required": True},
              {"key": "booked", "label": "Booked on", "type": "date", "width": 12}, {"key": "date", "label": "Meeting date", "type": "date", "width": 12}, {"key": "time", "label": "Time", "type": "text", "width": 8},
              {"key": "with", "label": "With", "type": "text", "width": 13}, {"key": "status", "label": "Status", "type": "list", "list": "conf_status", "width": 10},
              {"key": "notes", "label": "What we agreed", "type": "text", "width": 28}] + PH("conferences") + [
              {"key": "days", "label": "Days to go", "type": "calc", "format": "int", "width": 9, "formula": "IF({col:date}=\"\",\"\",{col:date}-{today})"}],
  "alerts": [{"column": "status", "when": "= " + LV("conf_status", "missed"), "style": "bad"}, {"column": "days", "when": "= 0", "style": "good"}], "demo": conferences},
 {"key": "comments", "sheet": "Comment Bank", "title": "Report card comments", "hint": "One comment per grade (the first row of each grade is used). Students get the comment of their grade on the progress report.", "rows": 100,
  "columns": [{"key": "grade", "label": "Grade", "type": "list", "list": "grade", "width": 8, "required": True}, {"key": "text", "label": "Comment", "type": "text", "width": 70}],
  "alerts": [], "demo": comments},
]
dashboard["kpis"] += [
 {"label": "Students with a falling average", "formula": "COUNTIFS({range:students.trend},%s)" % AL("falling"), "format": "int"},
 {"label": "Work handed in", "formula": "IFERROR(AVERAGE({range:students.handed}),\"\")", "format": "pct"},
 {"label": "Support plans due for review", "formula": "COUNTIFS({range:interventions.flag},%s)+COUNTIFS({range:interventions.flag},%s)" % (AL("review"), AL("overdue")), "format": "int"},
 {"label": "Reading minutes this month", "formula": "SUMIFS({range:reading.minutes},{range:reading.date},%s)" % MONTH0, "format": "int"},
 {"label": "Books and equipment overdue", "formula": "COUNTIFS({range:loans.flag},%s)" % AL("overdue"), "format": "int"},
 {"label": "Parent meetings in the next 7 days", "formula": "COUNTIFS({range:conferences.date},\">=\"&{today},{range:conferences.date},\"<=\"&({today}+7))", "format": "int"},
 {"label": "Calendar items in the next 7 days", "formula": "COUNTIFS({range:trips.date},\">=\"&{today},{range:trips.date},\"<=\"&({today}+7))", "format": "int"}]
insights["gauges"].append({"title": "Support plans that met their goal", "num": {"agg": "count", "table": "interventions", "where": [{"column": "status", "op": "=", "value": LV("iv_status", "met")}]}, "den": {"agg": "count", "table": "interventions"}})
insights["charts"] += [
 {"title": "Reading minutes by month", "type": "column", "by": "month", "series": [{"agg": "sum", "table": "reading", "value": "reading.minutes", "date": "reading.date", "label": "Minutes"}]},
 {"title": "Missing work by assignment type", "type": "bar", "by": "assignments.category", "series": [{"agg": "sum", "table": "assignments", "value": "assignments.missing", "label": "Missing"}]},
 {"title": "Merit points by note type", "type": "bar", "by": "behavior.type", "series": [{"agg": "sum", "table": "behavior", "value": "behavior.points", "label": "Merit points"}]},
 {"title": "Support plans by area", "type": "bar", "by": "interventions.area", "series": [{"agg": "count", "table": "interventions", "label": "Plans"}]},
 {"title": "Calendar by type", "type": "doughnut", "by": "trips.type", "series": [{"agg": "count", "table": "trips", "label": "Items"}]}]
forms[0]["fields"] += [{"label": "Average, last 30 days", "value": "students.recent"}, {"label": "Work handed in", "value": "students.handed"},
                       {"label": "Merit points", "value": "students.merit"}, {"label": "Reading minutes this month", "value": "students.reading_month"},
                       {"label": "Teacher's comment", "value": "students.comment"}]
forms.append({"key": "student_file", "sheet": "Student File", "title": "Student file", "pick": "students.st_id",
              "fields": [{"label": "Student", "value": "students.name"}, {"label": "Parent or guardian", "value": "students.guardian"}, {"label": "Relation", "value": "students.relation"},
                         {"label": "Phone", "value": "students.phone"}, {"label": "E-mail", "value": "students.email"}, {"label": "Support plan", "value": "students.support"},
                         {"label": "Notes (health, seating)", "value": "students.notes"}, {"label": "Open support plans", "value": "students.plans"},
                         {"label": "Last parent contact", "value": "students.last_contact"}, {"label": "Merit points", "value": "students.merit"}],
              "lines": {"from": "contacts", "match": "contacts.student", "columns": ["date", "way", "reason", "summary", "follow_up"], "max": 20}})
GL = (LV("grade", "ga"), LV("grade", "gb"), LV("grade", "gc"), LV("grade", "gd"), LV("grade", "gf"))
LET = lambda x: "IF(%s>={set:grade_a},%s,IF(%s>={set:grade_b},%s,IF(%s>={set:grade_c},%s,IF(%s>={set:grade_d},%s,%s))))" % (x, GL[0], x, GL[1], x, GL[2], x, GL[3], GL[4])
RUB = "({in:c1}+{in:c2}+{in:c3}+{in:c4})/(4*{in:levels})"
tools += [
 {"key": "rubric", "sheet": "Rubric Scorer", "title": "Rubric scorer", "hint": "Score four criteria of a rubric and get the points, the percent and the grade.",
  "inputs": [{"key": "levels", "label": "Highest level of the rubric", "type": "int", "default": 4}, {"key": "c1", "label": "Criterion 1: content", "type": "int", "default": 3},
             {"key": "c2", "label": "Criterion 2: method", "type": "int", "default": 4}, {"key": "c3", "label": "Criterion 3: presentation", "type": "int", "default": 2},
             {"key": "c4", "label": "Criterion 4: teamwork", "type": "int", "default": 3}, {"key": "points", "label": "Points the task is worth", "type": "num", "default": 40}],
  "outputs": [{"label": "Rubric score %", "format": "pct", "formula": "IFERROR(%s,\"\")" % RUB}, {"label": "Points earned", "format": "num", "formula": "IFERROR(ROUND(%s*{in:points},1),\"\")" % RUB},
              {"label": "Grade", "format": "text", "formula": "IFERROR(%s,\"\")" % LET(RUB)}]},
 {"key": "converter", "sheet": "Grade Converter", "title": "Grade converter", "hint": "Turn a percent into your letter grade and 4-point grade points, and see how far the next grade is.",
  "inputs": [{"key": "score", "label": "Score %", "type": "pct", "default": 0.77}],
  "outputs": [{"label": "Letter grade", "format": "text", "formula": LET("{in:score}")},
              {"label": "Grade points (4.0 scale)", "format": "num", "formula": "IF({in:score}>={set:grade_a},4,IF({in:score}>={set:grade_b},3,IF({in:score}>={set:grade_c},2,IF({in:score}>={set:grade_d},1,0))))"},
              {"label": "Points to the next grade", "format": "pct", "formula": "IF({in:score}>={set:grade_a},0,IF({in:score}>={set:grade_b},{set:grade_a},IF({in:score}>={set:grade_c},{set:grade_b},IF({in:score}>={set:grade_d},{set:grade_c},{set:grade_d}))))-{in:score}"}]},
 {"key": "mastery", "sheet": "Standard Mastery", "title": "Mastery of a standard", "hint": "Type a standard or unit code from the Assignments sheet to see how the class did on it.",
  "inputs": [{"key": "std", "label": "Standard or unit code", "type": "text", "default": "PS3.A"}],
  "outputs": [{"label": "Assignments on this standard", "format": "int", "formula": "COUNTIFS({range:assignments.standard},{in:std})"},
              {"label": "Class average on this standard", "format": "pct", "formula": "IFERROR(AVERAGEIFS({range:scores.pct},{range:scores.standard},{in:std}),\"\")"},
              {"label": "Scores below grade D", "format": "int", "formula": "COUNTIFS({range:scores.standard},{in:std},{range:scores.pct},\"<\"&{set:grade_d})"},
              {"label": "Missing work on this standard", "format": "int", "formula": "COUNTIFS({range:scores.standard},{in:std},{range:scores.status},%s)" % LV("sub_status", "missing")}]}]
messages += [
 {"key": "falling", "moment": "Falling results", "table": "students", "phone": "students.phone", "text": "Hello {guardian}, {name}'s results in the last few weeks are lower than usual. Could we work on this together? I am happy to talk."},
 {"key": "reading", "moment": "Reading", "table": "students", "phone": "students.phone", "text": "Hello {guardian}, {name} read for {reading_month} minutes this month. Thank you for reading together at home!"},
 {"key": "issue", "moment": "Behavior", "table": "students", "phone": "students.phone", "text": "Hello {guardian}, I need to tell you about something that happened in class with {name} today. Please call me when you can."},
 {"key": "meet_rem", "moment": "Meeting reminder", "table": "conferences", "phone": "conferences.phone", "text": "Hello {guardian}, a reminder of our meeting about {s_name} on {date} at {time}. See you then!"},
 {"key": "loan_rem", "moment": "Return reminder", "table": "loans", "phone": "loans.phone", "text": "Hello {guardian}, {s_name} borrowed {item} from our class. Please help bring it back by {due}. Thank you."},
 {"key": "plan_upd", "moment": "Support plan", "table": "interventions", "phone": "interventions.phone", "text": "Hello {guardian}, an update on {s_name}'s support plan: {progress}. Next review: {review}."}]
documents += [
 {"key": "certificate", "sheet": "Certificate", "title": "Certificate of achievement", "pick": "students.st_id",
  "paragraphs": ["This certificate is awarded to {col:students.name}", "for great effort and {col:students.merit} merit points this term.", "Well done, and keep it up!"],
  "sign": ["Teacher", "Head teacher"], "note": "Print on card. Choose any student at the top."},
 {"key": "cover_plan", "sheet": "Cover Plan", "title": "Plan for a cover teacher", "pick": "lessons.ls_id",
  "paragraphs": ["Lesson {col:lessons.ls_id} on {col:lessons.date}, {col:lessons.period}.", "Topic: {col:lessons.topic}. Learning objective: {col:lessons.objective}.",
                 "Materials: {col:lessons.materials}. Homework to set: {col:lessons.homework}.", "Slides or resources: {col:lessons.link}",
                 "Seating plan and class notes are on the Students sheet. Please leave a short note on how the lesson went."],
  "sign": ["Class teacher", "Cover teacher"], "note": "Choose the lesson from the Lesson Plan sheet."}]
checklists += [
 {"key": "meeting_prep", "title": "Meeting preparation", "table": "conferences", "start": "conferences.booked",
  "steps": [{"label": "Confirm the time with the family", "days": 0}, {"label": "Print the progress report and the student file", "days": 3}, {"label": "Pick two pieces of work to show", "days": 4},
            {"label": "Write two strengths and two goals", "days": 5}, {"label": "Send the meeting reminder", "days": 6}, {"label": "Meeting day", "days": 7}, {"label": "Send a short summary to the family", "days": 8}]},
 {"key": "support_plan", "title": "Support plan steps", "table": "interventions", "start": "interventions.start",
  "steps": [{"label": "Share the plan with the family", "days": 1}, {"label": "Start the strategy in class", "days": 2}, {"label": "First check: is it working?", "days": 14},
            {"label": "Update the family", "days": 21}, {"label": "Review: continue, change or close the plan", "days": 42}]}]
signature[:] = [
 {"name": "Weighted gradebook with late penalty and retakes", "why": "your own weights and A-F scale; late work loses your penalty and a better retake counts, up to your cap", "where": "Scores"},
 {"name": "Early warning", "why": "students at risk by average, absences or missing work, and a warning when the 30-day average falls", "where": "Students"},
 {"name": "Missing work tracker", "why": "missing work counts as zero and shows per student, per assignment and per standard", "where": "Scores"},
 {"name": "Attendance and lates", "why": "30-day attendance rate per student and absences by month", "where": "Attendance"},
 {"name": "11 ready parent messages", "why": "absence, missing work, good news, falling results, reading, meetings, loans and support plans on WhatsApp", "where": "Students"},
 {"name": "Support plans with review dates", "why": "goal, strategy and review date for every plan, with a checklist and an alert when the review is due", "where": "Support Plans"},
 {"name": "Reading log", "why": "minutes and books per student against your monthly reading goal", "where": "Reading Log"},
 {"name": "Automatic report card comments", "why": "your comment bank gives each student the comment of their grade on the progress report", "where": "Comment Bank"},
 {"name": "Parent meetings", "why": "booking, reminder message, preparation checklist and what you agreed", "where": "Parent Meetings"},
 {"name": "Six teacher calculators", "why": "score needed on the final, grade curve, marking time, rubric scorer, grade converter and standard mastery", "where": "Rubric Scorer"},
 {"name": "Printables", "why": "progress report, student file, meeting letter, permission slip, certificate and a cover plan for the substitute teacher", "where": "Cover Plan"},
 {"name": "Loans, spending and calendar", "why": "books and devices lent with return reminders, what the school owes you, and every duty, meeting and deadline", "where": "Calendar"}]
competitors += [{"what": "a teacher planner printable", "lacks": "no support plans, no reading log, no loans and no report card comments"}]
guide[:] = ["Open the Start sheet and type your school, your name, the class and the weight of each assessment type in the yellow cells.",
            "Set your grade scale, the late penalty, the retake cap, the reading goal and the alerts for averages, absences and missing work.",
            "List your students on the Students sheet with a parent or guardian and a phone number with the country code.",
            "Add each homework, quiz, project and test on the Assignments sheet with its maximum points and its standard or unit.",
            "Enter scores on the Scores sheet, one row per student per assignment. Mark late, missing or excused work, and add retake points when a student redoes it.",
            "Take attendance on the Attendance sheet: one row per student per day.",
            "Log merit points and issues on the Behavior Log, reading on the Reading Log and every call or message on Parent Contacts.",
            "Open a support plan for a student who needs extra help, with a goal and a review date.",
            "Book parent meetings on Parent Meetings and send the reminder from the same row.",
            "Plan your lessons on the Lesson Plan sheet; print the Cover Plan for a substitute teacher when you are away.",
            "Record books and devices you lend on Loans, and what you buy for the class on Classroom Spending.",
            "Put duties, meetings, deadlines and trips on the Calendar.",
            "Write one comment per grade on the Comment Bank; each student's comment appears on the progress report.",
            "Check the Class Dashboard and the Charts every week, and send ready messages from the Students sheet.",
            "Print the Progress Report, Student File, Meeting Letter, Permission Slip or Certificate by choosing a student, a trip or a lesson at the top."]
listing["title"] = "Teacher Excel Template: Gradebook, Attendance, Lesson Plan, Parent Contacts, Support Plans, Reading Log, 15 Languages"
listing["features"] = ["Weighted gradebook with late penalty, retakes and your A-F scale", "Early warning: at-risk students and falling averages",
                       "Attendance with 30-day rate and absences by month", "11 ready WhatsApp messages to parents", "Support plans with review dates and checklists",
                       "Reading log against a monthly goal", "Automatic report card comments from your comment bank", "Parent meetings with reminders and a preparation checklist",
                       "6 calculators: final score, curve, marking, rubric, grades, mastery",
                       "Progress report, student file, certificate, cover plan and more", "Loans, classroom spending and a calendar of duties and deadlines",
                       "Dashboard with 23 key figures and 11 charts"]
listing["description"] = ("Run your class from one Excel workbook: a weighted gradebook, attendance, missing work, support plans, reading, parent contacts and meetings, "
    "lesson plans, loans and your own classroom spending, with every average, grade and alert worked out for you.\n\n"
    "Most teachers keep grades in one file, attendance on paper and parent calls in their head. Missing work and falling results are noticed too late, and "
    "nobody adds up what you spend on the class. ClassMark puts it all in one place.\n\n"
    "WHAT IT DOES\n"
    "• Weighted term grade from homework, quizzes, projects and tests, with your weights and A-F scale\n"
    "• Late work loses your penalty, a better retake counts up to your cap, missing work counts as zero\n"
    "• Early warning: students at risk, and a warning when the 30-day average falls\n"
    "• Attendance rate and absences of the last 30 days for every student\n"
    "• 11 ready WhatsApp messages: absence, missing work, good news, falling results, reading, meetings, loans, support plans\n"
    "• Support plans with goals, review dates, alerts and a checklist\n"
    "• Reading log against your monthly goal, merit points and a behavior log\n"
    "• Report card comments filled in from your own comment bank\n"
    "• Parent meetings with reminders, a preparation checklist and what you agreed\n"
    "• Calculators: score needed on the final, grade curve, marking time, rubric scorer, grade converter, standard mastery\n"
    "• Printables: progress report, student file, meeting letter, permission slip, certificate, cover plan for a substitute teacher\n"
    "• Loans of books and devices, classroom spending and what the school owes you, and a calendar of duties, meetings and deadlines\n"
    "• Dashboard and charts: class average, attendance, missing work, reading, support plans, contacts and spending\n\n"
    "YOU RECEIVE a ZIP with the workbook in 15 languages and an English copy filled with sample data. Standard .xlsx files for Microsoft Excel and LibreOffice. "
    "No macros, no subscription. Licence for one teacher.")

spec = {"fx": 1, "id": "fx-20261110-2000-classroom-teacher", "slug": "teacher-gradebook-attendance-planner", "profession": "Classroom teacher",
        "name": "ClassMark Teacher Planner", "tagline": "Grades, attendance, support plans and parent messages in one Excel file", "price_usd": 29,
        "colors": {"primary": "#1F4E6E", "accent": "#E8A33D"}, "settings": settings, "lists": lists, "tables": tables, "dashboard": dashboard, "forms": forms,
        "guide": guide, "listing": listing, "insights": insights, "suite": {"key": "fx-20261110-2000-classroom-teacher", "part": 1, "of": 1, "focus": "Grades, attendance, families and lessons of one class"},
        "signature": signature, "competitors": competitors, "tools": tools, "messages": messages, "documents": documents, "checklists": checklists, "i18n": {}}
json.dump(spec, open('/home/user/tc/tc.en.json', 'w'), ensure_ascii=False, indent=1)
print({t['key']: len(t['demo']) for t in tables})
