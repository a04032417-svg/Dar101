"""Florist and Floral Design Business suite (Dar Templates) - shared demo story for ALL eight parts.

Pure data + tiny helpers + deterministic row generators, independent of call order (cached worlds are built on first use). The demo business is "Juniper & Vine Florals"
(fictional): a flower studio with a small retail counter run by an owner-designer (Marisol Vega, FL-01) with 2 floral designers on salary (FL-02 Thea Lindgren, FL-03 Kofi Asante),
a part-time shop assistant (FL-04 Hana Sato, hourly), a delivery driver (FL-05 Dmitri Petrov, hourly) and 4 freelance helpers on wedding weekends and holiday peaks (FL-06..FL-09 Aisha Rahman,
Lucas Weber, Camila Torres, Emeka Obi, day rate), plus 7 outside contacts (FL-10 accountant, FL-11 and FL-12 two flower wholesalers = "Wholesaler A" and "Wholesaler B", FL-13 local grower,
FL-14 supplies wholesaler, FL-15 van mechanic, FL-16 rentals partner). About 60 weddings and events a year (proposals built from flower recipes), daily retail (walk-in, phone, online, about
6,100 orders over ~2 years, oldest first), sympathy work (5 funeral-home accounts plus direct orders), 8 corporate standing-order accounts (10 standing arrangements), local delivery in 4 zones,
weekly wholesale orders plus event orders (~840 orders, ~5,700 lines), a cooler with waste and substitutions, 12 rental items, 16 supplies. Peaks: Valentine's Day, Mother's Day, Easter,
the year-end holidays and wedding season May-October. One generic currency; every date is relative to the build day. History = 24 months (HISTORY_START), events booked up to HORIZON (6 months ahead).

Money model: a recipe = stems x wholesale cost per stem + hard goods, LIST PRICE = flowers x MARKUP_FLOWERS (4.0) + greens x MARKUP_GREENS (3.5) + hard goods x MARKUP_HARD (2.5)
+ labour minutes / 60 x LABOUR_CHARGE_HOUR (45); a design hour COSTS the business LABOUR_COST_HOUR (20). Actual stem cost on a date = base cost x season shape x holiday surge x price index
(0.94 more than a year ago, 1.00, then 1.07 since a wholesale price rise PRICE_RISE_DAYS ago) x supplier factor; stem_cost(item, date) and goods_cost(recipe, date) give it. Shop prices rose 3% on 1 January
of this year. Retail order = recipe x size (0.8, 1.0, 1.25, 1.6); delivery fee by zone unless the order price is at least FREE_DELIVERY_OVER (180). Event proposal = recipe lines x list price x (1 - discount)
+ delivery charge by zone + set-up charge; planned goods cost uses plan_goods(recipe, event_date) (list costs, no price rise); deposit = DEPOSIT_PCT (50%) due 7 days after booking, final balance due
FINAL_DUE_DAYS (14) before the event. Account invoices: one per account per month, issued on the 1st of the next month, due INVOICE_DAYS (30) later. Wholesale lines: bunches = ceil(stems needed x (1 + buffer) /
stems per bunch); waste share about 9% of purchased cost (target WASTE_TARGET 8%), highest for peony, garden rose and ranunculus. Event margin = (final amount - actual goods - waste - design hours x LABOUR_COST_HOUR -
helper pay - logistics) / final amount, about 59% on average. P&L per month: revenue (orders by service date, events by event date, rentals) - flower purchases - labour (pay rows incl. helpers) - overhead
(expense rows incl. card fees and packaging). Cash starts at 50,000, owner draw 7,000 a month, tax set-aside 25% of profit paid quarterly; cash stays above CASH_FLOOR (15,000), lowest in April of last year.

Story rows (ids from story(), never hard-coded): low_margin_proposal (booked wedding quoted with a 32% discount: margin below the floor at today's stem costs), overdue_balance_proposal (wedding in 9 days,
final balance due 5 days ago and unpaid), deposit_missing_proposal (booked 12 days ago, retainer due 5 days ago, not collected), overbuy_line (a wholesale line of Peony for an event that shrank: 60 stems bought,
42 wasted), overdue_account (Meridian Accounting Group: standing orders, 4 unpaid monthly invoices, oldest 76 days past due; no other account invoice is more than 42 days past due and unpaid),
unreturned_rental (a wooden ceremony arch out 40 days past its due date; the only 'Out' item past due), losing_zone ('Zone 4 Valley': fee 15 against a cost of about 47 a stop) and undercosted_standing
(Riverside Boutique Hotel's reception arrangement at 150, margin about 31%).

Exports
  constants: COMPANY SUITE OWNER TODAY HISTORY_START HISTORY_DAYS HORIZON MARKUP_FLOWERS MARKUP_GREENS MARKUP_HARD LABOUR_CHARGE_HOUR LABOUR_COST_HOUR MARGIN_FLOOR MARGIN_TARGET LABOUR_SHARE_TARGET
             OVERBUY_BUFFER SUB_BUFFER WASTE_TARGET ROTATION_DAYS DEPOSIT_PCT FINAL_DUE_DAYS MIN_EVENT_SPEND PROPOSAL_HOUR_COST FREE_DELIVERY_OVER DRIVER_RATE VEHICLE_KM HELPER_RATE OWNER_DRAW
             TAX_SET_ASIDE_PCT CASH_FLOOR HOLIDAY_SHARE_FLAG INVOICE_DAYS RENTAL_DEPOSIT_PCT PRICE_RISE_DAYS PRICE_RISE STORY_ACCOUNT STORY_STANDING_ACCOUNT STORY_ZONE
  dates: ago ahead iso to_date month_start add_months months14() week_start day _ms; helpers pairs first_name fake_phone fake_email rng R2; holiday calendar mothers_day easter holiday_of(date)
         holiday_window(name, year)
  lists: ROLES TEAMS PAY_TYPES CLIENT_TYPES EVENT_TYPES ORDER_TYPES ORDER_STATUS ORDER_KINDS ORDER_PAY RECIPE_KINDS FLOWER_CLASSES SEASONS SUPPLIERS ENQUIRY_STATUS LOST_REASONS ENQUIRY_SOURCES
         CONSULT_KINDS PROPOSAL_STATUS SECTIONS PAYMENT_KINDS PAYMENT_METHODS INVOICE_STATUS WASTE_CAUSES SUB_REASONS DELIVERY_STATUS DELIVERY_WINDOWS HOLIDAYS RENTAL_STATUS STANDING_FREQ STANDING_STATUS
         PAY_STATUS EXPENSE_CATEGORIES MARKETING_KINDS CHANGE_KINDS HELPER_KINDS VENUE_KINDS WEEKDAYS WORKDAYS TAX_STATUS STOCK_STATUS TYPES (the 7 order types of margin by type) AREAS
  names: STAFF_NAMES (9) PAID_STAFF (8, pay rows) DESIGNERS (3) FREELANCERS (4) OUTSIDE (7) HOLDERS VENUE_NAMES ZONES RENTAL_ITEMS RECIPES (35) PRODUCTS (21 shop recipes) EVENT_RECIPES (14)
  people and reference (lists of dicts): staff (9) contacts (7) team (16: staff_id name role team pay_type phone email hours_week monthly_salary hourly_rate day_rate speciality country start)
         flowers (34: flower_id variety flower_class stems_per_bunch cost_spring cost_summer cost_autumn cost_winter base_cost supplier shrink_factor) supplies (16: supply_id item unit cost par_level on_hand
         reorder_qty supplier) recipes (35: recipe_id recipe kind labour_minutes goods_cost list_price stems) recipe_lines (244: line_id recipe_id recipe item item_class qty) zones (4: zone_id zone fee minutes km
         share cost) rental_items (12: item_id item units purchase_price rent_price damage_fee bookings_year) venues (12: venue_id name kind area contact phone) suppliers (4: supplier kind order_days lead_days
         minimum_order delivery_fee price_factor); dicts FL (by variety) HG (hard goods by item) RC (recipes) ZN (zones) RI (rental items) SUP (suppliers)
  cost helpers: stem_cost(item, date) goods_cost(recipe, date) plan_goods(recipe, event_date) recipe_price(name) recipe_cost_list(name) price_index(date) proposal_margin(pid, now=True)
         zone_profit(zone, months=12) standing_margin(standing_id) story()
  generators (fresh lists of dicts, oldest first; n= thins a long list but keeps the most recent rows; optional dates are '' when blank):
    client_rows order_rows standing_order_rows invoice_rows enquiry_rows consultation_rows proposal_rows proposal_line_rows revision_rows change_rows event_result_rows event_day_rows review_rows
    rental_rows helper_rows payment_rows wholesale_order_rows wholesale_line_rows waste_rows stock_rows substitution_rows delivery_rows supply_month_rows pay_rows marketing_rows expense_rows
    type_month_rows pnl_rows tax_rows cash_rows holiday_rows holiday_day_rows
Columns (ids first): client_rows client_id client client_type contact area zone source phone email orders lifetime_value first_order payment_terms_days; order_rows order_id date(placed) needed_on week month
  order_type client_id client recipe kind size price flower_cost labour_minutes zone delivery_fee pay_method preorder(bool) status; standing_order_rows standing_id client zone recipe frequency weekday started_on
  price status next_date last_date list_price; invoice_rows invoice_id client_id client month issued_on due_date amount paid_amount paid_on status orders; enquiry_rows enquiry_id date name event_type event_date guests
  budget source venue phone email status consult_date proposal_id booked_on lost_reason quoted; consultation_rows consult_id date enquiry_id client kind minutes fee; proposal_rows proposal_id enquiry_id client
  event_type event_date venue zone guests budget sent_on status revisions proposal_hours subtotal discount_pct delivery_charge setup_charge price planned_goods_cost planned_hours booked_on deposit deposit_due
  deposit_paid_on final_amount final_due final_paid_on cancelled_on source lost_reason; proposal_line_rows line_id proposal_id section recipe qty unit_price line_price; revision_rows revision_id proposal_id client round
  date hours charged fee; change_rows change_id proposal_id client date kind old_amount new_amount retainer_kept; event_result_rows result_id proposal_id client event_type event_date final_amount
  planned_goods_cost actual_goods_cost planned_hours actual_hours helper_hours helper_cost waste_cost logistics_cost margin; event_day_rows day_id proposal_id client date zone load_hours drive_hours setup_hours
  strike_hours helpers vehicle_km logistics_cost charged; review_rows review_id proposal_id client event_type venue event_date asked_on received_on rating(0 = none) repeat_client referred_others value;
  rental_rows rental_id date_out proposal_id client item qty due_back returned_on damaged lost rent_charge deposit_held deposit_kept status; helper_rows helper_id date month person kind proposal_id event hours rate pay
  status; payment_rows payment_id date month client_id client proposal_id invoice_id order_id kind amount method; wholesale_order_rows order_id date arrival month supplier kind proposal_id event lines total status;
  wholesale_line_rows line_id order_id date arrival month supplier kind proposal_id variety flower_class needed bunches stems cost_stem cost used waste_stems status; waste_rows waste_id date month variety
  flower_class supplier stems cost cause line_id order_id; stock_rows lot_id received variety supplier stems_in stems_left cost_stem; substitution_rows sub_id date proposal_id client planned_variety actual_variety
  stems planned_cost_stem actual_cost_stem cost_diff reason client_signoff; delivery_rows delivery_id date week month order_id client zone window stop driver minutes km cost fee_charged status time;
  supply_month_rows row_id month item used bought cost; pay_rows pay_id month person pay_type hours rate gross_pay employer_cost total_cost status paid_on; marketing_rows campaign_id month kind source spend;
  expense_rows expense_id date month category amount; type_month_rows row_id month type revenue goods_cost labour_cost delivery_cost orders; pnl_rows row_id month revenue flower_cost labour_cost overhead profit;
  tax_rows tax_id month profit set_aside paid_amount paid_on status; cash_rows row_id month cash_start cash_in cash_out owner_draw tax_paid cash_end cash_floor; holiday_rows holiday_id holiday year start end orders
  stems revenue avg_ticket preorders preorder_value helper_hours status; holiday_day_rows day_id holiday year date capacity orders preorders deposits stems.
Lessons: money cells are plain amounts; optional dates (sent_on, booked_on, paid_on, returned_on, consult_date, received_on, cancelled_on, next_date) are '' when blank: wrap lookups with IF(x=0,"",x).
Links hold NAMES (client, recipe, variety, zone, supplier, item) or ids (CL-0001 EN-0001 EP-0001 OR-00001 WO-0001 WL-00001 WS-00001 DL-00001 PM-00001 IN-0001 RN-0001 PL-00001). Unused list values to know:
INVOICE_STATUS 'Part paid' is rare (a few recent invoices); PAY_STATUS 'Due' is last month's pay (paid on the 20th); ORDER_STATUS 'Open' = service date today or later. A client with no orders is not listed.
Words: no brand, wholesaler, grower, bank or company names; no law or standard names; no claims about flower longevity or safety: the cooler rotation rule is the owner's own setting (ROTATION_DAYS).
"""
import datetime as dt
import calendar
import random
import hashlib
import math

COMPANY = 'Juniper & Vine Florals'
SUITE = 'fx-20261115-florist'
OWNER = 'Marisol Vega'
TODAY = dt.date.today()
D = dt.date

# ------------------------------------------------------------------ settings and rules (the editable targets of the suite; benchmarks are starting points, not facts)
MARKUP_FLOWERS = 4.0         # multiplier on wholesale cost of focal, filler and line flowers
MARKUP_GREENS = 3.5          # multiplier on greenery
MARKUP_HARD = 2.5            # multiplier on hard goods (containers, ribbon, wire, tape, mechanics)
LABOUR_CHARGE_HOUR = 45.0    # labour charged to the client per design hour
LABOUR_COST_HOUR = 20.0      # what a design hour costs the business (wages and extras)
MARGIN_FLOOR = 0.55          # gross margin below this is a red flag on a proposal or product
MARGIN_TARGET = 0.62         # wanted gross margin
LABOUR_SHARE_TARGET = 0.30   # labour share of an event price (25-35% band)
OVERBUY_BUFFER = 0.18        # event stems ordered above the recipe total (15-25% band)
SUB_BUFFER = 0.07            # substitution buffer on event orders (5-10% band)
WASTE_TARGET = 0.08          # waste share of purchased flower cost
ROTATION_DAYS = 5            # stems older than this in the cooler are used first or dumped (owner's own rule)
DEPOSIT_PCT = 0.50           # retainer share taken at booking
FINAL_DUE_DAYS = 14          # final balance due this many days before the event
MIN_EVENT_SPEND = 900.0      # smallest event worth taking
PROPOSAL_HOUR_COST = 45.0    # value of one hour of owner time spent on a proposal
FREE_DELIVERY_OVER = 180.0   # retail orders at or above this get free delivery
DRIVER_RATE = 20.0           # driver cost per hour
VEHICLE_KM = 0.60            # vehicle cost per km
HELPER_RATE = 20.0           # freelance helper per hour (day = 8 hours)
OWNER_DRAW = 7000.0
TAX_SET_ASIDE_PCT = 0.25     # confirm with your adviser
CASH_FLOOR = 15000.0
HOLIDAY_SHARE_FLAG = 0.45    # share of yearly sales in the top peaks above which the calendar is a risk
INVOICE_DAYS = 30
RENTAL_DEPOSIT_PCT = 0.5
PRICE_RISE_DAYS = 110        # a wholesale price rise took effect this many days ago
PRICE_RISE = 0.07


def day(n): return dt.timedelta(days=n)
def iso(d): return d.isoformat() if hasattr(d, 'isoformat') else d
def ago(days): return iso(TODAY - dt.timedelta(days=days))
def ahead(days): return iso(TODAY + dt.timedelta(days=days))
def to_date(s): return D.fromisoformat(s) if isinstance(s, str) and s else s


def month_start(k):
    y, m = TODAY.year, TODAY.month - k
    while m <= 0: m += 12; y -= 1
    while m > 12: m -= 12; y += 1
    return dt.date(y, m, 1)


def add_months(d, n):
    y, m = d.year, d.month + n
    while m > 12: m -= 12; y += 1
    while m <= 0: m += 12; y -= 1
    return dt.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def months14(): return [month_start(k) for k in range(13, -1, -1)]
def week_start(d): return d - day(d.weekday())


def pairs(labels):
    out = []
    for s in labels:
        k = ''.join(ch if ch.isalnum() else '_' for ch in s.lower()).strip('_')
        while '__' in k: k = k.replace('__', '_')
        out.append((k, s))
    return out


def first_name(name): return name.split()[0]
def fake_phone(i): return '+%d %d 555 %04d' % ([1, 44, 49, 61, 33, 34, 351, 31][i % 8], 20 + (i * 7) % 79, 3000 + (i * 37) % 6000)
def fake_email(name, i=0): return name.lower().replace(' ', '.').replace("'", '').replace('&', 'and') + (str(i) if i else '') + '@mail.example.com'
def rng(tag=''): return random.Random('fl-core-20261115-' + str(tag))
def R2(x): return round(x + 1e-9, 2)
def _ms(d): return dt.date(d.year, d.month, 1)
def _eom(d): return dt.date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])


HISTORY_START = month_start(23)
HISTORY_DAYS = (TODAY - HISTORY_START).days
HORIZON = add_months(_ms(TODAY), 6)          # events are booked up to here

# ------------------------------------------------------------------ lists (plain international English; keys from pairs() stay <= 21 characters)
ROLES = ['Owner designer', 'Floral designer', 'Shop assistant', 'Delivery driver', 'Freelance helper', 'Accountant', 'Flower wholesaler', 'Local grower', 'Supplies wholesaler',
         'Van mechanic', 'Rentals partner']
