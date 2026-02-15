import os
from datetime import datetime, timedelta
from PIL import Image
import piexif
import pandas as pd

from ulog_reader import extract_telemetry
from image_writer import write_metadata


def run_pipeline(
    image_folder,
    ulg_path,
    output_folder,
    apply_offset,
    progress_callback=None
):

    images = sorted(
        [f for f in os.listdir(image_folder)
         if f.lower().endswith((".jpg", ".jpeg"))]
    )

    if not images:
        raise ValueError("No JPG images found.")

    # ----------------------------------------
    # 🔥 PHASE 1 — VALIDATE IMAGE DATE
    # ----------------------------------------

    image_times = []
    violations = []

    for img_name in images:

        img_path = os.path.join(image_folder, img_name)

        # Safe image open
        try:
            with Image.open(img_path) as img:
                exif_bytes = img.info.get("exif", b"")
        except Exception:
            violations.append(f"{img_name} (Cannot open image)")
            continue

        # Safe EXIF load
        try:
            exif_dict = piexif.load(exif_bytes)
        except Exception:
            violations.append(f"{img_name} (Invalid EXIF)")
            continue

        # Check DateTimeOriginal exists
        if piexif.ExifIFD.DateTimeOriginal not in exif_dict["Exif"]:
            violations.append(f"{img_name} (Missing DateTimeOriginal)")
            continue

        dt_string = exif_dict["Exif"][
            piexif.ExifIFD.DateTimeOriginal
        ].decode()

        # Parse date safely
        try:
            image_time = datetime.strptime(
                dt_string,
                "%Y:%m:%d %H:%M:%S"
            )
        except Exception:
            violations.append(f"{img_name} (Invalid date format)")
            continue

        # 🚨 Reject unrealistic camera default dates (1970 etc.)
        if image_time.year < 2000:
            violations.append(
                f"{img_name} (Invalid camera date: {image_time.year})"
            )
            continue

        image_times.append((img_name, image_time))

    # If any violations found → stop processing
    if violations:
        return violations

    # ----------------------------------------
    # 🔥 PHASE 2 — TELEMETRY MATCHING
    # ----------------------------------------

    telemetry_df = extract_telemetry(ulg_path)

    if telemetry_df.empty:
        raise ValueError("Telemetry data is empty.")

    telemetry_df["utc_usec"] = pd.to_numeric(
        telemetry_df["utc_usec"],
        errors="coerce"
    )

    results = []
    total = len(image_times)

    for i, (img_name, image_time) in enumerate(image_times):

        # If checkbox is ticked Apply +8 hour correction
        if apply_offset:
            image_time_corrected = image_time + timedelta(hours=8)
        else:
            image_time_corrected = image_time


        # Safe timestamp conversion
        try:
            image_timestamp_usec = int(
                image_time_corrected.timestamp() * 1e6
            )
        except Exception:
            violations.append(
                f"{img_name} (Timestamp conversion failed)"
            )
            continue

        utc_series = telemetry_df["utc_usec"]

        # Safe telemetry matching
        time_diffs = (utc_series - image_timestamp_usec).abs()
        closest_idx = time_diffs.idxmin()

        telemetry_row = telemetry_df.loc[closest_idx]

        results.append({
            "image": img_name,
            "lat": float(telemetry_row["lat"]),
            "lon": float(telemetry_row["lon"]),
            "alt": float(telemetry_row["alt"]),
            "yaw": float(telemetry_row["yaw"]),
            "pitch": float(telemetry_row["pitch"]),
            "roll": float(telemetry_row["roll"]),
            "corrected_time":
                image_time_corrected.strftime("%Y:%m:%d %H:%M:%S")
        })

        if progress_callback:
            percent = int((i + 1) / total * 100)
            progress_callback(percent)

    # Write metadata
    results_df = pd.DataFrame(results)
    write_metadata(image_folder, results_df, output_folder)

    return []
