"""Doula Business suite part 2: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du2_lists import *
import du2_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def PH(role, key_, label): return CA(key_, label, 'text', 'IFERROR(INDEX({range:team.phone},MATCH(%s,{range:team.role},0))&"","")' % tok('role', role), 18)
def OWNER_PH(): return PH('Owner-doula', 'owner_phone', 'Owner-doula phone')
def ADMIN_PH(): return PH('Admin', 'admin_phone', 'Admin phone')
def CO(): return CA('company', 'Company', 'text', '{set:company}', 24)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
YES = '{list:yesno.yes}'
ADD, BIR, POS, COM = tok('pkind', 'Add-on'), tok('pkind', 'Birth'), tok('pkind', 'Postpartum'), tok('pkind', 'Combined')
def PKL(c): return LKN('packages.' + c, 'packages.package', 'package')
def INM(rng_, col='month', n=1): return '{range:%s},">="&{col:%s},{range:%s},"<"&EDATE({col:%s},%d)' % (rng_, col, rng_, col, n)
D365 = '">="&({today}-365)'; D90 = '">="&({today}-90)'

# parts of the three combined packages (the birth package and the postpartum pack they are made from)
PBT = 'IF({col:bundle}=%s,%s,IF({col:bundle}=%s,%s,%s))' % (tok('bundle', 'Combined Essential'), tok('package', 'Birth Essential'), tok('bundle', 'Combined Plus'), tok('package', 'Birth Plus'), tok('package', 'Birth Premier'))
PPT = 'IF({col:bundle}=%s,%s,IF({col:bundle}=%s,%s,%s))' % (tok('bundle', 'Combined Essential'), tok('package', 'Postpartum 40 Hours'), tok('bundle', 'Combined Plus'), tok('package', 'Postpartum 80 Hours'), tok('package', 'Postpartum 120 Hours'))
def PKX(col, t): return 'INDEX({range:packages.%s},MATCH(%s,{range:packages.package},0))' % (col, t)
def PFX(col, t): return 'INDEX({range:pk_profit.%s},MATCH(%s,{range:pk_profit.package},0))' % (col, t)

settings = [
    S('company', 'Your business name', 'text', COMPANY), S('target_income_hour', 'Target income per hour, all hours of a package', 'money', TARGET_INCOME_HOUR),
    S('prenatal_visit_hours', 'Hours of one prenatal visit', 'num', 2), S('pp_visit_hours', 'Hours of one postpartum visit', 'num', 3),
    S('oncall_before_days', 'On-call window starts, days before the estimated due date', 'int', ONCALL_BEFORE), S('oncall_after_days', 'On-call window ends, days after the estimated due date', 'int', ONCALL_AFTER),
    S('min_booking_hours', 'Minimum postpartum booking, hours', 'int', MIN_BOOKING_HOURS), S('plan_tolerance', 'Hours over plan that still count as on plan', 'pct', 0.10),
    S('mileage_share_max', 'Highest mileage cost as a share of the price', 'pct', 0.07), S('price_list_date', 'Date of your current price list', 'date', ago(140)),
    S('price_change_date', 'Date the next price list starts', 'date', ahead(60)), S('price_rise_pct', 'Planned rise of list prices on that date', 'pct', 0.05),
    S('community_pct', 'Community rate, a lower price for a client in need', 'pct', DISCOUNT_PCT['Community rate']),
    S('returning_pct', 'Returning client discount', 'pct', DISCOUNT_PCT['Returning client']), S('pack_expiry_days', 'Days an hour pack runs after the estimated due date', 'int', PACK_EXPIRY_DAYS),
    S('balance_weeks', 'Balance is due this many weeks before the estimated due date', 'int', BALANCE_WEEKS), S('quote_valid_days', 'Days a quote stays valid', 'int', 14),
    S('owner_draw', 'Owner pay you want each month', 'money', OWNER_DRAW),
]
assert 3 <= len(settings) <= 20

tables = []
# ---------------------------------------------------------------- 1 packages
tables.append(T('packages', 'Packages', 'Packages with planned hours by phase',
    'One row per package or add-on: list price, the part earned at the birth and as postpartum hours, visits and planned hours; the plan hours, the price per planned hour and the deposit fill in by themselves.', [
    C('package_id', 'Package ID', 'text', 10, required=True), LST('package', 'Package', 'package', 22), LST('kind', 'Kind', 'pkind', 12), C('price', 'List price', 'money', 11),
    C('birth_value', 'Birth part of the price', 'money', 11), C('pp_value', 'Postpartum part of the price', 'money', 11), C('prenatal_visits', 'Prenatal visits', 'int', 9),
    C('postpartum_visits', 'Postpartum visits', 'int', 9), C('birth_hours', 'Birth hours planned', 'num', 9), C('oncall_hours', 'On-call contact hours planned', 'num', 10),
    C('postpartum_hours', 'Postpartum hours in the pack', 'num', 10), C('deposit_pct', 'Deposit share', 'pct', 9),
    CA('plan_hours', 'Plan hours, all phases', 'num', '{col:prenatal_visits}*{set:prenatal_visit_hours}+{col:postpartum_visits}*{set:pp_visit_hours}+{col:birth_hours}+{col:oncall_hours}+{col:postpartum_hours}', 11),
    CA('price_hour', 'List price per plan hour', 'money', 'IF({col:plan_hours}>0,{col:price}/{col:plan_hours},0)', 11),
    CA('deposit', 'Deposit', 'money', 'ROUND({col:price}*{col:deposit_pct},0)', 11), OWNER_PH(), CO()],
    D.packages_d(), 30, [A('plan_hours', '> 150', 'warn')]))
# ---------------------------------------------------------------- 2 contracts
tables.append(T('contracts', 'Contracts', 'Contracts with list price, discount and price',
    'One row per contract: client, package, list price, discount and the price after it, signing date and status; the discount given, its share and the client phone fill in by themselves.', [
    C('contract_id', 'Contract ID', 'text', 10, required=True), C('client_id', 'Client ID', 'text', 10), C('client', 'Client', 'text', 24), LST('package', 'Package', 'cpackage', 22), LST('kind', 'Kind', 'ckind', 12),
    C('list_price', 'List price', 'money', 11), LST('discount', 'Discount', 'discount', 16), C('price', 'Price', 'money', 11), C('signed_on', 'Signed on', 'date', 11), LST('status', 'Status', 'ctstatus', 11),
    CA('discount_given', 'Discount given', 'money', '{col:list_price}-{col:price}', 11), CA('discount_pct', 'Discount share', 'pct', 'IF({col:list_price}>0,({col:list_price}-{col:price})/{col:list_price},0)', 9),
    CA('phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client_id', 'client_id'), 18), CO()],
    D.contracts_d(), 400, [A('status', '= ' + tok('ctstatus', 'Cancelled'), 'warn'), A('discount_given', '> 0', 'good')]))
# ---------------------------------------------------------------- 3 hours by client
tables.append(T('hours', 'Actual hours by client', 'Hours really spent on each finished client',
    'One row per finished client: prenatal, on-call contact, birth and postpartum hours and the mileage cost, taken from your logs; the total hours, the income per hour and the hours over plan fill in by themselves.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('client', 'Client', 'text', 24), LST('package', 'Package', 'cpackage', 22), LST('doula', 'Doula', 'doula', 16), LST('area', 'Area', 'area', 11),
    C('month', 'Due month', 'date', 11), C('prenatal_hours', 'Prenatal hours', 'num', 9), C('oncall_hours', 'On-call contact hours', 'num', 10), C('birth_hours', 'Birth hours', 'num', 9),
    C('postpartum_hours', 'Postpartum hours', 'num', 10), C('mileage_cost', 'Mileage cost', 'money', 11),
    CA('total_hours', 'Total hours', 'num', '{col:prenatal_hours}+{col:oncall_hours}+{col:birth_hours}+{col:postpartum_hours}', 9),
    CA('price', 'Price', 'money', LKN('contracts.price', 'contracts.client_id', 'client_id'), 11),
    CA('income_hour', 'Income per hour', 'money', 'IF({col:total_hours}>0,({col:price}-{col:mileage_cost})/{col:total_hours},0)', 11),
    CA('plan_hours', 'Plan hours', 'num', LKN('packages.plan_hours', 'packages.package', 'package'), 9), CA('over_hours', 'Hours over plan', 'num', 'MAX(0,{col:total_hours}-{col:plan_hours})', 9),
    CA('over_plan', 'Over plan', 'int', 'IF({col:total_hours}>{col:plan_hours}*(1+{set:plan_tolerance}),1,0)', 7),
    CA('mileage_share', 'Mileage share of price', 'pct', 'IF({col:price}>0,{col:mileage_cost}/{col:price},0)', 9),
    CA('doula_phone', 'Doula phone', 'text', 'IFERROR(INDEX({range:team.phone},MATCH({col:doula},{range:team.name},0))&"","")', 18), OWNER_PH(), CO()],
    D.hours_d(), 400, [A('income_hour', '< {set:target_income_hour}', 'warn'), A('over_plan', '= 1', 'bad')]))
# ---------------------------------------------------------------- 4 add-ons sold
tables.append(T('addons', 'Add-ons sold', 'Add-ons sold with price and hours',
    'One row per add-on sold (extra prenatal visit, class seat, photography referral, support referral note, debrief visit): date, client, price, hours and doula; the price per hour and the contact phones fill in by themselves.', [
    C('addon_id', 'Add-on ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), C('client_id', 'Client ID', 'text', 10), C('client', 'Client', 'text', 24),
    LST('addon', 'Add-on', 'addon', 22), C('price', 'Price', 'money', 11), C('hours', 'Hours', 'num', 9), LST('doula', 'Doula', 'doula', 16),
    CA('price_hour', 'Price per hour', 'money', 'IF({col:hours}>0,{col:price}/{col:hours},0)', 10), CA('phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client_id', 'client_id'), 18),
    ADMIN_PH(), PH('Photographer', 'photographer_phone', 'Photographer phone'), CO()],
    D.addons_d(), 120, [A('price_hour', '> 0', 'good')]))
# ---------------------------------------------------------------- 5 pay rates
tables.append(T('pp_rates', 'Pay rates', 'Postpartum rates by shift',
    'One row per shift: what a client pays per postpartum hour and the minimum booking in hours; the pack checks read these rates.', [
    LST('shift', 'Shift', 'shift', 24, required=True), C('rate_hour', 'Rate per hour', 'money', 11), C('min_hours', 'Minimum hours', 'int', 9)],
    D.rates_d(), 20))
# ---------------------------------------------------------------- 6 areas
tables.append(T('areas', 'Areas', 'Service areas with mileage rate and distance',
    'One row per area or trip type: mileage rate per mile and miles one way; the travel checks read the first two rows (Northgate and Southbank).', [
    C('area', 'Area or trip', 'text', 24, required=True), C('mileage_rate', 'Mileage rate per mile', 'money', 11), C('miles_one_way', 'Miles one way', 'int', 9)],
    D.areas_d(), 20))
# ---------------------------------------------------------------- 7 package profit
ISADD = '{col:kind}=%s' % ADD
tables.append(T('pk_profit', 'Package profit', 'Income per hour of every package, ranked',
    'One row per package or add-on: the price, plan hours and planned income per hour against what the finished clients really cost in hours and mileage; the actual income per hour, the rank, the target check and the local range check fill in by themselves.', [
    LST('package', 'Package', 'package', 22, required=True), LST('kind', 'Kind', 'pkind', 12),
    CA('price', 'List price', 'money', PKL('price'), 11), CA('plan_hours', 'Plan hours', 'num', PKL('plan_hours'), 9),
    CA('planned_pph', 'Planned income per hour', 'money', 'IF({col:plan_hours}>0,{col:price}/{col:plan_hours},0)', 11),
    CA('sold', 'Finished clients or add-ons sold', 'int', 'IF(%s,COUNTIFS({range:addons.addon},{col:package}),COUNTIFS({range:hours.package},{col:package}))' % ISADD, 11),
    CA('actual_hours', 'Actual hours', 'num', 'IF(%s,SUMIFS({range:addons.hours},{range:addons.addon},{col:package}),SUMIFS({range:hours.total_hours},{range:hours.package},{col:package}))' % ISADD, 10),
    CA('actual_income', 'Income earned', 'money', 'IF(%s,SUMIFS({range:addons.price},{range:addons.addon},{col:package}),SUMIFS({range:hours.price},{range:hours.package},{col:package}))' % ISADD, 12),
    CA('mileage', 'Mileage cost', 'money', 'IF(%s,0,SUMIFS({range:hours.mileage_cost},{range:hours.package},{col:package}))' % ISADD, 11),
    CA('actual_pph', 'Actual income per hour', 'money', 'IF({col:actual_hours}>0,({col:actual_income}-{col:mileage})/{col:actual_hours},0)', 11),
    CA('sort_key', 'Sort key', 'num', 'IF(%s,9999,{col:actual_pph})+MATCH({col:package},{range:pk_profit.package},0)/10000000' % ISADD, 9),
    CA('rank', 'Rank, lowest first', 'int', 'COUNTIFS({range:pk_profit.sort_key},"<"&{col:sort_key})+1', 9),
    CA('gap', 'Gap to the target per hour', 'money', '{col:actual_pph}-{set:target_income_hour}', 11),
    CA('flag', 'Target check', 'text', 'IF(%s,%s,IF({col:actual_pph}>={set:target_income_hour},%s,%s))' % (ISADD, ck('Add-on'), ck('Above the target'), ck('Below the target')), 16),
    CA('range_row', 'Local range used', 'text', 'IF({col:kind}=%s,%s,IF({col:package}=%s,%s,IF({col:kind}=%s,%s,IF({col:kind}=%s,%s,%s))))' % (
        BIR, tok('lrange', 'Birth package'), tok('package', 'Night Support 60 Hours'), tok('lrange', 'Night hour'), POS, tok('lrange', 'Postpartum hour'), COM, tok('lrange', 'Combined package'), tok('lrange', 'Add-on')), 16),
    CA('range_value', 'Price compared, package or hour', 'money', 'IF({col:kind}=%s,IF({col:plan_hours}>0,{col:price}/{col:plan_hours},0),{col:price})' % POS, 11),
    CA('range_low', 'Local low', 'money', LKN('local_range.local_low', 'local_range.label', 'range_row'), 10), CA('range_high', 'Local high', 'money', LKN('local_range.local_high', 'local_range.label', 'range_row'), 10),
    CA('range_check', 'Local range check', 'text', 'IF({col:range_value}<{col:range_low},%s,IF({col:range_value}>{col:range_high},%s,%s))' % (ck('Below the range'), ck('Above the range'), ck('Inside the range')), 16),
    CA('in_range', 'Inside the range', 'int', 'IF({col:range_check}=%s,1,0)' % ck('Inside the range'), 7),
    CA('price_check', 'Price check', 'text', 'IF(%s,%s,IF({col:actual_pph}<{set:target_income_hour},IF({col:range_check}=%s,%s,%s),IF(AND({col:actual_pph}>={set:target_income_hour}*1.5,{col:range_check}=%s),%s,%s)))' % (
        ISADD, ck('Hold the price'), ck('Above the range'), ck('Hold the price'), ck('Raise the price'), ck('Above the range'), ck('Lower the price'), ck('Hold the price')), 16),
    CA('sold_90', 'Sold, last 90 days', 'int', 'IF(%s,COUNTIFS({range:addons.addon},{col:package},{range:addons.date},%s),COUNTIFS({range:contracts.package},{col:package},{range:contracts.signed_on},%s))' % (ISADD, D90, D90), 9),
    CA('pph_pkg', 'Income per hour, packages only', 'money', 'IF(%s,0,{col:actual_pph})' % ISADD, 10), CA('sold_pkg', 'Sold in 90 days, packages only', 'int', 'IF(%s,0,{col:sold_90})' % ISADD, 9),
    CA('income_pkg', 'Income earned, packages only', 'money', 'IF(%s,0,{col:actual_income})' % ISADD, 11),
    CA('lowest_name', 'Lowest-earning package', 'text', 'IFERROR(INDEX({range:pk_profit.package},MATCH(1,{range:pk_profit.rank},0)),"")', 22),
    CA('target', 'Target income per hour', 'money', '{set:target_income_hour}', 10), OWNER_PH(), CO()],
    D.profit_d(), 30, [A('flag', '= ' + ck('Below the target'), 'bad'), A('flag', '= ' + ck('Above the target'), 'good'), A('range_check', '= ' + ck('Above the range'), 'warn')]))
# ---------------------------------------------------------------- 8 package mix by month
tables.append(T('mix', 'Package mix by month', 'Contracts and income by month and kind',
    'One row per month and kind (birth, postpartum, combined, add-on): the contracts signed or add-ons sold and the income booked, counted from Contracts and Add-ons sold.', [
    C('month', 'Month', 'date', 11, required=True), LST('kind', 'Kind', 'pkind', 12),
    CA('contracts', 'Contracts or add-ons', 'int', 'IF({col:kind}=%s,COUNTIFS(%s),COUNTIFS(%s,{range:contracts.kind},{col:kind}))' % (ADD, INM('addons.date'), INM('contracts.signed_on')), 10),
    CA('income', 'Income booked', 'money', 'IF({col:kind}=%s,SUMIFS({range:addons.price},%s),SUMIFS({range:contracts.price},%s,{range:contracts.kind},{col:kind}))' % (ADD, INM('addons.date'), INM('contracts.signed_on')), 12)],
    D.mix_d(), 120))
# ---------------------------------------------------------------- 9 bundle test
tables.append(T('bundles', 'Bundle test', 'Combined package against the sum of its parts',
    'One row per combined package and 3-month period of the last year: the contracts sold, the price against the list prices of the birth package and the postpartum pack it is made of, the discount given and the income per hour of the bundle against its parts.', [
    C('bundle_id', 'Bundle ID', 'text', 9, required=True), LST('bundle', 'Combined package', 'bundle', 22), C('from_month', 'From month', 'date', 11),
    CA('sold', 'Contracts sold in the 3 months', 'int', 'COUNTIFS({range:contracts.package},{col:bundle},{range:contracts.signed_on},">="&{col:from_month},{range:contracts.signed_on},"<"&EDATE({col:from_month},3))', 10),
    CA('price', 'Bundle price', 'money', LKN('packages.price', 'packages.package', 'bundle'), 11),
    CA('list_sum', 'Sum of the parts at list price', 'money', 'IFERROR(%s+%s,0)' % (PKX('price', PBT), PKX('price', PPT)), 12),
    CA('discount_given', 'Discount given', 'money', '{col:list_sum}-{col:price}', 11), CA('discount_share', 'Discount share', 'pct', 'IF({col:list_sum}>0,{col:discount_given}/{col:list_sum},0)', 9),
    CA('bundle_pph', 'Bundle income per hour', 'money', 'IFERROR(%s,0)' % PFX('actual_pph', '{col:bundle}'), 11),
    CA('parts_pph', 'Parts income per hour, hours weighted', 'money', 'IFERROR((%s*%s+%s*%s)/(%s+%s),0)' % (PFX('actual_pph', PBT), PKX('plan_hours', PBT), PFX('actual_pph', PPT), PKX('plan_hours', PPT), PKX('plan_hours', PBT), PKX('plan_hours', PPT)), 12),
    CA('bundle_flag', 'Bundle check', 'text', 'IF({col:bundle_pph}>={set:target_income_hour},%s,%s)' % (ck('Bundle pays'), ck('Bundle loses')), 14), OWNER_PH(), CO()],
    D.bundles_d(), 30, [A('bundle_flag', '= ' + ck('Bundle loses'), 'bad'), A('bundle_flag', '= ' + ck('Bundle pays'), 'good')]))
# ---------------------------------------------------------------- 10 add-on attach
tables.append(T('addon_attach', 'Add-on attach', 'How often each add-on is sold',
    'One row per add-on: how many were sold and the attach rate, the add-ons sold for each contract signed.', [
    LST('addon', 'Add-on', 'addon', 24, required=True), CA('sold', 'Sold', 'int', 'COUNTIFS({range:addons.addon},{col:addon})', 9),
    CA('attach_rate', 'Attach rate, per contract signed', 'pct', 'IFERROR(COUNTIFS({range:addons.addon},{col:addon})/COUNTIFS({range:contracts.client_id},"<>"),0)', 11)],
    D.attach_d(), 20))
# ---------------------------------------------------------------- 11 discount effect
tables.append(T('discounts', 'Discount effect', 'What each discount gave up, by 3-month period',
    'One row per discount and 3-month period of the last year: the contracts signed with it and the price given up against list; the average discount and the share of contracts fill in by themselves.', [
    C('discount_id', 'Discount ID', 'text', 9, required=True), LST('discount', 'Discount', 'discount', 16), C('from_month', 'From month', 'date', 11),
    CA('contracts', 'Contracts signed', 'int', 'COUNTIFS({range:contracts.discount},{col:discount},{range:contracts.signed_on},">="&{col:from_month},{range:contracts.signed_on},"<"&EDATE({col:from_month},3))', 10),
    CA('given_up', 'Price given up', 'money', 'SUMIFS({range:contracts.discount_given},{range:contracts.discount},{col:discount},{range:contracts.signed_on},">="&{col:from_month},{range:contracts.signed_on},"<"&EDATE({col:from_month},3))', 11),
    CA('avg_given', 'Average discount per contract', 'money', 'IF({col:contracts}>0,{col:given_up}/{col:contracts},0)', 11),
    CA('share', 'Share of contracts in the period', 'pct', 'IFERROR({col:contracts}/COUNTIFS({range:contracts.signed_on},">="&{col:from_month},{range:contracts.signed_on},"<"&EDATE({col:from_month},3)),0)', 10)],
    D.discounts_d(), 30))
# ---------------------------------------------------------------- 12 local price range
tables.append(T('local_range', 'Local price range', 'Your own local price range by kind',
    'One row per kind of package: the lowest and highest price you see locally, a package price for birth, combined and add-on, a price per hour for postpartum and night hours; set your own from what you know of your area.', [
    LST('label', 'Range', 'lrange', 24, required=True), C('local_low', 'Local low', 'money', 11), C('local_high', 'Local high', 'money', 11)],
    D.local_d(), 20))
# ---------------------------------------------------------------- 13 price scenarios
tables.append(T('price_scn', 'Price scenarios', 'Price change scenarios on your yearly income',
    'One row per scenario and price change: the share of sign-ups lost for each 1% price rise (type your own guess); the income change over the last 12 months and the income per hour after the change fill in by themselves.', [
    C('scn_id', 'Scenario ID', 'text', 9, required=True), LST('scenario', 'Scenario', 'scen', 11), C('price_change', 'Price change', 'pct', 9), C('volume_response', 'Sign-ups lost per 1% rise', 'num', 11),
    CA('income_12m', 'Income, last 12 months', 'money', 'SUMIFS({range:contracts.price},{range:contracts.signed_on},%s)' % D365, 12),
    CA('income_change', 'Income change', 'money', '{col:income_12m}*((1+{col:price_change})*(1-{col:volume_response}*{col:price_change})-1)', 12),
    CA('income_hour', 'Income per hour after the change', 'money', 'IFERROR((SUM({range:hours.price})*(1+{col:price_change})-SUM({range:hours.mileage_cost}))/SUM({range:hours.total_hours}),0)', 11),
    CA('scn_flag', 'Scenario check', 'text', 'IF(AND({col:income_change}>0,{col:income_hour}>={set:target_income_hour}),%s,%s)' % (ck('Raise the price'), ck('Hold the price')), 14)],
    D.scn_d(), 30, [A('income_change', '< 0', 'warn')]))
# ---------------------------------------------------------------- 14 hours plan vs actual
tables.append(T('hours_plan', 'Hours plan vs actual', 'Plan hours against the hours really spent',
    'One row per package or add-on: the plan hours of one client against the average hours your finished clients really took; the gap and the plan check fill in by themselves.', [
    LST('package', 'Package', 'package', 22, required=True), CA('kind', 'Kind', 'text', LKT('packages.kind', 'packages.package', 'package'), 12), CA('plan_hours', 'Plan hours', 'num', PKL('plan_hours'), 9),
    CA('actual_hours', 'Actual hours per client', 'num', 'IF({col:kind}=%s,IFERROR(AVERAGEIFS({range:addons.hours},{range:addons.addon},{col:package}),0),IFERROR(AVERAGEIFS({range:hours.total_hours},{range:hours.package},{col:package}),0))' % ADD, 10),
    CA('gap_share', 'Gap to plan', 'pct', 'IF({col:plan_hours}>0,{col:actual_hours}/{col:plan_hours}-1,0)', 9),
    CA('plan_flag', 'Plan check', 'text', 'IF(ABS({col:gap_share})<={set:plan_tolerance},%s,IF({col:gap_share}>0,%s,%s))' % (ck('On plan'), ck('Over plan'), ck('Under plan')), 12), OWNER_PH(), CO()],
    D.hplan_d(), 30, [A('plan_flag', '= ' + ck('Over plan'), 'warn')]))
# ---------------------------------------------------------------- 15 mileage by package
tables.append(T('mileage_pkg', 'Mileage by package', 'Mileage cost per client and its share of the price',
    'One row per package: the average mileage cost of a finished client and its share of the list price, against the highest share you accept.', [
    LST('package', 'Package', 'package', 22, required=True), CA('kind', 'Kind', 'text', LKT('packages.kind', 'packages.package', 'package'), 12), CA('price', 'List price', 'money', PKL('price'), 11),
    CA('mileage_cost', 'Mileage cost per client', 'money', 'IF({col:kind}=%s,0,IFERROR(AVERAGEIFS({range:hours.mileage_cost},{range:hours.package},{col:package}),0))' % ADD, 11),
    CA('share', 'Share of the price', 'pct', 'IF({col:price}>0,{col:mileage_cost}/{col:price},0)', 9),
    CA('travel_flag', 'Travel fee check', 'text', 'IF({col:share}>{set:mileage_share_max},%s,%s)' % (ck('Add a travel fee'), ck('Hold the fee')), 14)],
    D.mileage_d(), 30, [A('travel_flag', '= ' + ck('Add a travel fee'), 'warn')]))
# ---------------------------------------------------------------- 16 postpartum price per hour
tables.append(T('pp_price', 'Postpartum price per hour', 'Pack price per hour against the shift rates',
    'One row per postpartum pack and shift: the price per hour inside the pack against the rate for that shift; the gap, the share saved and the contracts sold fill in by themselves.', [
    C('pp_id', 'Row ID', 'text', 9, required=True), LST('package', 'Postpartum pack', 'ppack', 24), LST('shift', 'Shift', 'shift', 22),
    CA('price', 'Pack price', 'money', PKL('price'), 11), CA('hours', 'Pack hours', 'num', PKL('postpartum_hours'), 9),
    CA('pack_pph', 'Pack price per hour', 'money', 'IF({col:hours}>0,{col:price}/{col:hours},0)', 11),
    CA('shift_rate', 'Rate per hour for the shift', 'money', LKN('pp_rates.rate_hour', 'pp_rates.shift', 'shift'), 11), CA('min_hours', 'Minimum hours', 'int', LKN('pp_rates.min_hours', 'pp_rates.shift', 'shift'), 9),
    CA('gap', 'Hourly rate less pack price', 'money', '{col:shift_rate}-{col:pack_pph}', 11), CA('gap_share', 'Share saved by the pack', 'pct', 'IF({col:shift_rate}>0,{col:gap}/{col:shift_rate},0)', 9),
    CA('contracts', 'Contracts sold', 'int', 'COUNTIFS({range:contracts.package},{col:package})', 9),
    CA('pp_flag', 'Pack check', 'text', 'IF({col:gap_share}>0.1,%s,%s)' % (ck('Pack is cheaper than hourly'), ck('Pack price is fine')), 16)],
    D.pp_d(), 30, [A('pp_flag', '= ' + ck('Pack is cheaper than hourly'), 'warn')]))
# ---------------------------------------------------------------- 17 package sales by month
tables.append(T('sales_month', 'Package sales by month', 'Contracts, average price and income by month',
    'One row per month: contracts signed, the average price, the income booked, the discount given and the combined packages sold, counted from Contracts.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('contracts', 'Contracts signed', 'int', 'COUNTIFS(%s)' % INM('contracts.signed_on'), 10), CA('income', 'Income booked', 'money', 'SUMIFS({range:contracts.price},%s)' % INM('contracts.signed_on'), 12),
    CA('avg_price', 'Average price', 'money', 'IF({col:contracts}>0,{col:income}/{col:contracts},0)', 11),
    CA('discount_given', 'Discount given', 'money', 'SUMIFS({range:contracts.discount_given},%s)' % INM('contracts.signed_on'), 11),
    CA('combined', 'Combined packages sold', 'int', 'COUNTIFS(%s,{range:contracts.kind},%s)' % (INM('contracts.signed_on'), COM), 10), OWNER_PH(), CO()],
    D.sales_d(), 40))
# ---------------------------------------------------------------- 18 price list with discounts
tables.append(T('price_list', 'Price list with discounts', 'Price list with community and returning-client prices',
    'One row per package or add-on: the list price, the price after the community rate and the returning-client discount (set on Start) and the price planned for the next price list.', [
    LST('package', 'Package', 'package', 22, required=True), CA('list_price', 'List price', 'money', PKL('price'), 11),
    CA('community_price', 'Community rate price', 'money', 'ROUND({col:list_price}*(1-{set:community_pct}),0)', 11), CA('returning_price', 'Returning-client price', 'money', 'ROUND({col:list_price}*(1-{set:returning_pct}),0)', 11),
    CA('next_price', 'Price on the next list', 'money', 'ROUND({col:list_price}*(1+{set:price_rise_pct}),0)', 11), CA('price_change_date', 'Next list starts', 'date', '{set:price_change_date}', 11),
    OWNER_PH(), ADMIN_PH(), PH('Accountant', 'accountant_phone', 'Accountant phone'), CO()],
    D.plist_d(), 30))
# ---------------------------------------------------------------- 19 team
tables.append(T('team', 'Team', 'Team with roles and phones',
    'One row per person: the owner-doula, contracted doulas, backup doulas, the admin and outside contacts; the message links read these phones.', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 20), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26)],
    D.team_d(), 30))
# ---------------------------------------------------------------- 20 clients
tables.append(T('clients', 'Clients', 'Clients with package, doula and hours left',
    'One row per client (first name and family name, area, package, doula and dates only, no medical detail): add a prospect with the status Enquiry to send the package messages; the plan hours, hours left in an hour pack and the price lookups fill in by themselves.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('client', 'Client', 'text', 24), C('phone', 'Phone', 'text', 18), LST('area', 'Area', 'area', 11), LST('kind', 'Kind', 'ckind', 12),
    LST('package', 'Package', 'cpackage', 22), LST('doula', 'Doula', 'doula', 16), C('signed_on', 'Signed on', 'date', 11), LST('status', 'Status', 'cstatus', 15), C('pp_hours_used', 'Postpartum hours used', 'num', 10),
    CA('plan_hours', 'Plan hours', 'num', LKN('packages.plan_hours', 'packages.package', 'package'), 9), CA('package_price', 'Package list price', 'money', LKN('packages.price', 'packages.package', 'package'), 11),
    CA('hours_left', 'Hours left in the pack', 'num', 'MAX(0,%s-{col:pp_hours_used})' % LKN('packages.postpartum_hours', 'packages.package', 'package'), 10),
    CA('mileage_rate', 'Mileage rate per mile', 'money', LKN('areas.mileage_rate', 'areas.area', 'area'), 10),
    CA('extra_visit_price', 'Extra prenatal visit price', 'money', 'SUMIFS({range:packages.price},{range:packages.package},%s)' % tok('package', 'Extra prenatal visit'), 10),
    CA('debrief_price', 'Debrief visit price', 'money', 'SUMIFS({range:packages.price},{range:packages.package},%s)' % tok('package', 'Debrief visit'), 10),
    CA('class_price', 'Class seat price', 'money', 'SUMIFS({range:packages.price},{range:packages.package},%s)' % tok('package', 'Class seat (series)'), 10),
    CA('combo_saving', 'Saving of the Complete Care Bundle', 'money', 'SUMIFS({range:packages.price},{range:packages.package},%s)+SUMIFS({range:packages.price},{range:packages.package},%s)-SUMIFS({range:packages.price},{range:packages.package},%s)' % (
        tok('package', 'Birth Premier'), tok('package', 'Postpartum 120 Hours'), tok('package', 'Complete Care Bundle')), 11),
    CA('rate_day', 'Day shift rate', 'money', 'SUMIFS({range:pp_rates.rate_hour},{range:pp_rates.shift},%s)' % tok('shift', 'Day shift'), 9),
    CA('rate_evening', 'Evening shift rate', 'money', 'SUMIFS({range:pp_rates.rate_hour},{range:pp_rates.shift},%s)' % tok('shift', 'Evening shift'), 9),
    CA('rate_night', 'Night shift rate', 'money', 'SUMIFS({range:pp_rates.rate_hour},{range:pp_rates.shift},%s)' % tok('shift', 'Night shift'), 9),
    CA('rate_weekend', 'Weekend and holiday rate', 'money', 'SUMIFS({range:pp_rates.rate_hour},{range:pp_rates.shift},%s)' % tok('shift', 'Weekend and holiday'), 9),
    CA('night_pack_price', 'Night support pack price', 'money', 'SUMIFS({range:packages.price},{range:packages.package},%s)' % tok('package', 'Night Support 60 Hours'), 11),
    CA('night_pack_hours', 'Night support pack hours', 'num', 'SUMIFS({range:packages.postpartum_hours},{range:packages.package},%s)' % tok('package', 'Night Support 60 Hours'), 9),
    CA('min_hours', 'Minimum booking hours', 'int', '{set:min_booking_hours}', 9), CA('price_change_date', 'Next price list starts', 'date', '{set:price_change_date}', 11),
    OWNER_PH(), ADMIN_PH(), CA('doula_phone', 'Doula phone', 'text', 'IFERROR(INDEX({range:team.phone},MATCH({col:doula},{range:team.name},0))&"","")', 18), CO()],
    D.clients_d(), 400, [A('status', '= ' + tok('cstatus', 'On call'), 'good'), A('status', '= ' + tok('cstatus', 'Cancelled'), 'warn')]))
assert len(tables) == 20, len(tables)