TEAMS = ['Management', 'Studio', 'Shop', 'Delivery', 'Outside']
PAY_TYPES = ['Owner draw', 'Salary', 'Hourly', 'Day rate', 'Invoice']
CLIENT_TYPES = ['Couple', 'Event client', 'Retail customer', 'Sympathy account', 'Corporate account']
EVENT_TYPES = ['Wedding', 'Corporate event', 'Party', 'Memorial service', 'Installation']
ORDER_TYPES = ['Walk-in', 'Phone', 'Online', 'Sympathy', 'Standing order']
ORDER_STATUS = ['Open', 'Done']
RECIPE_KINDS = ['Retail', 'Holiday', 'Sympathy', 'Wedding', 'Event', 'Corporate']
ORDER_KINDS = ['Retail', 'Holiday', 'Sympathy', 'Corporate']
FLOWER_CLASSES = ['Focal', 'Filler', 'Line', 'Greenery', 'Hard goods']
SEASONS = ['Spring', 'Summer', 'Autumn', 'Winter']
SUPPLIERS = ['Wholesaler A', 'Wholesaler B', 'Local grower', 'Supplies wholesaler']
ENQUIRY_STATUS = ['New', 'Consultation booked', 'Proposal sent', 'Booked', 'Lost', 'Declined']
LOST_REASONS = ['Over budget', 'Date taken', 'Chose another florist', 'No reply', 'Below minimum', 'Changed plans']
ENQUIRY_SOURCES = ['Past client', 'Venue referral', 'Planner referral', 'Social media', 'Web search', 'Walk-in', 'Wedding fair', 'Online directory']
CONSULT_KINDS = ['Phone call', 'Studio visit', 'Venue visit', 'Video call']
PROPOSAL_STATUS = ['Draft', 'Sent', 'Booked', 'Completed', 'Lost', 'Cancelled']
SECTIONS = ['Bouquets and wearables', 'Ceremony', 'Reception tables', 'Installations', 'Delivery and set-up']
PAYMENT_KINDS = ['Deposit', 'Final balance', 'Account invoice', 'Pre-order deposit', 'Rental deposit']
PAYMENT_METHODS = ['Card', 'Bank transfer', 'Cash']
INVOICE_STATUS = ['Paid', 'Part paid', 'Unpaid']
WASTE_CAUSES = ['Overbuy', 'Age', 'Damage', 'Quality', 'Event change']
SUB_REASONS = ['Out of stock', 'Quality', 'Price jump', 'Client change', 'Colour match']
DELIVERY_STATUS = ['Delivered', 'Failed', 'Rescheduled', 'Scheduled']
DELIVERY_WINDOWS = ['Morning', 'Midday', 'Afternoon', 'Evening']
HOLIDAYS = ["Valentine's Day", "Mother's Day", 'Easter', 'Year-end holidays']
RENTAL_STATUS = ['Out', 'Returned', 'Part returned', 'Lost']
STANDING_FREQ = ['Weekly', 'Fortnightly', 'Monthly']
STANDING_STATUS = ['Active', 'Paused', 'Ended']
PAY_STATUS = ['Paid', 'Due', 'Accruing']
EXPENSE_CATEGORIES = ['Rent', 'Utilities', 'Vehicle', 'Insurance', 'Phone and internet', 'Order software', 'Marketing', 'Accounting', 'Card fees', 'Packaging and supplies',
                      'Training', 'Equipment', 'Cooler and repairs']
MARKETING_KINDS = ['Online directory', 'Wedding fair', 'Social ads', 'Venue partnership', 'Printed price guide', 'Photo shoot']
CHANGE_KINDS = ['Budget cut', 'Guest count change', 'Item added', 'Cancellation']
HELPER_KINDS = ['Wedding helper', 'Delivery helper', 'Holiday helper']
VENUE_KINDS = ['Venue', 'Planner', 'Photographer', 'Funeral home']
WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
WORKDAYS = WEEKDAYS[:6]
TAX_STATUS = ['Paid', 'Due', 'Upcoming']
STOCK_STATUS = ['Use first', 'Watch', 'Dump']

# ------------------------------------------------------------------ people (16: 9 staff, 7 outside contacts)
# id, name, country, role, team, pay type, hours a week, monthly salary, hourly rate, day rate, speciality, start days ago
_staff = [('FL-01', 'Marisol Vega', 'Colombia', 'Owner designer', 'Management', 'Owner draw', 45, 0, 0, 0, 'Wedding design, proposals and buying', 2900),
          ('FL-02', 'Thea Lindgren', 'Sweden', 'Floral designer', 'Studio', 'Salary', 38, 3800, 0, 0, 'Event design and installations', 1500),
          ('FL-03', 'Kofi Asante', 'Ghana', 'Floral designer', 'Studio', 'Salary', 38, 3600, 0, 0, 'Retail, sympathy and standing orders', 820),
          ('FL-04', 'Hana Sato', 'Japan', 'Shop assistant', 'Shop', 'Hourly', 26, 0, 17.5, 0, 'Counter, phone orders and conditioning', 520),
          ('FL-05', 'Dmitri Petrov', 'Bulgaria', 'Delivery driver', 'Delivery', 'Hourly', 32, 0, DRIVER_RATE, 0, 'Local delivery and event set-up', 1100),
          ('FL-06', 'Aisha Rahman', 'Bangladesh', 'Freelance helper', 'Studio', 'Day rate', 0, 0, 20.0, 160, 'Wedding weekends, ceremony set-up', 700),
          ('FL-07', 'Lucas Weber', 'Germany', 'Freelance helper', 'Studio', 'Day rate', 0, 0, 19.0, 150, 'Buckets, conditioning and strike', 640),
          ('FL-08', 'Camila Torres', 'Peru', 'Freelance helper', 'Studio', 'Day rate', 0, 0, 21.0, 165, 'Bouquets and table work', 410),
          ('FL-09', 'Emeka Obi', 'Nigeria', 'Freelance helper', 'Delivery', 'Day rate', 0, 0, 18.0, 145, 'Holiday delivery and loading', 330)]
staff = []
for i, (a, b, c, ro, te, pt, hw, sal, hr, dr, spec, st) in enumerate(_staff):
    staff.append(dict(staff_id=a, name=b, role=ro, team=te, pay_type=pt, phone=fake_phone(101 + i), email=fake_email(b), hours_week=hw, monthly_salary=float(sal),
                      hourly_rate=float(hr), day_rate=float(dr), speciality=spec, country=c, start=ago(st)))
_ctc = [('FL-10', 'Mateo Alvarez', 'Argentina', 'Accountant', 'Bookkeeping, tax set-aside and yearly accounts'),
        ('FL-11', 'Gabriela Costa', 'Portugal', 'Flower wholesaler', 'Wholesaler A: main weekly and event flower orders'),
        ('FL-12', 'Ravi Menon', 'India', 'Flower wholesaler', 'Wholesaler B: imported focal flowers and holiday roses'),
        ('FL-13', 'Olivia Hartmann', 'Austria', 'Local grower', 'Seasonal local flowers, April to October'),
        ('FL-14', 'Tariq Haddad', 'Lebanon', 'Supplies wholesaler', 'Containers, ribbon, wire, tape and mechanics'),
        ('FL-15', 'Piotr Nowak', 'Poland', 'Van mechanic', 'Delivery van service and repairs'),
        ('FL-16', 'Nadia Okonkwo', 'Nigeria', 'Rentals partner', 'Shared arches and stands for large weddings')]
contacts = [dict(staff_id=a, name=b, role=ro, team='Outside', pay_type='Invoice', phone=fake_phone(108 + i), email=fake_email(b), hours_week=0, monthly_salary=0.0,
                 hourly_rate=0.0, day_rate=0.0, speciality=sp, country=c, start=ago(1200 - i * 90)) for i, (a, b, c, ro, sp) in enumerate(_ctc)]
team = staff + contacts
STAFF_NAMES = [s['name'] for s in staff]
PAID_STAFF = STAFF_NAMES[1:]                           # the 8 people paid through pay rows (the owner takes a draw)
DESIGNERS = [s['name'] for s in staff[:3]]
FREELANCERS = [s['name'] for s in staff if s['role'] == 'Freelance helper']
HOLDERS = STAFF_NAMES + ['Studio']
OUTSIDE = [s['name'] for s in contacts]

# ------------------------------------------------------------------ reference tables: flowers, hard goods, recipes, zones, rentals, venues, suppliers
_SEAS = {'flat': [1.0, 1.0, 1.0, 1.1], 'spring': [0.85, 1.25, 1.5, 1.35], 'summer': [1.25, 0.8, 1.1, 1.5], 'autumn': [1.3, 1.1, 0.85, 1.3], 'winter': [1.1, 1.4, 1.2, 0.85]}
# variety, class, stems per bunch, base cost per stem, season shape, supplier, shrink factor (relative waste)
_FL = [('Garden rose', 'Focal', 10, 2.20, 'flat', 'Wholesaler A', 1.5), ('Peony', 'Focal', 5, 3.60, 'spring', 'Wholesaler B', 1.7), ('Ranunculus', 'Focal', 10, 1.60, 'spring', 'Local grower', 1.4),
       ('Dahlia', 'Focal', 10, 1.70, 'autumn', 'Local grower', 1.2), ('Lily', 'Focal', 10, 2.40, 'flat', 'Wholesaler A', 0.9), ('Hydrangea', 'Focal', 5, 3.20, 'summer', 'Wholesaler A', 1.3),
       ('Anemone', 'Focal', 10, 1.10, 'winter', 'Wholesaler B', 1.3), ('Sunflower', 'Focal', 10, 1.30, 'summer', 'Local grower', 1.0), ('Long-stem rose', 'Focal', 10, 1.35, 'flat', 'Wholesaler B', 1.1),
       ('Tulip', 'Focal', 10, 0.70, 'spring', 'Wholesaler A', 1.1), ('Orchid stem', 'Focal', 10, 2.80, 'flat', 'Wholesaler B', 0.8),
       ('Spray rose', 'Filler', 10, 1.05, 'flat', 'Wholesaler A', 1.0), ('Lisianthus', 'Filler', 10, 1.25, 'summer', 'Wholesaler A', 1.0), ('Alstroemeria', 'Filler', 10, 0.65, 'flat', 'Wholesaler A', 0.7),
       ('Carnation', 'Filler', 20, 0.32, 'flat', 'Wholesaler A', 0.6), ('Spray carnation', 'Filler', 10, 0.55, 'flat', 'Wholesaler A', 0.6), ('Chrysanthemum', 'Filler', 10, 0.60, 'autumn', 'Wholesaler A', 0.7),
       ('Gypsophila', 'Filler', 10, 0.85, 'flat', 'Wholesaler B', 0.8), ('Statice', 'Filler', 10, 0.55, 'summer', 'Wholesaler B', 0.5), ('Waxflower', 'Filler', 10, 0.95, 'winter', 'Wholesaler B', 0.8),
       ('Scabiosa', 'Filler', 10, 1.00, 'summer', 'Local grower', 1.2), ('Zinnia', 'Filler', 10, 0.90, 'summer', 'Local grower', 1.1), ('Freesia', 'Filler', 10, 0.85, 'winter', 'Wholesaler B', 1.0),
       ('Sweet pea', 'Filler', 10, 0.75, 'spring', 'Local grower', 1.5), ('Stock', 'Filler', 10, 1.00, 'spring', 'Wholesaler A', 0.9),
       ('Delphinium', 'Line', 10, 1.50, 'summer', 'Wholesaler A', 1.1), ('Snapdragon', 'Line', 10, 0.95, 'summer', 'Wholesaler A', 0.9), ('Gladiolus', 'Line', 10, 1.20, 'summer', 'Wholesaler A', 0.8),
       ('Eucalyptus', 'Greenery', 10, 0.90, 'flat', 'Wholesaler A', 0.5), ('Ruscus', 'Greenery', 10, 0.75, 'flat', 'Wholesaler A', 0.4), ('Ivy trail', 'Greenery', 10, 0.60, 'flat', 'Local grower', 0.5),
       ('Fern', 'Greenery', 10, 0.50, 'flat', 'Wholesaler A', 0.5), ('Olive branch', 'Greenery', 10, 1.10, 'flat', 'Wholesaler B', 0.4), ('Pittosporum', 'Greenery', 10, 0.70, 'flat', 'Wholesaler A', 0.4)]
flowers = []
for i, (v, cl, spb, base, shape, sup, shr) in enumerate(_FL, 1):
    sv = _SEAS[shape]
    flowers.append(dict(flower_id='FW-%02d' % i, variety=v, flower_class=cl, stems_per_bunch=spb, cost_spring=R2(base * sv[0]), cost_summer=R2(base * sv[1]), cost_autumn=R2(base * sv[2]),
                        cost_winter=R2(base * sv[3]), base_cost=base, supplier=sup, shrink_factor=shr, _shape=shape))
FL = {f['variety']: f for f in flowers}
# hard goods: item, unit, cost per unit, par level, on hand now, reorder quantity, share of use per month at the demo scale
_HG = [('Ribbon', 'cut', 0.90, 150, 96, 200), ('Floral tape', 'use', 0.15, 400, 310, 500), ('Bouquet wrap', 'sheet', 1.10, 250, 140, 300), ('Glass vase', 'each', 4.20, 80, 52, 60),
       ('Ceramic pot', 'each', 6.50, 40, 18, 40), ('Gift box', 'each', 4.80, 60, 34, 60), ('Wreath frame', 'each', 9.00, 12, 5, 12), ('Foam-free mechanic', 'each', 2.60, 60, 37, 60),
       ('Mechanic cage', 'each', 1.80, 50, 44, 50), ('Pins and wire', 'use', 0.30, 500, 420, 600), ('Water tube', 'each', 0.20, 600, 380, 600), ('Card and holder', 'each', 0.45, 400, 260, 400),
       ('Sash ribbon silk', 'each', 3.00, 40, 28, 40), ('Basket', 'each', 7.00, 24, 9, 24), ('Cellophane sleeve', 'each', 0.35, 500, 330, 500), ('Moss', 'bag', 0.90, 40, 21, 40)]
supplies = [dict(supply_id='SP-%02d' % i, item=a, unit=u, cost=c, par_level=p, on_hand=oh, reorder_qty=rq, supplier='Supplies wholesaler') for i, (a, u, c, p, oh, rq) in enumerate(_HG, 1)]
HG = {s['item']: s for s in supplies}
# recipes: name, kind, labour minutes, items (item:qty)
_RC = [('Valentine dozen roses', 'Holiday', 20, 'Long-stem rose:12,Eucalyptus:3,Bouquet wrap:1,Ribbon:1,Card and holder:1'),
       ('Valentine half dozen', 'Holiday', 12, 'Long-stem rose:6,Eucalyptus:2,Bouquet wrap:1,Ribbon:1,Card and holder:1'),
       ("Mother's Day box", 'Holiday', 30, 'Spray rose:5,Lisianthus:4,Alstroemeria:4,Eucalyptus:3,Gift box:1,Foam-free mechanic:1,Card and holder:1'),
       ("Mother's Day posy", 'Holiday', 18, 'Ranunculus:4,Spray rose:3,Waxflower:3,Fern:2,Cellophane sleeve:1,Ribbon:1,Card and holder:1'),
       ('Festive door wreath', 'Holiday', 55, 'Pittosporum:12,Eucalyptus:8,Spray carnation:6,Wreath frame:1,Pins and wire:8,Ribbon:1'),
       ('Festive table arrangement', 'Holiday', 35, 'Lily:3,Spray rose:6,Pittosporum:8,Waxflower:4,Ceramic pot:1,Foam-free mechanic:1,Card and holder:1'),
       ('Hand-tied small', 'Retail', 15, 'Spray rose:4,Alstroemeria:3,Eucalyptus:3,Bouquet wrap:1,Ribbon:1,Water tube:1'),
       ('Hand-tied medium', 'Retail', 22, 'Garden rose:3,Spray rose:4,Lisianthus:4,Alstroemeria:4,Eucalyptus:4,Bouquet wrap:1,Ribbon:1,Water tube:1'),
       ('Hand-tied large', 'Retail', 32, 'Garden rose:5,Lily:3,Lisianthus:5,Spray rose:6,Alstroemeria:3,Stock:3,Ruscus:5,Eucalyptus:5,Bouquet wrap:1,Ribbon:1,Water tube:1'),
       ('Seasonal posy', 'Retail', 12, 'Tulip:4,Sweet pea:3,Spray carnation:3,Gypsophila:2,Fern:2,Cellophane sleeve:1,Ribbon:1'),
       ('Vase arrangement', 'Retail', 30, 'Garden rose:3,Lily:2,Anemone:4,Snapdragon:4,Eucalyptus:4,Glass vase:1,Foam-free mechanic:1,Card and holder:1'),
       ('Birthday bouquet', 'Retail', 20, 'Sunflower:3,Alstroemeria:4,Zinnia:3,Spray rose:3,Eucalyptus:3,Bouquet wrap:1,Ribbon:1,Card and holder:1'),
       ('Get-well jar', 'Retail', 20, 'Spray carnation:4,Alstroemeria:3,Freesia:3,Fern:2,Glass vase:1,Card and holder:1'),
       ('Sympathy wreath', 'Sympathy', 90, 'Chrysanthemum:10,Carnation:15,Lily:5,Statice:6,Ruscus:8,Wreath frame:1,Moss:2,Pins and wire:10,Ribbon:2'),
       ('Casket spray', 'Sympathy', 120, 'Lily:8,Garden rose:8,Chrysanthemum:10,Carnation:15,Statice:8,Ruscus:10,Foam-free mechanic:2,Mechanic cage:2,Ribbon:2'),
       ('Sympathy sheaf', 'Sympathy', 35, 'Lily:5,Chrysanthemum:5,Carnation:8,Ruscus:5,Bouquet wrap:2,Ribbon:1,Card and holder:1'),
       ('Sympathy basket', 'Sympathy', 50, 'Lily:3,Carnation:10,Chrysanthemum:6,Fern:5,Basket:1,Foam-free mechanic:1,Moss:1,Card and holder:1'),
       ('Sympathy posy', 'Sympathy', 25, 'Spray rose:5,Carnation:6,Gypsophila:3,Ruscus:3,Cellophane sleeve:1,Ribbon:1,Card and holder:1'),
       ('Bridal bouquet', 'Wedding', 60, 'Garden rose:6,Peony:3,Ranunculus:6,Spray rose:6,Eucalyptus:5,Ruscus:3,Sash ribbon silk:1,Floral tape:2,Pins and wire:2'),
       ('Bridesmaid bouquet', 'Wedding', 35, 'Spray rose:5,Ranunculus:4,Lisianthus:3,Eucalyptus:3,Ribbon:1,Floral tape:1,Pins and wire:1'),
       ('Boutonniere', 'Wedding', 15, 'Spray rose:1,Ranunculus:1,Ruscus:1,Pins and wire:2,Ribbon:1'),
       ('Corsage', 'Wedding', 20, 'Spray rose:2,Waxflower:2,Ribbon:1,Pins and wire:2'),
       ('Flower crown', 'Wedding', 40, 'Spray rose:4,Gypsophila:5,Waxflower:3,Ivy trail:3,Pins and wire:3,Floral tape:2'),
       ('Ceremony arch', 'Wedding', 240, 'Garden rose:12,Hydrangea:8,Delphinium:15,Eucalyptus:20,Ruscus:15,Ivy trail:10,Lily:6,Mechanic cage:3,Pins and wire:6'),
       ('Aisle pedestal', 'Wedding', 60, 'Hydrangea:4,Delphinium:6,Garden rose:4,Eucalyptus:8,Ruscus:6,Foam-free mechanic:1,Mechanic cage:1'),
       ('Table centrepiece', 'Wedding', 30, 'Garden rose:3,Ranunculus:4,Lisianthus:3,Eucalyptus:4,Glass vase:1,Foam-free mechanic:1'),
       ('Low table arrangement', 'Wedding', 25, 'Spray rose:4,Ranunculus:3,Scabiosa:3,Olive branch:3,Ceramic pot:1,Foam-free mechanic:1'),
       ('Cake flowers', 'Wedding', 20, 'Spray rose:3,Waxflower:3,Gypsophila:3,Pins and wire:3,Floral tape:1'),
       ('Welcome sign flowers', 'Wedding', 35, 'Garden rose:3,Dahlia:3,Eucalyptus:6,Ruscus:4,Ivy trail:4,Mechanic cage:1,Pins and wire:3'),
       ('Party table arrangement', 'Event', 25, 'Alstroemeria:5,Sunflower:3,Zinnia:3,Eucalyptus:4,Glass vase:1,Foam-free mechanic:1'),
       ('Buffet arrangement', 'Event', 50, 'Hydrangea:3,Lily:4,Delphinium:3,Gladiolus:3,Eucalyptus:8,Ruscus:6,Ceramic pot:1,Mechanic cage:1'),
       ('Hanging installation', 'Event', 300, 'Delphinium:30,Gypsophila:25,Garden rose:15,Eucalyptus:40,Ivy trail:30,Olive branch:20,Mechanic cage:6,Pins and wire:15'),
       ('Office weekly vase', 'Corporate', 30, 'Lisianthus:5,Alstroemeria:5,Chrysanthemum:3,Eucalyptus:4,Glass vase:1,Foam-free mechanic:1'),
       ('Reception arrangement', 'Corporate', 55, 'Orchid stem:4,Hydrangea:3,Delphinium:6,Garden rose:4,Eucalyptus:8,Ruscus:6,Ceramic pot:1,Mechanic cage:1'),
       ('Boardroom table', 'Corporate', 35, 'Spray rose:6,Lisianthus:5,Gypsophila:3,Olive branch:4,Glass vase:1,Foam-free mechanic:1')]
