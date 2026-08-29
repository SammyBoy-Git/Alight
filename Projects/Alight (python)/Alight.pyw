import pygame
import random
import sys
import os
import math

# Initialize Pygame & Mixer
pygame.init()
pygame.mixer.init()

# Screen dimensions (Logical Canvas size)
LOGICAL_WIDTH = 800
LOGICAL_HEIGHT = 600
window = pygame.display.set_mode((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.RESIZABLE)
canvas = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))
crt_overlay = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.SRCALPHA)
fade_surface = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))
fade_surface.fill((0, 0, 0))
pygame.display.set_caption("Alight")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
GRAY = (100, 100, 100)
SKY_BLUE = (247, 223, 143)
GREEN = (50, 255, 50)

# Clock for frame rate
clock = pygame.time.Clock()

# Explicit Absolute Directories
SPRITE_DIR = r"C:\Projects\Alight (python)\Sprites"
SFX_DIR = r"C:\Projects\Alight (python)\Sound Effects"

# Ground level definition
ground_y = 420

# Robust Audio Loader with Dummy Fallback
class DummySound:
    def play(self): pass

def load_sound(filename):
    path = os.path.join(SFX_DIR, filename)
    if os.path.exists(path):
        return pygame.mixer.Sound(path)
    print(f"Warning: Could not locate sound '{filename}' in {SFX_DIR}")
    return DummySound()

sounds = {
    "damage": load_sound("damage.mp3"),
    "gun_shot": load_sound("Gun shot.mp3"),
    "talking": load_sound("Talking.mp3"),
    "victory": load_sound("Victory.mp3"),
    "walk": load_sound("Walk.mp3"),
    "jump": load_sound("Jump.mp3"),
    "heal": load_sound("Heal.mp3")
}

music_path = os.path.join(SFX_DIR, "instense music.mp3")
WALK_CHANNEL = pygame.mixer.Channel(1)
talking_played = False
victory_played = False

def update_background_music(state):
    combat_states = ["VILLAGE_FIGHT", "ZOMBIE_WAVE", "GUARD_STAGE", "FIRE_STAGE", "SLIME_STAGE", "BOSS_FIGHT"]
    if state in combat_states:
        if not pygame.mixer.music.get_busy() and os.path.exists(music_path):
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play(-1)
    else:
        if state not in ["WIN_SEQUENCE"]:
            pygame.mixer.music.stop()

# Load all required sprites
def load_sprite_flexible(name, size):
    for ext in [".png", ".jpg"]:
        path = os.path.join(SPRITE_DIR, name + ext)
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(img, size)
    print(f"Error: Could not locate sprite '{name}' in {SPRITE_DIR}")
    sys.exit()

map_img = load_sprite_flexible("Map", (1600, LOGICAL_HEIGHT)) 
village_img = load_sprite_flexible("Village", (1600, LOGICAL_HEIGHT))
dead_map_img = load_sprite_flexible("Dead Map", (1600, LOGICAL_HEIGHT))
start_screen_bg = load_sprite_flexible("Start Screen Blur", (LOGICAL_WIDTH, LOGICAL_HEIGHT))

noah_img = load_sprite_flexible("Noah", (70, 70))
max_img = load_sprite_flexible("Max", (70, 70))
dealer_img = load_sprite_flexible("Dealer", (70, 70))
guard_img = load_sprite_flexible("Body Guard", (70, 70))
raw_gun_img = load_sprite_flexible("Gun", (70, 45))
gun_img = pygame.transform.flip(raw_gun_img, True, False)

monster_img = load_sprite_flexible("Monster", (90, 70))
stranger_img = load_sprite_flexible("Stranger", (60, 70))
zombie_img = load_sprite_flexible("Zombie", (60, 70))
slime_img = load_sprite_flexible("Slime", (60, 60))
base_fireball_img = load_sprite_flexible("Fire_ball", (40, 40))
jump_cloud_img = load_sprite_flexible("Jump cloud", (70, 35))
shield_powerup_img = load_sprite_flexible("Sheild", (35, 35))
apple_powerup_img = load_sprite_flexible("apple", (35, 35))
heal_sprite = load_sprite_flexible("Healing noah", (70, 70))

# Load Ambient Particle Sprites & Dash Sprite
raw_cherry_img = load_sprite_flexible("Ambient cherry", (16, 16))
raw_firefly_img = load_sprite_flexible("Ambient fire fly", (14, 14))
dash_sprite_raw = load_sprite_flexible("Dash", (90, 45))

# Global Dying Enemy Effects Handler & Particle System
dying_enemies = []
critical_texts = []
ambient_particles = []

def init_ambient_particles(particle_type_name):
    ambient_particles.clear()
    for _ in range(10):
        ambient_particles.append({
            "x": random.randint(0, 1600),
            "y": random.randint(0, ground_y),
            "vel_x": random.uniform(-0.2, 0.2),
            "vel_y": random.uniform(-0.3, -0.1),
            "wobble": random.uniform(0, math.pi * 2),
            "type": particle_type_name
        })

def update_and_draw_ambient_particles(surface, camera_pos_x, particle_type_name):
    if len(ambient_particles) == 0 or ambient_particles[0]["type"] != particle_type_name:
        init_ambient_particles(particle_type_name)

    sprite_to_use = raw_cherry_img if particle_type_name == "cherry" else raw_firefly_img

    for p in ambient_particles:
        p["wobble"] += 0.02
        p["x"] += p["vel_x"] + math.sin(p["wobble"]) * 0.2
        p["y"] += p["vel_y"]

        if p["y"] < -10 or p["y"] > ground_y:
            p["y"] = ground_y - 10
            p["x"] = random.randint(0, 1600)
        if p["x"] < camera_pos_x - 20:
            p["x"] = camera_pos_x + LOGICAL_WIDTH + 20
        elif p["x"] > camera_pos_x + LOGICAL_WIDTH + 20:
            p["x"] = camera_pos_x - 20

        screen_x = p["x"] - camera_pos_x
        surface.blit(sprite_to_use, (screen_x, p["y"]))

def trigger_critical_text(x, y):
    critical_texts.append({
        "x": x,
        "y": y,
        "text": "CRITICAL 1% HIT!",
        "alpha": 255,
        "lifetime": 40
    })

def update_and_draw_critical_texts(surface, camera_pos_x):
    font_crit = pygame.font.SysFont(None, 28)
    for ct in critical_texts[:]:
        ct["y"] -= 1
        ct["lifetime"] -= 1
        ct["alpha"] = max(0, int((ct["lifetime"] / 40) * 255))
        
        if ct["lifetime"] <= 0:
            critical_texts.remove(ct)
        else:
            txt_surf = font_crit.render(ct["text"], True, (255, 215, 0))
            txt_surf.set_alpha(ct["alpha"])
            surface.blit(txt_surf, (ct["x"] - camera_pos_x, ct["y"]))

def trigger_enemy_death(sprite, x, y, knockback_dir):
    pygame.time.delay(50)
    dying_enemies.append({
        "sprite": sprite,
        "x": x,
        "y": y,
        "vel_x": knockback_dir * 12,
        "alpha": 255
    })

def update_and_draw_dying_enemies(surface, camera_pos_x):
    for de in dying_enemies[:]:
        de["x"] += de["vel_x"]
        de["vel_x"] *= 0.90 
        de["alpha"] -= 10   
        if de["alpha"] <= 0:
            dying_enemies.remove(de)
        else:
            surf = de["sprite"].copy()
            surf.set_alpha(max(0, de["alpha"]))
            surface.blit(surf, (de["x"] - camera_pos_x, de["y"]))

# Fixed Flashed Sprite using Pygame Masks (Fixes Surface Locked Crash & Lag)
white_silhouette_cache = {}

def get_white_silhouette(sprite):
    if sprite not in white_silhouette_cache:
        mask = pygame.mask.from_surface(sprite)
        white_surf = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
        white_silhouette_cache[sprite] = white_surf
    return white_silhouette_cache[sprite]

def draw_flashed_sprite(surface, sprite, pos, flash_timer, max_flash_frames=6):
    surface.blit(sprite, pos)
    if flash_timer > 0:
        flash_alpha = int((flash_timer / max_flash_frames) * 255)
        white_surf = get_white_silhouette(sprite)
        flashed_surf = white_surf.copy()
        flashed_surf.set_alpha(flash_alpha)
        surface.blit(flashed_surf, pos)

# CRT Overlay Setup
def generate_crt_overlay():
    crt_overlay.fill((0, 0, 0, 0))
    for y in range(0, LOGICAL_HEIGHT, 2):
        pygame.draw.line(crt_overlay, (0, 0, 0, 120), (0, y), (LOGICAL_WIDTH, y), 1)

generate_crt_overlay()

def get_logical_mouse_pos():
    mx, my = pygame.mouse.get_pos()
    win_w, win_h = window.get_size()
    scale_x = LOGICAL_WIDTH / win_w
    scale_y = LOGICAL_HEIGHT / win_h
    return (int(mx * scale_x), int(my * scale_y))

def draw_text_shadow(surface, text_string, font_obj, text_color, x, y, center=False):
    shadow = font_obj.render(text_string, True, BLACK)
    main_text = font_obj.render(text_string, True, text_color)
    
    if center:
        rect = main_text.get_rect(center=(x, y))
        surface.blit(shadow, (rect.x + 2, rect.y + 2))
        surface.blit(main_text, rect)
    else:
        surface.blit(shadow, (x + 2, y + 2))
        surface.blit(main_text, (x, y))

