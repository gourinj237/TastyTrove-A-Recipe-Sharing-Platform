import os
import re
import json

recipe_files = [
    ("avo.html", "Breakfast", "https://www.moltofood.it/wp-content/uploads/2022/07/avocado-toast.jpg"),
    ("omelette.html", "Breakfast", "https://www.thespruceeats.com/thmb/aWJ4W5Z6Ksf8VKl_WOT6gCGUMUw=/4200x2800/filters:fill(auto,1)/vegetarian-omelette-with-bell-peppers-3376569-hero-4-c276751995104c1e917070e911d2d677.jpg"),
    ("masala.html", "Breakfast", "/static/uploads/masaladosa.jpg"),
    ("lentil.html", "Breakfast", "https://www.allrecipes.com/thmb/UeFtapHyGFBo4Lx-72GxgjrOGnk=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/13978-lentil-soup-DDMFS-4x3-edfa47fc6b234e6b8add24d44c036d43.jpg"),
    ("bfc.html", "Desserts", "https://static01.nyt.com/images/2020/01/15/dining/ss-black-forest-cake/merlin_165684495_6689b1a0-42b5-4228-b871-37bb983d797e-superJumbo.jpg"),
    ("clc.html", "Desserts", "https://www.melskitchencafe.com/wp-content/uploads/2023/01/updated-lava-cakes7.jpg"),
    ("donut.html", "Desserts", "https://cdn.britannica.com/38/230838-050-D0173E79/doughnuts-donuts.jpg"),
    ("kheer.html", "Desserts", "https://aartimadan.com/wp-content/uploads/2019/07/rice-kheer-recipe-images-6.jpg"),
    ("chilli.html", "Snacks & Fast Foods", "http://www.herbsjoy.com/wp-content/uploads/2024/11/maxresdefault-3.jpg"),
    ("garlic.html", "Snacks & Fast Foods", "https://2.bp.blogspot.com/-anC6Uz0i6Gs/UZGsPH_RBOI/AAAAAAAAGx4/JuIu-ldKoGA/s1600/garlic-cheese-bread-2.jpg"),
    ("corn.html", "Snacks & Fast Foods", "https://img.taste.com.au/EfTLm0Fe/taste/2016/11/corn-fritters-with-avocado-cream-22235-1.jpeg"),
    ("nuggets.html", "Snacks & Fast Foods", "https://2.bp.blogspot.com/-5C4ooQRBlZ0/XDg5fFMqINI/AAAAAAAAD9E/J5JxPZpGh50CXhHhwpp341hmIwNJxbNtACLcBGAs/s1600/chicken-nuggets-with-ketchup-537703317-5a938584119fa80037581cc2.jpg"),
    ("chai.html", "Drinks", "/static/uploads/Indian-Masala-Chai-Spiced-Tea-Cover.jpg"),
    ("lemon.html", "Drinks", "https://d2lswn7b0fl4u2.cloudfront.net/photos/pg-lemon-iced-tea-1668715738.jpg"),
    ("smoothie.html", "Drinks", "https://www.tasteofhome.com/wp-content/uploads/2019/04/mango-smoothie-shutterstock_1007270005.jpg?w=1200")
]

ratings_map = {
    "avo.html": 4.2,
    "omelette.html": 4.0,
    "masala.html": 4.5,
    "quinoa.html": 4.1,
    "lentil.html": 4.3,
    "bfc.html": 4.6,
    "clc.html": 4.0,
    "donut.html": 4.4,
    "kheer.html": 4.2,
    "chilli.html": 4.2,
    "garlic.html": 4.2,
    "corn.html": 4.2,
    "nuggets.html": 4.0,
    "chai.html": 4.2,
    "lemon.html": 4.4,
    "smoothie.html": 4.2
}

recipes_data = []

for filename, category, image_url in recipe_files:
    if not os.path.exists(filename):
        print(f"Skipping {filename} - not found")
        continue
        
    with open(filename, 'r', encoding='utf-8') as f:
        html = f.read()
        
    # Extract title
    title_match = re.search(r'<p class="p1">(.*?)</p>', html)
    title = title_match.group(1).strip() if title_match else filename.replace(".html", "").title()
    
    # Extract time string
    time_match = re.search(r'<p class="p2">⏱️\s*(.*?)</p>', html)
    time_str = time_match.group(1).strip() if time_match else "15 mins"
    
    # Convert time to integer minutes
    time_mins = 15
    if "hour" in time_str:
        try:
            val_str = time_str.split("hour")[0].strip()
            # Handle ranges like 2-3 hours
            if "-" in val_str:
                val_str = val_str.split("-")[1].strip()
            time_mins = int(float(val_str) * 60)
        except Exception:
            time_mins = 120
    else:
        try:
            val_str = time_str.split("min")[0].strip()
            if "-" in val_str:
                val_str = val_str.split("-")[1].strip()
            time_mins = int(val_str)
        except Exception:
            time_mins = 15
            
    # Extract description
    desc_match = re.search(r'<p class="p3">(.*?)</p>', html, re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else ""
    
    # Extract ingredients (between <ul> and </ul>)
    ingredients_match = re.search(r'<ul>(.*?)</ul>', html, re.DOTALL)
    ingredients = []
    if ingredients_match:
        items = re.findall(r'<li>(.*?)</li>', ingredients_match.group(1))
        ingredients = [item.strip() for item in items]
    
    # Extract instructions (all <p> elements between Instructions header and the first <a> link)
    instructions_section = ""
    # Find start of instructions
    inst_header_idx = html.find('<p class="p4">Instructions</p>')
    if inst_header_idx == -1:
        # try lowercase or other classes
        inst_header_idx = html.find('Instructions')
        
    if inst_header_idx != -1:
        rest = html[inst_header_idx:]
        # find the first <a> tag after this
        first_a_idx = rest.find('<a href=')
        if first_a_idx != -1:
            instructions_html = rest[:first_a_idx]
        else:
            instructions_html = rest
        # find all <p> tags in this block
        p_tags = re.findall(r'<p>(.*?)</p>', instructions_html, re.DOTALL)
        # remove step numbers or just strip them
        instructions = [p.strip() for p in p_tags if p.strip()]
    else:
        instructions = []
        
    # Extract video links
    # Search for all links with youtube
    yt_links = re.findall(r'<a href="(https://(?:www\.)?youtube\.com/.*?)">(.*?)</a>', html)
    video_url_ml = ""
    video_url_en = ""
    for url, text in yt_links:
        if "Malayalam" in text or "malayalam" in text.lower():
            video_url_ml = url
        elif "English" in text or "english" in text.lower():
            video_url_en = url
            
    # Default to first link if only one and not specified
    if not video_url_ml and not video_url_en and yt_links:
        video_url_en = yt_links[0][0]
        if len(yt_links) > 1:
            video_url_ml = yt_links[1][0]
            
    recipe_dict = {
        "title": title,
        "time": time_mins,
        "rating": ratings_map.get(filename, 4.2),
        "rating_count": 5, # seed 5 ratings initially
        "rating_sum": ratings_map.get(filename, 4.2) * 5,
        "description": description,
        "ingredients": "\n".join(ingredients),
        "instructions": "\n".join(instructions),
        "category": category,
        "image_url": image_url,
        "author": "TastyTrove Chef",
        "video_url_ml": video_url_ml,
        "video_url_en": video_url_en,
        "likes": 12
    }
    recipes_data.append(recipe_dict)

with open("seed_recipes.json", "w", encoding="utf-8") as f:
    json.dump(recipes_data, f, indent=4)

print("Parsed recipes successfully!")
