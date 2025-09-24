from PIL import Image

img = Image.open(r"C:\Users\ayu11\Downloads\ak3668134_Modern_minimalist_logo_design_inspired_by_Slack_style_26bae322-b191-49eb-b15e-c5b363857b0f.png").convert("RGBA")
datas = img.getdata()

new_data = []
for item in datas:
    # 白に近いピクセルを透明化
    if item[0] > 240 and item[1] > 240 and item[2] > 240:
        new_data.append((255, 255, 255, 0))
    else:
        new_data.append(item)

img.putdata(new_data)
img.save("logo_transparent.png", "PNG")
