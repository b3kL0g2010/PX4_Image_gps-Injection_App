import os
import piexif
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True


def write_metadata(image_folder, sampled_df, output_folder):

    os.makedirs(output_folder, exist_ok=True)

    # Convert DataFrame to dictionary keyed by image name
    metadata_dict = {
        row["image"]: row
        for _, row in sampled_df.iterrows()
    }

    images = sorted(
        f for f in os.listdir(image_folder)
        if f.lower().endswith((".jpg", ".jpeg"))
    )

    for img_name in images:

        if img_name not in metadata_dict:
            continue

        row = metadata_dict[img_name]

        input_path = os.path.join(image_folder, img_name)
        output_path = os.path.join(output_folder, img_name)

        try:
            with Image.open(input_path) as img:

                # ---- SAFE LOAD EXIF ----
                try:
                    exif_dict = piexif.load(img.info.get("exif", b""))
                except Exception:
                    exif_dict = {
                        "0th": {},
                        "Exif": {},
                        "GPS": {},
                        "1st": {},
                        "thumbnail": None
                    }

                # ---------------------------------
                # 🔥 REWRITE EXIF TIME (+8h already computed)
                # ---------------------------------
                if "corrected_time" in row:
                    corrected_bytes = row["corrected_time"].encode()

                    exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = corrected_bytes
                    exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = corrected_bytes
                    exif_dict["0th"][piexif.ImageIFD.DateTime] = corrected_bytes

                # ---------------------------------
                # 🔥 GPS INJECTION
                # ---------------------------------
                gps_ifd = {
                    piexif.GPSIFD.GPSLatitudeRef:
                        "N" if row["lat"] >= 0 else "S",
                    piexif.GPSIFD.GPSLatitude:
                        _deg(abs(float(row["lat"]))),

                    piexif.GPSIFD.GPSLongitudeRef:
                        "E" if row["lon"] >= 0 else "W",
                    piexif.GPSIFD.GPSLongitude:
                        _deg(abs(float(row["lon"]))),

                    piexif.GPSIFD.GPSAltitude:
                        (int(float(row["alt"]) * 100), 100),
                }

                exif_dict["GPS"] = gps_ifd

                # ---- SAVE ----
                exif_bytes = piexif.dump(exif_dict)
                img.save(output_path, exif=exif_bytes)

        except Exception as e:
            print("FAILED:", img_name)
            print("ERROR:", e)


def _deg(value):
    deg = int(value)
    minute = int((value - deg) * 60)
    sec = int((((value - deg) * 60) - minute) * 60 * 100)
    return ((deg, 1), (minute, 1), (sec, 100))
