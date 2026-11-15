"""Short-term rental host suite part 6: the 14 calculators."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr6_lists import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
YES = tok('yn', 'Yes')
GRADE = None

# 1 rating impact
PTS1 = '(5*{in:n5}+4*{in:n4}+3*{in:n3}+2*{in:n2}+{in:n1})'; TOT1 = '({in:n5}+{in:n4}+{in:n3}+{in:n2}+{in:n1})'; AVG1 = '(%s/%s)' % (PTS1, TOT1)
# 2 reply helper
OPEN2 = 'IF({in:rating}>=5,%s,IF({in:rating}=4,%s,IF({in:rating}=3,%s,%s)))' % (cs('Thank you for your five-star review.'), cs('Thank you for your kind review.'),
                                                                               cs('Thank you for your honest review.'), cs('We are sorry your stay fell short.'))
TOPIC2 = {'Cleanliness': 'We shared your note on cleanliness.', 'Check-in': 'We are reviewing our check-in steps.',
          'Noise': 'We will share quiet hours more clearly.', 'Comfort': 'We will check the beds and furniture.',
          'Location': 'We will clarify the location text.', 'Value': 'We are reviewing our prices and extras.',
          'Host communication': 'We shared your note on our messages.', 'Amenities': 'We will add missing amenities.'}
def TOPICF(sel):
    f = cs(TOPIC2['Amenities'])
    for t in reversed(REVIEW_TOPICS[:-1]):
        f = 'IF(%s={list:rtopic.%s},%s,%s)' % (sel, key('rtopic', t), cs(TOPIC2[t]), f)
    return f
TOPIC2F = TOPICF('{in:topic}')
CLOSE2 = 'IF({in:rating}>=4,%s,%s)' % (cs('We would be happy to host you again.'), cs('We hope to put this right next time.'))
# 3 response time
MIN3 = 'ROUND(IF({in:replied}<{in:received},{in:replied}+24-{in:received},{in:replied}-{in:received})*60,0)'
# 4 complaint planner
SEV4 = 'IF({in:severity}=%s,{set:comp_serious},IF({in:severity}=%s,{set:comp_moderate},0))' % (tok('sev', 'Serious'), tok('sev', 'Moderate'))
ACT4 = 'IF({in:severity}=%s,IF({in:nights_left}>=2,%s,%s),IF({in:severity}=%s,IF({in:nights_left}<=1,%s,%s),IF({in:topic}=%s,%s,%s)))' % (
    tok('sev', 'Serious'), tok('cact', 'Moved to another unit'), tok('cact', 'Partial refund'), tok('sev', 'Moderate'), tok('cact', 'Partial refund'), tok('cact', 'Credit for next stay'),
    tok('rtopic', 'Cleanliness'), tok('cact', 'Fixed on site'), tok('cact', 'Apology'))
# 5 compensation
REF5 = '({in:nights}*{in:adr}*IF({in:severity}=%s,{set:comp_serious},IF({in:severity}=%s,{set:comp_moderate},0.05))+{in:extra})' % (tok('sev', 'Serious'), tok('sev', 'Moderate'))
# 6 check-in message
ACC6 = 'IF({in:method}=%s,%s,IF({in:method}=%s,%s,IF({in:method}=%s,%s,%s)))' % (
    tok('amethod', 'Smart lock code'), cs('The door code comes on arrival day.'), tok('amethod', 'Key box'), cs('The key box code comes on arrival day.'),
    tok('amethod', 'Meeting in person'), cs('We will meet you at the door.'), cs('A neighbour will hand over the key.'))
MSG6 = '{in:guest}&", "&%s&" "&{in:unit}&" "&%s&" "&{in:time}&". "&%s' % (cs('welcome. Your stay at'), cs('starts with check-in from'), ACC6)
# 7 repeat guest
SPY7 = '({in:stays}/MAX(0.5,({today}-{in:first})/365))'
OFF7 = 'IF({in:stays}>=5,0.15,IF({in:stays}>=3,0.1,IF({in:stays}>=2,0.05,0)))'
# 9 rating gap
NEWAVG9 = '(5*{in:share5}+4*(1-{in:share5}))'
NEED9 = 'IF(%s>{in:target},ROUNDUP({in:count}*({in:target}-{in:avg})/(%s-{in:target}),0),0)' % (NEWAVG9, NEWAVG9)
# 10 topic scoreboard
TK = [('Cleanliness', 't1', 4.4), ('Check-in', 't2', 4.5), ('Noise', 't3', 4.3), ('Comfort', 't4', 4.6), ('Location', 't5', 4.8), ('Value', 't6', 4.6), ('Host communication', 't7', 4.7), ('Amenities', 't8', 4.5)]
MINT = 'MIN(' + ','.join('{in:%s}' % k for _, k, _ in TK) + ')'; MAXT = 'MAX(' + ','.join('{in:%s}' % k for _, k, _ in TK) + ')'
def NAMEOF(target):
    f = tok('rtopic', TK[-1][0])
    for t, k, _ in reversed(TK[:-1]): f = 'IF({in:%s}=%s,%s,%s)' % (k, target, tok('rtopic', t), f)
    return f
FIX10 = {'Cleanliness': 'Add a photo checklist to each turnover.', 'Check-in': 'Test the lock code and send clear steps.',
         'Noise': 'Add quiet hours to the welcome text.', 'Comfort': 'Replace tired pillows and chairs.',
         'Location': 'Describe the walk to transport honestly.', 'Value': 'Check your rate against similar units.',
         'Host communication': 'Reply within target and use templates.', 'Amenities': 'Restock the amenities guests ask for.'}
def FIXF():
    f = cs(FIX10[TK[-1][0]])
    for t, k, _ in reversed(TK[:-1]): f = 'IF({in:%s}=%s,%s,%s)' % (k, MINT, cs(FIX10[t]), f)
    return f
# 11 early late
SPARE11 = '({in:gap}-{in:hours}-{in:clean})'; FEE11 = 'ROUND(MAX(0,{in:hours}-{set:free_hours})*{in:rate}*{set:hour_share},0)'
# 12 satisfaction
RP12 = '40*MIN(1,MAX(0,({in:rating}-3)/2))'; SP12 = '20*MAX(0,1-{in:minutes}/(4*{set:response_target_min}))'; CP12 = '20*MAX(0,1-{in:complaints}/20)'; RE12 = '10*MIN(1,{in:repeat}/0.5)'; SV12 = '10*MIN(1,{in:survey}/10)'
TOT12 = '(%s+%s+%s+%s+%s)' % (RP12, SP12, CP12, RE12, SV12)
# 14 what-if
PT14 = '({in:avg}*{in:count}+5*{in:n5}+4*{in:n4}+{in:n1})'; CT14 = '({in:count}+{in:n5}+{in:n4}+{in:n1})'

tools = [
    TOOL('rating_impact', 'Rating Impact', 'Average rating and the effect of one more review',
         'Type how many reviews you have at each star level and a target; see the average, the five-star share, the five-star reviews needed to reach the target and the cost of one bad review.', [
        I('n5', 'Reviews with 5 stars', 210, 'int'), I('n4', 'Reviews with 4 stars', 70, 'int'), I('n3', 'Reviews with 3 stars', 12, 'int'), I('n2', 'Reviews with 2 stars', 6, 'int'), I('n1', 'Reviews with 1 star', 3, 'int'),
        I('target', 'Wanted average rating', 4.6, 'num')], [
        O('Reviews counted', 'int', TOT1), O('Average rating', 'num', 'ROUND(%s,2)' % AVG1), O('Five-star share', 'pct', '{in:n5}/%s' % TOT1), O('Share of 3 stars or less', 'pct', '({in:n3}+{in:n2}+{in:n1})/%s' % TOT1),
        O('Gap to the wanted average', 'num', 'ROUND(%s-{in:target},2)' % AVG1),
        O('Five-star reviews needed to reach the wanted average', 'int', 'IF(%s>={in:target},0,ROUNDUP(({in:target}*%s-%s)/(5-{in:target}),0))' % (AVG1, TOT1, PTS1)),
        O('Average lost by one new 1-star review', 'num', 'ROUND(%s-(%s+1)/(%s+1),3)' % (AVG1, PTS1, TOT1)),
        O('Five-star reviews needed to cancel one 1-star review', 'int', 'ROUNDUP((%s*(%s+1)-%s-1)/(5-%s),0)' % (AVG1, TOT1, PTS1, AVG1)),
        O('Verdict', 'text', 'IF(%s>={in:target},%s,%s)' % (AVG1, ck2('Above the wanted rating'), ck2('Below the wanted rating')))],
         GR('What if', ('One more 1-star review', {'n1': 4}), ('Ten more 5-star reviews', {'n5': 220}), ('Five more 3-star reviews', {'n3': 17}), ('Strong month, 20 five-star reviews', {'n5': 230}),
            ('Weak month, 4 reviews of 2 stars', {'n2': 10, 'n3': 15}))),
    TOOL('reply_helper', 'Review Reply Helper', 'Review reply draft by rating and topic',
         'Type the rating, the topic and the guest name; see the tone to use, the opening, the topic line, the closing and a full reply draft to copy and adapt.', [
        I('rating', 'Rating of the review', 5, 'int'), IN('topic', 'Main topic of the review', 'list', key('rtopic', 'Cleanliness'), list='rtopic'), I('name', 'Guest name', 'Maya', 'text')], [
        O('Tone to use', 'text', 'IF({in:rating}>=5,%s,IF({in:rating}=4,%s,IF({in:rating}=3,%s,%s)))' % (ck2('Warm thanks'), ck2('Thanks and a tip'), ck2('Honest apology and fix'), ck2('Apology and a call'))),
        O('Opening sentence', 'text', OPEN2), O('Topic sentence', 'text', TOPIC2F), O('Closing sentence', 'text', CLOSE2), O('Full reply draft', 'text', '{in:name}&", "&%s&" "&%s&" "&%s' % (OPEN2, TOPIC2F, CLOSE2)),
        O('Wanted length in words', 'int', 'IF({in:rating}>=5,40,IF({in:rating}=4,70,110))'), O('Days allowed to reply', 'int', '{set:reply_days}'),
        O('Reviews still waiting in your log', 'int', 'COUNTIFS({range:reviews.replied},%s)' % tok('yn', 'No'))],
         GR('What if', ('Five stars', {'rating': 5}), ('Four stars', {'rating': 4}), ('Three stars', {'rating': 3}), ('Two stars', {'rating': 2}), ('One star', {'rating': 1}))),
    TOOL('response_time', 'Response Time Check', 'Reply time against your target',
         'Type when the guest wrote and when you replied (as hours, 14.5 is 14:30), the target and this week\'s messages; see the minutes, on time or late, and the share answered on time.', [
        I('received', 'Guest wrote at hour of the day', 14.5, 'num'), I('replied', 'You replied at hour of the day', 15.1, 'num'), I('target', 'Target in minutes', 30, 'int'), I('messages', 'Messages this week', 120, 'int'),
        I('on_time', 'Answered within the target this week', 96, 'int')], [
        O('Minutes to reply', 'int', MIN3), O('Minutes over the target', 'int', 'MAX(0,%s-{in:target})' % MIN3),
        O('Verdict', 'text', 'IF(%s<={in:target},%s,%s)' % (MIN3, ck2('Reply on time'), ck2('Reply was late'))),
        O('Share answered in time this week', 'pct', 'IFERROR({in:on_time}/{in:messages},0)'), O('Messages answered late', 'int', '{in:messages}-{in:on_time}'),
        O('Extra replies in time to reach 90 percent', 'int', 'MAX(0,ROUNDUP(0.9*{in:messages}-{in:on_time},0))'),
        O('Average reply minutes in your log, 90 days', 'int', 'IFERROR(AVERAGEIFS({range:gmsg.response_min},{range:gmsg.date},">="&({today}-90)),0)'),
        O('Share within the target in your log, 90 days', 'pct', 'IFERROR(COUNTIFS({range:gmsg.reply_flag},%s,{range:gmsg.date},">="&({today}-90))/COUNTIFS({range:gmsg.date},">="&({today}-90)),0)' % ca('Within target'))],
         GR('What if', ('Fast reply, 10 minutes', {'replied': 14.67}), ('Slow reply, one hour', {'replied': 15.5}), ('Reply after midnight', {'received': 23.5, 'replied': 0.5}), ('Target 15 minutes', {'target': 15}),
            ('Only 70 answered in time', {'on_time': 70}))),
    TOOL('complaint_planner', 'Complaint Planner', 'Action and compensation for a complaint',
         'Type the topic, the severity, the nights left in the stay, the nights affected and the nightly rate; see the action to take, the share to give back, the compensation and the hours to answer.', [
        IN('topic', 'Topic of the complaint', 'list', key('rtopic', 'Cleanliness'), list='rtopic'), IN('severity', 'Severity', 'list', key('sev', 'Moderate'), list='sev'), I('nights_left', 'Nights left in the stay', 3, 'int'),
        I('nights_hit', 'Nights affected', 1, 'int'), I('rate', 'Nightly rate', 140)], [
        O('Action to take', 'text', ACT4), O('Share of the affected nights to give back', 'pct', SEV4), O('Compensation', 'money', '%s*{in:nights_hit}*{in:rate}' % SEV4),
        O('Compensation per night of the stay left', 'money', 'IFERROR(%s*{in:nights_hit}*{in:rate}/{in:nights_left},0)' % SEV4), O('Hours to answer the guest', 'int', 'IF({in:severity}=%s,2,IF({in:severity}=%s,6,24))' % (tok('sev', 'Serious'), tok('sev', 'Moderate'))),
        O('Value of the nights left', 'money', '{in:nights_left}*{in:rate}'), O('Compensation as share of the nights left', 'pct', 'IFERROR(%s*{in:nights_hit}*{in:rate}/({in:nights_left}*{in:rate}),0)' % SEV4),
        O('Complaints still open in your log', 'int', 'COUNTIFS({range:complaints.status},%s)+COUNTIFS({range:complaints.status},%s)' % (ca('Open'), ca('Open and late')))],
         GR('What if', ('Serious complaint', {'severity': '=' + tok('sev', 'Serious')}), ('Two nights affected', {'nights_hit': 2}), ('Last night of the stay', {'nights_left': 1}), ('Premium unit, rate 220', {'rate': 220}),
            ('Long stay, 6 nights left', {'nights_left': 6, 'nights_hit': 3}))),
    TOOL('compensation_calc', 'Compensation Calculator', 'Refund or credit for a bad experience',
         'Type the nights affected, the average nightly price, the severity and any goodwill extra; see the refund, the credit, what the host loses and the better choice.', [
        I('nights', 'Nights affected', 1, 'num'), I('adr', 'Average price of a night sold', 140), IN('severity', 'Severity', 'list', key('sev', 'Moderate'), list='sev'), I('fee', 'Platform fee', 0.14, 'pct'), I('extra', 'Goodwill extra', 0)], [
        O('Refund amount', 'money', 'ROUND(%s,0)' % REF5), O('Credit for the next stay', 'money', 'ROUND(%s*1.25,0)' % REF5), O('Refund as share of the affected nights', 'pct', 'IFERROR(%s/({in:nights}*{in:adr}),0)' % REF5),
        O('Income lost if the platform returns its fee', 'money', 'ROUND(%s*(1-{in:fee}),0)' % REF5), O('Credit in nights of the next stay', 'num', 'ROUND(%s*1.25/{in:adr},1)' % REF5),
        O('Better choice', 'text', 'IF({in:severity}=%s,%s,%s)' % (tok('sev', 'Serious'), ck2('Refund the amount'), ck2('Offer a credit for the next stay'))),
        O('Compensation given in your log this year', 'money', 'SUMIFS({range:complaints.compensation},{range:complaints.date},">="&DATE(YEAR({today}),1,1))')],
         GR('What if', ('Serious, two nights', {'nights': 2, 'severity': '=' + tok('sev', 'Serious')}), ('Half a night affected', {'nights': 0.5}), ('Add a goodwill 20', {'extra': 20}), ('Premium unit, price 220', {'adr': 220}), ('Direct booking, fee 3 percent', {'fee': 0.03}))),
    TOOL('checkin_builder', 'Check-in Message Builder', 'Check-in text to send to a guest',
         'Type the unit, the guest, the check-in time, the way the guest gets in and the date; see the text to send, when to send it and whether it fits one message.', [
        I('unit', 'Unit', 'Chiado Loft', 'text'), I('guest', 'Guest name', 'Maya', 'text'), I('time', 'Check-in time', '15:00', 'text'), IN('method', 'Way to get in', 'list', key('amethod', 'Smart lock code'), list='amethod'),
        IN('date', 'Check-in date', 'date', 'today+3')], [
        O('Message to send', 'text', MSG6), O('Access sentence', 'text', ACC6), O('Check-in date', 'date', '{in:date}'), O('Send on', 'date', '{in:date}-1'),
        O('Usual check-in time', 'text', '{set:checkin_time}'),
        O('Check-ins with an issue in your log', 'int', 'COUNTIFS({range:checkins.issue_flag},%s)' % ca('Issue at check-in'))],
         GR('What if', ('Key box', {'method': '=' + tok('amethod', 'Key box')}), ('Meeting in person', {'method': '=' + tok('amethod', 'Meeting in person')}), ('Neighbour handover', {'method': '=' + tok('amethod', 'Neighbour handover')}), ('Check-in in 7 days', {'date': '={today}+7'}))),
    TOOL('repeat_value', 'Repeat Guest Value', 'Lifetime value and offer for a returning guest',
         'Type the stays, the spend, the first and last stay and the platform fee saved on a direct booking; see the value per stay, the expected year, the offer to make and whether to send it now.', [
        I('stays', 'Stays so far', 3, 'int'), I('spend', 'Total spend', 1450), IN('first', 'First stay', 'date', 'today-500'), IN('last', 'Last stay', 'date', 'today-200'), I('fee', 'Platform fee saved on a direct booking', 0.14, 'pct')], [
        O('Spend per stay', 'money', 'IFERROR({in:spend}/{in:stays},0)'), O('Days since the last stay', 'int', '{today}-{in:last}'), O('Stays per year', 'num', 'ROUND(%s,1)' % SPY7),
        O('Expected spend, next 12 months', 'money', '%s*{in:spend}/{in:stays}' % SPY7), O('Offer to make', 'pct', OFF7), O('Cost of the offer on the next stay', 'money', '%s*{in:spend}/{in:stays}' % OFF7),
        O('Platform fee saved if the stay is direct', 'money', '{in:fee}*{in:spend}/{in:stays}'), O('Net gain of a direct stay with the offer', 'money', '({in:fee}-%s)*{in:spend}/{in:stays}' % OFF7),
        O('Next step', 'text', 'IF({today}-{in:last}>={set:winback_days},%s,IF({in:stays}>=3,%s,%s))' % (ck2('Send the win-back offer now'), ck2('Keep in touch and ask for a referral'), ck2('Wait, the guest stayed recently')))],
         GR('What if', ('Five stays', {'stays': 5, 'spend': 2600}), ('One stay only', {'stays': 1, 'spend': 480}), ('Last stay 30 days ago', {'last': '={today}-30'}), ('High spender', {'spend': 4200}), ('Fee 3 percent', {'fee': 0.03}))),
    TOOL('review_timing', 'Review Request Timing', 'Best day to ask a guest for a review',
         'Type the checkout date, how long guests take to review and how many of 10 asked do; see the best day to ask, the reminder date and the last useful day, with the figures from your own log.', [
        IN('checkout', 'Check-out date', 'date', 'today-1'), I('avg_days', 'Average days a guest takes to review', 2.5, 'num'), I('reviewed', 'Guests who review, out of 10 asked', 6, 'int')], [
        O('Best day to ask', 'date', '{in:checkout}+IF({in:avg_days}<=1,0,IF({in:avg_days}<=3,1,2))'), O('Reminder on', 'date', '{in:checkout}+IF({in:avg_days}<=1,0,IF({in:avg_days}<=3,1,2))+3'),
        O('Last useful day to ask', 'date', '{in:checkout}+{set:review_window}'), O('Review rate', 'pct', '{in:reviewed}/10'), O('Reviews expected from the next 10 stays', 'int', '{in:reviewed}'),
        O('Verdict', 'text', 'IF({today}>{in:checkout}+{set:review_window},%s,IF({today}>={in:checkout}+IF({in:avg_days}<=1,0,IF({in:avg_days}<=3,1,2)),%s,%s))' % (ck2('Too late to ask'), ck2('Ask now'), ck2('Wait for the best day'))),
        O('Average days to review in your log', 'num', 'IFERROR(AVERAGE({range:revreq.days_to_review}),0)'), O('Review rate in your log', 'pct', 'IFERROR(SUM({range:revreq.reviewed_num})/COUNT({range:revreq.reviewed_num}),0)')],
         GR('What if', ('Guests review in a day', {'avg_days': 0.8}), ('Guests review in a week', {'avg_days': 7}), ('Weak review rate, 3 of 10', {'reviewed': 3}), ('Strong review rate, 8 of 10', {'reviewed': 8}))),
    TOOL('rating_gap', 'Rating Gap Calculator', 'New five-star reviews needed to reach the target',
         'Type the current average, the number of reviews, the wanted average, the reviews you get a month and the share of new reviews with 5 stars; see how many reviews and how many months it takes.', [
        I('avg', 'Current average rating', 4.52, 'num'), I('count', 'Reviews so far', 86, 'int'), I('target', 'Wanted average rating', 4.6, 'num'), I('monthly', 'New reviews a month', 12, 'int'), I('share5', 'Share of new reviews with 5 stars', 0.85, 'pct')], [
        O('Gap to the wanted average', 'num', 'ROUND({in:avg}-{in:target},2)'), O('Five-star reviews needed, if every new review has 5 stars', 'int', 'IF({in:avg}>={in:target},0,ROUNDUP({in:count}*({in:target}-{in:avg})/(5-{in:target}),0))'),
        O('Average of the new reviews at your mix', 'num', 'ROUND(%s,2)' % NEWAVG9), O('New reviews needed at your mix', 'int', NEED9), O('Months to reach the target at your mix', 'num', 'IFERROR(ROUND(%s/{in:monthly},1),0)' % NEED9),
        O('Months if every new review had 5 stars', 'num', 'IFERROR(ROUND(IF({in:avg}>={in:target},0,ROUNDUP({in:count}*({in:target}-{in:avg})/(5-{in:target}),0))/{in:monthly},1),0)'),
        O('Share of 5 stars needed in the next 12 months', 'pct', 'IFERROR(MIN(1,({in:target}*({in:count}+12*{in:monthly})-{in:avg}*{in:count}-4*12*{in:monthly})/(12*{in:monthly})),0)'),
        O('Verdict', 'text', 'IF({in:avg}>={in:target},%s,%s)' % (ck2('Above the wanted rating'), ck2('Below the wanted rating')))],
         GR('What if', ('Mix of 95 percent five stars', {'share5': 0.95}), ('Mix of 70 percent five stars', {'share5': 0.7}), ('Busy season, 25 reviews a month', {'monthly': 25}), ('Target 4.8', {'target': 4.8}), ('Many reviews, 300 so far', {'count': 300}))),
    TOOL('topic_scoreboard', 'Topic Scoreboard', 'Weakest review topic and the fix',
         'Type the average rating of each review topic; see the weakest and strongest topic, the gap to the minimum, how many topics fall below it and the fix for the weakest.', [
        I(k, 'Average rating, ' + t.lower(), d, 'num') for t, k, d in TK], [
        O('Weakest topic', 'text', NAMEOF(MINT)), O('Weakest topic rating', 'num', MINT), O('Fix for the weakest topic', 'text', FIXF()), O('Strongest topic', 'text', NAMEOF(MAXT)), O('Strongest topic rating', 'num', MAXT),
        O('Average of the topics', 'num', 'ROUND(AVERAGE(%s),2)' % ','.join('{in:%s}' % k for _, k, _ in TK)), O('Gap of the weakest topic to the minimum', 'num', 'ROUND(%s-{set:min_rating},2)' % MINT),
        O('Topics below the minimum', 'int', '+'.join('IF({in:%s}<{set:min_rating},1,0)' % k for _, k, _ in TK)),
        O('Reviews of 3 stars or less in your log', 'int', 'COUNTIFS({range:reviews.rating},"<="&{set:low_stars})')],
         GR('What if', ('Cleanliness drops to 3.9', {'t1': 3.9}), ('Noise drops to 3.8', {'t3': 3.8}), ('Check-in improves to 4.8', {'t2': 4.8}), ('All topics 4.6', {'t1': 4.6, 't2': 4.6, 't3': 4.6, 't4': 4.6, 't5': 4.6, 't6': 4.6, 't7': 4.6, 't8': 4.6}))),
    TOOL('early_late_pricing', 'Early and Late Pricing', 'Fee or free for an early check-in or late checkout',
         'Type the hours asked, the hours free between this stay and the next, the cleaner hours needed and the nightly rate; see the fee, the spare hours and whether to approve, charge or decline.', [
        I('hours', 'Hours asked', 2, 'num'), I('gap', 'Hours free before the next guest', 6, 'num'), I('clean', 'Cleaner hours needed in between', 2, 'num'), I('rate', 'Nightly rate', 140)], [
        O('Free hours', 'num', '{set:free_hours}'), O('Hours to charge', 'num', 'MAX(0,{in:hours}-{set:free_hours})'), O('Price of each extra hour', 'money', 'ROUND({in:rate}*{set:hour_share},0)'), O('Fee', 'money', FEE11),
        O('Fee as share of the night', 'pct', 'IFERROR(%s/{in:rate},0)' % FEE11), O('Spare hours after the clean', 'num', SPARE11),
        O('Verdict', 'text', 'IF(%s<0,%s,IF(%s=0,%s,%s))' % (SPARE11, ck2('Decline, the next guest arrives'), FEE11, ck2('Approve for free'), ck2('Approve with a fee'))),
        O('Fees charged in your log, last 90 days', 'money', 'SUMIFS({range:earlyout.fee},{range:earlyout.date},">="&({today}-90))')],
         GR('What if', ('One hour asked', {'hours': 1}), ('Four hours asked', {'hours': 4}), ('Same-day arrival, only 3 hours free', {'gap': 3}), ('Empty night after, 24 hours free', {'gap': 24}), ('Premium unit, rate 220', {'rate': 220}))),
    TOOL('satisfaction_score', 'Guest Satisfaction Score', 'One score for rating, replies, complaints and returns',
         'Type the 90-day rating, the average reply minutes, the complaints per 100 stays, the repeat share and the survey score; see a score out of 100 with each part and a verdict.', [
        I('rating', 'Average rating, 90 days', 4.6, 'num'), I('minutes', 'Average reply minutes', 35, 'int'), I('complaints', 'Complaints per 100 stays', 6, 'num'), I('repeat', 'Share of repeat guests', 0.45, 'pct'), I('survey', 'Average survey score out of 10', 8.7, 'num')], [
        O('Rating part, out of 40', 'num', 'ROUND(%s,1)' % RP12), O('Reply speed part, out of 20', 'num', 'ROUND(%s,1)' % SP12), O('Complaints part, out of 20', 'num', 'ROUND(%s,1)' % CP12), O('Repeat guests part, out of 10', 'num', 'ROUND(%s,1)' % RE12),
        O('Survey part, out of 10', 'num', 'ROUND(%s,1)' % SV12), O('Guest satisfaction score, out of 100', 'int', 'ROUND(%s,0)' % TOT12),
        O('Verdict', 'text', 'IF(%s>=85,%s,IF(%s>=70,%s,%s))' % (TOT12, ck2('Excellent guest experience'), TOT12, ck2('Good, with room to improve'), ck2('Needs attention'))),
        O('Rating wanted in the settings', 'num', '{set:target_rating}')],
         GR('What if', ('Faster replies, 15 minutes', {'minutes': 15}), ('Slow replies, 120 minutes', {'minutes': 120}), ('More complaints, 12 per 100', {'complaints': 12}), ('Rating falls to 4.2', {'rating': 4.2}), ('Loyal guests, repeat 60 percent', {'repeat': 0.6}))),
    TOOL('message_planner', 'Guest Message Planner', 'Dates of every message for one booking',
         'Type the check-in date and the nights; see the date for the confirmation, the arrival questions, the instructions, the stay checks, the checkout reminder and the review request.', [
        IN('check_in', 'Check-in date', 'date', 'today+10'), I('nights', 'Nights', 4, 'int')], [
        O('Booking confirmation, send now', 'date', '{today}'), O('Pre-arrival questions', 'date', 'MAX({today},{in:check_in}-5)'), O('Arrival time question', 'date', 'MAX({today},{in:check_in}-2)'),
        O('Check-in instructions', 'date', 'MAX({today},{in:check_in}-1)'), O('Welcome message on the day', 'date', '{in:check_in}'), O('First night check', 'date', '{in:check_in}+1'),
        O('Mid-stay check', 'date', 'IF({in:nights}>=4,{in:check_in}+ROUNDDOWN({in:nights}/2,0),{in:check_in}+1)'), O('Checkout reminder', 'date', '{in:check_in}+{in:nights}-1'), O('Thanks and review request', 'date', '{in:check_in}+{in:nights}+1'),
        O('Review reminder', 'date', '{in:check_in}+{in:nights}+4'), O('Messages to send', 'int', '9+IF({in:nights}>=4,1,0)'), O('Days until check-in', 'int', '{in:check_in}-{today}')],
         GR('What if', ('Two night stay', {'nights': 2}), ('Week long stay', {'nights': 7}), ('Check-in tomorrow', {'check_in': '={today}+1'}))),
    TOOL('review_whatif', 'What-if Reviews', 'New reviews against the average rating',
         'Type the current average, the number of reviews and the new reviews you expect at each star level; see the new average, the change and the five-star reviews still needed for the wanted average.', [
        I('avg', 'Current average rating', 4.55, 'num'), I('count', 'Reviews so far', 90, 'int'), I('n5', 'New reviews with 5 stars', 10, 'int'), I('n4', 'New reviews with 4 stars', 4, 'int'), I('n1', 'New reviews with 1 star', 0, 'int'),
        I('target', 'Wanted average rating', 4.6, 'num')], [
        O('New number of reviews', 'int', CT14), O('New average rating', 'num', 'ROUND(%s/%s,2)' % (PT14, CT14)), O('Change in the average', 'num', 'ROUND(%s/%s-{in:avg},2)' % (PT14, CT14)),
        O('Five-star reviews still needed for the wanted average', 'int', 'IF(%s/%s>={in:target},0,ROUNDUP(({in:target}*%s-%s)/(5-{in:target}),0))' % (PT14, CT14, CT14, PT14)),
        O('Share of new reviews with 5 stars', 'pct', 'IFERROR({in:n5}/({in:n5}+{in:n4}+{in:n1}),0)'), O('Verdict', 'text', 'IF(%s/%s>={in:target},%s,%s)' % (PT14, CT14, ck2('Above the wanted rating'), ck2('Below the wanted rating')))],
         GR('Reviews and rating together', ('Ten five-star reviews', {'n5': 10, 'n4': 0, 'n1': 0}), ('Twenty five-star reviews', {'n5': 20, 'n4': 0, 'n1': 0}), ('Mixed, 10 five and 10 four', {'n5': 10, 'n4': 10, 'n1': 0}),
            ('Two 1-star reviews', {'n5': 10, 'n4': 4, 'n1': 2}), ('Many reviews, 300 so far', {'count': 300, 'n5': 20}), ('Low start, average 4.2', {'avg': 4.2, 'n5': 20, 'n4': 0}))),
]
assert len(tools) == 14, len(tools)
