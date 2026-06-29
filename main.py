from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import os
import math
import random

app = Ursina()

# Hardware optimization for ThinkPad X220
window.title = "Python Life Sim 3D"
window.fps_counter.enabled = True

# --- CONFIGURATION PATHS ---
character_dir = 'assets/OBJ Character/'
character_tex_dir = 'assets/OBJ Character/Textures/'
suburban_dir = 'assets/OBJ Suburban/'
cars_dir = 'assets/OBJ Cars/'
furniture_dir = 'assets/OBJ Furniture/'

def find_texture(folder_path):
    sub_path = os.path.join(folder_path, 'Textures', 'colormap.png')
    root_path = os.path.join(folder_path, 'colormap.png')
    any_png = [f for f in os.listdir(folder_path) if f.endswith('.png')] if os.path.exists(folder_path) else []
    
    if os.path.exists(sub_path): return sub_path
    elif os.path.exists(root_path): return root_path
    elif any_png: return os.path.join(folder_path, any_png[0])
    return None

suburban_tex = find_texture(suburban_dir)
cars_tex = find_texture(cars_dir)
furniture_tex = find_texture(furniture_dir)

# --- LOADING THE ASSET LISTS ---
try:
    available_characters = [f.split('.')[0] for f in os.listdir(character_dir) if f.endswith('.obj')]
    available_characters.sort()
except: available_characters = ['character-a']

try:
    available_buildings = [f for f in os.listdir(suburban_dir) if f.endswith('.obj')]
    available_buildings.sort()
except: available_buildings = []

try:
    available_cars = [f.split('.')[0] for f in os.listdir(cars_dir) if f.endswith('.obj') and not f.startswith('wheel') and not f.startswith('debris')]
    available_cars.sort()
except: available_cars = []

try:
    furniture_items = [f for f in os.listdir(furniture_dir) if f.endswith('.obj')]
    furniture_items.sort()
except: furniture_items = []

current_index = 0
player_name = "Player 1"
game_started = False

# Player Stats Tracker
player_money = 1200  
player_energy = 100.0         
current_job_title = "Unemployed"
current_job_salary = 0
owned_houses_ids = []  

is_driving = False
owned_car_model = None

# Day & Night Environment Cycle State Variables
time_of_day = 0.0  
sky_ref = None

# UI Menu States
dealership_menu_open = False
car_catalog_index = 0

# --- FEATURE VARIABLES ---
SPAWN_POINT = (0, 2, 0)
INTERIOR_SPAWN = (0, -98, 0)
is_inside_house = False

furniture_shop_open = False
shop_catalog_index = 0

# --- NEW KEYBOARD EDITING VARIABLES ---
selected_furniture_to_place = None  # Holds the string filename
active_placement_entity = None      # Holds the temporary moving Entity object

furniture_prices = {}
if furniture_items:
    for index, item in enumerate(furniture_items):
        furniture_prices[item] = 50 + (index * 25)

active_mission = None
job_tiers = {'Courier': 1.5, 'Pro Driver': 3.0, 'Luxury Transport': 5.0}
car_specs = {
    'sedan': {'speed': 40},
    'sports_car': {'speed': 75},
    'truck': {'speed': 30}
}

# World Tracking Lists
all_city_buildings = []
all_city_npcs = []
parked_car_entity = None  

def get_current_texture(index):
    char_name = available_characters[index]
    letter = char_name.split('-')[-1]
    return f'{character_tex_dir}texture-{letter}.png'

# --- UI START MENU ---
menu_parent = Entity(enabled=True)
camera.orthographic = True
camera.fov = 10

name_input = InputField(default_value='Enter Name', parent=menu_parent, y=2, scale=(5, 0.5))
preview_character = Entity(
    parent=menu_parent, model=f'{character_dir}{available_characters[current_index]}.obj',
    texture=get_current_texture(current_index), position=(0, -2, 0), rotation=(0, 180, 0), scale=2
)

title_text = Text(text="CHARACTER CREATION", parent=menu_parent, y=3.5, scale=2, origin=(0,0))
help_text = Text(text="[A] Previous | [D] Next | [SPACE] to Start", parent=menu_parent, y=-3.5, scale=1.2, origin=(0,0))

