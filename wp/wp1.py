"""Wedding Planning suite - part 1: Budget, Payments and Cash Plan."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp1_lists import *
from wp1_tables import *
from wp1_tools import tools, HX, RES, REC, PRM, FUND_NC, DI, OVERDUE, TB
import wp1_data as D

SUITE = 'fx-20261116-wedding'
NOTE = "Sample wording: adapt it to your own wedding."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c_): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c_, t, idc)

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('budget_line_sheet', 'Budget Line Sheet', 'One budget line with its payments', 'budget.category', F(('Planned', 'budget.planned'), ('Committed', 'budget.committed'), ('Paid', 'budget.paid'), ('Still due', 'budget.still_due'),
        ('Variance', 'budget.variance'), ('Variance percent', 'budget.variance_pct'), ('Status', 'budget.status'), ('Priority 1 to 5', 'budget.priority'), ('Couple share', 'budget.share_couple'),
        ('Partner 1 family share', 'budget.share_p1_family'), ('Partner 2 family share', 'budget.share_p2_family')),
        {"from": "schedule", "match": "schedule.category", "columns": ["kind", "due_date", "amount_due", "status"], "max": 8}),
    FORM('funding_sheet', 'Funding Contribution Sheet', 'One funding contribution', 'funding.fund_id', F(('Source', 'funding.source'), ('Date', 'funding.date'), ('Amount', 'funding.amount'), ('Status', 'funding.status'),
        ('Payer', 'funding.payer'), ('Agreed amount of the payer', 'funding.agreed_amount'), ('Paid so far by the payer', 'funding.family_paid'))),
    FORM('schedule_sheet', 'Payment Schedule Sheet', 'One scheduled payment', 'schedule.pay_id', F(('Vendor', 'schedule.vendor'), ('Category', 'schedule.category'), ('Kind', 'schedule.kind'), ('Due date', 'schedule.due_date'),
        ('Amount due', 'schedule.amount_due'), ('Payer', 'schedule.payer'), ('Paid on', 'schedule.paid_on'), ('Amount paid', 'schedule.amount_paid'), ('Method', 'schedule.method'), ('Status', 'schedule.status'),
        ('Paid by', 'schedule.paid_by'), ('Flag', 'schedule.flag'))),
    FORM('payment_sheet', 'Payment Made Sheet', 'One payment made', 'payments.payment_id', F(('Pay ID', 'payments.pay_id'), ('Date', 'payments.date'), ('Amount', 'payments.amount'), ('Paid by', 'payments.paid_by'),
        ('Method', 'payments.method'), ('Vendor', 'payments.vendor')) + [
        FF('Amount due on the schedule', 'IFERROR(INDEX({range:schedule.amount_due},MATCH(%s,{range:schedule.pay_id},0)),0)' % LK('payments', 'payment_id', 'pay_id'), 'money')]),
    FORM('hidden_sheet', 'Hidden Cost Sheet', 'One hidden cost', 'hidden.hidden_id', F(('Item', 'hidden.item'), ('Expected', 'hidden.expected'), ('Status', 'hidden.status'), ('Category', 'hidden.category'),
        ('Counted in the true budget', 'hidden.counted')) + [FF('Share of the reserve line', 'IFERROR(%s/%s,0)' % (LK('hidden', 'hidden_id', 'expected'), RES), 'pct')]),
    FORM('tip_sheet', 'Tip Envelope Sheet', 'One tip envelope', 'tips.tip_id', F(('Vendor', 'tips.vendor'), ('Gratuity included', 'tips.gratuity_included'), ('Basis', 'tips.basis'), ('Percent', 'tips.pct'), ('Flat amount', 'tips.flat'),
        ('Vendor bill', 'tips.bill'), ('Planned tip', 'tips.planned_tip'), ('Handed out by', 'tips.handed_by'), ('Envelope ready', 'tips.envelope_ready'), ('Budget category', 'tips.category'))),
    FORM('priority_sheet', 'Priority Scoring Sheet', 'One area, both partners\' scores', 'pscore.area', F(('Partner 1 score', 'pscore.score_p1'), ('Partner 2 score', 'pscore.score_p2')) + [
        FF('Average score', LK('prank', 'area', 'avg'), 'num'), FF('Rank', LK('prank', 'area', 'rank'), 'int'),
        FF('Points of difference', 'ABS(%s-%s)' % (LK('pscore', 'area', 'score_p1'), LK('pscore', 'area', 'score_p2')), 'int')]),
    FORM('date_sheet', 'Date Option Sheet', 'One date option with its quotes', 'dates.option', F(('Date of the option', 'dates.option_date'), ('Option total', 'dates.option_total'), ('Against the current date', 'dates.vs_current'),
        ('Days to the date', 'dates.days_to'), ('Months to the date', 'dates.months_to')),
        {"from": "dates", "match": "dates.option", "columns": ["category", "quote", "lead_months", "lead_flag"], "max": 8}),
    FORM('cut_sheet', 'Guest Cut Scenario Sheet', 'One guest cut step', 'ladder.step', F(('Guests removed', 'ladder.removed'), ('Headcount', 'ladder.headcount'), ('Tables', 'ladder.tables'), ('Guests charged', 'ladder.billed'),
        ('Catering', 'ladder.catering'), ('Other per-guest lines', 'ladder.other_pg'), ('Fixed cost', 'ladder.fixed'), ('Total', 'ladder.total'), ('Saving', 'ladder.saving'), ('Cost per guest', 'ladder.cost_per_guest'))),
    FORM('payer_sheet', 'Payer Agreement Sheet', 'One payer\'s agreement', 'payers.payer', F(('Agreed share', 'payers.share'), ('Agreed amount', 'payers.agreed_amount')) + [
        FF('Confirmed funding of the payer', 'SUMIFS({range:funding.amount},{range:funding.payer},{pick},{range:funding.status},"<>"&%s)' % NOTC, 'money'),
        FF('Paid so far', 'SUMIFS({range:payments.amount},{range:payments.paid_by},{pick})', 'money'),
        FF('Left to pay of the agreed amount', LK('payers', 'payer', 'agreed_amount') + '-SUMIFS({range:payments.amount},{range:payments.paid_by},{pick})', 'money')],
        {"from": "funding", "match": "funding.payer", "columns": ["date", "source", "amount", "status"], "max": 12}),
    FORM('settle_sheet', 'Settle-up Sheet', 'One payer\'s settle-up', 'settle.payer', F(('Agreed share of what is paid', 'settle.agreed'), ('Actually paid', 'settle.paid')) + [
        FF('Paid less agreed share', '%s-%s' % (LK('settle', 'payer', 'paid'), LK('settle', 'payer', 'agreed')), 'money')],
        {"from": "payments", "match": "payments.paid_by", "columns": ["date", "pay_id", "amount", "method"], "max": 12}),
    FORM('cpg_sheet', 'Cost per Guest Sheet', 'One category in the cost per guest', 'budget.category', F(('Expected cost', 'budget.expected'), ('Cost type', 'budget.cost_type'), ('Planned', 'budget.planned'), ('Cost per guest of the whole wedding', 'budget.cost_per_guest')) + [
        FF('Cost per guest of this line', 'IFERROR(%s/{set:headcount},0)' % LK('budget', 'category', 'expected'), 'money'),
        FF('Share of the whole cost', 'IFERROR(%s/SUM({range:budget.expected}),0)' % LK('budget', 'category', 'expected'), 'pct'),
        FF('Your target per guest', '{set:cost_per_guest_target}', 'money')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('budget_summary', 'Budget Summary Page', 'Budget summary: planned, committed, paid, still due', 'budget.line_id', [
        '{set:couple}, dated {today}. Budget summary for the wedding on {set:wedding_day}.',
        'Planned total: {col:budget.total_planned}. Paid so far: {col:budget.total_paid}. Still due: {col:budget.total_still_due}. Total budget: {set:total_budget}. True budget: {col:budget.true_total}.',
        'Line {col:budget.category}: planned {col:budget.planned}, committed {col:budget.committed}, paid {col:budget.paid}, still due {col:budget.still_due}. Status: {col:budget.status}.',
        'Cost per guest at {set:headcount} guests: {col:budget.cost_per_guest}.'], ['The couple', 'Parent'], NOTE),
    DOC('funding_note', 'Funding Agreement Note', 'Funding agreement note', 'payers.payer', [
        '{set:couple}, dated {today}. A note for everyone who helps to pay for the wedding on {set:wedding_day}.',
        '{col:payers.payer} agrees to cover {col:payers.share} of the total budget of {set:total_budget}, which is {col:payers.agreed_amount}.',
        'The share can be reviewed together at any time. Cash gifts are never counted as money for the wedding until they are received.'], ['The couple', 'The payer'], NOTE),
    DOC('payment_calendar', 'Payment Calendar Page', 'Payment calendar: the next 90 days', 'due60.seqno', [
        '{set:couple}, dated {today}. The next payments, from the Payment Schedule.',
        'Overdue now: {col:due60.overdue}. Due within 30 days: {col:due60.due30}. Within 60 days: {col:due60.due60}. Within 90 days: {col:due60.due90}.',
        'Payment {col:due60.seqno}: {col:due60.vendor}, {col:due60.amount}, due {col:due60.due_date}, {col:due60.days_left} days left. {col:due60.flag}.'], ['The couple', 'Parent'], NOTE),
    DOC('cash_plan', 'Cash Plan Page', 'Cash plan for one month', 'cash.month', [
        '{set:couple}, dated {today}. Cash plan for the month starting {col:cash.month}.',
        'Savings in: {col:cash.savings_in}. Family transfers in: {col:cash.family_in}. Cash gifts in: {col:cash.gifts_in}. Payments out: {col:cash.payments_out}. Net: {col:cash.net}.',
        'Closing cash: {col:cash.closing}. Flag: {col:cash.flag}. Not confirmed cash gifts are never counted.'], ['The couple', 'Parent'], NOTE),
    DOC('settle_statement', 'Settle-up Statement', 'Settle-up statement for one payer', 'settle.payer', [
        '{set:couple}, dated {today}. Settle-up statement for {col:settle.payer}.',
        'Agreed share of everything paid so far: {col:settle.agreed}. Actually paid by {col:settle.payer}: {col:settle.paid}.',
        'If paid is more than the agreed share, the others owe the difference; if less, this payer owes it. See the Settle-up between Payers tool.'], ['The couple', 'The payer'], NOTE),
    DOC('vendor_record', 'Vendor Payment Record', 'Vendor payment record', 'vendors.vendor_id', [
        '{set:couple}, dated {today}. Payment record for the {col:vendors.vendor}, {col:vendors.category}.',
        'Contract total: {col:vendors.contract_total}. Scheduled payments: {col:vendors.scheduled}. Paid so far: {col:vendors.paid_so_far}. Still due: {col:vendors.still_due}. Status: {col:vendors.status}.',
        'Check your contract for cancellation terms and the final payment date.'], ['The couple', 'The vendor'], NOTE),
    DOC('tip_labels', 'Tip Envelope Labels', 'Tip envelope label', 'tips.tip_id', [
        'Envelope for the {col:tips.vendor}. Planned tip: {col:tips.planned_tip}.',
        'Handed out by: {col:tips.handed_by}. Envelope ready: {col:tips.envelope_ready}. Tips are optional and vary by market.'], ['The couple'], NOTE),
    DOC('true_budget_page', 'True Budget Page', 'True budget of one category', 'truebud.category', [
        '{set:couple}, dated {today}. True budget for {col:truebud.category}.',
        'Planned: {col:truebud.planned}. Hidden costs still expected: {col:truebud.hidden_exp}. Planned tips: {col:truebud.planned_tips}. True budget: {col:truebud.true_budget}, {col:truebud.share} of the total.',
        'The true budget is the plan plus the hidden costs you expect. Reserve is a budget line, not an extra.'], ['The couple'], NOTE),
    DOC('cut_page', 'Cut Guests Comparison Page', 'Cut guests comparison', 'ladder.step', [
        '{set:couple}, dated {today}. If you remove {col:ladder.removed} guests the headcount is {col:ladder.headcount} at {col:ladder.tables} tables.',
        'Guests the caterer charges for: {col:ladder.billed}. Total cost: {col:ladder.total}. Saving: {col:ladder.saving}. Cost per guest: {col:ladder.cost_per_guest}.',
        'Check your contract for the minimum guarantee.'], ['The couple', 'Parent'], NOTE),
    DOC('date_page', 'Date Comparison Page', 'Date comparison', 'dates.option', [
        '{set:couple}, dated {today}. {col:dates.option}, on {col:dates.option_date}, {col:dates.days_to} days from today.',
        'Total of the five main quotes: {col:dates.option_total}. Against your current date: {col:dates.vs_current}. Lead time check: {col:dates.lead_flag}.',
        'Quotes are estimates. Check availability with each vendor.'], ['The couple', 'Parent'], NOTE),
    DOC('priorities_page', 'Priorities Page', 'Priorities of both partners', 'pscore.area', [
        '{set:couple}, dated {today}. Area: {col:pscore.area}.',
        'Partner 1 score: {col:pscore.score_p1}. Partner 2 score: {col:pscore.score_p2}. Scores run from 1 (least important) to 5 (most important).'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('family_letter', 'Family Contribution Letter', 'Family contribution request', 'funding.fund_id', [
        'Dear family, dated {today}.',
        'We are grateful for your help with the wedding on {set:wedding_day}. We would like to ask for the transfer of {col:funding.amount} by {col:funding.date}.',
        'Your agreed amount is {col:funding.agreed_amount} and {col:funding.family_paid} has been paid so far. Please tell us if a date does not suit you.',
        'With thanks, {set:couple}.'], ['The couple', 'The family'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('money_checkin', 'Monthly money check-in', 'cash', 'cash.month', [('Log every payment made this month in Payments', 3), ('Check Budget against Actual and the Over-plan Ranker', 4), ('Look at Cash by Month for the next three months', 5),
                                                                          ('Ask any vendor whose invoice is missing', 6), ('Tell your partner and the families the new totals', 7)]),
    CHK('before_paying', 'Before paying a vendor', 'schedule', 'schedule.due_date', [('Check the amount against your contract', -10), ('Ask for an invoice', -7), ('Check the money set aside covers it', -5), ('Pay and keep the receipt', 0),
                                                                                      ('Log it in Payments', 1), ('Ask the vendor to confirm', 2)]),
    CHK('before_final', 'Before each final balance', 'schedule', 'schedule.due_date', [('Check the final headcount date in your contract', -60), ('Send the final headcount', -45), ('Ask for the final invoice', -30), ('Run the Final Balance Cover Check', -21),
                                                                                       ('Move money if you are short', -14), ('Pay the final balance', -7), ('Ask the vendor to confirm', -5)]),
    CHK('funding_review', 'Funding plan review', 'funding', 'funding.date', [('Confirm the amount with the payer', -14), ('Set the date of the transfer', -7), ('Mark the row Received when it arrives', 0), ('Thank the payer', 2), ('Check the Funding Plan Check tool', 7)]),
    CHK('hidden_walk', 'Hidden-cost walk-through', 'cash', 'cash.month', [('List the extra costs in every quote', 1), ('Ask each vendor about service charge, taxes, delivery and overtime', 5), ('Add each one to Hidden Costs', 8),
                                                                         ('Mark paid costs Paid and dropped costs Not needed', 12), ('Compare the reserve with the hidden costs', 15)]),
    CHK('tip_prep', 'Tip envelope preparation', 'dates', 'dates.option_date', [('Check which vendors include a gratuity in the contract', -45), ('Decide the tip for each vendor, tips are optional', -30), ('Withdraw the cash', -14), ('Label the envelopes', -10),
                                                                              ('Hand the envelopes to the person who gives them out', -2), ('Give the envelopes out', 0)]),
    CHK('cash_gifts', 'Cash gift handling', 'funding', 'funding.date', [('Name one person who keeps the gift cards and cash safe', -7), ('Log each gift as Not confirmed', 0), ('Pay the money in and mark it Received', 3), ('Write the thank-you note', 14)]),
    CHK('family_talk', 'Budget talk with a family', 'funding', 'funding.date', [('Print the Funding Agreement Note', -14), ('Share the total and the agreed shares', -10), ('Agree the dates of the transfers', -7), ('Note any change in Payers', -3), ('Send the Family Contribution Letter', 0)]),
    CHK('date_compare', 'Date and season comparison', 'dates', 'dates.option_date', [('Ask each vendor for a quote on each date', -240), ('Enter the quotes in Date Options', -230), ('Check the lead times', -220), ('Run the Move the Date Scenario', -215),
                                                                                  ('Talk it over with the families', -210), ('Decide and tell the vendors', -200)]),
    CHK('cut_decision', 'Cut-guests decision', 'dates', 'dates.option_date', [('Run the Cut Guests Scenario', -150), ('Check the minimum guarantee in your contract', -145), ('Decide who to remove together', -140), ('Tell the caterer and the venue', -135)]),
    CHK('money_close', 'After-wedding money close', 'dates', 'dates.option_date', [('Pay every last invoice', 3), ('Hand out any tips left', 5), ('Log every cash gift', 7), ('Run the Settle-up between Payers tool', 14), ('Settle between the payers', 21), ('Save the final cost per guest', 30)]),
    CHK('small_wedding', 'Small wedding, first budget', 'cash', 'cash.month', [('Set the total budget in Settings', 0), ('Keep ten budget lines and one payer', 1), ('Enter each quote as planned', 3), ('Add each booking as committed', 7), ('Run the Funding Plan Check', 10)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
M = MSG
messages = [
    M('m_p1_next', 'Partner 1 family: the next transfer', 'funding', 'funding.ph_p1next', 'Hello, the next transfer of {amount} for the wedding is due by {date}. Thank you. {couple}'),
    M('m_p2_next', 'Partner 2 family: the next transfer', 'funding', 'funding.ph_p2next', 'Hello, the next transfer of {amount} for the wedding is due by {date}. Thank you. {couple}'),
    M('m_thanks', 'Parent: thank you for the transfer', 'funding', 'funding.ph_thanks', 'Hello, thank you, we received your transfer of {amount}. {couple}'),
    M('m_share', 'Parent: your agreed share and paid', 'funding', 'funding.ph_share', 'Hello, your agreed share is {agreed_amount} and {family_paid} has been paid so far. {couple}'),
    M('m_saving', 'Partner: the savings transfer', 'funding', 'funding.ph_saving', 'Hi, the savings transfer of {amount} is due on {date}. {couple}'),
    M('m_cost', 'Parent: what the wedding has cost so far', 'budget', 'budget.ph_parent', 'Hello, so far the wedding has cost {total_paid} of {total_planned} planned. {couple}'),
    M('m_over', 'Partner: a line is over plan', 'budget', 'budget.ph_over', 'Hi, the {category} line is {variance_pct} over plan. Can we look at it? {couple}'),
    M('m_true', 'Partner: the true budget', 'budget', 'budget.ph_first_p2', 'Hi, the true budget is {true_total}, the plan plus hidden costs. {couple}'),
    M('m_checkin', 'Partner: the money check-in', 'budget', 'budget.ph_first_p2', 'Hi, money check-in: paid {total_paid} and still due {total_still_due}. {couple}'),
    M('m_final', 'Partner: the final cost', 'budget', 'budget.ph_first_p2', 'Hi, the wedding cost {total_paid} in the end, {cost_per_guest} per guest. {couple}'),
    M('m_att_balance', 'Partner: the attire shop balance', 'schedule', 'schedule.ph_partner_att', 'Hi, the attire shop balance of {amount_due} is due on {due_date}. Money set aside is {cash}. {couple}'),
    M('m_v_paid', 'Venue: we paid, please confirm', 'schedule', 'schedule.ph_v_paid', 'Hello, we paid {amount_paid} on {paid_on}, please confirm. {couple}'),
    M('m_v_inv', 'Venue: please send the final invoice', 'schedule', 'schedule.ph_v_inv', 'Hello, please send the invoice for the final balance of {amount_due}. {couple}'),
    M('m_c_paid', 'Caterer: we paid, please confirm', 'schedule', 'schedule.ph_c_paid', 'Hello, we paid {amount_paid} on {paid_on}, please confirm. {couple}'),
    M('m_c_move', 'Caterer: can we move the instalment', 'schedule', 'schedule.ph_c_move', 'Hello, can we move the instalment of {amount_due} to {moved_date}? {couple}'),
    M('m_c_head', 'Caterer: the final headcount', 'vendors', 'vendors.ph_c_head', 'Hello, the final headcount is {headcount}, please confirm the remaining balance of {still_due}. {couple}'),
    M('m_ph_paid', 'Photographer: we paid, please confirm', 'schedule', 'schedule.ph_ph_paid', 'Hello, we paid {amount_paid} on {paid_on}, please confirm receipt. {couple}'),
    M('m_f_rev', 'Florist: the revised quote', 'vendors', 'vendors.ph_f_rev', 'Hello, the revised total is {contract_total}, can we review the design? {couple}'),
    M('m_f_inst', 'Florist: please confirm the instalment', 'schedule', 'schedule.ph_f_inst', 'Hello, please confirm the instalment of {amount_due} due on {due_date}. {couple}'),
    M('m_b_paid', 'Band or DJ: we paid, please confirm', 'schedule', 'schedule.ph_b_paid', 'Hello, we paid {amount_paid} on {paid_on}, please confirm. {couple}'),
    M('m_att_pay', 'Attire shop: we will pay the balance', 'schedule', 'schedule.ph_att', 'Hello, we will pay the balance of {amount_due} on {due_date}. {couple}'),
    M('m_att_conf', 'Attire shop: confirm balance, pick-up', 'schedule', 'schedule.ph_att', 'Hello, please confirm the balance of {amount_due} and the pick-up date. {couple}'),
    M('m_stat', 'Stationery printer: the final balance', 'vendors', 'vendors.ph_stat', 'Hello, please confirm the final balance of {still_due}. {couple}'),
    M('m_r_dep', 'Rentals: deposit and final date', 'schedule', 'schedule.ph_r_dep', 'Hello, please confirm the deposit of {amount_paid} and the final payment date of {final_date}. {couple}'),
    M('m_d_fb', 'Day-of coordinator: the final payment', 'schedule', 'schedule.ph_d_fb', 'Hello, your final payment of {amount_due} is due on {due_date}. {couple}'),
    M('m_h_dep', 'Hotel contact: the deposit was paid', 'schedule', 'schedule.ph_h_dep', 'Hello, the deposit of {amount_paid} was paid on {paid_on}. {couple}'),
    M('m_o_paid', 'Officiant: we paid, thank you', 'schedule', 'schedule.ph_o_paid', 'Hello, we paid {amount_paid} on {paid_on}, thank you. {couple}'),
    M('m_month', 'Partner: payments due this month', 'cash', 'cash.ph_month', 'Hi, payments due this month total {payments_out}. {couple}'),
    M('m_neg', 'Partner: cash goes negative', 'cash', 'cash.ph_neg', 'Hi, cash goes negative in {month}, we need {short}. {couple}'),
    M('m_score', 'Partner: please score your priorities', 'bands', 'bands.ph_score', 'Hi, please score your priorities by {score_by}. {couple}'),
    M('m_gap', 'Partner: we disagree on an area', 'bands', 'bands.ph_gap', 'Hi, we disagree on {priority_area}, can we talk tonight? {couple}'),
    M('m_tip_total', 'Partner: tip envelopes total', 'tips', 'tips.ph_p2first', 'Hi, tip envelopes total {all_tips}, who hands them out? {couple}'),
    M('m_tip_friend', 'Friend helper: hand out the tips', 'tips', 'tips.ph_friend', 'Hello, please hand out the tip envelopes on {wedding_day}. {couple}'),
    M('m_tip_parent', 'Parent: the tip envelopes ready', 'tips', 'tips.ph_parent', 'Hello, the tip envelopes are ready: {ready_count} of {tip_count}, with the name on each. {couple}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
TRUE = 'SUM(%s)' % R('truebud', 'true_budget')
kpis = [
    KPI('Total budget', TB, 'money'),
    KPI('Planned total', 'SUM(%s)' % R('budget', 'planned'), 'money'),
    KPI('Committed total', 'SUM(%s)' % R('budget', 'committed'), 'money'),
    KPI('Paid total', 'SUM(%s)' % R('budget', 'paid'), 'money'),
    KPI('Still due total', 'SUM(%s)' % R('budget', 'still_due'), 'money'),
    KPI('Committed share of budget', 'IFERROR(SUM(%s)/%s,0)' % (R('budget', 'committed'), TB), 'pct'),
    KPI('Paid share of committed', 'IFERROR(SUM(%s)/SUM(%s),0)' % (R('budget', 'paid'), R('budget', 'committed')), 'pct'),
    KPI('Budget not yet committed', '%s-SUM(%s)' % (TB, R('budget', 'committed')), 'money'),
    KPI('Reserve line', RES, 'money'),
    KPI('Expected hidden costs', HX, 'money'),
    KPI('True budget', TRUE, 'money'),
    KPI('True budget share over the total budget', 'IFERROR((%s-%s)/%s,0)' % (TRUE, TB, TB), 'pct', alert={"when": "> 0", "style": "warn"}),
    KPI('Confirmed funding', FUND_OK, 'money'),
    KPI('Funding received', REC, 'money'),
    KPI('Funding gap against the budget', '%s-%s' % (TB, FUND_OK), 'money', alert={"when": "> 0", "style": "warn"}),
    KPI('Cash gifts not confirmed', FUND_NC, 'money'),
    KPI('Money set aside now', CASH_NOW, 'money'),
    KPI('Payments due in 30 days, with overdue', DI(30), 'money'),
    KPI('Payments due in 60 days, with overdue', DI(60), 'money'),
    KPI('Overdue payments', OVERDUE, 'money', alert={"when": "> 0", "style": "bad"}),
    KPI('Final balances due in 30 days', 'SUMIFS(%s,%s,%s,%s,"<>"&%s,%s,">="&{today},%s,"<="&{today}+30)' % (R('schedule', 'amount_due'), R('schedule', 'kind'), FB, R('schedule', 'status'), PAID, R('schedule', 'due_date'), R('schedule', 'due_date')), 'money'),
    KPI('Final balances not covered', 'COUNTIFS(%s,">0")' % R('schedule', 'fb_short'), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('First month cash is negative', 'IFERROR(SMALL(%s,1),"")' % R('cash', 'neg_month'), 'date', alert={"when": "> 0", "style": "bad"}),
    KPI('Lowest month-end cash', 'MIN(%s)' % R('cash', 'ahead'), 'money'),
    KPI('Categories over plan', 'COUNTIFS(%s,">0")' % R('budget', 'variance'), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Largest overrun amount', 'MAX(0,MAX(%s))' % R('budget', 'variance'), 'money'),
    KPI('Cost per guest, committed', 'IFERROR(ROUND(SUM(%s)/{set:headcount},0),0)' % R('budget', 'committed'), 'money'),
    KPI('Planned tips total', 'SUM(%s)' % R('tips', 'planned_tip'), 'money'),
    KPI('Partner 1 family paid against agreed', 'IFERROR(SUMIFS(%s,%s,%s)/INDEX(%s,MATCH(%s,%s,0)),0)' % (R('payments', 'amount'), R('payments', 'paid_by'), P1F, R('payers', 'agreed_amount'), P1F, R('payers', 'payer')), 'pct'),
    KPI('Partner 2 family paid against agreed', 'IFERROR(SUMIFS(%s,%s,%s)/INDEX(%s,MATCH(%s,%s,0)),0)' % (R('payments', 'amount'), R('payments', 'paid_by'), P2F, R('payers', 'agreed_amount'), P2F, R('payers', 'payer')), 'pct'),
]
assert len(kpis) == 30
dashboard = {"title": "Wedding Budget Dashboard", "kpis": kpis,
    "monthly": {"title": "Payments due, payments made and funding by month", "date": "schedule.due_date", "series": [
        {"label": "Payments due", "sum": "schedule.amount_due", "date": "schedule.due_date"}, {"label": "Payments made", "sum": "payments.amount", "date": "payments.date"},
        {"label": "Funding, all statuses", "sum": "funding.amount", "date": "funding.date"}]},
    "breakdowns": [{"title": "Planned by category", "by": "budget.category", "value": "budget.planned", "agg": "sum"}, {"title": "Funding by source", "by": "funding.source", "value": "funding.amount", "agg": "sum"},
                   {"title": "Payments due by payer", "by": "schedule.payer", "value": "schedule.amount_due", "agg": "sum"}, {"title": "Hidden costs by status", "by": "hidden.status", "value": "hidden.expected", "agg": "sum"}]}


def AG(kind, table, value=None, date=None, label=None, where=None): return AGG(kind, table, value, date, where, label)
insights = {"filters": [{"label": "Category", "list": "category"}, {"label": "Payer", "list": "payer"}, {"label": "Funding source", "list": "source"}],
    "gauges": [
        {"title": "Funded against the total budget", "num": AG('sum', 'funding', 'funding.amount', where=[('status', '<>', NOTC)]), "den": AG('sum', 'budget', 'budget.planned')},
        {"title": "Committed against the total budget", "num": AG('sum', 'budget', 'budget.committed'), "den": AG('sum', 'budget', 'budget.planned')},
        {"title": "Paid against committed", "num": AG('sum', 'budget', 'budget.paid'), "den": AG('sum', 'budget', 'budget.committed')},
        {"title": "Reserve against hidden costs", "num": AG('sum', 'budget', 'budget.planned', where=[('category', '=', RESERVE)]), "den": AG('sum', 'hidden', 'hidden.expected', where=[('status', '=', EXPECTED)])},
        {"title": "Final balances covered", "num": AG('count', 'schedule', where=[('kind', '=', FB), ('status', '<>', PAID), ('fb_short', '<=', 0)]), "den": AG('count', 'schedule', where=[('kind', '=', FB), ('status', '<>', PAID)])},
        {"title": "Categories on track", "num": AG('count', 'budget', where=[('status', '=', V('On track'))]), "den": AG('count', 'budget', where=[('planned', '>', 0)])}],
    "charts": [
        CHART('Planned, committed and paid by category', 'bar', 'budget.category', [AG('sum', 'budget', 'budget.planned', label='Planned'), AG('sum', 'budget', 'budget.committed', label='Committed'), AG('sum', 'budget', 'budget.paid', label='Paid')]),
        CHART('Still due by category', 'bar', 'budget.category', [AG('sum', 'budget', 'budget.still_due', label='Still due')]),
        CHART('Variance by category', 'bar', 'budget.category', [AG('sum', 'budget', 'budget.variance', label='Committed less planned')]),
        CHART('Committed by month booked', 'column', 'month', [AG('sum', 'vendors', 'vendors.contract_total', date='vendors.booked_on', label='Contract total')]),
        CHART('Payments due by month', 'column', 'month', [AG('sum', 'schedule', 'schedule.amount_due', date='schedule.due_date', label='Payments due')]),
        CHART('Payments made by month', 'column', 'month', [AG('sum', 'payments', 'payments.amount', date='payments.date', label='Payments made')]),
        CHART('Cash closing by month', 'column', 'month', [AG('sum', 'cash', 'cash.closing', date='cash.month', label='Closing cash')]),
        CHART('Savings and family transfers by month', 'column', 'month', [AG('sum', 'cash', 'cash.savings_in', date='cash.month', label='Savings'), AG('sum', 'cash', 'cash.family_in', date='cash.month', label='Family transfers')]),
        CHART('Funding by source', 'bar', 'funding.source', [AG('sum', 'funding', 'funding.amount', label='Amount')]),
        CHART('Funding by status', 'bar', 'funding.status', [AG('sum', 'funding', 'funding.amount', label='Amount')]),
        CHART('Payments by payer', 'bar', 'payments.paid_by', [AG('sum', 'payments', 'payments.amount', label='Paid')]),
        CHART('Agreed against paid by payer', 'bar', 'settle.payer', [AG('sum', 'settle', 'settle.agreed', label='Agreed share'), AG('sum', 'settle', 'settle.paid', label='Actually paid')]),
        CHART('Payments by kind', 'bar', 'schedule.kind', [AG('sum', 'schedule', 'schedule.amount_due', label='Amount due')]),
        CHART('Payments by status', 'bar', 'schedule.status', [AG('sum', 'schedule', 'schedule.amount_due', label='Amount due')]),
        CHART('Vendors by status', 'bar', 'vendors.status', [AG('count', 'vendors', label='Vendors')]),
        CHART('Contract total by category', 'bar', 'budget.category', [AG('sum', 'budget', 'budget.vendor_total', label='Vendor contracts')]),
        CHART('Hidden costs by category', 'bar', 'budget.category', [AG('sum', 'budget', 'budget.hidden_expected', label='Hidden costs expected')]),
        CHART('Hidden costs by status', 'bar', 'hidden.status', [AG('sum', 'hidden', 'hidden.expected', label='Expected amount')]),
        CHART('Tips by vendor basis', 'bar', 'tips.basis', [AG('sum', 'tips', 'tips.planned_tip', label='Planned tips')]),
        CHART('Priority scores by area', 'bar', 'pscore.area', [AG('sum', 'pscore', 'pscore.score_p1', label='Partner 1'), AG('sum', 'pscore', 'pscore.score_p2', label='Partner 2')]),
        CHART('Cost per guest by headcount', 'line', 'ladder.step', [AG('sum', 'ladder', 'ladder.cost_per_guest', label='Cost per guest')]),
        CHART('Final balances by category', 'bar', 'budget.category', [AG('sum', 'budget', 'budget.final_due', label='Final balances due')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Final balance cover check", "why": "every final balance set against the money set aside on its due date, after the payments due before it", "where": "Final Balance Cover Check"},
    {"name": "Cash needed by month", "why": "payments due each month against savings, family transfers and money set aside, with the first month cash goes short", "where": "Cash Needed by Month"},
    {"name": "Payment mover", "why": "the unpaid payments you could ask a vendor to move later, ranked by amount and how easy they are to move", "where": "Payment Mover"},
    {"name": "Budget rebalancer", "why": "a line that runs over is covered from the most flexible categories, with the amount taken from each", "where": "Budget Rebalancer"},
    {"name": "Cut guests scenario", "why": "per-guest lines scale, the minimum guarantee and table rounding are respected, and fixed lines stay", "where": "Cut Guests Scenario"},
    {"name": "Settle-up between payers", "why": "each payer's agreed share of everything paid against what they paid, so you see who owes whom", "where": "Settle-up between Payers"},
    {"name": "Savings pace", "why": "the extra saving needed each month to close the funding gap by the last payment date", "where": "Savings Pace"},
    {"name": "True budget and reserve", "why": "the plan plus the hidden costs you expect plus tips, with the reserve tested against them", "where": "True Budget and Reserve"},
    {"name": "Move the date scenario", "why": "quotes for the big five vendors on each date you consider, with the saving and the lead-time check", "where": "Move the Date Scenario"},
    {"name": "Funding plan check", "why": "received and promised money against the total budget, never counting a cash gift until it is received", "where": "Funding Plan Check"}]
competitors = [
    {"what": "a free planning app", "lacks": "has a budget list but no committed against paid, no cash needed by month, no check that each final balance is covered and no settle-up between payers"},
    {"what": "a single budget spreadsheet", "lacks": "has one planned column but no hidden-cost reserve, no payment schedule with due dates, no cut-guests scenario and no verdicts"},
    {"what": "a printable wedding binder", "lacks": "has blank money pages but does no sums, no funding plan, no variance flags and no savings pace"},
    {"what": "a wedding website with a registry", "lacks": "shares your plans with a company, takes fees on gifts and has no true budget, no rebalancer and no private payment plan"}]
guide = [
    'Open Start here and type your names, the wedding day, the total budget and your headcount in the yellow cells. Replace demo data: clear the sample rows and type your own.',
    'Fill Payers with who pays and each agreed share, then Funding Plan with every savings transfer, family transfer and cash gift. Mark a row Received, Promised or Not confirmed; a cash gift is never counted until it is received.',
    'Enter each budget category in Budget with planned, committed (signed contracts) and paid. Still due, variance and the status fill in by themselves.',
    'List every deposit, instalment and final balance in Payment Schedule and every payment you make in Payments. Next Payments Due, Cash by Month and the dashboard follow.',
    'Add the extra costs that are not in the first quote to Hidden Costs and the tips to Tips. True Budget by Category shows the plan plus hidden costs; tips are optional and vary by market.',
    'Each partner scores the areas in Priority Scores. The Split Bands sheet suggests a split from typical starting values (edit them); the Priority Ranker names where you differ.',
    'Use the Cut Guests Scenario, the Guest Cut Ladder and the Base, Best and Worst Cost tool to see what fewer or more guests cost. Check your contract for the minimum guarantee.',
    'Use Date Options to compare quotes on other dates, then the Move the Date Scenario tool.',
    f'Use the {len(tools)} tools, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details written in.',
    'A couple with a small wedding (30 guests, no wedding party) uses the same sheets with fewer rows: one payer, ten budget lines and a few vendors.',
    'This workbook has no macros and works in Excel and Google Sheets. Print any page for a parent or a helper.',
    'Why a workbook: one flat price, no vendor ever sees your details, no fees on your gifts, your own numbers, and it works offline.',
    'What this is not: not a booking service, not a payment service, and not legal, tax or insurance advice. Every default is a typical starting value you can edit, never a promise.']
listing = {"title": "Wedding Budget Planner Excel Template: Budget vs Actual, Payment Schedule, Cash Flow by Month, Funding Plan, Settle-Up",
    "headline": "Know what you owe, when it is due and whether you have the cash",
    "tags": ["wedding budget", "budget planner", "wedding planner", "payment schedule", "cash flow", "budget vs actual", "funding plan", "wedding spreadsheet", "excel template", "hidden costs", "settle up", "cost per guest", "wedding tips"],
    "description": ("Run the money of your wedding in one Excel workbook. Built for an engaged couple planning their own wedding, paid by the couple and often by one or two families, with a parent or a helper who gets a printed page.\n\n"
        "Budget holds every category with planned, committed (money you owe under a signed contract), paid and still due, a variance and a status of On track, Watch or Over. Payers and the Funding Plan show who pays what, with savings, family transfers and cash gifts kept apart: a cash gift is never counted until it is received. "
        "Payment Schedule lists every deposit, instalment and final balance with its due date, and Next Payments Due, Cash by Month and the dashboard show what is due and when cash runs short.\n\n"
        "Hidden Costs, Tips and True Budget by Category give the plan plus the extra costs that are not in the first quote. Priority Scores, Priority Ranking and Split Bands suggest a split from typical starting values you can edit. The Guest Cut Ladder and Date Options show what fewer guests or another date would cost.\n\n"
        f"{len(tools)} tools answer weekly questions: are we funded, can we pay every final balance on its date, will we have the cash each month, which payment could move, how to cover a line that runs over, what we save if we cut guests, who owes whom and how much more to save each month. Print {len(forms)} sheets and {len(documents)} pages, follow {len(checklists)} checklists and send {len(messages)} ready text messages to families, your partner and your vendors.\n\n"
        "A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Every default is a typical starting value you can edit, and forecasts are your own estimate. It is not a booking service, not a payment service and not legal, tax or insurance advice. This is part one of the Wedding Planning suite."),
    "features": ["Budget against actual: planned, committed, paid, still due", "Funding plan that never counts an unconfirmed cash gift", "Payment schedule with due dates and flags", "Cash needed by month with the first short month", "Final balance cover check",
                 "Hidden costs, tips and the true budget", "Cut guests scenario with minimum guarantee and tables", "Settle-up between payers", "Savings pace to close the gap", f"{len(tools)} decision tools",
                 f"{len(forms)} printable sheets and {len(documents)} pages", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}

lists = BASE_LISTS + verdict_lists()
assert len(lists) <= 20, len(lists)
s = spec(id=f'{SUITE}-p1', slug='wedding-budget', profession='Wedding Planning', name='Budget, Payments and Cash Plan',
         tagline='Wedding budget, payment schedule and cash by month in one workbook', price_usd=29,
         colors={"primary": "#7A4B68", "accent": "#D9A86C"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 1, "of": 8, "focus": "Budget, payments and cash plan"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wp1.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'lists', len(lists), 'desc', len(listing['description']), 'title', len(listing['title']), 'tag', len(s['tagline']))
