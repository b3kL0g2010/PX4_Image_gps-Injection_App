import os
from datetime import datetime, timedelta, timezone
from PIL import Image
import piexif
import pandas as pd

from ulog_reader import extract_telemetry
from image_writer import write_metadata


PH_TZ = timezone(timedelta(hours=8))

def run_pipeline(
    image_folder,
    ulg_path,
    output_folder,
    apply_offset,
    progress_callback=None,
    log_callback=None
):

    def log(msg):
        if log_callback:
            log_callback(msg)

    images = sorted(
        [f for f in os.listdir(image_folder)
         if f.lower().endswith((".jpg", ".jpeg"))]
    )

    if not images:
        raise ValueError("No JPG images found.")

    log("Starting image validation...")

    # ----------------------------------------
    # PHASE 1 — VALIDATE IMAGE DATE
    # ----------------------------------------

    image_times = []
    violations = []

    for img_name in images:

        img_path = os.path.join(image_folder, img_name)

        try:
            with Image.open(img_path) as img:
                exif_bytes = img.info.get("exif", b"")
        except Exception:
            violations.append(f"{img_name} (Cannot open image)")
            log(f"⚠ {img_name} cannot be opened.")
            continue

        try:
            exif_dict = piexif.load(exif_bytes)
        except Exception:
            violations.append(f"{img_name} (Invalid EXIF)")
            log(f"⚠ {img_name} has invalid EXIF.")
            continue

        if piexif.ExifIFD.DateTimeOriginal not in exif_dict["Exif"]:
            violations.append(f"{img_name} (Missing DateTimeOriginal)")
            log(f"⚠ {img_name} missing DateTimeOriginal.")
            continue

        dt_string = exif_dict["Exif"][
            piexif.ExifIFD.DateTimeOriginal
        ].decode()

        try:
            image_time = datetime.strptime(
                dt_string,
                "%Y:%m:%d %H:%M:%S"
            )
        except Exception:
            violations.append(f"{img_name} (Invalid date format)")
            log(f"⚠ {img_name} has invalid date format.")
            continue

        if image_time.year < 2000:
            violations.append(
                f"{img_name} (Invalid camera date: {image_time.year})"
            )
            log(f"⚠ {img_name} has invalid year {image_time.year}.")
            continue

        image_times.append((img_name, image_time))

    if violations:
        log("")
        log("❌ VALIDATION FAILED")
        log("--------------------------------------------------")

        for v in violations:
            log(f"⚠ {v}")

        log("")
        log("📌 RECOMMENDED ACTION:")
        log("• Open the listed images and verify Date Values.")
        log("• Camera default date (e.g., 1970) is invalid.")
        log("• If images are not important, delete them.")
        log("")
        log("Processing aborted due to invalid image dates.")
        log("--------------------------------------------------")

        return violations

    # ----------------------------------------
    # PHASE 2 — TELEMETRY MATCHING
    # ----------------------------------------

    telemetry_df = extract_telemetry(ulg_path)

    log("🔎 Validating flight time window...")

    flight_start = telemetry_df["utc_usec"].min()
    flight_end   = telemetry_df["utc_usec"].max()

    flight_start_dt = datetime.fromtimestamp(flight_start / 1e6, tz=timezone.utc).astimezone(PH_TZ)
    flight_end_dt   = datetime.fromtimestamp(flight_end / 1e6, tz=timezone.utc).astimezone(PH_TZ)

    log(f"Flight Start (PHT UTC +8): {flight_start_dt}")
    log(f"Flight End   (PHT UTC +8): {flight_end_dt}")



    if telemetry_df.empty:
        raise ValueError("Telemetry data is empty.")

    telemetry_df["utc_usec"] = pd.to_numeric(
        telemetry_df["utc_usec"],
        errors="coerce"
    )

    results = []
    total = len(image_times)

    log("Starting telemetry matching...")

    utc_series = telemetry_df["utc_usec"]

    MAX_ALLOWED_DIFF = 3  # seconds tolerance

    for i, (img_name, image_time) in enumerate(image_times):

        # Apply optional offset
        if apply_offset:
            image_time_corrected = image_time + timedelta(hours=8)
        else:
            image_time_corrected = image_time

        # Convert to timestamp
        try:
            image_timestamp_usec = int(
                image_time_corrected.timestamp() * 1e6
            )
        except Exception:
            violations.append(
                f"{img_name} (Timestamp conversion failed - Invalid EXIF date)"
            )

            log(f"⚠ {img_name} timestamp conversion failed.")
            log("   → Check image DateTimeOriginal.")
            log("   → Remove image if not important.")
            continue

        # 🔥 FLIGHT WINDOW VALIDATION
        if image_timestamp_usec < flight_start or image_timestamp_usec > flight_end:
            violations.append(
                f"{img_name} (Outside flight time window)"
            )

            log(f"❌ {img_name} rejected — Outside telemetry flight window.")
            continue

        # Find closest telemetry timestamp
        time_diffs = (utc_series - image_timestamp_usec).abs()
        closest_idx = time_diffs.idxmin()

        min_diff_usec = time_diffs.loc[closest_idx]
        min_diff_sec = min_diff_usec / 1e6

        # 🔥 STRICT TIME TOLERANCE CHECK
        if min_diff_sec > MAX_ALLOWED_DIFF:
            violations.append(
                f"{img_name} (No matching telemetry. Δ {min_diff_sec:.2f}s)"
            )

            log(f"❌ {img_name} rejected — Time mismatch {min_diff_sec:.2f}s.")
            continue

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

        log(f"✔ Injected telemetry into {img_name}")

        if progress_callback:
            percent = int((i + 1) / total * 100)
            progress_callback(percent)


    # ----------------------------------------
    # FINAL PHASE — FINISHING / WRITE METADATA
    # ----------------------------------------

    results_df = pd.DataFrame(results)

    # If no images were successfully matched
    if not results:
        log("❌ No valid images matched telemetry.")
        return violations if violations else ["No valid images matched telemetry."]

    log("Writing metadata to images...")
    write_metadata(image_folder, results_df, output_folder)

    if violations:
        log("⚠ Some images were rejected.")
    else:
        log("Processing completed successfully.")

    return violations