def change_character(direction):
    global current_index
    current_index = (current_index + direction) % len(available_characters)
    preview_character.model = f'{character_dir}{available_characters[current_index]}.obj'
    preview_character.texture = get_current_texture(current_index)

def start_game():
    global game_started, player_name
    player_name = name_input.text
    menu_parent.disable()       
    game_started = True
    setup_game_world()          

# --- WORLD GENERATION ---
world_parent = Entity(enabled=False)
player_entity = None
hud_text = None
interaction_text = None
driven_car_visual = None
dealership_ui_panel = None
police_siren_overlay = None

mission_hud_panel = None
furniture_shop_panel = None
furniture_build_panel = None

def setup_game_world():
    global player_entity, hud_text, interaction_text, dealership_ui_panel, all_city_buildings, sky_ref, all_city_npcs, police_siren_overlay, mission_hud_panel, furniture_shop_panel, furniture_build_panel
    world_parent.enable()
    camera.orthographic = False  
    
    sky_ref = Sky(color=color.light_gray)
    
    # Grass Background
    Entity(parent=world_parent, model='cube', scale=(3000, 2, 3000), color=color.green, unlit=True, position=(0, -1, 0), collider='box')
    
    # Asphalt Highways
    Entity(parent=world_parent, model='cube', scale=(50, 0.02, 3000), color=color.black, unlit=True, position=(0, 0.01, 0))
    Entity(parent=world_parent, model='cube', scale=(3000, 0.02, 50), color=color.black, unlit=True, position=(0, 0.01, 40))

    # --- House Interior Room ---
    interior_parent = Entity(parent=world_parent, position=(0, -100, 0))
    
    # Floor
    Entity(
        parent=interior_parent, model='cube', scale=(40, 1, 40), color=color.brown, 
        texture='white_cube', collider='box', position=(0, -0.5, 0), name='interior_floor'
    )
    
    # Walls
    Entity(parent=interior_parent, model='cube', scale=(40, 10, 1), color=color.salmon, collider='box', position=(0, 4.5, 20))
    Entity(parent=interior_parent, model='cube', scale=(40, 10, 1), color=color.salmon, collider='box', position=(0, 4.5, -20))
    Entity(parent=interior_parent, model='cube', scale=(1, 10, 40), color=color.salmon, collider='box', position=(20, 4.5, 0))
    Entity(parent=interior_parent, model='cube', scale=(1, 10, 40), color=color.salmon, collider='box', position=(-20, 4.5, 0))
    
    # Exit Door Mat Visual
    Entity(parent=interior_parent, model='cube', scale=(6, 0.1, 4), color=color.red, position=(0, 0.01, -18))

    AmbientLight(parent=world_parent, color=color.rgba(220, 220, 220, 255))
    
    building_roles = ["House", "Job", "Dealership", "Shop"]
    job_types = [
        {"title": "Local Clerk", "salary": 25, "energy": 15},
        {"title": "Office Manager", "salary": 60, "energy": 25},
        {"title": "Tech CEO", "salary": 150, "energy": 40}
    ]

    for index, bld_file in enumerate(available_buildings):
        z_pos = 80 + (index * 95)
        
        # Left Side
        role_left = random.choice(building_roles) if index > 3 else building_roles[index % 4]
        bld_left_data = {
            "unique_id": f"left_{index}", 
            "role": role_left, 
            "price": random.randint(100, 300) if role_left == "House" else random.randint(350, 600),
            "pos": (-65, 0, z_pos)
        }
        if role_left == "Job": bld_left_data["job"] = random.choice(job_types)
            
        house_left = Entity(
            parent=world_parent, model=f'{suburban_dir}{bld_file}', texture=suburban_tex,
            position=bld_left_data["pos"], rotation=(0, 90, 0), scale=14, collider='box'
        )
        house_left.collider.scale = (0.7, 1, 0.7)
        if role_left == "Job": house_left.color = color.light_gray
        elif role_left == "Dealership": house_left.color = color.azure
        elif role_left == "Shop": house_left.color = color.lime
        all_city_buildings.append(bld_left_data)

        # Right Side
        role_right = random.choice(building_roles) if index > 3 else building_roles[(index + 1) % 4]
        bld_right_data = {
            "unique_id": f"right_{index}", 
            "role": role_right, 
            "price": random.randint(120, 500),
            "pos": (65, 0, z_pos)
        }
        if role_right == "Job": bld_right_data["job"] = random.choice(job_types)
            
        house_right = Entity(
            parent=world_parent, model=f'{suburban_dir}{bld_file}', texture=suburban_tex,
            position=bld_right_data["pos"], rotation=(0, -90, 0), scale=14, collider='box'
        )
        house_right.collider.scale = (0.7, 1, 0.7)
        if role_right == "Job": house_right.color = color.light_gray
        elif role_right == "Dealership": house_right.color = color.azure
        elif role_right == "Shop": house_right.color = color.lime
        all_city_buildings.append(bld_right_data)

        # NPCs
        if len(available_characters) > 0:
            npc_char_idx = min(len(available_characters)-1, (index % max(1, len(available_characters))))
            npc_entity = Entity(
                parent=world_parent, model=f'{character_dir}{available_characters[npc_char_idx]}.obj',
                texture=f'{character_tex_dir}texture-{available_characters[npc_char_idx].split("-")[-1]}.png',
                position=(random.choice([-32, 32]), 0, z_pos + random.randint(-20, 20)),
                scale=1.4, rotation=(0, random.choice([0, 180]), 0)
            )
            npc_entity.start_z = z_pos - 30
            npc_entity.end_z = z_pos + 30
            npc_entity.direction = 1
            all_city_npcs.append(npc_entity)

    # Player
    player_entity = FirstPersonController(parent=world_parent)
    player_entity.position = SPAWN_POINT  
    player_entity.cursor.visible = False
    player_entity.speed = 12
    
    hud_text = Text(text="", position=(-0.85, 0.45), scale=1.5, color=color.yellow)
    interaction_text = Text(text="", position=(0, -0.3), scale=1.5, color=color.azure, origin=(0,0))
    
    police_siren_overlay = Entity(parent=camera.ui, model='quad', scale=(2, 2), color=color.rgba(255, 0, 0, 0), enabled=True)

    # Car Showroom UI
    dealership_ui_panel = Entity(enabled=False, parent=camera.ui, model='quad', scale=(0.7, 0.5), color=color.black66, position=(0,0))
    dealership_ui_panel.title = Text(text="DEALERSHIP CATALOG", parent=dealership_ui_panel, y=0.4, scale=2, origin=(0,0), color=color.gold)
    dealership_ui_panel.car_name = Text(text="Car Model", parent=dealership_ui_panel, y=0.1, scale=1.8, origin=(0,0))
    dealership_ui_panel.car_price = Text(text="Price: $120", parent=dealership_ui_panel, y=-0.1, scale=1.5, origin=(0,0), color=color.green)
    dealership_ui_panel.controls = Text(text="[A/Left] Prev | [D/Right] Next\n[B] Purchase Car\n[E/ESC] Close Showroom Menu", parent=dealership_ui_panel, y=-0.3, scale=1.2, origin=(0,0))

    # Furniture Store Menu UI
    furniture_shop_panel = Entity(enabled=False, parent=camera.ui, model='quad', scale=(0.75, 0.55), color=color.black90, position=(0,0))
    furniture_shop_panel.title = Text(text="FURNITURE STORE CATALOG", parent=furniture_shop_panel, y=0.4, scale=2, origin=(0,0), color=color.lime)
    furniture_shop_panel.item_name = Text(text="Item Name", parent=furniture_shop_panel, y=0.1, scale=1.8, origin=(0,0))
    furniture_shop_panel.item_price = Text(text="Price: $50", parent=furniture_shop_panel, y=-0.1, scale=1.5, origin=(0,0), color=color.yellow)
    furniture_shop_panel.controls = Text(text="[A/Left] Prev Item | [D/Right] Next Item\n[B] Buy & Spawn item\n[E/ESC] Close Catalog Menu", parent=furniture_shop_panel, y=-0.3, scale=1.1, origin=(0,0))

    # --- 🔨 UPDATED: KEYBOARD BUILD MODE DISPLAY BANNER ---
    furniture_build_panel = Entity(enabled=False, parent=camera.ui, model='quad', scale=(0.85, 0.25), color=color.black90, position=(0, 0.35))
    furniture_build_panel.txt = Text(text="--- KEYBOARD PLACEMENT ACTIVE ---\nUse [ARROW KEYS] to Move Furniture Around\nPress [ENTER] to Finish and Save", parent=furniture_build_panel, scale=1.8, origin=(0,0), color=color.cyan)

    mission_hud_panel = Text(text="", position=(-0.85, -0.3), scale=1.3, color=color.cyan)

    update_hud()

