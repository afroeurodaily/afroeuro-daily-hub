
"""AFROEURO Daily Hub - Global News and Football Automation."""

import datetime as dt
import json
import pathlib
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

ROOT = pathlib.Path(__file__).resolve().parent

HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json, application/rss+xml, application/xml, */*',
    'Accept-Language': 'en-US,en;q=0.9'
}

def get(url):
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=18) as response:
        return response.read()


LEAGUES = {
    'eng.1': 'Premier League',
    'esp.1': 'La Liga',
    'ger.1': 'Bundesliga',
    'ita.1': 'Serie A',
    'fra.1': 'Ligue 1',
    'uefa.champions': 'Champions League',
    'uefa.europa': 'Europa League',
    'uefa.europa.conf': 'Conference League',
    'eng.2': 'Championship',
    'eng.fa': 'FA Cup',
    'eng.league_cup': 'EFL Cup',
    'ned.1': 'Eredivisie',
    'por.1': 'Primeira Liga',
    'sco.1': 'Scottish Premiership',
    'usa.1': 'MLS',
    'bra.1': 'Brazil Serie A',
    'arg.1': 'Argentina Primera',
    'caf.champions': 'CAF Champions League',
    'caf.confederation': 'CAF Confederation Cup',
    'caf.nations': 'Africa Cup of Nations',
    'fifa.world': 'World Cup',
    'uefa.euro': 'European Championship',
    'nga.1': 'Nigeria Premier League',
}


def football():
    today = dt.datetime.now(dt.timezone.utc).date()
    out = []

    for league, name in LEAGUES.items():
        for offset in (-1, 0, 1, 2):
            day = today + dt.timedelta(days=offset)
            date_key = day.strftime('%Y%m%d')

            try:
                url = (
                    'https://site.api.espn.com/apis/site/v2/'
                    f'sports/soccer/{league}/scoreboard'
                    f'?dates={date_key}'
                )

                payload = json.loads(get(url))

                for event in payload.get('events', []):
                    competition = (
                        event.get('competitions') or [{}]
                    )[0]

                    competitors = competition.get('competitors') or []

                    home = next(
                        (x for x in competitors
                         if x.get('homeAway') == 'home'),
                        None
                    )

                    away = next(
                        (x for x in competitors
                         if x.get('homeAway') == 'away'),
                        None
                    )

                    if not home or not away:
                        continue

                    home_team = home.get('team') or {}
                    away_team = away.get('team') or {}

                    status_data = (
                        event.get('status')
                        or competition.get('status')
                        or {}
                    ).get('type', {})

                    state = status_data.get('state', 'pre')
                    status = status_data.get('shortDetail', 'Scheduled')

                    score = ''

                    if state in ('in', 'post'):
                        score = (
                            f"{home.get('score', '?')}"
                            f"–{away.get('score', '?')}"
                        )

                    out.append({
                        'home': home_team.get('displayName', 'Home'),
                        'away': away_team.get('displayName', 'Away'),
                        'home_logo': home_team.get('logo', ''),
                        'away_logo': away_team.get('logo', ''),
                        'status': status,
                        'state': state,
                        'score': score,
                        'date': event.get('date', ''),
                        'league': league,
                        'league_name': name
                    })

                print(
                    'Football collected:',
                    name,
                    date_key,
                    len(payload.get('events', []))
                )

            except Exception as exc:
                print(
                    'Football feed unavailable:',
                    league,
                    date_key,
                    str(exc)
                )

    unique = {
        (g['league'], g['home'], g['away'], g['date']): g
        for g in out
    }

    return sorted(
        unique.values(),
        key=lambda x: x['date']
    )




NEWS_FEEDS = [
    ('World', 'world news when:2d'),
    ('Nigeria', 'Nigeria news when:2d'),
    ('Africa', 'Africa news when:2d'),
    ('Europe', 'Europe news when:2d'),
    ('Germany', 'Germany news when:2d'),
    ('America', 'Americas news when:2d'),
    ('Asia', 'Asia news when:2d'),
    ('Middle East', 'Middle East news when:2d'),
    ('Politics', 'international politics when:2d'),
    ('Business', 'global business economy when:2d'),
    ('Entertainment', 'entertainment celebrity news when:2d'),
    ('Sports', 'international sports news when:2d'),
]


def publication_date(value):
    try:
        date = parsedate_to_datetime(value)

        if date.tzinfo is None:
            date = date.replace(tzinfo=dt.timezone.utc)

        return date.astimezone(dt.timezone.utc).isoformat()

    except Exception:
        return ''


def news():
    out = []
    seen_titles = set()
    seen_links = set()

    for category, query in NEWS_FEEDS:
        try:
            url = (
                'https://news.google.com/rss/search?'
                + urllib.parse.urlencode({
                    'q': query,
                    'hl': 'en-GB',
                    'gl': 'GB',
                    'ceid': 'GB:en'
                })
            )

            root = ET.fromstring(get(url))
            count = 0

            for item in root.findall('./channel/item'):
                title = (item.findtext('title') or '').strip()
                link = (item.findtext('link') or '').strip()
                pub = item.findtext('pubDate') or ''

                source = item.find('source')

                publisher = (
                    source.text
                    if source is not None and source.text
                    else category
                )

                if not title or not link.startswith('https://'):
                    continue

                title_key = ' '.join(title.lower().split())

                if title_key in seen_titles or link in seen_links:
                    continue

                seen_titles.add(title_key)
                seen_links.add(link)

                out.append({
                    'title': title[:220],
                    'url': link,
                    'source': publisher,
                    'date': pub[:22],
                    'published_at': publication_date(pub),
                    'category': category
                })

                count += 1

                if count >= 10:
                    break

            print('News collected:', category, count)

        except Exception as exc:
            print('News feed unavailable:', category, str(exc))

    return sorted(
        out,
        key=lambda x: x.get('published_at', ''),
        reverse=True
    )[:120]


if __name__ == '__main__':
    target = ROOT / 'data.json'
    old = {}

    if target.exists():
        try:
            old = json.loads(target.read_text(encoding='utf-8'))
        except Exception:
            pass

    scores = football() or old.get('football', [])
    headlines = news() or old.get('news', [])

    old.update({
        'updated_at': dt.datetime.now(
            dt.timezone.utc
        ).isoformat(),
        'football': scores,
        'news': headlines
    })

    target.write_text(
        json.dumps(
            old,
            ensure_ascii=False,
            indent=2
        ) + '\n',
        encoding='utf-8'
    )

    print(
        'AFROEURO Daily Hub:',
        len(scores),
        'fixtures and',
        len(headlines),
        'headlines'
    )