recipes = []; recipe_lines = []
_RCI = {}
for i, (nm, kind, mins, items) in enumerate(_RC, 1):
    rid = 'RC-%02d' % i
    ls = []
    for it in items.split(','):
        a, q = it.split(':'); ls.append((a, int(q)))
        cls = FL[a]['flower_class'] if a in FL else 'Hard goods'
        recipe_lines.append(dict(line_id='RL-%03d' % (len(recipe_lines) + 1), recipe_id=rid, recipe=nm, item=a, item_class=cls, qty=int(q)))
    _RCI[nm] = dict(recipe_id=rid, kind=kind, minutes=mins, lines=ls)


def _markup(cls): return MARKUP_FLOWERS if cls in ('Focal', 'Filler', 'Line') else MARKUP_GREENS if cls == 'Greenery' else MARKUP_HARD
def _base_cost(item): return FL[item]['base_cost'] if item in FL else HG[item]['cost']
def _class(item): return FL[item]['flower_class'] if item in FL else 'Hard goods'


def recipe_cost_list(name):
    """goods cost of one recipe at the list (base) stem costs"""
    return R2(sum(q * _base_cost(a) for a, q in _RCI[name]['lines']))


def recipe_price(name):
    """list price of one recipe: stems x base cost x markup per class + labour charge"""
    r = _RCI[name]
    return R2(sum(q * _base_cost(a) * _markup(_class(a)) for a, q in r['lines']) + r['minutes'] / 60.0 * LABOUR_CHARGE_HOUR)


for _nm, _r in _RCI.items():
    recipes.append(dict(recipe_id=_r['recipe_id'], recipe=_nm, kind=_r['kind'], labour_minutes=_r['minutes'], goods_cost=recipe_cost_list(_nm), list_price=recipe_price(_nm),
                        stems=sum(q for a, q in _r['lines'] if a in FL)))
RC = {r['recipe']: r for r in recipes}
RECIPES = [r['recipe'] for r in recipes]
PRODUCTS = [r['recipe'] for r in recipes if r['kind'] in ORDER_KINDS]      # the 21 shop products (orders)
EVENT_RECIPES = [r['recipe'] for r in recipes if r['kind'] in ('Wedding', 'Event')]   # the 14 event recipes (proposal lines)
# delivery zones: id, name, fee, minutes per stop (drive and hand-over), km for the round trip, share of orders
_ZN = [('ZN-1', 'Zone 1 Central', 9.0, 12, 4, .40), ('ZN-2', 'Zone 2 Inner suburbs', 14.0, 18, 9, .33), ('ZN-3', 'Zone 3 Outer suburbs', 22.0, 28, 18, .18),
       ('ZN-4', 'Zone 4 Valley', 15.0, 58, 46, .09)]
zones = [dict(zone_id=a, zone=b, fee=f, minutes=m, km=k, share=s, cost=R2(m / 60.0 * DRIVER_RATE + k * VEHICLE_KM)) for a, b, f, m, k, s in _ZN]
ZN = {z['zone']: z for z in zones}
ZONES = [z['zone'] for z in zones]
# rental items: id, item, units owned, purchase price each, rent price per booking, damage fee, bookings a year at the demo scale
_RN = [('RT-01', 'Glass cylinder vase', 80, 5.5, 2.0, 5.5, 40), ('RT-02', 'Wooden ceremony arch', 2, 260.0, 120.0, 260.0, 14), ('RT-03', 'Metal hoop arch', 2, 190.0, 95.0, 190.0, 12),
       ('RT-04', 'Pedestal stand', 10, 48.0, 22.0, 48.0, 20), ('RT-05', 'Aisle stand', 12, 35.0, 16.0, 35.0, 16), ('RT-06', 'Lantern', 30, 12.0, 5.0, 12.0, 24),
       ('RT-07', 'Cake stand', 4, 38.0, 18.0, 38.0, 10), ('RT-08', 'Bud vase set', 50, 3.2, 1.2, 3.2, 30), ('RT-09', 'Ceramic urn', 6, 42.0, 20.0, 42.0, 10),
       ('RT-10', 'Hanging frame', 3, 150.0, 70.0, 150.0, 6), ('RT-11', 'Easel for signs', 4, 28.0, 12.0, 28.0, 12), ('RT-12', 'Candle holder set', 24, 6.5, 2.5, 6.5, 26)]
rental_items = [dict(item_id=a, item=b, units=u, purchase_price=p, rent_price=r, damage_fee=d, bookings_year=y) for a, b, u, p, r, d, y in _RN]
RI = {r['item']: r for r in rental_items}
RENTAL_ITEMS = [r['item'] for r in rental_items]
# venues, planners and other relationships that send work
_VN = [('Orchard Barn Venue', 'Venue', 'Old Mill Road'), ('Glasshouse Hall', 'Venue', 'Riverside'), ('Old Mill Estate', 'Venue', 'Millbrook'), ('Harbour Rooms', 'Venue', 'Harbour'),
       ('Fernwood Manor', 'Venue', 'Hillcrest'), ('Lakeview Pavilion', 'Venue', 'Lakeside'), ('Stone Cellar Venue', 'Venue', 'Old Town'), ('Rosewater Events', 'Planner', 'Riverside'),
       ('Bright Day Planning', 'Planner', 'Westfield'), ('Silverleaf Planning', 'Planner', 'Northgate'), ('Lantern Photography', 'Photographer', 'Old Town'), ('Meadow Gardens Venue', 'Venue', 'Parkside')]
venues = [dict(venue_id='VN-%02d' % i, name=n, kind=k, area=a, contact=fake_phone(500 + i), phone=fake_phone(500 + i)) for i, (n, k, a) in enumerate(_VN, 1)]
VENUE_NAMES = [v['name'] for v in venues]
AREAS = ['Old Town', 'Riverside', 'Harbour', 'Northgate', 'Westfield', 'Parkside', 'Eastgate', 'Millbrook', 'Hillcrest', 'Lakeside', 'Orchard Hill', 'Southbank']
_AZ = {'Old Town': 0, 'Riverside': 0, 'Harbour': 0, 'Northgate': 1, 'Westfield': 1, 'Parkside': 1, 'Eastgate': 1, 'Millbrook': 2, 'Hillcrest': 2, 'Lakeside': 2, 'Orchard Hill': 3, 'Southbank': 3}
suppliers = [dict(supplier=s, kind=k, order_days=od, lead_days=ld, minimum_order=mo, delivery_fee=df, price_factor=pf)
             for s, k, od, ld, mo, df, pf in [('Wholesaler A', 'Flowers', 'Monday and Thursday', 1, 150.0, 12.0, 1.00), ('Wholesaler B', 'Flowers', 'Monday and Thursday', 1, 200.0, 18.0, 1.06),
                                               ('Local grower', 'Flowers', 'Monday and Thursday', 1, 80.0, 0.0, 0.90), ('Supplies wholesaler', 'Hard goods', 'Monday', 3, 250.0, 15.0, 1.00)]]
SUP = {s['supplier']: s for s in suppliers}

# ------------------------------------------------------------------ calendar, costs and helpers
_CACHE = {}
def _raw(key, fn):
    if key not in _CACHE: _CACHE[key] = fn()
    return _CACHE[key]
