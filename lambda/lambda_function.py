import io
import os
import urllib.parse

import boto3
from PIL import Image, ImageOps

s3 = boto3.client("s3")

DEST_BUCKET = os.environ["DEST_BUCKET"]
THUMBNAIL_SIZE = (128, 128)
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def resize_image(source_bucket, key):
    extension = os.path.splitext(key)[1].lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {extension}")

    body = s3.get_object(Bucket=source_bucket, Key=key)["Body"].read()

    with Image.open(io.BytesIO(body)) as image:
        image_format = image.format
        thumbnail = ImageOps.exif_transpose(image)
        thumbnail.thumbnail(THUMBNAIL_SIZE)
        buffer = io.BytesIO()
        thumbnail.save(buffer, format=image_format)

    buffer.seek(0)
    s3.put_object(Bucket=DEST_BUCKET, Key=key, Body=buffer, ContentType=f"image/{image_format.lower()}")
    return key


def lambda_handler(event, context):
    if "Records" in event:
        # Direct S3 upload trigger
        record = event["Records"][0]["s3"]
        bucket = record["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["object"]["key"])
    else:
        # Step Functions input: {"bucket": "...", "key": "..."}
        bucket = event["bucket"]
        key = event["key"]

    try:
        resize_image(bucket, key)
    except Exception as error:
        print(f"Failed to resize {key}: {error}")
        return {"status": "FAILED", "key": key, "error": str(error)}

    return {"status": "SUCCESS", "key": key, "thumbnail": f"s3://{DEST_BUCKET}/{key}"}