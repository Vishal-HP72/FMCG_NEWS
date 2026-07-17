import pandas as pd
from config import TIER_1_CHANNELS, TIER_2_CHANNELS, TIER_3_CHANNELS

def apply_source_credibility_filter(df, filter_strict=True):
    if df.empty:
        return df

    credibility_scores = []
    keep_mask = []

    for _, row in df.iterrows():
        source_name = str(row["source"]).lower()

        is_tier_1 = any(channel in source_name for channel in TIER_1_CHANNELS)
        is_tier_2 = any(channel in source_name for channel in TIER_2_CHANNELS)
        is_tier_3 = any(channel in source_name for channel in TIER_3_CHANNELS)

        if is_tier_3:
            credibility_scores.append(1)
            keep_mask.append(True)
        elif is_tier_1:
            credibility_scores.append(2)
            keep_mask.append(True)
        elif is_tier_2:
            credibility_scores.append(3)
            keep_mask.append(True)
        else:
            credibility_scores.append(4)
            keep_mask.append(not filter_strict)

    df["credibility_score"] = credibility_scores
    df_filtered = df[keep_mask].copy()
    df_filtered.reset_index(drop=True, inplace=True)
    
    return df_filtered