"""Home Management suite part 2 (Pantry, Freezer and Leftovers): label lists shared by data, tables, tools and the main file."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ho_core import *
from lib import L, LV


def P(labels):
    out, seen = [], set()
    for k, l in pairs(labels):
        k = {'g': 'gram', 'l': 'litre'}.get(k, k)
        if not k[:1].isalpha(): k = 'n' + k
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


WEEKS8 = ['Week %d' % i for i in range(1, 9)]
FSTATUS = ['ok', 'use soon', 'past date', 'finished']
INPLAN = ['In the plan', 'Not in the plan']
SFLAG = ['Close to typical', 'Typed earlier than typical', 'Typed later than typical', 'No date typed']
DKIND = ['Soup', 'Stew or chilli', 'Curry', 'Pasta dish or sauce', 'Burgers and balls', 'Other']
CMP = ['Fewer than your own average', 'Typical for your own history', 'More than your own average']

# words that verdict sentences and status cells are built from (formulas never write a label as text: they point at these cells)
WORDS = [
    ('cook', 'Cook'), ('first', 'first'), ('of', 'of'), ('on_hand', 'ingredients on hand'), ('use', 'Use'), ('by', 'by'), ('use_check', 'Use or check'), ('items_today', 'items today'),
    ('defrost', 'Defrost'), ('portions', 'portions'), ('eat', 'Eat'), ('buy', 'Buy'), ('items_list', 'items for the list'), ('use_soon_at', 'items use soon at'), ('days', 'days'),
    ('covers', 'Stock covers'), ('dinners', 'dinners,'), ('topup', 'need a top-up'), ('freeze', 'freeze'), ('oldest', 'Oldest first:'), ('months', 'months'),
    ('check_clear', 'Check and clear'), ('items', 'items'), ('missing_only', 'Missing only'), ('for', 'for'), ('best_fit', 'Best fit:'), ('of3', 'of 3 items'),
    ('adjust', 'Adjust'), ('units', 'units'), ('room_for', 'Room for'),
    ('over_by', 'Over by'), ('use_freeze', 'Use or freeze'), ('before_leaving', 'before leaving'), ('busiest', 'Busiest day'), ('no_fit', 'No recipe reaches the share'),
    ('no_dish', 'No dish has that many portions'), ('nothing_due', 'Nothing due'), ('cook_this', 'Cook this first'), ('ready', 'Ready to cook'), ('one_missing', 'One ingredient missing'),
    ('shopping', 'Needs shopping'), ('as_it_is', 'Eat as it is'), ('plan_it', 'Plan it'), ('fine', 'Fine as it is'), ('clear', 'Check and clear'), ('use_today', 'Use today'),
    ('next_item', 'Next in line'), ('no_leftover', 'No leftovers to plan'), ('no_missing', 'No recipe is one item short'), ('no_match', 'No recipe uses these items'),
    ('is_full', 'Over the typed space'), ('space_left', 'Space left'), ('nothing_past', 'Nothing past the date'), ('cooked_dish', 'Cooked dish'), ('hold', 'Hold'),
    ('portion', 'portion'), ('left', 'left'), ('no_freezer', 'No freezer item'), ('in_window', 'in the window'), ('no_recipe', 'No recipe uses it'),
]
assert len({k for k, _ in WORDS}) == len(WORDS)
_W = {}
_VW = WORDS[:30]; _VX = WORDS[30:60]
assert len(WORDS) <= 60
for k, _ in _VW: _W[k] = 'vw'
for k, _ in _VX: _W[k] = 'vx'


def W(k): return '{list:%s.%s}' % (_W[k], k)


MONTHS = MONTH_NAMES

lists = [
    L('role', 'Role', P(ROLES)), L('tgroup', 'Team group', P(TEAM_GROUPS)), L('rcat', 'Recipe category', P(RECIPE_CATS)), L('pref', 'Preference label', P(PREF_LABELS)),
    L('place', 'Storage place', P(STORAGE_PLACES)), L('unit', 'Unit', P(UNITS)), L('section', 'Shop section', P(SECTIONS)), L('shop', 'Shop', P(SHOPS)),
    L('slot', 'Meal slot', P(MEAL_SLOTS)), L('person', 'Person', P(PERSONS)), L('fstatus', 'Food status', P(FSTATUS)), L('wk', 'Week ahead', P(WEEKS8)),
    L('sflag', 'Shelf check', P(SFLAG)), L('inplan', 'In the plan', P(INPLAN)), L('cmp', 'Against own history', P(CMP)), L('mon', 'Month name', P(MONTHS)),
    L('wday', 'Weekday', P(WEEKDAYS)), L('dkind', 'Dish kind', P(DKIND)), L('vw', 'Verdict words A', _VW), L('vx', 'Verdict words B', _VX),
]
assert len(lists) <= 20
_M = {'role': K(ROLES), 'tgroup': K(TEAM_GROUPS), 'rcat': K(RECIPE_CATS), 'pref': K(PREF_LABELS), 'place': K(STORAGE_PLACES), 'unit': K(UNITS), 'section': K(SECTIONS), 'shop': K(SHOPS),
      'slot': K(MEAL_SLOTS), 'person': K(PERSONS), 'fstatus': K(FSTATUS), 'wk': K(WEEKS8), 'sflag': K(SFLAG), 'inplan': K(INPLAN), 'cmp': K(CMP), 'mon': K(MONTHS), 'wday': K(WEEKDAYS), 'dkind': K(DKIND)}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def MT(i): return LV('mon', _M['mon'][MONTHS[i]])


OK, SOON, PAST, FIN = (tok('fstatus', x) for x in FSTATUS)
IN_PLAN, NOT_PLAN = tok('inplan', 'In the plan'), tok('inplan', 'Not in the plan')
FRIDGE, PANTRY, FREEZER = tok('place', 'Fridge'), tok('place', 'Pantry'), tok('place', 'Chest freezer')
PORTION = tok('unit', 'portion')
DINNER = tok('slot', 'Dinner')
YES = '{list:yesno.yes}'