def _cached(key, fn): return [dict(r) for r in _raw(key, fn)]
def _thin(rows, n):
    if not n or n >= len(rows): return rows
    k = min(max(3, n // 5), n)
    if k >= n: return rows[-n:]
    recent = rows[-k:]; rest = rows[:-k]; m = n - k; step = len(rest) / float(m)
    return [rest[int(i * step)] for i in range(m)] + recent
def _pub(rows): return [{k: v for k, v in x.items() if not k.startswith('_')} for x in rows]
def _wchoice(r, vals, ws):
    x, acc = r.random() * sum(ws), 0
    for v, w in zip(vals, ws):
        acc += w
        if x <= acc: return v
    return vals[-1]


def mothers_day(y):
    d = D(y, 5, 1)
    while d.weekday() != 6: d += day(1)
    return d + day(7)


def easter(y):
    a = y % 19; b = y // 100; c = y % 100; d_ = b // 4; e = b % 4; f = (b + 8) // 25; g = (b - f + 1) // 3; h = (19 * a + b - d_ - g + 15) % 30
    i = c // 4; k = c % 4; l = (32 + 2 * e + 2 * i - h - k) % 7; m = (a + 11 * h + 22 * l) // 451
    mo = (h + l - 7 * m + 114) // 31; da = (h + l - 7 * m + 114) % 31 + 1
    return D(y, mo, da)


def holiday_of(d):
    y = d.year
    if D(y, 2, 7) <= d <= D(y, 2, 14): return HOLIDAYS[0]
    md = mothers_day(y)
    if md - day(4) <= d <= md: return HOLIDAYS[1]
    e = easter(y)
    if e - day(3) <= d <= e: return HOLIDAYS[2]
    if D(y, 12, 15) <= d <= D(y, 12, 24): return HOLIDAYS[3]
    return ''


def holiday_window(name, y):
    """first and last day of a holiday window in year y"""
    if name == HOLIDAYS[0]: return D(y, 2, 7), D(y, 2, 14)
    if name == HOLIDAYS[1]: return mothers_day(y) - day(4), mothers_day(y)
    if name == HOLIDAYS[2]: return easter(y) - day(3), easter(y)
    return D(y, 12, 15), D(y, 12, 24)


def _day_mult(d):
    h = holiday_of(d); y = d.year
    if h == HOLIDAYS[0]: return {14: 6.5, 13: 4.0, 12: 3.0, 11: 2.2, 10: 1.8, 9: 1.5, 8: 1.4, 7: 1.3}[d.day]
    if h == HOLIDAYS[1]: return {0: 2.2, 1: 4.5, 2: 5.2, 3: 3.4, 4: 2.5}[(mothers_day(y) - d).days]
    if h == HOLIDAYS[2]: return 1.5
    if h == HOLIDAYS[3]: return [1.4, 1.5, 1.7, 2.0, 2.3, 2.7, 3.2, 3.4, 3.0, 1.8][d.day - 15]
    if d.month == 12 and d.day >= 26: return 0.7
    if d.month == 1 and d.day <= 10: return 0.6
    return 1.0


def _season(d): return 0 if d.month in (3, 4, 5) else 1 if d.month in (6, 7, 8) else 2 if d.month in (9, 10, 11) else 3
def _infl(d):
    n = (TODAY - d).days
    return 0.94 if n > 365 else 1.0 if n > PRICE_RISE_DAYS else 1.0 + PRICE_RISE


_SC = {}
def stem_cost(item, d):
    """actual wholesale cost of one stem or hard-goods unit on a date: base x season x holiday surge x price index"""
    k = (item, d)
    if k in _SC: return _SC[k]
    if item in FL:
        f = FL[item]; c = f['base_cost'] * _SEAS[f['_shape']][_season(d)]; h = holiday_of(d)
        if h == HOLIDAYS[0]:
            c *= 2.0 if item in ('Long-stem rose', 'Garden rose') and d.day >= 11 else 1.6 if item in ('Long-stem rose', 'Garden rose') else 1.25 if item == 'Spray rose' else 1.1
        elif h == HOLIDAYS[1]: c *= 1.18
        elif h == HOLIDAYS[3]: c *= 1.25
        v = c * _infl(d) * SUP[f['supplier']]['price_factor']
    else:
        v = HG[item]['cost'] * (1 + (_infl(d) - 1) * 0.5)
    _SC[k] = v
    return v


_GC = {}
def goods_cost(recipe, d):
    k = (recipe, d)
    if k not in _GC: _GC[k] = sum(q * stem_cost(a, d) for a, q in _RCI[recipe]['lines'])
    return _GC[k]


def price_index(d): return 1.03 if to_date(d) >= D(TODAY.year, 1, 1) else 1.0


def _month_list(a, b):
    out = []; m = _ms(a)
    while m <= b: out.append(m); m = add_months(m, 1)
    return out


# ------------------------------------------------------------------ names
_FIRST = ['Amara', 'Jonas', 'Mei', 'Rafael', 'Ingrid', 'Tariq', 'Sofia', 'Kwame', 'Yuki', 'Elena', 'Omar', 'Nia', 'Lars', 'Priya', 'Mateo', 'Chloe', 'Ahmed', 'Zofia', 'Diego', 'Hana', 'Callum',
          'Fatima', 'Anders', 'Lucia', 'Kofi', 'Ines', 'Noah', 'Leila', 'Piotr', 'Ayesha', 'Tomas', 'Greta', 'Ravi', 'Camille', 'Dmitri', 'Amina', 'Santiago', 'Freya', 'Hiro', 'Isabela', 'Emeka',
          'Sven', 'Zara', 'Mikael', 'Nadia', 'Oskar', 'Paloma', 'Idris', 'Alma', 'Kenji']
_LAST = ['Okafor', 'Lindqvist', 'Tanaka', 'Rossi', 'Haddad', 'Mensah', 'Novak', 'Silva', 'Kowalski', 'Nguyen', 'Patel', 'Garcia', 'Becker', 'Moreau', 'Eriksen', 'Ali', 'Costa', 'Yilmaz', 'Sato',
         'Fernandez', 'Dubois', 'Adeyemi', 'Petrov', 'Hansen', 'Kim', 'Rahman', 'Murphy', 'Santos', 'Ivanov', 'Bianchi', 'Mwangi', 'Larsen', 'Khan', 'Torres', 'Weber', 'Olsen', 'Chaudhry', 'Popescu',
         'Ferreira', 'Jansen', 'Abara', 'Lopez', 'Wong', 'Reyes', 'Horvat', 'Saleh', 'Berg', 'Mbeki']
_RESERVED = {s['name'] for s in team}


class _Names:
    def __init__(self, tag):
        r = rng('names-' + tag); combos = [(f, l) for f in _FIRST for l in _LAST]; r.shuffle(combos)
        self.c = [x for x in combos if x[0] + ' ' + x[1] not in _RESERVED]; self.i = 0; self.r = r
    def person(self):
        f, l = self.c[self.i]; self.i += 1; return f + ' ' + l
    def couple(self):
        f, l = self.c[self.i]; self.i += 1; g = _FIRST[self.r.randrange(len(_FIRST))]
        while g == f: g = _FIRST[self.r.randrange(len(_FIRST))]
        return '%s & %s %s' % (f, g, l)


CORPORATE = [('Northgate Dental Clinic', 'Northgate'), ('Alder and Finch Law Office', 'Old Town'), ('Riverside Boutique Hotel', 'Millbrook'), ('Summit Fitness Studio', 'Westfield'),
             ('Oakmont Estate Agents', 'Parkside'), ('Meridian Accounting Group', 'Old Town'), ('Greenway Medical Centre', 'Eastgate'), ('Stonebridge Art Gallery', 'Riverside')]
FUNERAL = [('Oak Hill Funeral Home', 'Hillcrest'), ('Willow Lane Funeral Directors', 'Westfield'), ('Eastgate Memorial Services', 'Eastgate'), ('Parkside Funeral Care', 'Parkside'),
           ('Hillcrest Family Funeral Home', 'Northgate')]
# the unpaid account, the undercosted standing order and the money-losing zone of the story
STORY_ACCOUNT = 'Meridian Accounting Group'
STORY_STANDING_ACCOUNT = 'Riverside Boutique Hotel'
STORY_ZONE = 'Zone 4 Valley'

# ------------------------------------------------------------------ world part 1: accounts, retail customers, standing orders, retail orders, account invoices
_BASE_ORDERS = 7.2
_WD = [0.80, 0.85, 0.95, 1.0, 1.3, 1.3, 0.45]
_MF = [0.75, 1.0, 1.0, 1.05, 1.15, 1.1, 0.95, 0.9, 1.0, 1.0, 0.95, 1.2]
_RETAIL_W = {'Hand-tied small': .22, 'Hand-tied medium': .25, 'Hand-tied large': .10, 'Seasonal posy': .15, 'Vase arrangement': .12, 'Birthday bouquet': .10, 'Get-well jar': .06}
_SYMP_W = {'Sympathy wreath': .15, 'Casket spray': .06, 'Sympathy sheaf': .35, 'Sympathy basket': .20, 'Sympathy posy': .24}
_HOL_W = {HOLIDAYS[0]: {'Valentine dozen roses': .45, 'Valentine half dozen': .25, 'Hand-tied small': .10, 'Hand-tied medium': .10, 'Vase arrangement': .10},
          HOLIDAYS[1]: {"Mother's Day box": .30, "Mother's Day posy": .25, 'Hand-tied small': .10, 'Hand-tied medium': .15, 'Hand-tied large': .10, 'Vase arrangement': .10},
          HOLIDAYS[2]: {'Seasonal posy': .30, 'Hand-tied small': .25, 'Hand-tied medium': .25, 'Vase arrangement': .20},
          HOLIDAYS[3]: {'Festive door wreath': .25, 'Festive table arrangement': .30, 'Hand-tied medium': .15, 'Vase arrangement': .15, 'Hand-tied large': .15}}
# standing orders: account, recipe, frequency, weekday (0=Monday), started days ago, price (None = 93% of list), status, days since it stopped
_SO = [('Northgate Dental Clinic', 'Office weekly vase', 'Weekly', 0, 690, None, 'Active', 0), ('Alder and Finch Law Office', 'Reception arrangement', 'Weekly', 1, 610, None, 'Active', 0),
       (STORY_STANDING_ACCOUNT, 'Reception arrangement', 'Weekly', 3, 700, 150.0, 'Active', 0), ('Summit Fitness Studio', 'Office weekly vase', 'Fortnightly', 2, 420, None, 'Paused', 35),
       ('Oakmont Estate Agents', 'Boardroom table', 'Fortnightly', 4, 560, None, 'Ended', 120), (STORY_ACCOUNT, 'Office weekly vase', 'Weekly', 0, 650, None, 'Active', 0),
       (STORY_ACCOUNT, 'Boardroom table', 'Fortnightly', 3, 500, None, 'Active', 0), ('Greenway Medical Centre', 'Reception arrangement', 'Weekly', 2, 480, None, 'Active', 0),
       ('Greenway Medical Centre', 'Office weekly vase', 'Weekly', 4, 380, None, 'Active', 0), ('Stonebridge Art Gallery', 'Reception arrangement', 'Monthly', 1, 340, None, 'Active', 0)]
ORDER_PAY = ['Card', 'Cash', 'Online payment', 'On account']


def _zone_of_area(a): return ZONES[_AZ[a]]


def _world1():
    r = rng('w1'); nm = _Names('a'); W = {}
    accts = []
    for i, (n, a) in enumerate(CORPORATE):
        accts.append(dict(name=n, client_type='Corporate account', area=a, zone=_zone_of_area(a), terms=INVOICE_DAYS, source='Walk-in', first=None))
    for i, (n, a) in enumerate(FUNERAL):
        accts.append(dict(name=n, client_type='Sympathy account', area=a, zone=_zone_of_area(a), terms=INVOICE_DAYS, source='Online directory', first=None))
    W['accounts'] = accts; AC = {a['name']: a for a in accts}
    pool = []
    for i in range(280):
        a = _wchoice(r, AREAS, [10, 9, 8, 8, 8, 7, 7, 7, 6, 6, 5, 5])
        pool.append(dict(name=nm.person(), client_type='Retail customer', area=a, zone=_zone_of_area(a), terms=0, source='Walk-in' if r.random() < .4 else 'Web search', first=None))
    W['retail_pool'] = pool; W['_nm'] = nm
    orders = []
    end = TODAY + day(45)
    d = HISTORY_START
    while d <= end:
        hol = holiday_of(d); mult = _day_mult(d)
        n = _BASE_ORDERS * _WD[d.weekday()] * _MF[d.month - 1] * mult * (0.85 + 0.3 * r.random())
        n = int(n) + (1 if r.random() < n - int(n) else 0)
        far = (d - TODAY).days
        for _ in range(n):
            # when the order was placed: same day mostly, pre-orders before a holiday peak
            if hol and hol != HOLIDAYS[2] and r.random() < 0.30: lead = r.randint(3, 40 if hol == HOLIDAYS[3] else 21); pre = True
            else:
                u = r.random(); lead = 0 if u < .72 else r.randint(1, 3) if u < .94 else r.randint(4, 14); pre = False
            placed = d - day(lead)
            if placed > TODAY or placed < HISTORY_START: continue
            ws = [.25, .20, .52, .03] if hol else [.37, .22, .31, .10]
            typ = _wchoice(r, ['Walk-in', 'Phone', 'Online', 'Sympathy'], ws)
            if pre and typ == 'Walk-in': typ = 'Online'
            if typ == 'Sympathy': w = _SYMP_W
            elif hol: w = _HOL_W[hol]
            else: w = _RETAIL_W
            rec = _wchoice(r, list(w), list(w.values()))
            size = 1.0 if rec == 'Casket spray' else _wchoice(r, [0.8, 1.0, 1.25, 1.6], [.15, .58, .19, .08])
            acct = None
            if typ == 'Sympathy' and r.random() < .6: acct = FUNERAL[r.randrange(len(FUNERAL))][0]
            if acct: cl = AC[acct]
            elif typ == 'Walk-in' and r.random() > .38: cl = None
            else: cl = pool[min(len(pool) - 1, int(len(pool) * r.random() ** 1.7))]
            deliv = acct is not None or r.random() < {'Walk-in': .06, 'Phone': .62, 'Online': .88, 'Sympathy': .9}[typ]
            if cl is not None: zone = cl['zone'] if deliv else ''
            else: zone = _wchoice(r, ZONES, [z['share'] for z in zones]) if deliv else ''
            if cl is not None and cl['first'] is None or cl is not None and d < cl['first']: cl['first'] = d
            price = int(round(RC[rec]['list_price'] * size * price_index(d)))
            fee = 0.0
            if zone and price < FREE_DELIVERY_OVER: fee = ZN[zone]['fee']
            paym = 'On account' if acct else {'Walk-in': _wchoice(r, ['Card', 'Cash'], [.65, .35]), 'Phone': 'Card', 'Online': 'Online payment', 'Sympathy': 'Card'}[typ]
            orders.append(dict(date=placed, needed_on=d, order_type=typ, client=cl, recipe=rec, size=size, price=price, goods=goods_cost(rec, d) * size, zone=zone, delivery_fee=fee,
                               pay_method=paym, preorder=pre, labour_minutes=int(round(RC[rec]['labour_minutes'] * (0.6 + 0.4 * size)))))
        d += day(1)
    # standing orders
    sos = []
    for i, (acct, rec, fq, wd, started, price, status, stopped) in enumerate(_SO, 1):
        a = AC[acct]; list_p = RC[rec]['list_price']
        p = price if price else float(int(round(list_p * 0.93)))
        start = TODAY - day(started); stop = TODAY - day(stopped) if status != 'Active' else None
        d = start
        while d.weekday() != wd: d += day(1)
        step = 7 if fq == 'Weekly' else 14 if fq == 'Fortnightly' else 28; first = d; last = None
        while d <= TODAY + day(7):
            if stop and d > stop: break
            placed = d - day(2)
            if placed <= TODAY:
                orders.append(dict(date=placed, needed_on=d, order_type='Standing order', client=a, recipe=rec, size=1.0, price=int(p), goods=goods_cost(rec, d), zone=a['zone'], delivery_fee=ZN[a['zone']]['fee'],
                                   pay_method='On account', preorder=False, labour_minutes=RC[rec]['labour_minutes'], _so='SO-%02d' % i))
                if a['first'] is None or d < a['first']: a['first'] = d
            if d <= TODAY: last = d
            d += day(step)
        nxt = d if status == 'Active' else None
        sos.append(dict(standing_id='SO-%02d' % i, client=acct, zone=a['zone'], recipe=rec, frequency=fq, weekday=WEEKDAYS[wd], started_on=iso(first), price=float(p), status=status,
                        next_date=iso(nxt) if nxt else '', last_date=iso(last) if last else '', list_price=list_p))
    W['standing'] = sos
    orders.sort(key=lambda o: (o['needed_on'], o['date']))
    for k, o in enumerate(orders, 1):
        o['order_id'] = 'OR-%05d' % k
    W['orders'] = orders
    # account invoices: one per account per month, issued on the 1st of the next month
    inv = []
    by = {}
    for o in orders:
        if o['client'] is not None and o['client']['terms'] and o['needed_on'] <= TODAY:
            by.setdefault((o['client']['name'], _ms(o['needed_on'])), []).append(o)
    keys = sorted(by, key=lambda k: (add_months(k[1], 1), k[0]))
    for (acct, m), os_ in [(k, by[k]) for k in keys]:
        issued = add_months(m, 1)
        if issued > TODAY: continue
        due = issued + day(INVOICE_DAYS); amt = float(sum(o['price'] + o['delivery_fee'] for o in os_))
        story = acct == STORY_ACCOUNT and m >= month_start(4)
        paid_on = ''; paid = 0.0
        if not story:
            p = due + day(max(-8, min(18, int(r.gauss(3, 6)))))
            if p <= TODAY: paid_on = iso(p); paid = amt
            if paid_on == '' and due < TODAY - day(30): paid_on = iso(due + day(9)); paid = amt
            if paid_on and r.random() < .15 and due >= TODAY - day(30): paid = R2(amt * .6)
        else:
            if m < month_start(4): pass
        status = 'Paid' if paid >= amt - .01 else 'Part paid' if paid > 0 else 'Unpaid'
        inv.append(dict(client=acct, month=m, issued_on=issued, due_date=due, amount=amt, paid_amount=paid, paid_on=paid_on, status=status, orders=len(os_), _story=story))
    for k, x in enumerate(inv, 1):
        x['invoice_id'] = 'IN-%04d' % k
    W['invoices'] = inv
    return W


def _W1(): return _raw('w1', _world1)

# ------------------------------------------------------------------ world part 2: enquiries, proposals, events, payments, rentals
_EV_W = [2, 2, 3, 5, 8, 10, 10, 10, 9, 7, 3, 2]
_ENQ_SEAS = [1.3, 1.4, 1.2, 1.0, 0.9, 0.8, 0.7, 0.7, 1.0, 1.2, 1.0, 0.8]
_SRC_BOOKED = [.12, .24, .12, .16, .14, .06, .08, .08]
_SRC_LOST = [.05, .12, .08, .22, .25, .08, .06, .14]
_ZONE_CHARGE = {ZONES[0]: 120.0, ZONES[1]: 150.0, ZONES[2]: 220.0, ZONES[3]: 300.0}
_PC = {}


def plan_goods(recipe, d):
    """planned goods cost of a recipe in a quote: base cost x season shape of the event date (no price rise, no holiday surge)"""
    k = (recipe, _season(d))
    if k not in _PC:
        s = 0.0
        for a, q in _RCI[recipe]['lines']:
            s += q * (FL[a]['base_cost'] * _SEAS[FL[a]['_shape']][_season(d)] if a in FL else HG[a]['cost'])
        _PC[k] = s
    return _PC[k]


def _event_lines(r, etype, guests):
    """list of (section, recipe, qty) for one proposal"""
    L = []
    tables = max(3, guests // 9)
    if etype == 'Wedding':
        L.append((SECTIONS[0], 'Bridal bouquet', 1)); L.append((SECTIONS[0], 'Bridesmaid bouquet', r.randint(2, 5))); L.append((SECTIONS[0], 'Boutonniere', r.randint(3, 8)))
        L.append((SECTIONS[0], 'Corsage', r.randint(2, 4)))
        if r.random() < .4: L.append((SECTIONS[0], 'Flower crown', r.randint(1, 2)))
        if r.random() < .55: L.append((SECTIONS[1], 'Ceremony arch', 1))
        if r.random() < .6: L.append((SECTIONS[1], 'Aisle pedestal', r.randint(2, 4)))
        if r.random() < .5: L.append((SECTIONS[1], 'Welcome sign flowers', 1))
        a = int(tables * .6); L.append((SECTIONS[2], 'Table centrepiece', a)); L.append((SECTIONS[2], 'Low table arrangement', tables - a))
        if r.random() < .7: L.append((SECTIONS[2], 'Cake flowers', 1))
    elif etype == 'Corporate event':
        L.append((SECTIONS[2], 'Reception arrangement', r.randint(2, 6))); L.append((SECTIONS[2], 'Buffet arrangement', r.randint(1, 3))); L.append((SECTIONS[2], 'Party table arrangement', max(4, guests // 10)))
        if r.random() < .35: L.append((SECTIONS[3], 'Hanging installation', 1))
    elif etype == 'Party':
        L.append((SECTIONS[2], 'Party table arrangement', max(3, guests // 8))); L.append((SECTIONS[2], 'Buffet arrangement', r.randint(1, 2)))
        if r.random() < .5: L.append((SECTIONS[2], 'Cake flowers', 1))
    elif etype == 'Memorial service':
        L.append((SECTIONS[1], 'Sympathy wreath', r.randint(1, 2))); L.append((SECTIONS[1], 'Sympathy sheaf', r.randint(2, 6))); L.append((SECTIONS[1], 'Sympathy basket', r.randint(2, 3)))
        if r.random() < .5: L.append((SECTIONS[1], 'Casket spray', 1))
    else:
        L.append((SECTIONS[3], 'Hanging installation', r.randint(1, 2))); L.append((SECTIONS[3], 'Ceremony arch', 1)); L.append((SECTIONS[3], 'Reception arrangement', r.randint(2, 4)))
    return [x for x in L if x[2] > 0]


def _event_money(lines, event_date, disc, zone):
    sub = sum(RC[rec]['list_price'] * q for _, rec, q in lines)
    delivery = _ZONE_CHARGE[zone]; hrs_set = 1.5 + sum(q * RC[rec]['labour_minutes'] for _, rec, q in lines) / 60.0 * 0.12
    setup = float(int(round(hrs_set * LABOUR_CHARGE_HOUR / 5.0) * 5))
    price = float(int(round(sub * (1 - disc) + delivery + setup)))
    goods = sum(plan_goods(rec, event_date) * q for _, rec, q in lines)
    hours = sum(q * RC[rec]['labour_minutes'] for _, rec, q in lines) / 60.0
    return dict(subtotal=R2(sub), delivery_charge=delivery, setup_charge=setup, price=price, planned_goods=R2(goods), planned_hours=R2(hours), setup_hours=R2(hrs_set))


def _world2():
    W1 = _W1(); r = rng('w2'); nm = W1['_nm']; W = {}
    enq = []; props = []; plines = []
    horizon = HORIZON
    tp = {'Wedding': .64, 'Corporate event': .12, 'Party': .12, 'Memorial service': .04, 'Installation': .08}
    kinds = list(tp); kw = list(tp.values())
    vkind = {'Venue referral': ('Venue',), 'Planner referral': ('Planner', 'Photographer')}

    def pick_venue(src):
        if src in vkind:
            c = [v['name'] for v in venues if v['kind'] in vkind[src]]; return c[r.randrange(len(c))]
        return ''

    def guests_of(et):
        if et == 'Wedding': return int(min(200, max(30, r.gauss(88, 32))))
        if et == 'Corporate event': return r.randint(50, 220)
        if et == 'Party': return r.randint(20, 80)
        if et == 'Memorial service': return r.randint(30, 120)
        return r.randint(40, 160)

    def new_prop(name, et, event_date, e, src, forced=None, booked=False):
        g = guests_of(et)
        lines = _event_lines(r, et, g)
        zone = _wchoice(r, ZONES, [.4, .33, .18, .09])
        disc = 0.0 if r.random() < .55 else r.choice([.03, .05, .05, .08])
        m = _event_money(lines, event_date, disc, zone)
        budget = float(int(round(m['price'] * (r.uniform(.92, 1.3) if booked else r.uniform(.6, 1.05)) / 50.0) * 50))
        return dict(name=name, event_type=et, event_date=event_date, guests=g, source=src, venue=pick_venue(src), zone=zone, discount=disc, lines=lines, budget=budget, e=e, **m)

    # ---- booked events (the 60 a year of the demo business)
    booked = []
    for m in _month_list(_ms(HISTORY_START), horizon):
        w = _EV_W[m.month - 1] / 71.0 * 60
        ahead_m = (m.year - TODAY.year) * 12 + m.month - TODAY.month
        fill = 1.0 if ahead_m <= 1 else {2: .95, 3: .85, 4: .75, 5: .6, 6: .5}.get(ahead_m, .5)
        k = int(w * fill + r.random())
        for _ in range(k):
            for _t in range(30):
                d = D(m.year, m.month, r.randint(1, calendar.monthrange(m.year, m.month)[1]))
                if r.random() < {5: .5, 4: .2, 6: .15}.get(d.weekday(), .04): break
            if d <= HISTORY_START + day(14): continue
            booked.append(dict(event_date=d))
    for b in booked:
        et = _wchoice(r, kinds, kw); d = b['event_date']; src = _wchoice(r, ENQUIRY_SOURCES, _SRC_BOOKED)
        name = nm.couple() if et == 'Wedding' else nm.person()
        lead = int(r.triangular(60, 420, 230)) if et == 'Wedding' else r.randint(14, 80) if et != 'Memorial service' else r.randint(5, 12)
        e = d - day(lead)
        if e < HISTORY_START: e = HISTORY_START + day(r.randint(0, 20))
        p = new_prop(name, et, d, e, src, booked=True); p['story'] = ''
        booked_list = booked  # noqa
        b.update(p); b['et'] = et
    # ---- story events (forced dates)
    S = {}
    def forced(tag, name, et, d, booked_ago, disc=None, lines=None, src='Venue referral'):
        e = TODAY - day(booked_ago + 12)
        p = new_prop(name, et, d, e, src, booked=True)
        if lines: p['lines'] = lines
        if disc is not None: p['discount'] = disc
        m = _event_money(p['lines'], d, p['discount'], p['zone']); p.update(m); p['budget'] = float(int(round(m['price'] * 1.05 / 50.0) * 50)); p['story'] = tag; p['event_date'] = d
        p['forced_booked_ago'] = booked_ago
        booked.append(p)
    forced('overdue_balance', nm.couple(), 'Wedding', TODAY + day(9), 200)
    forced('deposit_missing', nm.couple(), 'Wedding', TODAY + day(175), 12)
    forced('low_margin', nm.couple(), 'Wedding', TODAY + day(38), 120, disc=0.32,
           lines=[(SECTIONS[0], 'Bridal bouquet', 1), (SECTIONS[0], 'Bridesmaid bouquet', 5), (SECTIONS[0], 'Boutonniere', 6), (SECTIONS[1], 'Ceremony arch', 1), (SECTIONS[1], 'Aisle pedestal', 4),
                  (SECTIONS[2], 'Table centrepiece', 14), (SECTIONS[2], 'Low table arrangement', 6)])
    forced('arch_out', nm.couple(), 'Wedding', TODAY - day(42), 220,
           lines=[(SECTIONS[0], 'Bridal bouquet', 1), (SECTIONS[0], 'Bridesmaid bouquet', 3), (SECTIONS[0], 'Boutonniere', 5), (SECTIONS[1], 'Ceremony arch', 1), (SECTIONS[2], 'Table centrepiece', 8),
                  (SECTIONS[2], 'Low table arrangement', 4)], disc=0.0)
    booked.sort(key=lambda b: b['event_date'])
    for b in booked:
        d = b['event_date']; e = b['e']
        if 'forced_booked_ago' in b: booked_on = TODAY - day(b['forced_booked_ago']); e = booked_on - day(12); b['e'] = e
        else:
            skip = r.random() < .12 or b['event_type'] == 'Memorial service'
            c = None if skip else e + day(r.randint(2, 9)); sent = (c if c else e) + day(r.randint(1, 6)); booked_on = sent + day(r.randint(2, 16))
            if booked_on > TODAY - day(1):
                shift = (booked_on - (TODAY - day(2))).days + r.randint(0, 40); e -= day(shift)
                if e < HISTORY_START: e = HISTORY_START
                c = None if skip else e + day(r.randint(2, 9)); sent = (c if c else e) + day(r.randint(1, 6)); booked_on = min(sent + day(r.randint(2, 16)), TODAY - day(2))
            if d - booked_on < day(10): booked_on = max(sent, d - day(10)) if d - day(10) <= TODAY else booked_on
            b['e'] = e
        b['consult'] = c if 'forced_booked_ago' not in b else e + day(5)
        b['sent_on'] = (b['consult'] if b['consult'] else e) + day(r.randint(1, 5)) if 'forced_booked_ago' in b else sent
        b['booked_on'] = booked_on if 'forced_booked_ago' in b else booked_on
        if b['booked_on'] < b['sent_on']: b['sent_on'] = b['booked_on'] - day(2)
        b['status'] = 'Completed' if d < TODAY else 'Booked'
        b['revisions'] = _wchoice(r, [0, 1, 2, 3, 4], [.2, .32, .28, .14, .06]); b['cancelled_on'] = ''
        if not b.get('story') and b['status'] == 'Booked' and r.random() < .05 and (d - b['booked_on']).days > 45:
            b['status'] = 'Cancelled'; b['cancelled_on'] = b['booked_on'] + day(r.randint(14, max(15, min(60, (TODAY - b['booked_on']).days))))
            if b['cancelled_on'] > TODAY: b['cancelled_on'] = TODAY - day(3)
        elif not b.get('story') and b['status'] == 'Completed' and r.random() < .03 and d < TODAY - day(30):
            b['status'] = 'Cancelled'; b['cancelled_on'] = d - day(r.randint(30, 60))
            if b['cancelled_on'] < b['booked_on']: b['cancelled_on'] = b['booked_on'] + day(10)
    # ---- lost and open enquiries
    lost = []
    d = HISTORY_START
    while d <= TODAY:
        n = 0.62 * _ENQ_SEAS[d.month - 1] * (0.6 if d.weekday() == 6 else 1.1)
        n = int(n) + (1 if r.random() < n - int(n) else 0)
        for _ in range(n):
            et = _wchoice(r, kinds, kw); src = _wchoice(r, ENQUIRY_SOURCES, _SRC_LOST)
            lead = int(r.triangular(60, 420, 230)) if et == 'Wedding' else r.randint(14, 80) if et != 'Memorial service' else r.randint(5, 14)
            ed = d + day(lead)
            lost.append(dict(e=d, event_type=et, source=src, event_date=ed))
        d += day(1)
    for x in lost:
        et = x['event_type']; e = x['e']; age = (TODAY - e).days
        x['name'] = nm.couple() if et == 'Wedding' else nm.person(); x['story'] = ''
        u = r.random()
        x['consult'] = None; x['sent_on'] = None; x['status'] = 'Lost'; x['lost_reason'] = ''; x['has_prop'] = False
        if age <= 6:
            x['status'] = _wchoice(r, ['New', 'Consultation booked'], [.6, .4]); x['consult'] = e + day(3) if x['status'] == 'Consultation booked' else None
        elif u < .26:
            x['lost_reason'] = 'No reply'
        elif u < .38:
            x['status'] = 'Declined'; x['lost_reason'] = _wchoice(r, ['Below minimum', 'Date taken'], [.5, .5]); x['consult'] = e + day(r.randint(2, 7)) if r.random() < .6 else None
        else:
            x['has_prop'] = True; x['consult'] = e + day(r.randint(2, 9)) if r.random() > .12 else None; x['sent_on'] = (x['consult'] or e) + day(r.randint(1, 6))
            if x['sent_on'] > TODAY: x['sent_on'] = TODAY - day(r.randint(0, 3))
            if age < 40 and r.random() < .55 or (TODAY - x['sent_on']).days < 6:
                x['status'] = 'Sent'
            else:
                x['status'] = 'Lost'; x['lost_reason'] = _wchoice(r, ['Over budget', 'Chose another florist', 'Changed plans', 'Date taken', 'No reply'], [.34, .30, .13, .10, .13])
        if x['has_prop']:
            p = new_prop(x['name'], et, x['event_date'], e, x['source'], booked=False)
            x.update({k: v for k, v in p.items() if k not in ('e', 'name', 'event_type', 'event_date', 'source')})
            x['revisions'] = _wchoice(r, [0, 1, 2], [.5, .35, .15])
            if x['status'] == 'Lost' and x['lost_reason'] == 'Over budget': x['budget'] = float(int(round(x['price'] * r.uniform(.55, .85) / 50.0) * 50))
        else:
            x['guests'] = guests_of(et); x['budget'] = float(int(round(r.uniform(400, 3000) / 50.0) * 50)); x['venue'] = pick_venue(x['source']); x['revisions'] = 0
            x['price'] = 0.0; x['zone'] = ''
        x['booked_on'] = ''; x['cancelled_on'] = ''
    # the open proposals, a draft and a few consultations in the last 30 days are guaranteed by the loop above (age < 40 stays open); make sure a draft exists
    opens = [x for x in lost if x['status'] == 'Sent']
    if opens: opens[-1]['status'] = 'Draft'
    allq = booked + lost
    allq.sort(key=lambda x: (x['e'], x['name']))
    for k, x in enumerate(allq, 1): x['enquiry_id'] = 'EN-%04d' % k
    props = [x for x in allq if x.get('sent_on') or x.get('status') in ('Booked', 'Completed', 'Cancelled')]
    props.sort(key=lambda x: (x['sent_on'], x['name']))
    for k, x in enumerate(props, 1):
        x['proposal_id'] = 'EP-%04d' % k
        if x.get('status') in ('Draft',): x['sent_on'] = ''
    W['enq'] = allq; W['props'] = props
    return W


def _W2(): return _raw('w2', _world2)

# ------------------------------------------------------------------ world part 3: proposal lines, changes, payments, results, rentals, helpers, consultations, reviews
def _world3():
    W2 = _W2(); r = rng('w3'); W = {}
    props = W2['props']; enq = W2['enq']
    lines = []; changes = []; revs = []; pays = []; results = []; rentals = []; helpers = []; consults = []; reviews = []; eday = []
    cust = {}
    for x in props:
        for sec, rec, q in x['lines']:
            lines.append(dict(proposal_id=x['proposal_id'], section=sec, recipe=rec, qty=q, unit_price=RC[rec]['list_price'], line_price=R2(RC[rec]['list_price'] * q), _p=x))
    for k, l in enumerate(lines, 1): l['line_id'] = 'PL-%05d' % k
    # revisions
    for x in props:
        n = x.get('revisions', 0)
        for k in range(1, n + 1):
            base = x['sent_on'] if x.get('sent_on') else x['e']
            dd = base + day(k * r.randint(2, 6))
            if dd > TODAY: dd = TODAY - day(r.randint(0, 2))
            if dd < base: dd = base
            charged = k > 2 and r.random() < .55
            revs.append(dict(proposal_id=x['proposal_id'], client=x['name'], round=k, date=dd, hours=R2(r.uniform(.8, 2.0)), charged=charged, fee=75.0 if charged else 0.0))
    revs.sort(key=lambda z: (z['date'], z['proposal_id']))
    for k, z in enumerate(revs, 1): z['revision_id'] = 'RV-%04d' % k
    # booked events: changes, payments, results
    bk = [x for x in props if x['status'] in ('Booked', 'Completed', 'Cancelled')]
    inv_rows = _W1()['invoices']
    for x in bk:
        price = x['price']; dep = float(int(round(price * DEPOSIT_PCT)))
        x['deposit'] = dep; x['final_due'] = x['event_date'] - day(FINAL_DUE_DAYS)
        if x['final_due'] < x['booked_on'] + day(7): x['final_due'] = x['booked_on'] + day(7)
        x['deposit_due'] = x['booked_on'] + day(7)
        fin = price; ch = None
        if x['status'] == 'Cancelled':
            ch = dict(kind='Cancellation', old=price, new=0.0, kept=dep, date=x['cancelled_on']); fin = dep
        elif not x.get('story') and r.random() < .24 and (x['event_date'] - x['booked_on']).days > 40:
            kd = _wchoice(r, ['Budget cut', 'Guest count change', 'Item added'], [.3, .4, .3])
            f = (1 - r.uniform(.1, .3)) if kd == 'Budget cut' else (1 + r.choice([-1, 1]) * r.uniform(.05, .18)) if kd == 'Guest count change' else 1 + r.uniform(.04, .12)
            dd = x['booked_on'] + day(r.randint(14, max(15, (x['event_date'] - x['booked_on']).days - 10)))
            if dd > TODAY: dd = TODAY - day(2)
            if dd < x['booked_on']: dd = x['booked_on'] + day(1)
            fin = float(int(round(price * f))); ch = dict(kind=kd, old=price, new=fin, kept=0.0, date=dd)
        x['final_amount'] = fin
        if ch: changes.append(dict(proposal_id=x['proposal_id'], client=x['name'], date=ch['date'], kind=ch['kind'], old_amount=ch['old'], new_amount=ch['new'], retainer_kept=ch['kept']))
        # deposit
        pd = x['booked_on'] + day(r.randint(0, 5))
        if x.get('story') == 'deposit_missing': pd = None
        elif pd > TODAY: pd = TODAY - day(1)
        x['deposit_paid'] = pd if pd else ''
        if pd: pays.append(dict(date=pd, client=x['name'], proposal_id=x['proposal_id'], kind='Deposit', amount=dep, method=_wchoice(r, PAYMENT_METHODS, [.45, .5, .05])))
        # final balance
        if x['status'] != 'Cancelled':
            bal = fin - dep
            if x.get('story') == 'overdue_balance' or x.get('story') == 'deposit_missing' and False: fp = None
            else:
                fp = x['final_due'] + day(int(max(-6, min(9, r.gauss(0, 3)))))
                if fp > TODAY: fp = None if x['final_due'] > TODAY - day(3) else TODAY - day(1)
                if fp and fp > x['event_date'] + day(5): fp = x['event_date'] + day(2)
                if fp and fp > TODAY: fp = TODAY - day(1)
            x['final_paid'] = fp if fp else ''
            if x.get('story') == 'deposit_missing': x['final_paid'] = ''
            if fp: pays.append(dict(date=fp, client=x['name'], proposal_id=x['proposal_id'], kind='Final balance', amount=bal, method=_wchoice(r, PAYMENT_METHODS, [.4, .58, .02])))
        else: x['final_paid'] = ''
        cust[x['name']] = x
    # actual results of completed events
    for x in bk:
        if x['status'] != 'Completed': continue
        d = x['event_date']; buy = d - day(2)
        act = sum(goods_cost(rec, buy) * q for _, rec, q in x['lines']) * r.uniform(.97, 1.10)
        hrs = x['planned_hours'] * r.uniform(.9, 1.15)
        n_help = 0 if x['price'] < 1800 else 1 if x['price'] < 3200 else 2 if x['price'] < 4800 else 3
        hh = [r.uniform(4.5, 7.0) for _ in range(n_help)]
        zc = ZN[x['zone']]; trips = 2
        drive_h = R2(zc['minutes'] * 2 * trips / 60.0 + .6); load_h = R2(.8 + x['planned_hours'] * .06); strike_h = R2(x['setup_hours'] * .7)
        log_cost = R2((drive_h + x['setup_hours'] + load_h) * DRIVER_RATE + zc['km'] * trips * VEHICLE_KM)
        waste = R2(act * r.uniform(.02, .07))
        hcost = 0.0
        pers = [FREELANCERS[(len(helpers) + i) % 4] for i in range(n_help)]
        for i in range(n_help):
            st = [s for s in staff if s['name'] == pers[i]][0]
            h = R2(hh[i]); pay = R2(h * st['hourly_rate']); hcost += pay
            helpers.append(dict(date=d, person=pers[i], kind='Wedding helper', proposal_id=x['proposal_id'], event=x['name'], hours=h, rate=st['hourly_rate'], pay=pay))
        rev = x['final_amount']; cost = act + waste + hrs * LABOUR_COST_HOUR + hcost + log_cost
        results.append(dict(proposal_id=x['proposal_id'], client=x['name'], event_type=x['event_type'], event_date=d, final_amount=rev, planned_goods_cost=R2(x['planned_goods']), actual_goods_cost=R2(act),
                            planned_hours=x['planned_hours'], actual_hours=R2(hrs), helper_hours=R2(sum(hh)), helper_cost=R2(hcost), waste_cost=waste, logistics_cost=log_cost, margin=R2((rev - cost) / rev) if rev else 0.0))
        eday.append(dict(proposal_id=x['proposal_id'], client=x['name'], date=d, zone=x['zone'], load_hours=load_h, drive_hours=drive_h, setup_hours=x['setup_hours'], strike_hours=strike_h, helpers=n_help,
                         vehicle_km=zc['km'] * trips, logistics_cost=log_cost, charged=R2(x['delivery_charge'] + x['setup_charge'])))
    # holiday helpers
    for y in (TODAY.year - 2, TODAY.year - 1, TODAY.year):
        for h in HOLIDAYS:
            a, b = holiday_window(h, y); dd = a
            while dd <= b:
                if HISTORY_START <= dd <= TODAY and _day_mult(dd) >= 3.0:
                    for i in range(1 if _day_mult(dd) < 4 else 3):
                        st = staff[5 + (int(dd.day) + i) % 4]; hv = R2(r.uniform(6, 9))
                        helpers.append(dict(date=dd, person=st['name'], kind='Delivery helper' if i == 0 else 'Holiday helper', proposal_id='', event=h, hours=hv, rate=st['hourly_rate'], pay=R2(hv * st['hourly_rate'])))
                dd += day(1)
    helpers.sort(key=lambda z: (z['date'], z['person']))
    for k, z in enumerate(helpers, 1): z['helper_id'] = 'HP-%04d' % k; z['status'] = 'Paid' if z['date'] + day(7) <= TODAY else 'Due'
    # rentals
    for x in bk:
        if x['status'] == 'Cancelled' or x['event_date'] - day(1) > TODAY: continue
        want = []; rec = {rr: q for _, rr, q in x['lines']}
        tables = rec.get('Table centrepiece', 0) + rec.get('Low table arrangement', 0) + rec.get('Party table arrangement', 0)
        if 'Ceremony arch' in rec and (r.random() < .5 or x.get('story') == 'arch_out'): want.append(('Wooden ceremony arch', 1))
        elif 'Ceremony arch' in rec and r.random() < .35: want.append(('Metal hoop arch', 1))
        if 'Aisle pedestal' in rec: want.append(('Pedestal stand', rec['Aisle pedestal'])); want.append(('Aisle stand', min(12, rec['Aisle pedestal'] * 2))) if r.random() < .3 else None
        if x['event_type'] == 'Memorial service' and r.random() < .5: want.append(('Ceramic urn', 2))
        if tables and r.random() < .25: want.append(('Bud vase set', min(50, tables * 4)))
        if tables and r.random() < .6: want.append(('Glass cylinder vase', tables * r.randint(2, 4)))
        if tables and r.random() < .35: want.append(('Lantern', min(30, tables * 2)))
        if tables and r.random() < .25: want.append(('Candle holder set', min(24, tables)))
        if 'Cake flowers' in rec and r.random() < .4: want.append(('Cake stand', 1))
        if 'Welcome sign flowers' in rec and r.random() < .8: want.append(('Easel for signs', 1))
        if 'Hanging installation' in rec: want.append(('Hanging frame', 1))
        for it, q in want:
            ri = RI[it]; q = min(q, ri['units']); due = x['event_date'] + day(2)
            val = q * ri['purchase_price']; dep = float(min(150, int(round(val * RENTAL_DEPOSIT_PCT)))) if val >= 60 else 0.0
            ret = ''; dam = 0; lost_q = 0; status = 'Out'; kept = 0.0
            if x.get('story') == 'arch_out' and it == 'Wooden ceremony arch': ret = ''; status = 'Out'; dep = 130.0
            elif due <= TODAY:
                ret = iso(due + day(_wchoice(r, [0, 1, 2, 4], [.6, .25, .1, .05]))); 
                if to_date(ret) > TODAY: ret = ago(0)
                status = 'Returned'
                if r.random() < .06: dam = 1; kept = min(dep, ri['damage_fee']) if dep else ri['damage_fee'] * .5
                if r.random() < .02 and q > 3: lost_q = 1; status = 'Part returned'; kept = min(dep, ri['damage_fee']) if dep else 0.0
                elif r.random() < .02 and q == 1 and ri['units'] > 2: lost_q = 1; status = 'Lost'; ret = ''; kept = min(dep, ri['damage_fee']) if dep else ri['damage_fee']
            rentals.append(dict(date_out=x['event_date'] - day(1), proposal_id=x['proposal_id'], client=x['name'], item=it, qty=q, due_back=due, returned_on=ret, damaged=dam, lost=lost_q,
                                rent_charge=R2(q * ri['rent_price']), deposit_held=dep, deposit_kept=R2(kept), status=status))
            if dep: pays.append(dict(date=x['event_date'] - day(1), client=x['name'], proposal_id=x['proposal_id'], kind='Rental deposit', amount=dep, method='Card'))
    rentals.sort(key=lambda z: (z['date_out'], z['item']))
    for k, z in enumerate(rentals, 1): z['rental_id'] = 'RN-%04d' % k
    # consultations
    for x in enq:
        if x.get('consult'):
            c = x['consult']
            if c > TODAY + day(7): continue
            consults.append(dict(date=c, enquiry_id=x['enquiry_id'], client=x['name'], kind=_wchoice(r, CONSULT_KINDS, [.3, .35, .12, .23]), minutes=int(r.choice([30, 45, 60, 60, 90])), fee=60.0 if r.random() < .14 else 0.0))
    consults.sort(key=lambda z: (z['date'], z['enquiry_id']))
    for k, z in enumerate(consults, 1): z['consult_id'] = 'CS-%04d' % k
    # reviews and follow-up
    for x in bk:
        if x['status'] != 'Completed': continue
        asked = x['event_date'] + day(r.randint(2, 9))
        if asked > TODAY: asked = ''
        rec = bool(asked) and r.random() < .58
        got = (asked + day(r.randint(1, 20))) if rec else ''
        if got and got > TODAY: got = TODAY
        reviews.append(dict(proposal_id=x['proposal_id'], client=x['name'], event_type=x['event_type'], venue=x['venue'], event_date=x['event_date'], asked_on=asked, received_on=got,
                            rating=_wchoice(r, [3, 4, 5], [.06, .24, .70]) if rec else 0, repeat_client=x['source'] == 'Past client' or r.random() < .12, referred_others=r.random() < .2, value=x['final_amount']))
    for k, z in enumerate(reviews, 1): z['review_id'] = 'RR-%04d' % k
    # account invoice payments and pre-order deposits
    for v in inv_rows:
        if v['paid_on']: pays.append(dict(date=to_date(v['paid_on']), client=v['client'], proposal_id='', kind='Account invoice', amount=v['paid_amount'], method='Bank transfer', _inv=v['invoice_id']))
    for o in _W1()['orders']:
        if o['preorder'] and o['date'] <= TODAY: pays.append(dict(date=o['date'], client=o['client']['name'] if o['client'] else 'Counter sale', proposal_id='', kind='Pre-order deposit', amount=float(int(round(o['price'] * .3))),
                                                                  method=_wchoice(r, PAYMENT_METHODS, [.85, .1, .05]), _ord=o['order_id']))
    pays.sort(key=lambda z: (z['date'], z['client']))
    for k, z in enumerate(pays, 1): z['payment_id'] = 'PM-%05d' % k
    W.update(lines=lines, changes=changes, revs=revs, pays=pays, results=results, rentals=rentals, helpers=helpers, consults=consults, reviews=reviews, eday=eday, bk=bk)
    return W


def _W3(): return _raw('w3', _world3)

# ------------------------------------------------------------------ world part 4: wholesale orders, waste, stock, substitutions, deliveries, supplies, pay, expenses, cash
def _sup_for(item, d):
    s = FL[item]['supplier']
    if s == 'Local grower' and not (4 <= d.month <= 10): s = 'Wholesaler A'
    return s


def _bucket(d):
    w = d.weekday()
    return d - day(4) if w == 0 else d - day(w) if w <= 3 else d - day(w - 3)


def _world4():
    W1 = _W1(); W2 = _W2(); W3 = _W3(); r = rng('w4'); W = {}
    need = {}
    for o in W1['orders']:
        if o['needed_on'] > TODAY + day(6): continue
        b = _bucket(o['needed_on'])
        if b > TODAY or b < HISTORY_START: continue
        nd = need.setdefault(b, {})
        for a, q in _RCI[o['recipe']]['lines']:
            if a in FL: nd[a] = nd.get(a, 0.0) + q * o['size']
    wo = []; wl = []
    for b in sorted(need):
        hol = holiday_of(b + day(2)) or holiday_of(b + day(5))
        buf0 = 0.20 if hol else 0.10
        bysup = {}
        for a, q in need[b].items(): bysup.setdefault(_sup_for(a, b), []).append((a, q))
        for sup, items in bysup.items():
            arr = b + day(1)
            head = dict(date=b, arrival=arr, supplier=sup, kind='Weekly', proposal_id='', event='Shop and standing orders', status='Received' if arr <= TODAY else 'Ordered', lines=[])
            for a, q in items:
                f = FL[a]; buf = max(0.0, r.gauss(buf0, 0.05)); spb = f['stems_per_bunch']
                bunches = int(math.ceil(q * (1 + buf) / spb)); bought = bunches * spb
                fac = SUP[sup]['price_factor'] / SUP[f['supplier']]['price_factor']
                cs = R2(stem_cost(a, arr) * fac)
                left = bought - q; waste = max(0.0, left * 0.34 + bought * 0.010 * f['shrink_factor'])
                head['lines'].append(dict(variety=a, supplier=sup, needed=int(round(q)), bunches=bunches, stems=bought, cost_stem=cs, used=int(round(min(bought, q))), waste_stems=int(round(waste)),
                                          overbuy_pct=R2(buf), _arr=arr))
            wo.append(head)
    # event orders
    story_over = None
    done = [x for x in W3['bk'] if x['status'] == 'Completed' and x['event_date'] < TODAY - day(3) and not x.get('story') and any(rec == 'Bridal bouquet' for _, rec, _q in x['lines'])]
    story_over = done[-1]['proposal_id'] if done else ''
    for x in W3['bk']:
        if x['status'] == 'Cancelled': continue
        od = x['event_date'] - day(r.randint(5, 9)); arr = od + day(1)
        if od > TODAY or od < HISTORY_START: continue
        nd = {}
        for sec, rec, q in x['lines']:
            for a, qq in _RCI[rec]['lines']:
                if a in FL: nd[a] = nd.get(a, 0) + q * qq
        bysup = {}
        for a, q in nd.items(): bysup.setdefault(_sup_for(a, od), []).append((a, q))
        for sup, items in bysup.items():
            head = dict(date=od, arrival=arr, supplier=sup, kind='Event', proposal_id=x['proposal_id'], event=x['name'], status='Received' if arr <= TODAY else 'Ordered', lines=[])
            for a, q in items:
                f = FL[a]; spb = f['stems_per_bunch']; buf = max(0.05, r.gauss(OVERBUY_BUFFER, 0.06))
                bunches = int(math.ceil(q * (1 + buf) / spb)); bought = bunches * spb
                fac = SUP[sup]['price_factor'] / SUP[f['supplier']]['price_factor']
                cs = R2(stem_cost(a, arr) * fac); left = bought - q
                waste = max(0.0, left * 0.5 + bought * 0.008 * f['shrink_factor'])
                cause = ''
                if x['proposal_id'] == story_over and a == 'Peony':
                    q = max(q, 12); bunches = 12; bought = 60; waste = 42.0; left = 48; cause = 'Event change'
                head['lines'].append(dict(variety=a, supplier=sup, needed=int(q), bunches=bunches, stems=bought, cost_stem=cs, used=int(round(min(bought, q))), waste_stems=int(round(waste)), overbuy_pct=R2(buf),
                                          _arr=arr, _cause=cause))
            wo.append(head)
    wo.sort(key=lambda h: (h['date'], h['supplier'], h['kind']))
    waste = []
    for k, h in enumerate(wo, 1):
        h['order_id'] = 'WO-%04d' % k
        h['total'] = R2(sum(l['stems'] * l['cost_stem'] for l in h['lines']))
        for l in h['lines']:
            l['line_id'] = 'WL-%05d' % (len(wl) + 1); l['order_id'] = h['order_id']; l['date'] = h['date']; l['arrival'] = h['arrival']; l['kind'] = h['kind']; l['proposal_id'] = h['proposal_id']
            l['cost'] = R2(l['stems'] * l['cost_stem']); l['status'] = h['status']; l['flower_class'] = FL[l['variety']]['flower_class']
            wl.append(l)
            if h['status'] == 'Received' and l['waste_stems'] >= 2:
                cause = l.get('_cause') or _wchoice(r, ['Overbuy', 'Age', 'Damage', 'Quality', 'Event change' if h['kind'] == 'Event' else 'Age'], [.38, .27, .12, .13, .10 if h['kind'] == 'Event' else .05])
                wd = h['arrival'] + day(r.randint(2, 6))
                if wd > TODAY: wd = TODAY
                waste.append(dict(date=wd, variety=l['variety'], supplier=l['supplier'], stems=l['waste_stems'], cost=R2(l['waste_stems'] * l['cost_stem']), cause=cause, line_id=l['line_id'], order_id=h['order_id'],
                                  flower_class=l['flower_class']))
    waste.sort(key=lambda z: (z['date'], z['variety']))
    for k, z in enumerate(waste, 1): z['waste_id'] = 'WS-%05d' % k
    # cooler stock now: lots received in the last 12 days
    stock = []
    for l in wl:
        age = (TODAY - l['arrival']).days
        if l['kind'] == 'Weekly' and 0 <= age <= 12 and l['status'] == 'Received':
            left = int(round(l['stems'] * max(0.0, 1 - min(1.0, (age + 1) / 8.0) * 0.92) * r.uniform(.8, 1.1)))
            if left > 0: stock.append(dict(lot_id='LT-' + l['line_id'][3:], received=l['arrival'], variety=l['variety'], supplier=l['supplier'], stems_in=l['stems'], stems_left=min(left, l['stems']), cost_stem=l['cost_stem']))
    for l in wl:
        age = (TODAY - l['arrival']).days
        if l['kind'] == 'Weekly' and 0 <= age <= 12 and l['status'] == 'Received' and l['flower_class'] == 'Greenery' and r.random() < .5:
            pass
    stock.sort(key=lambda z: (z['received'], z['variety']))
    # substitutions
    subs = []
    for x in W3['bk']:
        if x['status'] not in ('Completed', 'Booked') or x['event_date'] > TODAY + day(4) or r.random() > .75: continue
        for _ in range(r.randint(1, 3)):
            sec, rec, q = x['lines'][r.randrange(len(x['lines']))]
            its = [a for a, qq in _RCI[rec]['lines'] if a in FL]
            if not its: continue
            a = its[r.randrange(len(its))]; cl = FL[a]['flower_class']
            alts = [v for v in FL if FL[v]['flower_class'] == cl and v != a]
            b = alts[r.randrange(len(alts))]; stems = sum(qq for aa, qq in _RCI[rec]['lines'] if aa == a) * q
            d = min(TODAY, x['event_date'] - day(r.randint(1, 4)))
            subs.append(dict(date=d, proposal_id=x['proposal_id'], client=x['name'], planned_variety=a, actual_variety=b, stems=stems, planned_cost_stem=R2(stem_cost(a, d)), actual_cost_stem=R2(stem_cost(b, d)),
                             reason=_wchoice(r, SUB_REASONS, [.4, .2, .15, .1, .15]), client_signoff=r.random() < .7))
    for wk in range(100):
        if r.random() < .6:
            d = TODAY - day(wk * 7 + r.randint(0, 6)); a = ['Garden rose', 'Peony', 'Ranunculus', 'Lisianthus', 'Hydrangea', 'Dahlia', 'Lily'][r.randrange(7)]
            alts = [v for v in FL if FL[v]['flower_class'] == FL[a]['flower_class'] and v != a]; b = alts[r.randrange(len(alts))]
            subs.append(dict(date=d, proposal_id='', client='Shop order', planned_variety=a, actual_variety=b, stems=r.choice([10, 15, 20, 30]), planned_cost_stem=R2(stem_cost(a, d)), actual_cost_stem=R2(stem_cost(b, d)),
                             reason=_wchoice(r, SUB_REASONS, [.5, .25, .15, 0, .1]), client_signoff=True))
    subs.sort(key=lambda z: (z['date'], z['client']))
    for k, z in enumerate(subs, 1):
        z['sub_id'] = 'SB-%04d' % k; z['cost_diff'] = R2((z['actual_cost_stem'] - z['planned_cost_stem']) * z['stems'])
    # deliveries
    dl = []
    for o in W1['orders']:
        if not o['zone'] or o['needed_on'] > TODAY + day(6): continue
        z = ZN[o['zone']]; mins = int(round(z['minutes'] * r.uniform(.8, 1.3))); km = int(round(z['km'] * r.uniform(.8, 1.15)))
        hol = holiday_of(o['needed_on'])
        driver = 'Dmitri Petrov' if not hol or r.random() < .65 else _wchoice(r, ['Emeka Obi', 'Aisha Rahman'], [.7, .3]) if r.random() < .8 else 'Marisol Vega'
        hr = {'Morning': 9, 'Midday': 12, 'Afternoon': 15, 'Evening': 18}; win = _wchoice(r, DELIVERY_WINDOWS, [.35, .25, .3, .1])
        if o['needed_on'] < TODAY: st = _wchoice(r, ['Delivered', 'Failed', 'Rescheduled'], [.94, .02, .04])
        elif o['needed_on'] == TODAY: st = 'Delivered' if win in ('Morning', 'Midday') else 'Scheduled'
        else: st = 'Scheduled'
        dl.append(dict(date=o['needed_on'], order_id=o['order_id'], client=o['client']['name'] if o['client'] else 'Counter sale', zone=o['zone'], window=win, driver=driver, minutes=mins, km=km,
                       cost=R2(mins / 60.0 * DRIVER_RATE + km * VEHICLE_KM), fee_charged=o['delivery_fee'], status=st, _o=o, _win=hr[win]))
    dl.sort(key=lambda z: (z['date'], z['_win'], z['zone']))
    cnt = {}
    for k, z in enumerate(dl, 1):
        z['delivery_id'] = 'DL-%05d' % k; key = z['date']; cnt[key] = cnt.get(key, 0) + 1; z['stop'] = cnt[key]
    # supplies by month
    use = {}
    for o in W1['orders']:
        if o['needed_on'] > TODAY: continue
        m = _ms(o['needed_on'])
        for a, q in _RCI[o['recipe']]['lines']:
            if a in HG: use[(m, a)] = use.get((m, a), 0.0) + q * (0.6 + 0.4 * o['size'])
    for x in W3['bk']:
        if x['status'] == 'Cancelled' or x['event_date'] > TODAY: continue
        m = _ms(x['event_date'])
        for sec, rec, q in x['lines']:
            for a, qq in _RCI[rec]['lines']:
                if a in HG: use[(m, a)] = use.get((m, a), 0.0) + q * qq
    supply_m = []
    for m in _month_list(_ms(HISTORY_START), _ms(TODAY)):
        for s in supplies:
            u = use.get((m, s['item']), 0.0); bought = int(round(u * r.uniform(.9, 1.15) / 5.0) * 5) if m < _ms(TODAY) else int(u * .6)
            cost = R2(bought * s['cost'] * (1.0 if (TODAY - m).days > 365 else 1.03))
            supply_m.append(dict(month=m, item=s['item'], used=int(round(u)), bought=bought, cost=cost))
    W.update(wo=wo, wl=wl, waste=waste, stock=stock, subs=subs, dl=dl, supply_m=supply_m, story_over=story_over)
    return W


def _W4(): return _raw('w4', _world4)

# ------------------------------------------------------------------ world part 5: monthly money (types, pay, expenses, marketing, tax, cash) and holidays
_MK_SOURCE = {'Online directory': 'Online directory', 'Wedding fair': 'Wedding fair', 'Social ads': 'Social media', 'Venue partnership': 'Venue referral', 'Printed price guide': 'Walk-in',
              'Photo shoot': 'Web search'}
TYPES = ['Wedding', 'Event', 'Retail', 'Sympathy', 'Corporate', 'Delivery fees', 'Rentals']


def _event_type_class(et): return 'Wedding' if et == 'Wedding' else 'Sympathy' if et == 'Memorial service' else 'Event'


def _world5():
    W1 = _W1(); W2 = _W2(); W3 = _W3(); W4 = _W4(); r = rng('w5'); W = {}
    months = _month_list(_ms(HISTORY_START), _ms(TODAY))
    tm = {}
    def add(m, t, rev=0.0, goods=0.0, lab=0.0, dlv=0.0, n=0):
        k = (m, t); a = tm.setdefault(k, [0.0, 0.0, 0.0, 0.0, 0]); a[0] += rev; a[1] += goods; a[2] += lab; a[3] += dlv; a[4] += n
    dcost = {z['order_id']: z['cost'] for z in W4['dl']}
    for o in W1['orders']:
        if o['needed_on'] > TODAY: continue
        m = _ms(o['needed_on']); t = 'Corporate' if o['order_type'] == 'Standing order' else 'Sympathy' if o['order_type'] == 'Sympathy' else 'Retail'
        add(m, t, o['price'], o['goods'], o['labour_minutes'] / 60.0 * LABOUR_COST_HOUR, dcost.get(o['order_id'], 0.0), 1)
        if o['delivery_fee']: add(m, 'Delivery fees', o['delivery_fee'], 0, 0, 0, 0)
    res = {x['proposal_id']: x for x in W3['results']}
    for x in W3['bk']:
        if x['status'] == 'Completed':
            q = res[x['proposal_id']]; add(_ms(x['event_date']), _event_type_class(x['event_type']), x['final_amount'], q['actual_goods_cost'] + q['waste_cost'], q['actual_hours'] * LABOUR_COST_HOUR + q['helper_cost'],
                                           q['logistics_cost'], 1)
        elif x['status'] == 'Cancelled' and x['cancelled_on'] <= TODAY: add(_ms(x['cancelled_on']), _event_type_class(x['event_type']), x['final_amount'], 0, 0, 0, 0)
    for z in W3['rentals']:
        if z['date_out'] <= TODAY: add(_ms(z['date_out']), 'Rentals', z['rent_charge'] + z['deposit_kept'], 0, 0, 0, 1)
    W['type_month'] = [dict(month=m, type=t, revenue=R2(a[0]), goods_cost=R2(a[1]), labour_cost=R2(a[2]), delivery_cost=R2(a[3]), orders=a[4]) for (m, t), a in sorted(tm.items(), key=lambda kv: (kv[0][0], TYPES.index(kv[0][1])))]
    rev_m = {}
    for x in W['type_month']: rev_m[x['month']] = rev_m.get(x['month'], 0.0) + x['revenue']
    purch = {}
    for l in W4['wl']:
        if l['status'] == 'Received': purch[_ms(l['arrival'])] = purch.get(_ms(l['arrival']), 0.0) + l['cost']
    # staff pay
    pay = []; hrs_m = {}
    for h in W3['helpers']: hrs_m.setdefault((_ms(h['date']), h['person']), []).append(h)
    for m in months:
        frac = 1.0 if m < _ms(TODAY) else TODAY.day / float(calendar.monthrange(m.year, m.month)[1])
        hol = any(holiday_window(h, m.year)[0].month == m.month for h in HOLIDAYS[:2] + HOLIDAYS[3:])
        for s in staff[1:]:
            if s['pay_type'] == 'Salary': hrs = float(s['hours_week']) * 4.33 * frac; gross = s['monthly_salary'] * frac; emp = R2(gross * 0.10); rate = 0.0
            elif s['pay_type'] == 'Hourly': hrs = R2(s['hours_week'] * 4.33 * r.uniform(.9, 1.08) * (1.12 if hol else 1.0) * frac); gross = R2(hrs * s['hourly_rate']); emp = 0.0; rate = s['hourly_rate']
            else:
                hs = hrs_m.get((m, s['name']), [])
                if not hs: continue
                hrs = R2(sum(h['hours'] for h in hs)); gross = R2(sum(h['pay'] for h in hs)); emp = 0.0; rate = s['hourly_rate']
            paid_on = add_months(m, 1).replace(day=20) if m < _ms(TODAY) else None
            st = 'Paid' if paid_on and paid_on <= TODAY else 'Accruing' if m == _ms(TODAY) else 'Due'
            pay.append(dict(month=m, person=s['name'], pay_type=s['pay_type'], hours=R2(hrs), rate=rate, gross_pay=R2(gross), employer_cost=emp, total_cost=R2(gross + emp), status=st, paid_on=iso(paid_on) if st == 'Paid' else ''))
    for k, z in enumerate(pay, 1): z['pay_id'] = 'PY-%04d' % k
    W['pay'] = pay
    lab_m = {}
    for z in pay: lab_m[z['month']] = lab_m.get(z['month'], 0.0) + z['total_cost']
    # marketing
    mk = []
    for m in months:
        for kind in MARKETING_KINDS:
            amt = 0.0
            if kind == 'Online directory': amt = 85.0 if (TODAY - m).days > 200 else 95.0
            elif kind == 'Social ads': amt = R2(150 + 120 * r.random() + (80 if m.month in (1, 2, 9) else 0))
            elif kind == 'Wedding fair' and m.month in (1, 9): amt = 450.0
            elif kind == 'Venue partnership' and m.month in (3, 6, 9, 12): amt = 120.0
            elif kind == 'Printed price guide' and m.month in (2, 8): amt = 380.0
            elif kind == 'Photo shoot' and m.month == 4: amt = 600.0
            if amt: mk.append(dict(month=m, kind=kind, source=_MK_SOURCE[kind], spend=amt))
    for k, z in enumerate(mk, 1): z['campaign_id'] = 'MK-%03d' % k
    W['marketing'] = mk
    mk_m = {}
    for z in mk: mk_m[z['month']] = mk_m.get(z['month'], 0.0) + z['spend']
    supply_cost = {}
    for z in W4['supply_m']: supply_cost[z['month']] = supply_cost.get(z['month'], 0.0) + z['cost']
    # expenses
    ex = []
    for m in months:
        old = (TODAY - m).days > 330
        seas = {1: 1.25, 2: 1.2, 7: .9, 8: .9, 12: 1.15}.get(m.month, 1.0)
        base = {'Rent': 3900.0 if old else 4100.0, 'Utilities': R2(520 * seas + r.uniform(0, 80)), 'Vehicle': R2(720 + r.uniform(0, 300) + (160 if holiday_window(HOLIDAYS[1], m.year)[0].month == m.month else 0)),
                'Insurance': 295.0 if old else 310.0, 'Phone and internet': 140.0, 'Order software': 189.0, 'Marketing': R2(mk_m.get(m, 0.0)), 'Accounting': 320.0,
                'Card fees': R2(rev_m.get(m, 0.0) * 0.6 * 0.019), 'Packaging and supplies': R2(supply_cost.get(m, 0.0)),
                'Training': {3: 280.0, 10: 340.0}.get(m.month, 0.0), 'Equipment': {2: 620.0, 8: 1150.0, 11: 380.0}.get(m.month, 0.0) if m.year == TODAY.year or m.year == TODAY.year - 1 else 0.0,
                'Cooler and repairs': R2(190 + r.uniform(0, 260))}
        for cat in EXPENSE_CATEGORIES:
            v = base[cat]
            if v > 0: ex.append(dict(month=m, date=m.replace(day=min(28, 1 + (EXPENSE_CATEGORIES.index(cat) * 2) % 27)), category=cat, amount=R2(v)))
    ex = [e for e in ex if e['date'] <= TODAY]
    ex.sort(key=lambda z: (z['date'], z['category']))
    for k, z in enumerate(ex, 1): z['expense_id'] = 'EX-%04d' % k
    W['expenses'] = ex
    ex_m = {}
    for z in ex: ex_m[z['month']] = ex_m.get(z['month'], 0.0) + z['amount']
    pnl = []
    for m in months:
        rev = rev_m.get(m, 0.0); fl = purch.get(m, 0.0); lb = lab_m.get(m, 0.0); oh = ex_m.get(m, 0.0)
        pnl.append(dict(month=m, revenue=R2(rev), flower_cost=R2(fl), labour_cost=R2(lb), overhead=R2(oh), profit=R2(rev - fl - lb - oh)))
    W['pnl'] = pnl
    # tax set-aside (quarterly payment on the 20th of Jan, Apr, Jul and Oct) and cash
    tax = []; acc = 0.0; cash = []; bal = 50000.0
    for i, p in enumerate(pnl):
        m = p['month']; sa = R2(max(0.0, p['profit']) * TAX_SET_ASIDE_PCT); acc += sa
        paid = 0.0; paid_on = ''
        if m.month in (1, 4, 7, 10) and m > _ms(HISTORY_START) and m.replace(day=20) <= TODAY: paid = R2(acc - sa); acc = sa; paid_on = iso(m.replace(day=20))
        draw = OWNER_DRAW if m < _ms(TODAY) else R2(OWNER_DRAW * TODAY.day / 30.0)
        qpaid = m < D(TODAY.year, ((TODAY.month - 1) // 3) * 3 + 1, 1)
        tax.append(dict(month=m, profit=p['profit'], set_aside=sa, paid_amount=paid, paid_on=paid_on, status='Paid' if qpaid else 'Upcoming'))
        start = bal; bal = bal + p['profit'] - draw - paid
        cash.append(dict(month=m, cash_start=R2(start), cash_in=p['revenue'], cash_out=R2(p['flower_cost'] + p['labour_cost'] + p['overhead']), owner_draw=R2(draw), tax_paid=paid, cash_end=R2(bal), cash_floor=CASH_FLOOR))
    for k, z in enumerate(tax, 1): z['tax_id'] = 'TX-%03d' % k
    W['tax'] = tax; W['cash'] = cash
    # holidays
    hol = []; hd = []
    ords = W1['orders']
    for y in (TODAY.year - 2, TODAY.year - 1, TODAY.year):
        for h in HOLIDAYS:
            a, b = holiday_window(h, y)
            if b < HISTORY_START or a > add_months(TODAY, 2): continue
            os_ = [o for o in ords if a <= o['needed_on'] <= b and o['order_type'] != 'Standing order']
            if not os_: continue
            stems = int(sum(sum(q for aa, q in _RCI[o['recipe']]['lines'] if aa in FL) * o['size'] for o in os_))
            pre = [o for o in os_ if o['preorder']]
            hrs = sum(z['hours'] for z in W3['helpers'] if a <= z['date'] <= b)
            status = 'Done' if b < TODAY else 'Planning' if a > TODAY else 'Running'
            rev = float(sum(o['price'] + o['delivery_fee'] for o in os_))
            hol.append(dict(holiday=h, year=y, start=a, end=b, orders=len(os_), stems=stems, revenue=R2(rev), avg_ticket=R2(rev / len(os_)), preorders=len(pre), preorder_value=R2(sum(o['price'] for o in pre)),
                            helper_hours=R2(hrs), status=status))
            d = a
            while d <= b:
                do = [o for o in os_ if o['needed_on'] == d]
                cap = {HOLIDAYS[0]: 80, HOLIDAYS[1]: 75, HOLIDAYS[2]: 40, HOLIDAYS[3]: 60}[h] + (10 if d.weekday() in (4, 5) else 0)
                hd.append(dict(holiday=h, year=y, date=d, capacity=cap, orders=len(do), preorders=sum(1 for o in do if o['preorder']), deposits=R2(sum(o['price'] * .3 for o in do if o['preorder'])), stems=int(sum(sum(q for aa, q in _RCI[o['recipe']]['lines'] if aa in FL) * o['size'] for o in do))))
                d += day(1)
    for k, z in enumerate(hol, 1): z['holiday_id'] = 'HL-%02d' % k
    for k, z in enumerate(hd, 1): z['day_id'] = 'HD-%03d' % k
    W['holiday'] = hol; W['holiday_day'] = hd
    return W


def _W5(): return _raw('w5', _world5)

# ------------------------------------------------------------------ clients and the public generators
def _clients():
    W1 = _W1(); W3 = _W3(); r = rng('cl'); nm = W1['_nm']; rows = []
    for a in W1['accounts']:
        rows.append(dict(client=a['name'], client_type=a['client_type'], contact=nm.person(), area=a['area'], zone=a['zone'], terms=a['terms'], source=a['source'], first=a['first']))
    for c in W1['retail_pool']:
        if c['first'] is not None: rows.append(dict(client=c['name'], client_type='Retail customer', contact=c['name'], area=c['area'], zone=c['zone'], terms=0, source=c['source'], first=c['first']))
    for x in W3['bk']:
        a = _wchoice(r, AREAS, [10, 9, 8, 8, 8, 7, 7, 7, 6, 6, 5, 5])
        rows.append(dict(client=x['name'], client_type='Couple' if x['event_type'] == 'Wedding' else 'Event client', contact=first_name(x['name']), area=a, zone=_zone_of_area(a), terms=0,
                         source=x['source'], first=x['booked_on']))
    rows.sort(key=lambda c: (c['first'], c['client']))
    tot = {}; cnt = {}
    for o in W1['orders']:
        if o['client'] is not None and o['needed_on'] <= TODAY:
            tot[o['client']['name']] = tot.get(o['client']['name'], 0.0) + o['price'] + o['delivery_fee']; cnt[o['client']['name']] = cnt.get(o['client']['name'], 0) + 1
    for x in W3['bk']:
        if x['status'] in ('Completed', 'Cancelled'): tot[x['name']] = tot.get(x['name'], 0.0) + x['final_amount']; cnt[x['name']] = cnt.get(x['name'], 0) + 1
    for k, c in enumerate(rows, 1):
        c['client_id'] = 'CL-%04d' % k; c['phone'] = fake_phone(1000 + k); c['email'] = fake_email(c['client'])
        c['orders'] = cnt.get(c['client'], 0); c['lifetime_value'] = R2(tot.get(c['client'], 0.0)); c['first_order'] = iso(c['first'])
    return rows


def _cid(): return _raw('cid', lambda: {c['client']: c['client_id'] for c in _raw('clients', _clients)})
def _g(name, fn):
    globals()[name] = lambda n=None: _thin(_cached(name, fn), n)


def _f_clients(): return [{k: v for k, v in c.items() if k not in ('first', 'terms')} | {'payment_terms_days': c['terms']} for c in _raw('clients', _clients)]
_g('client_rows', _f_clients)


def _f_orders():
    out = []; ids = _cid()
    for i, o in enumerate(_W1()['orders']):
        status = 'Open' if o['needed_on'] > TODAY or (o['needed_on'] == TODAY and i % 2) else 'Done'
        out.append(dict(order_id=o['order_id'], date=iso(o['date']), needed_on=iso(o['needed_on']), week=iso(week_start(o['needed_on'])), month=iso(_ms(o['needed_on'])), order_type=o['order_type'],
                        client_id=ids.get(o['client']['name'], '') if o['client'] else '', client=o['client']['name'] if o['client'] else 'Counter sale', recipe=o['recipe'], kind=RC[o['recipe']]['kind'],
                        size=o['size'], price=float(o['price']), flower_cost=R2(o['goods']), labour_minutes=o['labour_minutes'], zone=o['zone'], delivery_fee=o['delivery_fee'], pay_method=o['pay_method'],
                        preorder=o['preorder'], status=status))
    return out
_g('order_rows', _f_orders)


def _f_standing():
    return [dict(x) for x in _W1()['standing']]
_g('standing_order_rows', _f_standing)


def _f_invoices():
    ids = _cid()
    return [dict(invoice_id=v['invoice_id'], client_id=ids[v['client']], client=v['client'], month=iso(v['month']), issued_on=iso(v['issued_on']), due_date=iso(v['due_date']), amount=v['amount'],
                 paid_amount=v['paid_amount'], paid_on=v['paid_on'], status=v['status'], orders=v['orders']) for v in _W1()['invoices']]
_g('invoice_rows', _f_invoices)


def _f_enq():
    ids = {}; out = []
    rp = {x['enquiry_id']: x for x in _W2()['props']}
    for k, x in enumerate(_W2()['enq']):
        st = x['status']; p = rp.get(x['enquiry_id'])
        es = 'Booked' if st in ('Booked', 'Completed', 'Cancelled') else 'Proposal sent' if st == 'Sent' else 'Consultation booked' if st == 'Draft' else st
        out.append(dict(enquiry_id=x['enquiry_id'], date=iso(x['e']), name=x['name'], event_type=x['event_type'], event_date=iso(x['event_date']), guests=x['guests'], budget=x['budget'], source=x['source'],
                        venue=x.get('venue', ''), phone=fake_phone(2000 + k), email=fake_email(x['name'].split(' & ')[-1] if ' & ' in x['name'] else x['name'], 0), status=es,
                        consult_date=iso(x['consult']) if x.get('consult') else '', proposal_id=p['proposal_id'] if p else '', booked_on=iso(x['booked_on']) if x.get('booked_on') else '',
                        lost_reason=x.get('lost_reason', ''), quoted=float(x.get('price', 0.0))))
    return out
_g('enquiry_rows', _f_enq)


def _f_consult():
    return [dict(consult_id=z['consult_id'], date=iso(z['date']), enquiry_id=z['enquiry_id'], client=z['client'], kind=z['kind'], minutes=z['minutes'], fee=z['fee']) for z in _W3()['consults']]
_g('consultation_rows', _f_consult)


def _f_props():
    out = []
    for x in _W2()['props']:
        hrs = R2(2.5 + 1.1 * x.get('revisions', 0) + (int(x['proposal_id'][3:]) * 7 % 10) / 10.0)
        out.append(dict(proposal_id=x['proposal_id'], enquiry_id=x['enquiry_id'], client=x['name'], event_type=x['event_type'], event_date=iso(x['event_date']), venue=x.get('venue', ''), zone=x['zone'],
                        guests=x['guests'], budget=x['budget'], sent_on=iso(x['sent_on']) if x.get('sent_on') else '', status=x['status'], revisions=x.get('revisions', 0), proposal_hours=hrs,
                        subtotal=x['subtotal'], discount_pct=x['discount'], delivery_charge=x['delivery_charge'], setup_charge=x['setup_charge'], price=x['price'], planned_goods_cost=x['planned_goods'],
                        planned_hours=x['planned_hours'], booked_on=iso(x['booked_on']) if x.get('booked_on') else '', deposit=x.get('deposit', 0.0),
                        deposit_due=iso(x['deposit_due']) if x.get('deposit_due') else '', deposit_paid_on=iso(x['deposit_paid']) if x.get('deposit_paid') else '',
                        final_amount=x.get('final_amount', 0.0), final_due=iso(x['final_due']) if x.get('final_due') else '', final_paid_on=iso(x['final_paid']) if x.get('final_paid') else '',
                        cancelled_on=iso(x['cancelled_on']) if x.get('cancelled_on') else '', source=x['source'], lost_reason=x.get('lost_reason', '')))
    return out
_g('proposal_rows', _f_props)


def _f_lines():
    return [dict(line_id=l['line_id'], proposal_id=l['proposal_id'], section=l['section'], recipe=l['recipe'], qty=l['qty'], unit_price=l['unit_price'], line_price=l['line_price']) for l in _W3()['lines']]
_g('proposal_line_rows', _f_lines)
_g('revision_rows', lambda: [dict(revision_id=z['revision_id'], proposal_id=z['proposal_id'], client=z['client'], round=z['round'], date=iso(z['date']), hours=z['hours'], charged=z['charged'], fee=z['fee']) for z in _W3()['revs']])
_g('change_rows', lambda: [dict(change_id='CH-%03d' % k, proposal_id=z['proposal_id'], client=z['client'], date=iso(z['date']), kind=z['kind'], old_amount=z['old_amount'], new_amount=z['new_amount'],
                                 retainer_kept=z['retainer_kept']) for k, z in enumerate(sorted(_W3()['changes'], key=lambda z: z['date']), 1)])
_g('event_result_rows', lambda: [dict(result_id='ER-%03d' % k, **{a: (iso(b) if hasattr(b, 'isoformat') else b) for a, b in z.items()}) for k, z in enumerate(_W3()['results'], 1)])
_g('event_day_rows', lambda: [dict(day_id='ED-%03d' % k, **{a: (iso(b) if hasattr(b, 'isoformat') else b) for a, b in z.items()}) for k, z in enumerate(_W3()['eday'], 1)])
_g('review_rows', lambda: [dict(review_id=z['review_id'], proposal_id=z['proposal_id'], client=z['client'], event_type=z['event_type'], venue=z['venue'], event_date=iso(z['event_date']),
                                 asked_on=iso(z['asked_on']) if z['asked_on'] else '', received_on=iso(z['received_on']) if z['received_on'] else '', rating=z['rating'], repeat_client=z['repeat_client'],
                                 referred_others=z['referred_others'], value=z['value']) for z in _W3()['reviews']])
_g('rental_rows', lambda: [dict(rental_id=z['rental_id'], date_out=iso(z['date_out']), proposal_id=z['proposal_id'], client=z['client'], item=z['item'], qty=z['qty'], due_back=iso(z['due_back']),
                                 returned_on=z['returned_on'], damaged=z['damaged'], lost=z['lost'], rent_charge=z['rent_charge'], deposit_held=z['deposit_held'], deposit_kept=z['deposit_kept'],
                                 status=z['status']) for z in _W3()['rentals']])
_g('helper_rows', lambda: [dict(helper_id=z['helper_id'], date=iso(z['date']), month=iso(_ms(z['date'])), person=z['person'], kind=z['kind'], proposal_id=z['proposal_id'], event=z['event'], hours=z['hours'],
                                 rate=z['rate'], pay=z['pay'], status=z['status']) for z in _W3()['helpers']])


def _f_pay():
    ids = _cid(); out = []; inv = {}
    for z in _W3()['pays']:
        out.append(dict(payment_id=z['payment_id'], date=iso(z['date']), month=iso(_ms(z['date'])), client_id=ids.get(z['client'], ''), client=z['client'], proposal_id=z['proposal_id'], invoice_id=z.get('_inv', ''),
                        order_id=z.get('_ord', ''), kind=z['kind'], amount=z['amount'], method=z['method']))
    return out
_g('payment_rows', _f_pay)
_g('wholesale_order_rows', lambda: [dict(order_id=h['order_id'], date=iso(h['date']), arrival=iso(h['arrival']), month=iso(_ms(h['date'])), supplier=h['supplier'], kind=h['kind'], proposal_id=h['proposal_id'],
                                         event=h['event'], lines=len(h['lines']), total=h['total'], status=h['status']) for h in _W4()['wo']])
_g('wholesale_line_rows', lambda: [dict(line_id=l['line_id'], order_id=l['order_id'], date=iso(l['date']), arrival=iso(l['arrival']), month=iso(_ms(l['date'])), supplier=l['supplier'], kind=l['kind'],
                                         proposal_id=l['proposal_id'], variety=l['variety'], flower_class=l['flower_class'], needed=l['needed'], bunches=l['bunches'], stems=l['stems'], cost_stem=l['cost_stem'],
                                         cost=l['cost'], used=l['used'], waste_stems=l['waste_stems'], status=l['status']) for l in _W4()['wl']])
_g('waste_rows', lambda: [dict(waste_id=z['waste_id'], date=iso(z['date']), month=iso(_ms(z['date'])), variety=z['variety'], flower_class=z['flower_class'], supplier=z['supplier'], stems=z['stems'],
                                cost=z['cost'], cause=z['cause'], line_id=z['line_id'], order_id=z['order_id']) for z in _W4()['waste']])
_g('stock_rows', lambda: [dict(lot_id=z['lot_id'], received=iso(z['received']), variety=z['variety'], supplier=z['supplier'], stems_in=z['stems_in'], stems_left=z['stems_left'], cost_stem=z['cost_stem'])
                          for z in _W4()['stock']])
_g('substitution_rows', lambda: [dict(sub_id=z['sub_id'], date=iso(z['date']), proposal_id=z['proposal_id'], client=z['client'], planned_variety=z['planned_variety'], actual_variety=z['actual_variety'],
                                       stems=z['stems'], planned_cost_stem=z['planned_cost_stem'], actual_cost_stem=z['actual_cost_stem'], cost_diff=z['cost_diff'], reason=z['reason'],
                                       client_signoff=z['client_signoff']) for z in _W4()['subs']])


def _f_deliv():
    out = []
    for z in _W4()['dl']:
        hh = z['_win'] + (z['stop'] * 7) % 50 // 60; mm = (z['stop'] * 7) % 50 + (z['_win'] and 5)
        out.append(dict(delivery_id=z['delivery_id'], date=iso(z['date']), week=iso(week_start(z['date'])), month=iso(_ms(z['date'])), order_id=z['order_id'], client=z['client'], zone=z['zone'],
                        window=z['window'], stop=z['stop'], driver=z['driver'], minutes=z['minutes'], km=z['km'], cost=z['cost'], fee_charged=z['fee_charged'], status=z['status'],
                        time='%02d:%02d' % (z['_win'] + (1 if z['stop'] % 3 == 0 else 0), (z['stop'] * 7) % 60) if z['status'] == 'Delivered' else ''))
    return out
_g('delivery_rows', _f_deliv)
_g('supply_month_rows', lambda: [dict(row_id='SU-%03d' % k, month=iso(z['month']), item=z['item'], used=z['used'], bought=z['bought'], cost=z['cost']) for k, z in enumerate(_W4()['supply_m'], 1)])
_g('pay_rows', lambda: [dict(pay_id=z['pay_id'], month=iso(z['month']), person=z['person'], pay_type=z['pay_type'], hours=z['hours'], rate=z['rate'], gross_pay=z['gross_pay'], employer_cost=z['employer_cost'],
                              total_cost=z['total_cost'], status=z['status'], paid_on=z['paid_on']) for z in _W5()['pay']])
_g('marketing_rows', lambda: [dict(campaign_id=z['campaign_id'], month=iso(z['month']), kind=z['kind'], source=z['source'], spend=z['spend']) for z in _W5()['marketing']])
_g('expense_rows', lambda: [dict(expense_id=z['expense_id'], date=iso(z['date']), month=iso(z['month']), category=z['category'], amount=z['amount']) for z in _W5()['expenses']])
_g('type_month_rows', lambda: [dict(row_id='TM-%03d' % k, month=iso(z['month']), type=z['type'], revenue=z['revenue'], goods_cost=z['goods_cost'], labour_cost=z['labour_cost'],
                                     delivery_cost=z['delivery_cost'], orders=z['orders']) for k, z in enumerate(_W5()['type_month'], 1)])
_g('pnl_rows', lambda: [dict(row_id='PL-%02d' % k, month=iso(z['month']), revenue=z['revenue'], flower_cost=z['flower_cost'], labour_cost=z['labour_cost'], overhead=z['overhead'], profit=z['profit'])
                         for k, z in enumerate(_W5()['pnl'], 1)])
_g('tax_rows', lambda: [dict(tax_id=z['tax_id'], month=iso(z['month']), profit=z['profit'], set_aside=z['set_aside'], paid_amount=z['paid_amount'], paid_on=z['paid_on'], status=z['status']) for z in _W5()['tax']])
_g('cash_rows', lambda: [dict(row_id='CA-%02d' % k, month=iso(z['month']), cash_start=z['cash_start'], cash_in=z['cash_in'], cash_out=z['cash_out'], owner_draw=z['owner_draw'], tax_paid=z['tax_paid'],
                               cash_end=z['cash_end'], cash_floor=z['cash_floor']) for k, z in enumerate(_W5()['cash'], 1)])
_g('holiday_rows', lambda: [dict(holiday_id=z['holiday_id'], holiday=z['holiday'], year=z['year'], start=iso(z['start']), end=iso(z['end']), orders=z['orders'], stems=z['stems'], revenue=z['revenue'],
                                  avg_ticket=z['avg_ticket'], preorders=z['preorders'], preorder_value=z['preorder_value'], helper_hours=z['helper_hours'], status=z['status']) for z in _W5()['holiday']])
_g('holiday_day_rows', lambda: [dict(day_id=z['day_id'], holiday=z['holiday'], year=z['year'], date=iso(z['date']), capacity=z['capacity'], orders=z['orders'], preorders=z['preorders'],
                                      deposits=z['deposits'], stems=z['stems']) for z in _W5()['holiday_day']])


def proposal_margin(pid, now=True):
    """gross margin of one proposal: (price - goods - design hours x labour cost - delivery and set-up cost) / price. now=True costs the stems at today's wholesale cost,
    now=False at the quoted (list) cost. Delivery and set-up cost = 4 x the zone's cost per stop (two trips with driver, van and a set-up crew)."""
    x = [p for p in _W2()['props'] if p['proposal_id'] == pid][0]
    g = sum((goods_cost(rec, TODAY) if now else plan_goods(rec, x['event_date'])) * q for _, rec, q in x['lines'])
    cost = g + x['planned_hours'] * LABOUR_COST_HOUR + ZN[x['zone']]['cost'] * 4
    return R2(1 - cost / x['price'])


def zone_profit(zone, months=12):
    """deliveries, fees charged and cost of one delivery zone over the last `months` months"""
    lo = month_start(months - 1); dl = [z for z in _W4()['dl'] if z['zone'] == zone and lo <= z['date'] <= TODAY and z['status'] == 'Delivered']
    fee = sum(z['fee_charged'] for z in dl); cost = sum(z['cost'] for z in dl)
    return dict(deliveries=len(dl), fees=R2(fee), cost=R2(cost), profit=R2(fee - cost), fee_each=R2(fee / len(dl)) if dl else 0.0, cost_each=R2(cost / len(dl)) if dl else 0.0)


def standing_margin(sid):
    """margin of one standing arrangement per delivery at today's stem costs: (price - goods - labour - delivery cost) / price"""
    s = [x for x in _W1()['standing'] if x['standing_id'] == sid][0]; rec = s['recipe']
    c = goods_cost(rec, TODAY) + RC[rec]['labour_minutes'] / 60.0 * LABOUR_COST_HOUR + ZN[s['zone']]['cost']
    return R2(1 - c / s['price']), R2(c)


def story():
    """ids of the story rows (always taken from here, never hard-coded; ids depend on the build date):
    low_margin_proposal (+ low_margin_client, low_margin_price, low_margin_now, low_margin_quoted, margin_floor): a booked wedding quoted with a 32% discount, below the margin floor at today's stem costs
    overdue_balance_proposal (+ overdue_balance_client, overdue_balance_amount, overdue_balance_due, overdue_balance_days, overdue_balance_event): wedding in 9 days, final balance due 5 days ago and unpaid
    deposit_missing_proposal (+ deposit_missing_client, deposit_missing_amount, deposit_missing_due, deposit_missing_days): booked 12 days ago, retainer due 5 days ago and not collected
    overbuy_line (+ overbuy_order, overbuy_proposal, overbuy_variety, overbuy_stems, overbuy_waste_stems, overbuy_waste_cost): Peony bought for an event that shrank, 42 stems wasted
    overdue_account (+ overdue_client_id, overdue_invoices, overdue_balance, overdue_days): corporate standing-order account with 4 unpaid monthly invoices, oldest 6+ weeks past due
    unreturned_rental (+ unreturned_item, unreturned_client, unreturned_due, unreturned_days, unreturned_deposit): a wooden arch that never came back
    losing_zone (+ losing_zone_fee, losing_zone_cost, losing_zone_profit, losing_zone_deliveries) and undercosted_standing (+ undercosted_account, undercosted_price, undercosted_margin, undercosted_cost)"""
    out = {}; W2 = _W2(); W4 = _W4()
    P = {x['story']: x for x in W2['props'] if x.get('story')}
    x = P['low_margin']; out['low_margin_proposal'] = x['proposal_id']; out['low_margin_client'] = x['name']; out['low_margin_price'] = x['price']
    out['low_margin_now'] = proposal_margin(x['proposal_id']); out['low_margin_quoted'] = proposal_margin(x['proposal_id'], False); out['margin_floor'] = MARGIN_FLOOR
    x = P['overdue_balance']; out['overdue_balance_proposal'] = x['proposal_id']; out['overdue_balance_client'] = x['name']; out['overdue_balance_amount'] = R2(x['final_amount'] - x['deposit'])
    out['overdue_balance_due'] = iso(x['final_due']); out['overdue_balance_days'] = (TODAY - x['final_due']).days; out['overdue_balance_event'] = iso(x['event_date'])
    x = P['deposit_missing']; out['deposit_missing_proposal'] = x['proposal_id']; out['deposit_missing_client'] = x['name']; out['deposit_missing_amount'] = x['deposit']
    out['deposit_missing_due'] = iso(x['deposit_due']); out['deposit_missing_days'] = (TODAY - x['deposit_due']).days
    ol = [l for l in W4['wl'] if l['proposal_id'] == W4['story_over'] and l['variety'] == 'Peony'][0]
    out['overbuy_line'] = ol['line_id']; out['overbuy_order'] = ol['order_id']; out['overbuy_proposal'] = ol['proposal_id']; out['overbuy_variety'] = 'Peony'; out['overbuy_stems'] = ol['stems']
    out['overbuy_waste_stems'] = ol['waste_stems']; out['overbuy_waste_cost'] = R2(ol['waste_stems'] * ol['cost_stem'])
    inv = [v for v in _W1()['invoices'] if v['_story']]; ids = _cid()
    out['overdue_account'] = STORY_ACCOUNT; out['overdue_client_id'] = ids[STORY_ACCOUNT]; out['overdue_invoices'] = [v['invoice_id'] for v in inv]
    out['overdue_balance'] = R2(sum(v['amount'] - v['paid_amount'] for v in inv)); out['overdue_days'] = (TODAY - inv[0]['due_date']).days
    rn = [z for z in _W3()['rentals'] if z['returned_on'] == '' and z['status'] == 'Out' and z['due_back'] < TODAY - day(5)][0]
    out['unreturned_rental'] = rn['rental_id']; out['unreturned_item'] = rn['item']; out['unreturned_client'] = rn['client']; out['unreturned_due'] = iso(rn['due_back'])
    out['unreturned_days'] = (TODAY - rn['due_back']).days; out['unreturned_deposit'] = rn['deposit_held']
    zp = zone_profit(STORY_ZONE); out['losing_zone'] = STORY_ZONE; out['losing_zone_fee'] = ZN[STORY_ZONE]['fee']; out['losing_zone_cost'] = ZN[STORY_ZONE]['cost']
    out['losing_zone_profit'] = zp['profit']; out['losing_zone_deliveries'] = zp['deliveries']
    so = [s for s in _W1()['standing'] if s['client'] == STORY_STANDING_ACCOUNT][0]; mg, cost = standing_margin(so['standing_id'])
    out['undercosted_standing'] = so['standing_id']; out['undercosted_account'] = STORY_STANDING_ACCOUNT; out['undercosted_price'] = so['price']; out['undercosted_margin'] = mg; out['undercosted_cost'] = cost
    return out


_GENS = ['client_rows', 'order_rows', 'standing_order_rows', 'invoice_rows', 'enquiry_rows', 'consultation_rows', 'proposal_rows', 'proposal_line_rows', 'revision_rows', 'change_rows', 'event_result_rows',
         'event_day_rows', 'review_rows', 'rental_rows', 'helper_rows', 'payment_rows', 'wholesale_order_rows', 'wholesale_line_rows', 'waste_rows', 'stock_rows', 'substitution_rows', 'delivery_rows',
         'supply_month_rows', 'pay_rows', 'marketing_rows', 'expense_rows', 'type_month_rows', 'pnl_rows', 'tax_rows', 'cash_rows', 'holiday_rows', 'holiday_day_rows']
_IDS = {'client_rows': 'client_id', 'order_rows': 'order_id', 'standing_order_rows': 'standing_id', 'invoice_rows': 'invoice_id', 'enquiry_rows': 'enquiry_id', 'consultation_rows': 'consult_id',
        'proposal_rows': 'proposal_id', 'proposal_line_rows': 'line_id', 'revision_rows': 'revision_id', 'change_rows': 'change_id', 'event_result_rows': 'result_id', 'event_day_rows': 'day_id',
        'review_rows': 'review_id', 'rental_rows': 'rental_id', 'helper_rows': 'helper_id', 'payment_rows': 'payment_id', 'wholesale_order_rows': 'order_id', 'wholesale_line_rows': 'line_id',
        'waste_rows': 'waste_id', 'stock_rows': 'lot_id', 'substitution_rows': 'sub_id', 'delivery_rows': 'delivery_id', 'supply_month_rows': 'row_id', 'pay_rows': 'pay_id', 'marketing_rows': 'campaign_id',
        'expense_rows': 'expense_id', 'type_month_rows': 'row_id', 'pnl_rows': 'row_id', 'tax_rows': 'tax_id', 'cash_rows': 'row_id', 'holiday_rows': 'holiday_id', 'holiday_day_rows': 'day_id'}
# date columns checked for "rows in the current month and the last 30 days"
_DATECOL = {'order_rows': 'needed_on', 'enquiry_rows': 'date', 'consultation_rows': 'date', 'proposal_rows': 'sent_on', 'revision_rows': 'date', 'review_rows': 'asked_on', 'rental_rows': 'date_out',
            'helper_rows': 'date', 'payment_rows': 'date', 'wholesale_order_rows': 'date', 'wholesale_line_rows': 'date', 'waste_rows': 'date', 'substitution_rows': 'date', 'delivery_rows': 'date',
            'expense_rows': 'date', 'invoice_rows': 'issued_on', 'event_result_rows': 'event_date', 'event_day_rows': 'date', 'change_rows': 'date', 'stock_rows': 'received'}


def _digest():
    h = hashlib.md5()
    for nm in _GENS: h.update(repr(globals()[nm]()).encode())
    return h.hexdigest()[:12]


if __name__ == '__main__':
    import time
    t0 = time.time(); S = story(); G = {nm: globals()[nm]() for nm in _GENS}
    print('team', len(team), 'flowers', len(flowers), 'supplies', len(supplies), 'recipes', len(recipes), 'recipe_lines', len(recipe_lines), 'zones', len(zones), 'rental_items', len(rental_items),
          'venues', len(venues), 'suppliers', len(suppliers))
    print(' '.join('%s %d' % (nm.replace('_rows', ''), len(v)) for nm, v in G.items()))
    for nm, k in _IDS.items(): assert len({x[k] for x in G[nm]}) == len(G[nm]), nm
    assert len({c['client'] for c in G['client_rows']}) == len(G['client_rows']), 'client names unique'
    m0 = iso(_ms(TODAY)); d30 = ago(30)
    for nm, col in _DATECOL.items():
        rows = [x for x in G[nm] if x[col]]
        cm = sum(1 for x in rows if m0 <= x[col] <= iso(TODAY)); l30 = sum(1 for x in rows if d30 <= x[col] <= iso(TODAY))
        print('  %-22s %-12s this month %4d  last 30 days %4d' % (nm, col, cm, l30)); assert cm > 0 and l30 > 0, (nm, col)
    chk = [('client_rows', 'client_type', CLIENT_TYPES), ('order_rows', 'order_type', ORDER_TYPES), ('order_rows', 'kind', ORDER_KINDS), ('order_rows', 'status', ORDER_STATUS), ('order_rows', 'recipe', PRODUCTS), ('proposal_line_rows', 'recipe', EVENT_RECIPES),
           ('order_rows', 'zone', ZONES + ['']), ('order_rows', 'pay_method', ORDER_PAY), ('enquiry_rows', 'status', ENQUIRY_STATUS), ('enquiry_rows', 'source', ENQUIRY_SOURCES), ('enquiry_rows', 'event_type', EVENT_TYPES),
           ('enquiry_rows', 'lost_reason', LOST_REASONS + ['']), ('enquiry_rows', 'venue', VENUE_NAMES + ['']), ('consultation_rows', 'kind', CONSULT_KINDS), ('proposal_rows', 'status', PROPOSAL_STATUS),
           ('proposal_line_rows', 'section', SECTIONS[:4]), ('proposal_rows', 'zone', ZONES), ('payment_rows', 'kind', PAYMENT_KINDS), ('payment_rows', 'method', PAYMENT_METHODS), ('invoice_rows', 'status', INVOICE_STATUS),
           ('standing_order_rows', 'frequency', STANDING_FREQ), ('standing_order_rows', 'status', STANDING_STATUS), ('waste_rows', 'cause', WASTE_CAUSES), ('substitution_rows', 'reason', SUB_REASONS),
           ('delivery_rows', 'status', DELIVERY_STATUS), ('delivery_rows', 'window', DELIVERY_WINDOWS), ('delivery_rows', 'zone', ZONES), ('rental_rows', 'item', RENTAL_ITEMS), ('rental_rows', 'status', RENTAL_STATUS),
           ('helper_rows', 'kind', HELPER_KINDS), ('helper_rows', 'person', FREELANCERS), ('pay_rows', 'status', PAY_STATUS), ('pay_rows', 'person', PAID_STAFF), ('expense_rows', 'category', EXPENSE_CATEGORIES),
           ('marketing_rows', 'kind', MARKETING_KINDS), ('change_rows', 'kind', CHANGE_KINDS), ('type_month_rows', 'type', TYPES), ('holiday_rows', 'holiday', HOLIDAYS), ('wholesale_order_rows', 'supplier', SUPPLIERS[:3]),
           ('wholesale_order_rows', 'kind', ['Weekly', 'Event']), ('wholesale_line_rows', 'flower_class', FLOWER_CLASSES[:4]), ('waste_rows', 'variety', [f['variety'] for f in flowers]),
           ('tax_rows', 'status', TAX_STATUS[::2]), ('team', 'role', ROLES), ('team', 'team', TEAMS), ('team', 'pay_type', PAY_TYPES), ('review_rows', 'event_type', EVENT_TYPES)]
    for nm, col, vals in chk:
        src = team if nm == 'team' else G[nm]; got = {x[col] for x in src}; miss = [v for v in vals if v not in got]
        if miss: print('  unused values', nm, col, miss)
    print(S)
    print('seconds %.1f digest %s' % (time.time() - t0, _digest()))