def respawn_player():
    global player_energy, active_mission, is_driving, driven_car_visual, is_inside_house, active_placement_entity
    if is_driving:
        is_driving = False
        if driven_car_visual: destroy(driven_car_visual)
        camera.y = 0
    is_inside_house = False
    if active_placement_entity:
        destroy(active_placement_entity)
        active_placement_entity = None
    furniture_build_panel.disable()
    player_entity.position = SPAWN_POINT
    player_energy = max(40.0, player_energy)
    active_mission = None
    update_hud()
    print("Emergency Respawn Triggered!")

def update_hud():
    global hud_text, active_mission, mission_hud_panel
    if hud_text:
        houses_count = len(owned_houses_ids)
        car_status = f"Owned ({owned_car_model.title()})" if owned_car_model else "None"
        location_tag = "Inside House" if is_inside_house else "City Streets"
        
        hud_text.text = (
            f"Name: {player_name} | Location: {location_tag}\n"
            f"Cash: ${player_money} | Energy: {int(player_energy)}%\n"
            f"Job: {current_job_title} (Salary: ${current_job_salary})\n"
            f"Properties: Owned {houses_count} | Car: {car_status}\n\n"
            f"[Q/ESC] Exit Game | [R] Respawn Point"
        )
    
    if mission_hud_panel:
        if active_mission:
            mission_hud_panel.text = (
                f"--- ACTIVE DELIVERY ---\n"
                f"Tier: {active_mission['job']}\n"
                f"Payout: ${active_mission['payment']}\n"
                f"Time Left: {int(active_mission['time'])}s\n"
                f"Distance to Target: {int(distance(player_entity.position, active_mission['target_pos']))}m"
            )
            mission_hud_panel.color = color.red if active_mission['time'] < 15 else color.cyan
        else:
            mission_hud_panel.text = "Job Status: Visit city NPCs [E] for Delivery Missions"
            mission_hud_panel.color = color.light_gray

