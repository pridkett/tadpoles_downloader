"""tagger.py

This is part of my Tadpoles suite of tools and accomplishes
the scond part of the project - adding in the exif tags.
"""

import argparse
import datetime
import json
from json.decoder import JSONDecodeError
from typing import Tuple, Iterable, List, Dict
from fractions import Fraction
import os
import shutil
from PIL import Image
import piexif


# some of this GPS stuff was pulled from:
#    https://gist.github.com/c060604/8a51f8999be12fc2be498e9ca56adc72
def to_deg(value: float, loc: List[str]) -> Tuple[int, int, float, str]:
    """Convert decimal coordinates into degrees, munutes and seconds tuple.

    args:
        value: float of the location in degrees
        loc: the direction N, S, E, W to go along with output
    returns:
        a Tuple of (int, int, float, str) to represent degrees, minutes, seconds, direction
    """
    if value < 0:
        loc_value = loc[0]
    elif value > 0:
        loc_value = loc[1]
    else:
        loc_value = ""
    abs_value = abs(value)
    deg = int(abs_value)
    t1 = (abs_value - deg) * 60
    min = int(t1)
    sec = round((t1 - min) * 60, 5)
    return (deg, min, sec, loc_value)


def change_to_rational(number: float) -> Tuple[int, int]:
    """Convert a number to a rational.

    args:
        number: the number to rationalize
    returns:
        tuple like (1, 2), (numerator, denominator)
    """
    f = Fraction(str(number))
    return (f.numerator, f.denominator)


def create_gps_block(lat: float, lng: float, altitude: float = None) -> Dict:
    """Create an EXIF GPSIFD block for geo data.

    args:
        lat: latitude (as float)
        lng: longitude (as float)
        altitude: altitude (as float in meters)
    returns:
        A dictionary for the GPD IFD block
    """
    lat_deg = to_deg(lat, ["S", "N"])
    lng_deg = to_deg(lng, ["W", "E"])

    exiv_lat = (
        change_to_rational(lat_deg[0]),
        change_to_rational(lat_deg[1]),
        change_to_rational(lat_deg[2]),
    )
    exiv_lng = (
        change_to_rational(lng_deg[0]),
        change_to_rational(lng_deg[1]),
        change_to_rational(lng_deg[2]),
    )

    gps_ifd = {
        piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
        piexif.GPSIFD.GPSAltitudeRef: 0,
        piexif.GPSIFD.GPSLatitudeRef: lat_deg[3],
        piexif.GPSIFD.GPSLatitude: exiv_lat,
        piexif.GPSIFD.GPSLongitudeRef: lng_deg[3],
        piexif.GPSIFD.GPSLongitude: exiv_lng,
    }

    if altitude:
        gps_ifd[piexif.GPSIFD.GPSAltitude] = change_to_rational(round(altitude))

    print(gps_ifd)
    return gps_ifd


def parse_tags(tags: str = None) -> Iterable[str]:
    """Convert comma separated strings into an iterable.

    args:
        tags: a string of comma separated tag like "school, daycare"
    return:
        a list of tags like ["school", "daycare"]
    """
    if not tags:
        return []
    return [x.strip() for x in tags.split(",")]


def parse_coords(geo: str) -> Tuple[float, float]:
    """Parse lat/long from a string to a tuple of floats.

    args:
        geo: The coordinates as string such as '45.123,-123.12'
    returns:
        a tuple of lat,long as floats
    """
    lat, long = [float(x.strip()) for x in geo.split(",")]
    if lat > 90 or lat < -90:
        raise ValueError("latitude does not fall in the range (-90, 90)")
    if long > 180 or long < -180:
        raise ValueError("longitude does not fall in the range (-180, 180)")
    return (lat, long)


