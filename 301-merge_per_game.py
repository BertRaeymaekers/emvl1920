#!/usr/bin/env python


import pandas as pd


def merge_game(name):
    # Read the game data
    game_df = pd.read_parquet("data/df2/%s.prqt" % (name))

    #print(game_df)

    # Split home and guest lines
    def split_df_and_rename_columns_on_column_value(game_df, column, value):
        result = game_df[game_df[column] == value]
        result.columns = ["%s_%s" % (value, name) for name in game_df.columns]
        del result["%s_%s" % (value, column)]
        return result

    game_home_df =  split_df_and_rename_columns_on_column_value(game_df, "hg", "home")
    game_guest_df = split_df_and_rename_columns_on_column_value(game_df, "hg", "guest")

    # Get the home teams from the index
    home_teams = [t for (t,gid) in game_home_df.index.values]
    guest_teams = [t for (t,gid) in game_guest_df.index.values]

    # Transform the index to just the game ID (gid) by dropping the team name
    game_home_df.reset_index(level=0, drop=True, inplace=True)
    game_guest_df.reset_index(level=0, drop=True, inplace=True)

    # Add home and guest team columns
    result = game_home_df.assign(home_team=home_teams).merge(game_guest_df.assign(guest_team=guest_teams), left_on='home_game', right_on='guest_game')

    # Sets to game win points:
    # 3-0: +3
    # 3-1: +2
    # 3-2: +1
    # 2-3: -1
    # 1-3: -2
    # 0-3: -3

    result.to_parquet("data/df3/%s.prqt" % (name), compression='gzip')

    return result


game_df = merge_game("games")
print(game_df)