def draw_skip_button(surface):
    skip_rect = pygame.Rect(LOGICAL_WIDTH - 100, 20, 80, 35)
    logical_mouse = get_logical_mouse_pos()
    is_hovering = skip_rect.collidepoint(logical_mouse)
    
    bg_color = (150, 50, 50) if is_hovering else (50, 50, 50)
    pygame.draw.rect(surface, bg_color, skip_rect, border_radius=6)
    pygame.draw.rect(surface, WHITE, skip_rect, 2, border_radius=6)
    
    skip_font = pygame.font.SysFont(None, 24)
    draw_text_shadow(surface, "Skip >>", skip_font, WHITE, skip_rect.centerx, skip_rect.centery, center=True)
    
    return skip_rect

# Default Game Parameters
config_zombie_hits = 3
config_stranger_hits = 1
config_slime_hits = 3
config_guard_hits = 20  
config_guard_count = 2
config_fire_count = 6
config_monster_health = 200
config_player_lives = 3
config_zombie_count = 8
config_slime_count = 10
config_stranger_count = 5
config_monster_count = 1

def reset_game():
    global game_state, noah_world_x, noah_y, noah_vel_y, noah_on_ground, noah_is_crouching, noah_jump_count
    global max_world_x, max_y, camera_x, cutscene_timer, dealer_timer, active_bosses, guard_ambush_x
    global enemy_fireballs, player_fireballs, fireball_timer, lives, score, win_phase, win_timer
    global is_charging, charge_time, last_shot_time, is_dashing, dash_timer, dash_dir
    global strangers_remaining, stranger_spawn_timer, active_strangers, boss_stranger_timer
    global zombies_remaining, zombie_spawn_timer, active_zombies
    global slimes_remaining, slime_spawn_timer, active_slimes
    global guards_spawned, active_guards
    global fires_remaining, fire_spawn_timer, active_fires, active_jump_clouds
    global fade_alpha, fade_direction, next_state_after_fade, gun_damage_multiplier
    global monster_world_x, monster_y, talking_played, victory_played, dying_enemies, critical_texts
    global active_powerups, powerup_spawn_timer, shield_active
    global last_heal_time, is_healing_display, heal_display_timer
    global ultra_transform_available, ultra_transform_active, HEAL_COOLDOWN
    
    game_state = "START_SCREEN"
    talking_played = False
    dying_enemies.clear()
    critical_texts.clear()
    active_powerups.clear()
    active_strangers.clear()
    boss_stranger_timer = 0
    shield_active = False
    guard_ambush_x = 1100
    last_heal_time = -30000
    is_healing_display = False
    heal_display_timer = 0
    ultra_transform_available = False
    ultra_transform_active = False
    HEAL_COOLDOWN = 30000
    pygame.mixer.music.stop()
    
    noah_world_x = 400
    noah_y = ground_y
    noah_vel_y = 0
    noah_on_ground = True
    noah_is_crouching = False
    noah_jump_count = 0

    max_world_x = 490
    max_y = ground_y

    monster_world_x = 1200
    monster_y = 150

    camera_x = 0
    cutscene_timer = 0
    dealer_timer = 0

    active_bosses = []
    for i in range(config_monster_count):
        active_bosses.append({
            "x": 1150 + (i * 120),
            "y": 100,
            "health": config_monster_health,
            "max_health": config_monster_health,
            "flash_timer": 0
        })

    enemy_fireballs = []
    player_fireballs = []
    active_jump_clouds = []
    fireball_timer = 0
    lives = config_player_lives
    score = 0

    win_phase = 1
    win_timer = 0
    
    is_charging = False
    charge_time = 0.0
    last_shot_time = 0
    
    is_dashing = False
    dash_timer = 0
    dash_dir = 1

    strangers_remaining = config_stranger_count
    stranger_spawn_timer = 0
    active_strangers = []

    zombies_remaining = config_zombie_count
    zombie_spawn_timer = 0
    active_zombies = []

    slimes_remaining = config_slime_count
    slime_spawn_timer = 0
    active_slimes = []

    guards_spawned = False
    active_guards = []

    fires_remaining = config_fire_count
    fire_spawn_timer = 0
    active_fires = []

    fade_alpha = 0
    fade_direction = 1
    next_state_after_fade = "VILLAGE_FIGHT"
    gun_damage_multiplier = 1.0

# Game Initialization
game_state = "START_SCREEN"
gravity = 0.6

noah_world_x = 400
noah_y = ground_y
noah_vel_y = 0
noah_on_ground = True
noah_is_crouching = False
noah_jump_count = 0

max_world_x = 490
max_y = ground_y
monster_world_x = 1200
monster_y = 150
camera_x = 0

cutscene_timer = 0
dealer_timer = 0
guard_ambush_x = 1100

active_bosses = []
for i in range(config_monster_count):
    active_bosses.append({
        "x": 1150 + (i * 120),
        "y": 100,
        "health": config_monster_health,
        "max_health": config_monster_health,
        "flash_timer": 0
    })

enemy_fireballs = []
player_fireballs = []
active_jump_clouds = []
active_powerups = []
powerup_spawn_timer = 0
shield_active = False

HEAL_COOLDOWN = 30000  # 30 seconds in milliseconds
last_heal_time = -30000
heal_display_timer = 0
HEAL_DISPLAY_DURATION = 1000
is_healing_display = False

ultra_transform_available = False
ultra_transform_active = False

fireball_timer = 0
boss_stranger_timer = 0
lives = 3
score = 0

win_phase = 1
win_timer = 0

is_charging = False
charge_time = 0.0
last_shot_time = 0
COOLDOWN_MS = 333

is_dashing = False
dash_timer = 0
dash_dir = 1
last_facing_dir = 1

strangers_remaining = 5
stranger_spawn_timer = 0
active_strangers = []

zombies_remaining = 8
zombie_spawn_timer = 0
active_zombies = []

slimes_remaining = 10
slime_spawn_timer = 0
active_slimes = []

guards_spawned = False
active_guards = []

fires_remaining = 6
fire_spawn_timer = 0
active_fires = []

fade_alpha = 0
fade_direction = 1
next_state_after_fade = "VILLAGE_FIGHT"
gun_damage_multiplier = 1.0

font = pygame.font.SysFont(None, 32)
large_font = pygame.font.SysFont(None, 48)

pygame.mouse.set_visible(True)

def render_jump_clouds(surface, camera_pos_x):
    for cloud in active_jump_clouds[:]:
        cloud["lifetime"] -= 1
        if cloud["lifetime"] <= 0:
            active_jump_clouds.remove(cloud)
        else:
            alpha = int((cloud["lifetime"] / 18) * 255)
            cloud_surf = jump_cloud_img.copy()
            cloud_surf.set_alpha(alpha)
            surface.blit(cloud_surf, (cloud["x"] - camera_pos_x, cloud["y"]))

def update_and_draw_powerups(surface, camera_pos_x, noah_rect):
    global lives, shield_active, score
    
    global powerup_spawn_timer
    powerup_spawn_timer += 1
    if powerup_spawn_timer > 350 and len(active_powerups) < 2:
        powerup_spawn_timer = 0
        
        roll = random.random()
        if roll < 0.15:
            p_type = "life"
        elif roll < 0.30:
            p_type = "shield"
        else:
            p_type = None

        if p_type:
            active_powerups.append({
                "x": noah_world_x + random.randint(200, 500),
                "y": ground_y + 15,
                "type": p_type
            })

    for p in active_powerups[:]:
        p_rect = pygame.Rect(p["x"], p["y"], 35, 35)
        
        if p["type"] == "life":
            surface.blit(apple_powerup_img, (p["x"] - camera_x, p["y"]))
        else:
            surface.blit(shield_powerup_img, (p["x"] - camera_x, p["y"]))

        if p_rect.colliderect(noah_rect):
            active_powerups.remove(p)
            sounds["victory"].play()
            score += 100
            if p["type"] == "life":
                lives += 1
            elif p["type"] == "shield":
                shield_active = True

