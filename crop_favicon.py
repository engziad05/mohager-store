from PIL import Image

def create_favicon(image_path, output_path):
    img = Image.open(image_path).convert("RGBA")
    # Get bounding box of non-transparent pixels
    bbox = img.getbbox()
    if bbox:
        # Crop the image to its non-transparent bounds
        img_cropped = img.crop(bbox)
        
        # We want the favicon to be square, so let's create a square background
        max_size = max(img_cropped.size)
        square = Image.new('RGBA', (max_size, max_size), (0, 0, 0, 0))
        
        # Paste the cropped image into the center of the square
        offset = ((max_size - img_cropped.width) // 2, (max_size - img_cropped.height) // 2)
        square.paste(img_cropped, offset)
        
        # Optional: Resize to standard favicon size (e.g., 256x256) for smaller file size
        square = square.resize((256, 256), Image.Resampling.LANCZOS)
        
        square.save(output_path, format="PNG")
        print(f"Successfully saved cropped favicon to {output_path}")
    else:
        print("Image is entirely transparent.")

if __name__ == '__main__':
    create_favicon('static/images/logo-Photoroom.png', 'static/images/favicon.png')
