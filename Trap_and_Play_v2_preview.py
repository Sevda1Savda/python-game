import sys
import os
import math
import array
import json
from datetime import datetime

#--- 1.STARTING LEVEL DEVIL: 6-GAME ---

try:
    import pygame
    import random
    
    pygame.mixer.init(frequency=22050, size=-16, channels=1)
    pygame.display.init()
    pygame.font.init()

    info = pygame.display.Info()
    SCREEN_WIDTH = info.current_w if info.current_w > 0 else 800
    SCREEN_HEIGHT = info.current_h if info.current_h > 0 else 1280

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
    pygame.display.set_caption("Savda's Ultimate 6-Game hub 🎮")

    # Colors
    BG_DARK = (15, 16, 22)
    PANEL_BG = (28, 30, 41)
    ACCENT_CYAN = (0, 245, 255)
    ACCENT_GREEN = (57, 255, 20)
    ACCENT_RED = (255, 7, 58)
    ACCENT_YELLOW = (255, 215, 0)
    ACCENT_PURPLE = (180, 50, 255)
    TEXT_WHITE = (245, 245, 250)
    TEXT_MUTED = (130, 137, 163)
    
    FLOWER_CENTER = (255, 215, 0)
    FLOWER_PETAL = (255, 105, 180)

    # Fonts
    font_tiny = pygame.font.Font(None, 24)
    font_small = pygame.font.Font(None, 32)   
    font_medium = pygame.font.Font(None, 45)  
    font_large = pygame.font.Font(None, 65)   
    font_jumbo = pygame.font.Font(None, 90)   

    # High Scores & Progress Tracking
    high_score_shooter = 0
    high_score_runaway = 0
    collected_secret_keys_set = set() # Unique keys set to avoid duplicate farming on death

    # Official Level Devil Structure
    DOOR_NAMES = [
        "Pits", "Spikes", "Push", "Coins", 
        "Controls", "Platforms", "Springs", "Warps", 
        "Scale", "Doors", "Saws", "Flappy", 
        "Gravity", "Movement", "Wraparound", "Hell"
    ]
    
    level_stars = {}
    for d in range(len(DOOR_NAMES)):
        for s in range(1, 6):
            level_stars[(d, s)] = 0

    # Local persistent progress, stored in the app's private directory on Android.
    try:
        from android.storage import app_storage_path
        save_dir = app_storage_path()
    except ImportError:
        save_dir = os.path.join(os.path.expanduser("~"), ".trap_and_play")
    save_path = os.path.join(save_dir, "progress.json")
    history = []
    previous_quiz = []
    try:
        with open(save_path, encoding="utf-8") as f:
            data = json.load(f)
        high_score_shooter = int(data.get("shooter", 0))
        high_score_runaway = int(data.get("runaway", 0))
        for d, stage, stars in data.get("stars", []):
            if (d, stage) in level_stars:
                level_stars[(d, stage)] = stars
        collected_secret_keys_set.update(tuple(k) for k in data.get("keys", []))
        history = data.get("history", [])
        previous_quiz = data.get("previous_quiz", [])
    except (OSError, ValueError, TypeError, KeyError):
        pass

    def save_progress():
        try:
            os.makedirs(save_dir, exist_ok=True)
            with open(save_path + ".tmp", "w", encoding="utf-8") as f:
                json.dump(dict(shooter=high_score_shooter, runaway=high_score_runaway,
                    stars=[[d, n, v] for (d, n), v in level_stars.items()],
                    keys=list(collected_secret_keys_set), history=history[-100:],
                    previous_quiz=previous_quiz), f)
            os.replace(save_path + ".tmp", save_path)
        except OSError as err:
            print("Could not save progress:", err)

    def record_result(game, result):
        history.append([datetime.now().strftime("%Y-%m-%d %H:%M"), game, str(result)])
        del history[:-100]
        save_progress()

    def history_game():
        clock = pygame.time.Clock()
        page = 0
        while True:
            screen.fill(BG_DARK)
            screen.blit(font_large.render("Game History", True, ACCENT_CYAN), (35, 35))
            screen.blit(font_small.render(f"Shooter best: {high_score_shooter} | Runaway best: {high_score_runaway}", True, TEXT_WHITE), (35, 110))
            rows = max(1, min(8, (SCREEN_HEIGHT - 300)//68))
            entries = list(reversed(history))
            for i, (stamp, game, result) in enumerate(entries[page*rows:(page+1)*rows]):
                y = 175 + i*68
                screen.blit(font_tiny.render(stamp + " | " + game, True, TEXT_MUTED), (35, y))
                screen.blit(font_small.render(result, True, TEXT_WHITE), (35, y+23))
            buttons = [(pygame.Rect(25, SCREEN_HEIGHT-100, 140, 65), "Prev"),
                       (pygame.Rect(SCREEN_WIDTH//2-70, SCREEN_HEIGHT-100, 140, 65), "Back"),
                       (pygame.Rect(SCREEN_WIDTH-165, SCREEN_HEIGHT-100, 140, 65), "Next")]
            for rect, label in buttons:
                draw_glass_panel(screen, rect)
                screen.blit(font_small.render(label, True, TEXT_WHITE), (rect.x+20, rect.y+20))
            pygame.display.flip()
            for e in pygame.event.get():
                if e.type == pygame.QUIT: return
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if buttons[1][0].collidepoint(e.pos): return
                    if buttons[0][0].collidepoint(e.pos): page=max(0,page-1)
                    if buttons[2][0].collidepoint(e.pos) and (page+1)*rows<len(entries): page+=1
            clock.tick(30)

    # Synth Sound Engine
    def generate_synth_music(track_type):
        sample_rate = 22050
        duration = 4.0  
        num_samples = int(sample_rate * duration)
        buf = array.array('h', [0] * num_samples)
        
        if track_type == "entrance": sequence = [261, 329, 392, 523, 392, 329, 440, 523]; base_amp = 2800
        elif track_type == "devil": sequence = [130, 146, 130, 123, 110, 123, 130, 98]; base_amp = 5000
        elif track_type == "puzzle": sequence = [196, 220, 261, 293, 261, 220, 196, 165]; base_amp = 3000
        else: sequence = [146, 165, 196, 220, 130, 146, 165, 196]; base_amp = 3500
            
        note_length = num_samples // len(sequence)
        
        for i in range(num_samples):
            seq_idx = (i // note_length) % len(sequence)
            freq = sequence[seq_idx]
            t = i / sample_rate
            val = math.sin(2 * math.pi * freq * t)
            amplitude = base_amp if val > 0 else -base_amp
            pulse = (i % (sample_rate // 4)) / (sample_rate // 4)
            amplitude *= (1.2 - pulse)
            buf[i] = int(max(-32768, min(32767, amplitude)))
            
        return pygame.mixer.Sound(buffer=buf)

    music_hub = generate_synth_music("entrance")
    music_devil = generate_synth_music("devil")
    music_puzzle = generate_synth_music("puzzle")

    def play_track(sound_object):
        pygame.mixer.fadeout(300)
        sound_object.play(loops=-1, fade_ms=200)

    def reset_to_menu():
        global screen
        play_track(music_hub)
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)

    def draw_glass_panel(surface, rect, border_color=ACCENT_CYAN, border_weight=3, radius=16):
        pygame.draw.rect(surface, PANEL_BG, rect, border_radius=radius)
        pygame.draw.rect(surface, border_color, rect, border_weight, border_radius=radius)

    def draw_corner_flowers(surface):
        positions = [(50, 50), (SCREEN_WIDTH - 50, 50), (50, SCREEN_HEIGHT - 50), (SCREEN_WIDTH - 50, SCREEN_HEIGHT - 50)]
        petal_offsets = [(-15, 0), (15, 0), (0, -15), (0, 15), (-11, -11), (11, -11), (-11, 11), (11, 11)]
        for cx, cy in positions:
            for ox, oy in petal_offsets:
                pygame.draw.circle(surface, FLOWER_PETAL, (cx + ox, cy + oy), 12)
            pygame.draw.circle(surface, FLOWER_CENTER, (cx, cy), 10)

    # ================= 1. LEVEL DEVIL ENGINE =================
    def play_level_devil_stage(door_idx, stage_num):
        global screen, level_stars, collected_secret_keys_set
        play_track(music_devil)
        clock = pygame.time.Clock()
        
        deaths = 0
        door_title = DOOR_NAMES[door_idx]
        
        def reset_stage():
            p = pygame.Rect(80, SCREEN_HEIGHT - 220, 45, 45)
            vel_y = 0
            is_jumping = False
            door = pygame.Rect(SCREEN_WIDTH - 130, SCREEN_HEIGHT - 230, 60, 80)
            platforms = [
                pygame.Rect(0, SCREEN_HEIGHT - 150, SCREEN_WIDTH//3-15, 40),
                pygame.Rect(SCREEN_WIDTH//3+15, SCREEN_HEIGHT - 150, SCREEN_WIDTH//3-30, 40),
                pygame.Rect(2*SCREEN_WIDTH//3+15, SCREEN_HEIGHT - 150, SCREEN_WIDTH//3-15, 40)
            ]
            spikes, falling_spikes, hidden_spikes, fake_platforms = [], [], [], []
            gravity_dir = 1
            has_secret_key = (door_idx in [0, 3, 6, 12, 14] and stage_num == 4 and (door_idx, stage_num) not in collected_secret_keys_set)
            key_rect = pygame.Rect(SCREEN_WIDTH // 2, 200, 30, 30) if has_secret_key else None
            
            if door_title == "Pits" and stage_num >= 2: fake_platforms.append(platforms.pop(1))
            elif door_title == "Spikes": hidden_spikes = [pygame.Rect(SCREEN_WIDTH - 260, SCREEN_HEIGHT - 180, 50, 30)]
            elif door_title == "Push": falling_spikes = [pygame.Rect(380, 100, 45, 40)]
            elif door_title == "Gravity": gravity_dir = -1
            elif door_title == "Doors": door.x = 200

            return p, vel_y, is_jumping, door, platforms, spikes, falling_spikes, hidden_spikes, fake_platforms, gravity_dir, key_rect

        p_rect, vel_y, is_jumping, door_rect, platforms, spikes, falling_spikes, hidden_spikes, fake_platforms, gravity_dir, key_rect = reset_stage()

        while True:
            screen.fill((224, 211, 182))
            btn_left = pygame.Rect(30, SCREEN_HEIGHT - 120, 140, 80)
            btn_jump = pygame.Rect(190, SCREEN_HEIGHT - 120, 150, 80)
            btn_right = pygame.Rect(360, SCREEN_HEIGHT - 120, 140, 80)
            back_btn = pygame.Rect(SCREEN_WIDTH - 150, 30, 110, 60)
            
            move_dir, do_jump = 0, False
            mouse_p, mouse_b = pygame.mouse.get_pos(), pygame.mouse.get_pressed()
            keys = pygame.key.get_pressed()

            if keys[pygame.K_LEFT]: move_dir = -1
            if keys[pygame.K_RIGHT]: move_dir = 1
            if keys[pygame.K_UP] or keys[pygame.K_SPACE]: do_jump = True

            for e in pygame.event.get():
                if e.type == pygame.QUIT: return
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if back_btn.collidepoint(e.pos): return
                    if btn_jump.collidepoint(e.pos): do_jump = True

            if mouse_b[0]:
                if btn_left.collidepoint(mouse_p): move_dir = -1
                elif btn_right.collidepoint(mouse_p): move_dir = 1
                if btn_jump.collidepoint(mouse_p): do_jump = True

            if door_title == "Controls" and p_rect.x > 250: move_dir = -move_dir
            if do_jump and not is_jumping:
                vel_y = -22 * gravity_dir
                is_jumping = True

            if door_title == "Doors" and p_rect.x > SCREEN_WIDTH - 320 and door_rect.x < SCREEN_WIDTH - 70: door_rect.x += 8
            elif door_title == "Spikes" and p_rect.x > SCREEN_WIDTH - 380: spikes = list(hidden_spikes)
            elif door_title == "Push" and p_rect.x > 250:
                for fs in falling_spikes: fs.y += 16

            p_rect.x += move_dir * 10
            vel_y += 1.2 * gravity_dir
            p_rect.y += vel_y

            for plat in platforms:
                if p_rect.colliderect(plat) and vel_y * gravity_dir >= 0:
                    if gravity_dir == 1 and p_rect.bottom <= plat.bottom + 10:
                        p_rect.bottom = plat.top
                        vel_y, is_jumping = 0, False
                    elif gravity_dir == -1 and p_rect.top >= plat.top - 10:
                        p_rect.top = plat.bottom
                        vel_y, is_jumping = 0, False

            if key_rect and p_rect.colliderect(key_rect):
                collected_secret_keys_set.add((door_idx, stage_num))
                save_progress()
                key_rect = None

            if p_rect.y > SCREEN_HEIGHT or p_rect.y < 0 or any(p_rect.colliderect(s) for s in spikes + falling_spikes):
                deaths += 1
                p_rect, vel_y, is_jumping, door_rect, platforms, spikes, falling_spikes, hidden_spikes, fake_platforms, gravity_dir, key_rect = reset_stage()

            if p_rect.colliderect(door_rect):
                stars = 3 if deaths == 0 else (2 if deaths <= 2 else 1)
                level_stars[(door_idx, stage_num)] = max(level_stars[(door_idx, stage_num)], stars)
                record_result("Trap Trials", f"{door_title} {stage_num}: {stars} stars")
                return

            pygame.draw.rect(screen, (44, 39, 48), door_rect)
            pygame.draw.rect(screen, (244, 193, 92), door_rect.inflate(-12, -12), 3)
            for plat in platforms:
                pygame.draw.rect(screen, (55, 48, 58), plat, border_radius=6)
                pygame.draw.rect(screen, (55, 48, 58), plat, width=2, border_radius=6)
            for f_plat in fake_platforms:
                pygame.draw.rect(screen, (55, 48, 58), f_plat, border_radius=6)
                pygame.draw.rect(screen, (55, 48, 58), f_plat, width=2, border_radius=6)
            for s in spikes + falling_spikes:
                pygame.draw.polygon(screen, ACCENT_RED, [(s.left, s.bottom), (s.centerx, s.top), (s.right, s.bottom)])
            if key_rect: pygame.draw.rect(screen, ACCENT_PURPLE, key_rect, border_radius=6)

            pygame.draw.rect(screen, (45, 75, 95), p_rect, border_radius=4)
            pygame.draw.circle(screen, (255, 255, 255), (p_rect.x+30, p_rect.y+12), 4)
            screen.blit(font_medium.render(f"Door: {door_title} ({stage_num}/5)", True, (55, 48, 58)), (40, 30))
            screen.blit(font_small.render(f"Deaths: {deaths}", True, ACCENT_RED), (40, 80))

            draw_glass_panel(screen, btn_left, ACCENT_CYAN, 3, 12)
            draw_glass_panel(screen, btn_jump, ACCENT_GREEN, 3, 12)
            draw_glass_panel(screen, btn_right, ACCENT_CYAN, 3, 12)
            draw_glass_panel(screen, back_btn, ACCENT_RED, 2, 10)
            
            screen.blit(font_medium.render("← Left", True, TEXT_WHITE), (btn_left.x + 15, btn_left.y + 20))
            screen.blit(font_medium.render("Jump ⬆", True, TEXT_WHITE), (btn_jump.x + 10, btn_jump.y + 20))
            screen.blit(font_medium.render("Right →", True, TEXT_WHITE), (btn_right.x + 10, btn_right.y + 20))
            screen.blit(font_tiny.render("Back", True, TEXT_WHITE), (back_btn.x + 30, back_btn.y + 18))

            pygame.display.update()
            clock.tick(30)

    def door_stage_select_menu(door_idx):
        global screen
        play_track(music_puzzle)
        clock = pygame.time.Clock()
        door_title = DOOR_NAMES[door_idx]
        
        while True:
            screen.fill(BG_DARK)
            title = font_large.render(f"Door: {door_title}", True, ACCENT_CYAN)
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
            
            stage_buttons = []
            for stage_num in range(1, 6):
                bx = SCREEN_WIDTH//2 - 250 + ((stage_num - 1) % 3 * 180)
                by = 200 + ((stage_num - 1) // 3 * 180)
                rect = pygame.Rect(bx, by, 140, 140)
                stage_buttons.append((rect, stage_num))
                
                draw_glass_panel(screen, rect, ACCENT_GREEN, 3, 16)
                num_txt = font_medium.render(f"1-{stage_num}", True, TEXT_WHITE)
                screen.blit(num_txt, (bx + (140 - num_txt.get_width())//2, by + 30))
                
                stars = level_stars[(door_idx, stage_num)]
                star_str = "⭐" * stars if stars > 0 else "---"
                st_surf = font_tiny.render(star_str, True, ACCENT_YELLOW)
                screen.blit(st_surf, (bx + (140 - st_surf.get_width())//2, by + 85))

            back_btn = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 120, 200, 70)
            draw_glass_panel(screen, back_btn, ACCENT_RED, 3, 12)
            screen.blit(font_medium.render("Back", True, TEXT_WHITE), (back_btn.x + 50, back_btn.y + 15))

            pygame.display.update()

            for e in pygame.event.get():
                if e.type == pygame.QUIT: return
                if e.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    if back_btn.collidepoint(x, y): return
                    for rect, stage_num in stage_buttons:
                        if rect.collidepoint(x, y):
                            play_level_devil_stage(door_idx, stage_num)
            clock.tick(30)

    def level_devil_overworld():
        global screen
        play_track(music_puzzle)
        clock = pygame.time.Clock()
        current_chapter = 1
        
        while True:
            screen.fill(BG_DARK)
            chap_titles = {1: "Trap Trials", 2: "Trap Trials II", 3: "Trap Trials III"}
            title = font_large.render(f"Chapter {current_chapter}: {chap_titles[current_chapter]}", True, ACCENT_CYAN)
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 40))

            chap_start_door = (current_chapter - 1) * 5
            total_chap_stars = sum(level_stars[(d, s)] for d in range(chap_start_door, chap_start_door + 5) for s in range(1, 6))
            
            info_txt = font_small.render(f"Chapter Stars: ⭐ {total_chap_stars} / 75 | Secret Keys: 🔑 {len(collected_secret_keys_set)}", True, ACCENT_YELLOW)
            screen.blit(info_txt, (SCREEN_WIDTH//2 - info_txt.get_width()//2, 110))

            is_unlocked = True
            if current_chapter > 1:
                prev_chap_start = (current_chapter - 2) * 5
                prev_stars = sum(level_stars[(d, s)] for d in range(prev_chap_start, prev_chap_start + 5) for s in range(1, 6))
                if prev_stars < 30: is_unlocked = False

            door_buttons = []
            if is_unlocked:
                for i in range(5):
                    door_idx = chap_start_door + i
                    if door_idx >= len(DOOR_NAMES): break
                    bx = SCREEN_WIDTH//2 - 270 + (i % 3 * 190)
                    by = 200 + (i // 3 * 180)
                    rect = pygame.Rect(bx, by, 160, 140)
                    door_buttons.append((rect, door_idx))
                    
                    draw_glass_panel(screen, rect, ACCENT_GREEN, 3, 16)
                    d_txt = font_small.render(DOOR_NAMES[door_idx], True, TEXT_WHITE)
                    screen.blit(d_txt, (bx + (160 - d_txt.get_width())//2, by + 30))
                    
                    door_stars = sum(level_stars[(door_idx, s)] for s in range(1, 6))
                    st_surf = font_tiny.render(f"⭐ {door_stars}/15", True, ACCENT_YELLOW)
                    screen.blit(st_surf, (bx + (160 - st_surf.get_width())//2, by + 85))
            else:
                lock_msg = font_large.render("🔒 CHAPTER LOCKED", True, ACCENT_RED)
                req_msg = font_small.render("Earn 30+ Stars in previous Chapter to Unlock!", True, TEXT_MUTED)
                screen.blit(lock_msg, (SCREEN_WIDTH//2 - lock_msg.get_width()//2, 280))
                screen.blit(req_msg, (SCREEN_WIDTH//2 - req_msg.get_width()//2, 360))

            btn_prev = pygame.Rect(50, SCREEN_HEIGHT - 220, 200, 70)
            btn_next = pygame.Rect(SCREEN_WIDTH - 250, SCREEN_HEIGHT - 220, 200, 70)
            back_btn = pygame.Rect(SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT - 120, 240, 70)
            
            if current_chapter > 1:
                draw_glass_panel(screen, btn_prev, ACCENT_CYAN, 2, 12)
                screen.blit(font_small.render("← Prev Chapter", True, TEXT_WHITE), (btn_prev.x + 10, btn_prev.y + 20))
            if current_chapter < 3:
                draw_glass_panel(screen, btn_next, ACCENT_CYAN, 2, 12)
                screen.blit(font_small.render("Next Chapter →", True, TEXT_WHITE), (btn_next.x + 10, btn_next.y + 20))

            draw_glass_panel(screen, back_btn, ACCENT_RED, 3, 12)
            screen.blit(font_medium.render("Main Menu", True, TEXT_WHITE), (back_btn.x + 30, back_btn.y + 15))

            pygame.display.update()

            for e in pygame.event.get():
                if e.type == pygame.QUIT: reset_to_menu(); return
                if e.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    if back_btn.collidepoint(x, y): reset_to_menu(); return
                    if current_chapter > 1 and btn_prev.collidepoint(x, y): current_chapter -= 1
                    if current_chapter < 3 and btn_next.collidepoint(x, y): current_chapter += 1
                    if is_unlocked:
                        for rect, door_idx in door_buttons:
                            if rect.collidepoint(x, y): door_stage_select_menu(door_idx)
            clock.tick(30)

    # ================= 2. GUESS NUMBER GAME (WITH KEYPAD & WIN SCREEN) =================
    def guess_the_number():
        global screen
        play_track(music_devil)
        clock = pygame.time.Clock()

        def start_new_game():
            return random.randint(1, 20), 0, "", "Guess a number between 1 and 20!", ACCENT_CYAN

        target, attempts, user_input, feedback, feedback_color = start_new_game()
        game_won = False

        def process_guess():
            nonlocal target, attempts, user_input, feedback, feedback_color, game_won
            if user_input == "":
                return
            val = int(user_input)
            attempts += 1
            if val < target:
                feedback = "Too Low! Try Higher ↑"
                feedback_color = ACCENT_YELLOW
            elif val > target:
                feedback = "Too High! Try Lower ↓"
                feedback_color = ACCENT_RED
            else:
                feedback = "Correct! You got it!"
                game_won = True
                record_result("Guess Number", f"Won in {attempts} attempts")
            user_input = ""

        # Keypad Layout Setup
        keypad_buttons = []
        labels = [
            "1", "2", "3",
            "4", "5", "6",
            "7", "8", "9",
            "C", "0", "⌫"
        ]
        
        btn_w, btn_h = 90, 75
        grid_start_x = SCREEN_WIDTH // 2 - 150
        grid_start_y = 360
        gap = 15

        for i, label in enumerate(labels):
            row, col = i // 3, i % 3
            bx = grid_start_x + col * (btn_w + gap)
            by = grid_start_y + row * (btn_h + gap)
            rect = pygame.Rect(bx, by, btn_w, btn_h)
            keypad_buttons.append((rect, label))

        btn_submit = pygame.Rect(SCREEN_WIDTH//2 - 150, grid_start_y + 4 * (btn_h + gap), 300, 75)

        while True:
            screen.fill(BG_DARK)

            back_btn = pygame.Rect(SCREEN_WIDTH - 150, 30, 110, 60)

            # Win Screen Panel & Buttons
            win_box = pygame.Rect(SCREEN_WIDTH//2 - 260, SCREEN_HEIGHT//2 - 220, 520, 440)
            btn_restart = pygame.Rect(SCREEN_WIDTH//2 - 210, win_box.y + 310, 190, 70)
            btn_quit = pygame.Rect(SCREEN_WIDTH//2 + 20, win_box.y + 310, 190, 70)

            # Event Handling
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    reset_to_menu()
                    return

                if e.type == pygame.MOUSEBUTTONDOWN:
                    if game_won:
                        if btn_restart.collidepoint(e.pos):
                            target, attempts, user_input, feedback, feedback_color = start_new_game()
                            game_won = False
                            pygame.event.clear()
                            break
                        elif btn_quit.collidepoint(e.pos):
                            reset_to_menu()
                            return
                    else:
                        if back_btn.collidepoint(e.pos):
                            reset_to_menu()
                            return

                        # Check Keypad clicks
                        for rect, label in keypad_buttons:
                            if rect.collidepoint(e.pos):
                                if label.isdigit():
                                    if len(user_input) < 3:
                                        user_input += label
                                elif label == "C":
                                    user_input = ""
                                elif label == "⌫":
                                    user_input = user_input[:-1]

                        # Check Submit button
                        if btn_submit.collidepoint(e.pos):
                            process_guess()

                # Keyboard input handling
                if e.type == pygame.KEYDOWN and not game_won:
                    if e.key == pygame.K_BACKSPACE:
                        user_input = user_input[:-1]
                    elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        process_guess()
                    elif e.unicode.isdigit() and len(user_input) < 3:
                        user_input += e.unicode

            # --- DRAW MAIN GAME SCREEN ---
            draw_glass_panel(screen, back_btn, ACCENT_RED, 2, 10)
            screen.blit(font_tiny.render("Back", True, TEXT_WHITE), (back_btn.x + 30, back_btn.y + 18))

            title_txt = font_large.render("Guess The Number", True, ACCENT_CYAN)
            screen.blit(title_txt, (SCREEN_WIDTH//2 - title_txt.get_width()//2, 50))

            fb_txt = font_medium.render(feedback, True, feedback_color)
            screen.blit(fb_txt, (SCREEN_WIDTH//2 - fb_txt.get_width()//2, 130))

            att_txt = font_small.render(f"Attempts: {attempts}", True, TEXT_WHITE)
            screen.blit(att_txt, (SCREEN_WIDTH//2 - att_txt.get_width()//2, 185))

            # Input Display Box
            input_box = pygame.Rect(SCREEN_WIDTH//2 - 150, 240, 300, 80)
            draw_glass_panel(screen, input_box, ACCENT_CYAN, 3, 15)
            disp_input = user_input if user_input != "" else "..."
            in_txt = font_large.render(disp_input, True, TEXT_WHITE if user_input != "" else TEXT_MUTED)
            screen.blit(in_txt, (SCREEN_WIDTH//2 - in_txt.get_width()//2, input_box.y + 15))

            # Draw On-Screen Keypad
            for rect, label in keypad_buttons:
                border = ACCENT_RED if label in ("C", "⌫") else ACCENT_CYAN
                draw_glass_panel(screen, rect, border, 2, 10)
                lbl_surf = font_medium.render(label, True, TEXT_WHITE)
                screen.blit(lbl_surf, (rect.x + (rect.width - lbl_surf.get_width())//2, rect.y + (rect.height - lbl_surf.get_height())//2))

            # Draw Submit Button
            draw_glass_panel(screen, btn_submit, ACCENT_GREEN, 3, 12)
            sub_txt = font_medium.render("SUBMIT", True, TEXT_WHITE)
            screen.blit(sub_txt, (SCREEN_WIDTH//2 - sub_txt.get_width()//2, btn_submit.y + 20))

            # --- DRAW WIN OVERLAY ---
            if game_won:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 225))
                screen.blit(overlay, (0, 0))

                draw_glass_panel(screen, win_box, ACCENT_GREEN, 4, 20)

                win_txt = font_large.render("YOU WIN! 🎉", True, ACCENT_GREEN)
                screen.blit(win_txt, (SCREEN_WIDTH//2 - win_txt.get_width()//2, win_box.y + 35))

                target_txt = font_medium.render(f"The number was: {target}", True, ACCENT_YELLOW)
                screen.blit(target_txt, (SCREEN_WIDTH//2 - target_txt.get_width()//2, win_box.y + 130))

                total_att_txt = font_medium.render(f"Total Attempts: {attempts}", True, TEXT_WHITE)
                screen.blit(total_att_txt, (SCREEN_WIDTH//2 - total_att_txt.get_width()//2, win_box.y + 190))

                # Play Again & Quit Buttons
                draw_glass_panel(screen, btn_restart, ACCENT_GREEN, 3, 12)
                draw_glass_panel(screen, btn_quit, ACCENT_RED, 3, 12)

                screen.blit(font_small.render("Play Again", True, TEXT_WHITE), (btn_restart.x + 25, btn_restart.y + 22))
                screen.blit(font_small.render("Exit Game", True, TEXT_WHITE), (btn_quit.x + 30, btn_quit.y + 22))

            pygame.display.update()
            clock.tick(30)

    # ================= 3. SHOOTER GAME =================
    def shooter_game():
        global screen, high_score_shooter
        play_track(music_devil)
        clock = pygame.time.Clock()
        
        def start_new_game():
            return pygame.Rect(SCREEN_WIDTH//2 - 35, SCREEN_HEIGHT - 220, 70, 40), [], [], 0, 3, 0, 0, 0

        player, bullets, enemies, enemies_hit, lives, spawn_timer, shoot_timer, last_hit_time = start_new_game()
        game_over = False
        HIT_COOLDOWN = 1500  # 1.5 seconds invulnerability after hit

        while True:
            screen.fill(BG_DARK)
            current_time = pygame.time.get_ticks()

            back_btn = pygame.Rect(SCREEN_WIDTH - 150, 30, 110, 60)
            btn_left = pygame.Rect(60, SCREEN_HEIGHT - 120, 260, 80)
            btn_right = pygame.Rect(SCREEN_WIDTH - 320, SCREEN_HEIGHT - 120, 260, 80)
            
            # Setup Game Over Buttons
            go_box = pygame.Rect(SCREEN_WIDTH//2 - 280, SCREEN_HEIGHT//2 - 220, 560, 440)
            btn_restart = pygame.Rect(SCREEN_WIDTH//2 - 220, go_box.y + 310, 200, 70)
            btn_quit = pygame.Rect(SCREEN_WIDTH//2 + 20, go_box.y + 310, 200, 70)

            # Event Loop
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    reset_to_menu()
                    return

                if e.type == pygame.MOUSEBUTTONDOWN:
                    if game_over:
                        if btn_restart.collidepoint(e.pos):
                            player, bullets, enemies, enemies_hit, lives, spawn_timer, shoot_timer, last_hit_time = start_new_game()
                            game_over = False
                        elif btn_quit.collidepoint(e.pos):
                            reset_to_menu()
                            return
                    else:
                        if back_btn.collidepoint(e.pos):
                            reset_to_menu()
                            return

            # Gameplay Logic
            if not game_over:
                mouse_p, mouse_b = pygame.mouse.get_pos(), pygame.mouse.get_pressed()
                keys = pygame.key.get_pressed()
                
                # Movement Controls
                if keys[pygame.K_LEFT] or (mouse_b[0] and btn_left.collidepoint(mouse_p)):
                    player.x = max(20, player.x - 14)
                if keys[pygame.K_RIGHT] or (mouse_b[0] and btn_right.collidepoint(mouse_p)):
                    player.x = min(SCREEN_WIDTH - 90, player.x + 14)

                # Bullet Spawning
                shoot_timer += 1
                if shoot_timer >= 8:
                    bullets.append(pygame.Rect(player.centerx - 5, player.top - 15, 10, 20))
                    shoot_timer = 0

                # Enemy Spawning
                spawn_timer += 1
                if spawn_timer > 22:
                    enemies.append(pygame.Rect(random.randint(40, SCREEN_WIDTH - 100), -50, 50, 50))
                    spawn_timer = 0

                # Bullet Movement & Cleanup
                for b in bullets[:]:
                    b.y -= 18
                    if b.y < 0:
                        bullets.remove(b)

                # Enemy Movement & Collisions
                for enemy in enemies[:]:
                    enemy.y += 8

                    # Player touched enemy
                    if enemy.colliderect(player):
                        enemies.remove(enemy)
                        if current_time - last_hit_time > HIT_COOLDOWN:
                            lives -= 1
                            last_hit_time = current_time
                            if lives <= 0:
                                lives = 0
                                game_over = True
                                if enemies_hit > high_score_shooter:
                                    high_score_shooter = enemies_hit
                                    save_progress()
                        continue

                    # Enemy reaches bottom
                    elif enemy.y > SCREEN_HEIGHT - 180:
                        enemies.remove(enemy)
                        continue

                    # Bullet hits enemy
                    for b in bullets[:]:
                        if enemy.colliderect(b):
                            if b in bullets: bullets.remove(b)
                            if enemy in enemies: enemies.remove(enemy)
                            enemies_hit += 1
                            if enemies_hit > high_score_shooter:
                                high_score_shooter = enemies_hit
                                save_progress()
                            break

            # Drawing Game Objects
            for b in bullets: 
                pygame.draw.rect(screen, ACCENT_YELLOW, b)
            for enemy in enemies: 
                draw_glass_panel(screen, enemy, ACCENT_RED, 2, 8)
            
            # Draw Player (Flashes when invulnerable)
            is_invulnerable = (current_time - last_hit_time) < HIT_COOLDOWN
            if not is_invulnerable or (current_time // 100) % 2 == 0:
                draw_glass_panel(screen, player, ACCENT_CYAN, 3, 10)

            # HUD Display
            screen.blit(font_medium.render(f"Enemies Hit: {enemies_hit}", True, ACCENT_GREEN), (40, 25))
            screen.blit(font_small.render(f"High Score: {high_score_shooter}", True, ACCENT_YELLOW), (40, 75))
            screen.blit(font_medium.render(f"Lives: {'❤️ ' * lives}", True, ACCENT_RED), (40, 115))

            # Controls & Back Button
            draw_glass_panel(screen, btn_left, ACCENT_CYAN, 3, 12)
            draw_glass_panel(screen, btn_right, ACCENT_CYAN, 3, 12)
            draw_glass_panel(screen, back_btn, ACCENT_RED, 2, 10)
            
            screen.blit(font_medium.render("← Left", True, TEXT_WHITE), (btn_left.x + 80, btn_left.y + 20))
            screen.blit(font_medium.render("Right →", True, TEXT_WHITE), (btn_right.x + 70, btn_right.y + 20))
            screen.blit(font_tiny.render("Back", True, TEXT_WHITE), (back_btn.x + 30, back_btn.y + 18))

            # GAME OVER OVERLAY
            if game_over:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 215))
                screen.blit(overlay, (0, 0))

                draw_glass_panel(screen, go_box, ACCENT_RED, 4, 20)

                go_txt = font_large.render("GAME OVER", True, ACCENT_RED)
                screen.blit(go_txt, (SCREEN_WIDTH//2 - go_txt.get_width()//2, go_box.y + 35))
                
                sc_txt = font_medium.render(f"Enemies Hit: {enemies_hit}", True, ACCENT_GREEN)
                screen.blit(sc_txt, (SCREEN_WIDTH//2 - sc_txt.get_width()//2, go_box.y + 130))
                
                hs_txt = font_medium.render(f"High Score: {high_score_shooter}", True, ACCENT_YELLOW)
                screen.blit(hs_txt, (SCREEN_WIDTH//2 - hs_txt.get_width()//2, go_box.y + 200))

                draw_glass_panel(screen, btn_restart, ACCENT_GREEN, 3, 12)
                draw_glass_panel(screen, btn_quit, ACCENT_RED, 3, 12)

                screen.blit(font_small.render("Play Again", True, TEXT_WHITE), (btn_restart.x + 30, btn_restart.y + 22))
                screen.blit(font_small.render("Quit Game", True, TEXT_WHITE), (btn_quit.x + 35, btn_quit.y + 22))

            pygame.display.update()
            clock.tick(30)

    # ================= 4. QUIZ GAME =================
    def quiz_game():
        global screen
        play_track(music_puzzle)
        clock = pygame.time.Clock()
        
        bank = [
            {"q": "What is the capital of Japan?", "o": ["Tokyo", "Kyoto", "Osaka"], "a": 0},
            {"q": "What is the capital of France?", "o": ["Lyon", "Paris", "Marseille"], "a": 1},
            {"q": "What is the capital of Australia?", "o": ["Sydney", "Melbourne", "Canberra"], "a": 2},
            {"q": "What is the capital of Canada?", "o": ["Toronto", "Ottawa", "Vancouver"], "a": 1},
            {"q": "What is the capital of Egypt?", "o": ["Cairo", "Alexandria", "Giza"], "a": 0},
            {"q": "What is the capital of Brazil?", "o": ["Rio de Janeiro", "São Paulo", "Brasília"], "a": 2},
            {"q": "What is the capital of South Korea?", "o": ["Seoul", "Busan", "Incheon"], "a": 0},
            {"q": "What is the capital of Kenya?", "o": ["Mombasa", "Nairobi", "Kisumu"], "a": 1},
            {"q": "What is the capital of Germany?", "o": ["Munich", "Frankfurt", "Berlin"], "a": 2},
            {"q": "What is the capital of Italy?", "o": ["Milan", "Rome", "Venice"], "a": 1}
        ]
        
        # 500 additional distinct arithmetic questions, plus original geography.
        for a in range(1, 21):
            for b in range(1, 26):
                answer = a * b
                bank.append({"q": f"What is {a} x {b}?", "o": [str(answer), str(answer+1), str(answer+3)], "a": 0})
        def new_questions():
            pool = [q for q in bank if q["q"] not in previous_quiz]
            selected = random.sample(pool, 20)
            previous_quiz[:] = [q["q"] for q in selected]
            save_progress()
            result = []
            for q in selected:
                order = random.sample(range(3), 3)
                result.append(dict(q=q["q"], o=[q["o"][i] for i in order], a=order.index(q["a"])))
            return result
        questions = new_questions()

        q_idx, score, user_answers, finished, review_page = 0, 0, [], False, 0

        while True:
            screen.fill(BG_DARK)
            back_btn = pygame.Rect(SCREEN_WIDTH - 150, 30, 110, 60)
            title = font_large.render("Mixed Quiz", True, ACCENT_CYAN)
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 35))

            if not finished:
                q_data = questions[q_idx]
                prog_txt = font_small.render(f"Question {q_idx + 1} of {len(questions)}", True, ACCENT_YELLOW)
                screen.blit(prog_txt, (SCREEN_WIDTH//2 - prog_txt.get_width()//2, 110))
                q_surf = font_medium.render(q_data["q"], True, TEXT_WHITE)
                screen.blit(q_surf, (SCREEN_WIDTH//2 - q_surf.get_width()//2, 170))

                option_rects = []
                for idx, opt in enumerate(q_data["o"]):
                    rect = pygame.Rect(SCREEN_WIDTH//2 - 250, 260 + (idx * 110), 500, 80)
                    option_rects.append((rect, idx))
                    draw_glass_panel(screen, rect, ACCENT_CYAN, 3, 14)
                    opt_txt = font_small.render(opt, True, TEXT_WHITE)
                    screen.blit(opt_txt, (rect.x + (500 - opt_txt.get_width())//2, rect.y + 25))
            else:
                sc_txt = font_medium.render(f"Final Score: {score} / {len(questions)}", True, ACCENT_GREEN)
                screen.blit(sc_txt, (SCREEN_WIDTH//2 - sc_txt.get_width()//2, 95))

                start_i = review_page * 5
                end_i = min(start_i + 5, len(questions))

                for idx in range(start_i, end_i):
                    q_data = questions[idx]
                    user_ans_i, correct_ans_i = user_answers[idx], q_data["a"]
                    is_correct = (user_ans_i == correct_ans_i)
                    user_str, correct_str = q_data["o"][user_ans_i], q_data["o"][correct_ans_i]

                    box_y = 150 + ((idx - start_i) * 115)
                    r_box = pygame.Rect(40, box_y, SCREEN_WIDTH - 80, 105)
                    draw_glass_panel(screen, r_box, ACCENT_GREEN if is_correct else ACCENT_RED, 2, 12)

                    q_lbl = font_small.render(f"Q{idx+1}: {q_data['q']}", True, TEXT_WHITE)
                    screen.blit(q_lbl, (r_box.x + 15, r_box.y + 12))

                    if is_correct:
                        ans_lbl = font_small.render(f"Your Answer: {user_str}  ✓ Correct!", True, ACCENT_GREEN)
                        screen.blit(ans_lbl, (r_box.x + 15, r_box.y + 55))
                    else:
                        ans_lbl = font_small.render(f"Your Answer: {user_str} ✗", True, ACCENT_RED)
                        cor_lbl = font_small.render(f"Correct Answer: {correct_str}", True, ACCENT_YELLOW)
                        screen.blit(ans_lbl, (r_box.x + 15, r_box.y + 55))
                        screen.blit(cor_lbl, (r_box.x + 360, r_box.y + 55))

                btn_prev_p = pygame.Rect(50, SCREEN_HEIGHT - 130, 160, 65)
                btn_next_p = pygame.Rect(230, SCREEN_HEIGHT - 130, 160, 65)
                replay_btn = pygame.Rect(SCREEN_WIDTH - 250, SCREEN_HEIGHT - 130, 200, 65)

                if review_page > 0:
                    draw_glass_panel(screen, btn_prev_p, ACCENT_CYAN, 2, 10)
                    screen.blit(font_small.render("← Previous", True, TEXT_WHITE), (btn_prev_p.x + 25, btn_prev_p.y + 18))
                if review_page < (len(questions)-1)//5:
                    draw_glass_panel(screen, btn_next_p, ACCENT_CYAN, 2, 10)
                    screen.blit(font_small.render("Next →", True, TEXT_WHITE), (btn_next_p.x + 25, btn_next_p.y + 18))

                draw_glass_panel(screen, replay_btn, ACCENT_GREEN, 3, 10)
                screen.blit(font_small.render("Try Again 🔄", True, TEXT_WHITE), (replay_btn.x + 30, replay_btn.y + 18))

            draw_glass_panel(screen, back_btn, ACCENT_RED, 2, 10)
            screen.blit(font_tiny.render("Back", True, TEXT_WHITE), (back_btn.x + 30, back_btn.y + 18))

            pygame.display.update()

            for e in pygame.event.get():
                if e.type == pygame.QUIT: reset_to_menu(); return
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if back_btn.collidepoint(e.pos): reset_to_menu(); return
                    if not finished:
                        for rect, opt_idx in option_rects:
                            if rect.collidepoint(e.pos):
                                user_answers.append(opt_idx)
                                if opt_idx == questions[q_idx]["a"]: score += 1
                                q_idx += 1
                                if q_idx >= len(questions):
                                    finished = True
                                    record_result("Quiz", f"{score}/{len(questions)}")
                    else:
                        if review_page > 0 and btn_prev_p.collidepoint(e.pos): review_page -= 1
                        if review_page < (len(questions)-1)//5 and btn_next_p.collidepoint(e.pos): review_page += 1
                        if replay_btn.collidepoint(e.pos):
                            questions = new_questions()
                            q_idx, score, user_answers, finished, review_page = 0, 0, [], False, 0
            clock.tick(30)

    # ================= 5. TIC TAC TOE =================
    def tic_tac_toe():
        global screen
        play_track(music_puzzle)
        clock = pygame.time.Clock()

        def check_win(board):
            wins = [
                (0,1,2), (3,4,5), (6,7,8),
                (0,3,6), (1,4,7), (2,5,8),
                (0,4,8), (2,4,6)
            ]
            for a, b, c in wins:
                if board[a] != "" and board[a] == board[b] == board[c]:
                    return board[a], (a, b, c)
            if "" not in board:
                return "Tie", None
            return None, None

        def robot_move(board):
            # Robot uses O. This minimax robot plays strongly.
            def minimax(test_board, is_maximizing):
                result, _ = check_win(test_board)
                if result == "O":
                    return 10
                if result == "X":
                    return -10
                if result == "Tie":
                    return 0

                if is_maximizing:
                    best = -999
                    for i in range(9):
                        if test_board[i] == "":
                            test_board[i] = "O"
                            score = minimax(test_board, False)
                            test_board[i] = ""
                            best = max(best, score)
                    return best
                else:
                    best = 999
                    for i in range(9):
                        if test_board[i] == "":
                            test_board[i] = "X"
                            score = minimax(test_board, True)
                            test_board[i] = ""
                            best = min(best, score)
                    return best

            best_score = -999
            best_moves = []
            for i in range(9):
                if board[i] == "":
                    board[i] = "O"
                    score = minimax(board, False)
                    board[i] = ""
                    if score > best_score:
                        best_score = score
                        best_moves = [i]
                    elif score == best_score:
                        best_moves.append(i)

            return random.choice(best_moves) if best_moves else None

        # ---------- MODE SELECT ----------
        mode = None
        while mode is None:
            screen.fill(BG_DARK)

            title = font_large.render("Tic Tac Toe", True, ACCENT_CYAN)
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))

            sub = font_small.render("Choose Game Mode", True, TEXT_WHITE)
            screen.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, 165))

            btn_one = pygame.Rect(SCREEN_WIDTH//2 - 260, 280, 520, 100)
            btn_two = pygame.Rect(SCREEN_WIDTH//2 - 260, 420, 520, 100)
            back_btn = pygame.Rect(SCREEN_WIDTH//2 - 120, 580, 240, 70)

            draw_glass_panel(screen, btn_one, ACCENT_GREEN, 3, 16)
            draw_glass_panel(screen, btn_two, ACCENT_CYAN, 3, 16)
            draw_glass_panel(screen, back_btn, ACCENT_RED, 3, 12)

            one_txt = font_medium.render("1 Player", True, TEXT_WHITE)
            two_txt = font_medium.render("2 Player", True, TEXT_WHITE)
            back_txt = font_small.render("Back", True, TEXT_WHITE)

            screen.blit(one_txt, (btn_one.centerx - one_txt.get_width()//2, btn_one.centery - one_txt.get_height()//2))
            screen.blit(two_txt, (btn_two.centerx - two_txt.get_width()//2, btn_two.centery - two_txt.get_height()//2))
            screen.blit(back_txt, (back_btn.centerx - back_txt.get_width()//2, back_btn.centery - back_txt.get_height()//2))

            pygame.display.update()

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    reset_to_menu()
                    return
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if btn_one.collidepoint(e.pos):
                        mode = "1P"
                    elif btn_two.collidepoint(e.pos):
                        mode = "2P"
                    elif back_btn.collidepoint(e.pos):
                        reset_to_menu()
                        return
            clock.tick(30)

        # ---------- PLAYER NAMES ----------
        if mode == "1P":
            player_names = {"X": "You", "O": "Robot"}
        else:
            player1 = ""
            player2 = ""
            active_field = 1
            name_entry_done = False

            try:
                pygame.key.start_text_input()
            except Exception:
                pass

            while not name_entry_done:
                screen.fill(BG_DARK)

                title = font_large.render("Enter Player Names", True, ACCENT_CYAN)
                screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 65))

                label1 = font_small.render("Player 1 (X)", True, ACCENT_GREEN)
                label2 = font_small.render("Player 2 (O)", True, ACCENT_RED)
                screen.blit(label1, (SCREEN_WIDTH//2 - 260, 190))
                screen.blit(label2, (SCREEN_WIDTH//2 - 260, 340))

                box1 = pygame.Rect(SCREEN_WIDTH//2 - 260, 235, 520, 75)
                box2 = pygame.Rect(SCREEN_WIDTH//2 - 260, 385, 520, 75)
                start_btn = pygame.Rect(SCREEN_WIDTH//2 - 180, 510, 360, 80)
                back_btn = pygame.Rect(SCREEN_WIDTH//2 - 120, 625, 240, 65)

                draw_glass_panel(screen, box1, ACCENT_YELLOW if active_field == 1 else ACCENT_CYAN, 3, 12)
                draw_glass_panel(screen, box2, ACCENT_YELLOW if active_field == 2 else ACCENT_CYAN, 3, 12)
                draw_glass_panel(screen, start_btn, ACCENT_GREEN, 3, 12)
                draw_glass_panel(screen, back_btn, ACCENT_RED, 3, 12)

                p1_show = player1 if player1 else "Tap and type Player 1 name"
                p2_show = player2 if player2 else "Tap and type Player 2 name"

                p1_txt = font_small.render(p1_show, True, TEXT_WHITE if player1 else TEXT_MUTED)
                p2_txt = font_small.render(p2_show, True, TEXT_WHITE if player2 else TEXT_MUTED)
                start_txt = font_medium.render("START GAME", True, TEXT_WHITE)
                back_txt = font_small.render("Back", True, TEXT_WHITE)

                screen.blit(p1_txt, (box1.x + 20, box1.y + 22))
                screen.blit(p2_txt, (box2.x + 20, box2.y + 22))
                screen.blit(start_txt, (start_btn.centerx - start_txt.get_width()//2, start_btn.centery - start_txt.get_height()//2))
                screen.blit(back_txt, (back_btn.centerx - back_txt.get_width()//2, back_btn.centery - back_txt.get_height()//2))

                hint = font_tiny.render("Tap a box, then type a name. Max 12 characters.", True, TEXT_MUTED)
                screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, 720))

                pygame.display.update()

                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        try:
                            pygame.key.stop_text_input()
                        except Exception:
                            pass
                        reset_to_menu()
                        return

                    if e.type == pygame.MOUSEBUTTONDOWN:
                        if box1.collidepoint(e.pos):
                            active_field = 1
                        elif box2.collidepoint(e.pos):
                            active_field = 2
                        elif start_btn.collidepoint(e.pos):
                            if player1.strip() and player2.strip():
                                player1 = player1.strip()
                                player2 = player2.strip()
                                name_entry_done = True
                        elif back_btn.collidepoint(e.pos):
                            try:
                                pygame.key.stop_text_input()
                            except Exception:
                                pass
                            return tic_tac_toe()

                    if e.type == pygame.TEXTINPUT:
                        clean_text = "".join(ch for ch in e.text if ch.isprintable())
                        if active_field == 1 and len(player1) < 12:
                            player1 += clean_text[:12-len(player1)]
                        elif active_field == 2 and len(player2) < 12:
                            player2 += clean_text[:12-len(player2)]

                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_TAB:
                            active_field = 2 if active_field == 1 else 1
                        elif e.key == pygame.K_BACKSPACE:
                            if active_field == 1:
                                player1 = player1[:-1]
                            else:
                                player2 = player2[:-1]
                        elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            if player1.strip() and player2.strip():
                                player1 = player1.strip()
                                player2 = player2.strip()
                                name_entry_done = True

                clock.tick(30)

            try:
                pygame.key.stop_text_input()
            except Exception:
                pass

            player_names = {"X": player1, "O": player2}

        # ---------- GAME ----------
        board = [""] * 9
        turn = "X"
        winner = None
        winning_line = None

        grid_start_x = SCREEN_WIDTH // 2 - 210
        grid_start_y = 220
        cell_size = 140

        while True:
            screen.fill(BG_DARK)
            back_btn = pygame.Rect(SCREEN_WIDTH - 150, 30, 110, 60)

            title = font_large.render("Tic Tac Toe", True, ACCENT_CYAN)
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 45))

            if not winner:
                turn_name = player_names[turn]
                turn_color = ACCENT_GREEN if turn == "X" else ACCENT_RED
                turn_txt = font_small.render(f"{turn_name}'s Turn ({turn})", True, turn_color)
                screen.blit(turn_txt, (SCREEN_WIDTH//2 - turn_txt.get_width()//2, 125))

            line_color = ACCENT_CYAN
            line_width = 8

            pygame.draw.line(screen, line_color, (grid_start_x + cell_size, grid_start_y), (grid_start_x + cell_size, grid_start_y + cell_size * 3), line_width)
            pygame.draw.line(screen, line_color, (grid_start_x + cell_size * 2, grid_start_y), (grid_start_x + cell_size * 2, grid_start_y + cell_size * 3), line_width)
            pygame.draw.line(screen, line_color, (grid_start_x, grid_start_y + cell_size), (grid_start_x + cell_size * 3, grid_start_y + cell_size), line_width)
            pygame.draw.line(screen, line_color, (grid_start_x, grid_start_y + cell_size * 2), (grid_start_x + cell_size * 3, grid_start_y + cell_size * 2), line_width)

            grid_rects = []
            for i in range(9):
                row, col = i // 3, i % 3
                rect = pygame.Rect(grid_start_x + (col * cell_size), grid_start_y + (row * cell_size), cell_size, cell_size)
                grid_rects.append((rect, i))

                if board[i] != "":
                    color = ACCENT_GREEN if board[i] == "X" else ACCENT_RED
                    mark = font_jumbo.render(board[i], True, color)
                    screen.blit(mark, (rect.x + (cell_size - mark.get_width())//2, rect.y + (cell_size - mark.get_height())//2))

            if winning_line:
                start_rect = grid_rects[winning_line[0]][0]
                end_rect = grid_rects[winning_line[2]][0]
                pygame.draw.line(screen, ACCENT_RED, start_rect.center, end_rect.center, 12)

            if winner:
                if winner == "Tie":
                    msg = "It's a Tie!"
                    color = ACCENT_YELLOW
                else:
                    msg = f"{player_names[winner]} WINS!"
                    color = ACCENT_GREEN if winner == "X" else ACCENT_RED

                w_txt = font_medium.render(msg, True, color)
                screen.blit(w_txt, (SCREEN_WIDTH//2 - w_txt.get_width()//2, grid_start_y + cell_size * 3 + 40))

                btn_restart = pygame.Rect(SCREEN_WIDTH//2 - 170, grid_start_y + cell_size * 3 + 110, 340, 70)
                btn_mode = pygame.Rect(SCREEN_WIDTH//2 - 170, grid_start_y + cell_size * 3 + 200, 340, 70)

                draw_glass_panel(screen, btn_restart, ACCENT_GREEN, 3, 12)
                draw_glass_panel(screen, btn_mode, ACCENT_CYAN, 3, 12)

                again_txt = font_small.render("Play Again", True, TEXT_WHITE)
                mode_txt = font_small.render("Change Mode", True, TEXT_WHITE)

                screen.blit(again_txt, (btn_restart.centerx - again_txt.get_width()//2, btn_restart.centery - again_txt.get_height()//2))
                screen.blit(mode_txt, (btn_mode.centerx - mode_txt.get_width()//2, btn_mode.centery - mode_txt.get_height()//2))

            draw_glass_panel(screen, back_btn, ACCENT_RED, 2, 10)
            screen.blit(font_tiny.render("Back", True, TEXT_WHITE), (back_btn.x + 30, back_btn.y + 18))

            pygame.display.update()

            # In 1-player mode, the robot moves automatically after the human.
            if mode == "1P" and not winner and turn == "O":
                pygame.time.delay(300)
                move = robot_move(board)
                if move is not None:
                    board[move] = "O"
                    winner, winning_line = check_win(board)
                    if winner:
                        record_result("Tic Tac Toe", "Tie" if winner == "Tie" else player_names[winner] + " wins")
                    if not winner:
                        turn = "X"
                continue

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    reset_to_menu()
                    return

                if e.type == pygame.MOUSEBUTTONDOWN:
                    if back_btn.collidepoint(e.pos):
                        reset_to_menu()
                        return

                    if winner:
                        if btn_restart.collidepoint(e.pos):
                            board = [""] * 9
                            turn = "X"
                            winner = None
                            winning_line = None
                        elif btn_mode.collidepoint(e.pos):
                            return tic_tac_toe()
                    else:
                        if mode == "1P" and turn != "X":
                            continue

                        for rect, idx in grid_rects:
                            if rect.collidepoint(e.pos) and board[idx] == "":
                                board[idx] = turn
                                winner, winning_line = check_win(board)
                                if winner:
                                    record_result("Tic Tac Toe", "Tie" if winner == "Tie" else player_names[winner] + " wins")
                                if not winner:
                                    turn = "O" if turn == "X" else "X"
                                break

            clock.tick(30)

    # ================= 6. RUNAWAY GAME =================
    def runaway_game():
        global screen, high_score_runaway
        play_track(music_devil)
        clock = pygame.time.Clock()

        ground_y = SCREEN_HEIGHT - 220

        def start_new_run():
            return SCREEN_WIDTH // 2 - 25, ground_y, 0, False, False, 0, [], [], 0, 0, False

        player_x, player_y, vel_y, is_jumping, is_ducking, duck_timer, obstacles, coins, coins_collected, frame_count, game_over = start_new_run()

        touch_start_pos = None
        tunnel_scroll = 0

        def draw_jail_tunnel_background(surface, scroll):
            surface.fill((18, 20, 26))
            pygame.draw.polygon(surface, (28, 30, 40), [(0, 0), (SCREEN_WIDTH, 0), (SCREEN_WIDTH - 60, ground_y + 10), (60, ground_y + 10)])
            
            brick_h = 40
            offset_y = (scroll * 12) % brick_h
            for y in range(0, SCREEN_HEIGHT, brick_h):
                line_y = y + offset_y
                pygame.draw.line(surface, (40, 45, 60), (0, line_y), (SCREEN_WIDTH, line_y), 2)
            
            pygame.draw.rect(surface, (25, 27, 36), (50, ground_y + 5, SCREEN_WIDTH - 100, SCREEN_HEIGHT - ground_y))
            pygame.draw.line(surface, ACCENT_RED, (50, ground_y + 5), (SCREEN_WIDTH - 50, ground_y + 5), 4)

        def draw_real_character(surface, x, y, jumping, ducking):
            body_h = 30 if ducking else 45
            head_r = 12 if not ducking else 10
            head_y = y - body_h - head_r

            pygame.draw.circle(surface, ACCENT_YELLOW, (x + 20, head_y), head_r)
            pygame.draw.line(surface, ACCENT_CYAN, (x + 20, head_y + head_r), (x + 20, y - 15), 4)
            
            if ducking:
                pygame.draw.line(surface, ACCENT_CYAN, (x + 20, head_y + head_r + 5), (x + 5, y - 10), 3)
                pygame.draw.line(surface, ACCENT_CYAN, (x + 20, head_y + head_r + 5), (x + 35, y - 10), 3)
                pygame.draw.line(surface, ACCENT_CYAN, (x + 20, y - 15), (x + 5, y), 4)
                pygame.draw.line(surface, ACCENT_CYAN, (x + 20, y - 15), (x + 35, y), 4)
            elif jumping:
                pygame.draw.line(surface, ACCENT_CYAN, (x + 20, head_y + head_r + 5), (x, head_y + head_r - 10), 3)
                pygame.draw.line(surface, ACCENT_CYAN, (x + 20, head_y + head_r + 5), (x + 40, head_y + head_r - 10), 3)
                pygame.draw.line(surface, ACCENT_CYAN, (x + 20, y - 15), (x + 10, y + 10), 4)
                pygame.draw.line(surface, ACCENT_CYAN, (x + 20, y - 15), (x + 30, y + 10), 4)
            else:
                t = pygame.time.get_ticks() // 100
                leg_shift = math.sin(t) * 12
                pygame.draw.line(surface, ACCENT_CYAN, (x + 20, head_y + head_r + 5), (x + 5, head_y + head_r + 20), 3)
                pygame.draw.line(surface, ACCENT_CYAN, (x + 20, head_y + head_r + 5), (x + 35, head_y + head_r + 20), 3)
                pygame.draw.line(surface, ACCENT_CYAN, (x + 20, y - 15), (x + 20 + leg_shift, y), 4)
                pygame.draw.line(surface, ACCENT_CYAN, (x + 20, y - 15), (x + 20 - leg_shift, y), 4)

        while True:
            tunnel_scroll += 1
            draw_jail_tunnel_background(screen, tunnel_scroll)
            
            back_btn = pygame.Rect(SCREEN_WIDTH - 150, 30, 110, 60)
            
            go_box = pygame.Rect(SCREEN_WIDTH//2 - 260, SCREEN_HEIGHT//2 - 220, 520, 440)
            btn_restart = pygame.Rect(SCREEN_WIDTH//2 - 210, go_box.y + 290, 190, 70)
            btn_exit = pygame.Rect(SCREEN_WIDTH//2 + 20, go_box.y + 290, 190, 70)

            for e in pygame.event.get():
                if e.type == pygame.QUIT: reset_to_menu(); return
                
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if game_over:
                        if btn_restart.collidepoint(e.pos):
                            player_x, player_y, vel_y, is_jumping, is_ducking, duck_timer, obstacles, coins, coins_collected, frame_count, game_over = start_new_run()
                        elif btn_exit.collidepoint(e.pos):
                            reset_to_menu()
                            return
                    else:
                        if back_btn.collidepoint(e.pos): 
                            reset_to_menu()
                            return
                        touch_start_pos = e.pos
                
                if e.type == pygame.MOUSEBUTTONUP and touch_start_pos and not game_over:
                    dx = e.pos[0] - touch_start_pos[0]
                    dy = e.pos[1] - touch_start_pos[1]
                    
                    if abs(dx) > abs(dy):
                        if dx < -30: player_x = max(40, player_x - 120)
                        elif dx > 30: player_x = min(SCREEN_WIDTH - 80, player_x + 120)
                    else:
                        if dy < -30 and not is_jumping:
                            vel_y = -22
                            is_jumping = True
                        elif dy > 30:
                            is_ducking = True
                            duck_timer = 15
                    touch_start_pos = None

            if not game_over:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT]: player_x = max(40, player_x - 12)
                if keys[pygame.K_RIGHT]: player_x = min(SCREEN_WIDTH - 80, player_x + 12)
                if (keys[pygame.K_UP] or keys[pygame.K_SPACE]) and not is_jumping:
                    vel_y = -22
                    is_jumping = True
                if keys[pygame.K_DOWN]:
                    is_ducking = True
                    duck_timer = 15

                if is_jumping:
                    player_y += vel_y
                    vel_y += 1.4
                    if player_y >= ground_y:
                        player_y = ground_y
                        is_jumping = False
                        vel_y = 0

                if duck_timer > 0:
                    duck_timer -= 1
                    if duck_timer == 0: is_ducking = False

                frame_count += 1

                # Spawn Obstacles & Coins
                if frame_count % 20 == 0:
                    obs_type = random.choice(["high", "low"])
                    if obs_type == "high":
                        obstacles.append({"rect": pygame.Rect(random.randint(60, SCREEN_WIDTH - 120), -40, 60, 40), "type": "high"})
                    else:
                        obstacles.append({"rect": pygame.Rect(random.randint(60, SCREEN_WIDTH - 120), -40, 60, 80), "type": "low"})

                if frame_count % 15 == 0:
                    coins.append(pygame.Rect(random.randint(60, SCREEN_WIDTH - 90), -30, 30, 30))

                p_h = 35 if is_ducking else 65
                player_rect = pygame.Rect(player_x, player_y - p_h, 40, p_h)

                for obs in obstacles[:]:
                    obs["rect"].y += 12
                    if obs["rect"].colliderect(player_rect):
                        game_over = True
                        if coins_collected > high_score_runaway:
                            high_score_runaway = coins_collected
                            save_progress()
                    if obs["rect"].y > SCREEN_HEIGHT: obstacles.remove(obs)

                for coin in coins[:]:
                    coin.y += 10
                    if coin.colliderect(player_rect):
                        coins.remove(coin)
                        coins_collected += 1
                        if coins_collected > high_score_runaway:
                            high_score_runaway = coins_collected
                            save_progress()
                    elif coin.y > SCREEN_HEIGHT: coins.remove(coin)

            for obs in obstacles:
                color = ACCENT_PURPLE if obs["type"] == "high" else ACCENT_RED
                pygame.draw.rect(screen, color, obs["rect"], border_radius=8)

            for coin in coins:
                pygame.draw.circle(screen, ACCENT_YELLOW, coin.center, 14)
                screen.blit(font_tiny.render("🪙", True, TEXT_WHITE), (coin.x + 3, coin.y + 4))

            draw_real_character(screen, player_x, player_y, is_jumping, is_ducking)

            # HUD Display
            screen.blit(font_medium.render(f"Coins (Score): 🪙 {coins_collected}", True, ACCENT_YELLOW), (30, 25))
            screen.blit(font_small.render(f"High Score: 🪙 {high_score_runaway}", True, ACCENT_CYAN), (30, 75))
            
            draw_glass_panel(screen, back_btn, ACCENT_RED, 2, 10)
            screen.blit(font_tiny.render("Back", True, TEXT_WHITE), (back_btn.x + 30, back_btn.y + 18))

            if game_over:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 210))
                screen.blit(overlay, (0, 0))

                draw_glass_panel(screen, go_box, ACCENT_RED, 4, 20)

                go_txt = font_large.render("CAUGHT BY GUARDS!", True, ACCENT_RED)
                screen.blit(go_txt, (SCREEN_WIDTH//2 - go_txt.get_width()//2, go_box.y + 45))

                sc_txt = font_medium.render(f"Coins Collected: 🪙 {coins_collected}", True, ACCENT_YELLOW)
                screen.blit(sc_txt, (SCREEN_WIDTH//2 - sc_txt.get_width()//2, go_box.y + 140))

                hs_txt = font_medium.render(f"High Score: 🪙 {high_score_runaway}", True, ACCENT_CYAN)
                screen.blit(hs_txt, (SCREEN_WIDTH//2 - hs_txt.get_width()//2, go_box.y + 205))

                draw_glass_panel(screen, btn_restart, ACCENT_GREEN, 3, 12)
                draw_glass_panel(screen, btn_exit, ACCENT_RED, 3, 12)

                screen.blit(font_small.render("Play Again", True, TEXT_WHITE), (btn_restart.x + 25, btn_restart.y + 20))
                screen.blit(font_small.render("Exit Game", True, TEXT_WHITE), (btn_exit.x + 30, btn_exit.y + 20))

            pygame.display.update()
            clock.tick(30)

    # ================= MAIN MENU =================
    def exit_game():
        pygame.quit()
        sys.exit()

    buttons = [
        ("Trap Trials", level_devil_overworld),
        ("Guess Number", guess_the_number),
        ("Shooter Game", shooter_game),
        ("Quiz Game", quiz_game),
        ("Tic Tac Toe", tic_tac_toe),
        ("Runaway", runaway_game),
        ("History", history_game),
        ("Exit", exit_game)
    ]

    clock = pygame.time.Clock()
    play_track(music_hub)

    while True:
        screen.fill(BG_DARK)
        draw_corner_flowers(screen)
        
        title = font_jumbo.render("Trap & Play: Mini Games", True, ACCENT_GREEN)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        mouse_x, mouse_y = pygame.mouse.get_pos()
        button_rects = []
        
        for idx, (text, _) in enumerate(buttons):
            bx = SCREEN_WIDTH // 2 - 280
            by = 150 + (idx * min(85, (SCREEN_HEIGHT-240)//len(buttons)))
            bw, bh = 560, min(75, (SCREEN_HEIGHT-240)//len(buttons)-8)
            rect = pygame.Rect(bx, by, bw, bh)
            button_rects.append(rect)
            
            color_state = ACCENT_GREEN if rect.collidepoint(mouse_x, mouse_y) else ACCENT_CYAN
            draw_glass_panel(screen, rect, color_state, 3, 14)
            
            txt_surf = font_medium.render(text, True, TEXT_WHITE)
            screen.blit(txt_surf, (bx + (bw - txt_surf.get_width()) // 2, by + (bh - txt_surf.get_height()) // 2))

        # Small subtitle under Exit
        subtitle = font_tiny.render(
            "Six games. Countless challenges. Can you beat them all?",
            True,
            TEXT_MUTED
        )
        screen.blit(
            subtitle,
            (
                SCREEN_WIDTH // 2 - subtitle.get_width() // 2,
                150 + (len(buttons) * min(85, (SCREEN_HEIGHT-240)//len(buttons))) + 10
            )
        )

        # Copyright
        copyright_text = font_tiny.render(
            "© 2026 Savda Shah",
            True,
            TEXT_MUTED
        )
        screen.blit(
            copyright_text,
            (
                SCREEN_WIDTH // 2 - copyright_text.get_width() // 2,
                150 + (len(buttons) * min(85, (SCREEN_HEIGHT-240)//len(buttons))) + 40
            )
        )

        pygame.display.update()

        pygame.display.update()
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for idx, rect in enumerate(button_rects):
                    if rect.collidepoint(mouse_x, mouse_y):
                        buttons[idx][1]()

except Exception as error:
    print("\n--- AN ERROR OCCURRED ---")
    print(error)
    input("\nPress Enter to exit...")