# Main Game Loop
while True:
    dt = clock.tick(60) / 1000.0
    current_time_ms = pygame.time.get_ticks()

    if is_healing_display and current_time_ms - heal_display_timer > HEAL_DISPLAY_DURATION:
        is_healing_display = False

    update_background_music(game_state)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                if game_state in ["GAME_OVER", "WIN_SEQUENCE"]:
                    reset_game()

            elif event.key in (pygame.K_e, pygame.K_3):
                # Restricted Ultra Transform activation specifically to the boss stage
                if game_state == "BOSS_FIGHT":
                    if ultra_transform_available and not ultra_transform_active:
                        ultra_transform_active = True
                        ultra_transform_available = False
                        HEAL_COOLDOWN = 15000

            elif event.key == pygame.K_h:
                if game_state in ["BOSS_FIGHT", "VILLAGE_FIGHT", "ZOMBIE_WAVE", "GUARD_STAGE", "FIRE_STAGE", "SLIME_STAGE"]:
                    if current_time_ms - last_heal_time >= HEAL_COOLDOWN:
                        lives += 1
                        last_heal_time = current_time_ms
                        sounds["heal"].play()
                        is_healing_display = True
                        heal_display_timer = current_time_ms

            elif event.key == pygame.K_q:
                if game_state in ["BOSS_FIGHT", "VILLAGE_FIGHT", "ZOMBIE_WAVE", "GUARD_STAGE", "FIRE_STAGE", "SLIME_STAGE"]:
                    if not is_dashing:
                        is_dashing = True
                        dash_timer = 15  
                        dash_dir = last_facing_dir

            elif event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                if game_state in ["BOSS_FIGHT", "VILLAGE_FIGHT", "ZOMBIE_WAVE", "GUARD_STAGE", "FIRE_STAGE", "SLIME_STAGE"]:
                    if not noah_is_crouching and noah_jump_count < 2:
                        noah_vel_y = -12
                        noah_on_ground = False
                        noah_jump_count += 1
                        sounds["jump"].play()
                        if noah_jump_count == 2:
                            active_jump_clouds.append({
                                "x": noah_world_x,
                                "y": noah_y + 45,
                                "lifetime": 18
                            })

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            logical_mouse = get_logical_mouse_pos()
            
            if game_state == "START_SCREEN":
                start_btn_rect = pygame.Rect(40, 475, 220, 85)
                if start_btn_rect.collidepoint(logical_mouse):
                    game_state = "WALK"
                    pygame.mouse.set_visible(False)
            
            elif game_state in ["WALK", "ABDUCTION"]:
                skip_rect = pygame.Rect(LOGICAL_WIDTH - 100, 20, 80, 35)
                if skip_rect.collidepoint(logical_mouse):
                    game_state = "FADE_TRANSITION"
                    fade_alpha = 0
                    fade_direction = 1
                    next_state_after_fade = "VILLAGE_FIGHT"
            elif game_state == "DEALER_SCENE":
                skip_rect = pygame.Rect(LOGICAL_WIDTH - 100, 20, 80, 35)
                if skip_rect.collidepoint(logical_mouse):
                    gun_damage_multiplier = 2.0
                    game_state = "FADE_TRANSITION"
                    fade_alpha = 0
                    fade_direction = 1
                    next_state_after_fade = "GUARD_STAGE"
                    dealer_timer = 0
            
            elif game_state == "WIN_SEQUENCE":
                skip_rect = pygame.Rect(LOGICAL_WIDTH - 100, 20, 80, 35)
                if skip_rect.collidepoint(logical_mouse):
                    win_phase = 3

            elif game_state in ["BOSS_FIGHT", "VILLAGE_FIGHT", "ZOMBIE_WAVE", "GUARD_STAGE", "FIRE_STAGE", "SLIME_STAGE"]:
                if current_time_ms - last_shot_time >= COOLDOWN_MS:
                    is_charging = True
                    charge_time = 0.0
                    
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if game_state in ["BOSS_FIGHT", "VILLAGE_FIGHT", "ZOMBIE_WAVE", "GUARD_STAGE", "FIRE_STAGE", "SLIME_STAGE"] and is_charging:
                is_charging = False
                last_shot_time = current_time_ms
                
                sounds["gun_shot"].play()
                
                final_charge = min(charge_time, 5.0)
                scale_multiplier = 1.0 + (final_charge / 5.0)
                
                damage = int((2 + (final_charge / 5.0) * 8) * gun_damage_multiplier)
                if ultra_transform_active:
                    damage *= 2
                    scale_multiplier *= 2.0
                
                target_x, target_y = get_logical_mouse_pos()
                world_spawn_x = target_x + camera_x
                world_spawn_y = target_y
                
                base_size = int(40 * scale_multiplier)
                fb_surf = pygame.transform.scale(base_fireball_img, (base_size, base_size))
                
                player_fireballs.append({
                    "x": world_spawn_x,
                    "y": world_spawn_y,
                    "vel_x": 12,
                    "vel_y": 0,
                    "lifetime": 90,
                    "size": base_size,
                    "damage": damage,
                    "surface": fb_surf
                })

    canvas.fill(SKY_BLUE)
    
    if game_state == "START_SCREEN":
        pygame.mouse.set_visible(True)
        canvas.blit(start_screen_bg, (0, 0))
        
        start_btn_rect = pygame.Rect(40, 475, 220, 85)
        logical_mouse = get_logical_mouse_pos()
        is_hovering = start_btn_rect.collidepoint(logical_mouse)
        
        btn_color = (70, 160, 70) if is_hovering else (50, 120, 50)
        pygame.draw.rect(canvas, btn_color, start_btn_rect, border_radius=8)
        pygame.draw.rect(canvas, WHITE, start_btn_rect, 2, border_radius=8)
        draw_text_shadow(canvas, "Start game", font, WHITE, start_btn_rect.centerx, start_btn_rect.centery, center=True)
    
    else:
        if game_state in ["ZOMBIE_WAVE", "FIRE_STAGE", "SLIME_STAGE"]:
            current_map = dead_map_img
        elif game_state in ["VILLAGE_FIGHT", "BOSS_FIGHT", "DEALER_SCENE", "GUARD_STAGE"]:
            current_map = village_img
        else:
            current_map = map_img
            
        canvas.blit(current_map, (-camera_x, 0))

        # Render Ambient Particles
        if game_state in ["ZOMBIE_WAVE", "SLIME_STAGE"]:
            update_and_draw_ambient_particles(canvas, camera_x, "firefly")
        else:
            update_and_draw_ambient_particles(canvas, camera_x, "cherry")

        # Restrict Ultra Transform availability check to the Boss Fight stage when lives hit 1
        if game_state == "BOSS_FIGHT" and lives == 1 and not ultra_transform_active and not ultra_transform_available:
            ultra_transform_available = True

        # ==================== STATE 1: WALKING CUTSCENE ====================
        if game_state == "WALK":
            cutscene_timer += 1
            noah_world_x += 1.5
            max_world_x += 1.5
            
            if not talking_played:
                sounds["talking"].play()
                talking_played = True

            if not WALK_CHANNEL.get_busy():
                WALK_CHANNEL.play(sounds["walk"])
            
            camera_x = noah_world_x - (LOGICAL_WIDTH // 2)
            camera_x = max(0, min(camera_x, 1600 - LOGICAL_WIDTH))

            screen_noah_x = noah_world_x - camera_x
            screen_max_x = max_world_x - camera_x

            canvas.blit(noah_img, (screen_noah_x, ground_y))
            canvas.blit(max_img, (screen_max_x, ground_y))
            
            draw_text_shadow(canvas, "Noah and Max take a peaceful evening walk...", font, WHITE, LOGICAL_WIDTH // 2, 80, center=True)
            draw_skip_button(canvas)

            if cutscene_timer > 180:
                game_state = "ABDUCTION"
                cutscene_timer = 0

        # ==================== STATE 2: ABDUCTION CUTSCENE ====================
        elif game_state == "ABDUCTION":
            cutscene_timer += 1
            
            if monster_world_x > max_world_x:
                monster_world_x -= 4
            if monster_y < ground_y:
                monster_y += 2
                
            camera_x = noah_world_x - (LOGICAL_WIDTH // 2)
            camera_x = max(0, min(camera_x, 1600 - LOGICAL_WIDTH))

            screen_noah_x = noah_world_x - camera_x
            screen_max_x = max_world_x - camera_x
            screen_monster_x = monster_world_x - camera_x

            canvas.blit(noah_img, (screen_noah_x, ground_y))
            
            if cutscene_timer < 100:
                canvas.blit(max_img, (screen_max_x, ground_y))
                canvas.blit(monster_img, (screen_monster_x, monster_y))
                draw_text_shadow(canvas, "Watch out!!", font, WHITE, screen_max_x - 10, ground_y - 40)
            else:
                max_world_x = monster_world_x + 10
                max_y = monster_y - 10
                screen_max_x = max_world_x - camera_x
                
                canvas.blit(max_img, (screen_max_x, max_y))
                canvas.blit(monster_img, (screen_monster_x, monster_y))
                
                draw_text_shadow(canvas, "A mysterious monster kidnapped Max!", font, WHITE, LOGICAL_WIDTH // 2, 80, center=True)

            draw_skip_button(canvas)

            if cutscene_timer > 220:
                game_state = "FADE_TRANSITION"
                fade_alpha = 0
                fade_direction = 1
                next_state_after_fade = "VILLAGE_FIGHT"

        # ==================== STATE 2.5: FADE TRANSITION ====================
        elif game_state == "FADE_TRANSITION":
            screen_noah_x = noah_world_x - camera_x
            canvas.blit(noah_img, (screen_noah_x, ground_y))

            if fade_direction == 1:
                fade_alpha += 6
                if fade_alpha >= 255:
                    fade_alpha = 255
                    fade_direction = -1
                    if next_state_after_fade == "VILLAGE_FIGHT":
                        noah_world_x = 200
                        camera_x = 0
                    elif next_state_after_fade == "ZOMBIE_WAVE":
                        noah_world_x = 200
                        camera_x = 0
                    elif next_state_after_fade == "DEALER_SCENE":
                        noah_world_x = 350
                        camera_x = 200
                        dealer_timer = 0
                    elif next_state_after_fade == "GUARD_STAGE":
                        noah_world_x = 200
                        camera_x = 0
                    elif next_state_after_fade == "FIRE_STAGE":
                        noah_world_x = 200
                        camera_x = 0
                    elif next_state_after_fade == "SLIME_STAGE":
                        noah_world_x = 200
                        camera_x = 0
                    elif next_state_after_fade == "BOSS_FIGHT":
                        noah_world_x = 400
                        camera_x = 0
            else:
                fade_alpha -= 6
                if fade_alpha <= 0:
                    fade_alpha = 0
                    game_state = next_state_after_fade

            fade_surface.set_alpha(fade_alpha)
            canvas.blit(fade_surface, (0, 0))

        # ==================== STATE 3: VILLAGE STRANGER FIGHT ====================
        elif game_state == "VILLAGE_FIGHT":
            if is_charging:
                charge_time += dt

            keys = pygame.key.get_pressed()
            noah_vel_x = 0
            is_walking_now = False
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                noah_vel_x = -4
                is_walking_now = True
                last_facing_dir = -1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                noah_vel_x = 4
                is_walking_now = True
                last_facing_dir = 1

            if is_dashing:
                dash_timer -= 1
                noah_vel_x = dash_dir * 10
                if dash_timer <= 0:
                    is_dashing = False

            if is_walking_now and noah_on_ground and not is_dashing:
                if not WALK_CHANNEL.get_busy():
                    WALK_CHANNEL.play(sounds["walk"])

            noah_world_x += noah_vel_x
            noah_world_x = max(50, min(noah_world_x, 1550 - 90))

            camera_x = noah_world_x - (LOGICAL_WIDTH // 2)
            camera_x = max(0, min(camera_x, 1600 - LOGICAL_WIDTH))

            noah_vel_y += gravity
            noah_y += noah_vel_y
            if noah_y >= ground_y:
                noah_y = ground_y
                noah_vel_y = 0
                noah_on_ground = True
                noah_jump_count = 0

            stranger_spawn_timer += 1
            if strangers_remaining > 0 and stranger_spawn_timer > 90 and len(active_strangers) < 2:
                stranger_spawn_timer = 0
                active_strangers.append({
                    "x": noah_world_x + 500 + random.randint(0, 200),
                    "y": ground_y,
                    "health": config_stranger_hits,
                    "vel_x": 2.0,
                    "flash_timer": 0
                })
                strangers_remaining -= 1

            noah_rect = pygame.Rect(noah_world_x, noah_y, 70, 70)
            update_and_draw_powerups(canvas, camera_x, noah_rect)

            for st in active_strangers[:]:
                st["flash_timer"] = max(0, st["flash_timer"] - 1)
                if st["x"] > noah_world_x:
                    st["x"] -= st["vel_x"]
                else:
                    st["x"] += st["vel_x"]

                st_rect = pygame.Rect(st["x"], st["y"], 60, 70)
                if st_rect.colliderect(noah_rect) and not is_dashing:
                    active_strangers.remove(st)
                    sounds["damage"].play()
                    if shield_active:
                        shield_active = False
                    else:
                        lives -= 1
                        if lives <= 0:
                            game_state = "GAME_OVER"

            for pfb in player_fireballs[:]:
                pfb["x"] += pfb["vel_x"]
                pfb["y"] += pfb["vel_y"]
                pfb["lifetime"] -= 1
                
                pfb_rect = pygame.Rect(pfb["x"], pfb["y"], pfb["size"], pfb["size"])
                if pfb["lifetime"] <= 0:
                    player_fireballs.remove(pfb)
                    continue
                    
                hit_stranger = False
                for st in active_strangers[:]:
                    st_rect = pygame.Rect(st["x"], st["y"], 60, 70)
                    if pfb_rect.colliderect(st_rect):
                        hit_stranger = True
                        sounds["damage"].play()
                        st["health"] -= pfb["damage"]
                        st["flash_timer"] = 6
                        score += 25
                        if st["health"] <= 0:
                            active_strangers.remove(st)
                            score += 50
                            kb_dir = 1 if pfb["vel_x"] > 0 else -1
                            trigger_enemy_death(stranger_img, st["x"], st["y"], kb_dir)
                        break
                
                if hit_stranger:
                    if pfb in player_fireballs:
                        player_fireballs.remove(pfb)
                else:
                    pfb_screen_x = pfb["x"] - camera_x
                    if pfb_screen_x < 0 or pfb_screen_x > LOGICAL_WIDTH:
                        player_fireballs.remove(pfb)

            if strangers_remaining == 0 and len(active_strangers) == 0 and len(dying_enemies) == 0:
                game_state = "FADE_TRANSITION"
                fade_alpha = 0
                fade_direction = 1
                next_state_after_fade = "ZOMBIE_WAVE"

            render_jump_clouds(canvas, camera_x)
            
            if is_healing_display:
                canvas.blit(heal_sprite, (noah_world_x - camera_x, noah_y))
            elif is_dashing:
                if dash_dir == 1:
                    canvas.blit(dash_sprite_raw, (noah_world_x - camera_x - 10, noah_y + 25))
                else:
                    flipped_dash = pygame.transform.flip(dash_sprite_raw, True, False)
                    canvas.blit(flipped_dash, (noah_world_x - camera_x - 10, noah_y + 25))
            else:
                canvas.blit(noah_img, (noah_world_x - camera_x, noah_y))

            for st in active_strangers:
                draw_flashed_sprite(canvas, stranger_img, (st["x"] - camera_x, st["y"]), st["flash_timer"])
            update_and_draw_dying_enemies(canvas, camera_x)
            
            for pfb in player_fireballs:
                canvas.blit(pfb["surface"], (pfb["x"] - camera_x, pfb["y"]))

            logical_mouse = get_logical_mouse_pos()
            canvas.blit(gun_img, (logical_mouse[0] - 20, logical_mouse[1] - 20))

            draw_text_shadow(canvas, f"Village Strangers Left: {strangers_remaining + len(active_strangers)}/{config_stranger_count}", font, WHITE, LOGICAL_WIDTH // 2, 30, center=True)
            draw_text_shadow(canvas, f"Score: {score}", font, WHITE, 20, 20)
            draw_text_shadow(canvas, f"Lives: {lives}", font, WHITE, 20, 55)

            time_since_heal = current_time_ms - last_heal_time
            if time_since_heal >= HEAL_COOLDOWN:
                heal_text_str = "Heal Ready! (Press H)"
                heal_text_color = GREEN
            else:
                seconds_left = math.ceil((HEAL_COOLDOWN - time_since_heal) / 1000)
                heal_text_str = f"Heal CD: {seconds_left}s"
                heal_text_color = RED
            draw_text_shadow(canvas, heal_text_str, font, heal_text_color, 20, 90)

            if shield_active:
                draw_text_shadow(canvas, "Shield Active!", font, (50, 200, 255), 20, 125)

            if is_charging:
                charge_pct = min(100, int((charge_time / 5.0) * 100))
                draw_text_shadow(canvas, f"Charging Power: {charge_pct}%", font, RED, LOGICAL_WIDTH // 2, LOGICAL_HEIGHT - 40, center=True)

        # ==================== STATE 3.2: ZOMBIE WAVE LEVEL ====================
        elif game_state == "ZOMBIE_WAVE":
            if is_charging:
                charge_time += dt

            keys = pygame.key.get_pressed()
            noah_vel_x = 0
            is_walking_now = False
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                noah_vel_x = -4
                is_walking_now = True
                last_facing_dir = -1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                noah_vel_x = 4
                is_walking_now = True
                last_facing_dir = 1

            if is_dashing:
                dash_timer -= 1
                noah_vel_x = dash_dir * 10
                if dash_timer <= 0:
                    is_dashing = False

            if is_walking_now and noah_on_ground and not is_dashing:
                if not WALK_CHANNEL.get_busy():
                    WALK_CHANNEL.play(sounds["walk"])

            noah_world_x += noah_vel_x
            noah_world_x = max(50, min(noah_world_x, 1550 - 90))

            camera_x = noah_world_x - (LOGICAL_WIDTH // 2)
            camera_x = max(0, min(camera_x, 1600 - LOGICAL_WIDTH))

            noah_vel_y += gravity
            noah_y += noah_vel_y
            if noah_y >= ground_y:
                noah_y = ground_y
                noah_vel_y = 0
                noah_on_ground = True
                noah_jump_count = 0

            zombie_spawn_timer += 1
            if zombies_remaining > 0 and zombie_spawn_timer > 70 and len(active_zombies) < 3:
                zombie_spawn_timer = 0
                active_zombies.append({
                    "x": noah_world_x + 500 + random.randint(0, 200),
                    "y": ground_y,
                    "health": config_zombie_hits,
                    "vel_x": 1.7,
                    "flash_timer": 0
                })
                zombies_remaining -= 1

            noah_rect = pygame.Rect(noah_world_x, noah_y, 70, 70)
            update_and_draw_powerups(canvas, camera_x, noah_rect)

            for zb in active_zombies[:]:
                zb["flash_timer"] = max(0, zb["flash_timer"] - 1)
                if zb["x"] > noah_world_x:
                    zb["x"] -= zb["vel_x"]
                else:
                    zb["x"] += zb["vel_x"]

                zb_rect = pygame.Rect(zb["x"], zb["y"], 60, 70)
                if zb_rect.colliderect(noah_rect) and not is_dashing:
                    active_zombies.remove(zb)
                    sounds["damage"].play()
                    if shield_active:
                        shield_active = False
                    else:
                        lives -= 1
                        if lives <= 0:
                            game_state = "GAME_OVER"

            for pfb in player_fireballs[:]:
                pfb["x"] += pfb["vel_x"]
                pfb["y"] += pfb["vel_y"]
                pfb["lifetime"] -= 1
                
                pfb_rect = pygame.Rect(pfb["x"], pfb["y"], pfb["size"], pfb["size"])
                if pfb["lifetime"] <= 0:
                    player_fireballs.remove(pfb)
                    continue
                    
                hit_zombie = False
                for zb in active_zombies[:]:
                    zb_rect = pygame.Rect(zb["x"], zb["y"], 60, 70)
                    if pfb_rect.colliderect(zb_rect):
                        hit_zombie = True
                        sounds["damage"].play()
                        zb["health"] -= pfb["damage"]
                        zb["flash_timer"] = 6
                        score += 25
                        if zb["health"] <= 0:
                            active_zombies.remove(zb)
                            score += 75
                            kb_dir = 1 if pfb["vel_x"] > 0 else -1
                            trigger_enemy_death(zombie_img, zb["x"], zb["y"], kb_dir)
                        break
                
                if hit_zombie:
                    if pfb in player_fireballs:
                        player_fireballs.remove(pfb)
                else:
                    pfb_screen_x = pfb["x"] - camera_x
                    if pfb_screen_x < 0 or pfb_screen_x > LOGICAL_WIDTH:
                        player_fireballs.remove(pfb)

            if zombies_remaining == 0 and len(active_zombies) == 0 and len(dying_enemies) == 0:
                game_state = "FADE_TRANSITION"
                fade_alpha = 0
                fade_direction = 1
                next_state_after_fade = "DEALER_SCENE"

            render_jump_clouds(canvas, camera_x)
            
            if is_healing_display:
                canvas.blit(heal_sprite, (noah_world_x - camera_x, noah_y))
            elif is_dashing:
                if dash_dir == 1:
                    canvas.blit(dash_sprite_raw, (noah_world_x - camera_x - 10, noah_y + 25))
                else:
                    flipped_dash = pygame.transform.flip(dash_sprite_raw, True, False)
                    canvas.blit(flipped_dash, (noah_world_x - camera_x - 10, noah_y + 25))
            else:
                canvas.blit(noah_img, (noah_world_x - camera_x, noah_y))

            for zb in active_zombies:
                draw_flashed_sprite(canvas, zombie_img, (zb["x"] - camera_x, zb["y"]), zb["flash_timer"])
            update_and_draw_dying_enemies(canvas, camera_x)

            for pfb in player_fireballs:
                canvas.blit(pfb["surface"], (pfb["x"] - camera_x, pfb["y"]))

            logical_mouse = get_logical_mouse_pos()
            canvas.blit(gun_img, (logical_mouse[0] - 20, logical_mouse[1] - 20))

            draw_text_shadow(canvas, f"Zombies Left: {zombies_remaining + len(active_zombies)}/{config_zombie_count}", font, WHITE, LOGICAL_WIDTH // 2, 30, center=True)
            draw_text_shadow(canvas, f"Score: {score}", font, WHITE, 20, 20)
            draw_text_shadow(canvas, f"Lives: {lives}", font, WHITE, 20, 55)

            time_since_heal = current_time_ms - last_heal_time
            if time_since_heal >= HEAL_COOLDOWN:
                heal_text_str = "Heal Ready! (Press H)"
                heal_text_color = GREEN
            else:
                seconds_left = math.ceil((HEAL_COOLDOWN - time_since_heal) / 1000)
                heal_text_str = f"Heal CD: {seconds_left}s"
                heal_text_color = RED
            draw_text_shadow(canvas, heal_text_str, font, heal_text_color, 20, 90)

            if shield_active:
                draw_text_shadow(canvas, "Shield Active!", font, (50, 200, 255), 20, 125)

            if is_charging:
                charge_pct = min(100, int((charge_time / 5.0) * 100))
                draw_text_shadow(canvas, f"Charging Power: {charge_pct}%", font, RED, LOGICAL_WIDTH // 2, LOGICAL_HEIGHT - 40, center=True)

        # ==================== STATE 3.5: DEALER SCENE ====================
        elif game_state == "DEALER_SCENE":
            dealer_timer += 1
            camera_x = 200

            screen_noah_x = 350 - camera_x
            screen_dealer_x = 600 - camera_x

            canvas.blit(noah_img, (screen_noah_x, ground_y))
            canvas.blit(dealer_img, (screen_dealer_x, ground_y))

            if dealer_timer < 120:
                draw_text_shadow(canvas, "Dealer: 'You survived the graveyard, but the guards protect the core...'", font, WHITE, LOGICAL_WIDTH // 2, 80, center=True)
                draw_text_shadow(canvas, "Dealer: 'Take this enhanced gun! (2x Damage)'", font, WHITE, LOGICAL_WIDTH // 2, 115, center=True)
                gun_damage_multiplier = 2.0
            elif dealer_timer < 220:
                guard_ambush_x = max(700, 1100 - (dealer_timer - 120) * 5)
                screen_guard_x = guard_ambush_x - camera_x
                canvas.blit(guard_img, (screen_guard_x, ground_y))
                draw_text_shadow(canvas, "Elite Body Guards are approaching!", font, RED, LOGICAL_WIDTH // 2, 80, center=True)
            else:
                game_state = "FADE_TRANSITION"
                fade_alpha = 0
                fade_direction = 1
                next_state_after_fade = "GUARD_STAGE"
                dealer_timer = 0

            draw_skip_button(canvas)

        # ==================== STATE 3.75: GUARD STAGE ====================
        elif game_state == "GUARD_STAGE":
            if is_charging:
                charge_time += dt

            keys = pygame.key.get_pressed()
            noah_vel_x = 0
            is_walking_now = False
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                noah_vel_x = -4
                is_walking_now = True
                last_facing_dir = -1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                noah_vel_x = 4
                is_walking_now = True
                last_facing_dir = 1

            if is_dashing:
                dash_timer -= 1
                noah_vel_x = dash_dir * 10
                if dash_timer <= 0:
                    is_dashing = False

            if is_walking_now and noah_on_ground and not is_dashing:
                if not WALK_CHANNEL.get_busy():
                    WALK_CHANNEL.play(sounds["walk"])

            noah_world_x += noah_vel_x
            noah_world_x = max(50, min(noah_world_x, 1550 - 90))

            camera_x = noah_world_x - (LOGICAL_WIDTH // 2)
            camera_x = max(0, min(camera_x, 1600 - LOGICAL_WIDTH))

            noah_vel_y += gravity
            noah_y += noah_vel_y
            if noah_y >= ground_y:
                noah_y = ground_y
                noah_vel_y = 0
                noah_on_ground = True
                noah_jump_count = 0

            if not guards_spawned:
                for i in range(config_guard_count):
                    active_guards.append({
                        "x": 1050 + (i * 140),
                        "y": ground_y,
                        "health": config_guard_hits,
                        "max_health": config_guard_hits,
                        "vel_x": 1.7,
                        "flash_timer": 0
                    })
                guards_spawned = True

            noah_rect = pygame.Rect(noah_world_x, noah_y, 70, 70)
            update_and_draw_powerups(canvas, camera_x, noah_rect)

            for guard in active_guards[:]:
                guard["flash_timer"] = max(0, guard["flash_timer"] - 1)
                if guard["x"] > noah_world_x:
                    guard["x"] -= guard["vel_x"]
                else:
                    guard["x"] += guard["vel_x"]
                guard["x"] = max(50, min(guard["x"], 1550 - 70))

                guard_touch_rect = pygame.Rect(guard["x"] + 20, guard["y"] + 20, 30, 30)
                if guard_touch_rect.colliderect(noah_rect) and not is_dashing:
                    active_guards.remove(guard)
                    sounds["damage"].play()
                    if shield_active:
                        shield_active = False
                    else:
                        lives -= 3
                        if lives <= 0:
                            game_state = "GAME_OVER"

            for pfb in player_fireballs[:]:
                pfb["x"] += pfb["vel_x"]
                pfb["y"] += pfb["vel_y"]
                pfb["lifetime"] -= 1
                
                pfb_rect = pygame.Rect(pfb["x"], pfb["y"], pfb["size"], pfb["size"])
                if pfb["lifetime"] <= 0:
                    player_fireballs.remove(pfb)
                    continue
                    
                hit_guard = False
                for guard in active_guards[:]:
                    guard_rect = pygame.Rect(guard["x"], guard["y"], 70, 70)
                    if pfb_rect.colliderect(guard_rect):
                        hit_guard = True
                        sounds["damage"].play()
                        guard["health"] -= pfb["damage"]
                        guard["flash_timer"] = 6
                        score += 100
                        if guard["health"] <= 0:
                            active_guards.remove(guard)
                            score += 500
                            kb_dir = 1 if pfb["vel_x"] > 0 else -1
                            trigger_enemy_death(guard_img, guard["x"], guard["y"], kb_dir)
                        break
                
                if hit_guard:
                    if pfb in player_fireballs:
                        player_fireballs.remove(pfb)
                else:
                    pfb_screen_x = pfb["x"] - camera_x
                    if pfb_screen_x < 0 or pfb_screen_x > LOGICAL_WIDTH:
                        player_fireballs.remove(pfb)

            if guards_spawned and len(active_guards) == 0 and len(dying_enemies) == 0:
                game_state = "FADE_TRANSITION"
                fade_alpha = 0
                fade_direction = 1
                next_state_after_fade = "FIRE_STAGE"

            render_jump_clouds(canvas, camera_x)
            
            if is_healing_display:
                canvas.blit(heal_sprite, (noah_world_x - camera_x, noah_y))
            elif is_dashing:
                if dash_dir == 1:
                    canvas.blit(dash_sprite_raw, (noah_world_x - camera_x - 10, noah_y + 25))
                else:
                    flipped_dash = pygame.transform.flip(dash_sprite_raw, True, False)
                    canvas.blit(flipped_dash, (noah_world_x - camera_x - 10, noah_y + 25))
            else:
                canvas.blit(noah_img, (noah_world_x - camera_x, noah_y))

            for guard in active_guards:
                draw_flashed_sprite(canvas, guard_img, (guard["x"] - camera_x, guard["y"]), guard["flash_timer"])
            update_and_draw_dying_enemies(canvas, camera_x)

            for pfb in player_fireballs:
                canvas.blit(pfb["surface"], (pfb["x"] - camera_x, pfb["y"]))

            logical_mouse = get_logical_mouse_pos()
            canvas.blit(gun_img, (logical_mouse[0] - 20, logical_mouse[1] - 20))

            pygame.draw.rect(canvas, GRAY, (LOGICAL_WIDTH // 2 - 200, 30, 400, 20))
            total_current_hp = sum([g["health"] for g in active_guards])
            total_max_hp = config_guard_hits * config_guard_count
            health_ratio = max(0, total_current_hp / total_max_hp) if total_max_hp > 0 else 0
            pygame.draw.rect(canvas, RED, (LOGICAL_WIDTH // 2 - 200, 30, int(400 * health_ratio), 20))

            draw_text_shadow(canvas, f"Guards Remaining: {len(active_guards)}/{config_guard_count}", font, WHITE, LOGICAL_WIDTH // 2, 55, center=True)
            draw_text_shadow(canvas, f"Score: {score}", font, WHITE, 20, 20)
            draw_text_shadow(canvas, f"Lives: {lives}", font, WHITE, 20, 55)

            time_since_heal = current_time_ms - last_heal_time
            if time_since_heal >= HEAL_COOLDOWN:
                heal_text_str = "Heal Ready! (Press H)"
                heal_text_color = GREEN
            else:
                seconds_left = math.ceil((HEAL_COOLDOWN - time_since_heal) / 1000)
                heal_text_str = f"Heal CD: {seconds_left}s"
                heal_text_color = RED
            draw_text_shadow(canvas, heal_text_str, font, heal_text_color, 20, 90)

            if shield_active:
                draw_text_shadow(canvas, "Shield Active!", font, (50, 200, 255), 20, 125)

            if is_charging:
                charge_pct = min(100, int((charge_time / 5.0) * 100))
                draw_text_shadow(canvas, f"Charging Power: {charge_pct}%", font, RED, LOGICAL_WIDTH // 2, LOGICAL_HEIGHT - 40, center=True)

        # ==================== STATE 3.85: FIRE JUMP & CROUCH STAGE ====================
        elif game_state == "FIRE_STAGE":
            if is_charging:
                charge_time += dt

            keys = pygame.key.get_pressed()
            noah_vel_x = 0
            is_walking_now = False
            
            if noah_on_ground and (keys[pygame.K_DOWN] or keys[pygame.K_s]):
                noah_is_crouching = True
            else:
                noah_is_crouching = False

            if not noah_is_crouching:
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    noah_vel_x = -4
                    is_walking_now = True
                    last_facing_dir = -1
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    noah_vel_x = 4
                    is_walking_now = True
                    last_facing_dir = 1

            if is_dashing:
                dash_timer -= 1
                noah_vel_x = dash_dir * 10
                if dash_timer <= 0:
                    is_dashing = False

            if is_walking_now and noah_on_ground and not noah_is_crouching and not is_dashing:
                if not WALK_CHANNEL.get_busy():
                    WALK_CHANNEL.play(sounds["walk"])

            noah_world_x += noah_vel_x
            noah_world_x = max(50, min(noah_world_x, 1550 - 90))

            camera_x = noah_world_x - (LOGICAL_WIDTH // 2)
            camera_x = max(0, min(camera_x, 1600 - LOGICAL_WIDTH))

            noah_vel_y += gravity
            noah_y += noah_vel_y
            if noah_y >= ground_y:
                noah_y = ground_y
                noah_vel_y = 0
                noah_on_ground = True
                noah_jump_count = 0

            fire_spawn_timer += 1
            if fires_remaining > 0 and fire_spawn_timer > 70 and len(active_fires) < 2:
                fire_spawn_timer = 0
                fire_type = random.choice(["ground", "high"])
                spawn_y = ground_y + 20 if fire_type == "ground" else ground_y - 15
                active_fires.append({
                    "x": noah_world_x + 600,
                    "y": spawn_y,
                    "type": fire_type,
                    "vel_x": 4.5
                })
                fires_remaining -= 1

            if noah_is_crouching:
                noah_rect = pygame.Rect(noah_world_x, noah_y + 35, 70, 35)
            else:
                noah_rect = pygame.Rect(noah_world_x, noah_y, 70, 70)

            update_and_draw_powerups(canvas, camera_x, noah_rect)

            for fire in active_fires[:]:
                fire["x"] -= fire["vel_x"]
                
                if fire["x"] < camera_x - 100:
                    active_fires.remove(fire)
                    continue

                fire_rect = pygame.Rect(fire["x"] + 5, fire["y"] + 5, 30, 30)
                if fire_rect.colliderect(noah_rect) and not is_dashing:
                    active_fires.remove(fire)
                    sounds["damage"].play()
                    if shield_active:
                        shield_active = False
                    else:
                        lives -= 1
                        if lives <= 0:
                            game_state = "GAME_OVER"

            for pfb in player_fireballs[:]:
                pfb["x"] += pfb["vel_x"]
                pfb["y"] += pfb["vel_y"]
                pfb["lifetime"] -= 1
                
                pfb_rect = pygame.Rect(pfb["x"], pfb["y"], pfb["size"], pfb["size"])
                if pfb["lifetime"] <= 0:
                    player_fireballs.remove(pfb)
                    continue
                    
                hit_fire = False
                for fire in active_fires[:]:
                    fire_rect = pygame.Rect(fire["x"], fire["y"], 40, 40)
                    if pfb_rect.colliderect(fire_rect):
                        hit_fire = True
                        sounds["damage"].play()
                        active_fires.remove(fire)
                        score += 50
                        break
                
                if hit_fire:
                    if pfb in player_fireballs:
                        player_fireballs.remove(pfb)
                else:
                    pfb_screen_x = pfb["x"] - camera_x
                    if pfb_screen_x < 0 or pfb_screen_x > LOGICAL_WIDTH:
                        player_fireballs.remove(pfb)

            if fires_remaining == 0 and len(active_fires) == 0 and len(dying_enemies) == 0:
                game_state = "FADE_TRANSITION"
                fade_alpha = 0
                fade_direction = 1
                next_state_after_fade = "SLIME_STAGE"

            render_jump_clouds(canvas, camera_x)
            
            if is_healing_display:
                canvas.blit(heal_sprite, (noah_world_x - camera_x, noah_y))
            elif is_dashing:
                if dash_dir == 1:
                    canvas.blit(dash_sprite_raw, (noah_world_x - camera_x - 10, noah_y + 25))
                else:
                    flipped_dash = pygame.transform.flip(dash_sprite_raw, True, False)
                    canvas.blit(flipped_dash, (noah_world_x - camera_x - 10, noah_y + 25))
            elif noah_is_crouching:
                crouch_img = pygame.transform.scale(noah_img, (70, 35))
                canvas.blit(crouch_img, (noah_world_x - camera_x, noah_y + 35))
            else:
                canvas.blit(noah_img, (noah_world_x - camera_x, noah_y))

            for fire in active_fires:
                scaled_fire = pygame.transform.scale(base_fireball_img, (50, 50))
                canvas.blit(scaled_fire, (fire["x"] - camera_x, fire["y"]))
            update_and_draw_dying_enemies(canvas, camera_x)

            for pfb in player_fireballs:
                canvas.blit(pfb["surface"], (pfb["x"] - camera_x, pfb["y"]))

            logical_mouse = get_logical_mouse_pos()
            canvas.blit(gun_img, (logical_mouse[0] - 20, logical_mouse[1] - 20))

            draw_text_shadow(canvas, f"Fire Hazards Left: {fires_remaining + len(active_fires)}/{config_fire_count}", font, WHITE, LOGICAL_WIDTH // 2, 30, center=True)
            draw_text_shadow(canvas, "Press DOWN/S to Crouch | SPACE to Jump | Q to Dash", font, (50, 200, 255), LOGICAL_WIDTH // 2, 60, center=True)
            draw_text_shadow(canvas, f"Score: {score}", font, WHITE, 20, 20)
            draw_text_shadow(canvas, f"Lives: {lives}", font, WHITE, 20, 55)

            time_since_heal = current_time_ms - last_heal_time
            if time_since_heal >= HEAL_COOLDOWN:
                heal_text_str = "Heal Ready! (Press H)"
                heal_text_color = GREEN
            else:
                seconds_left = math.ceil((HEAL_COOLDOWN - time_since_heal) / 1000)
                heal_text_str = f"Heal CD: {seconds_left}s"
                heal_text_color = RED
            draw_text_shadow(canvas, heal_text_str, font, heal_text_color, 20, 90)

            if shield_active:
                draw_text_shadow(canvas, "Shield Active!", font, (50, 200, 255), 20, 125)

            if is_charging:
                charge_pct = min(100, int((charge_time / 5.0) * 100))
                draw_text_shadow(canvas, f"Charging Power: {charge_pct}%", font, RED, LOGICAL_WIDTH // 2, LOGICAL_HEIGHT - 40, center=True)

        # ==================== STATE 3.95: SLIME WAVE LEVEL ====================
        elif game_state == "SLIME_STAGE":
            if is_charging:
                charge_time += dt

            keys = pygame.key.get_pressed()
            noah_vel_x = 0
            is_walking_now = False
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                noah_vel_x = -4
                is_walking_now = True
                last_facing_dir = -1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                noah_vel_x = 4
                is_walking_now = True
                last_facing_dir = 1

            if is_dashing:
                dash_timer -= 1
                noah_vel_x = dash_dir * 10
                if dash_timer <= 0:
                    is_dashing = False

            if is_walking_now and noah_on_ground and not is_dashing:
                if not WALK_CHANNEL.get_busy():
                    WALK_CHANNEL.play(sounds["walk"])

            noah_world_x += noah_vel_x
            noah_world_x = max(50, min(noah_world_x, 1550 - 90))

            camera_x = noah_world_x - (LOGICAL_WIDTH // 2)
            camera_x = max(0, min(camera_x, 1600 - LOGICAL_WIDTH))

            noah_vel_y += gravity
            noah_y += noah_vel_y
            if noah_y >= ground_y:
                noah_y = ground_y
                noah_vel_y = 0
                noah_on_ground = True
                noah_jump_count = 0

            slime_spawn_timer += 1
            if slimes_remaining > 0 and slime_spawn_timer > 60 and len(active_slimes) < 4:
                slime_spawn_timer = 0
                active_slimes.append({
                    "x": noah_world_x + 500 + random.randint(0, 200),
                    "y": ground_y,
                    "health": config_slime_hits,
                    "vel_x": 2.2,
                    "vel_y": -5,
                    "flash_timer": 0
                })
                slimes_remaining -= 1

            noah_rect = pygame.Rect(noah_world_x, noah_y, 70, 70)
            update_and_draw_powerups(canvas, camera_x, noah_rect)

            for slime in active_slimes[:]:
                slime["flash_timer"] = max(0, slime["flash_timer"] - 1)
                
                if slime["x"] > noah_world_x:
                    slime["x"] -= slime["vel_x"]
                else:
                    slime["x"] += slime["vel_x"]

                slime["vel_y"] += gravity
                slime["y"] += slime["vel_y"]
                if slime["y"] >= ground_y:
                    slime["y"] = ground_y
                    slime["vel_y"] = -random.uniform(7, 11)

                slime_rect = pygame.Rect(slime["x"], slime["y"], 60, 60)
                if slime_rect.colliderect(noah_rect) and not is_dashing:
                    active_slimes.remove(slime)
                    sounds["damage"].play()
                    if shield_active:
                        shield_active = False
                    else:
                        lives -= 1
                        if lives <= 0:
                            game_state = "GAME_OVER"

            for pfb in player_fireballs[:]:
                pfb["x"] += pfb["vel_x"]
                pfb["y"] += pfb["vel_y"]
                pfb["lifetime"] -= 1
                
                pfb_rect = pygame.Rect(pfb["x"], pfb["y"], pfb["size"], pfb["size"])
                if pfb["lifetime"] <= 0:
                    player_fireballs.remove(pfb)
                    continue
                    
                hit_slime = False
                for slime in active_slimes[:]:
                    slime_rect = pygame.Rect(slime["x"], slime["y"], 60, 60)
                    if pfb_rect.colliderect(slime_rect):
                        hit_slime = True
                        sounds["damage"].play()
                        slime["health"] -= pfb["damage"]
                        slime["flash_timer"] = 6
                        score += 30
                        if slime["health"] <= 0:
                            active_slimes.remove(slime)
                            score += 80
                            kb_dir = 1 if pfb["vel_x"] > 0 else -1
                            trigger_enemy_death(slime_img, slime["x"], slime["y"], kb_dir)
                        break
                
                if hit_slime:
                    if pfb in player_fireballs:
                        player_fireballs.remove(pfb)
                else:
                    pfb_screen_x = pfb["x"] - camera_x
                    if pfb_screen_x < 0 or pfb_screen_x > LOGICAL_WIDTH:
                        player_fireballs.remove(pfb)

            if slimes_remaining == 0 and len(active_slimes) == 0 and len(dying_enemies) == 0:
                game_state = "FADE_TRANSITION"
                fade_alpha = 0
                fade_direction = 1
                next_state_after_fade = "BOSS_FIGHT"

            render_jump_clouds(canvas, camera_x)
            
            if is_healing_display:
                canvas.blit(heal_sprite, (noah_world_x - camera_x, noah_y))
            elif is_dashing:
                if dash_dir == 1:
                    canvas.blit(dash_sprite_raw, (noah_world_x - camera_x - 10, noah_y + 25))
                else:
                    flipped_dash = pygame.transform.flip(dash_sprite_raw, True, False)
                    canvas.blit(flipped_dash, (noah_world_x - camera_x - 10, noah_y + 25))
            else:
                canvas.blit(noah_img, (noah_world_x - camera_x, noah_y))

            for slime in active_slimes:
                draw_flashed_sprite(canvas, slime_img, (slime["x"] - camera_x, slime["y"]), slime["flash_timer"])
            update_and_draw_dying_enemies(canvas, camera_x)

            for pfb in player_fireballs:
                canvas.blit(pfb["surface"], (pfb["x"] - camera_x, pfb["y"]))

            logical_mouse = get_logical_mouse_pos()
            canvas.blit(gun_img, (logical_mouse[0] - 20, logical_mouse[1] - 20))

            draw_text_shadow(canvas, f"Bouncing Slimes Left: {slimes_remaining + len(active_slimes)}/{config_slime_count}", font, WHITE, LOGICAL_WIDTH // 2, 30, center=True)
            draw_text_shadow(canvas, f"Score: {score}", font, WHITE, 20, 20)
            draw_text_shadow(canvas, f"Lives: {lives}", font, WHITE, 20, 55)

            time_since_heal = current_time_ms - last_heal_time
            if time_since_heal >= HEAL_COOLDOWN:
                heal_text_str = "Heal Ready! (Press H)"
                heal_text_color = GREEN
            else:
                seconds_left = math.ceil((HEAL_COOLDOWN - time_since_heal) / 1000)
                heal_text_str = f"Heal CD: {seconds_left}s"
                heal_text_color = RED
            draw_text_shadow(canvas, heal_text_str, font, heal_text_color, 20, 90)

            if shield_active:
                draw_text_shadow(canvas, "Shield Active!", font, (50, 200, 255), 20, 125)

            if is_charging:
                charge_pct = min(100, int((charge_time / 5.0) * 100))
                draw_text_shadow(canvas, f"Charging Power: {charge_pct}%", font, RED, LOGICAL_WIDTH // 2, LOGICAL_HEIGHT - 40, center=True)

        # ==================== STATE 4: BOSS FIGHT ====================
        elif game_state == "BOSS_FIGHT":
            if is_charging:
                charge_time += dt

            keys = pygame.key.get_pressed()
            noah_vel_x = 0
            is_walking_now = False
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                noah_vel_x = -4
                is_walking_now = True
                last_facing_dir = -1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                noah_vel_x = 4
                is_walking_now = True
                last_facing_dir = 1

            if is_dashing:
                dash_timer -= 1
                noah_vel_x = dash_dir * 10
                if dash_timer <= 0:
                    is_dashing = False

            if is_walking_now and noah_on_ground and not is_dashing:
                if not WALK_CHANNEL.get_busy():
                    WALK_CHANNEL.play(sounds["walk"])

            noah_world_x += noah_vel_x
            noah_world_x = max(50, min(noah_world_x, 1550 - 90))

            camera_x = noah_world_x - (LOGICAL_WIDTH // 2)
            camera_x = max(0, min(camera_x, 1600 - LOGICAL_WIDTH))

            noah_vel_y += gravity
            noah_y += noah_vel_y
            if noah_y >= ground_y:
                noah_y = ground_y
                noah_vel_y = 0
                noah_on_ground = True
                noah_jump_count = 0

            monster_speed = 3.0
            for boss in active_bosses:
                boss["flash_timer"] = max(0, boss["flash_timer"] - 1)
                if boss["x"] < noah_world_x:
                    boss["x"] += monster_speed
                elif boss["x"] > noah_world_x:
                    boss["x"] -= monster_speed
                boss["x"] = max(50, min(boss["x"], 1550 - 110))

            if active_bosses:
                max_world_x = active_bosses[0]["x"] + 20
                max_y = 100

            noah_rect = pygame.Rect(noah_world_x, noah_y, 70, 70)
            update_and_draw_powerups(canvas, camera_x, noah_rect)

            # Passively spawn strangers from the boss during the boss fight
            boss_stranger_timer += 1
            if boss_stranger_timer > 120 and len(active_strangers) < 3:
                boss_stranger_timer = 0
                for boss in active_bosses:
                    active_strangers.append({
                        "x": boss["x"],
                        "y": ground_y,
                        "health": config_stranger_hits,
                        "vel_x": 2.0,
                        "flash_timer": 0
                    })

            for st in active_strangers[:]:
                st["flash_timer"] = max(0, st["flash_timer"] - 1)
                if st["x"] > noah_world_x:
                    st["x"] -= st["vel_x"]
                else:
                    st["x"] += st["vel_x"]

                st_rect = pygame.Rect(st["x"], st["y"], 60, 70)
                if st_rect.colliderect(noah_rect) and not is_dashing:
                    active_strangers.remove(st)
                    sounds["damage"].play()
                    if shield_active:
                        shield_active = False
                    else:
                        lives -= 1
                        if lives <= 0:
                            game_state = "GAME_OVER"

            fireball_timer += 1
            if fireball_timer > 60:
                fireball_timer = 0
                sounds["gun_shot"].play()
                for boss in active_bosses:
                    enemy_fireballs.append({
                        "x": boss["x"] + 30,
                        "y": 140,
                        "vel_x": 2 if noah_world_x > boss["x"] else -2,
                        "vel_y": 4
                    })

            for fb in enemy_fireballs[:]:
                fb["x"] += fb["vel_x"]
                fb["y"] += fb["vel_y"]
                
                fb_screen_x = fb["x"] - camera_x
                if fb["y"] > ground_y + 50 or fb_screen_x < 0 or fb_screen_x > LOGICAL_WIDTH:
                    enemy_fireballs.remove(fb)
                elif pygame.Rect(fb["x"], fb["y"], 40, 40).colliderect(noah_rect) and not is_dashing:
                    enemy_fireballs.remove(fb)
                    sounds["damage"].play()
                    if shield_active:
                        shield_active = False
                    else:
                        lives -= 1
                        if lives <= 0:
                            game_state = "GAME_OVER"

            for pfb in player_fireballs[:]:
                pfb["x"] += pfb["vel_x"]
                pfb["y"] += pfb["vel_y"]
                pfb["lifetime"] -= 1
                
                pfb_rect = pygame.Rect(pfb["x"], pfb["y"], pfb["size"], pfb["size"])
                if pfb["lifetime"] <= 0:
                    player_fireballs.remove(pfb)
                    continue
                    
                hit_target = False
                
                # Check collision with passive strangers first
                for st in active_strangers[:]:
                    st_rect = pygame.Rect(st["x"], st["y"], 60, 70)
                    if pfb_rect.colliderect(st_rect):
                        hit_target = True
                        sounds["damage"].play()
                        st["health"] -= pfb["damage"]
                        st["flash_timer"] = 6
                        score += 25
                        if st["health"] <= 0:
                            active_strangers.remove(st)
                            score += 50
                            kb_dir = 1 if pfb["vel_x"] > 0 else -1
                            trigger_enemy_death(stranger_img, st["x"], st["y"], kb_dir)
                        break

                if not hit_target:
                    for boss in active_bosses[:]:
                        boss_rect = pygame.Rect(boss["x"], 100, 90, 70)
                        if pfb_rect.colliderect(boss_rect):
                            hit_target = True
                            sounds["damage"].play()
                            
                            is_critical = random.random() < 0.01
                            if is_critical:
                                final_damage = pfb["damage"] * 10
                                trigger_critical_text(boss["x"], 80)
                            else:
                                final_damage = pfb["damage"]
                            
                            boss["health"] -= final_damage
                            boss["flash_timer"] = 6
                            score += (final_damage * 10)
                            
                            if boss["health"] <= 0:
                                active_bosses.remove(boss)
                                kb_dir = 1 if pfb["vel_x"] > 0 else -1
                                trigger_enemy_death(monster_img, boss["x"], 100, kb_dir)
                            break
                
                if hit_target:
                    if pfb in player_fireballs:
                        player_fireballs.remove(pfb)
                else:
                    pfb_screen_x = pfb["x"] - camera_x
                    if pfb["y"] < 0 or pfb_screen_x < 0 or pfb_screen_x > LOGICAL_WIDTH:
                        player_fireballs.remove(pfb)

            if len(active_bosses) == 0 and len(dying_enemies) == 0:
                game_state = "WIN_SEQUENCE"
                win_phase = 1
                win_timer = 0
                pygame.mixer.music.stop()
                sounds["victory"].play()

            render_jump_clouds(canvas, camera_x)
            
            if is_healing_display:
                canvas.blit(heal_sprite, (noah_world_x - camera_x, noah_y))
            elif is_dashing:
                if dash_dir == 1:
                    canvas.blit(dash_sprite_raw, (noah_world_x - camera_x - 10, noah_y + 25))
                else:
                    flipped_dash = pygame.transform.flip(dash_sprite_raw, True, False)
                    canvas.blit(flipped_dash, (noah_world_x - camera_x - 10, noah_y + 25))
            else:
                canvas.blit(noah_img, (noah_world_x - camera_x, noah_y))

            for boss in active_bosses:
                draw_flashed_sprite(canvas, monster_img, (boss["x"] - camera_x, 100), boss["flash_timer"])
            for st in active_strangers:
                draw_flashed_sprite(canvas, stranger_img, (st["x"] - camera_x, st["y"]), st["flash_timer"])
            update_and_draw_dying_enemies(canvas, camera_x)
            update_and_draw_critical_texts(canvas, camera_x)

            if active_bosses:
                canvas.blit(max_img, (max_world_x - camera_x, max_y))

            for fb in enemy_fireballs:
                canvas.blit(base_fireball_img, (fb["x"] - camera_x, fb["y"]))
            for pfb in player_fireballs:
                canvas.blit(pfb["surface"], (pfb["x"] - camera_x, pfb["y"]))

            logical_mouse = get_logical_mouse_pos()
            canvas.blit(gun_img, (logical_mouse[0] - 20, logical_mouse[1] - 20))

            pygame.draw.rect(canvas, GRAY, (LOGICAL_WIDTH // 2 - 200, 30, 400, 20))
            total_current_hp = sum([b["health"] for b in active_bosses])
            total_max_hp = config_monster_health * config_monster_count
            health_ratio = max(0, total_current_hp / total_max_hp) if total_max_hp > 0 else 0
            pygame.draw.rect(canvas, RED, (LOGICAL_WIDTH // 2 - 200, 30, int(400 * health_ratio), 20))
            
            draw_text_shadow(canvas, "HP", font, WHITE, LOGICAL_WIDTH // 2, 55, center=True)
            draw_text_shadow(canvas, f"Score: {score}", font, WHITE, 20, 20)
            draw_text_shadow(canvas, f"Lives: {lives}", font, WHITE, 20, 55)

            time_since_heal = current_time_ms - last_heal_time
            if time_since_heal >= HEAL_COOLDOWN:
                heal_text_str = "Heal Ready! (Press H)"
                heal_text_color = GREEN
            else:
                seconds_left = math.ceil((HEAL_COOLDOWN - time_since_heal) / 1000)
                heal_text_str = f"Heal CD: {seconds_left}s"
                heal_text_color = RED
            draw_text_shadow(canvas, heal_text_str, font, heal_text_color, 20, 90)

            if shield_active:
                draw_text_shadow(canvas, "Shield Active!", font, (50, 200, 255), 20, 125)

            if ultra_transform_available and not ultra_transform_active:
                popup_rect = pygame.Rect(LOGICAL_WIDTH // 2 - 200, 150, 400, 50)
                pygame.draw.rect(canvas, (50, 0, 0), popup_rect, border_radius=8)
                pygame.draw.rect(canvas, RED, popup_rect, 2, border_radius=8)
                draw_text_shadow(canvas, "Ultra tranform mode... press E", font, WHITE, popup_rect.centerx, popup_rect.centery, center=True)
            
            if is_charging:
                charge_pct = min(100, int((charge_time / 5.0) * 100))
                draw_text_shadow(canvas, f"Charging Power: {charge_pct}%", font, RED, LOGICAL_WIDTH // 2, LOGICAL_HEIGHT - 40, center=True)

        # ==================== STATE 6: WIN SEQUENCE ====================
        elif game_state == "WIN_SEQUENCE":
            win_timer += 1
            pygame.mouse.set_visible(True)

            if win_phase == 1:
                if max_y < ground_y:
                    max_y += 4
                else:
                    max_y = ground_y
                    if win_timer > 90:
                        win_phase = 2

                screen_noah_x = noah_world_x - camera_x
                screen_max_x = max_world_x - camera_x

                canvas.blit(max_img, (screen_max_x, max_y))
                canvas.blit(noah_img, (screen_noah_x, noah_y))

                draw_text_shadow(canvas, "Max is dropped safely to the ground!", font, WHITE, LOGICAL_WIDTH // 2, 80, center=True)
                draw_skip_button(canvas)

            elif win_phase == 2:
                noah_world_x += 2
                max_world_x += 2
                camera_x = noah_world_x - (LOGICAL_WIDTH // 2)

                screen_noah_x = noah_world_x - camera_x
                screen_max_x = max_world_x - camera_x

                canvas.blit(noah_img, (screen_noah_x, ground_y))
                canvas.blit(max_img, (screen_max_x, ground_y))

                draw_text_shadow(canvas, "Noah and Max head home...", font, WHITE, LOGICAL_WIDTH // 2, 80, center=True)
                draw_skip_button(canvas)

                if noah_world_x > 1600 + 50:
                    win_phase = 3

            elif win_phase == 3:
                draw_text_shadow(canvas, "MAX RESCUED!", large_font, WHITE, LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 - 40, center=True)
                draw_text_shadow(canvas, "Noah defeated the monsters and saved Max!", font, WHITE, LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 + 10, center=True)
                draw_text_shadow(canvas, "Press 'R' to Replay or ESC to Exit", font, WHITE, LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 + 50, center=True)

                keys = pygame.key.get_pressed()
                if keys[pygame.K_ESCAPE]:
                    pygame.quit()
                    sys.exit()

        # ==================== STATE 7: GAME OVER ====================
        elif game_state == "GAME_OVER":
            pygame.mouse.set_visible(True)
            pygame.mixer.music.stop()
            draw_text_shadow(canvas, "GAME OVER", large_font, WHITE, LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 - 30, center=True)
            draw_text_shadow(canvas, "Noah was defeated...", font, WHITE, LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 + 10, center=True)
            draw_text_shadow(canvas, "Press 'R' to Replay or ESC to Exit", font, WHITE, LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 + 50, center=True)
            
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                pygame.quit()
                sys.exit()

    canvas.blit(crt_overlay, (0, 0))

    win_w, win_h = window.get_size()
    scaled_canvas = pygame.transform.scale(canvas, (win_w, win_h))
    window.blit(scaled_canvas, (0, 0))

    pygame.display.flip() 

    #visit "https://tinyurl.com/Sams-Games" to see more of my games!