def update_dealership_ui():
    global dealership_ui_panel, car_catalog_index
    if available_cars and dealership_ui_panel:
        current_model_name = available_cars[car_catalog_index].replace('_', ' ').title()
        dealership_ui_panel.car_name.text = f"Model: {current_model_name}"
        dealership_ui_panel.car_price.text = f"Price: $120"

def update_furniture_shop_ui():
    global furniture_shop_panel, shop_catalog_index
    if furniture_items and furniture_shop_panel:
        current_item = furniture_items[shop_catalog_index]
        display_name = current_item.replace('.obj', '').replace('_', ' ').title()
        cost = furniture_prices.get(current_item, 50)
        furniture_shop_panel.item_name.text = f"Item: {display_name}"
        furniture_shop_panel.item_price.text = f"Cost: ${cost}"

def update():
    global player_money, player_energy, is_driving, interaction_text, dealership_menu_open, furniture_shop_open, parked_car_entity, time_of_day, sky_ref, all_city_npcs, police_siren_overlay, active_mission, is_inside_house, active_placement_entity
    if not game_started or not player_entity:
        return

    # --- 🔨 REAL-TIME KEYBOARD MOVEMENT FOR ACTIVE FURNITURE ---
    if active_placement_entity and furniture_build_panel.enabled:
        move_speed = time.dt * 12
        if held_keys['up arrow']:    active_placement_entity.z += move_speed
        if held_keys['down arrow']:  active_placement_entity.z -= move_speed
        if held_keys['left arrow']:  active_placement_entity.x -= move_speed
        if held_keys['right arrow']: active_placement_entity.x += move_speed
        player_entity.speed = 0 # Lock the player down while they build
        return

    if dealership_menu_open or furniture_shop_open:
        player_entity.speed = 0
        return

    # Day & Night
    time_of_day += time.dt * 0.01  
    if time_of_day > 1.0: time_of_day = 0.0
    sky_ref.color = color.light_gray if time_of_day < 0.5 else color.rgba(40, 44, 52, 255)

    is_moving = held_keys['w'] or held_keys['s'] or held_keys['a'] or held_keys['d']
    if is_moving or is_driving:
        drain_factor = 1.6 if is_driving else 0.9
        player_energy = max(0.0, player_energy - (time.dt * drain_factor))
        update_hud()
    
    if player_energy <= 0:
        player_money = max(0, player_money - 20)
        player_energy = 40.0
        respawn_player()

    if active_mission:
        active_mission['time'] -= time.dt
        update_hud()
        if distance(player_entity.position, active_mission['target_pos']) < 22:
            player_money += active_mission['payment']
            active_mission = None
            update_hud()
        elif active_mission['time'] <= 0:
            active_mission = None
            update_hud()

    if police_siren_overlay.color.a > 0:
        police_siren_overlay.color = color.rgba(255, 0, 0, max(0, int(police_siren_overlay.color.rgba[3] - time.dt * 150)))

    if is_inside_house:
        player_entity.speed = 10
        interaction_text.text = ""
        if distance(player_entity.position, Vec3(0, -100, -18)) < 6:
            interaction_text.text = "Exit Door. Press [E] to Return to City Streets\nPress [I] to open Furniture Catalog Shop"
        else:
            interaction_text.text = "Inside Property. Press [I] to open Furniture Catalog Shop"
        return

    for npc in all_city_npcs:
        npc.z += time.dt * 4 * npc.direction
        if npc.z > npc.end_z:
            npc.direction = -1
            npc.rotation_y = 180
        elif npc.z < npc.start_z:
            npc.direction = 1
            npc.rotation_y = 0
            
        if is_driving and distance(player_entity.position, npc.position) < 8:
            player_money = max(0, player_money - 50)
            police_siren_overlay.color = color.rgba(255, 0, 0, 180) 
            npc.z += 25 * npc.direction 
            update_hud()

    interaction_text.text = ""
    near_any_target = False

    if not is_driving:
        for bld in all_city_buildings:
            if distance(player_entity.position, bld["pos"]) < 24:
                near_any_target = True
                if bld["role"] == "House":
                    if bld["unique_id"] in owned_houses_ids:
                        interaction_text.text = "Your House. Press [E] to Enter Interior | [H] to Sleep (+50 Energy)"
                    else:
                        interaction_text.text = f"Residential House. Press [H] to Buy Property (${bld['price']})"
                elif bld["role"] == "Job":
                    job_info = bld["job"]
                    if current_job_title == job_info["title"]:
                        interaction_text.text = f"Your Workplace. Press [E] to Work Shift (+${job_info['salary']} | -{job_info['energy']} Energy)"
                    else:
                        interaction_text.text = f"Corporate Hub. Press [E] to Apply for '{job_info['title']}' Job (Pays: ${job_info['salary']})"
                elif bld["role"] == "Dealership":
                    interaction_text.text = f"Dealership Lot. Press [E] to Browse Car Catalog"
                elif bld["role"] == "Shop":
                    interaction_text.text = "Grocery Store. Press [E] to Buy a Fast Food Burger ($15 | +35 Energy)"
                break

        if not near_any_target and not active_mission:
            for npc in all_city_npcs:
                if distance(player_entity.position, npc.position) < 7:
                    interaction_text.text = "City Resident. Press [E] to Accept a Delivery Mission Contract"
                    break

    if is_driving:
        base_car_key = owned_car_model.lower() if owned_car_model else 'sedan'
        matched_speed = car_specs.get(base_car_key, {'speed': 40})['speed']
        player_entity.speed = matched_speed
    else: 
        player_entity.speed = 12  

    if owned_car_model and not near_any_target:
        if is_driving:
            interaction_text.text = "Driving! Press [F] to Park and Step Out"
        elif parked_car_entity and distance(player_entity.position, parked_car_entity.position) < 15:
            interaction_text.text = f"Press [F] to Enter your {owned_car_model.title()} (1st Person)"

