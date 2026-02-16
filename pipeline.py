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

    if telemetry_df.empty:
        raise ValueError("Telemetry data is empty.")

    telemetry_df["utc_usec"] = pd.to_numeric(
        telemetry_df["utc_usec"],
        errors="coerce"
    )

    results = []
    total = len(image_times)

    log("Starting telemetry matching...")

    for i, (img_name, image_time) in enumerate(image_times):

        if apply_offset:
            image_time_corrected = image_time + timedelta(hours=8)
        else:
            image_time_corrected = image_time

        try:
            image_timestamp_usec = int(
                image_time_corrected.timestamp() * 1e6
            )
        except Exception:
            violations.append(
                f"{img_name} (Timestamp conversion failed - Invalid or corrupted EXIF date)\n"
                f"  → Check the image Date value.\n"
                f"  → If the image is not important, consider deleting it."
            )

            log(f"⚠ {img_name} timestamp conversion failed.")
            log("   → Possible corrupted or unrealistic EXIF date.")
            log("   → Remove the image if unnecessary.")

            continue


        utc_series = telemetry_df["utc_usec"]
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

        log(f"✔ Injected telemetry into {img_name}")

        if progress_callback:
            percent = int((i + 1) / total * 100)
            progress_callback(percent)

    log("Writing metadata to images...")

    results_df = pd.DataFrame(results)
    write_metadata(image_folder, results_df, output_folder)

    log("Processing completed successfully.")

    return []
