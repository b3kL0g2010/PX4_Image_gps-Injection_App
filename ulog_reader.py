from pyulog import ULog
import pandas as pd
import numpy as np


def quaternion_to_euler(q0, q1, q2, q3):

    sinr_cosp = 2 * (q0 * q1 + q2 * q3)
    cosr_cosp = 1 - 2 * (q1 * q1 + q2 * q2)
    roll = np.degrees(np.arctan2(sinr_cosp, cosr_cosp))

    sinp = 2 * (q0 * q2 - q3 * q1)
    pitch = np.degrees(np.arcsin(np.clip(sinp, -1.0, 1.0)))

    siny_cosp = 2 * (q0 * q3 + q1 * q2)
    cosy_cosp = 1 - 2 * (q2 * q2 + q3 * q3)
    yaw = np.degrees(np.arctan2(siny_cosp, cosy_cosp))

    return yaw, pitch, roll


def extract_telemetry(ulg_path):

    ulog = ULog(ulg_path)

    gps = ulog.get_dataset("vehicle_gps_position").data
    att = ulog.get_dataset("vehicle_attitude").data

    gps_df = pd.DataFrame({
        "timestamp": gps["timestamp"],
        "utc_usec": gps["time_utc_usec"],
        "lat": gps["latitude_deg"],
        "lon": gps["longitude_deg"],
        "alt": gps["altitude_msl_m"]
    })

    att_df = pd.DataFrame({
        "timestamp": att["timestamp"],
        "q0": att["q[0]"],
        "q1": att["q[1]"],
        "q2": att["q[2]"],
        "q3": att["q[3]"]
    })

    yaw_list = []
    pitch_list = []
    roll_list = []

    for _, row in att_df.iterrows():
        yaw, pitch, roll = quaternion_to_euler(
            row["q0"], row["q1"], row["q2"], row["q3"]
        )
        yaw_list.append(yaw)
        pitch_list.append(pitch)
        roll_list.append(roll)

    att_df["yaw"] = yaw_list
    att_df["pitch"] = pitch_list
    att_df["roll"] = roll_list

    att_df = att_df[["timestamp", "yaw", "pitch", "roll"]]

    gps_df = gps_df.sort_values("timestamp")
    att_df = att_df.sort_values("timestamp")

    telemetry_df = pd.merge_asof(
        gps_df,
        att_df,
        on="timestamp",
        direction="nearest"
    )

    telemetry_df = telemetry_df[telemetry_df["utc_usec"] > 0]

    telemetry_df = telemetry_df.reset_index(drop=True)

    return telemetry_df
