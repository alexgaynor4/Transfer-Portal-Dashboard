import time
import csv
import cloudscraper
from bs4 import BeautifulSoup

PAGE_URL   = 'https://www.on3.com/transfer-portal/wire/basketball/'
OUTPUT_CSV = 'portal_players.csv'
MAX_PAGES  = 50   # safety cap

scraper = cloudscraper.create_scraper(
    browser={'custom': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/113.0.0.0 Safari/537.36'
    )}
)

def parse_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    ol   = soup.find('ol', class_='TransferPortalPage_transferPortalList__vbYpa')
    if not ol:
        return []
    items = ol.find_all('li')
    players = []
    for li in items:
        name_a   = li.select_one('div.TransferPortalItem_playerNameContainer__bwhKH a')
        name     = name_a.get_text(strip=True)
        profile  = 'https://www.on3.com' + name_a['href']

        def t(sel):
            el = li.select_one(sel)
            return el.get_text(strip=True) if el else ''

        # last / new team from <img> titles
        last_img = li.select_one('div.TransferPortalItem_lastTeamWrapper__dusYk img')
        last_team = last_img.get('title', '') if last_img else ''

        new_imgs = li.select('div.TransferPortalItem_teamStatusContainer__IVsOd img')
        if len(new_imgs) > 1:
            new_team = new_imgs[-1].get("title", "")
        else:
            new_team = "N/A"

        players.append({
            'name':        name,
            'profile':     profile,
            'position':    t('span.TransferPortalItem_position__w3yR_'),
            'class':       t('div.TransferPortalItem_playerVitalsContainer__S1kpd span:nth-of-type(1)'),
            'height':      t('div.TransferPortalItem_playerVitalsContainer__S1kpd span:nth-of-type(2)'),
            'weight':      t('div.TransferPortalItem_playerVitalsContainer__S1kpd span:nth-of-type(3)'),
            'high_school': t('a.TransferPortalItem_highSchool__pvhfn'),
            'hometown':    t('span.TransferPortalItem_homeTown__9b7I4'),
            'rating':      t('span[data-name="overall-rating"]'),
            'nil_value':   t('div.TransferPortalItem_nilValuation__aLmJD'),
            'status':      t('span.TransferPortalItem_statusLabel__Y4_16'),
            'last_team':   last_team,
            'new_team':    new_team
        })
    return players

all_players = []
for page_num in range(1, MAX_PAGES+1):
    print(f"Fetching page {page_num}…")
    resp = scraper.get(PAGE_URL, params={'page': page_num}, timeout=30)
    resp.raise_for_status()

    page_players = parse_page(resp.text)
    if not page_players:
        print("No more players—done.")
        break

    all_players.extend(page_players)
    time.sleep(0.5)

print(f"Total players scraped: {len(all_players)}")

# write to CSV
with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=all_players[0].keys())
    writer.writeheader()
    writer.writerows(all_players)

print(f"Saved → {OUTPUT_CSV}")