def input(key):
    global game_started, current_index, player_money, player_energy, current_job_title, current_job_salary, owned_houses_ids, owned_car_model, is_driving, driven_car_visual, dealership_menu_open, car_catalog_index, parked_car_entity, active_mission, is_inside_house, furniture_shop_open, shop_catalog_index, selected_furniture_to_place, furniture_shop_panel, furniture_build_panel, active_placement_entity
    
    if key == 'escape' or key == 'q':
        if dealership_menu_open:
            dealership_menu_open = False
            dealership_ui_panel.disable()
            mouse.locked = True
        elif furniture_shop_open:
            furniture_shop_open = False
            furniture_shop_panel.disable()
            mouse.locked = True
        else:
            application.quit()

    if not game_started:
        if key == 'd' or key == 'right arrow': change_character(1)
        elif key == 'a' or key == 'left arrow': change_character(-1)
        elif key == 'space': start_game()
        return

    # [R] Respawn Key
    if key == 'r':
        respawn_player()
        return

    # --- 🔨 SAVE PLACEMENT VIA [ENTER] ---
    if key == 'enter' and furniture_build_panel.enabled and active_placement_entity:
        # Highlighting off: return to natural model state color
        active_placement_entity.color = color.white
        active_placement_entity = None
        selected_furniture_to_place = None
        furniture_build_panel.disable()
        mouse.locked = True
        return

    # [I] Menu Toggle Action Logic
    if key == 'i' and is_inside_house and not furniture_build_panel.enabled:
        furniture_shop_open = not furniture_shop_open
        furniture_shop_panel.enabled = furniture_shop_open
        mouse.locked = not furniture_shop_open
        if furniture_shop_open:
            update_furniture_shop_ui()
        return

    # Catalog Store Interaction Actions
    if furniture_shop_open:
        if key == 'd' or key == 'right arrow':
            shop_catalog_index = (shop_catalog_index + 1) % len(furniture_items)
            update_furniture_shop_ui()
        elif key == 'a' or key == 'left arrow':
            shop_catalog_index = (shop_catalog_index - 1) % len(furniture_items)
            update_furniture_shop_ui()
        elif key == 'b' and furniture_items:
            current_item = furniture_items[shop_catalog_index]
            cost = furniture_prices.get(current_item, 50)
            if player_money >= cost:
                player_money -= cost
                selected_furniture_to_place = current_item
                update_hud()
                
                # Close the menu screen
                furniture_shop_open = False
                furniture_shop_panel.disable()
                furniture_build_panel.enable()
                mouse.locked = True
                
                # --- 🏢 SPAWN TARGET DIRECTLY IN THE MIDDLE OF THE ROOM ---
                active_placement_entity = Entity(
                    parent=world_parent, 
                    model=f'{furniture_dir}{selected_furniture_to_place}', 
                    texture=furniture_tex,
                    position=(0, -99.5, 0),     # Centered perfectly on the floor grid
                    scale=2.2, 
                    color=color.lime,           # Highlights it in a lime color while moving!
                    collider='box'
                )
            return
        elif key == 'e':
            furniture_shop_open = False
            furniture_shop_panel.disable()
            mouse.locked = True
        return

    if dealership_menu_open:
        if key == 'd' or key == 'right arrow':
            car_catalog_index = (car_catalog_index + 1) % len(available_cars)
            update_dealership_ui()
        elif key == 'a' or key == 'left arrow':
            car_catalog_index = (car_catalog_index - 1) % len(available_cars)
            update_dealership_ui()
        elif key == 'b':
            if player_money >= 120:
                player_money -= 120
                owned_car_model = available_cars[car_catalog_index]
                if parked_car_entity: destroy(parked_car_entity)
                parked_car_entity = Entity(
                    parent=world_parent, model=f'{cars_dir}{owned_car_model}.obj', texture=cars_tex,
                    position=(0, 0, player_entity.z + 6), scale=2.5, collider='box'
                )
                update_hud()
                dealership_menu_open = False
                dealership_ui_panel.disable()
                mouse.locked = True
        elif key == 'e':
            dealership_menu_open = False
            dealership_ui_panel.disable()
            mouse.locked = True
        return

    # Exit Interior
    if is_inside_house and key == 'e':
        if distance(player_entity.position, Vec3(0, -100, -18)) < 6:
            is_inside_house = False
            player_entity.position = SPAWN_POINT
            update_hud()
            return

    if not is_driving and not is_inside_house:
        near_building = False
        for bld in all_city_buildings:
            if distance(player_entity.position, bld["pos"]) < 24:
                near_building = True
                if key == 'e':
                    if bld["role"] == "House" and bld["unique_id"] in owned_houses_ids:
                        is_inside_house = True
                        player_entity.position = INTERIOR_SPAWN
                        update_hud()
                    elif bld["role"] == "Dealership" and available_cars:
                        dealership_menu_open = True
                        dealership_ui_panel.enable()
                        update_dealership_ui()
                    elif bld["role"] == "Job":
                        job_info = bld["job"]
                        if current_job_title == job_info["title"]:
                            if player_energy >= job_info["energy"]:
                                player_money += job_info["salary"]
                                player_energy -= job_info["energy"]
                            else:
                                interaction_text.text = "Too exhausted! Sleep at your house."
                        else:
                            current_job_title = job_info["title"]
                            current_job_salary = job_info["salary"]
                        update_hud()
                    elif bld["role"] == "Shop":
                        if player_money >= 15:
                            player_money -= 15
                            player_energy = min(100.0, player_energy + 35.0)
                        update_hud()
                
                elif key == 'h' and bld["role"] == "House":
                    if bld["unique_id"] in owned_houses_ids:
                        player_energy = min(100.0, player_energy + 50.0)
                    else:
                        if player_money >= bld["price"]:
                            player_money -= bld["price"]
                            owned_houses_ids.append(bld["unique_id"])
                    update_hud()
                break

        if not near_building and key == 'e' and not active_mission:
            for npc in all_city_npcs:
                if distance(player_entity.position, npc.position) < 7:
                    house_destinations = [b for b in all_city_buildings if b["role"] == "House"]
                    if house_destinations:
                        selected_destination = random.choice(house_destinations)
                        job_rank = random.choice(list(job_tiers.keys()))
                        dist_val = distance(player_entity.position, selected_destination["pos"])
                        calulated_payout = int((dist_val / 8) * job_tiers[job_rank])
                        
                        active_mission = {
                            'target_pos': selected_destination["pos"],
                            'payment': max(40, calulated_payout),
                            'time': 90.0,
                            'job': job_rank
                        }
                        update_hud()
                    break

    if key == 'f':
        if is_driving:
            is_driving = False
            if driven_car_visual: destroy(driven_car_visual)
            rad = math.radians(player_entity.rotation_y)
            car_x = player_entity.x + math.sin(rad) * 8
            car_z = player_entity.z + math.cos(rad) * 8
            
            parked_car_entity = Entity(
                parent=world_parent, model=f'{cars_dir}{owned_car_model}.obj', texture=cars_tex,
                position=(car_x, 0, car_z), rotation=(0, player_entity.rotation_y, 0),
                scale=2.5, collider='box'
            )
            player_entity.x -= math.sin(rad) * 3
            player_entity.z -= math.cos(rad) * 3
            camera.y = 0  
            update_hud()
            
        elif owned_car_model and parked_car_entity:
            if distance(player_entity.position, parked_car_entity.position) < 15:
                is_driving = True
                destroy(parked_car_entity)
                parked_car_entity = None
                
                driven_car_visual = Entity(
                    parent=player_entity, model=f'{cars_dir}{owned_car_model}.obj', texture=cars_tex,
                    position=(0, -1.5, 1.5), scale=2.5, rotation=(0, 0, 0)
                )
                camera.y = 0.5 
                update_hud()

app.run()