def process_image(
    src: str,
    dest: str,
    desc: str,
    timestamp: datetime.datetime,
    geo: Tuple[float, float] = None,
    altitude: float = None,
    tags: Iterable[str] = None,
) -> None:
    """Add exif tags to an image.

    args:
        src: source filename
        dest: destination file
        desc: a string description attached to the image
        timestamp: the timestamp to atatch to the image
        geo: (lat, long) in degrees to attach to the image
        altitude: the altitude of the geo coordinatoes
        tags: an iterable of tags to attach to the image

    Note: as of right now this doesn't properly bring all the tags into Apple
    Photos. Notably, the desc and tags are not brought in because it seems like
    Apple Photos is looking for XMP tags.
    """

    shutil.copy2(src, dest)
    exif_dict = piexif.load(src)

    if geo:
        exif_dict["GPS"] = create_gps_block(lat=geo[0], lng=geo[1], altitude=altitude)

    if desc:
        exif_dict["0th"][piexif.ImageIFD.ImageDescription] = desc

    if timestamp:
        exif_time = timestamp.strftime("%Y:%m:%d %H:%M:%S")
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = exif_time
        exif_dict["0th"][piexif.ImageIFD.DateTime] = exif_time
        if timestamp.tzinfo:
            tzoffset = timestamp.tzinfo.utcoffset(timestamp)
            if tzoffset:
                exif_dict["1st"][piexif.ImageIFD.TimeZoneOffset] = int(
                    tzoffset.total_seconds()
                )

    if tags:
        keywords = ",".join(tags)
        print(keywords)
        exif_dict["0th"][piexif.ImageIFD.XPKeywords] = keywords.encode("utf-16le")

    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, dest)


def main(
    src: str,
    dest: str,
    logfile: str,
    geo: Tuple[float, float] = None,
    alt: float = None,
    tags: Iterable[str] = None,
) -> None:
    """Execute the main routine for the program.

    args:
        src: the source folder for the images
        dest: the destination folder where the images will be written
        logfile: the json file with the image descriptions
        geo: the (lat, long) coordinates to geocode the images
    """
    if not (os.path.exists(src)):
        raise FileNotFoundError(f'source path "{src}" not found')
    if not (os.path.exists(dest)):
        raise FileNotFoundError(f'destination path "{dest}" not found')
    if not (os.path.exists(logfile)):
        raise FileNotFoundError(f'json log file "{logfile}" not found')

    with open(logfile) as fp:
        for line in fp:
            try:
                logline = json.loads(line.strip())
                img_date = datetime.datetime.fromisoformat(logline["date"])
                print(logline["date"])
                process_image(
                    src=os.path.join(src, logline["outfile"]),
                    dest=os.path.join(dest, logline["outfile"]),
                    desc=logline["description"],
                    timestamp=img_date,
                    geo=geo,
                    altitude=alt,
                    tags=tags,
                )
                break
            except JSONDecodeError:
                pass


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()

    # this is a hack - see https://stackoverflow.com/a/41747010/57626
    optional_args = argparser._action_groups.pop()
    required_args = argparser.add_argument_group("required arguments")
    required_args.add_argument(
        "--logfile", type=str, help="location of JSON file", required=True
    )
    required_args.add_argument(
        "--dest", type=str, help="destination folder", required=True
    )
    required_args.add_argument(
        "--src", type=str, help="source image folder", required=True
    )
    argparser._action_groups.append(optional_args)
    argparser.add_argument(
        "--geo",
        help='lat/long for geocoding images (use --geo="-45,32" when latitude is negative)',
        action="store",
        default=None,
        type=parse_coords,
    )
    argparser.add_argument(
        "--alt",
        help="altitude for geocoding image",
        type=float,
        action="store",
        default=None,
    )
    argparser.add_argument(
        "--tags",
        help="command separated list of for the image",
        type=parse_tags,
        action="store",
        default=None,
    )

    args = argparser.parse_args()

    main(args.src, args.dest, args.logfile, args.geo, alt=args.alt, tags=args.tags)
