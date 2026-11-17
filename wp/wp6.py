"""Wedding Planning suite - part 6: Wedding Party and Day-Of Run-of-Show."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp6_lists import *
from wp6_tables import settings, tables, NS, ORD, ARR, FITD, READY, DONE, W_AG, W_VE, PL_H, PL_V, PL_T, ID, RS, RE, VEND_MIN, PLAN_END, PLAN_START, OVER_MIN, HMT, R as R_
from wp6_tools import tools
import wp6_data as D

SUITE = 'fx-20261116-wedding'
NOTE = "Sample wording: adapt it to your own wedding."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c_): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c_, t, idc)
def R(t, c_): return '{range:%s.%s}' % (t, c_)

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('member_sheet', 'Wedding Party Member Sheet', 'One person in the wedding party', 'party.party_id', F(('Person', 'party.person'), ('Side', 'party.side'), ('Role', 'party.role'), ('Task', 'party.task'),
        ('Attire status', 'party.attire_status'), ('Outfit cost', 'party.outfit_cost'), ('Paid by', 'party.paid_by'), ('Fitting date', 'party.fitting_date'), ('Alteration weeks', 'party.alteration_weeks'), ('Phone', 'party.phone')) + [
        FF('Last safe order date', LK('party', 'party_id', 'last_order_date'), 'date'), FF('Days left to order', LK('party', 'party_id', 'days_left'), 'int'), FF('Order flag', LK('party', 'party_id', 'order_flag'), 'text'),
        FF('Arrives at', LK('party', 'party_id', 'arrive_place') + '&" "&' + LK('party', 'party_id', 'arrive_at'), 'text')]),
    FORM('attire_sheet', 'Attire Status Sheet', 'Everyone at one attire status', 'attire_s.status', F(('People', 'attire_s.people'), ('Outfit cost', 'attire_s.cost')) + [
        FF('Share of the party', 'IFERROR(%s/COUNTIFS(%s,"<>"),0)' % (LK('attire_s', 'status', 'people'), R('party', 'party_id')), 'pct'), FF('Outfit cost of the whole party', 'SUM(%s)' % R('party', 'outfit_cost'), 'money')],
        {"from": "party", "match": "party.attire_status", "columns": ["person", "role", "outfit_cost", "fitting_date"], "max": 10}),
    FORM('fitting_sheet', 'Fitting Sheet', 'Fitting and order dates of one person', 'fits.person', F(('Fitting date', 'fits.fitting_date'), ('Last safe order date', 'fits.last_order_date'), ('Latest fitting date', 'fits.latest_fit'),
        ('Attire status', 'fits.status'), ('Days to the fitting', 'fits.days_to_fit'), ('People fitted that day', 'fits.same_day'), ('Flag', 'fits.fit_flag')) + [
        FF('Alteration weeks', 'INDEX(%s,MATCH({pick},%s,0))' % (R('party', 'alteration_weeks'), R('party', 'person')), 'int'), FF('Phone', 'INDEX(%s,MATCH({pick},%s,0))' % (R('party', 'phone'), R('party', 'person')), 'text')]),
    FORM('task_sheet', 'Party Task Sheet', 'One task of one person', 'ptasks.task_id', F(('Person', 'ptasks.person'), ('Task', 'ptasks.task'), ('Due date', 'ptasks.due_date'), ('Status', 'ptasks.status'), ('Flag', 'ptasks.flag'), ('Phone', 'ptasks.phone')) + [
        FF('Days to the due date', LK('ptasks', 'task_id', 'due_date') + '-{today}', 'int'), FF('Tasks this person holds', 'COUNTIFS(%s,%s)' % (R('ptasks', 'person'), LK('ptasks', 'task_id', 'person')), 'int')]),
    FORM('step_sheet', 'Run of Show Step Sheet', 'One step of the day', 'run.step_id', F(('Date', 'run.date'), ('Start', 'run.start'), ('Minutes', 'run.minutes'), ('Buffer minutes', 'run.buffer_min'), ('Block', 'run.block'), ('What happens', 'run.what'),
        ('Who', 'run.who'), ('Place', 'run.place'), ('Vendor', 'run.vendor'), ('Person in charge', 'run.lead'), ('Ends', 'run.end')) + [
        FF('Minutes to the next start', LK('run', 'step_id', 'gap_next'), 'int'), FF('Minutes after the venue closes', LK('run', 'step_id', 'late_min'), 'int')]),
    FORM('hours_sheet', 'Venue Hours Sheet', 'One hour from your venue contract', 'hours.item', F(('Time', 'hours.time'), ('Note', 'hours.note')) + [
        FF('Minutes before the plan ends', PLAN_END + '-ROUND(%s*1440,0)' % LK('hours', 'item', 'time'), 'int'), FF('Steps after this time', 'COUNTIFS(%s,">"&ROUND(%s*1440,0))' % (R('run', 'start_m'), LK('hours', 'item', 'time')), 'int'),
        FF('Plan ends at', HMT(PLAN_END), 'text')]),
    FORM('move_sheet', 'Place Move Sheet', 'One move between two places', 'moves.move_id', F(('From step', 'moves.from_step'), ('To step', 'moves.to_step'), ('Who', 'moves.who'), ('From place', 'moves.from_place'), ('To place', 'moves.to_place'),
        ('Leaves at', 'moves.from_end'), ('Must be there at', 'moves.to_start'), ('Minutes allowed', 'moves.allowed'), ('Minutes needed', 'moves.needed'), ('Minutes short', 'moves.short'), ('Flag', 'moves.flag'))),
    FORM('duty_sheet', 'Day-of Duty Sheet', 'One duty on the day', 'duties.duty', F(('Named person', 'duties.named'), ('Phone', 'duties.phone'), ('Backup', 'duties.backup'), ('Backup phone', 'duties.backup_phone'), ('Briefed', 'duties.status')) + [
        FF('Meeting point', '{set:meeting_point}', 'text'), FF('Duties this person holds', 'COUNTIFS(%s,%s)' % (R('duties', 'named'), LK('duties', 'duty', 'named')), 'int')]),
    FORM('person_page_sheet', 'Person Page Sheet', 'The page of one person in the wedding party', 'load.person', F(('Tasks', 'load.tasks'), ('Open tasks', 'load.open')) + [
        FF('Role', 'INDEX(%s,MATCH({pick},%s,0))' % (R('party', 'role'), R('party', 'person')), 'text'), FF('Arrives at', 'INDEX(%s,MATCH({pick},%s,0))&" "&INDEX(%s,MATCH({pick},%s,0))' % (R('party', 'arrive_place'), R('party', 'person'), R('party', 'arrive_at'), R('party', 'person')), 'text'),
        FF('Attire status', 'INDEX(%s,MATCH({pick},%s,0))' % (R('party', 'attire_status'), R('party', 'person')), 'text'), FF('Fitting date', 'INDEX(%s,MATCH({pick},%s,0))' % (R('party', 'fitting_date'), R('party', 'person')), 'date'),
        FF('Last safe order date', 'INDEX(%s,MATCH({pick},%s,0))' % (R('party', 'last_order_date'), R('party', 'person')), 'date'), FF('Phone', 'INDEX(%s,MATCH({pick},%s,0))' % (R('party', 'phone'), R('party', 'person')), 'text')],
        {"from": "ptasks", "match": "ptasks.person", "columns": ["task", "due_date", "status", "flag"], "max": 6}),
    FORM('arrival_sheet', 'Vendor Arrival Sheet', 'Arrival and leave times of one vendor', 'onsite.vendor', F(('Steps', 'onsite.steps'), ('Arrives', 'onsite.arrives'), ('Last step ends', 'onsite.leaves'), ('Hours on site', 'onsite.hours'),
        ('First place', 'onsite.first_place'), ('Phone', 'onsite.phone')) + [FF('Longest vendor day, hours', 'MAX(%s)' % R('onsite', 'hours'), 'num')],
        {"from": "run", "match": "run.vendor", "columns": ["start", "minutes", "what", "place"], "max": 8}),
    FORM('tip_sheet', 'Tip Hand-out Sheet', 'One tip envelope', 'tips.vendor', F(('Who hands it', 'tips.handed_by'), ('Planned tip', 'tips.planned'), ('Envelope ready', 'tips.envelope_ready'), ('Hand out at', 'tips.hand_at')) + [
        FF('Tips planned in all', 'SUM(%s)' % R('tips', 'planned'), 'money'), FF('Envelopes not ready', 'SUM(%s)' % R('tips', 'notready_n'), 'int')]),
    FORM('late_sheet', 'Late Start Sheet', 'What a late start does to one step', 'run.step_id', F(('Block', 'run.block'), ('What happens', 'run.what'), ('Start', 'run.start'), ('Minutes', 'run.minutes'), ('Buffer minutes', 'run.buffer_min')) + [
        FF('Starts at if the day runs late', HMT(LK('run', 'step_id', 'start_m') + '+{set:late_min}'), 'text'), FF('Minutes late you plan for', '{set:late_min}', 'int'),
        FF('Minutes past the venue closing if late', 'MAX(0,%s+%s+{set:late_min}-%s)' % (LK('run', 'step_id', 'start_m'), LK('run', 'step_id', 'minutes'), VEND_MIN), 'int'),
        FF('Overtime for this step if late', 'ROUND(MAX(0,%s+%s+{set:late_min}-%s)/60*{set:overtime_rate},0)' % (LK('run', 'step_id', 'start_m'), LK('run', 'step_id', 'minutes'), VEND_MIN), 'money')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('roster_page', 'Party Roster Page', 'One person of the wedding party', 'party.party_id', [
        '{set:couple}, dated {today}. Wedding party: {col:party.person}, {col:party.role}, {col:party.side}.',
        'Task: {col:party.task}. Outfit: {col:party.attire_status}, cost {col:party.outfit_cost}, paid by {col:party.paid_by}. Fitting: {col:party.fitting_date}.',
        'On the day, please be at {col:party.arrive_place} at {col:party.arrive_at}. Phone: {col:party.phone}.'], ['The couple', 'Wedding party member'], NOTE),
    DOC('order_page', 'Fitting Dates Page', 'Fitting and last safe order date of one person', 'fits.person', [
        '{set:couple}, dated {today}. Fitting and order dates for {col:fits.person}.',
        'Fitting: {col:fits.fitting_date}. Latest fitting that leaves time for alterations: {col:fits.latest_fit}. Last safe order date: {col:fits.last_order_date}. Attire status: {col:fits.status}. Flag: {col:fits.fit_flag}.',
        'The dates count back from the wedding day with your own shipping days and safety margin. Check the lead time of your shop.'], ['The couple', 'Wedding party member'], NOTE),
    DOC('step_page', 'Step Page', 'One step of the run of show, minute by minute', 'run.step_id', [
        '{set:couple}, dated {today}. Run of show, step {col:run.step_id} on {col:run.date}.',
        '{col:run.start} to {col:run.end}: {col:run.what}. Block: {col:run.block}. Who: {col:run.who}. Place: {col:run.place}. Vendor: {col:run.vendor}. Person in charge: {col:run.lead}.',
        'Buffer minutes in this step: {col:run.buffer_min}. Minutes to the next start: {col:run.gap_next}. The day runs from {col:run.first_start_t} to {col:run.plan_end_t}.'], ['The couple', 'Day-of coordinator'], NOTE),
    DOC('vendor_plan_page', 'Vendor Plan Page', 'The run of show for the venue and one vendor', 'vendors.vendor_id', [
        '{set:couple}, dated {today}. Plan for the venue and {col:vendors.vendor}, on {col:vendors.wedding_day}. Contact: {col:vendors.contact}, {col:vendors.phone}.',
        'Your role: {col:vendors.day_role}. Vendors may arrive at the venue from {col:vendors.vendors_in}. Steps on the day: {col:vendors.steps}.',
        'The plan ends at {col:vendors.plan_end_t} and the venue ends at {col:vendors.venue_end_t}. Check the overtime terms in your contract.'], ['The couple', 'Vendor', 'Venue contact'], NOTE),
    DOC('where_page', 'Who Is Where Page', 'Who needs to be where in one block', 'where.where_id', [
        '{set:couple}, dated {today}. Who is where: {col:where.who}, block {col:where.block}.',
        'Steps: {col:where.steps}. First start: {col:where.first_start}. Last end: {col:where.last_end}. Place: {col:where.place}.',
        'Share this page with the person or group so they know where to be.'], ['The couple', 'Day-of coordinator'], NOTE),
    DOC('person_page', 'One Page per Person', 'One step on the page of a person or group', 'pages.page_id', [
        '{set:couple}, dated {today}. Page for {col:pages.who}, row {col:pages.page_id}.',
        '{col:pages.start} to {col:pages.end}: {col:pages.what}. Place: {col:pages.place}. Block: {col:pages.block}. With: {col:pages.with_whom}.',
        'Print the whole page for each person or group from Page per Person.'], ['The couple', 'Page holder'], NOTE),
    DOC('contact_page', 'Contact List Page', 'One person on the day-of contact list', 'team.team_id', [
        '{set:couple}, dated {today}. Day-of contact: {col:team.name}, {col:team.role}.',
        'Phone: {col:team.phone}. E-mail: {col:team.email}. Duties named: {col:team.duties}. Steps led: {col:team.steps_led}. Meeting point: {set:meeting_point}.',
        'Keep this page with the day-of coordinator and the person who holds the gifts.'], ['The couple', 'Day-of coordinator'], NOTE),
    DOC('duties_page', 'Day-of Duties Page', 'One duty on the day with a backup', 'duties.duty', [
        '{set:couple}, dated {today}. Duty: {col:duties.duty}.',
        'Named person: {col:duties.named}, {col:duties.phone}. Backup: {col:duties.backup}, {col:duties.backup_phone}. Briefed: {col:duties.status}.',
        'Meeting point: {set:meeting_point}. The gifts, the cards, the tip envelopes and the returns each need one named person.'], ['The couple', 'Named person'], NOTE),
    DOC('arrival_page', 'Vendor Arrival Page', 'Arrival and leave times of one vendor', 'onsite.vendor', [
        '{set:couple}, dated {today}. Vendor: {col:onsite.vendor}, {col:onsite.contact}, {col:onsite.phone}.',
        'Arrives at {col:onsite.arrives_t} at the {col:onsite.first_place}. Last step ends at {col:onsite.leaves}. Hours on site: {col:onsite.hours}. Steps: {col:onsite.steps}.',
        'Meeting point: {set:meeting_point}.'], ['The couple', 'Vendor'], NOTE),
    DOC('tip_page', 'Tip Page', 'One tip envelope and who hands it', 'tips.vendor', [
        '{set:couple}, dated {today}. Tip for {col:tips.vendor}: {col:tips.planned}, handed by {col:tips.handed_by}.',
        'Envelope ready: {col:tips.envelope_ready}. Hand out at {col:tips.hand_at}.',
        'Tips are optional and vary by market. Check your contract to see if a service charge is already included.'], ['The couple', 'Person who hands the envelope'], NOTE),
    DOC('overtime_page', 'Overtime Page', 'The plan end against the venue closing time', 'run.step_id', [
        '{set:couple}, dated {today}. Overrun and overtime, run of show of {col:run.wedding_day}.',
        'The plan ends at {col:run.plan_end_t} and the venue ends at {col:run.venue_end_t}. Overrun: {col:run.over_min} minutes. Overtime cost estimate: {col:run.overtime_cost}.',
        'The estimate uses your overtime rate per hour from Settings. Check your contract for how overtime is billed.'], ['The couple', 'Day-of coordinator'], NOTE),
    DOC('guest_page', 'Guest Timeline Page', 'What guests do and when', 'gtl.step_id', [
        '{set:couple}. Welcome. {col:gtl.time}: {col:gtl.what}.',
        'Where: {col:gtl.place}. Part of the day: {col:gtl.block}.',
        'Print the whole timeline from Guest Timeline for a welcome sign or a note in the guest room.'], ['The couple'], 'Sample wording: adapt it to your own wedding and your own guests.'),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('choose_party', 'Choose the wedding party', 'run', 'run.date', [('Agree how many people stand with each of you', -300), ('Write the roles you want, they are labels you can edit', -290), ('Ask each person in person or by phone', -280),
                                                                       ('Add each person to Wedding Party', -270), ('Share the date and what you hope for', -260), ('Give each person a task and a date', -240)]),
    CHK('outfit_fittings', 'Outfit order and fittings', 'party', 'party.fitting_date', [('Choose the outfit and ask the shop for its lead time', -90), ('Order by the last safe order date', -70), ('Check that the outfit has arrived', -28), ('Book the fitting',
                                                                                        -21), ('Tell your tailor the alteration weeks', -14), ('Go to the fitting', 0), ('Collect the outfit after alterations', 21), ('Do a last check at home', 35)]),
    CHK('party_briefing', 'Wedding party briefing', 'run', 'run.date', [('Send each person their task and the date', -90), ('Send the fitting and order dates', -75), ('Hold a short call with the wedding party leads', -45),
                                                                        ('Share the page for the day with the party', -21), ('Confirm the rehearsal time', -10), ('Hand out the pages for the day', -1)]),
    CHK('run_draft', 'Run of show draft', 'run', 'run.date', [('List every step from the morning to the last dance', -120), ('Put the venue hours into Venue Hours', -110), ('Add minutes and buffer to each step', -100), ('Name a person in charge for each step', -90),
                                                              ('Check the travel between places in Moves', -80), ('Run the overrun check against the closing time', -70)]),
    CHK('run_review', 'Run of show review with vendors', 'run', 'run.date', [('Send each vendor their times', -45), ('Ask each vendor to confirm', -40), ('Check arrival and set-up times for clashes', -35), ('Check the venue access hours', -30),
                                                                              ('Agree the music, dinner and photo times', -21), ('Send the final plan to the day-of coordinator', -14)]),
    CHK('rehearsal_day', 'Rehearsal day', 'run', 'run.date', [('Confirm the time with the officiant and the venue', -7), ('Tell the wedding party and the parents', -6), ('Print the order of the ceremony', -3), ('Walk through the entrance, the places and the exit', -1),
                                                              ('Practise the signing', -1), ('Hand out the pages for the day', -1)]),
    CHK('day_morning', 'Wedding day morning', 'run', 'run.date', [('Eat breakfast and drink water', 0), ('Hair and makeup starts on time', 0), ('Flowers arrive at the hotel', 0), ('Rings and outfits go to the photographer for detail shots', 0),
                                                                  ('The day-of coordinator walks the venue', 0), ('The party and parents travel to the venue', 0)]),
    CHK('day_ceremony', 'Wedding day ceremony', 'run', 'run.date', [('Ushers and greeters are in place with the programs', 0), ('Guests are seated and the music plays', 0), ('The officiant and the couple are ready', 0), ('The ceremony and the signing', 0),
                                                                    ('Family photos', 0)]),
    CHK('day_reception', 'Wedding day reception', 'run', 'run.date', [('Cocktail hour starts', 0), ('Guests move to the reception room', 0), ('Grand entrance and welcome', 0), ('Dinner and speeches', 0), ('Cake cutting', 0), ('First dance and open dancing', 0)]),
    CHK('day_loadout', 'End of night and load-out', 'run', 'run.date', [('Last dance and send-off', 0), ('The shuttle runs to the hotel', 0), ('Hand out the tip envelopes', 0), ('Count the rentals and begin the load-out', 0), ('Hand the venue back and return the keys', 0), ('Check for lost property', 0)]),
    CHK('handoff', 'Gifts, cards and tips hand-off', 'run', 'run.date', [('Name the person for gifts and cards', -60), ('Name the person for the returns', -45), ('Prepare the tip envelopes', -14), ('Brief the people you named', -3), ('Hand over the gift box and the envelopes', 0), ('Return the rentals', 2)]),
    CHK('small_day', 'Small wedding day plan', 'run', 'run.date', [('Keep only Run of Show and Day-of Duties', -60), ('Write the six or eight steps of the day', -50), ('Name one person for gifts, cards and tips', -30), ('Check the venue closing time', -21), ('Tell each guest the time and the place', -14),
                                                                          ('Print one page for the day', -2)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
M = MSG
messages = [
    M('m_wp_thanks', 'Party member: thank you', 'party', 'party.phone', 'Hello {person}, thank you for saying yes. Your role is {role}. {couple}'),
    M('m_wp_task', 'Wedding party member: your task', 'party', 'party.phone', 'Hello {person}, your task is: {task}. Please confirm by {confirm_by}. {couple}'),
    M('m_wp_fitting', 'Wedding party member: your fitting', 'party', 'party.phone', 'Hello {person}, your fitting is on {fitting_date}. {couple}'),
    M('m_wp_order', 'Party member: order your outfit', 'party', 'party.phone', 'Hello {person}, please order your outfit by {last_order_date}. {couple}'),
    M('m_wp_attire', 'Wedding party member: your outfit status', 'party', 'party.phone', 'Hello {person}, your outfit is {attire_status}. Any questions? {couple}'),
    M('m_wp_rehearsal', 'Wedding party member: the rehearsal', 'party', 'party.phone', 'Hello {person}, the rehearsal is on {rehearsal_date} at {rehearsal_start}. {couple}'),
    M('m_wp_place', 'Party member: where to be', 'party', 'party.phone', 'Hello {person}, please be at {arrive_place} at {arrive_at} on {wedding_day}. {couple}'),
    M('m_wp_page', 'Party member: your page', 'party', 'party.phone', 'Hello {person}, your page for the day is ready and I will send it to you. {couple}'),
    M('m_lead_count', 'Wedding party lead: outfits not ordered', 'fits', 'fits.lead_phone', 'Hello {lead_name}, {not_ordered} outfits are not ordered yet. Can you remind the party? {couple}'),
    M('m_lead_run', 'Party lead: the run of show', 'fits', 'fits.lead_phone', 'Hello {lead_name}, the wedding party starts at {party_start} at {party_place} on {wedding_day}. I will send the run of show. {couple}'),
    M('m_lead_programs', 'Party lead: hand out programs', 'fits', 'fits.lead_phone', 'Hello {lead_name}, please hand out the programs at {programs_at} on {wedding_day}. {couple}'),
    M('m_par1_hair', 'Parent of partner 1: hair and makeup', 'team', 'team.ph_par1', 'Hello {name}, please be at {hm_place} at {hm_start} for hair and makeup on the wedding day. {couple}'),
    M('m_par2_photos', 'Parent of partner 2: photos', 'team', 'team.ph_par2', 'Hello {name}, please be at {ph_place} at {ph_start} for photos on the wedding day. {couple}'),
    M('m_par_page', 'Parent: your page for the day', 'team', 'team.ph_parents', 'Hello {name}, your page for the day is ready and I will send it to you. {couple}'),
    M('m_friend_gifts', 'Close friend helper: gifts and cards', 'team', 'team.ph_friend', 'Hello {name}, you hold the gifts and cards on the day. Your backup is {gifts_backup}. {couple}'),
    M('m_friend_tips', 'Close friend helper: the tip envelopes', 'team', 'team.ph_friend', 'Hello {name}, please hand out the tip envelopes at {tips_at}. {couple}'),
    M('m_off_start', 'Officiant: the ceremony time', 'vendors', 'vendors.ph_officiant', 'Hello {contact}, the ceremony starts at {ceremony_start} and lasts {ceremony_min} minutes on {wedding_day}. {couple}'),
    M('m_off_arrive', 'Officiant: arrival for the sound check', 'vendors', 'vendors.ph_officiant', 'Hello {contact}, please arrive at {officiant_arrive} for the sound check on {wedding_day}. {couple}'),
    M('m_coord_run', 'Coordinator: run of show, buffer', 'team', 'team.ph_coord', 'Hello {name}, the run of show has {steps} steps and {buffer} buffer minutes. I will send the buffer plan too. {couple}'),
    M('m_coord_end', 'Coordinator: venue and plan end', 'team', 'team.ph_coord', 'Hello {name}, the venue ends at {venue_end_t} and the plan ends at {plan_end_t}. {couple}'),
    M('m_coord_buffer', 'Day-of coordinator: add buffer', 'team', 'team.ph_coord', 'Hello {name}, please add {buffer_add} minutes of buffer at {buffer_block}. {couple}'),
    M('m_coord_contacts', 'Coordinator: contacts and duties', 'team', 'team.ph_coord', 'Hello {name}, the contact list and the duties are ready and I will send them. {couple}'),
    M('m_venue_extend', 'Venue: can we extend the hours', 'vendors', 'vendors.ph_venue', 'Hello {contact}, our plan ends at {plan_end_t}. Can we stay past {venue_end_t} on {wedding_day}? {couple}'),
    M('m_venue_access', 'Venue: confirm vendor access', 'vendors', 'vendors.ph_venue', 'Hello {contact}, please confirm vendor access from {vendors_in} on {wedding_day}. {couple}'),
    M('m_photo_portraits', 'Photographer: the portraits', 'vendors', 'vendors.ph_photog', 'Hello {contact}, portraits start at {portrait_start} at the {portrait_place}. Please confirm the light and the place. {couple}'),
    M('m_photo_family', 'Photographer: the family photos', 'vendors', 'vendors.ph_photog', 'Hello {contact}, family photos start at {family_start} at the {family_place}. I will send the family photo list. {couple}'),
    M('m_band_sets', 'Band or DJ: the set times', 'vendors', 'vendors.ph_band', 'Hello {contact}, your set is {band_start} to {band_end} with a break at {band_break} on {wedding_day}. {couple}'),
    M('m_caterer_dinner', 'Caterer: dinner service', 'vendors', 'vendors.ph_caterer', 'Hello {contact}, dinner starts at {dinner_start} on {wedding_day}. Please confirm service. {couple}'),
    M('m_hair_start', 'Hair and makeup: your start time', 'onsite', 'onsite.ph_hair', 'Hello {contact}, your start time is {arrives_t} at the {first_place} on {wedding_day}. {couple}'),
    M('m_transport', 'Transport: pick-up times', 'onsite', 'onsite.ph_transport', 'Hello {contact}, pick-up times are {arrives_t} and {last_start} on {wedding_day}. Please confirm. {couple}'),
    M('m_hotel_shuttle', 'Hotel: shuttle, late check-out', 'vendors', 'vendors.ph_hotel', 'Hello {contact}, the shuttle and the late check-out are on {wedding_day}. The last pick-up is {shuttle_at}. {couple}'),
    M('m_partner_over', 'Partner: the overrun and the overtime', 'run', 'run.partner_phone', 'Hello, the run of show is over by {over_min} minutes, overtime {overtime_cost}. {couple}'),
    M('m_partner_noperson', 'Partner: steps without a person', 'run', 'run.partner_phone', 'Hello, {no_person} steps have no person yet. {couple}'),
    M('m_partner_page', 'Partner: the one-page plan is ready', 'run', 'run.partner_phone', 'Hello, the one-page plan for the day is ready to print, from {first_start_t} to {plan_end_t}. {couple}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
def A_(c_, v_): return 'COUNTIFS(%s,%s,%s,"<>")' % (R('party', 'attire_status'), v_, R('party', 'party_id'))
kpis = [
    KPI('Wedding party size', 'COUNTIFS(%s,"<>")-COUNTIFS(%s,%s,%s,"<>")' % (R('party', 'party_id'), R('party', 'role'), tok('prole', 'Helper'), R('party', 'party_id')), 'int'),
    KPI('Family helpers', 'COUNTIFS(%s,%s,%s,"<>")' % (R('party', 'role'), tok('prole', 'Helper'), R('party', 'party_id')), 'int'),
    KPI('Roles filled', 'COUNTIFS(%s,">0")' % R('roles', 'people'), 'int'),
    KPI('People with an outfit ordered', 'COUNTIFS(%s,">=2")' % R('party', 'stage'), 'int'),
    KPI('Outfits not started', A_('', NS), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Outfits arrived', A_('', ARR), 'int'), KPI('Outfits fitted', A_('', FITD), 'int'), KPI('Outfits ready', A_('', READY), 'int'),
    KPI('Fittings in the next 30 days', 'COUNTIFS(%s,">="&{today},%s,"<="&({today}+30))' % (R('party', 'fitting_date'), R('party', 'fitting_date')), 'int'),
    KPI('Earliest last safe order date', 'IFERROR(SMALL(%s,1),"")' % R('party', 'open_order_date'), 'date'),
    KPI('Outfits past their last safe order date', 'COUNTIFS(%s,%s)' % (R('party', 'order_flag'), v('Late')), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Outfit cost total', 'SUM(%s)' % R('party', 'outfit_cost'), 'money'), KPI('Outfit cost paid by the couple', 'SUM(%s)' % R('party', 'couple_cost'), 'money'),
    KPI('Run of show steps', 'COUNTIFS(%s,"<>")' % R('run', 'step_id'), 'int'),
    KPI('Run of show minutes, start to end', 'IF(COUNT(%s)=0,"",%s-%s)' % (R('run', 'start'), PLAN_END, PLAN_START), 'int'),
    KPI('First start time', 'IF(COUNT(%s)=0,"",%s)' % (R('run', 'start'), HMT(PLAN_START)), 'text'),
    KPI('Plan end time, 24:00 is midnight', 'IF(COUNT(%s)=0,"",%s)' % (R('run', 'start'), HMT(PLAN_END)), 'text'),
    KPI('Venue end time', 'IFERROR(%s,"")' % HMT(VEND_MIN), 'text'),
    KPI('Overrun minutes', 'IF(COUNT(%s)=0,"",%s)' % (R('run', 'start'), OVER_MIN), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Overtime cost estimate', 'IF(COUNT(%s)=0,"",ROUND(%s/60*{set:overtime_rate},0))' % (R('run', 'start'), OVER_MIN), 'money', alert={"when": "> 0", "style": "warn"}),
    KPI('Buffer minutes planned', 'SUM(%s)' % R('run', 'buffer_min'), 'int'),
    KPI('Moves between places', 'COUNTIFS(%s,">0")' % R('moves', 'kind'), 'int'),
    KPI('Travel minutes allowed, average per move', 'IFERROR(ROUND(AVERAGEIFS(%s,%s,">0"),0),"")' % (R('moves', 'allowed'), R('moves', 'kind')), 'int'),
    KPI('Vendors on site', 'COUNTIFS(%s,">0")' % R('onsite', 'steps'), 'int'),
    KPI('Longest vendor on site, hours', 'IF(COUNT(%s)=0,"",MAX(%s))' % (R('onsite', 'hours'), R('onsite', 'hours')), 'num'),
    KPI('Steps with no person', 'COUNTIFS(%s,"<>",%s,"")' % (R('run', 'step_id'), R('run', 'lead')), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Day-of duties named', 'COUNTIFS(%s,1)' % R('duties', 'named_ok'), 'int'),
    KPI('Tip envelopes ready', 'SUM(%s)' % R('tips', 'ready_n'), 'int'), KPI('Tip envelopes not ready', 'SUM(%s)' % R('tips', 'notready_n'), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Days to the wedding', '{set:wedding_day}-{today}', 'int'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Party and Run of Show", "kpis": kpis,
    "monthly": {"title": "Outfit cost by fitting month", "date": "party.fitting_date", "series": [
        {"label": "Outfit cost", "sum": "party.outfit_cost", "date": "party.fitting_date"}, {"label": "Paid by the couple", "sum": "party.couple_cost", "date": "party.fitting_date"}]},
    "breakdowns": [{"title": "Outfit cost by role", "by": "party.role", "value": "party.outfit_cost", "agg": "sum"}, {"title": "Planned minutes by block", "by": "run.block", "value": "run.minutes", "agg": "sum"},
                   {"title": "Tips by vendor", "by": "tips.vendor", "value": "tips.planned", "agg": "sum"}, {"title": "Outfit cost by attire status", "by": "party.attire_status", "value": "party.outfit_cost", "agg": "sum"}]}


def AG(kind, table, value=None, date=None, label=None, where=None): return AGG(kind, table, value, date, where, label)
insights = {"filters": [{"label": "Wedding party role", "list": "prole"}, {"label": "Run of show block", "list": "block"}, {"label": "Attire status", "list": "attire"}],
    "gauges": [
        {"title": "Outfits ordered", "num": AG('count', 'party', where=[('stage', '>=', 2)]), "den": AG('count', 'party', where=[('stage', '>=', 1)])},
        {"title": "Outfits fitted or ready", "num": AG('count', 'party', where=[('stage', '>=', 4)]), "den": AG('count', 'party', where=[('stage', '>=', 1)])},
        {"title": "Run of show within venue hours", "num": AG('count', 'run', where=[('within', '=', 1)]), "den": AG('count', 'run', where=[('minutes', '>', 0)])},
        {"title": "Buffer against the goal you set", "num": AG('sum', 'run', 'run.buffer_min'), "den": AG('sum', 'run', 'run.buffer_goal')},
        {"title": "Steps with a person in charge", "num": AG('count', 'run', where=[('lead_set', '=', 1)]), "den": AG('count', 'run', where=[('minutes', '>', 0)])},
        {"title": "Day-of duties named with a backup", "num": AG('count', 'duties', where=[('backup_ok', '=', 1)]), "den": AG('count', 'duties', where=[('named_ok', '>=', 0)])}],
    "charts": [
        CHART('Wedding party by role', 'bar', 'party.role', [AG('count', 'party', label='People')]),
        CHART('Wedding party by side', 'bar', 'party.side', [AG('count', 'party', label='People')]),
        CHART('Attire status', 'bar', 'party.attire_status', [AG('count', 'party', label='People')]),
        CHART('Outfit cost by person', 'bar', 'party.person', [AG('sum', 'party', 'party.outfit_cost', label='Outfit cost')]),
        CHART('Outfit cost by payer', 'bar', 'party.paid_by', [AG('sum', 'party', 'party.outfit_cost', label='Outfit cost')]),
        CHART('Fittings by month', 'column', 'month', [AG('count', 'party', date='party.fitting_date', label='Fittings')]),
        CHART('Alteration weeks by role', 'bar', 'party.role', [AG('avg', 'party', 'party.alteration_weeks', label='Weeks')]),
        CHART('Party tasks by status', 'bar', 'ptasks.status', [AG('count', 'ptasks', label='Tasks')]),
        CHART('Run of show minutes by block', 'bar', 'run.block', [AG('sum', 'run', 'run.minutes', label='Minutes')]),
        CHART('Run of show steps by block', 'bar', 'run.block', [AG('count', 'run', label='Steps')]),
        CHART('Run of show steps by place', 'bar', 'run.place', [AG('count', 'run', label='Steps')]),
        CHART('Run of show steps by who', 'bar', 'run.who', [AG('count', 'run', label='Steps')]),
        CHART('Buffer minutes by block', 'bar', 'run.block', [AG('sum', 'run', 'run.buffer_min', label='Buffer minutes')]),
        CHART('Steps by vendor', 'bar', 'onsite.vendor', [AG('sum', 'onsite', 'onsite.steps', label='Steps')]),
        CHART('Overrun by block', 'bar', 'overrun.block', [AG('sum', 'overrun', 'overrun.overrun', label='Overrun minutes')]),
        CHART('Vendor hours on site', 'bar', 'onsite.vendor', [AG('sum', 'onsite', 'onsite.hours', label='Hours')]),
        CHART('Wedding party by attire status and side', 'bar', 'party.side', [AG('count', 'party', label='Not started', where=[('stage', '=', 1)]), AG('count', 'party', label='Ordered', where=[('stage', '=', 2)]),
                                                                              AG('count', 'party', label='Arrived', where=[('stage', '=', 3)]), AG('count', 'party', label='Fitted or ready', where=[('stage', '>=', 4)])]),
        CHART('Tips by vendor', 'bar', 'tips.vendor', [AG('sum', 'tips', 'tips.planned', label='Planned tip')]),
        CHART('Envelopes ready by owner', 'bar', 'tips.handed_by', [AG('sum', 'tips', 'tips.ready_n', label='Ready'), AG('sum', 'tips', 'tips.notready_n', label='Not ready')]),
        CHART('Duties by person', 'bar', 'duties.named', [AG('count', 'duties', label='Duties')]),
        CHART('Guest timeline by block', 'bar', 'run.block', [AG('count', 'run', label='Guest steps', where=[('who', '=', W_AG)])]),
        CHART('Day-of duties by status', 'bar', 'duties.status', [AG('count', 'duties', label='Duties')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Last safe order date", "why": "counts back from the fitting, the alteration weeks and the shipping days so no outfit is ordered too late", "where": "Last Safe Order Date"},
    {"name": "Run of show overrun check", "why": "the plan end against the venue closing time with the overtime cost and the minutes to cut", "where": "Run of Show Overrun Check"},
    {"name": "Travel time check", "why": "every move between the hotel, the venue and the shuttle tested against the minutes the plan gives it", "where": "Travel Time Check"},
    {"name": "Who needs to be where", "why": "pick a person or group and a time and see the step, the place and the person in charge", "where": "Who Needs to Be Where"},
    {"name": "Page per person", "why": "one printable page for the wedding party, the parents, the vendors, the officiant and the guests, built from the run of show", "where": "Page per Person"},
    {"name": "Late start impact", "why": "a ceremony that starts late: which steps slide, the new end time and the overtime it adds", "where": "Late Start Impact"},
    {"name": "Day-of contact list", "why": "a named person and a backup for the gifts, the cards, the tip envelopes and the returns", "where": "Day-of Contact List"},
    {"name": "Buffer planner", "why": "names the block of the day that needs buffer minutes first, from its vendor and guest steps", "where": "Buffer Planner"},
    {"name": "Fitting calendar with a clash flag", "why": "fittings by date with the days that hold more people than your shop can fit", "where": "Fitting Calendar"},
    {"name": "Sunset and light check", "why": "the portraits and the ceremony against the sunset time you set, with the minutes to move them earlier", "where": "Sunset and Light Check"}]
competitors = [
    {"what": "a free planning app", "lacks": "keeps a guest and task list but has no minute-by-minute run of show checked against the venue hours, no overtime cost and no who-is-where matrix"},
    {"what": "a single budget spreadsheet", "lacks": "tracks costs only: no wedding party roster, no attire status with a last safe order date and no page for each person"},
    {"what": "a printable wedding binder", "lacks": "has blank pages for the timeline but does no sums, no travel time check, no late start impact and no buffer planner"},
    {"what": "a wedding website with a registry", "lacks": "shares your plans with a company and has no vendor arrival times, no tip hand-out plan and no day-of duties with a backup"}]
guide = [
    'Open Settings and type your names, the wedding day, the minutes by road between the hotel and the venue and your overtime rate. Replace demo data: clear the sample rows and type your own.',
    'Fill Wedding Party with each person: role, task, outfit status, cost, who pays, fitting date and alteration weeks. Role names are labels you can edit; a helper or a parent is just another row.',
    'Check Fitting Plan and the Last Safe Order Date tool: the last date to order each outfit counts back from the fitting and your shipping days.',
    'Fill Venue Hours from your venue contract: when vendors and guests may enter and when the venue closes. The run of show is checked against Venue closes.',
    'Fill Run of Show, one row per step with start, minutes, buffer, block, who, place, vendor and the person in charge. End times, gaps and the overrun fill in.',
    'Use Moves for the trips between the hotel, the venue and the shuttle, and Who and Where and Page per Person for the printed pages of each person or group.',
    'Name one person and a backup for each job in Day-of Duties: the gifts, the cards, the tip envelopes and the returns come first.',
    'Add Tips Handed Out for the vendors you want to tip. Tips are optional and vary by market; check your contract for a service charge.',
    f'Use the {len(tools)} tools, print {len(forms)} sheets and {len(documents)} pages, follow {len(checklists)} checklists and tap a message link to send a text with the details written in.',
    'A couple with a small wedding (30 guests, no wedding party) uses the same sheets with fewer rows: keep Run of Show, Venue Hours and Day-of Duties, and leave Wedding Party empty.',
    'This workbook has no macros and works in Excel and Google Sheets. Print any page for a parent, a helper or a vendor.',
    'Why a workbook: one flat price, no vendor ever sees your details, no fees on your gifts, your own numbers, and it works offline.',
    'What this is not: not a booking service, not a payment service, and not legal, tax or insurance advice. Every default is a typical starting value you can edit, never a promise.']
listing = {"title": "Wedding Party and Run of Show Excel Template: Day-Of Timeline, Wedding Party Roster, Fittings, Vendor Arrival Times, Tips",
    "headline": "Plan the wedding party and the minutes of the day in one workbook",
    "tags": ["wedding planner", "run of show", "wedding timeline", "day of timeline", "wedding party", "wedding checklist", "excel template", "bridal party", "wedding spreadsheet", "wedding day plan", "vendor schedule", "wedding fittings", "tip planner"],
    "description": ("Plan the people and the minutes of your wedding day in one Excel workbook. Built for an engaged couple planning their own wedding, with a day-of coordinator, a parent or a wedding party lead helping. "
        "Wedding Party holds each person with a role, a task, an outfit status, the cost, who pays and the fitting date. The last safe order date counts back from the fitting, the alteration weeks and the shipping days, and Fitting Plan flags a clash or a fitting that is too late.\n\n"
        "Run of Show holds the minute-by-minute plan of the day: start, minutes, buffer, block, who, place, vendor and the person in charge. End times, idle gaps and the overrun against your venue hours fill in, with the overtime cost. Moves checks the time between the hotel, the venue and the shuttle. "
        "Who and Where is the who-needs-to-be-where matrix, and Page per Person builds a printable page for the wedding party, the parents, the vendors, the officiant and the guests.\n\n"
        "Day-of Duties names one person and a backup for the gifts, the cards, the tip envelopes and the returns. Vendor On-site shows when each vendor arrives and leaves, and Tips Handed Out plans each envelope.\n\n"
        f"{len(tools)} tools answer the weekly questions: which outfit to order by when, whether the day ends before the venue closes, where to add buffer, what a late ceremony costs, whether the portraits are in good light and whether every duty has a name. Print {len(forms)} sheets and {len(documents)} pages, follow {len(checklists)} checklists and send {len(messages)} ready text messages to the wedding party, parents, vendors and the day-of coordinator.\n\n"
        "A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Every default is a typical starting value you can edit, and forecasts are your own estimate. It is not a booking service, not a payment service and not legal, tax or insurance advice. This is part six of the Wedding Planning suite."),
    "features": ["Wedding party roster with outfit status", "Last safe order date for every outfit", "Fitting plan with a clash flag", "Minute-by-minute run of show", "Overrun and overtime against the venue hours", "Travel time between places",
                 "Who needs to be where matrix", "Printable page per person or group", "Late start impact", "Day-of duties with a backup", f"{len(tools)} decision tools", f"{len(forms)} printable sheets and {len(documents)} pages",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}

for _t in tables: _t['rows'] = max(50, _t['rows'])
lists = BASE_LISTS + verdict_lists()
assert len(lists) <= 20, len(lists)
s = spec(id=f'{SUITE}-p6', slug='wedding-dayof', profession='Wedding Planning', name='Wedding Party and Day-Of Run-of-Show',
         tagline='Plan the wedding party and the minutes of the day in one workbook', price_usd=29,
         colors={"primary": "#7A4B68", "accent": "#D9A86C"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 6, "of": 8, "focus": "Wedding party and day-of run of show"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wp6.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'lists', len(lists), 'desc', len(listing['description']), 'title', len(listing['title']))
