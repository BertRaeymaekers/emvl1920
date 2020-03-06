#!/usr/bin/env python3

import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt
# Paired t-test
from scipy import stats

np.random.seed(42)


def get_df(filename='data/df3/games.prqt'):
    # PointsTot (total points), Points (# break points), L_VP (Win-Lost), PointsTot_sm (total points)
    # ServeTot (total serves), ServeErr (#serve errors), ServeAce (#serve aces)
    # RecTot (total receptions), RecErr (#reception errors), RecPos (#positive receptions), RecPerf (?), RecTot_sm (?), RecPos_SM (?)
    # SpikeTot (total attacks), SpikeErr (#attack errors), SpikeHP (#blocked attacks), SpikeWin (#excellent attacks), SpikePos (?), SpikeWin_sm
    # BlockWin,  BlockWin_sm
    # game
    return pd.read_parquet(filename)


df = get_df()

# Hypotesis 1: L_VP = PointsTot - ServeErr - RecErr - SpikeErr - SpikeHP
for hg in ["home", "guest"]:
    H1 = df["%s_PointsTot" % (hg)] - df["%s_ServeErr" % (hg)] - df["%s_RecErr" % (hg)] - df["%s_SpikeErr" % (hg)] - df["%s_SpikeHP" % (hg)]
    plt.figure()
    plt.scatter(
        x=df["%s_L_VP" % (hg)],
        y=H1
    ).get_figure().savefig("fig/H1_%s.png" % (hg))
    corr = H1.corr(df["%s_L_VP" % (hg)])
    print("Correlation L_VP and PointsTot - ServeErr - RecErr - SpikeErr - SpikeHP: %s" % (corr))
    if corr < 0.99:
        sys.exit(1)
    plt.close()
print()

# Hypothesis 2: PointsTot = ServeAce + SpikeWin + BlockWin
for hg in ["home", "guest"]:
    H2 = df["%s_ServeAce" % (hg)] + df["%s_SpikeWin" % (hg)] + df["%s_BlockWin" % (hg)]
    plt.figure()
    plt.scatter(
        x=df["%s_PointsTot" % (hg)],
        y=H2
    ).get_figure().savefig("fig/H2_%s.png" % (hg))
    corr = H2.corr(df["%s_PointsTot" % (hg)])
    print("Correlation PointsTot and ServeAce + SpikeWin + BlockWin: %s" % (corr))
    if corr < 0.99:
        sys.exit(1)
    plt.close()
print()

# Doing some HOME vs GUEST
parameter_index = [
    "PointsTot", "Points", "L_VP",
    "ServeTot", "ServeErr", "ServeAce",
    "RecTot", "RecErr", "RecPos", "RecPerf", "RecTot_sm",
    "SpikeTot", "SpikeErr", "SpikeHP", "SpikeWin", "SpikePos",
    "BlockWin"
    ]
home_advantage_list = [] # pd.DataFrame(columns=['wilcoxon', 'pairwise t-test'])
print("Comparing HOHE vs GUEST (aka the home advantage)")
for parameter in parameter_index:
    # Scatter
    plt.figure()
    df.plot(
        kind="scatter", 
        title="%s home vs guest" % (parameter), 
        x="home_%s" % (parameter), 
        y="guest_%s" % (parameter)
    ).get_figure().savefig("fig/games_scatter_%s.png" % (parameter))
    plt.close()

    # Histogram
    plt.figure()
    df["home_%s" % (parameter)].plot(kind="hist", title="%s home vs guest" % (parameter), bins=50)
    df["guest_%s" % (parameter)].plot(kind="hist", title="%s home vs guest" % (parameter), bins=50).get_figure().savefig("fig/games_hist_%s.png" % (parameter))
    plt.close()

    #print("Home %s:  %s" % (parameter, df["home_%s" % (parameter)].mean()))
    #print("Guest %s: %s" % (parameter, df["guest_%s" % (parameter)].mean()))
    w = stats.wilcoxon(df["home_%s" % (parameter)], df["guest_%s" % (parameter)])
    t = stats.ttest_rel(df["home_%s" % (parameter)], df["guest_%s" % (parameter)])
    #print(w)
    #print(t)
    home_advantage_list.append({"wilcoxon": w.pvalue, "pairwise t-test": t.pvalue})
    #print()

home_advantage = pd.DataFrame(home_advantage_list, index=parameter_index)
print(home_advantage.sort_values(by="wilcoxon"))

sys.exit(0)

# Trying to predict the total amount of points
y = df.iloc[:, 0].values
x = df.iloc[:, 1:-20].values

print(x)
print(y)

sys.exit(0)

# Note the difference in argument order
model = sm.OLS(y, x).fit()
y_pred = model.predict(x)

# Print out the statistics
model.summary()

## Run the model...
#regressor = RandomForestRegressor(n_estimators=20, random_state=0)
#regressor.fit(x, y)
#
## See how well it did
#y_pred = regressor.predict(x)
#
print(y - y_pred)
