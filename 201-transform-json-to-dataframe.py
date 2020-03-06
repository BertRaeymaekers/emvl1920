#!/usr/bin/env python3

"""
This script will transform all the json game data
into four panda's dataframes:
    - team game statistics
    - team set statistics
    - player game statistics
    - player set statistics
"""

import json
import sys

import numpy as np
import pandas as pd


def purge_game_stats(stats):
    flat_stats = stats.copy()
    for remove in ['Set1', 'Set2', 'Set3', 'Set4', 'Set5']:
        del flat_stats[remove]
    return flat_stats

def purge_set_stats(setid, stats):
    flat_stats = stats.copy()
    for remove in ['Set1', 'Set2', 'Set3', 'Set4', 'Set5']:
        del flat_stats[remove]
    flat_stats['set'] = setid
    return flat_stats

def purge_players_set_stats(gameid, setid, hg, plrs_stats):
    result = {}
    for name, stats in plrs_stats.items():
        if stats['stats']['Set%s' % (setid)] == "":
            break
        flat_stats = stats['stats'].copy()
        for remove in ['Set1', 'Set2', 'Set3', 'Set4', 'Set5']:
            del flat_stats[remove]
        flat_stats['starting_position'] = stats['stats']['Set%s' % (setid)]
        flat_stats['number'] = stats['number']
        flat_stats['position'] = stats['position']
        flat_stats['hg'] = hg
        flat_stats['set'] = setid
        result[(name, gameid, setid)] = flat_stats
    return result

def purge_players_game_stats(gameid, hg, plrs_stats):
    result = {}
    for name, stats in plrs_stats.items():
        for set in ['Set1', 'Set2', 'Set3', 'Set4', 'Set5']:
            if stats['stats'][set] != "":
                break
        else:
            # Didn't play any sets
            break
        flat_stats = stats['stats'].copy()
        flat_stats['number'] = stats['number']
        flat_stats['position'] = stats['position']
        flat_stats['hg'] = hg
        result[(name, gameid)] = flat_stats
    return result

def read_json(srcpath='data/json'):
    game_dict = {}
    set_dict = {}
    player_game_dict = {}
    player_set_dict = {}
    for gameid in range(1, 57):
        with open(srcpath + '/game_%s.json' % (gameid)) as fd:
            data = json.load(fd)
            for hg in ['home', 'guest']:
                team = data['%s_team' % hg]
                game_stats = purge_game_stats(data['match']['%s_stats' % hg]['stats'])
                for set_data in data['sets']:
                    setid = set_data['set']
                    player_set_dict.update(purge_players_set_stats(gameid, setid, hg, set_data['%s_stats' % hg]['players']))
                    set_stats = purge_set_stats(setid, set_data['%s_stats' % hg]['stats'])
                    set_stats['hg'] = hg
                    set_stats['game'] = gameid
                    set_dict[(team, gameid, setid)] = set_stats
                player_game_dict.update(purge_players_game_stats(gameid, hg, data['match']['%s_stats' % hg]['players']))
                game_stats['hg'] = hg
                game_stats['game'] = gameid
                game_dict[(team, gameid)] = game_stats
    return (
        pd.DataFrame.from_dict(game_dict, orient='index'),
        pd.DataFrame.from_dict(set_dict, orient='index'),
        pd.DataFrame.from_dict(player_game_dict, orient='index'),
        pd.DataFrame.from_dict(player_set_dict, orient='index'))

def clean_dataframe(df):
    """
    Cleans the dataframe:
        - Remove the % from percentages.
        - Replaces '-' with NaN
    """
    # These column need to be of this type
    force_type = {
        'hg': 'category',
        'PointsTot': 'float',
        'Points': 'float',
        'L_VP': 'float',
        'PointsTot_sm': 'float',
        'ServeTot': 'float',
        'ServeErr': 'float',
        'ServeAce': 'float',
        'RecTot': 'float',
        'RecErr': 'float',
        'RecTot_sm': 'float',
        'SpikeTot': 'float',
        'SpikeErr': 'float',
        'SpikeHP': 'float',
        'SpikeWin': 'float',
        'SpikePos': 'float',
        'SpikeWin_sm': 'float',
        'BlockWin': 'float',
        'BlockWin_sm': 'float',
        'RecPos': 'float',
        'RecPerf': 'float',
        'RecPos_SM': 'float'
    }

    # These aren't in all dataframes
    if 'number' in df:
        force_type.update({'number': 'category'})
    if 'position' in df:
        cat_type = pd.api.types.CategoricalDtype(categories=["libero", "opposite", "middle", "setter", "wing spiker"])
        force_type.update({'position': cat_type})
    if 'starting_position' in df:
        force_type.update({'starting_position': 'category'})
    if 'Set1' in df:
        force_type.update({
            'Set1': 'category',
            'Set2': 'category',
            'Set3': 'category',
            'Set4': 'category',
            'Set5': 'category'
        })
    if 'set' in df:
        force_type.update({'set': 'category'})

    return df \
        .replace('^([0-9]+)%$', '\\1', regex=True) \
        .replace('-', 0) \
        .replace('.', np.nan) \
        .astype(force_type)


# JSON to dataframe
(games_df, sets_df, pls_games_df, pls_sets_df) = read_json()

# Clean dataframes
games_df = clean_dataframe(games_df)
sets_df = clean_dataframe(sets_df)
pls_games_df = clean_dataframe(pls_games_df)
pls_sets_df = clean_dataframe(pls_sets_df)

# Set position of libero from game position (TODO: fix this for better performance?)
# TODO: based on the starting position of the setter, figure out the other positions.
for ((player, gameid, setid), row) in pls_sets_df.iterrows():
    pls_sets_df.at[(player, gameid, setid), 'position'] = pls_games_df.loc[(player, gameid)].position

# Printout for a visual check.
print(games_df)
print(sets_df)
print(pls_games_df)
print(pls_sets_df)

print(games_df.dtypes)
print(sets_df.dtypes)
print(pls_games_df.dtypes)
print(pls_sets_df.dtypes)

# Writing
games_df.to_parquet('data/df2/games.prqt', compression='gzip')
sets_df.to_parquet('data/df2/sets.prqt', compression='gzip')
pls_games_df.to_parquet('data/df2/pls_games.prqt', compression='gzip')
pls_sets_df.to_parquet('data/df2/pls_sets.prqt', compression='gzip')
