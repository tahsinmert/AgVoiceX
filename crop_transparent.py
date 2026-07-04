from PIL import Image
import sys

def crop_transparent(input_path, output_path):
    img = Image.open(input_path)
    img = img.convert("RGBA")
    
    # getbbox() finds the bounding box of the non-zero alpha regions
    bbox = img.getbbox()
    if bbox:
        img_cropped = img.crop(bbox)
        img_cropped.save(output_path, "PNG")
    else:
        print("No bounding box found (image might be fully transparent).")

crop_transparent(sys.argv[1], sys.argv[2])
