# Q044 — Fresh Alpha PIT on Q043 Universe

Q044 validates six fixed price/OHLCV mechanisms on the fresh Q043 stock universe before any replication performance computation.

Universe: AON, CVS, ADSK, BA, T, F, LUV, NFLX.

Mechanisms:
- A1 multi-horizon TSM consensus
- A2 cross-sectional momentum top-2
- A3 residual momentum top-2
- A5 low-beta top-2
- A1b 52-week-high anchoring top-2
- A6 overnight/daytime tug-of-war top-2

At fixed decision points, future bars and the next session's OHLC are mutated. All six signal outputs must remain unchanged.

Q044 contains no performance, OOS, holdout, parameter, threshold, horizon or family selection.
