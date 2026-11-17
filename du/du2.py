"""Doula Business suite - part 2: Packages, Pricing and Profit per Hour."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du2_lists import *
from du2_tables import settings, tables
from du2_tools import tools

NOTE = "Sample wording: adapt it to your own business and check your local rules."
YES = '{list:yesno.yes}'
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
TGT = '{set:target_income_hour}'
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
D365 = '">="&({today}-365)'; D90 = '">="&({today}-90)'; D30 = '">="&({today}-30)'
ADD, BIR, POS, COM = tok('pkind', 'Add-on'), tok('pkind', 'Birth'), tok('pkind', 'Postpartum'), tok('pkind', 'Combined')

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('pkg_def_sheet', 'Package Definition Sheet', 'Package with visits, hours and deposit', 'packages.package_id', F(
        ('Package', 'packages.package'), ('Kind', 'packages.kind'), ('List price', 'packages.price'), ('Birth part of the price', 'packages.birth_value'), ('Postpartum part of the price', 'packages.pp_value'),
        ('Prenatal visits', 'packages.prenatal_visits'), ('Postpartum visits', 'packages.postpartum_visits'), ('Birth hours planned', 'packages.birth_hours'), ('On-call contact hours planned', 'packages.oncall_hours'),
        ('Postpartum hours in the pack', 'packages.postpartum_hours'), ('Plan hours, all phases', 'packages.plan_hours'), ('List price per plan hour', 'packages.price_hour'), ('Deposit share', 'packages.deposit_pct'),
        ('Deposit', 'packages.deposit')) + [
        FF('Share of the price earned at the birth', 'IFERROR(%s/%s,0)' % (LK('packages', 'package_id', 'birth_value'), LK('packages', 'package_id', 'price')), 'pct'),
        FF('Price for your target at plan hours', '%s*%s' % (TGT, LK('packages', 'package_id', 'plan_hours')), 'money')]),
    FORM('price_review_sheet', 'Package Price Review Sheet', 'Package price review with income per hour', 'pk_profit.package', F(
        ('List price', 'pk_profit.price'), ('Plan hours', 'pk_profit.plan_hours'), ('Planned income per hour', 'pk_profit.planned_pph'), ('Finished clients or add-ons sold', 'pk_profit.sold'), ('Actual hours', 'pk_profit.actual_hours'),
        ('Income earned', 'pk_profit.actual_income'), ('Mileage cost', 'pk_profit.mileage'), ('Actual income per hour', 'pk_profit.actual_pph'), ('Rank, lowest first', 'pk_profit.rank'), ('Gap to the target per hour', 'pk_profit.gap'),
        ('Target check', 'pk_profit.flag'), ('Local range check', 'pk_profit.range_check'), ('Price check', 'pk_profit.price_check')) + [
        FF('Price for the target at actual hours', 'IFERROR((%s*%s+%s)/%s,0)' % (TGT, LK('pk_profit', 'package', 'actual_hours'), LK('pk_profit', 'package', 'mileage'), LK('pk_profit', 'package', 'sold')), 'money'),
        FF('Packages below the target', 'COUNTIFS({range:pk_profit.flag},%s)' % ck('Below the target'), 'int')]),
    FORM('addon_sheet', 'Add-on Sheet', 'Add-on sold with price and hours', 'addons.addon_id', F(
        ('Date', 'addons.date'), ('Client', 'addons.client'), ('Add-on', 'addons.addon'), ('Price', 'addons.price'), ('Hours', 'addons.hours'), ('Price per hour', 'addons.price_hour'), ('Doula', 'addons.doula'),
        ('Client phone', 'addons.phone')) + [
        FF('Sold of this add-on, all history', 'COUNTIFS({range:addons.addon},%s)' % LK('addons', 'addon_id', 'addon'), 'int'),
        FF('Income of this add-on', 'SUMIFS({range:addons.price},{range:addons.addon},%s)' % LK('addons', 'addon_id', 'addon'), 'money')]),
    FORM('bundle_sheet', 'Bundle Proposal Sheet', 'Combined package against its parts', 'bundles.bundle_id', F(
        ('Combined package', 'bundles.bundle'), ('From month', 'bundles.from_month'), ('Contracts sold in the 3 months', 'bundles.sold'), ('Bundle price', 'bundles.price'), ('Sum of the parts at list price', 'bundles.list_sum'),
        ('Discount given', 'bundles.discount_given'), ('Discount share', 'bundles.discount_share'), ('Bundle income per hour', 'bundles.bundle_pph'), ('Parts income per hour', 'bundles.parts_pph'),
        ('Bundle check', 'bundles.bundle_flag')) + [
        FF('Gap to your target per hour', '%s-%s' % (LK('bundles', 'bundle_id', 'bundle_pph'), TGT), 'money'),
        FF('Price at the parts income per hour', 'IFERROR(%s*%s/%s,0)' % (LK('bundles', 'bundle_id', 'price'), LK('bundles', 'bundle_id', 'parts_pph'), LK('bundles', 'bundle_id', 'bundle_pph')), 'money')]),
    FORM('rate_sheet', 'Hourly Rate Sheet', 'Postpartum rate for one shift', 'pp_rates.shift', F(
        ('Rate per hour', 'pp_rates.rate_hour'), ('Minimum hours', 'pp_rates.min_hours')) + [
        FF('Minimum booking charge', '%s*%s' % (LK('pp_rates', 'shift', 'rate_hour'), LK('pp_rates', 'shift', 'min_hours')), 'money'),
        FF('Cheapest pack price per hour', 'MIN({range:pp_price.pack_pph})', 'money'), FF('Rate less the cheapest pack hour', '%s-MIN({range:pp_price.pack_pph})' % LK('pp_rates', 'shift', 'rate_hour'), 'money'),
        FF('Largest share a pack saves', 'MAX({range:pp_price.gap_share})', 'pct'), FF('Minimum booking on your Start sheet', '{set:min_booking_hours}', 'int')]),
    FORM('pack_sheet', 'Hour Pack Sheet', 'Hour pack against one shift rate', 'pp_price.pp_id', F(
        ('Postpartum pack', 'pp_price.package'), ('Shift', 'pp_price.shift'), ('Pack price', 'pp_price.price'), ('Pack hours', 'pp_price.hours'), ('Pack price per hour', 'pp_price.pack_pph'),
        ('Rate per hour for the shift', 'pp_price.shift_rate'), ('Minimum hours', 'pp_price.min_hours'), ('Hourly rate less pack price', 'pp_price.gap'), ('Share saved by the pack', 'pp_price.gap_share'),
        ('Contracts sold', 'pp_price.contracts'), ('Pack check', 'pp_price.pp_flag')) + [
        FF('Days the pack runs after the due date', '{set:pack_expiry_days}', 'int'), FF('Minimum booking, hours', '{set:min_booking_hours}', 'int')]),
    FORM('discount_sheet', 'Discount Policy Sheet', 'Discount given in one 3-month period', 'discounts.discount_id', F(
        ('Discount', 'discounts.discount'), ('From month', 'discounts.from_month'), ('Contracts signed', 'discounts.contracts'), ('Price given up', 'discounts.given_up'),
        ('Average discount per contract', 'discounts.avg_given'), ('Share of contracts in the period', 'discounts.share')) + [
        FF('Community rate you set', '{set:community_pct}', 'pct'), FF('Returning-client discount you set', '{set:returning_pct}', 'pct'),
        FF('Price given up, all periods', 'SUMIFS({range:discounts.given_up},{range:discounts.discount},%s)' % LK('discounts', 'discount_id', 'discount'), 'money')]),
    FORM('travel_sheet', 'Travel Fee Sheet', 'Travel cost for one area', 'areas.area', F(
        ('Mileage rate per mile', 'areas.mileage_rate'), ('Miles one way', 'areas.miles_one_way')) + [
        FF('Miles, round trip', '2*%s' % LK('areas', 'area', 'miles_one_way'), 'int'), FF('Cost of one round trip', '2*%s*%s' % (LK('areas', 'area', 'miles_one_way'), LK('areas', 'area', 'mileage_rate')), 'money'),
        FF('Finished clients in this area', 'COUNTIFS({range:hours.area},{pick})', 'int'), FF('Mileage cost of those clients', 'SUMIFS({range:hours.mileage_cost},{range:hours.area},{pick})', 'money'),
        FF('Mileage share of the price paid', 'IFERROR(SUMIFS({range:hours.mileage_cost},{range:hours.area},{pick})/SUMIFS({range:hours.price},{range:hours.area},{pick}),0)', 'pct'),
        FF('Highest share you accept', '{set:mileage_share_max}', 'pct')]),
    FORM('plist_sheet', 'Price List Update Sheet', 'Price list line with the next price', 'price_list.package', F(
        ('List price', 'price_list.list_price'), ('Community rate price', 'price_list.community_price'), ('Returning-client price', 'price_list.returning_price'), ('Price on the next list', 'price_list.next_price'),
        ('Next list starts', 'price_list.price_change_date')) + [
        FF('Rise of the list price', '%s-%s' % (LK('price_list', 'package', 'next_price'), LK('price_list', 'package', 'list_price')), 'money'),
        FF('Age of the current list, days', '{today}-{set:price_list_date}', 'int'), FF('Planned rise on your Start sheet', '{set:price_rise_pct}', 'pct')]),
    FORM('hours_plan_sheet', 'Package Hours Plan Sheet', 'Plan hours against actual hours', 'hours_plan.package', F(
        ('Kind', 'hours_plan.kind'), ('Plan hours', 'hours_plan.plan_hours'), ('Actual hours per client', 'hours_plan.actual_hours'), ('Gap to plan', 'hours_plan.gap_share'), ('Plan check', 'hours_plan.plan_flag')) + [
        FF('Hours gap per client', '%s-%s' % (LK('hours_plan', 'package', 'actual_hours'), LK('hours_plan', 'package', 'plan_hours')), 'num'),
        FF('Hours of prenatal visits in the plan', 'IFERROR(INDEX({range:packages.prenatal_visits},MATCH({pick},{range:packages.package},0))*{set:prenatal_visit_hours},0)', 'num'),
        FF('Gap you accept', '{set:plan_tolerance}', 'pct')]),
    FORM('community_sheet', 'Community Rate Request Sheet', 'Community-rate contract with the price given up', 'contracts.contract_id', F(
        ('Client', 'contracts.client'), ('Package', 'contracts.package'), ('Kind', 'contracts.kind'), ('List price', 'contracts.list_price'), ('Discount', 'contracts.discount'), ('Price', 'contracts.price'),
        ('Signed on', 'contracts.signed_on'), ('Discount given', 'contracts.discount_given'), ('Discount share', 'contracts.discount_pct'), ('Status', 'contracts.status')) + [
        FF('Price at the community rate you set', 'ROUND(%s*(1-{set:community_pct}),0)' % LK('contracts', 'contract_id', 'list_price'), 'money'),
        FF('Price given up at the community rate', '%s-ROUND(%s*(1-{set:community_pct}),0)' % (LK('contracts', 'contract_id', 'list_price'), LK('contracts', 'contract_id', 'list_price')), 'money')]),
    FORM('yearly_sheet', 'Yearly Price Review Sheet', 'One month of sales and the year behind it', 'sales_month.month', F(
        ('Contracts signed', 'sales_month.contracts'), ('Income booked', 'sales_month.income'), ('Average price', 'sales_month.avg_price'), ('Discount given', 'sales_month.discount_given'),
        ('Combined packages sold', 'sales_month.combined')) + [
        FF('Income booked, last 12 months', 'SUMIFS({range:contracts.price},{range:contracts.signed_on},%s)' % D365, 'money'),
        FF('Average price, last 12 months', 'IFERROR(AVERAGEIFS({range:contracts.price},{range:contracts.signed_on},%s),0)' % D365, 'money'),
        FF('Packages below your target', 'COUNTIFS({range:pk_profit.flag},%s)' % ck('Below the target'), 'int'), FF('Age of your price list, days', '{today}-{set:price_list_date}', 'int')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('price_list_doc', 'Package Price List', 'Package and price list for clients', 'price_list.package', [
        'Price list of {set:company}, dated {today}. Package: {col:price_list.package}.',
        'List price: {col:price_list.list_price}. With the community rate (a lower price for a client who cannot pay the full price): {col:price_list.community_price}. For a returning client: {col:price_list.returning_price}. Prices are before any tax.',
        'The next price list starts on {col:price_list.price_change_date}. A contract you have signed keeps the price you signed.', 'Please ask us if you would like to go through the packages.'], ['Owner-doula', 'Client'], NOTE),
    DOC('pkg_desc_doc', 'Package Description', 'Package description: what is included', 'packages.package_id', [
        'Package description of {set:company}, dated {today}. Package: {col:packages.package}.',
        'Included: prenatal visits {col:packages.prenatal_visits}, postpartum visits {col:packages.postpartum_visits}, planned hours at the birth {col:packages.birth_hours}, planned contact hours inside the on-call window {col:packages.oncall_hours} and postpartum hours {col:packages.postpartum_hours}. In all, {col:packages.plan_hours} planned hours.',
        'The on-call window is the days around the estimated due date when your doula keeps themselves free: {set:oncall_before_days} days before it to {set:oncall_after_days} days after it. The estimated due date is a date you give us, used only to plan the window.',
        'Price: {col:packages.price}. Deposit: {col:packages.deposit}, a payment that reserves the date and is applied to the price. The package describes hours and dates and promises no outcome.'], ['Owner-doula', 'Client'], NOTE),
    DOC('pkg_compare_doc', 'Package Comparison', 'Comparison of one package with your list', 'packages.package_id', [
        'Package comparison of {set:company}, dated {today}. Package: {col:packages.package} ({col:packages.kind}).',
        'Price {col:packages.price} for {col:packages.plan_hours} planned hours, which is {col:packages.price_hour} for each planned hour. Visits: {col:packages.prenatal_visits} prenatal and {col:packages.postpartum_visits} postpartum.',
        'Our other packages differ in the number of visits, the planned birth and on-call hours and the postpartum hours in the pack. Please ask for the full price list to compare them side by side.', 'Choose the package that fits your plans and your budget.'], ['Owner-doula', 'Client'], NOTE),
    DOC('bundle_prop_doc', 'Combined Package Proposal', 'Combined package proposal', 'bundles.bundle_id', [
        'Proposal of {set:company}, dated {today}. Combined package: {col:bundles.bundle}.',
        'The package is priced at {col:bundles.price}. Bought one by one, its birth package and postpartum pack would cost {col:bundles.list_sum} at list price, so the combined price saves {col:bundles.discount_given}, which is {col:bundles.discount_share} of the parts.',
        'The package keeps one doula across the prenatal visits, the birth and the weeks after, with the hours set out in the package description. It promises no outcome and counts hours, dates and money only.', 'A deposit reserves your date and the balance is due {set:balance_weeks} weeks before the estimated due date.'], ['Owner-doula', 'Client'], NOTE),
    DOC('addon_menu_doc', 'Add-on Menu', 'Add-on menu with prices', 'price_list.package', [
        'Add-on menu of {set:company}, dated {today}. Add-on: {col:price_list.package}.',
        'Price: {col:price_list.list_price}. For a client on the community rate: {col:price_list.community_price}. Prices are before any tax.',
        'Add-ons are booked on top of your package and invoiced when they are delivered. Ask your doula for the next free time.', 'The price list changes on {col:price_list.price_change_date}.'], ['Owner-doula', 'Client'], NOTE),
    DOC('pack_terms_doc', 'Hour Pack Terms', 'Postpartum hour pack terms', 'packages.package_id', [
        'Hour pack terms of {set:company}, dated {today}. Pack: {col:packages.package}.',
        'The pack holds {col:packages.postpartum_hours} postpartum hours (the weeks after a birth) for {col:packages.price}, which is {col:packages.price_hour} an hour. Deposit share: {col:packages.deposit_pct}.',
        'Hours are used in visits of at least {set:min_booking_hours} hours. The pack runs {set:pack_expiry_days} days after the estimated due date. Hours not used by then are not refunded unless your contract says so.',
        'Hours beyond the pack are invoiced at the hourly rate for the shift. Check the contract terms.'], ['Owner-doula', 'Client'], NOTE),
    DOC('disc_policy_doc', 'Discount Policy', 'Discount and community-rate policy', 'discounts.discount_id', [
        'Discount policy of {set:company}, dated {today}. Discount: {col:discounts.discount}.',
        'We offer a community rate of {set:community_pct} off the list price to a client who cannot pay the full price, and {set:returning_pct} off for a returning client. A discount is agreed before signing and shown on the contract.',
        'In the 3 months from {col:discounts.from_month} we signed {col:discounts.contracts} contracts with this discount and gave up {col:discounts.given_up} against list prices.', 'We review the policy once a year.'], ['Owner-doula', 'Admin'], NOTE),
    DOC('travel_notice_doc', 'Travel Fee Notice', 'Travel fee notice', 'areas.area', [
        'Travel notice of {set:company}, dated {today}. Area: {col:areas.area}.',
        'Travel to a client in this area is charged at {col:areas.mileage_rate} a mile for about {col:areas.miles_one_way} miles each way. A travel fee may apply when mileage is more than {set:mileage_share_max} of the price of the package.',
        'The fee is shown on your quote before you sign.', 'Please ask us how the travel cost is worked out.'], ['Owner-doula', 'Client'], NOTE),
    DOC('price_notice_doc', 'Price Change Notice', 'Price change notice for next year', 'price_list.package', [
        'Price change notice of {set:company}, dated {today}. Package: {col:price_list.package}.',
        'Our prices change on {col:price_list.price_change_date}. The price of this package moves from {col:price_list.list_price} to {col:price_list.next_price}.',
        'A contract you have signed keeps the price you signed, and so does its deposit. The community rate and the returning-client discount apply to the new prices too.', 'Please call us if you have a question.'], ['Owner-doula', 'Client'], NOTE),
    DOC('profit_report_doc', 'Package Profit Report', 'Package profit report for the owner-doula', 'pk_profit.package', [
        'Package profit report of {set:company}, dated {today}. Package: {col:pk_profit.package}.',
        'List price {col:pk_profit.price} for {col:pk_profit.plan_hours} plan hours: {col:pk_profit.planned_pph} planned per hour. {col:pk_profit.sold} finished clients or add-ons sold, {col:pk_profit.actual_hours} hours in all, income {col:pk_profit.actual_income}, mileage {col:pk_profit.mileage}.',
        'Actual income per hour: {col:pk_profit.actual_pph}, against your target of {col:pk_profit.target}. Target check: {col:pk_profit.flag}. Rank, lowest first: {col:pk_profit.rank}. The lowest-earning package is {col:pk_profit.lowest_name}.',
        'Local range check: {col:pk_profit.range_check}. Price check: {col:pk_profit.price_check}. Write the decision below.'], ['Owner-doula'], NOTE),
    DOC('bundle_review_doc', 'Bundle Review Note', 'Bundle review note', 'bundles.bundle_id', [
        'Bundle review of {set:company}, dated {today}. Combined package: {col:bundles.bundle}, 3 months from {col:bundles.from_month}.',
        'Contracts sold: {col:bundles.sold}. Price {col:bundles.price} against {col:bundles.list_sum} for the parts: {col:bundles.discount_given} given, {col:bundles.discount_share} of the parts.',
        'Income per hour of the bundle: {col:bundles.bundle_pph}. Its parts, weighted by plan hours: {col:bundles.parts_pph}. Check: {col:bundles.bundle_flag}.', 'Decide whether to reprice the bundle, change its hours or stop selling it. Write the decision below.'], ['Owner-doula'], NOTE),
    DOC('rate_card_doc', 'Postpartum Rate Card', 'Rate card for postpartum shifts', 'pp_rates.shift', [
        'Rate card of {set:company}, dated {today}. Shift: {col:pp_rates.shift}.',
        'Rate: {col:pp_rates.rate_hour} an hour, with a minimum booking of {col:pp_rates.min_hours} hours. Prices are before any tax.',
        'Postpartum hours are the hours of support in the weeks after a birth. An hour pack lowers the price of an hour; ask us for the pack prices.', 'Hours are invoiced after the visit unless your contract says otherwise.'], ['Owner-doula', 'Client'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('new_package', 'New Package Steps', 'sales_month', 'sales_month.month', [('Write the visits and hours of the package', 1), ('Price it with the New Package Designer', 2), ('Check the price against your local range', 3), ('Add it to the Packages sheet', 4), ('Write the package description', 6), ('Tell your doulas what it includes', 8), ('Add it to the price list', 10), ('Review sales after 90 days', 90)]),
    CHK('price_review', 'Price Review Steps', 'sales_month', 'sales_month.month', [('Open Package profit and sort by the lowest income per hour', 1), ('Run Is my price right on each package below the target', 2), ('Check each price against your local range', 3), ('Decide: raise, hold or lower', 5), ('Write the decisions in the review notes', 6), ('Update the price list', 10), ('Tell clients with a notice', 14)]),
    CHK('addon_review', 'Add-on Review Steps', 'addons', 'addons.date', [('Count the add-ons sold in the last 90 days', 1), ('Check the income per hour of each add-on', 2), ('Check the attach rate for each add-on', 3), ('Keep, reprice or drop each add-on', 5), ('Update the add-on menu', 7), ('Tell the admin about price changes', 8)]),
    CHK('bundle_check', 'Bundle Check Steps', 'contracts', 'contracts.signed_on', [('Compare the bundle price with its parts', 1), ('Check the hours the bundle really took', 3), ('Work out the income per hour of the bundle', 5), ('Run the Combined-Package Test', 6), ('Decide: reprice, change hours or stop selling', 10), ('Write the decision in the review notes', 12)]),
    CHK('yearly_rise', 'Yearly Price Rise Steps', 'sales_month', 'sales_month.month', [('Set the planned rise on the Start sheet', 1), ('Run the Next-Year Price Plan for each package', 3), ('Check the new prices against your local range', 5), ('Write the new price list', 10), ('Send the price change notice to clients', 30), ('Tell your accountant the new prices', 32), ('Start the new list on the set date', 60)]),
    CHK('community_req', 'Community-Rate Request Steps', 'contracts', 'contracts.signed_on', [('Write down the request and the date', 0), ('Check your discount ceiling for the package', 1), ('Decide with your own rule, never on the client story alone', 2), ('Tell the client the decision', 3), ('Write the discount on the contract', 4), ('Record the price given up', 5)]),
    CHK('hours_plan_chk', 'Package Hours Plan Check', 'hours', 'hours.month', [('Open Hours plan vs actual', 1), ('Find packages more than the accepted gap over plan', 2), ('Check whether the plan hours or the price is wrong', 4), ('Change the plan hours on the Packages sheet', 6), ('Tell your doulas the new plan', 8), ('Check again after 3 months', 90)]),
    CHK('rate_card_upd', 'Rate Card Update Steps', 'sales_month', 'sales_month.month', [('Check the postpartum rate for each shift', 1), ('Compare each pack price per hour with the shift rates', 3), ('Change the rates on the Pay rates sheet', 5), ('Update the rate card document', 7), ('Tell clients with a postpartum pack', 14), ('Tell your admin', 15)]),
    CHK('price_notice_chk', 'Price Change Notice Steps', 'clients', 'clients.signed_on', [('Write the notice with the new prices', 0), ('Check the date the new list starts', 1), ('Send the notice to current clients', 2), ('Tell prospects the new prices', 3), ('Answer questions about signed contracts', 7), ('Update the website and the price list', 10)]),
    CHK('local_range_chk', 'Local Range Check Steps', 'mix', 'mix.month', [('Look at the prices of other doulas near you', 1), ('Write your own local low and high on the Local price range sheet', 3), ('Check which packages are above or below the range', 4), ('Decide whether each one is deliberate', 6), ('Run the Local Range Position tool', 7), ('Write the decisions in the review notes', 8)]),
    CHK('pkg_retire', 'Package Retirement Steps', 'sales_month', 'sales_month.month', [('Run the Volume and Income Grid', 1), ('Count the sales of the last 12 months', 2), ('Check clients still on the package', 4), ('Decide the last date to sell it', 6), ('Remove it from the price list and the website', 10), ('Tell your doulas', 12), ('Keep the old contracts at their price', 14)]),
    CHK('seasonal_chk', 'Seasonal Package Review', 'mix', 'mix.month', [('Open Package mix by month for the last 12 months', 1), ('Find the busy and the quiet months', 2), ('Check which packages sell in each season', 4), ('Plan a package or an offer for the quiet months', 8), ('Run the Package Sales Forecast', 10), ('Write the plan in the review notes', 12)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('c_start', 'Client: what your package includes', 'clients', 'clients.phone', 'Hello {client}, {package} was booked on {signed_on}: {plan_hours} planned hours for {package_price}. Please call with any question. {company}'),
    M('c_addon', 'Client: your add-on is booked', 'addons', 'addons.phone', 'Hello {client}, your add-on {addon} is booked for {price}. I will confirm the day with you. {company}'),
    M('c_hours_left', 'Client: hours left in your pack', 'clients', 'clients.phone', 'Hello {client}, you have {hours_left} hours left in your {package} pack. Tell me when you would like the next visit. {company}'),
    M('c_price_change', 'Client: our prices change', 'clients', 'clients.phone', 'Hello {client}, our prices change on {price_change_date}. Your contract keeps the price you signed. {company}'),
    M('c_comm_ok', 'Client: community rate approved', 'contracts', 'contracts.phone', 'Hello {client}, your community-rate request is approved. {package} moves from {list_price} to {price}. {company}'),
    M('c_comm_info', 'Client: community rate needs more', 'contracts', 'contracts.phone', 'Hello {client}, we need a little more information for your community-rate request on {package}. May I call you today? {company}'),
    M('c_travel', 'Client: a travel fee applies', 'clients', 'clients.phone', 'Hello {client}, a travel fee applies in {area}, because mileage costs {mileage_rate} a mile. I can explain how it is worked out. {company}'),
    M('c_extra', 'Client: an extra prenatal visit', 'clients', 'clients.phone', 'Hello {client}, would you like an extra prenatal visit for {extra_visit_price}? Reply and I will find a time. {company}'),
    M('c_debrief', 'Client: a debrief visit', 'clients', 'clients.phone', 'Hello {client}, a debrief visit after the birth costs {debrief_price}. Would you like me to book one? {company}'),
    M('c_class', 'Client: a class seat', 'clients', 'clients.phone', 'Hello {client}, a seat in our class series is {class_price}. Shall I keep a seat for you? {company}'),
    M('e_compare', 'Enquirer: compare our packages', 'clients', 'clients.phone', 'Hello {client}, {package} plans {plan_hours} hours at {package_price}. I can send the full list of packages. {company}'),
    M('e_combo', 'Enquirer: the combined package saves', 'clients', 'clients.phone', 'Hello {client}, the Complete Care Bundle saves you {combo_saving} against buying its parts. Shall I explain what is in it? {company}'),
    M('e_rates', 'Enquirer: postpartum rates by shift', 'clients', 'clients.phone', 'Hello {client}, postpartum rates an hour: day {rate_day}, evening {rate_evening}, night {rate_night}, weekend {rate_weekend}. {company}'),
    M('e_night', 'Enquirer: our night support pack', 'clients', 'clients.phone', 'Hello {client}, our night support pack is {night_pack_hours} hours for {night_pack_price}. Would you like the details? {company}'),
    M('o_earns', 'Owner: package income per hour', 'pk_profit', 'pk_profit.owner_phone', 'Hello, {package} earns {actual_pph} an hour against your target of {target}. {company}'),
    M('o_below', 'Owner: package below your target', 'pk_profit', 'pk_profit.owner_phone', 'Hello, check {package}: {actual_pph} an hour against your target of {target}. Price check: {price_check}. {company}'),
    M('o_bundle', 'Owner: bundle against its parts', 'bundles', 'bundles.owner_phone', 'Hello, {bundle} earns {bundle_pph} an hour against {parts_pph} for its parts, with {discount_given} given off. Check: {bundle_flag}. {company}'),
    M('o_disc', 'Owner: discount given in a month', 'sales_month', 'sales_month.owner_phone', 'Hello, the discount given in {month} was {discount_given} on {contracts} contracts. {company}'),
    M('o_price', 'Owner: your price check says', 'pk_profit', 'pk_profit.owner_phone', 'Hello, your price check says {price_check} for {package}: {actual_pph} an hour, range check {range_check}. {company}'),
    M('o_addon', 'Owner: sales in the last 90 days', 'pk_profit', 'pk_profit.owner_phone', 'Hello, {package} sold {sold_90} times in the last 90 days. {company}'),
    M('o_lowest', 'Owner: the lowest-earning package', 'pk_profit', 'pk_profit.owner_phone', 'Hello, your lowest-earning package is {lowest_name}. {package} ranks {rank} from the lowest on income per hour. {company}'),
    M('o_list', 'Owner: next price list for review', 'price_list', 'price_list.owner_phone', 'Hello, your price list for {price_change_date} is ready for review: {package} moves from {list_price} to {next_price}. {company}'),
    M('o_mileage', 'Owner: mileage share of the price', 'hours', 'hours.owner_phone', 'Hello, mileage for {client} in {area} was {mileage_cost}, which is {mileage_share} of the price. {company}'),
    M('o_plan', 'Owner: plan hours differ from actual', 'hours_plan', 'hours_plan.owner_phone', 'Hello, plan hours differ from actual hours for {package}: {plan_hours} planned against {actual_hours} on average, a gap of {gap_share}. {company}'),
    M('o_range', 'Owner: the local range check', 'pk_profit', 'pk_profit.owner_phone', 'Hello, the local range check says {range_check} for {package} at a price of {price}. {company}'),
    M('o_idea', 'Owner: a new package idea', 'packages', 'packages.owner_phone', 'Hello, a new package idea based on {package} at {price} for {plan_hours} planned hours is ready for your review. {company}'),
    M('a_list', 'Admin: update the price list', 'price_list', 'price_list.admin_phone', 'Hello, please update the price list on {price_change_date}: {package} moves to {next_price}. {company}'),
    M('a_notice', 'Admin: send the price notice', 'price_list', 'price_list.admin_phone', 'Hello, please send the price change notice for {package} clients before {price_change_date}. {company}'),
    M('a_addon', 'Admin: add-on to invoice', 'addons', 'addons.admin_phone', 'Hello, {addon} for {client} was sold on {date} at {price}. Please add it to the invoice. {company}'),
    M('d_client', 'Doula: your client and package', 'clients', 'clients.doula_phone', 'Hello {doula}, {client} is booked on {package} from {signed_on}. Please plan the visits. {company}'),
    M('d_hours', 'Doula: hours logged against plan', 'hours', 'hours.doula_phone', 'Hello {doula}, hours logged for {client}: {total_hours} against {plan_hours} planned. Please check your log. {company}'),
    M('d_prenatal', 'Doula: log your prenatal hours', 'hours', 'hours.doula_phone', 'Hello {doula}, please log your prenatal hours for {client}: {prenatal_hours} so far. {company}'),
    M('acc_prices', 'Accountant: package prices', 'price_list', 'price_list.accountant_phone', 'Hello, our package prices from {price_change_date} are ready for the new year: {package} will be {next_price}. {company}'),
    M('ph_ref', 'Photographer: referral for a client', 'addons', 'addons.photographer_phone', 'Hello, {client} booked the photography referral at {price} on {date}. Please confirm your fee and the date. {company}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ KPIs (30), dashboard, insights
K12 = '{range:contracts.signed_on},%s' % D365
kpis = [
    KPI('Packages on offer', 'COUNTIFS({range:packages.price},">0")', 'int'),
    KPI('Contracts signed, last 30 days', 'COUNTIFS({range:contracts.signed_on},%s)' % D30, 'int'),
    KPI('Contracts signed, last 12 months', 'COUNTIFS(%s)' % K12, 'int'),
    KPI('Average package price, last 90 days', 'IFERROR(AVERAGEIFS({range:contracts.price},{range:contracts.signed_on},%s),0)' % D90, 'money'),
    KPI('Package income booked, last 12 months', 'SUMIFS({range:contracts.price},%s)' % K12, 'money'),
    KPI('Average income per hour, all packages', 'IFERROR((SUM({range:hours.price})-SUM({range:hours.mileage_cost}))/SUM({range:hours.total_hours}),0)', 'money'),
    KPI('Income per hour of the best package', 'MAX({range:pk_profit.pph_pkg})', 'money'),
    KPI('Income per hour of the lowest package', 'IFERROR(INDEX({range:pk_profit.actual_pph},MATCH(1,{range:pk_profit.rank},0)),0)', 'money'),
    KPI('Packages below the target per hour', 'COUNTIFS({range:pk_profit.flag},%s)' % ck('Below the target'), 'int'),
    KPI('Plan hours per finished client', 'IFERROR(AVERAGE({range:hours.plan_hours}),0)', 'num'),
    KPI('Actual hours per finished client', 'IFERROR(AVERAGE({range:hours.total_hours}),0)', 'num'),
    KPI('Share of clients over plan hours', 'IFERROR(COUNTIFS({range:hours.over_plan},1)/COUNTIFS({range:hours.client_id},"<>"),0)', 'pct'),
    KPI('Average mileage cost per client', 'IFERROR(AVERAGE({range:hours.mileage_cost}),0)', 'money'),
    KPI('Mileage share of income', 'IFERROR(SUM({range:hours.mileage_cost})/SUM({range:hours.price}),0)', 'pct'),
    KPI('Birth packages sold, last 30 days', 'COUNTIFS({range:contracts.kind},%s,{range:contracts.signed_on},%s)' % (BIR, D30), 'int'),
    KPI('Postpartum packs sold, last 30 days', 'COUNTIFS({range:contracts.kind},%s,{range:contracts.signed_on},%s)' % (POS, D30), 'int'),
    KPI('Combined packages sold, last 30 days', 'COUNTIFS({range:contracts.kind},%s,{range:contracts.signed_on},%s)' % (COM, D30), 'int'),
    KPI('Combined share of contracts, 12 months', 'IFERROR(COUNTIFS({range:contracts.kind},%s,%s)/COUNTIFS(%s),0)' % (COM, K12, K12), 'pct'),
    KPI('Add-on income, last 90 days', 'SUMIFS({range:addons.price},{range:addons.date},%s)' % D90, 'money'),
    KPI('Add-ons per 100 contracts, 12 months', 'IFERROR(100*COUNTIFS({range:addons.date},%s)/COUNTIFS(%s),0)' % (D365, K12), 'num'),
    KPI('Discount given, last 12 months', 'SUMIFS({range:contracts.discount_given},%s)' % K12, 'money'),
    KPI('Clients on a discount, last 12 months', 'COUNTIFS({range:contracts.discount_given},">0",%s)' % K12, 'int'),
    KPI('Average discount of discounted clients', 'IFERROR(AVERAGEIFS({range:contracts.discount_pct},{range:contracts.discount_given},">0"),0)', 'pct'),
    KPI('Price list age in days', '{today}-{set:price_list_date}', 'int'),
    KPI('Packages inside your local range', 'COUNTIFS({range:pk_profit.in_range},1)', 'int'),
    KPI('Postpartum pack price per hour, average', 'IFERROR(AVERAGE({range:pp_price.pack_pph}),0)', 'money'),
    KPI('Hours worked beyond plan, last 12 months', 'SUMIFS({range:hours.over_hours},{range:hours.month},%s)' % D365, 'num'),
    KPI('Complete Care Bundle income per hour', 'IFERROR(INDEX({range:pk_profit.actual_pph},MATCH(%s,{range:pk_profit.package},0)),0)' % tok('package', 'Complete Care Bundle'), 'money'),
    KPI('Most sold package, last 90 days', 'IFERROR(INDEX({range:pk_profit.package},MATCH(MAX({range:pk_profit.sold_pkg}),{range:pk_profit.sold_pkg},0)),"")', 'text'),
    KPI('Income share of the top package', 'IFERROR(MAX({range:pk_profit.income_pkg})/SUM({range:pk_profit.income_pkg}),0)', 'pct'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Package Profit Dashboard", "kpis": kpis,
    "monthly": {"title": "Contracts signed and combined packages sold", "date": "sales_month.month", "series": [
        {"label": "Contracts signed", "sum": "sales_month.contracts", "date": "sales_month.month"}, {"label": "Combined packages sold", "sum": "sales_month.combined", "date": "sales_month.month"}]},
    "breakdowns": [{"title": "Income booked by kind", "by": "contracts.kind", "value": "contracts.price", "agg": "sum"}, {"title": "Discount given by discount", "by": "contracts.discount", "value": "contracts.discount_given", "agg": "sum"},
                   {"title": "Add-on income by add-on", "by": "addons.addon", "value": "addons.price", "agg": "sum"}, {"title": "Mileage cost by area", "by": "hours.area", "value": "hours.mileage_cost", "agg": "sum"}]}
def SER(kind_label, label): return AGG('sum', 'mix', 'mix.income', date='mix.month', where=[('kind', '=', tok('pkind', kind_label))], label=label)
insights = {"filters": [{"label": "Doula", "list": "doula"}, {"label": "Service area", "list": "area"}, {"label": "Client kind", "list": "ckind"}],
    "gauges": [
        {"title": "Packages at or above the target", "num": AGG('count', 'pk_profit', where=[('flag', '=', ck('Above the target'))]), "den": AGG('count', 'pk_profit', where=[('flag', '<>', ck('Add-on'))])},
        {"title": "Clients within plan hours", "num": AGG('count', 'hours', where=[('over_plan', '=', 0)]), "den": AGG('count', 'hours')},
        {"title": "Combined packages that pay", "num": AGG('count', 'bundles', where=[('bundle_flag', '=', ck('Bundle pays'))]), "den": AGG('count', 'bundles')},
        {"title": "Add-ons sold per contract", "num": AGG('count', 'addons'), "den": AGG('count', 'contracts')},
        {"title": "Packages inside the local range", "num": AGG('count', 'pk_profit', where=[('in_range', '=', 1)]), "den": AGG('count', 'pk_profit')},
        {"title": "Clients with mileage within your limit", "num": AGG('count', 'hours', where=[('mileage_share', '<=', '{set:mileage_share_max}')]), "den": AGG('count', 'hours')}],
    "charts": [
        CHART('Contracts per month', 'column', 'month', [AGG('count', 'contracts', date='contracts.signed_on', label='Contracts')]),
        CHART('Contracts by package', 'bar', 'contracts.package', [AGG('count', 'contracts', label='Contracts')]),
        CHART('Contracts by kind', 'bar', 'contracts.kind', [AGG('count', 'contracts', label='Contracts')]),
        CHART('Contracts by discount', 'bar', 'contracts.discount', [AGG('count', 'contracts', label='Contracts')]),
        CHART('Contracts by status', 'bar', 'contracts.status', [AGG('count', 'contracts', label='Contracts')]),
        CHART('Income booked by package', 'bar', 'contracts.package', [AGG('sum', 'contracts', 'contracts.price', label='Income booked')]),
        CHART('Income booked per month by kind', 'column', 'month', [SER('Birth', 'Birth'), SER('Postpartum', 'Postpartum'), SER('Combined', 'Combined'), SER('Add-on', 'Add-on')]),
        CHART('Average price per month', 'column', 'month', [AGG('avg', 'sales_month', 'sales_month.avg_price', date='sales_month.month', label='Average price')]),
        CHART('Add-ons sold by add-on', 'bar', 'addons.addon', [AGG('count', 'addons', label='Add-ons sold')]),
        CHART('Add-on income per month', 'column', 'month', [AGG('sum', 'addons', 'addons.price', date='addons.date', label='Add-on income')]),
        CHART('Add-ons sold by doula', 'bar', 'addons.doula', [AGG('count', 'addons', label='Add-ons sold')]),
        CHART('Clients by doula', 'bar', 'clients.doula', [AGG('count', 'clients', label='Clients')]),
        CHART('Plan hours by package', 'bar', 'hours_plan.package', [AGG('avg', 'hours_plan', 'hours_plan.plan_hours', label='Plan hours')]),
        CHART('Actual hours per client by package', 'bar', 'hours_plan.package', [AGG('avg', 'hours_plan', 'hours_plan.actual_hours', label='Actual hours')]),
        CHART('Income per hour by package', 'bar', 'pk_profit.package', [AGG('avg', 'pk_profit', 'pk_profit.actual_pph', label='Income per hour')]),
        CHART('Mileage cost per client by package', 'bar', 'mileage_pkg.package', [AGG('avg', 'mileage_pkg', 'mileage_pkg.mileage_cost', label='Mileage cost per client')]),
        CHART('Mileage cost per month', 'column', 'month', [AGG('sum', 'hours', 'hours.mileage_cost', date='hours.month', label='Mileage cost')]),
        CHART('Mileage cost by area', 'bar', 'hours.area', [AGG('sum', 'hours', 'hours.mileage_cost', label='Mileage cost')]),
        CHART('Discount given per month', 'column', 'month', [AGG('sum', 'sales_month', 'sales_month.discount_given', date='sales_month.month', label='Discount given')]),
        CHART('Contracts per postpartum pack', 'bar', 'pp_price.package', [AGG('avg', 'pp_price', 'pp_price.contracts', label='Contracts')]),
        CHART('Combined contracts per month', 'column', 'month', [AGG('count', 'contracts', date='contracts.signed_on', where=[('kind', '=', tok('ckind', 'Combined'))], label='Combined contracts')]),
        CHART('Clients by kind', 'bar', 'clients.kind', [AGG('count', 'clients', label='Clients')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Package profit per hour, ranked", "why": "every package set against the hours really spent in each phase, with mileage taken off, so the lowest-earning one is named before it costs you another year", "where": "Package profit"},
    {"name": "Is my price right? verdict", "why": "your own owner pay and costs turned into the income per hour you need, the price needed and a raise, hold or lower verdict", "where": "Is my price right"},
    {"name": "Combined-package test", "why": "the bundle price against its parts, the discount given and the income per hour, with a verdict that says whether the bundle pays", "where": "Combined-Package Test"},
    {"name": "Add-on keep, reprice or drop", "why": "income, hours and attach rate of each add-on against your target, so a small add-on never hides a loss", "where": "Add-on Keep or Drop"},
    {"name": "Break-even price solver", "why": "the price that earns exactly your target per hour at plan hours and at actual hours, in closed form", "where": "Break-Even Price Solver"},
    {"name": "Hour-pack sizing", "why": "the 40, 80 and 120 hour packs and the night pack against the shift rates, with the discount each gives away", "where": "Hour-Pack Sizing"},
    {"name": "Discount ceiling", "why": "the biggest community-rate or returning-client discount that still holds your target income per hour", "where": "Discount Ceiling"},
    {"name": "Plan hours against actual hours", "why": "the hours each package plans against the hours your finished clients took, with the clients over plan", "where": "Hours plan vs actual"},
    {"name": "Price change scenarios", "why": "a rise or cut on one package in a Base, Best or Worst scenario, with the effect on yearly income and income per hour", "where": "Price Change Scenario"},
    {"name": "Local range position", "why": "each package price against your own local low and high, with a below, inside or above verdict", "where": "Local Range Position"}]
competitors = [
    {"what": "free client-tracker templates", "lacks": "list clients and payments but never count the hours a package really takes, so they cannot show the income per hour"},
    {"what": "subscription practice-management software", "lacks": "charge every month for invoices and notes but give no package profit, no bundle test and no price check against your own target"},
    {"what": "generic invoice spreadsheets", "lacks": "total what was billed and know nothing of prenatal, on-call, birth and postpartum hours or of mileage"},
    {"what": "single-sheet price lists", "lacks": "show a price per package but never compare it with your costs, your local range or the discounts you give"},
    {"what": "pricing blog posts and rate surveys", "lacks": "describe other businesses and cannot work out the price your own hours and costs need"}]
guide = [
    'Open Start and type your business name and your own limits in the yellow cells: the target income per hour, the plan hours of a visit, the highest mileage share and the date of your price list.',
    'Check Packages, Pay rates, Areas and Local price range. They hold the prices, planned hours, shift rates, mileage rates and your own local range that the other sheets read.',
    'Paste your finished clients into Actual hours by client: prenatal, on-call contact, birth and postpartum hours and the mileage cost, taken from your logs.',
    'Keep Contracts and Add-ons sold up to date. Package profit, Package mix by month and Package sales by month count from them.',
    'Read Package profit first: it ranks every package by income per hour and checks it against your target and your local range.',
    'Use Bundle test, Discount effect and Add-on attach to see what the combined packages, the discounts and the add-ons do to your income.',
    'Open Hours plan vs actual and Mileage by package to find a package whose plan hours or travel cost is wrong.',
    'Use Postpartum price per hour to compare each hour pack with the shift rates, and Price list with discounts to write the next list.',
    f'Run the {len(tools)} calculators before you change a price, a discount, a pack or a package: each ends in a clear verdict and has a what-if grid.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'A solo doula can use the same sheets with one doula and no backup rota: keep one row in each doula list.',
    'Read the Package Profit Dashboard and the charts every month: income per hour, plan against actual hours, mileage, discounts and add-ons.']
listing = {"title": "Doula Business Package Pricing and Profit per Hour Excel Template: Price Check, Bundle Test, Add-on Income, Hour Packs",
    "headline": "Know what every package really earns for each hour you give",
    "tags": ["doula business", "doula pricing", "package pricing", "profit per hour", "doula packages", "excel template", "hour pack", "price list", "bundle pricing", "add-on income", "doula agency", "income per hour", "mileage log"],
    "description": ("Price a doula business from the hours it really takes. Built for an owner-doula who runs a small agency or works alone, with packages for birth, postpartum hours and a combined package. "
        "Package profit sets every package against the prenatal, on-call, birth and postpartum hours of your finished clients and the mileage cost, ranks them from the lowest income per hour and checks each against your own target and your own local price range.\n\n"
        "Bundle test compares a combined package with the birth package and the postpartum pack it is made of. Discount effect shows what the community rate and the returning-client discount give up each quarter. Add-on attach shows how often each add-on sells. "
        "Hours plan vs actual finds a package whose planned hours are wrong, Mileage by package shows where a travel fee is due and Postpartum price per hour sets every hour pack against your shift rates.\n\n"
        f"{len(tools)} calculators answer the questions you ask each week: which package earns the least, is the price right, does the bundle pay, keep or drop an add-on, the break-even price, the pack ladder, the discount ceiling, a travel fee, a new package, next year's price plan and a 3-month sales forecast. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to clients, enquirers, the owner-doula, doulas, the admin, the accountant and a photographer.\n\n"
        "This is part two of the Doula Business suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Clients appear by name, package, doula and dates only, with no medical detail, and the sheets count hours, dates and money, never outcomes. Prices and targets are your own settings: confirm tax and local rules with your adviser."),
    "features": ["Package profit ranked by income per hour", "Is my price right verdict", "Combined-package test", "Add-on keep or drop", "Break-even price solver", "Hour-pack ladder against shift rates",
                 "Discount ceiling for community rate", "Plan hours against actual hours", f"{len(tools)} calculators for pricing decisions", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
HINTS = {
 'packages': 'One row per package or add-on: list price, birth and postpartum parts, visits and planned hours; the plan hours, price per plan hour and deposit fill in by themselves.',
 'hours': 'One row per finished client: prenatal, on-call, birth and postpartum hours and mileage cost from your logs; total hours, income per hour and hours over plan fill in.',
 'addons': 'One row per add-on sold: date, client, price, hours and doula; the price per hour and the contact phones fill in by themselves.',
 'pk_profit': 'One row per package: price and plan hours against the hours and mileage of finished clients; the income per hour, rank, target check and local range check fill in.',
 'bundles': 'One row per combined package and 3-month period: contracts sold, price against its parts, discount given and income per hour against its parts.',
 'local_range': 'One row per kind: your own local low and high, a package price for birth, combined and add-on and a price per hour for postpartum and night.',
 'price_scn': 'One row per scenario and price change: type the share of sign-ups lost per 1% rise; the income change and income per hour after the change fill in.',
 'clients': 'One row per client (name, area, package, doula and dates only, no medical detail): add a prospect with the status Enquiry; plan hours, hours left and price lookups fill in.',

 'price_right': 'Pick a package; type your owner pay, costs and billable hours: see the income per hour you need, the price needed, your local range and a raise, hold or lower verdict.',
 'bundle_tool': 'Pick a combined package: its price against its parts at list price, the discount given, the hours and income per hour; the verdict says whether the bundle pays against your target.',
 'breakeven': 'Pick a package and your target income per hour: the price that earns exactly that at plan hours and at actual hours, against the list price and the average price paid.',
 'price_chg': 'Pick a package, a price change and a Base, Best or Worst scenario: your sign-ups of 12 months, the income and the income per hour after the change.',
 'pp_rate_check': 'Pick a pack and a shift: the pack price per hour against the hourly rate, the minimum booking and how much the pack saves; the verdict compares it with your limit.',
 'pack_ladder': 'Pick a shift: the price per hour and the discount of each hour pack against that rate and your sales of 12 months; keep the ladder, reprice a pack or drop the 120.',
 'disc_ceiling': 'Pick a package and a discount: the highest discount that still holds your target income per hour, in closed form, and a verdict against the discount you give.',
 'travel_fee': 'Pick an area: the mileage rate, what mileage cost your finished clients there as a share of the price and the fee per client that brings it back to your limit.',
 'plan_actual': 'Pick a package: the plan hours against the hours finished clients took, the clients over plan and the income per hour at each; the verdict points to the price or the plan.',
 'volume_grid': 'Pick a package: its sales of 12 months against the average package and its income per hour against your target; the verdict is promote, keep, reprice or retire.',
 'new_pkg': 'Type the visits and hours of a new package, a travel allowance and your target: the price needed, the deposit and its place in your local range; launch or adjust it.',
 'next_year': 'Pick a package, a planned rise and how much your costs rise: the income per hour after the rise against the raised target and the yearly income; the rise holds or is too small.',
 'sales_fc': 'Pick a Base, Best or Worst scenario: the same 3 months a year ago by kind times your growth of the last 6 months, set against your last 3 months.',
 'oncall_len': 'Type the on-call window (days around the estimated due date), a shorter one and the share of births inside it; see the contact hours saved, free days and income per hour.',
 'range_pos': 'Pick a package and a price to test: it is set against the low and high of your own local range for its kind, a price per hour for postpartum, with the packages in each band.',
 'sensitivity': 'Pick a package and a price step and an hours step: income per hour when the price or the hours move; the verdict names the input that matters most.',
}
for _t in tables + tools:
    if _t['key'] in HINTS: _t['hint'] = HINTS[_t['key']]
for _t in tables: _t['rows'] = max(50, _t['rows'])
s = spec(id='fx-20261115-doula-business-p2', slug='doula-business-packages', profession='Doula Business', name='Packages, Pricing and Profit',
         tagline='Know what every package really earns for each hour you give', price_usd=29, colors={"primary": "#4A3F6B", "accent": "#E8A87C"},
         settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide, listing=listing, insights=insights,
         suite={"key": SUITE, "part": 2, "of": 8, "focus": "Packages, pricing and profit per hour"}, signature=signature, competitors=competitors, tools=tools, messages=messages,
         documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'du2.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
