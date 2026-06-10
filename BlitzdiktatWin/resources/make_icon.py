from PIL import Image, ImageDraw
import os

sizes = [16, 32, 48, 64, 128, 256]
base = r"C:\Github\blitztext-app-main\BlitztextMac\Resources\Assets.xcassets\AppIcon.appiconset"
out = os.path.join(os.path.dirname(__file__), "blitztext.ico")

frames = []
for size in sizes:
    for name in [f"icon_{size}x{size}.png", f"icon_{size}x{size}@2x.png"]:
        path = os.path.join(base, name)
        if os.path.exists(path):
            frames.append(Image.open(path).convert("RGBA").resize((size, size), Image.LANCZOS))
            break

if not frames:
    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([2, 2, size - 2, size - 2], fill="#1E293B")
        scale = size / 64
        pts = [(int(x * scale), int(y * scale)) for x, y in [
            (36, 4), (20, 32), (32, 32), (28, 60), (44, 32), (32, 32), (36, 4)
        ]]
        d.polygon(pts, fill="white")
        frames.append(img)

frames[0].save(out, format="ICO", sizes=[(f.width, f.height) for f in frames], append_images=frames[1:])
print("ICO erstellt:", out)
