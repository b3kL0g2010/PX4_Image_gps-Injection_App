import numpy as np
import pandas as pd


def quaternion_to_euler(q0, q1, q2, q3):

    yaw = np.arctan2(2*(q0*q3+q1*q2), 1-2*(q2*q2+q3*q3))
    pitch = np.arcsin(2*(q0*q2-q3*q1))
    roll = np.arctan2(2*(q0*q1+q2*q3), 1-2*(q1*q1+q2*q2))

    return np.degrees(yaw), np.degrees(pitch), np.degrees(roll)


def merge_and_sample(gps_df, att_df, interval):

    gps_df["utc"] = pd.to_datetime(gps_df["utc_usec"], unit="us")

    df = pd.merge_asof(
        gps_df.sort_values("timestamp"),
        att_df.sort_values("timestamp"),
        on="timestamp"
    )

    yaw, pitch, roll = quaternion_to_euler(
        df["q0"], df["q1"], df["q2"], df["q3"]
    )

    df["yaw"] = yaw
    df["pitch"] = pitch
    df["roll"] = roll

    start = df["utc"].iloc[0]
    end = df["utc"].iloc[-1]

    sample_times = pd.date_range(start, end, freq=f"{interval}s")

    sampled = pd.merge_asof(
        pd.DataFrame({"utc": sample_times}),
        df.sort_values("utc"),
        on="utc"
    )

    return sampled
