"""Generate data.json from public feeds; intended for GitHub Actions."""
import datetime as dt
import json
import pathlib
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

ROOT=pathlib.Path(__file__).resolve().parent
HEADERS={'User-Agent':'AFROEURODailyHub/1.0 (public feed reader)'}
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=18) as r:
        return r.read()

# ESPN's public endpoints are unofficial; coverage and availability may change.
LEAGUES = {
    'eng.1':'Premier League','esp.1':'La Liga','ger.1':'Bundesliga',
    'ita.1':'Serie A','fra.1':'Ligue 1','uefa.champions':'Champions League',
    'uefa.europa':'Europa League','uefa.europa.conf':'Conference League',
    'eng.2':'Championship','eng.fa':'FA Cup','eng.league_cup':'EFL Cup',
    'ned.1':'Eredivisie','por.1':'Primeira Liga','sco.1':'Scottish Premiership',
    'usa.1':'MLS','bra.1':'Brazil Série A','arg.1':'Argentina Primera',
    'caf.champions':'CAF Champions League','caf.confederation':'CAF Confederation Cup',
    'caf.nations':'Africa Cup of Nations','fifa.world':'World Cup',
    'uefa.euro':'European Championship','nga.1':'Nigeria Premier League',
}

def football():
    today=dt.datetime.now(dt.timezone.utc).date()
    start=(today-dt.timedelta(days=2)).strftime('%Y%m%d')
    end=(today+dt.timedelta(days=7)).strftime('%Y%m%d')
    out=[]
    for league, name in LEAGUES.items():
        try:
            url=f'https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard?dates={start}-{end}&limit=100'
            payload=json.loads(get(url))
            for event in payload.get('events',[]):
                competition=(event.get('competitions') or [{}])[0]
                competitors=competition.get('competitors') or []
                home=next((x for x in competitors if x.get('homeAway')=='home'),None)
                away=next((x for x in competitors if x.get('homeAway')=='away'),None)
                if not home or not away: continue
                state=event.get('status',{}).get('type',{}).get('state','pre')
                status=event.get('status',{}).get('type',{}).get('shortDetail','Scheduled')
                score=''
                if state in ('in','post'):
                    score=f"{home.get('score','?')}–{away.get('score','?')}"
                out.append({'home':home.get('team',{}).get('displayName','Home'),
                    'away':away.get('team',{}).get('displayName','Away'),
                    'status':status,'state':state,'score':score,
                    'date':event.get('date',''),'league':league,'league_name':name})
        except Exception as exc:
            print('Football feed unavailable:',league,str(exc))
    # Remove duplicates and keep upcoming plus recent matches.
    unique={ (g['league'],g['home'],g['away'],g['date']):g for g in out }
    return sorted(unique.values(),key=lambda x:x['date'])[:400]

def news():
    feeds=[('Africa','Africa news when:3d'),('Europe','Europe news when:3d'),('Nigeria','Nigeria news when:3d')]
    out=[]
    for region,query in feeds:
        try:
            url='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':query,'hl':'en-GB','gl':'GB','ceid':'GB:en'})
            root=ET.fromstring(get(url))
            for item in root.findall('./channel/item')[:6]:
                title=item.findtext('title') or ''
                link=item.findtext('link') or ''
                source=item.find('source')
                publisher=source.text if source is not None and source.text else region
                pub=item.findtext('pubDate') or ''
                if title and link.startswith('https://'):
                    out.append({'title':title[:220],'url':link,'source':publisher,'date':pub[:22]})
        except Exception as exc:
            print('News feed unavailable:',region,str(exc))
    return out[:18]

if __name__=='__main__':
    target=ROOT/'data.json'
    old={}
    if target.exists():
        try:old=json.loads(target.read_text())
        except Exception:pass
    scores=football() or old.get('football',[])
    headlines=news() or old.get('news',[])
    target.write_text(json.dumps({'updated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'football':scores,'news':headlines},ensure_ascii=False,indent=2)+'\n')
    print('Wrote',len(scores),'fixtures and',len(headlines),'headlines')
