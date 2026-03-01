"""
Create Installer Assets from Logo
==================================

This script creates all required installer images from the main logo.png:
- logo.bmp (500x300) - Inno Setup sidebar banner (larger, more visible)
- logo.ico (256x256) - Setup and application icon
- logo_small.bmp (150x90) - Small header logo (larger)
- logo_large.bmp (600x314) - Large banner
"""

from PIL import Image
import os

def create_installer_assets():
    """Create all installer assets from logo.png"""
    
    # Paths
    source_path = os.path.join("assets", "logo", "logo.png")
    output_dir = os.path.join("installer", "setup_assets")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Loading source image: {source_path}")
    
    # Load source image
    img = Image.open(source_path)
    print(f"Source image size: {img.size}")
    print(f"Source image mode: {img.mode}")
    
    # Convert to RGBA if needed
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # ============================================
    # 1. Create Sidebar Banner (500x300 pixels) - LARGER
    # ============================================
    # This is the main banner shown on the left side of installer
    banner_width = 500
    banner_height = 300
    
    # Create banner with proper aspect ratio
    banner = Image.new('RGBA', (banner_width, banner_height), (255, 255, 255, 255))
    
    # Calculate scaling to fit logo in banner while maintaining aspect ratio
    img_ratio = img.width / img.height
    banner_ratio = banner_width / banner_height
    
    if img_ratio > banner_ratio:
        # Image is wider - fit to width
        new_width = banner_width - 40  # 20px padding on each side
        new_height = int(new_width / img_ratio)
    else:
        # Image is taller - fit to height
        new_height = banner_height - 40  # 20px padding top and bottom
        new_width = int(new_height * img_ratio)
    
    # Resize logo
    resized_logo = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Center the logo on the banner
    x_offset = (banner_width - new_width) // 2
    y_offset = (banner_height - new_height) // 2
    
    banner.paste(resized_logo, (x_offset, y_offset), resized_logo)
    
    # Convert to RGB for BMP (no transparency in BMP)
    banner_rgb = Image.new('RGB', (banner_width, banner_height), (255, 255, 255))
    banner_rgb.paste(banner, (0, 0), banner)
    
    banner_path = os.path.join(output_dir, "logo.bmp")
    banner_rgb.save(banner_path, "BMP")
    print(f"Created: {banner_path} ({banner_width}x{banner_height})")
    
    # ============================================
    # 2. Create Application Icon (256x256 pixels)
    # ============================================
    # Icon for setup.exe and application
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    
    # Create square icon
    icon_size = 256
    icon = Image.new('RGBA', (icon_size, icon_size), (0, 0, 0, 0))
    
    # Scale logo to fit in icon
    scale = min(icon_size / img.width, icon_size / img.height) * 0.9
    new_width = int(img.width * scale)
    new_height = int(img.height * scale)
    
    resized_icon = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Center the logo
    x_offset = (icon_size - new_width) // 2
    y_offset = (icon_size - new_height) // 2
    
    icon.paste(resized_icon, (x_offset, y_offset), resized_icon)
    
    icon_path = os.path.join(output_dir, "logo.ico")
    
    # Save as ICO with multiple sizes
    icon.save(icon_path, format='ICO', sizes=icon_sizes)
    print(f"Created: {icon_path} (multi-size icon)")
    
    # Also save as PNG for reference
    icon_png_path = os.path.join(output_dir, "logo_icon.png")
    icon.save(icon_png_path, "PNG")
    print(f"Created: {icon_png_path} (256x256)")
    
    # ============================================
    # 3. Create Small Header Logo (150x90 pixels) - LARGER
    # ============================================
    small_width = 150
    small_height = 90
    small_logo = Image.new('RGBA', (small_width, small_height), (255, 255, 255, 255))
    
    # Scale logo to fit
    scale = min(small_width / img.width, small_height / img.height) * 0.85
    new_width = int(img.width * scale)
    new_height = int(img.height * scale)
    
    resized_small = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Center
    x_offset = (small_width - new_width) // 2
    y_offset = (small_height - new_height) // 2
    
    small_logo.paste(resized_small, (x_offset, y_offset), resized_small)
    
    # Convert to RGB for BMP
    small_rgb = Image.new('RGB', (small_width, small_height), (255, 255, 255))
    small_rgb.paste(small_logo, (0, 0), small_logo)
    
    small_path = os.path.join(output_dir, "logo_small.bmp")
    small_rgb.save(small_path, "BMP")
    print(f"Created: {small_path} ({small_width}x{small_height})")
    
    # ============================================
    # 4. Create Large Banner for Modern Installers (600x314)
    # ============================================
    large_width = 600
    large_height = 314
    
    large_banner = Image.new('RGBA', (large_width, large_height), (255, 255, 255, 255))
    
    # Scale logo
    scale = min(large_width / img.width, large_height / img.height) * 0.85
    new_width = int(img.width * scale)
    new_height = int(img.height * scale)
    
    resized_large = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Center
    x_offset = (large_width - new_width) // 2
    y_offset = (large_height - new_height) // 2
    
    large_banner.paste(resized_large, (x_offset, y_offset), resized_large)
    
    # Convert to RGB
    large_rgb = Image.new('RGB', (large_width, large_height), (255, 255, 255))
    large_rgb.paste(large_banner, (0, 0), large_banner)
    
    large_path = os.path.join(output_dir, "logo_large.bmp")
    large_rgb.save(large_path, "BMP")
    print(f"Created: {large_path} ({large_width}x{large_height})")
    
    # ============================================
    # 5. Copy icon to assets/logo for app icon
    # ============================================
    app_icon_path = os.path.join("assets", "logo", "logo.ico")
    icon.save(app_icon_path, format='ICO', sizes=icon_sizes)
    print(f"Created: {app_icon_path} (application icon)")
    
    print("\n" + "=" * 50)
    print("All installer assets created successfully!")
    print("=" * 50)
    print(f"\nOutput directory: {output_dir}")
    print("\nFiles created:")
    print(f"  - logo.bmp (500x300) - Sidebar banner")
    print(f"  - logo.ico (multi-size) - Setup icon")
    print(f"  - logo_small.bmp (150x90) - Header icon")
    print(f"  - logo_large.bmp (600x314) - Large banner")
    print(f"  - logo_icon.png (256x256) - PNG reference")

if __name__ == "__main__":
    create_installer_assets()
