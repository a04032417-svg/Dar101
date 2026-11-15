"""Car rental suite part 3 (Handover, Return, Fees and Damage): label lists shared by data, tables and tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cr_core import *
from lib import L, LV


def P(labels):
    out, seen = [], set()
    for k, l in pairs(labels):
        if not k[:1].isalpha(): k = 'n' + k
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


HANDLERS = ['Tomas Kowalski', 'Sana Malik', 'Jun Park', 'Nadia Haddad']
SEGKINDS = ['Class', 'Channel', 'Plan', 'Young driver', 'Cover option']
# check results shown by calculated status columns
CKA = ['Complete', 'Checks missing', 'Open claim', 'Closed claim', 'Chase', 'Wait', 'Pass on', 'Already passed on', 'Absorbed', 'No rental found', 'Check overlap', 'Go',
       'Hold, documents due', 'No-go', 'Above your usual', 'On your usual', 'Below your usual', 'Ask a larger deposit', 'Keep the deposit', 'Still on the road', 'Fee billed',
       'Fee not billed', 'Fee collected', 'Fee written off']
# verdicts of the tools
CK2 = ['Fees due', 'No fee', 'Complete, release the car', 'Checks missing, do not release', 'Bill the late fee', 'Inside the grace', 'Allowance generous', 'Allowance fair',
       'Allowance tight', 'Fee covers the cost', 'Raise the step fee', 'Chase the open fees', 'Chase and review write-offs', 'Nothing to chase', 'Bill the fees now', 'Nothing missed',
       'Chase the claim', 'Wait for the repair', 'Close the claim', 'Chase the first claim', 'No open claim', 'Above your usual', 'On your usual', 'Below your usual',
       'Ask a larger deposit', 'No segment stands out', 'Raise the deposit', 'Keep the deposit', 'Promote cover', 'Cover is neutral']
CK3 = ['Pass on', 'Handled by the renter', 'No rental found', 'Fee covers the work', 'Raise the fee', 'Go', 'Hold, documents due', 'No-go', 'Recovery low, tighten terms',
       'Recovery is fine', 'Retrain', 'On target', 'Hand over the car', 'Ask for the documents', 'Do not rent', 'Add the young-driver fee', 'No extra fee']
assert len(CKA) <= 30 and len(CK2) <= 30 and len(CK3) <= 30

lists = [
    L('class', 'Vehicle class', P(CLASSES)), L('channel', 'Channel', P(CHANNELS)), L('plan', 'Plan', P(PLANS)), L('fuel', 'Fuel type', P(FUELS)), L('vstatus', 'Vehicle status', P(VEH_STATUS)),
    L('feekind', 'Fee kind', P(FEE_KINDS)), L('feestatus', 'Fee status', P(FEE_STATUS)), L('claimkind', 'Claim kind', P(CLAIM_KINDS)), L('claimstatus', 'Claim status', P(CLAIM_STATUS)),
    L('tollkind', 'Toll or ticket kind', P(TOLL_KINDS)), L('tollstatus', 'Toll or ticket status', P(TOLL_STATUS)), L('rstatus', 'Renter status', P(RENTER_STATUS)), L('ageband', 'Age band', P(AGE_BANDS)),
    L('bstatus', 'Booking status', P(BOOK_STATUS)), L('handler', 'Handled by', P(HANDLERS)), L('segkind', 'Segment kind', P(SEGKINDS)),
    L('cka', 'Check result', P(CKA)), L('ck2', 'Verdict A', P(CK2)), L('ck3', 'Verdict B', P(CK3)),
]
assert len(lists) <= 20
_M = {'class': K(CLASSES), 'channel': K(CHANNELS), 'plan': K(PLANS), 'fuel': K(FUELS), 'vstatus': K(VEH_STATUS), 'feekind': K(FEE_KINDS), 'feestatus': K(FEE_STATUS), 'claimkind': K(CLAIM_KINDS),
      'claimstatus': K(CLAIM_STATUS), 'tollkind': K(TOLL_KINDS), 'tollstatus': K(TOLL_STATUS), 'rstatus': K(RENTER_STATUS), 'ageband': K(AGE_BANDS), 'bstatus': K(BOOK_STATUS),
      'handler': K(HANDLERS), 'segkind': K(SEGKINDS), 'cka': K(CKA), 'ck2': K(CK2), 'ck3': K(CK3)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def ca(label): return tok('cka', label)
def c2(label): return tok('ck2', label)
def c3(label): return tok('ck3', label)
