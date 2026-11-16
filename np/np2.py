"""Nonprofit Organization suite - part 2: Donor Growth, Retention and Major Gifts."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np2_lists import *
from np2_tables import settings, tables
from np2_tools import tools
import np2_data as D

SUITE = 'fx-20261115-nonprofit'
NOTE = "Sample wording, adapt it to your own organization and check your local rules."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
def R(t, c): return '{range:%s.%s}' % (t, c)
THIS, LASTY = tok('yr', 'This year'), tok('yr', 'Last year')
THIS2 = tok('yr2', 'This year'); ALL = tok('dgroup', 'All donors')
CLOSED = tok('pstage', 'Closed')

# ------------------------------------------------------------------ forms (12)
def PF(c): return LK('prospects', 'prospect_id', c)
forms = [
    FORM('prospect_sheet', 'Prospect Sheet', 'Prospect profile', 'prospects.prospect_id', F(('Donor', 'prospects.donor'), ('Capacity', 'prospects.capacity'), ('Stage', 'prospects.stage'), ('Ask amount', 'prospects.ask_amount'),
        ('Probability, your estimate', 'prospects.probability'), ('Weighted value', 'prospects.weighted_value'), ('Owner', 'prospects.owner'), ('Expected close', 'prospects.expected_close')) + [
        FF('Ask as a share of capacity', 'IFERROR(%s/%s,0)' % (PF('ask_amount'), PF('capacity')), 'pct'), FF('Capacity left after the ask', '%s-%s' % (PF('capacity'), PF('ask_amount')), 'money'),
        FF('Prospects of the same owner', 'COUNTIFS({range:prospects.owner},%s)' % PF('owner'), 'int')]),
    FORM('prospect_contact', 'Prospect Contact Sheet', 'Contact log and next step', 'prospects.prospect_id', F(('Donor', 'prospects.donor'), ('Phone', 'prospects.phone'), ('Owner', 'prospects.owner'), ('Last contact', 'prospects.last_contact'),
        ('Days since contact', 'prospects.days_quiet'), ('Next step', 'prospects.next_step'), ('Next step date', 'prospects.next_step_date'), ('Days overdue', 'prospects.overdue_days'), ('Verdict', 'prospects.verdict')) + [
        FF('Weeks since contact', 'ROUND(%s/7,1)' % PF('days_quiet'), 'num'), FF('Days until the next step', '%s-{today}' % PF('next_step_date'), 'int'), FF('Next steps overdue, all prospects', 'COUNTIFS({range:prospects.overdue_days},">0")', 'int')]),
    FORM('ask_plan_sheet', 'Ask Plan Sheet', 'Plan for one ask', 'prospects.prospect_id', F(('Donor', 'prospects.donor'), ('Stage', 'prospects.stage'), ('Ask amount', 'prospects.ask_amount'), ('Capacity', 'prospects.capacity'),
        ('Weighted value', 'prospects.weighted_value'), ('Next step', 'prospects.next_step'), ('Owner', 'prospects.owner')) + [
        FF('Open weighted value of the same owner', 'SUMIFS({range:prospects.weighted_value},{range:prospects.owner},%s,{range:prospects.stage},"<>"&%s)' % (PF('owner'), CLOSED), 'money'),
        FF('Share of the major-gift goal', 'IFERROR(%s/{set:major_goal},0)' % PF('ask_amount'), 'pct'), FF('Weighted value, all open prospects', 'SUMIFS({range:prospects.weighted_value},{range:prospects.stage},"<>"&%s)' % CLOSED, 'money')]),
    FORM('lapsed_outreach_sheet', 'Lapsed Outreach Sheet', 'Outreach to a lapsed donor', 'lapsed.rank', F(('Donor', 'lapsed.donor'), ('Last gift', 'lapsed.last_gift'), ('Last gift amount', 'lapsed.last_amount'), ('Years given', 'lapsed.years_given'),
        ('Given last year', 'lapsed.last_year'), ('Given in the 3 years before this one', 'lapsed.three_years'), ('Next step', 'lapsed.next_step'), ('Contact by', 'lapsed.contact_by')) + [
        FF('Months since the last gift', 'ROUND(({today}-%s)/30.4,0)' % LK('lapsed', 'rank', 'last_gift'), 'int'), FF('Last year as a share of the 3 years', 'IFERROR(%s/%s,0)' % (LK('lapsed', 'rank', 'last_year'), LK('lapsed', 'rank', 'three_years')), 'pct'),
        FF('Lapsed donors to call', 'COUNTIFS({range:lapsed.next_step},%s)' % va('Call'), 'int')]),
    FORM('winback_call_sheet', 'Win-back Call Sheet', 'Call sheet for a lapsed donor', 'lapsed.rank', F(('Donor', 'lapsed.donor'), ('Phone', 'lapsed.phone'), ('Caller', 'lapsed.caller'), ('Call day', 'lapsed.contact_by'), ('Invite to', 'lapsed.appeal'),
        ('Last gift', 'lapsed.last_gift'), ('Last gift amount', 'lapsed.last_amount')) + [
        FF('Calls planned for the same day', 'COUNTIFS({range:lapsed.contact_by},%s)' % LK('lapsed', 'rank', 'contact_by'), 'int'), FF('Money back, your estimate', '%s*{set:win1}' % LK('lapsed', 'rank', 'last_year'), 'money'),
        FF('Calls planned this week', 'COUNTIFS({range:lapsed.contact_by},">="&{today},{range:lapsed.contact_by},"<="&({today}+6),{range:lapsed.next_step},%s)' % va('Call'), 'int')]),
    FORM('upgrade_ask_sheet', 'Upgrade Ask Sheet', 'Upgrade ask for a regular donor', 'upgrade.rank', F(('Donor', 'upgrade.donor'), ('Years given', 'upgrade.years_given'), ('Given this year', 'upgrade.this_year'), ('Given last year', 'upgrade.last_year'),
        ('Average gift', 'upgrade.avg_gift'), ('Suggested ask', 'upgrade.suggested_ask'), ('Planned ask date', 'upgrade.ask_on'), ('Verdict', 'upgrade.verdict')) + [
        FF('Extra on each gift if they agree', '%s-%s' % (LK('upgrade', 'rank', 'suggested_ask'), LK('upgrade', 'rank', 'avg_gift')), 'money'), FF('Days until the ask', '%s-{today}' % LK('upgrade', 'rank', 'ask_on'), 'int'),
        FF('Donors to ask now', 'COUNTIFS({range:upgrade.verdict},%s)' % va('Ask now'), 'int')]),
    FORM('second_gift_sheet', 'Second-gift Message Sheet', 'Second gift of a first-time donor', 'first_time.donor_id', F(('Donor', 'first_time.donor'), ('First gift', 'first_time.first_gift'), ('First gift amount', 'first_time.first_amount'),
        ('First appeal', 'first_time.first_appeal'), ('Second gift', 'first_time.second_gift'), ('Days to second gift', 'first_time.days_to_second'), ('Second gift check', 'first_time.flag'), ('Window ends', 'first_time.ask_by')) + [
        FF('Days left in the window', '%s-{today}' % LK('first_time', 'donor_id', 'ask_by'), 'int'), FF('Donors still waiting for a second gift', 'COUNTIFS({range:first_time.flag},%s)' % vb('Waiting for second gift'), 'int'),
        FF('Conversion of the same appeal', 'IFERROR(INDEX({range:conversion.conversion},MATCH(%s,{range:conversion.appeal},0)),0)' % LK('first_time', 'donor_id', 'first_appeal'), 'pct')]),
    FORM('appeal_cost_sheet', 'Appeal Cost Sheet', 'Cost of one appeal and year', 'appeal_costs.appeal_id', F(('Appeal', 'appeal_costs.appeal'), ('Year', 'appeal_costs.year'), ('Cost', 'appeal_costs.cost'), ('Channel', 'appeal_costs.channel'),
        ('Pieces sent', 'appeal_costs.pieces'), ('What it covers', 'appeal_costs.cost_note'), ('Cost per piece', 'appeal_costs.cost_piece'), ('Raised, closed years', 'appeal_costs.raised')) + [
        FF('Raised so far this year by the appeal', 'SUMIFS({range:gifts.amount},{range:gifts.appeal},%s)' % LK('appeal_costs', 'appeal_id', 'appeal'), 'money'),
        FF('Cost to raise one dollar this year', 'IFERROR(SUMIFS({range:appeal_costs.cost},{range:appeal_costs.appeal},%s,{range:appeal_costs.year},YEAR({today}))/SUMIFS({range:gifts.amount},{range:gifts.appeal},%s),0)' % (LK('appeal_costs', 'appeal_id', 'appeal'), LK('appeal_costs', 'appeal_id', 'appeal')), 'num'),
        FF('Your starting point', '{set:cost_per_dollar}', 'num')]),
    FORM('major_visit_sheet', 'Major Donor Visit Sheet', 'Visit brief for a top donor', 'top_donors.rank', F(('Donor', 'top_donors.donor'), ('Given this year', 'top_donors.amount'), ('Given last year', 'top_donors.last_year'), ('Years given', 'top_donors.years_given'),
        ('Share of the year', 'top_donors.share'), ('Running share', 'top_donors.cum_share'), ('Phone', 'top_donors.phone')) + [
        FF('Given 2 years ago', 'IFERROR(INDEX({range:giving.y2},MATCH(%s,{range:giving.donor_id},0)),0)' % LK('top_donors', 'rank', 'donor_id'), 'money'),
        FF('Given 3 years ago', 'IFERROR(INDEX({range:giving.y3},MATCH(%s,{range:giving.donor_id},0)),0)' % LK('top_donors', 'rank', 'donor_id'), 'money'),
        FF('Months of reserve if they left', 'IFERROR(%s,0)' % LK('top_donors', 'rank', 'months_if_left'), 'num')]),
    FORM('donor_care_sheet', 'Donor Care Plan Sheet', 'Care plan for one donor', 'donors.donor_id', F(('Donor', 'donors.donor'), ('Type', 'donors.type'), ('Joined via', 'donors.joined_via'), ('First gift', 'donors.first_gift'), ('Last gift', 'donors.last_gift'),
        ('Gifts', 'donors.gifts'), ('Total given', 'donors.total_given'), ('Contact person', 'donors.contact'), ('Contact preference', 'donors.contact_pref')) + [
        FF('Average gift', 'IFERROR(%s/%s,0)' % (LK('donors', 'donor_id', 'total_given'), LK('donors', 'donor_id', 'gifts')), 'money'), FF('Given this year', 'IFERROR(INDEX({range:giving.y0},MATCH({pick},{range:giving.donor_id},0)),0)', 'money'),
        FF('Given last year', 'IFERROR(INDEX({range:giving.y1},MATCH({pick},{range:giving.donor_id},0)),0)', 'money')]),
    FORM('pipeline_review_sheet', 'Pipeline Review Sheet', 'Review of one pipeline stage', 'pipeline.stage', F(('Prospects', 'pipeline.prospects'), ('Weighted value', 'pipeline.weighted')) + [
        FF('Amount asked at this stage', 'SUMIFS({range:prospects.ask_amount},{range:prospects.stage},{pick})', 'money'), FF('Share of the weighted pipeline', 'IFERROR(%s/SUM({range:pipeline.weighted}),0)' % LK('pipeline', 'stage', 'weighted'), 'pct'),
        FF('Probability, your estimate', 'IFERROR(AVERAGEIFS({range:prospects.probability},{range:prospects.stage},{pick}),0)', 'pct'), FF('Prospects with a next step overdue', 'COUNTIFS({range:prospects.stage},{pick},{range:prospects.overdue_days},">0")', 'int'),
        FF('Average ask at this stage', 'IFERROR(AVERAGEIFS({range:prospects.ask_amount},{range:prospects.stage},{pick}),0)', 'money')]),
    FORM('retention_goal_sheet', 'Retention Goal Sheet', 'Retention goal for a year and group', 'three_year.row_id', F(('Year', 'three_year.year'), ('Donor group', 'three_year.group'), ('Donors', 'three_year.donors'), ('Donors the year before', 'three_year.donors_prev'),
        ('Retained donors', 'three_year.retained'), ('Retention', 'three_year.retention'), ('Lapsed donors', 'three_year.lapsed')) + [
        FF('Your target', '{set:retention_target}', 'pct'), FF('Donors to retain to reach your target', 'ROUNDUP({set:retention_target}*%s,0)' % LK('three_year', 'row_id', 'donors_prev'), 'int'),
        FF('Donors still to win back', 'MAX(0,ROUNDUP({set:retention_target}*%s-%s,0))' % (LK('three_year', 'row_id', 'donors_prev'), LK('three_year', 'row_id', 'retained')), 'int')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
def DC(*a): return DOC(*a, NOTE) if len(a) == 5 else DOC(*a)
documents = [
    DOC('lapsed_letter', 'Lapsed Donor Letter', 'We miss you letter', 'lapsed.rank', [
        'Letter of {set:org}, dated {today}. Dear {col:lapsed.donor}, we have not received a gift from you since {col:lapsed.last_gift}, when you gave {col:lapsed.last_amount}.',
        'You gave in {col:lapsed.years_given} of the last years and your gifts have helped children, families and seniors in our community. We would be glad to hear from you and to tell you what is new.',
        'If you would like to give again, you can do it through {col:lapsed.appeal} or by calling us. A short call from {col:lapsed.caller} is planned for {col:lapsed.contact_by}.',
        'A record of each of your gifts is available on request. Please check with your accountant what your own rules need.'], ['Executive director', 'Donor'], NOTE),
    DOC('winback_letter', 'Win-Back Offer Letter', 'Welcome back letter', 'lapsed.rank', [
        'Letter of {set:org}, dated {today}. Dear {col:lapsed.donor}, thank you for the {col:lapsed.three_years} you gave us in the last three years before this one.',
        'We would like to welcome you back. A gift of any size to {col:lapsed.appeal} helps us keep our programs open this winter.',
        'You told us you prefer to be contacted by phone or mail; if that has changed, tell us and we will update your contact preference.',
        'No gift is expected. We simply wanted you to know that your support was noticed and valued.'], ['Development manager', 'Donor'], NOTE),
    DOC('upgrade_letter', 'Upgrade Ask Letter', 'Letter asking a regular donor to give a little more', 'upgrade.rank', [
        'Letter of {set:org}, dated {today}. Dear {col:upgrade.donor}, you have given in {col:upgrade.years_given} years, and this year so far you gave {col:upgrade.this_year}.',
        'Your average gift is {col:upgrade.avg_gift}. Would you consider a gift of {col:upgrade.suggested_ask} each time? This amount is our own suggestion, based on your average gift and a small raise. Please give what suits you.',
        'A small increase from many regular donors lets us plan the year with more confidence. You can reply to this letter, call us or use the online giving page.',
        'Thank you for being a regular donor.'], ['Development manager', 'Donor'], NOTE),
    DOC('second_gift_letter', 'Second-Gift Thank-You and Ask', 'Thank you for a first gift and an invitation to give again', 'first_time.donor_id', [
        'Letter of {set:org}, dated {today}. Dear {col:first_time.donor}, thank you for your first gift of {col:first_time.first_amount} on {col:first_time.first_gift}.',
        'Your gift is part of what keeps our programs running. Most donors who give a second time do so within a year; your window runs until {col:first_time.ask_by}.',
        'If you would like to give again, you can do it online, by mail or in person. Your second gift means a great deal to us.',
        'A record of your gift is available on request. Please ask your accountant what your own rules need.'], ['Development manager', 'Donor'], NOTE),
    DOC('major_proposal', 'Major-Gift Proposal Outline', 'Outline of a major-gift proposal', 'prospects.prospect_id', [
        'Proposal outline of {set:org}, dated {today}. Prepared for {col:prospects.donor}. Owner: {col:prospects.owner}. Stage: {col:prospects.stage}.',
        'The need: describe the program need in two or three sentences, with one number from your own results.',
        'The ask: {col:prospects.ask_amount}, which is the amount we suggest from a capacity of {col:prospects.capacity}. Expected decision around {col:prospects.expected_close}.',
        'The benefits: how the gift will be used, how you will report back and how you will thank the donor. Next step: {col:prospects.next_step} on {col:prospects.next_step_date}.'], ['Executive director', 'Donor'], NOTE),
    DOC('major_visit_brief', 'Major Donor Visit Brief', 'Giving history and visit brief', 'top_donors.rank', [
        'Visit brief of {set:org}, dated {today}. Donor: {col:top_donors.donor}. Contact: {col:top_donors.phone}.',
        'Giving: this year so far {col:top_donors.amount}, last year {col:top_donors.last_year}. Years given: {col:top_donors.years_given}. Share of this year: {col:top_donors.share}.',
        'Before the visit: read the last contact note, prepare one story and one number, and decide what you want to ask for.',
        'After the visit: write a thank-you within two days and record the next step and its date.'], ['Executive director', 'Development manager'], NOTE),
    DOC('retention_board', 'Retention Report for the Board', 'Retention for the board', 'donor_types.type', [
        'Report of {set:org}, dated {today}. Donor type: {col:donor_types.type}.',
        'Donors who gave this year: {col:donor_types.donors}. Retention: {col:donor_types.retention}, which is the share of last year donors of this type who gave again.',
        'Your target is {set:retention_target}, set from your own last year. The year to date is not finished, so the rate may still rise.',
        'Questions for the board: which donor groups need a plan, and who will own the second-gift and win-back follow-up?'], ['Executive director', 'Board chair'], NOTE),
    DOC('appeal_report', 'Appeal Results Report', 'Results of one appeal', 'appeal_results.appeal', [
        'Report of {set:org}, dated {today}. Appeal: {col:appeal_results.appeal}.',
        'Gifts: {col:appeal_results.gifts_n}. Donors: {col:appeal_results.donors}. Amount: {col:appeal_results.amount}. Average gift: {col:appeal_results.avg_gift}.',
        'Cost: {col:appeal_results.cost}. Cost to raise one dollar: {col:appeal_results.cost_per_dollar} against your starting point of {set:cost_per_dollar} and {col:appeal_results.last_cpd} last year.',
        'Verdict: {col:appeal_results.verdict}. The verdict is your own rule applied to your own numbers.'], ['Development manager', 'Fundraising committee'], NOTE),
    DOC('source_onepager', 'Source Comparison One-Pager', 'One channel on one page', 'source_results.channel', [
        'One-pager of {set:org}, dated {today}. Channel: {col:source_results.channel}.',
        'Cost to raise one dollar this year: {col:source_results.cost_per_dollar}. Retention of the donors this channel brought: {col:source_results.retention}.',
        'Use this page with the Source Comparison tool to decide where to put effort. A channel that costs more can still be worth it if its donors stay.',
        'These are your own figures and not a promise of any result.'], ['Development manager', 'Executive director'], NOTE),
    DOC('pipeline_report', 'Pipeline Report', 'Stage of the major-gift pipeline', 'pipeline.stage', [
        'Pipeline report of {set:org}, dated {today}. Stage: {col:pipeline.stage}.',
        'Prospects at this stage: {col:pipeline.prospects}. Weighted value: {col:pipeline.weighted}. The weights are your estimate of the chance that a prospect gives, set on the Start sheet.',
        'The major-gift goal this year is {set:major_goal}. Weighted values are planning figures and not a promise of any gift.',
        'Next: review stalled prospects and set a date for every next step.'], ['Executive director', 'Board member'], NOTE),
    DOC('concentration_note', 'Concentration and Scenario Note', 'Scenario for the board', 'scenarios.scenario', [
        'Note of {set:org}, dated {today}. Scenario: {col:scenarios.scenario}.',
        'Income lost: {col:scenarios.income_lost}, which is {col:scenarios.share_lost} of this year. Months of reserve left after the loss: {col:scenarios.months_left}.',
        'Gap to your reserve months of {set:reserve_months}: {col:scenarios.gap}. Verdict: {col:scenarios.verdict}.',
        'Free money now is {set:free_money} and an average month costs {set:monthly_expense}. These are your own figures; a scenario is not a forecast.'], ['Executive director', 'Finance committee'], NOTE),
    DOC('three_year_page', 'Three-Year Donor Story Page', 'Three-year story on one page', 'three_year.row_id', [
        'Story of {set:org}, dated {today}. Year: {col:three_year.year}. Group: {col:three_year.group}.',
        'Donors: {col:three_year.donors} against {col:three_year.donors_prev} the year before. Money: {col:three_year.amount} against {col:three_year.amount_prev}. Average gift: {col:three_year.avg_gift}.',
        'In a sentence: {col:three_year.story}. Lapsed donors: {col:three_year.lapsed}. Share from the top 5 donors: {col:three_year.top_share}.',
        'This year is to date. Use the page with your annual report numbers.'], ['Executive director', 'Board chair'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('annual_retention', 'Annual Retention Review', 'ret_detail', 'ret_detail.review_on', [('Open Retention Detail and read all donors', 0), ('Compare with your own last year', 1), ('Check new-donor and repeat-donor retention', 2), ('List the groups that fell', 3), ('Agree one action for each group', 7), ('Report to the board', 14)]),
    CHK('lapsed_outreach_chk', 'Lapsed List Outreach', 'lapsed', 'lapsed.contact_by', [('Check the rank and the last gift', -2), ('Prepare a short call script', -1), ('Call or write on the planned day', 0), ('Record the answer', 1), ('Send a thank-you for any gift', 2), ('Move to Let go after two tries', 30)]),
    CHK('pipeline_review_chk', 'Quarterly Pipeline Review', 'prospects', 'prospects.expected_close', [('Check the stage of the prospect', -90), ('Confirm the ask amount', -60), ('Check the next step date', -45), ('Update the probability, your estimate', -30), ('Agree who owns the next move', -14), ('Report the weighted value to the board', 0)]),
    CHK('ask_prep_chk', 'Major-Gift Ask Preparation', 'prospects', 'prospects.next_step_date', [('Read the giving history', -21), ('Choose the ask amount', -14), ('Write the proposal outline', -10), ('Agree who joins the meeting', -7), ('Send a short note before the meeting', -3), ('Make the ask', 0), ('Write a thank-you within two days', 2)]),
    CHK('stewardship_chk', 'Major Donor Stewardship', 'prospects', 'prospects.last_contact', [('Thank the donor within two days', 2), ('Send an impact update', 30), ('Invite to a visit or an open day', 60), ('Share a result with one number', 90), ('Plan the next ask conversation', 150)]),
    CHK('upgrade_round_chk', 'Upgrade Ask Round', 'upgrade', 'upgrade.ask_on', [('Check the donors who are due', -7), ('Check the last ask date', -5), ('Prepare the ask with the suggested amount', -3), ('Send the ask', 0), ('Record the answer', 7), ('Thank those who agreed', 8)]),
    CHK('second_gift_chk', 'Second-Gift Follow-Up', 'first_time', 'first_time.first_gift', [('Send a thank-you within two days', 2), ('Send what the gift supports', 14), ('Ask for a second gift', 45), ('Follow up by phone or mail', 90), ('Check the window end', 365)]),
    CHK('appeal_review_chk', 'Appeal Results Review', 'appeal_costs', 'appeal_costs.review_on', [('Add all costs of the appeal', -7), ('Check gifts and donors', -3), ('Work out cost per dollar', 0), ('Compare with the setting and last year', 1), ('Choose Keep, Fix or Stop', 3), ('Tell the fundraising committee', 7)]),
    CHK('source_review_chk', 'Source Review', 'appeal_costs', 'appeal_costs.review_on', [('Check the cost by channel', 0), ('Check retention by channel', 1), ('Use the Source Comparison tool', 2), ('Decide where to shift effort', 5), ('Write the decision down', 7)]),
    CHK('concentration_chk', 'Concentration Review', 'scenarios', 'scenarios.review_on', [('Check the top 5 and top 10 shares', 0), ('Run the lose-the-biggest-donor scenario', 1), ('Check months of reserve left', 2), ('Plan a call with each top donor', 7), ('Report to the finance committee', 14)]),
    CHK('year_end_chk', 'Year-End Donor Analysis', 'three_year', 'three_year.review_on', [('Wait until the last gifts are recorded', 0), ('Refresh Giving by Donor and Year', 3), ('Read the three-year story', 5), ('List lapsed donors for outreach', 7), ('Write the annual report numbers', 14), ('Plan next year retention goal', 21)]),
    CHK('founder_first_ten', 'Founder First Ten Donors', 'donors', 'donors.first_gift', [('Write the donor in the list', 0), ('Thank the donor within two days', 2), ('Add the contact preference', 3), ('Send what the gift supports', 14), ('Ask for a second gift', 60), ('Review who has not given again', 365)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
DM, ED, BK, PRN = 'Mateus', 'Grace', 'Fiona', 'Kenji'
BOARD = first_name(D.BOARD_CHAIR['name'].replace('Dr. ', '')); COMM = first_name(D.FR_MEMBER['name']); VOLN = first_name(D.VOL['name'])
M = MSG
messages = [
    M('lapsed_miss', 'Donor: we have not seen a gift since', 'lapsed', 'lapsed.phone', 'Hello {donor}, we have not seen a gift from you since {last_gift}. Could we talk about how things are going? {org}'),
    M('donor_years', 'Donor: your gifts have helped', 'donors', 'donors.phone', 'Hello {donor}, your {gifts} gifts since {first_gift} have helped children, families and seniors in our community. Thank you. {org}'),
    M('donor_impact', 'Donor: what your gift did', 'upgrade', 'upgrade.phone', 'Hello {donor}, your giving of {last_year} last year helped keep our programs open. Thank you. {org}'),
    M('donor_ask', 'Donor: would you consider a gift', 'upgrade', 'upgrade.phone', 'Hello {donor}, would you consider a gift of {suggested_ask} this year? Please give what suits you. {org}'),
    M('donor_years_row', 'Donor: thank you for years of giving', 'upgrade', 'upgrade.phone', 'Hello {donor}, thank you for giving in {years_given} years. It means a great deal to us. {org}'),
    M('second_thanks', 'Donor: your second gift', 'first_time', 'first_time.phone', 'Hello {donor}, thank you for your second gift on {second_gift}. It means a great deal and it supports our programs. {org}'),
    M('donor_visit', 'Donor: can we visit you', 'prospects', 'prospects.phone', 'Hello {donor}, we would like to visit you. Are you free on {next_step_date}? {org}'),
    M('visit_thanks', 'Donor: thank you for the visit', 'prospects', 'prospects.phone', 'Hello {donor}, thank you for our contact on {last_contact}. Our next step is: {next_step}. {org}'),
    M('fund_note', 'Donor: a note on a fund', 'gifts', 'gifts.phone', 'Hello {donor}, a short note: your gift of {amount} on {date} to the {fund} is in use. Thank you. {org}'),
    M('giving_history', 'Donor: your giving history', 'top_donors', 'top_donors.phone', 'Hello {donor}, you gave {last_year} last year and {amount} so far this year, over {years_given} years. A record you can keep is on its way. {org}'),
    M('winback_welcome', 'Lapsed donor: welcome back', 'lapsed', 'lapsed.phone', 'Hello {donor}, we would be glad to welcome you back with a gift to {appeal}. No pressure, we just miss you. {org}'),
    M('lapsed_call', 'Lapsed donor: a call is planned', 'lapsed', 'lapsed.phone', 'Hello {donor}, {caller} from our team plans to call you on {contact_by}. If another day suits you, tell us. {org}'),
    M('new_donor_thanks', 'New donor: thank you for your first gift', 'first_time', 'first_time.phone', 'Hello {donor}, thank you for your first gift of {first_amount} on {first_gift}. You will hear from us soon about what it supports. {org}'),
    M('new_donor_again', 'New donor: would you give again', 'first_time', 'first_time.phone', 'Hello {donor}, would you give again before {ask_by}? Your first gift on {first_gift} started something good. {org}'),
    M('regular_up', 'Regular donor: try a little more', 'upgrade', 'upgrade.phone', 'Hello {donor}, you give {avg_gift} each time. Would you try {suggested_ask}? Please give what suits you. {org}'),
    M('regular_thanks', 'Regular donor: your increase', 'giving', 'giving.phone', 'Hello {donor}, thank you. You gave {y0} so far this year against {y1} last year. Your increase is recorded. {org}'),
    M('donor_change', 'Donor: your giving changed', 'downgrade', 'downgrade.phone', 'Hello {donor}, we saw your giving go from {last_year} last year to {this_year} this year. Is everything well? {org}'),
    M('prospect_meet', 'Prospect: thank you for meeting', 'prospects', 'prospects.phone', 'Hello {donor}, thank you for meeting us on {last_contact}. We will follow up on {next_step_date}. {org}'),
    M('prospect_proposal', 'Prospect: a proposal is attached', 'prospects', 'prospects.phone', 'Hello {donor}, a proposal for {ask_amount} is on its way to you. Tell us what you think. {org}'),
    M('prospect_remind', 'Prospect: we agreed to talk', 'prospects', 'prospects.phone', 'Hello {donor}, a reminder that we agreed to talk on {next_step_date}. {org}'),
    M('prospect_commit', 'Prospect: thank you for your commitment', 'prospects', 'prospects.phone', 'Hello {donor}, thank you for your commitment of {ask_amount}. We will send the details soon. {org}'),
    M('dm_overdue', 'Development manager: next steps overdue', 'next_steps', 'next_steps.dm_phone', 'Hello %s, {overdue_n} next steps are overdue, the oldest {oldest} days. {org}' % DM),
    M('dm_asklist', 'Development manager: ask list', 'next_steps', 'next_steps.dm_phone', 'Hello %s, the ask list for this month has {ask_n} prospects worth {ask_value}, your estimate. {org}' % DM),
    M('dm_calls', 'Development manager: calls this week', 'lapsed', 'lapsed.dm_phone', 'Hello %s, {week_calls} lapsed donors have a call planned this week. {org}' % DM),
    M('ed_retention', 'Executive director: retention', 'ret_detail', 'ret_detail.ed_phone', 'Hello %s, retention for {group}, {year} is {retention} against {last_ret} the year before. {org}' % ED),
    M('ed_top5', 'Executive director: top 5 donors', 'top_donors', 'top_donors.ed_phone', 'Hello %s, our top 5 donors give {top5_share} of the year so far. {org}' % ED),
    M('ed_leave', 'Executive director: if a top donor left', 'top_donors', 'top_donors.ed_phone', 'Hello %s, if {donor} left, giving of {yearly} would go and free money would cover {months_if_left} months. {org}' % ED),
    M('board_pipeline', 'Board member: pipeline value', 'prospects', 'prospects.board_phone', 'Hello %s, the pipeline weighted value is {pipeline_value}, your estimate. {org}' % BOARD),
    M('board_appeals', 'Board member: appeal results', 'appeal_results', 'appeal_results.board_phone', 'Hello %s, appeal results are ready, {fix_n} appeals to fix or stop. {org}' % BOARD),
    M('committee_cost', 'Fundraising committee: cost per dollar', 'appeal_results', 'appeal_results.committee_phone', 'Hello %s, the {appeal} costs {cost_per_dollar} per dollar raised this year. {org}' % COMM),
    M('volunteer_notes', 'Volunteer: help write notes', 'lapsed', 'lapsed.vol_phone', 'Hello %s, could you help write {write_n} thank-you and win-back notes on {note_date}? {org}' % VOLN),
    M('bookkeeper_costs', 'Bookkeeper: appeal costs', 'appeal_costs', 'appeal_costs.bookkeeper_phone', 'Hello %s, appeal costs for {appeal} in {year} total {cost}. Please check them against the books. {org}' % BK),
    M('printer_letters', 'Printer and mail house: letters', 'appeal_costs', 'appeal_costs.printer_phone', 'Hello %s, we need {pieces} pieces for the {appeal} mailing. Please confirm the date. {org}' % PRN),
    M('pref_updated', 'Donor: contact preference updated', 'donors', 'donors.phone', 'Hello {donor}, we have updated your contact preference to {contact_pref}. {org}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
GV = lambda c: R('giving', c)
S_NEW, S_LAP, S_REC = tok('gstate', 'New'), tok('gstate', 'Lapsed'), tok('gstate', 'Recaptured')
def RDK(col, yr=THIS2): return 'SUMIFS({range:ret_detail.%s},{range:ret_detail.year},%s,{range:ret_detail.group},%s)' % (col, yr, ALL)
TOPS = lambda n: 'SUMIFS({range:top_donors.amount},{range:top_donors.rank},"<=%d")/SUM(%s)' % (n, GV('y0'))
CPD = R('appeal_results', 'cost_per_dollar'); APP = R('appeal_results', 'appeal')
kpis = [
    KPI('Donors this year', 'COUNTIFS(%s,">0")' % GV('y0'), 'int'), KPI('Donors last year', 'COUNTIFS(%s,">0")' % GV('y1'), 'int'),
    KPI('Donor Retention Rate this year', 'IFERROR(COUNTIFS(%s,">0",%s,">0")/COUNTIFS(%s,">0"),0)' % (GV('y0'), GV('y1'), GV('y1')), 'pct'),
    KPI('Donor Retention Rate last year', 'IFERROR(COUNTIFS(%s,">0",%s,">0")/COUNTIFS(%s,">0"),0)' % (GV('y1'), GV('y2'), GV('y2')), 'pct'),
    KPI('New-donor retention', RDK('new_ret'), 'pct'), KPI('Repeat-donor retention', RDK('repeat_ret'), 'pct'),
    KPI('New donors this year', 'COUNTIFS(%s,%s)' % (GV('state'), S_NEW), 'int'), KPI('Lapsed Donors now', 'COUNTIFS(%s,%s)' % (GV('state'), S_LAP), 'int'),
    KPI('Money lapsed, last year gifts', 'SUMIFS(%s,%s,%s)' % (GV('y1'), GV('state'), S_LAP), 'money'), KPI('Recaptured donors this year', 'COUNTIFS(%s,%s)' % (GV('state'), S_REC), 'int'),
    KPI('Donors upgraded this year', 'COUNTIFS(%s,%s)' % (GV('flag'), tok('gflag', 'Upgraded')), 'int'), KPI('Donors downgraded this year', 'COUNTIFS(%s,%s)' % (GV('flag'), tok('gflag', 'Downgraded')), 'int'),
    KPI('Average gift this year', 'SUM({range:gifts.amount})/COUNT({range:gifts.amount})', 'money'), KPI('Median gift this year', 'MEDIAN({range:gifts.amount})', 'money'),
    KPI('First-time donors, last 12 months', 'COUNTIFS({range:first_time.first_gift},">="&EDATE({today},-12))', 'int'),
    KPI('Second-gift conversion', 'IFERROR(SUM({range:conversion.gave_again})/SUM({range:conversion.first_timers}),0)', 'pct'),
    KPI('Open prospects', 'COUNTIFS({range:prospects.prospect_id},"<>",{range:prospects.stage},"<>"&%s)' % CLOSED, 'int'), KPI('Pipeline total asked', 'SUMIFS({range:prospects.ask_amount},{range:prospects.stage},"<>"&%s)' % CLOSED, 'money'),
    KPI('Pipeline weighted value, your estimate', 'SUMIFS({range:prospects.weighted_value},{range:prospects.stage},"<>"&%s)' % CLOSED, 'money'), KPI('Prospects at the ask stage', 'COUNTIFS({range:prospects.stage},%s)' % tok('pstage', 'Ask made'), 'int'),
    KPI('Next steps overdue', 'COUNTIFS({range:prospects.overdue_days},">0")', 'int'), KPI('Closed gifts this year from the pipeline', 'SUMIFS({range:prospects.ask_amount},{range:prospects.stage},%s)' % CLOSED, 'money'),
    KPI('Best appeal by cost per dollar', 'INDEX(%s,MATCH(SMALL(%s,1),%s,0))' % (APP, CPD, CPD), 'text'), KPI('Worst appeal by cost per dollar', 'INDEX(%s,MATCH(LARGE(%s,1),%s,0))' % (APP, CPD, CPD), 'text'),
    KPI('Appeals above the cost setting', 'COUNTIFS(%s,">"&{set:cost_per_dollar})' % CPD, 'int'), KPI('Share from the top 5 donors', TOPS(5), 'pct'), KPI('Share from the top 10 donors', TOPS(10), 'pct'),
    KPI('Giving at risk if the biggest donor left', 'SUMIFS({range:top_donors.yearly},{range:top_donors.rank},1)', 'money'),
    KPI('Major donors lapsing now', 'COUNTIFS(%s,%s,%s,">="&{set:major_min})' % (GV('state'), S_LAP, GV('y1')), 'int'), KPI('Donor change in three years', 'IFERROR(COUNTIFS(%s,">0")/COUNTIFS(%s,">0")-1,0)' % (GV('y0'), GV('y2')), 'pct'),
]
assert len(kpis) == 30
dashboard = {"title": "Donor Growth Dashboard", "kpis": kpis,
    "monthly": {"title": "Gifts, first gifts and asks by month", "date": "gifts.date", "series": [
        {"label": "Gifts", "sum": "gifts.amount", "date": "gifts.date"}, {"label": "First gifts", "sum": "first_time.first_amount", "date": "first_time.first_gift"},
        {"label": "Asks with a next step", "sum": "prospects.ask_amount", "date": "prospects.next_step_date"}]},
    "breakdowns": [{"title": "Gifts by appeal", "by": "gifts.appeal", "value": "gifts.amount", "agg": "sum"}, {"title": "Gifts by channel", "by": "gifts.channel", "value": "gifts.amount", "agg": "sum"},
                   {"title": "Weighted value by stage", "by": "prospects.stage", "value": "prospects.weighted_value", "agg": "sum"}, {"title": "Donors by type", "by": "donors.type", "value": "donors.total_given", "agg": "count"}]}
GA = tok('dgroup', 'All donors')
insights = {"filters": [{"label": "Channel", "list": "channel"}, {"label": "Appeal", "list": "appeal"}],
    "gauges": [
        {"title": "Retention this year, to date", "num": AGG('sum', 'ret_detail', 'ret_detail.retained', where=[('year', '=', THIS2), ('group', '=', GA)]), "den": AGG('sum', 'ret_detail', 'ret_detail.base', where=[('year', '=', THIS2), ('group', '=', GA)])},
        {"title": "New donors giving a second time", "num": AGG('count', 'first_time', where=[('flag', '=', vb('Second gift in time'))]), "den": AGG('count', 'first_time', where=[('flag', '<>', vb('Waiting for second gift'))])},
        {"title": "Lapsed donors won back", "num": AGG('sum', 'giving', 'giving.lapsed_start', where=[('y0', '>', 0)]), "den": AGG('sum', 'giving', 'giving.lapsed_start')},
        {"title": "Weighted pipeline against the goal", "num": AGG('sum', 'prospects', 'prospects.weighted_value', where=[('stage', '<>', CLOSED)]), "den": AGG('avg', 'prospects', 'prospects.goal')},
        {"title": "Appeals at or under the cost setting", "num": AGG('count', 'appeal_results', where=[('verdict', '=', va('Keep'))]), "den": AGG('count', 'appeal_results')},
        {"title": "Giving from outside the top 10 donors", "num": AGG('sum', 'giving', 'giving.y0', where=[('in_top10', '=', 0)]), "den": AGG('sum', 'giving', 'giving.y0')}],
    "charts": [
        CHART('Donors per year', 'bar', 'three_year.year', [AGG('sum', 'three_year', 'three_year.donors', where=[('group', '=', GA)], label='Donors')]),
        CHART('Money per year', 'bar', 'three_year.year', [AGG('sum', 'three_year', 'three_year.amount', where=[('group', '=', GA)], label='Money')]),
        CHART('Retention per year', 'line', 'three_year.year', [AGG('avg', 'three_year', 'three_year.retention', where=[('group', '=', GA)], label='Retention')]),
        CHART('Lapsed donors per year', 'bar', 'three_year.year', [AGG('sum', 'three_year', 'three_year.lapsed', where=[('group', '=', GA)], label='Lapsed donors')]),
        CHART('New donors per month', 'column', 'month', [AGG('count', 'first_time', date='first_time.first_gift', label='New donors')]),
        CHART('First gift amount by appeal', 'bar', 'first_time.first_appeal', [AGG('sum', 'first_time', 'first_time.first_amount', label='First gifts')]),
        CHART('Money by gift size band', 'bar', 'bands.band', [AGG('sum', 'bands', 'bands.amount', label='Money')]),
        CHART('Donors by gift size band', 'bar', 'bands.band', [AGG('sum', 'bands', 'bands.donors', label='Donors')]),
        CHART('Second-gift conversion by appeal', 'bar', 'conversion.appeal', [AGG('avg', 'conversion', 'conversion.conversion', label='Conversion')]),
        CHART('Average gift per year', 'line', 'three_year.year', [AGG('avg', 'three_year', 'three_year.avg_gift', where=[('group', '=', GA)], label='Average gift')]),
        CHART('Gift amount by appeal', 'bar', 'gifts.appeal', [AGG('sum', 'gifts', 'gifts.amount', label='Gifts')]),
        CHART('Cost per dollar by appeal', 'bar', 'appeal_results.appeal', [AGG('avg', 'appeal_results', 'appeal_results.cost_per_dollar', label='Cost per dollar')]),
        CHART('Gift amount by channel', 'bar', 'gifts.channel', [AGG('sum', 'gifts', 'gifts.amount', label='Gifts')]),
        CHART('Donors by channel', 'bar', 'gifts.channel', [AGG('sum', 'gifts', 'gifts.new_in_channel', label='Donors')]),
        CHART('Cost per dollar by channel', 'bar', 'source_results.channel', [AGG('avg', 'source_results', 'source_results.cost_per_dollar', label='Cost per dollar')]),
        CHART('Prospects by stage', 'bar', 'prospects.stage', [AGG('count', 'prospects', label='Prospects')]),
        CHART('Weighted value by stage', 'bar', 'prospects.stage', [AGG('sum', 'prospects', 'prospects.weighted_value', label='Weighted value')]),
        CHART('Ask amount by owner', 'bar', 'prospects.owner', [AGG('sum', 'prospects', 'prospects.ask_amount', label='Ask amount')]),
        CHART('Next steps by month', 'column', 'month', [AGG('count', 'prospects', date='prospects.next_step_date', label='Next steps')]),
        CHART('Prospects by capacity band', 'bar', 'prospects.capband', [AGG('count', 'prospects', label='Prospects')]),
        CHART('Top donor share per year', 'line', 'three_year.year', [AGG('avg', 'three_year', 'three_year.top_share', where=[('group', '=', GA)], label='Share from the top 5')]),
        CHART('Donors by type', 'bar', 'donors.type', [AGG('count', 'donors', label='Donors')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Retention checker", "why": "retained, new, lapsed and recaptured donors against your own last year, with the donors still to win back", "where": "Retention Checker"},
    {"name": "Lapsed donor ranker", "why": "every lapsed donor ranked by three years of giving with Call, Write or Let go, so the first calls go to the donors who matter", "where": "Lapsed Donor Ranker"},
    {"name": "Win-back planner", "why": "your estimate of who returns, the money back and the cost, with a best and a worst case", "where": "Win-Back Planner"},
    {"name": "Upgrade ask ranker", "why": "regular donors with a suggested ask from their own average gift and the date they were last asked", "where": "Upgrade Ask Ranker"},
    {"name": "Second-gift plan", "why": "first-time donors still waiting for a second gift, the day to send and the message that fits", "where": "Second-Gift Plan"},
    {"name": "Major-gift pipeline view", "why": "weighted value by stage with your own estimates against the major-gift goal", "where": "Major-Gift Pipeline View"},
    {"name": "Appeal keep-fix-stop", "why": "cost to raise one dollar by appeal against your setting and your own last year, with the cost cut or money needed", "where": "Appeal Keep-Fix-Stop"},
    {"name": "Lose-the-biggest-donor scenario", "why": "free money and months of reserve left if a top donor or the lapsing major donors do not give", "where": "Lose-the-Biggest-Donor Scenario"},
    {"name": "Overdue next-step chaser", "why": "late next steps ranked by days and value so none slips", "where": "Overdue Next-Step Chaser"},
    {"name": "Donor story writer", "why": "three years of donors and money turned into one plain sentence for the board", "where": "Donor Story Writer"}]
competitors = [
    {"what": "donor-management software", "lacks": "charges per contact every month and hides the retention, lapsed and win-back math you cannot test or change"},
    {"what": "a generic donation log spreadsheet", "lacks": "lists gifts but never shows retained, new, lapsed and recaptured donors or a ranked lapsed list"},
    {"what": "a single-purpose grant tracker template", "lacks": "has no donor growth, no second-gift conversion, no upgrade asks and no major-gift pipeline"},
    {"what": "a nonprofit accounting add-on", "lacks": "records money but never says which appeal to keep, which donors to call or what losing a top donor does to your reserve"}]
guide = [
    'Open Start here, type your organization name and read the settings: your retention target, the cost to raise one dollar, your estimates for lapsed donors who return and your stage estimates for the pipeline.',
    'Keep Donors and Giving by Donor and Year up to date: one row per donor with the total given in each of the last four years, from your gift log.',
    'Record this year gifts in Gifts with the appeal, campaign and channel so the appeal and source results fill in.',
    'Read Retention by Year and Retention Detail: retained, new, lapsed and recaptured donors, new-donor and repeat-donor retention against your own last year.',
    'Work the Lapsed List from rank 1: Call, Write or Let go. Set a caller and a contact date for each.',
    'Use Upgrade Ask List and Downgrade Watch to plan asks and calls, and First-Time Donors with Second-Gift Conversion to follow up first gifts.',
    'Keep Prospects current with stage, ask, next step and its date; Next Steps Due and Pipeline by Stage fill in.',
    'Type the cost of every appeal in Appeal Costs, then read Appeal Results and Source Results for Keep, Fix or Stop.',
    'Check Top Donors and Concentration Scenarios before you set the budget.',
    f'Use the {len(tools)} tools for weekly decisions, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text already written.',
    'A founder with volunteers and no staff can use the same sheets with a short donor list, the Lapsed Donor Ranker and the Second-Gift Plan.',
    'To replace the demo data, clear the yellow cells of each sheet, paste your own donors, gifts and prospects and check the Start here settings.',
    'This workbook runs in Excel and Google Sheets with no macros. It is not a mass-email tool, not a payment service and not accounting or legal advice.']
listing = {"title": "Nonprofit Donor Retention and Major Gifts Excel Template: Lapsed Donors, Upgrade Asks, Appeal Results, Gift Pipeline",
    "headline": "See who stays, who lapsed and who to ask next",
    "tags": ["nonprofit", "donor retention", "lapsed donors", "major gifts", "fundraising", "donor tracker", "excel template", "charity", "upgrade ask", "gift pipeline", "appeal results", "win-back", "development"],
    "description": ("Run the donor growth side of a small nonprofit in one Excel workbook. Built for an executive director, a development manager or a founder with volunteers who needs to know which donors stay, which have lapsed and who to ask next. "
        "Giving by Donor and Year shows every donor as retained, new, recaptured or lapsed. Retention Detail gives retention, new-donor retention and repeat-donor retention by donor group against your own last year. "
        "Lapsed List ranks donors to Call, Write or Let go, Upgrade Ask List suggests an ask from each regular donor's own average gift, and Downgrade Watch shows donors whose giving fell.\n\n"
        "First-Time Donors and Second-Gift Conversion show who gave a second time by appeal. Prospects holds the major-gift pipeline with stages, weighted value (your own estimate) and next steps, and Next Steps Due ranks what is overdue. "
        "Appeal Costs, Appeal Results and Source Results give the cost to raise one dollar by appeal and channel with Keep, Fix or Stop. Top Donors and Concentration Scenarios show what losing a large donor does to your months of reserve.\n\n"
        f"{len(tools)} tools answer weekly questions with a verdict, a what-if grid and your own history. Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to donors, prospects, staff and the board. "
        "The dashboard shows 30 live figures, 22 charts and 6 gauges.\n\n"
        "This is part two of an eight-part Nonprofit Organization suite. A standard .xlsx workbook with no macros and no per-contact fee, with a demo copy of sample data. Donors appear as a name, contact preference, amounts and dates only. "
        "It helps you keep track of your own numbers and does not promise any gift, grant or result. It is not a mass-email tool, a payment service, or accounting or legal advice; ask your accountant what your own rules need."),
    "features": ["Retained, new, lapsed and recaptured donors", "Retention against your own last year", "Lapsed list ranked Call, Write or Let go", "Upgrade asks from each donor's own average", "Second-gift conversion by appeal",
                 "Major-gift pipeline with weighted value", "Appeal and source cost per dollar", "Lose-the-biggest-donor scenarios", f"{len(tools)} decision tools", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p2', slug='nonprofit-donors', profession='Nonprofit Organization', name='Donor Growth and Major Gifts',
         tagline='See who stays, who lapsed and who to ask next', price_usd=29, colors={"primary": "#22577A", "accent": "#F2A541"},
         settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide, listing=listing, insights=insights,
         suite={"key": SUITE, "part": 2, "of": 8, "focus": "Donor growth, retention and major gifts"}, signature=signature, competitors=competitors,
         tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'np2.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
