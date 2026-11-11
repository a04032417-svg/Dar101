"""English pre-edit: replaces ambiguous words with unambiguous ones before machine translation (the translator is blind to context).
Only the text sent to the translator changes; the product keeps its English text. Placeholders are never touched."""
import re
PH = re.compile(r'\{[a-z_]+(?::[a-z0-9_.]+)?\}')
EXACT = {
 'Core': 'Core muscles', 'Core brace': 'Trunk bracing exercise', 'Core client': 'Loyal client', 'Core sets per week': 'Core muscles sets per week',
 'Chest': 'Chest muscles', 'Chest sets per week': 'Chest muscles sets per week', 'Shoulders': 'Shoulder muscles', 'Shoulders sets per week': 'Shoulder muscles sets per week',
 'Arms': 'Arm muscles', 'Hip hinge': 'Hip hinge movement', 'Carry': 'Loaded carry', 'Push': 'Pushing movement', 'Pull': 'Pulling movement',
 'Horizontal push': 'Horizontal pushing movement', 'Vertical push': 'Vertical pushing movement', 'Horizontal pull': 'Horizontal pulling movement', 'Vertical pull': 'Vertical pulling movement',
 'Missing': 'Not on file', 'Programme Split': 'Training plan structure', 'Split': 'Structure', 'Offer to split the balance into two payments': 'Offer to divide the balance into two payments',
 'Opening check': 'Opening inspection', 'Closing check': 'Closing inspection', 'Margin check': 'Margin review', 'Cash check': 'Cash review', 'Discount Check': 'Discount Review',
 'Contact details check': 'Contact details verification', 'Safety Check Type': 'Safety inspection type', 'Safety Checks': 'Safety Inspections', 'Item or check': 'Item or inspection',
 'Next check': 'Next inspection', 'Check ID': 'Inspection ID', 'Check every, days': 'Inspect every, days', 'Check Card': 'Inspection Card', 'Safety checks due soon or overdue': 'Safety inspections due soon or overdue',
 'Safety checks in date': 'Safety inspections in date', 'Safety check dates': 'Safety inspection dates', 'First aid, emergency and facility check dates': 'First aid, emergency and facility inspection dates',
 'First aid, emergency equipment and facility checks': 'First aid, emergency equipment and facility inspections', 'Opening, closing and cleaning check card': 'Opening, closing and cleaning inspection card',
 'Weekly volume check per muscle group': 'Weekly volume review per muscle group', 'Trial session and a short health check': 'Trial session and a short health screening',
 'Record the check on the Cleaning Log': 'Record the inspection on the Cleaning Log', 'Lock up and record the check on the Cleaning Log': 'Lock up and record the inspection on the Cleaning Log',
 'Bookings, check-in and slot use': 'Bookings, arrival check-in and time slot use', 'Session card with check-in': 'Session card with arrival check-in',
 'Days of cover': 'Days the stock lasts', 'Months of spending the cash covers': 'Months of spending your cash can pay for', 'Leave and shift cover with slots to cover': 'Time off and substitute shifts with time slots to fill',
 'No cover': 'No substitute', 'Covered': 'Substitute found', 'Leave and Cover': 'Time Off and Substitutes', 'Coach leave and shift cover': 'Trainer time off and substitute shifts',
 'Cover coach': 'Substitute trainer', 'Slots to cover': 'Time slots to fill', 'Cover': 'Substitute', 'Cover phone': 'Substitute phone', 'Cover request': 'Substitute request',
 'Cover thank you': 'Thank-you to the substitute', 'Cover Handover': 'Substitute Handover', 'Leave and cover handover': 'Time off and substitute handover', 'Leave Cover Plan': 'Time Off Plan',
 'Choose the cover coach': 'Choose the substitute trainer', 'Brief the cover coach on clients and kit': 'Brief the substitute trainer on clients and equipment',
 'Confirm the cover by message': 'Confirm the substitute by message', 'Leave starts, check the timetable shows the cover': 'Time off starts, check the timetable shows the substitute',
 'Ask clients how the cover went': 'Ask clients how the substitute coaching went', 'Quantity needed to reach your cover': 'Quantity needed to reach your target days of stock',
 'Wanted coach': 'Requested trainer', 'Wanted times': 'Requested times', 'Walk-in or drop-in': 'Walk-in or single visit', 'Equipment Repair Round': 'Equipment Repair Tour',
 'Event Run Sheet': 'Event Schedule Sheet', 'Plateau': 'Stalled progress', 'Records and Plateaus': 'Records and Stalled Progress', 'Plateau talk': 'Stalled progress talk',
 'Annual leave': 'Annual time off', 'Sick leave': 'Sick days', 'Leave Type': 'Time-off type', 'Leave ID': 'Time-off ID', 'Leave days, next 30 days': 'Time-off days, next 30 days', 'Coach on leave': 'Trainer on time off',
 'Agree the leave dates': 'Agree the time-off dates', 'Heart rate reserve': 'Heart rate reserve',
}
RULES = [  # (regex, replacement) — applied in order to the text between placeholders
 (r'\bcoach load\b', 'trainer workload'), (r'\bCoach Load\b', 'Trainer Workload'), (r'\bTeam hours, load and\b', 'Team hours, workload and'),
 (r'\bdeload weeks?\b', 'recovery week'), (r'\bDeload weeks?\b', 'Recovery week'), (r'\bdeload\b', 'recovery week'), (r'\bDeload\b', 'Recovery week'),
 (r'\b(Heaviest|Normal working|Total|Smallest jump in|Estimated max for 5 reps at that|Change from the) load\b', r'\1 weight'),
 (r'\bplateaued\b', 'stalled'), (r'\bplateaus?\b', 'stalled progress'), (r'\bPlateaus?\b', 'Stalled progress'),
 (r'\bcheck-ins\b', 'progress updates'), (r'\bCheck-ins\b', 'Progress updates'), (r'\bcheck-in\b', 'progress update'), (r'\bCheck-in\b', 'Progress update'),
 (r'\btrial-to-package\b', 'trial session to package'), (r'\bTrial-to-package\b', 'Trial session to package'),
 (r'\btrials\b', 'trial sessions'), (r'\bTrials\b', 'Trial sessions'), (r'\btrial\b(?! session)', 'trial session'), (r'\bTrial\b(?! session)', 'Trial session'),
 (r'\bcoaches\b', 'trainers'), (r'\bCoaches\b', 'Trainers'), (r'\bcoach\b', 'trainer'), (r'\bCoach\b', 'Trainer'),
 (r'\blead time\b', 'delivery time'), (r'\bleads\b', 'prospects'), (r'\bLeads\b', 'Prospects'), (r'\blead\b', 'prospect'), (r'\bLead\b', 'Prospect'),
 (r'\blifts\b', 'exercises'), (r'\bLifts\b', 'Exercises'), (r'\blift\b', 'exercise'), (r'\bLift\b', 'Exercise'),
 (r'\bplates\b', 'weight plates'), (r'\bPlates\b', 'Weight plates'), (r'\bplate\b', 'weight plate'), (r'\bPlate\b', 'Weight plate'),
 (r'(?<!aid )\bkit\b', 'equipment'), (r'(?<!aid )\bKit\b', 'Equipment'),
 (r'\bQuads\b', 'Quadriceps'), (r'\bCalves\b', 'Calf muscles'), (r'\bHamstrings\b', 'Hamstring muscles'), (r'\bGlutes\b', 'Gluteal muscles'),
 (r'(?<!to )(?<!really )\bloads\b', 'weights'), (r'(?<!to )(?<!really )\bLoads\b', 'Weights'), (r'(?<!to )(?<!really )\bload\b', 'weight'), (r'(?<!to )(?<!really )\bLoad\b', 'Weight'),
 (r'\bfreezes\b', 'pauses'), (r'\bFreezes\b', 'Pauses'), (r'\bfreeze\b', 'pause'), (r'\bFreeze\b', 'Pause'),
 (r'\bwaivers\b', 'liability waivers'), (r'\bwaiver\b', 'liability waiver'), (r'\bWaiver\b', 'Liability waiver'),
 (r'\bslots\b', 'time slots'), (r'\bSlots\b', 'Time slots'), (r'\bslot\b', 'time slot'), (r'\bSlot\b', 'Time slot'),
 (r'\bprogrammes\b', 'training plans'), (r'\bProgrammes\b', 'Training plans'), (r'\bprogramme\b', 'training plan'), (r'\bProgramme\b', 'Training plan'),
 (r'\bno-shows\b', 'missed bookings'), (r'\bNo-shows\b', 'Missed bookings'), (r'\bno-show\b', 'missed booking'), (r'\bNo-show\b', 'Missed booking'),
 (r'(?<!one-)\breps\b', 'repetitions'), (r'(?<!one-)\bReps\b', 'Repetitions'),
 (r'(?<!clients )(?<!who )(?<!to )(?<!they )(?<!coaches )(?<!trainers )\bleave\b(?! idle)', 'time off'), (r'(?<!clients )(?<!who )(?<!to )(?<!they )\bLeave\b', 'Time off'),
]
COACH = {r'\bcoaches\b', r'\bCoaches\b', r'\bcoach\b', r'\bCoach\b'}
CRULES = [(re.compile(a), b, a in COACH) for a, b in RULES]
SMALL = {'and', 'of', 'to', 'a', 'an', 'the', 'in', 'for', 'vs', 'or', 'per', 'by', 'on', 'with', 'from', 'at'}


def sentence_case(t, force=False):
    w = t.split(' ')
    if len(w) < 2: return t
    rest = [x for x in w[1:] if x.lower() not in SMALL and x[:1].isalpha()]
    if not rest or not (force or all(x[:1].isupper() for x in rest)): return t
    return ' '.join([w[0]] + [x if (x.lower() in SMALL or x[1:] != x[1:].lower() or x in ('I',)) else x.lower() for x in w[1:]])


def rewrite(en, kind='sentence', trainer=True):
    if en in EXACT: r = EXACT[en]
    else:
        parts = PH.split(en); phs = PH.findall(en)
        out = []
        for p in parts:
            for rx, rp, is_coach in CRULES:
                if is_coach and not trainer: continue
                p = rx.sub(rp, p)
            out.append(p)
        r = ''.join(x + (phs[i] if i < len(phs) else '') for i, x in enumerate(out))
    if kind in ('sheet', 'label', 'title', 'list', 'setting'): r = sentence_case(r, force=(kind == 'sheet'))
    if not trainer: r = r.replace('trainers', 'coaches').replace('trainer', 'coach').replace('Trainers', 'Coaches').replace('Trainer', 'Coach')
    return r
