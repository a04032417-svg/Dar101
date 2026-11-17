"""Household Finance suite - part 6: Net Worth and Accounts."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf6_lists import *
from hf6_tables import *
from hf6_tables import R, MS, LM, NWM, NWNOW, POT, PIV, A_, L_, CHKG, SAV, CARD, RET, BRK, PJ, PP1, PP2
from hf6_tools import tools, ASS, LIA, BACK
import hf6_data as D

SUITE = 'fx-20261116-household-finance'
NOTE = "Sample wording: adapt it to your own household."
def F(*pairs): return [FV(a, b) for a, b in pairs]
IDCOL = {'accounts': 'account_id', 'networth': 'nw_id', 'nwm': 'month', 'bnow': 'account', 'grp': 'grp_id', 'projection': 'month', 'proj_inputs': 'item', 'milestones': 'milestone', 'bcheck': 'account_id',
         'payplan': 'plan_id', 'pspend': 'ps_id', 'transfers': 'transfer_id', 'map': 'bill', 'owners': 'own_id', 'alm': 'month'}
def LK(t, c, v='{pick}'): return 'INDEX({range:%s.%s},MATCH(%s,{range:%s.%s},0))' % (t, c, v, t, IDCOL[t])
def Rg(t, c): return R(t, c)

# ------------------------------------------------------------------ forms (12)
_AID = '{pick}'
forms = [
    FORM('account_open', 'Account Opening Sheet', 'One account and its place in your net worth', 'accounts.account_id', F(
        ('Account', 'accounts.account'), ('Type', 'accounts.type'), ('Owner', 'accounts.owner'), ('Asset or liability', 'accounts.side'), ('Opened', 'accounts.opened'),
        ('Opening balance', 'accounts.opening_balance'), ('Balance now', 'accounts.balance_now')) + [
        FF('Change since opening', '%s-%s' % (LK('accounts', 'balance_now'), LK('accounts', 'opening_balance')), 'money'),
        FF('Share of its side', 'IFERROR(%s/SUMIFS(%s,%s,%s),0)' % (LK('accounts', 'balance_now'), Rg('accounts', 'balance_now'), Rg('accounts', 'side'), LK('accounts', 'side')), 'pct'),
        FF('Accounts of the same type', 'COUNTIFS(%s,%s)' % (Rg('accounts', 'type'), LK('accounts', 'type')), 'int'),
        FF('Accounts of the same owner', 'COUNTIFS(%s,%s)' % (Rg('accounts', 'owner'), LK('accounts', 'owner')), 'int')]),
    FORM('account_close', 'Account Closing Sheet', 'What leaves or arrives before an account is closed', 'accounts.account_id', F(
        ('Account', 'accounts.account'), ('Type', 'accounts.type'), ('Owner', 'accounts.owner'), ('Balance now', 'accounts.balance_now')) + [
        FF('Bills that leave this account', 'COUNTIFS(%s,%s)' % (Rg('bills', 'account_id'), _AID), 'int'), FF('Bills a month from this account', 'SUMIFS(%s,%s,%s)' % (Rg('bills', 'monthly_cost'), Rg('bills', 'account_id'), _AID), 'money'),
        FF('Payments in the last 90 days', 'COUNTIFS(%s,%s,%s,">="&({today}-90))' % (Rg('tx', 'account_id'), _AID, Rg('tx', 'date')), 'int'),
        FF('Transfers in, last 12 months', 'SUMIFS(%s,%s,%s,%s,">="&({today}-365))' % (Rg('transfers', 'amount'), Rg('transfers', 'to_account'), _AID, Rg('transfers', 'date')), 'money'),
        FF('Transfers out, last 12 months', 'SUMIFS(%s,%s,%s,%s,">="&({today}-365))' % (Rg('transfers', 'amount'), Rg('transfers', 'from_account'), _AID, Rg('transfers', 'date')), 'money')]),
    FORM('month_end', 'Month-end Balance Sheet', 'One month of balances and net worth', 'nwm.month', F(
        ('Assets', 'nwm.assets'), ('Liabilities', 'nwm.liabilities'), ('Net worth', 'nwm.net_worth'), ('Change on last month', 'nwm.chg_month'), ('Change on last year', 'nwm.chg_year'), ('Accounts typed', 'nwm.accounts_typed')) + [
        FF('Accounts in the list', 'COUNTA(%s)' % Rg('accounts', 'account_id'), 'int'), FF('Accounts missing', 'MAX(0,COUNTA(%s)-%s)' % (Rg('accounts', 'account_id'), LK('nwm', 'accounts_typed')), 'int'),
        FF('Cash and savings', LK('alm', 'cash_savings'), 'money'), FF('Retirement and brokerage', LK('alm', 'long_term'), 'money'), FF('Liquid net worth', LK('alm', 'liquid_net'), 'money')]),
    FORM('asset_sheet', 'Asset Sheet', 'One asset account and how it changed', 'bnow.account', F(
        ('Account', 'bnow.account'), ('Type', 'bnow.type'), ('Owner', 'bnow.owner'), ('Latest month typed', 'bnow.last_month'), ('Balance', 'bnow.balance'), ('Change on last month', 'bnow.chg_month'),
        ('Change on last year', 'bnow.chg_year'), ('Share of its group', 'bnow.share_group'), ('Share of assets', 'bnow.share_side')) + [
        FF('Balance a year ago', '%s-%s' % (LK('bnow', 'balance'), LK('bnow', 'chg_year')), 'money'),
        FF('Share of net worth', 'IFERROR(%s/%s,0)' % (LK('bnow', 'balance'), NWNOW), 'pct')]),
    FORM('liability_sheet', 'Liability Sheet', 'One month of cards, loans and debts', 'alm.month', F(
        ('Cards', 'alm.cards'), ('Loans', 'alm.loans'), ('Debts', 'alm.debts'), ('Cash and savings', 'alm.cash_savings'), ('Liquid net worth', 'alm.liquid_net')) + [
        FF('Liabilities over assets', 'IFERROR(%s/%s,0)' % (LIA('{pick}'), ASS('{pick}')), 'pct'), FF('Debts a year earlier', 'SUMIFS(%s,%s,EDATE({pick},-12))' % (Rg('alm', 'debts'), Rg('alm', 'month')), 'money'),
        FF('Change on a year earlier', '%s-SUMIFS(%s,%s,EDATE({pick},-12))' % (LK('alm', 'debts'), Rg('alm', 'debts'), Rg('alm', 'month')), 'money'),
        FF('Cards as a share of debts', 'IFERROR(%s/%s,0)' % (LK('alm', 'cards'), LK('alm', 'debts')), 'pct')]),
    FORM('transfer_sheet', 'Transfer Sheet', 'One transfer between your accounts', 'transfers.transfer_id', F(
        ('Date', 'transfers.date'), ('From account', 'transfers.from_name'), ('To account', 'transfers.to_name'), ('Amount', 'transfers.amount'), ('Purpose', 'transfers.purpose')) + [
        FF('Transfers that month', 'SUMIFS(%s,%s,%s)' % (Rg('transfers', 'amount'), Rg('transfers', 'month'), LK('transfers', 'month')), 'money'),
        FF('Same purpose that month', 'SUMIFS(%s,%s,%s,%s,%s)' % (Rg('transfers', 'amount'), Rg('transfers', 'month'), LK('transfers', 'month'), Rg('transfers', 'purpose'), LK('transfers', 'purpose')), 'money'),
        FF('Share of the month', 'IFERROR(%s/SUMIFS(%s,%s,%s),0)' % (LK('transfers', 'amount'), Rg('transfers', 'amount'), Rg('transfers', 'month'), LK('transfers', 'month')), 'pct'),
        FF('Same route, last 12 months', 'SUMIFS(%s,%s,%s,%s,%s,%s,">="&({today}-365))' % (Rg('transfers', 'amount'), Rg('transfers', 'from_account'), LK('transfers', 'from_account'), Rg('transfers', 'to_account'), LK('transfers', 'to_account'), Rg('transfers', 'date')), 'money')]),
    FORM('payday_sheet', 'Payday Transfer Plan Sheet', 'One partner, basis and pay rhythm', 'payplan.plan_id', F(
        ('Partner', 'payplan.partner'), ('Basis', 'payplan.basis'), ('Pay rhythm', 'payplan.rhythm'), ('Share of the joint need', 'payplan.share'), ('Transfer a month', 'payplan.transfer_month'),
        ('Paydays a month', 'payplan.paydays'), ('Transfer each payday', 'payplan.transfer_payday'), ('Take-home a month', 'payplan.takehome'), ('Kept after the transfer', 'payplan.keeps'),
        ('Own bills a month', 'payplan.own_bills'), ('Left to spend', 'payplan.left')) + [
        FF('Joint account needs a month', '{set:joint_monthly}', 'money'), FF('Transfer on an equal split', '{set:joint_monthly}/2', 'money'),
        FF('Against an equal split', '%s-{set:joint_monthly}/2' % LK('payplan', 'transfer_month'), 'money')]),
    FORM('personal_sheet', 'Personal Spending Money Sheet', 'One partner and month of personal spending money', 'pspend.ps_id', F(
        ('Month', 'pspend.month'), ('Partner', 'pspend.partner'), ('Transferred in', 'pspend.transfer_in'), ('Spent', 'pspend.spent'), ('Left', 'pspend.left'), ('Status', 'pspend.status')) + [
        FF('Spent as a share of the transfer', 'IFERROR(%s/%s,0)' % (LK('pspend', 'spent'), LK('pspend', 'transfer_in')), 'pct'),
        FF('Average spent, last 6 months', 'AVERAGEIFS(%s,%s,%s,%s,"<"&%s,%s,">="&EDATE(%s,-6))' % (Rg('pspend', 'spent'), Rg('pspend', 'partner'), LK('pspend', 'partner'), Rg('pspend', 'month'), LK('pspend', 'month'), Rg('pspend', 'month'), LK('pspend', 'month')), 'money'),
        FF('Spent in the last 12 months', 'SUMIFS(%s,%s,%s,%s,">="&EDATE(%s,-11),%s,"<="&%s)' % (Rg('pspend', 'spent'), Rg('pspend', 'partner'), LK('pspend', 'partner'), Rg('pspend', 'month'), LK('pspend', 'month'), Rg('pspend', 'month'), LK('pspend', 'month')), 'money')]),
    FORM('projection_sheet', 'Projection Inputs Sheet', 'One projection input and what it drives', 'proj_inputs.item', F(('Input', 'proj_inputs.item'), ('Value', 'proj_inputs.value'), ('Note', 'proj_inputs.note')) + [
        FF('Yearly growth in Settings, an example', '{set:growth_rate}', 'pct'), FF('Monthly amount in Settings', '{set:monthly_contribution}', 'money'), FF('Savings and investments now', POT(), 'money'),
        FF('Net worth now', NWNOW, 'money'), FF('Net worth in the years shown, an example', 'SUMIFS(%s,%s,%s*12)' % (Rg('projection', 'nw_example'), Rg('projection', 'ahead'), PIV(PITEMS[2])), 'money')]),
    FORM('milestone_sheet', 'Net Worth Milestone Sheet', 'One net worth level you want to reach', 'milestones.milestone', F(('Milestone', 'milestones.milestone'), ('Amount', 'milestones.amount'), ('Reached or expected on', 'milestones.reached_on'), ('Months to go', 'milestones.months_to_go')) + [
        FF('Net worth now', NWNOW, 'money'), FF('Still to reach', 'MAX(0,%s-%s)' % (LK('milestones', 'amount'), NWNOW), 'money'), FF('Share of the way there', 'MIN(1,IFERROR(%s/%s,0))' % (NWNOW, LK('milestones', 'amount')), 'pct'),
        FF('Years to go, an example', 'IFERROR(%s/12,0)' % LK('milestones', 'months_to_go'), 'num')]),
    FORM('check_sheet', 'Balance Check Sheet', 'One statement against the workbook', 'bcheck.account_id', F(
        ('Account', 'bcheck.account'), ('Statement balance', 'bcheck.statement'), ('Statement date', 'bcheck.statement_date'), ('Balance in the workbook', 'bcheck.calculated'), ('Difference', 'bcheck.difference'), ('Check', 'bcheck.flag')) + [
        FF('Days since the statement date', '{today}-%s' % LK('bcheck', 'statement_date'), 'int'), FF('Difference as a share of the balance', 'IFERROR(ABS(%s)/%s,0)' % (LK('bcheck', 'difference'), LK('bcheck', 'calculated')), 'pct'),
        FF('Total of all differences', 'SUM(%s)' % Rg('bcheck', 'difference'), 'money'), FF('Statements still missing', 'COUNTA(%s)-COUNT(%s)' % (Rg('bcheck', 'account_id'), Rg('bcheck', 'statement')), 'int')]),
    FORM('owner_change', 'Account Owner Change Sheet', 'What changes when an account changes owner', 'accounts.account_id', F(
        ('Account', 'accounts.account'), ('Type', 'accounts.type'), ('Owner now', 'accounts.owner'), ('Balance now', 'accounts.balance_now'), ('Asset or liability', 'accounts.side')) + [
        FF('Bills that leave it', 'COUNTIFS(%s,%s)' % (Rg('bills', 'account_id'), _AID), 'int'), FF('Bills a month from it', 'SUMIFS(%s,%s,%s)' % (Rg('bills', 'monthly_cost'), Rg('bills', 'account_id'), _AID), 'money'),
        FF('Net worth of the current owner', 'SUMIFS(%s,%s,%s,%s,0)' % (Rg('owners', 'net'), Rg('owners', 'owner'), LK('accounts', 'owner'), Rg('owners', 'months_back')), 'money'),
        FF('Accounts of the current owner', 'COUNTIFS(%s,%s)' % (Rg('accounts', 'owner'), LK('accounts', 'owner')), 'int')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
SG = ['Partner 1', 'Partner 2']
documents = [
    DOC('nw_statement', 'Net Worth Statement', 'Net worth statement for one month', 'nwm.month', [
        'Net worth statement of {set:household}, dated {today}. Month: {col:nwm.month}.', 'Assets {col:nwm.assets}; liabilities {col:nwm.liabilities}; net worth {col:nwm.net_worth}.',
        'Change on last month: {col:nwm.chg_month}. Change on last year: {col:nwm.chg_year}. Accounts typed: {col:nwm.accounts_typed}.', 'A card or loan balance is the amount owed. Figures are what you typed in Net worth.'], SG, NOTE),
    DOC('nw_account_page', 'Net Worth by Account', 'Net worth by account page', 'bnow.account', [
        'Account page of {set:household}, dated {today}. Account: {col:bnow.account} ({col:bnow.type}, {col:bnow.owner}).', 'Balance {col:bnow.balance} at {col:bnow.as_of}. Change on last month {col:bnow.chg_month}; change on last year {col:bnow.chg_year}.',
        'Share of its group {col:bnow.share_group}; share of assets or liabilities {col:bnow.share_side}. Bills that leave it each month: {col:bnow.bills_amount}.', 'Figures are what you typed in Net worth.'], SG, NOTE),
    DOC('nw_history', 'Net Worth History', 'Net worth history page', 'nwm.month', [
        'Net worth history of {set:household}, dated {today}. Month: {col:nwm.month}.', 'Net worth {col:nwm.net_worth}: assets {col:nwm.assets} less liabilities {col:nwm.liabilities}.',
        'Compared with your own past: {col:nwm.chg_month} on last month and {col:nwm.chg_year} on last year.', 'Your own history is the benchmark; no national figure is shown.'], SG, NOTE),
    DOC('group_page', 'Account Group Share Page', 'Share by account group page', 'grp.grp_id', [
        'Account group page of {set:household}, dated {today}. Group: {col:grp.group} ({col:grp.side}), {col:grp.months_back} months back.', 'Balance {col:grp.balance}. Share of assets {col:grp.share_assets}; share of net worth {col:grp.share_nw}.',
        'Change on a year earlier: {col:grp.change}.', 'Shares are estimates from your own numbers.'], SG, NOTE),
    DOC('projection_page', 'Projection Page', 'Net worth projection page, an example', 'projection.month', [
        'Net worth projection of {set:household}, dated {today}. An example, not a forecast. Month: {col:projection.month} ({col:projection.years} years ahead).',
        'With {set:monthly_contribution} added each month and an assumed growth of {set:growth_rate} a year: contributed {col:projection.contribution}; growth earned {col:projection.growth}; savings and investments {col:projection.balance}.',
        'At lower growth {col:projection.low}; at higher growth {col:projection.high}. Net worth in this example: {col:projection.nw_example}.', 'Real returns vary and can be negative. These are estimates from your numbers.'], SG, NOTE),
    DOC('map_page', 'Joint and Separate Accounts Map', 'Joint and separate accounts map', 'map.bill', [
        'Accounts map of {set:household}, dated {today}. Bill: {col:map.bill}.', 'It leaves from {col:map.account} (owner: {col:map.owner}); amount {col:map.amount}, due on day {col:map.due_day}, next due {col:map.due_date}.',
        'Who pays: {col:map.who_pays}. Keep the joint account above {set:cash_floor} before each payday.', 'Agree changes to this map together.'], SG, NOTE),
    DOC('payday_page', 'Payday Plan Page', 'Payday transfer plan', 'payplan.plan_id', [
        'Payday transfer plan of {set:household}, dated {today}. Partner: {col:payplan.partner}; basis: {col:payplan.basis}; pay rhythm: {col:payplan.rhythm}.',
        'Share of the joint need {col:payplan.share}: {col:payplan.transfer_month} a month, {col:payplan.transfer_payday} each payday ({col:payplan.paydays} paydays a month).',
        'Take-home {col:payplan.takehome}; kept after the transfer {col:payplan.keeps}; own bills {col:payplan.own_bills}; left to spend {col:payplan.left}.', 'Estimates from your numbers; review when pay changes.'], SG, NOTE),
    DOC('personal_page', 'Personal Money Page', 'Personal spending money page', 'pspend.ps_id', [
        'Personal spending money of {set:household}, dated {today}. Month: {col:pspend.month}; partner: {col:pspend.partner}.', 'Transferred in {col:pspend.transfer_in}; spent {col:pspend.spent}; left {col:pspend.left}. Status: {col:pspend.status}.',
        'Personal spending money is the amount each partner may spend without asking, agreed together.'], SG, NOTE),
    DOC('account_list', 'Account List', 'Account list page', 'accounts.account_id', [
        'Account record of {set:household}, dated {today}. Account: {col:accounts.account} ({col:accounts.account_id}).', 'Type {col:accounts.type}; owner {col:accounts.owner}; {col:accounts.side}; opened {col:accounts.opened}.',
        'Opening balance {col:accounts.opening_balance}; balance now {col:accounts.balance_now}.', 'Keep this list with your other papers; it holds no account numbers.'], SG, NOTE),
    DOC('month_end_page', 'Month-end Balances', 'Month-end balances page', 'alm.month', [
        'Month-end balances of {set:household}, dated {today}. Month: {col:alm.month}.', 'Cash {col:alm.cash}; savings {col:alm.savings}; retirement {col:alm.retirement}; brokerage {col:alm.brokerage}.',
        'Cards {col:alm.cards}; loans {col:alm.loans}. Liquid net worth {col:alm.liquid_net}.', 'Figures are what you typed in Net worth.'], SG, NOTE),
    DOC('change_note', 'Net Worth Change Note', 'Net worth change note', 'bnow.account', [
        'Net worth change note of {set:household}, dated {today}. Account: {col:bnow.account}.', 'Its effect on net worth since last month: {col:bnow.nw_effect} (balance change {col:bnow.chg_month}).',
        'Compare with the other accounts in the Net Worth Change Explainer tool.', 'Estimates from the balances you typed.'], SG, NOTE),
    DOC('year_summary', 'Year Net Worth Summary', 'Year net worth summary by owner', 'owners.own_id', [
        'Net worth summary of {set:household}, dated {today}. Owner: {col:owners.owner}; {col:owners.months_back} months back.', 'Assets {col:owners.assets}; liabilities {col:owners.liabilities}; net worth {col:owners.net}.',
        'Bills a month from this owner\'s accounts: {col:owners.bills_amount}.', 'Review it together at year end; figures are estimates from your numbers.'], SG, NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('month_end_chk', 'Month-end Balances Steps', 'nwm', 'nwm.month', [('Download or open each statement', 28), ('Type one balance per account in Net worth', 30), ('Check Accounts typed in Net worth by month', 31), ('Run the Month-end Snapshot Check', 31), ('Read the Net Worth Change Explainer', 32)]),
    CHK('snapshot_chk', 'Net Worth Snapshot Steps', 'nwm', 'nwm.month', [('Read Net Worth Now', 32), ('Read Net Worth by Group', 32), ('Compare with your own history', 33), ('Print the Net Worth Statement', 34), ('Talk it through with your partner', 36)]),
    CHK('balance_chk', 'Balance Check Steps', 'bcheck', 'bcheck.statement_date', [('Type the statement balance of each account', 0), ('Read the difference column', 1), ('Run the Balance Reconcile tool', 1), ('Find the missing or doubled entry', 3), ('Ask your bank branch if a difference stays', 7)]),
    CHK('payday_chk', 'Payday Transfers Steps', 'transfers', 'transfers.date', [('Read the Payday Transfer Plan', -2), ('Check the Joint Account Cover tool', -1), ('Move the amount to the joint account', 0), ('Move personal spending money to each partner', 1), ('Type the transfers in Transfers', 2)]),
    CHK('new_account_chk', 'New Account Steps', 'accounts', 'accounts.opened', [('Type the account in Accounts', 0), ('Type its first balance in Net worth', 1), ('Add the bills that leave it in Bills', 3), ('Check the Joint and Separate Map', 5), ('Tell your partner and update standing transfers', 7)]),
    CHK('closed_chk', 'Account Closed Steps', 'accounts', 'accounts.opened', [('Move the remaining balance', 0), ('Move every bill to another account', 1), ('Check the Account Closing Sheet', 2), ('Type a zero balance in Net worth', 3), ('Keep the final statement with your papers', 14)]),
    CHK('quarterly_chk', 'Quarterly Net Worth Review', 'nwm', 'nwm.month', [('Type the balances for the quarter end', 30), ('Read Net Worth Against Own History', 32), ('Check the milestones', 33), ('Review the Savings Spread', 34), ('Agree one change for the next quarter', 36)]),
    CHK('joint_review_chk', 'Joint and Separate Review Steps', 'accounts', 'accounts.opened', [('Read the Joint and Separate Map', 0), ('Check the joint account against the cash floor', 1), ('Check each partner\'s personal spending money', 2), ('Move any bill to a better account', 5), ('Agree the payday transfers', 7)]),
    CHK('retire_chk', 'Retirement and Brokerage Update', 'networth', 'networth.as_of', [('Find the latest statement of each account', 0), ('Type the balances in Net worth', 1), ('Check the change on last month', 2), ('Note any contribution change in Projection inputs', 5)]),
    CHK('projection_chk', 'Projection Update Steps', 'projection', 'projection.month', [('Check the monthly amount in Settings', 0), ('Check the example growth in Settings', 1), ('Read the Net Worth Projection tool', 2), ('Run the Projection Sensitivity tool', 3), ('Remember: an example, not a forecast', 4)]),
    CHK('year_end_chk', 'Year-end Net Worth Steps', 'nwm', 'nwm.month', [('Type the December balances', 31), ('Print the Year Net Worth Summary', 33), ('Send the year-end balances to your tax preparer if asked', 35), ('Set next year\'s milestones', 40), ('Review accounts you no longer use', 45)]),
    CHK('single_chk', 'Single Adult First Net Worth', 'accounts', 'accounts.opened', [('List your accounts in Accounts and leave partner rows empty', 0), ('Type one balance for each in Net worth', 1), ('Read Net Worth Now', 2), ('Set your monthly amount in Settings', 3), ('Check Net Worth Projection', 7)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('p2_nw', 'Partner 2: net worth and change', 'nwm', 'nwm.p2_phone', 'Hello {partner2}, net worth at {month} is {net_worth}, a change of {chg_month} on last month. {household}'),
    M('p2_typed', 'Partner 2: balances are typed', 'nwm', 'nwm.p2_phone', 'Hello {partner2}, the month-end balances for {month} are typed ({accounts_typed} accounts). Please check yours by {date}. {household}'),
    M('p2_type_bal', 'Partner 2: type your balance', 'bnow', 'bnow.p2_phone', 'Hello {partner2}, please type the balance of {account} by {date}. Thank you. {household}'),
    M('p2_payday', 'Partner 2: payday transfer', 'payplan', 'payplan.p2_phone', 'Hello {partner2}, the payday transfer of {transfer_payday} to the joint account is on {date}. {household}'),
    M('p2_personal', 'Partner 2: personal spending money', 'pspend', 'pspend.p2_phone', 'Hello {partner2}, your personal spending money for {month} has {left} left. {household}'),
    M('p2_projection', 'Partner 2: projection example', 'projection', 'projection.p2_phone', 'Hello {partner2}, the projection shows {nw_example} in {years} years, an example only, not a forecast. {household}'),
    M('p1_year', 'Partner 1: up on last year', 'nwm', 'nwm.p1_phone', 'Hello {partner1}, net worth at {month} changed by {chg_year} on last year. {household}'),
    M('p1_retire', 'Partner 1: retirement balance', 'bnow', 'bnow.p1_phone', 'Hello {partner1}, the balance of {account} is {balance} at {as_of}. {household}'),
    M('p1_type_bal', 'Partner 1: type your balance', 'bnow', 'bnow.p1_phone', 'Hello {partner1}, please type the balance of {account} by {date}. Thank you. {household}'),
    M('p1_personal', 'Partner 1: personal spending money', 'pspend', 'pspend.p1_phone', 'Hello {partner1}, your personal spending money for {month} has {left} left. {household}'),
    M('p1_joint', 'Partner 1: joint account needs', 'bnow', 'bnow.p1_phone', 'Hello {partner1}, the joint account needs {cover_need} by {date} to stay above our floor. {household}'),
    M('hm_statement', 'Household member: statement ready', 'nwm', 'nwm.member_phone', 'Hello, the net worth statement for {month} is ready to read. {household}'),
    M('hm_debts', 'Household member: debts and assets', 'nwm', 'nwm.member_phone', 'Hello, at {month} our debts are {liabilities} against assets of {assets}. {household}'),
    M('hm_map', 'Household member: accounts map updated', 'map', 'map.member_phone', 'Hello, the accounts map was updated on {date}. {household}'),
    M('hm_review', 'Household member: quarterly review', 'nwm', 'nwm.member_phone', 'Hello, we plan the quarterly net worth review on {date}. {household}'),
    M('bk_balance', 'Bank branch: send the balance', 'accounts', 'accounts.bank_phone', 'Hello, please send the balance of {account} on {date}. Thank you. {household}'),
    M('bk_confirm', 'Bank branch: confirm our record', 'bcheck', 'bcheck.bank_phone', 'Hello, please confirm the balance of {account} against our record of {calculated}. Thank you. {household}'),
    M('bk_statement', 'Bank branch: send the statement', 'accounts', 'accounts.bank_phone', 'Hello, please send the statement of {account} for {month}. Thank you. {household}'),
    M('bk_standing', 'Bank branch: standing transfer', 'payplan', 'payplan.bank_phone', 'Hello, please set up a standing transfer of {transfer_payday} on day {day}. What is needed? {household}'),
    M('bk_owner', 'Bank branch: change the owner', 'accounts', 'accounts.bank_phone', 'Hello, we ask to change the owner of {account} to {owner}. What is needed? {household}'),
    M('bk_close', 'Bank branch: close an account', 'accounts', 'accounts.bank_phone', 'Hello, we want to close {account}. Please confirm the steps. {household}'),
    M('bk_interest', 'Bank branch: interest for the year', 'accounts', 'accounts.bank_phone', 'Hello, please confirm the interest on {account} for {year}. Thank you. {household}'),
    M('bk_open', 'Bank branch: open a savings account', 'accounts', 'accounts.bank_phone', 'Hello, we want to open a savings account for a new goal. What are the terms? {household}'),
    M('bk_arrived', 'Bank branch: did the transfer arrive', 'transfers', 'transfers.bank_phone', 'Hello, please confirm that the transfer of {amount} on {date} arrived. Thank you. {household}'),
    M('bk_loan', 'Bank branch: loan balance', 'accounts', 'accounts.bank_phone', 'Hello, please send the loan balance of {account} on {date}. Thank you. {household}'),
    M('pay_split', 'Payroll office: split my pay', 'accounts', 'accounts.payroll_phone', 'Hello, please split my pay between {joint_name} and {account}. What do you need from me? {household}'),
    M('pay_where', 'Payroll office: where is my pay paid', 'accounts', 'accounts.payroll_phone', 'Hello, please confirm which account my pay is deposited to; we hold {account}. {household}'),
    M('pay_retire', 'Payroll office: retirement statement', 'bnow', 'bnow.payroll_phone', 'Hello, please send the retirement balance statement for {account}. Thank you. {household}'),
    M('tax_year', 'Tax preparer: year-end balances', 'nwm', 'nwm.tax_phone', 'Hello, here are our year-end balances for {year}: assets {assets}, liabilities {liabilities}, net worth {net_worth}. {household}'),
    M('tax_statements', 'Tax preparer: which statements', 'accounts', 'accounts.tax_phone', 'Hello, please tell us which statements you need for the interest and investment accounts, for example {account}. {household}'),
    M('ins_owner', 'Insurance agent: confirm the owner', 'map', 'map.insurance_phone', 'Hello, please confirm that the owner on the policy matches {owner}. Thank you. {household}'),
    M('landlord', 'Landlord: payment account changed', 'map', 'map.landlord_phone', 'Hello, our payment now leaves from {account} on {due_date}. Please tell us if you see a problem. {household}'),
    M('utility', 'Utility company: change the account', 'map', 'map.utility_phone', 'Hello, please change the payment account to {account}. What do you need from us? {household}'),
    M('gp_thanks', 'Grandparent: family goals account', 'bnow', 'bnow.member_phone', 'Hello, thank you for your help. The family goals account holds {balance} at {as_of}. {household}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
BN_ = lambda c: R('bnow', c)
def BT(t): return 'SUMIFS(%s,%s,%s)' % (BN_('balance'), BN_('type'), t)
def OW(o): return 'SUMIFS(%s,%s,%s,%s,0)' % (R('owners', 'net'), R('owners', 'owner'), o, R('owners', 'months_back'))
LBELOW = 'SUMPRODUCT(MAX((%s<%s)*%s))' % (R('nwm', 'net_worth'), NWNOW, R('nwm', 'month'))
kpis = [
    KPI('Net worth now', NWNOW, 'money'), KPI('Net worth last month', NWM(BACK(1)), 'money'), KPI('Net worth last year', NWM(BACK(12)), 'money'),
    KPI('Change on last month', '%s-%s' % (NWNOW, NWM(BACK(1))), 'money'), KPI('Change on last year', '%s-%s' % (NWNOW, NWM(BACK(12))), 'money'),
    KPI('Total assets', ASS(LM), 'money'), KPI('Total liabilities', LIA(LM), 'money'), KPI('Cash in checking accounts', BT(CHKG), 'money'), KPI('Savings balances', BT(SAV), 'money'),
    KPI('Emergency savings balance', 'SUMIFS(%s,%s,{set:emergency_account})' % (BN_('balance'), BN_('account')), 'money'), KPI('Retirement balances', BT(RET), 'money'), KPI('Brokerage balance', BT(BRK), 'money'),
    KPI('Card balances', BT(CARD), 'money'), KPI('Loan balances', BT(tok('atype', 'Loan')), 'money'),
    KPI('Liquid net worth', 'SUMIFS(%s,%s,%s)' % (R('alm', 'liquid_net'), R('alm', 'month'), LM), 'money'),
    KPI('Liabilities over assets', 'IFERROR(%s/%s,0)' % (LIA(LM), ASS(LM)), 'pct'),
    KPI('Cash and savings share of assets', 'IFERROR((%s+%s)/%s,0)' % (BT(CHKG), BT(SAV), ASS(LM)), 'pct'), KPI('Retirement share of assets', 'IFERROR(%s/%s,0)' % (BT(RET), ASS(LM)), 'pct'),
    KPI('Net worth of partner 1 accounts', OW(PP1), 'money'), KPI('Net worth of partner 2 accounts', OW(PP2), 'money'), KPI('Net worth of joint accounts', OW(PJ), 'money'),
    KPI('Accounts typed this month', 'COUNTIFS(%s,%s)' % (R('networth', 'month'), MS), 'int'), KPI('Accounts missing a balance this month', 'MAX(0,COUNTA(%s)-COUNTIFS(%s,%s))' % (R('accounts', 'account_id'), R('networth', 'month'), MS), 'int'),
    KPI('Largest account', 'MAX(%s)' % BN_('asset_balance'), 'money'), KPI('Smallest asset account', 'MIN(%s)' % BN_('asset_balance'), 'money'),
    KPI('Transfers last 30 days', 'SUMIFS(%s,%s,">="&({today}-30))' % (R('transfers', 'amount'), R('transfers', 'date')), 'money'),
    KPI('Personal money transfers this month', 'SUMIFS(%s,%s,%s,%s,%s)' % (R('transfers', 'amount'), R('transfers', 'month'), MS, R('transfers', 'purpose'), tok('purpose', 'Personal spending money')), 'money'),
    KPI('Joint balance now', 'SUMIFS(%s,%s,{set:joint_account})' % (BN_('balance'), BN_('account_id')), 'money'),
    KPI('Projection in 5 years (example)', 'SUMIFS(%s,%s,60)' % (R('projection', 'nw_example'), R('projection', 'ahead')), 'money'),
    KPI('Months since net worth was last lower', 'IF(%s=0,COUNT(%s),(YEAR(%s)-YEAR(%s))*12+MONTH(%s)-MONTH(%s))' % (LBELOW, R('nwm', 'month'), LM, LBELOW, LM, LBELOW), 'int'),
]
assert len(kpis) == 30
dashboard = {"title": "Net Worth Dashboard", "kpis": kpis,
    "monthly": {"title": "Assets, liabilities and net worth by month", "date": "nwm.month", "series": [
        {"label": "Assets", "sum": "nwm.assets", "date": "nwm.month"}, {"label": "Liabilities", "sum": "nwm.liabilities", "date": "nwm.month"}, {"label": "Net worth", "sum": "nwm.net_worth", "date": "nwm.month"}]},
    "breakdowns": [{"title": "Balance by account type", "by": "accounts.type", "value": "accounts.balance_now", "agg": "sum"},
                   {"title": "Balance by owner", "by": "accounts.owner", "value": "accounts.balance_now", "agg": "sum"},
                   {"title": "Bills by cycle", "by": "bills.cycle", "value": "bills.amount", "agg": "sum"},
                   {"title": "Transfers by purpose", "by": "transfers.purpose", "value": "transfers.amount", "agg": "sum"}]}

def AM(t, c, date=None, label=None, where=None): return AGG('sum', t, '%s.%s' % (t, c), date=('%s.%s' % (t, date)) if date else None, where=where, label=label)
def AV(t, c, label): return AGG('avg', t, '%s.%s' % (t, c), label=label)
NOW = [('months_back', '=', 0)]
insights = {"filters": [{"label": "Owner", "list": "person"}, {"label": "Account group", "list": "atype"}],
    "gauges": [
        {"title": "Accounts typed this month", "num": AGG('sum', 'bnow', 'bnow.typed_now'), "den": AGG('count', 'bnow')},
        {"title": "Liquid net worth against 3 months", "num": AGG('sum', 'bnow', 'bnow.liquid_part'), "den": AGG('sum', 'bnow', 'bnow.liquid_need')},
        {"title": "Liabilities now against last year", "num": AGG('sum', 'owners', 'owners.liabilities', where=NOW), "den": AGG('sum', 'owners', 'owners.liabilities', where=[('months_back', '=', 12)])},
        {"title": "Net worth against own last year", "num": AGG('sum', 'owners', 'owners.net', where=NOW), "den": AGG('sum', 'owners', 'owners.net', where=[('months_back', '=', 12)])},
        {"title": "Emergency fund against the target", "num": AGG('sum', 'bnow', 'bnow.emerg_part'), "den": AGG('sum', 'bnow', 'bnow.emerg_need')},
        {"title": "Balance checks matched", "num": AGG('count', 'bcheck', where=[('flag', '=', V('Matches'))]), "den": AGG('count', 'bcheck')}],
    "charts": [
        CHART('Net worth per month', 'column', 'month', [AM('nwm', 'net_worth', 'month', 'Net worth')]),
        CHART('Assets and liabilities per month', 'column', 'month', [AM('nwm', 'assets', 'month', 'Assets'), AM('nwm', 'liabilities', 'month', 'Liabilities')]),
        CHART('Net worth change per month', 'column', 'month', [AM('nwm', 'chg_month', 'month', 'Change on last month')]),
        CHART('Net worth by account group', 'bar', 'grp.group', [AM('grp', 'balance', None, 'Balance now', NOW)]),
        CHART('Assets by account type', 'bar', 'grp.group', [AM('grp', 'asset_balance', None, 'Assets', NOW)]),
        CHART('Liabilities by type', 'bar', 'grp.group', [AM('grp', 'liab_balance', None, 'Liabilities', NOW)]),
        CHART('Balance by account now', 'bar', 'bnow.account', [AM('bnow', 'balance', None, 'Balance')]),
        CHART('Savings balances per month', 'column', 'month', [AM('alm', 'savings', 'month', 'Savings')]),
        CHART('Retirement and brokerage per month', 'column', 'month', [AM('alm', 'retirement', 'month', 'Retirement'), AM('alm', 'brokerage', 'month', 'Brokerage')]),
        CHART('Cards and loans per month', 'column', 'month', [AM('alm', 'cards', 'month', 'Cards'), AM('alm', 'loans', 'month', 'Loans')]),
        CHART('Checking balances per month', 'column', 'month', [AM('alm', 'cash', 'month', 'Checking')]),
        CHART('Net worth by owner', 'bar', 'owners.owner', [AM('owners', 'net', None, 'Net worth', NOW)]),
        CHART('Share of assets by group', 'bar', 'grp.group', [AM('grp', 'share_assets', None, 'Share of assets', NOW)]),
        CHART('Liquid and long-term per month', 'stacked', 'month', [AM('alm', 'cash_savings', 'month', 'Cash and savings'), AM('alm', 'long_term', 'month', 'Retirement and brokerage')]),
        CHART('Transfers per month', 'column', 'month', [AM('transfers', 'amount', 'date', 'Transfers')]),
        CHART('Transfers by purpose', 'bar', 'transfers.purpose', [AM('transfers', 'amount', 'date', 'Transfers')]),
        CHART('Personal spending money per month', 'stacked', 'month', [AM('pspend', 'transfer_in', 'month', 'Partner 1', [('partner', '=', P1)]), AM('pspend', 'transfer_in', 'month', 'Partner 2', [('partner', '=', P2)])]),
        CHART('Bills by account', 'bar', 'bnow.account', [AM('bnow', 'bills_amount', None, 'Bills a month')]),
        CHART('Bills by owner', 'bar', 'owners.owner', [AM('owners', 'bills_amount', None, 'Bills a month', NOW)]),
        CHART('Projection balance by year', 'line', 'projection.year_no', [AV('projection', 'nw_example', 'Net worth, an example')]),
        CHART('Projection at three growth rates', 'line', 'projection.year_no', [AV('projection', 'low', 'Lower growth'), AV('projection', 'balance', 'Growth you typed'), AV('projection', 'high', 'Higher growth')]),
        CHART('Accounts by type', 'bar', 'accounts.type', [AGG('count', 'accounts', label='Accounts')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Net worth now", "why": "assets less liabilities with the change since last month and last year in one line", "where": "Net Worth Now"},
    {"name": "Net worth by account group", "why": "how much of net worth sits in cash, savings, retirement, brokerage and debts", "where": "Net Worth by Group"},
    {"name": "Net worth change explainer", "why": "the accounts that moved net worth this month, so a jump is explained in one line", "where": "Net Worth Change Explainer"},
    {"name": "Net worth projection", "why": "your monthly amount and an assumed growth projected forward, an example and not a forecast", "where": "Net Worth Projection"},
    {"name": "Years to a net worth target", "why": "a closed-form estimate of how long a level takes at the amount you add", "where": "Years to a Net Worth Target"},
    {"name": "Payday transfer plan", "why": "what each partner moves to the joint account on each payday and what is left to spend", "where": "Payday Transfer Plan"},
    {"name": "Joint against separate map", "why": "every bill by the account it leaves from, so the joint account covers what it must", "where": "Joint and Separate map"},
    {"name": "Joint account cover", "why": "the joint balance against bills due before payday, with the amount to move in and how soon", "where": "Joint Account Cover"},
    {"name": "Balance reconcile", "why": "statement balances typed against the workbook, with the account that is out", "where": "Balance Reconcile"}]
competitors = [
    {"what": "budgeting app with a monthly subscription and bank links", "lacks": "charges every month, loses its bank links and cannot show a joint against separate accounts map with the transfer before the childcare bill"},
    {"what": "free net worth sheet", "lacks": "one balance column with no change explainer, no projection range and no balance reconcile against statements"},
    {"what": "single-purpose budget template", "lacks": "no assets and liabilities by month, no net worth by owner and no payday transfer plan for two partners"},
    {"what": "retirement calculator sheet", "lacks": "projects one pot only, with no cards and loans, no liquid net worth and no years to a net worth target"}]
guide = [
    'Start here: open Start and type the household name, both partner names, your monthly amount and the example growth in the yellow cells.',
    'Replace demo data, step 1: in Accounts list your own accounts (a card or loan balance is the amount owed) and clear the demo rows; a single adult lists fewer accounts and leaves partner 2 empty.',
    'Replace demo data, step 2: in Net worth type one balance per account for each month you want; the monthly pages, shares and charts fill in by themselves.',
    'Replace demo data, step 3: in Bills list each bill with the account it leaves from, and type your transfers; the Joint and Separate map and the payday plan follow.',
    'Pay-day routine: move the transfer from the Payday Transfer Plan to the joint account, move personal spending money and type both in Transfers.',
    'Weekly routine: look at Joint Account Cover and the Balances now page before the next payday.',
    'Month-close routine, in this order: type every account balance in Net worth, run the Month-end Snapshot Check, read Net Worth Now and the Change Explainer, type statements in Balance check, print the Net Worth Statement.',
    'The projection and the target tools use your monthly amount and an example growth rate: an example, not a forecast.',
    'A single adult with one income and no children can use most sheets and leave partner 2 rows, personal spending money and shared accounts empty.',
    f'Use the {len(tools)} tools, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details written in.',
    'Every verdict is an estimate from your numbers; any range shown is a typical range, check your own numbers.',
    'Why a workbook: one flat price, no yearly renewal, your data stays with you and there is nothing to link or re-connect; you type or paste your own data. It works in Excel and Google Sheets with no macros.',
    'What this is not: it is not a bank app, and not tax, legal, investment or credit advice.']
listing = {"title": "Net Worth Tracker Excel Template: Assets, Liabilities, Net Worth Projection, Joint and Separate Accounts, Payday Transfers",
    "headline": "Track net worth by month and plan the joint account transfers",
    "tags": ["net worth tracker", "net worth template", "assets liabilities", "household finance", "joint account", "couples budget", "payday transfers", "balance check", "excel template", "no subscription", "family finance", "net worth projection", "account tracker"],
    "description": ("Know what you own and owe in one Excel workbook, for a couple, a family or a single adult. Type one balance per account each month and the workbook shows assets, liabilities and net worth by month, the change on last month and on last year, "
        "the share by account group and by owner, and which accounts moved net worth this month.\n\n"
        "A projection from your monthly amount and an assumed yearly growth shows an example at three growth rates, with years to a net worth target and the monthly amount that reaches a level by a date. Every projection is an example, not a forecast.\n\n"
        "The Joint and Separate map shows every bill by the account it leaves from. The Payday Transfer Plan gives each partner's transfer to the joint account on every payday and what is left to spend, Joint Account Cover compares the joint balance with the bills due before payday, "
        "and Personal Spending Money follows each partner's own account. Balance Reconcile checks the balances you typed from statements against the workbook.\n\n"
        f"{len(tools)} tools, {len(forms)} printable sheets, {len(documents)} documents, {len(checklists)} checklists and {len(messages)} ready text messages to partners, the grandparent, your bank branch, the payroll office and your tax preparer are included. "
        "This is part six of the Household Finance suite. A standard .xlsx workbook that works in Excel and Google Sheets, with no macros, no subscription and no bank links: you type or paste your own data. "
        "It is a household money kit, not a bank app, and not tax, legal, investment or credit advice. Every verdict is an estimate from your own numbers."),
    "features": ["Net worth by month with change on last month and last year", "Share by account group and by owner", "Net worth change explainer", "Projection at three growth rates, an example", "Years to a net worth target and the monthly amount to reach it",
                 "Joint and separate accounts map", "Payday transfer plan for two partners", "Joint account cover before payday", f"{len(tools)} tools and {len(forms)} printable sheets", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "One flat price, no subscription, no bank links"]}
for _t in tables: _t['rows'] = max(50, _t['rows'])
s = spec(id=f'{SUITE}-p6', slug='household-finance-networth', profession='Household Finance', name='Net Worth and Accounts',
         tagline='Track net worth by month and plan the joint account transfers', price_usd=29,
         colors={"primary": "#1F5F5B", "accent": "#F2B134"}, settings=settings, lists=base_lists + verdict_lists(), tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 6, "of": 8, "focus": "Net worth and accounts"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hf6.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'lists', len(s['lists']))
