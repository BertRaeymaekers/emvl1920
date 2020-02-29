#!/usr/bin/env python3

"""
This stript transforms the downloaded html to a json file.
It will renumber the games starting with 1.

SRC:
    data/source
DEST:
    data/json
"""

import sys
import json

from bs4 import BeautifulSoup

stats = {}

def parse_set_team(set_soup, doprint=False):
    set_stats = {'players': {}}
    rows = set_soup.find('tbody')
    if doprint:
        print(str(rows)[0:1000])
    for tr in rows.children:
        if tr.name == 'tr':
            player_number = None
            player_name = None
            player_stats = {}
            if doprint:
                print(str(tr))
            for td in tr.children:
                if td.name == 'td':
                    span = td.find('span')
                    if span['id'] == 'PlayerNumber':
                        player_number = span.text
                    elif span['id'] == 'PlayerName':
                        player_name = span.b.text
                    else:
                        stat_name = span['id']
                        stat_value = span.text
                        player_stats[stat_name] = stat_value
            if player_name == 'TOTALS':
                set_stats['stats'] = player_stats
            else:
                player_position = None
                if player_name.endswith(' (L)'):
                    player_name = player_name[:-4]
                    player_position = 'libero'
                set_stats['players'][player_name] = {'number': player_number, 'name': player_name, 'position': player_position, 'stats': player_stats}
    return set_stats

def parse(gameid, doprint=False):
    match_stats = {'game_id': gameid, 'sets': []}
    with open("data/source/game_" + str(gameid) + ".html") as fp:
        soup = BeautifulSoup(fp)
        match_stats['home_team'] = soup.body.find('span', attrs={'id': 'Content_Main_LBL_HomeTeam'}).text
        match_stats['guest_team'] = soup.body.find('span', attrs={'id': 'Content_Main_LBL_GuestTeam'}).text
        if doprint:
            print(str(gameid) + ": " + match_stats['home_team'] + " vs " + match_stats['guest_team']) 
        match_statistics_soup = soup.body.find('div', attrs={'class': 'Class_DIV_MatchStats'})
        if doprint:
            print(dir(match_statistics_soup))
        for set_soup in match_statistics_soup.children:
            if set_soup.name == 'div':
                set_name = set_soup.find('span').text
                set_home_soup = set_soup.find('div', attrs={'id': 'RG_HomeTeam'})
                set_guest_soup = set_soup.find('div', attrs={'id': 'RG_GuestTeam'}) 
                if set_name == 'Match Statistics':
                    set_home_soup = set_soup.find('div', attrs={'id': 'RG_HomeTeam'})
                    set_guest_soup = set_soup.find('div', attrs={'id': 'RG_GuestTeam'})
                    match_stats['match'] = {
                        'home_stats': parse_set_team(set_home_soup, doprint=doprint),
                        'guest_stats': parse_set_team(set_guest_soup, doprint=doprint)
                        }
                else:
                    match_stats['sets'].append({
                        'set': set_name[4:],
                        'home_stats': parse_set_team(set_home_soup, doprint=doprint),
                        'guest_stats': parse_set_team(set_guest_soup, doprint=doprint)
                        })
    return match_stats


if False:
    match_stats = parse(195, doprint=False)
    print(json.dumps(match_stats, indent=4))
    sys.exit(0)

i = 1
for gameid in range(195,251):
    stats[gameid] = parse(gameid)
    with open('data/json/game_%s.json' % (i), 'w') as of:
        json.dump(stats[gameid], of, indent=4)
    i += 1