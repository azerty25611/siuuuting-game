import pygame
import random
import math

# =============================================================================
# 1. 초기 설정 (Initialization)
# =============================================================================
pygame.init()
pygame.mixer.init()

# 화면 크기
WIDTH, HEIGHT = 540, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
virtual_screen = pygame.Surface((WIDTH, HEIGHT))
is_fullscreen = False
pygame.display.set_caption("siuuuting! demo")

# 게임 루프 제어
clock = pygame.time.Clock()
running = True

# =============================================================================
# 2. 상수 (Constants)
# =============================================================================
# 색상
WHITE = (160, 160, 160)
BLACK = (0, 0, 0)

# 플레이어 설정
PLAYER_SIZE = 45
PLAYER_SPEED = 5
PLAYER_HP_START = 3
PLAYER_INVINCIBLE_DURATION = 120  # 60프레임 = 약 2초

# 총알 설정
BULLET_SPEED = 10
MAX_BULLETS = 5        #플레이어 기체가 최대 발사 가능한 총알 수
PLAYER_BULLET_VISUAL_SIZE = (50, 100)
PLAYER_BULLET_HITBOX_SIZE = (15, 70)

# 적 설정
ENEMY_SIZE = 50

# 배경 설정
BG_SPEED = 6

# =============================================================================
# 3. 리소스 로딩 (Asset Loading)
# =============================================================================
# 배경 이미지
background = pygame.image.load("background.png")
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

# 플레이어 이미지
player_image = pygame.image.load("player.png")
player_image = pygame.transform.scale(player_image, (PLAYER_SIZE, PLAYER_SIZE))

# 총알 이미지
bullet_image = pygame.image.load("playerbullet.png")
bullet_image = pygame.transform.scale(bullet_image, PLAYER_BULLET_VISUAL_SIZE)
enemy_bullet_img = pygame.image.load("enemy_bullet.png")
enemy_bullet_img = pygame.transform.scale(enemy_bullet_img, (80, 80))

# 적 이미지
enemy_images = {
    "normal": pygame.image.load("enemy_normal.png"),
    "strong": pygame.image.load("enemy_strong.png"),
    "shooter": pygame.image.load("enemy_shooter.png")
}

enemy_sizes = {
    "normal": (40, 40),
    "shooter": (175, 175),
    "strong": (300, 300)
}

enemy_hitbox_sizes = {
    "normal": (40, 40),
    "shooter": (75, 175),
    "strong": (130, 300)
}

# 적 타입별 폭발 크기 딕셔너리
enemy_explosion_sizes = {
    "normal": 80,
    "shooter": 175,
    "strong": 300
}

# 적 이미지 크기 조절
for key in enemy_images:
    w, h = enemy_sizes[key]
    enemy_images[key] = pygame.transform.scale(enemy_images[key], (w, h))

# 폭발 이미지
explosion_image = pygame.image.load("explosion.png")
explosion_image = pygame.transform.scale(explosion_image, (50, 50))

# 사운드
pygame.mixer.music.load("backgroundmusic.ogg")
pygame.mixer.music.set_volume(0.2)
shoot_sound = pygame.mixer.Sound("shoot_sound.ogg")
shoot_sound.set_volume(0.4)
explosion_sound = pygame.mixer.Sound("explosion_sound.ogg")
explosion_sound.set_volume(0.3)

# 폰트
font_title = pygame.font.SysFont(None, 74)
font_start = pygame.font.SysFont(None, 48)
font_ui = pygame.font.SysFont(None, 36)
font_gameover_big = pygame.font.SysFont(None, 70)
font_gameover_small = pygame.font.SysFont(None, 40)
# 일시정지 폰트
font_pause = pygame.font.SysFont(None, 60)


# =============================================================================
# 4. 게임 변수 (Game Variables)
# =============================================================================
# 게임 상태
game_started = False
gameover = False
is_paused = False # 일시정지 상태 변수

# 플레이어 상태
player_x = WIDTH // 2 - PLAYER_SIZE // 2
player_y = HEIGHT - PLAYER_SIZE - 10
player_hp = PLAYER_HP_START
player_dead = False
player_explosion_timer = 0
player_invincible = False
invincible_timer = 0

# 객체 리스트
bullets = []
enemies = []
enemy_bullets = []
explosions = []

# 점수
score = 0
game_timer = 0

# 배경 위치
bg_y1 = 0
bg_y2 = -HEIGHT

# 플레이어 기체의 총알 연속 발사
firing = False      # 스페이스바 눌림 상태
fire_delay = 0.1    # 발사 간격 (초)
fire_timer = 0      # 발사 쿨타임


# =============================================================================
# 5. 함수 (Functions)
# =============================================================================
def draw_neon_glow_text(surface, text, font, text_color, glow_color, pos, glow_radius=8):
    """네온 효과 텍스트를 그리는 함수"""
    text_surface = font.render(text, True, text_color)
    for i in range(glow_radius, 1, -2):
        glow_surface = font.render(text, True, glow_color)
        glow_surface.set_alpha(30)
        surface.blit(glow_surface, (pos[0] - i, pos[1] - i))
        surface.blit(glow_surface, (pos[0] + i, pos[1] - i))
        surface.blit(glow_surface, (pos[0] - i, pos[1] + i))
        surface.blit(glow_surface, (pos[0] + i, pos[1] + i))
    surface.blit(text_surface, pos)

def reset_enemies():
    """적 리스트를 초기화하고 새로 생성하는 함수"""
    enemies.clear()
    # 일반 적
    for _ in range(5):
        enemies.append({"type": "normal", "x": random.randint(0, WIDTH - ENEMY_SIZE),
                        "y": random.randint(-300, -ENEMY_SIZE), "hp": 1, "speed": 7,
                        "score": 1, "shoot_timer": 0})
    # 슈터 적
    for _ in range(3):
        enemies.append({"type": "shooter", "x": random.randint(0, WIDTH - ENEMY_SIZE),
                        "y": random.randint(-700, -ENEMY_SIZE), "hp": 5, "speed": 2,
                        "score": 5, "shoot_timer": 0, "shoot_delay": random.uniform(2, 3)})
    # 강력한 적
    for _ in range(1):
        enemies.append({"type": "strong", "x": random.randint(0, WIDTH - ENEMY_SIZE),
                        "y": random.randint(-500, -ENEMY_SIZE), "hp": 10, "speed": 1,
                        "score": 10, "shoot_timer": 0,
                        "shoot_delay": random.uniform(2.0, 3.5)})

def game_reset():
    """게임오버 후 재시작 시 변수를 초기화하는 함수"""
    global player_x, player_y, score, player_hp, player_dead, player_explosion_timer, player_invincible, invincible_timer, gameover, game_timer, is_paused
    global firing, fire_timer
    score = 0
    game_timer = 0
    player_hp = PLAYER_HP_START
    player_dead = False
    player_explosion_timer = 0
    player_invincible = False
    invincible_timer = 0
    gameover = False
    is_paused = False # 재시작 시 일시정지 해제
    firing = False
    fire_timer = 0
    bullets.clear()
    enemy_bullets.clear()
    reset_enemies()


# =============================================================================
# 6. 메인 게임 루프 (Main Game Loop)
# =============================================================================
reset_enemies()

while running:
    # --- 프레임 설정 ---
    dt = clock.tick(60) / 1000

    # -------------------------------------------------------------------------
    # (1) 이벤트 처리 (Event Handling)
    # -------------------------------------------------------------------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # --- 키 눌림 ---
        elif event.type == pygame.KEYDOWN:
            # P 키로 일시정지/재개
            if event.key == pygame.K_p and game_started and not gameover:
                is_paused = not is_paused
                if is_paused:
                    pygame.mixer.music.pause()
                else:
                    pygame.mixer.music.unpause()

            # 전체화면 토글 (Alt + Enter)
            elif event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT):
                is_fullscreen = not is_fullscreen
                if is_fullscreen:
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    screen = pygame.display.set_mode((WIDTH, HEIGHT))
                    
            # 게임 시작
            elif not game_started and event.key == pygame.K_RETURN:
                game_started = True
                pygame.mixer.music.play(-1)
                
            # 게임 재시작
            elif gameover and event.key == pygame.K_RETURN:
                game_reset()
                
            # 플레이어 총알 발사 (일시정지 아닐 때만)
            elif game_started and not gameover and not player_dead and not is_paused:
                if event.key == pygame.K_SPACE:
                    firing = True
        # --- 키 뗌 ---
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                firing = False

    # -------------------------------------------------------------------------
    # (2) 게임 로직 (Game Logic) - 일시정지 아닐 때만 실행
    # -------------------------------------------------------------------------
    # 게임 로직 전체를 if not is_paused: 로 감쌈
    if game_started and not gameover and not is_paused:
        if not player_dead:
            game_timer += dt
            # --- 플레이어 이동 ---
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] and player_x > 0:
                player_x -= PLAYER_SPEED
            if keys[pygame.K_RIGHT] and player_x < WIDTH - PLAYER_SIZE:
                player_x += PLAYER_SPEED
            if keys[pygame.K_UP] and player_y > 0:
                player_y -= PLAYER_SPEED
            if keys[pygame.K_DOWN] and player_y < HEIGHT - PLAYER_SIZE:
                player_y += PLAYER_SPEED

            # --- 플레이어 총알 자동 발사 ---
            if firing:
                fire_timer -= dt
                if fire_timer <= 0 and len(bullets) < MAX_BULLETS:
                    bullets.append({"x": player_x + PLAYER_SIZE // 2 - 25,
                                    "y": player_y - 70, "w": 50, "h": 100})
                    shoot_sound.play()
                    fire_timer = fire_delay

            # --- 플레이어 총알 이동 ---
            for bullet in bullets[:]:
                bullet["y"] -= BULLET_SPEED
                if bullet["y"] < 0:
                    bullets.remove(bullet)

            # --- 적 이동 및 행동 ---
            for enemy in enemies[:]:
                enemy["y"] += enemy["speed"] * dt * 60
                enemy["shoot_timer"] += dt
                w, h = enemy_sizes[enemy["type"]]

                # 화면 밖으로 나간 적 재생성
                if enemy["y"] > HEIGHT:
                    enemy["y"] = -h
                    enemy["x"] = random.randint(0, WIDTH - w)
                    if enemy["type"] == "normal": enemy["hp"] = 1
                    elif enemy["type"] == "shooter": enemy["hp"] = 5
                    elif enemy["type"] == "strong": enemy["hp"] = 10
                
                # 'shooter' 타입 적 총알 발사 (플레이어 조준)
                if enemy["type"] == "shooter" and enemy["shoot_timer"] >= enemy["shoot_delay"]:
                    enemy["shoot_timer"] = 0
                    enemy["shoot_delay"] = random.uniform(1.0, 1.5)
                    bullet_x = enemy["x"] + w // 2 - 5
                    bullet_y = enemy["y"] + h
                    dx = (player_x + PLAYER_SIZE // 2) - bullet_x
                    dy = (player_y + PLAYER_SIZE // 2) - bullet_y
                    distance = (dx**2 + dy**2)**0.5
                    if distance > 0:
                        speed = 5
                        vx = dx / distance * speed
                        vy = dy / distance * speed
                        angle = math.degrees(math.atan2(-dy, dx))
                        enemy_bullets.append({"x": bullet_x, "y": bullet_y, "w":10, "h":20, 
                                              "speed_x": vx, "speed_y": vy, "angle": angle, "shooter": True})

                # 'strong' 타입 적 총알 발사 (3방향)
                if enemy["type"] == "strong" and enemy["shoot_timer"] >= enemy.get("shoot_delay", 2.5):
                    enemy["shoot_timer"] = 0
                    enemy["shoot_delay"] = random.uniform(1.4, 1.8)
                    bullet_x = enemy["x"] + w // 2 - 5
                    bullet_y = enemy["y"] + h
                    speeds_angles = [(0, 6, 0), (-3, 6, -15), (3, 6, 15)]
                    for sx, sy, angle in speeds_angles:
                        enemy_bullets.append({"x": bullet_x, "y": bullet_y, "w":10, "h":20, 
                                              "speed_x": sx, "speed_y": sy, "angle": angle, "shooter": False})

            # --- 적 총알 이동 ---
            for eb in enemy_bullets[:]:
                eb["x"] += eb["speed_x"] * dt * 60
                eb["y"] += eb["speed_y"] * dt * 60
                if eb["y"] > HEIGHT or eb["y"] < -eb["h"] or eb["x"] < -eb["w"] or eb["x"] > WIDTH:
                    enemy_bullets.remove(eb)

            # --- 충돌 처리 ---
            hitbox_size = 20
            hitbox_center_x = player_x + PLAYER_SIZE // 2 + 2
            hitbox_center_y = player_y + PLAYER_SIZE // 2 + 10
            player_hitbox_rect = pygame.Rect(0, 0, hitbox_size, hitbox_size)
            player_hitbox_rect.center = (hitbox_center_x, hitbox_center_y)

            # 플레이어 총알 vs 적
            for bullet in bullets[:]:
                hit_w, hit_h = PLAYER_BULLET_HITBOX_SIZE
                bullet_hitbox = pygame.Rect(bullet["x"] + (bullet["w"] - hit_w)//2, 
                                            bullet["y"] + (bullet["h"] - hit_h)//2, hit_w, hit_h)
                for enemy in enemies[:]:
                    img_w, img_h = enemy_sizes[enemy["type"]]
                    e_hit_w, e_hit_h = enemy_hitbox_sizes[enemy["type"]]
                    enemy_hitbox = pygame.Rect(enemy["x"] + (img_w - e_hit_w)//2, 
                                               enemy["y"] + (img_h - e_hit_h)//2, e_hit_w, e_hit_h)
                    
                    if bullet_hitbox.colliderect(enemy_hitbox):
                        if bullet in bullets: bullets.remove(bullet)
                        enemy["hp"] -= 1
                        if enemy["hp"] <= 0:
                            score += enemy["score"]
                            explosion_sound.play()
                            
                            # 적 타입별 폭발 크기 딕셔너리에서 폭발 크기 가져오기
                            explosion_size = enemy_explosion_sizes[enemy["type"]]
                            explosions.append({"x": enemy["x"] + img_w//2, "y": enemy["y"] + img_h//2, 
                                               "timer": 30, "max_timer": 30, "max_size": explosion_size})
                            
                            enemies.remove(enemy)
                            if enemy["type"] == "normal":
                                enemies.append({"type": "normal", "x":random.randint(0,WIDTH-enemy_sizes["normal"][0]),
                                                "y":-enemy_sizes["normal"][1],"hp":1,"speed":7,"score":1,"shoot_timer":0})
                            elif enemy["type"] == "shooter":
                                enemies.append({"type":"shooter","x":random.randint(0,WIDTH-enemy_sizes["shooter"][0]),
                                                "y":-enemy_sizes["shooter"][1],"hp":5,"speed":2,"score":5,
                                                "shoot_timer":0,"shoot_delay":random.uniform(2,3)})
                            elif enemy["type"] == "strong":
                                enemies.append({"type":"strong","x":random.randint(0,WIDTH-enemy_sizes["strong"][0]),
                                                "y":-enemy_sizes["strong"][1],"hp":10,"speed":1,"score":10,
                                                "shoot_timer":0, "shoot_delay": random.uniform(2.0, 3.5)})
                        break
            
            # 플레이어 vs 적
            if not player_dead and not player_invincible:
                for enemy in enemies:
                    img_w, img_h = enemy_sizes[enemy["type"]]
                    hit_w, hit_h = enemy_hitbox_sizes[enemy["type"]]
                    enemy_hitbox = pygame.Rect(
                        enemy["x"] + (img_w - hit_w)//2, 
                        enemy["y"] + (img_h - hit_h)//2, hit_w, hit_h
                    )
                    if player_hitbox_rect.colliderect(enemy_hitbox):
                        player_hp -= 1      #맞을 때 1씩만 깎음
                        player_invincible = True        #무적 상태 시작
                        invincible_timer = PLAYER_INVINCIBLE_DURATION      #프레임 수만큼 무적 유지
                        break   #한번 맞으면 루프 탈출
            
            # 플레이어 vs 적 총알
            if not player_dead and not player_invincible:
                bullet_hitbox_size = 20
                for eb in enemy_bullets[:]:
                    bullet_rect = pygame.Rect(0, 0, bullet_hitbox_size, bullet_hitbox_size)
                    bullet_rect.center = (eb["x"] + eb["w"]//2, eb["y"] + eb["h"]//2)
                    
                    if player_hitbox_rect.colliderect(bullet_rect):
                        player_hp -= 1      # HP 1 감소
                        player_invincible = True    # 무적 상태 시작
                        invincible_timer = PLAYER_INVINCIBLE_DURATION   # 무적 시간 설정
                        if eb in enemy_bullets:
                            enemy_bullets.remove(eb) # 충돌한 총알 제거
                        break 

            # 플레이어 사망 처리 로직
            if player_hp <= 0 and not player_dead:
                player_dead = True
                player_explosion_timer = 60 # GAME OVER 화면이 나오기 전까지의 시간
                explosion_sound.play()
                # 사망 시 폭발 효과를 한 번만 추가.
                explosions.append({
                    "x": hitbox_center_x, "y": hitbox_center_y,
                    "timer": 60, "max_timer": 60, "max_size": PLAYER_SIZE * 3
                })

            # --- 무적 시간 감소 ---
            if player_invincible:
                invincible_timer -= 1
                if invincible_timer <= 0:
                    player_invincible = False
            
        # --- 플레이어 사망 후 처리 ---
        if player_dead:
            player_explosion_timer -= 1
            if player_explosion_timer <= 0:
                gameover = True

    # -------------------------------------------------------------------------
    # (3) 화면 그리기 (Rendering)
    # -------------------------------------------------------------------------
    # --- 배경 그리기 ---
    if game_started:
        # 배경 스크롤은 일시정지 아닐 때만
        if not gameover and not is_paused:
            bg_y1 += BG_SPEED
            bg_y2 += BG_SPEED
            if bg_y1 >= HEIGHT: bg_y1 = -HEIGHT
            if bg_y2 >= HEIGHT: bg_y2 = -HEIGHT
        virtual_screen.blit(background, (0, bg_y1))
        virtual_screen.blit(background, (0, bg_y2))
    else:
        virtual_screen.fill((100, 100, 100))

    # --- 게임 시작 화면 ---
    if not game_started:
        draw_neon_glow_text(virtual_screen, "Siuuuting!", font_title,
                          text_color=(0, 255, 255), glow_color=(0, 100, 255),
                          pos=(WIDTH//2 - 130, HEIGHT//2 - 100), glow_radius=8)
        draw_neon_glow_text(virtual_screen, "by Choi Jaemin", font_ui,
                            text_color=(200, 200, 200), glow_color=(100, 100, 255),
                            pos=(WIDTH//2 - 90, HEIGHT//2 - 30), glow_radius=4)
        draw_neon_glow_text(virtual_screen, "Press ENTER to start", font_start,
                          text_color=(255, 255, 0), glow_color=(255, 150, 0),
                          pos=(WIDTH//2 - 170, HEIGHT//2 + 80), glow_radius=6)
    
    # --- 인게임 화면 ---
    else:
        # 모든 게임 오브젝트 그리기
        for enemy in enemies:
            img = enemy_images.get(enemy["type"], enemy_images["normal"])
            virtual_screen.blit(img, (enemy["x"], enemy["y"]))
            """
            # === 디버그용 히트박스 (적) ===
            e_hit_w, e_hit_h = enemy_hitbox_sizes[enemy["type"]]
            img_w, img_h = enemy_sizes[enemy["type"]]
            enemy_hitbox = pygame.Rect(
                enemy["x"] + (img_w - e_hit_w)//2,
                enemy["y"] + (img_h - e_hit_h)//2,
                e_hit_w, e_hit_h
            )
            pygame.draw.rect(virtual_screen, (255, 0, 0), enemy_hitbox, 2)
            """
        for eb in enemy_bullets:
            bullet_rect = pygame.Rect(0, 0, eb["w"], eb["h"])
            bullet_rect.center = (eb["x"] + eb["w"] // 2, eb["y"] + eb["h"] // 2)
            angle = eb.get("angle", 0)
            rotated_img = pygame.transform.rotate(enemy_bullet_img, angle + (90 if eb.get("shooter") else 0))
            rect = rotated_img.get_rect(center=bullet_rect.center)
            virtual_screen.blit(rotated_img, rect.topleft)
            """
            # === 디버그용 히트박스 (적 총알) ===
            bullet_hitbox_size = 20
            debug_rect = pygame.Rect(0, 0, bullet_hitbox_size, bullet_hitbox_size)
            debug_rect.center = (eb["x"] + eb["w"]//2, eb["y"] + eb["h"]//2)
            pygame.draw.rect(virtual_screen, (0, 255, 255), debug_rect, 2)
            """
        for bullet in bullets:
            virtual_screen.blit(bullet_image, (bullet["x"], bullet["y"]))
            """
            # === 디버그용 히트박스 (플레이어 총알) ===
            hit_w, hit_h = PLAYER_BULLET_HITBOX_SIZE
            bullet_hitbox = pygame.Rect(
                bullet["x"] + (bullet["w"] - hit_w)//2,
                bullet["y"] + (bullet["h"] - hit_h)//2,
                hit_w, hit_h
            )
            pygame.draw.rect(virtual_screen, (0, 255, 0), bullet_hitbox, 2)
            """
        if not player_dead:
            if player_invincible and invincible_timer % 6 < 3:
                pass # 깜빡이는 효과를 위해 그리지 않음
            else:
                virtual_screen.blit(player_image, (player_x, player_y))
            """
            # === 디버그용 히트박스 (플레이어) ===
            hitbox_size = 20
            hitbox_center_x = player_x + PLAYER_SIZE // 2 + 2
            hitbox_center_y = player_y + PLAYER_SIZE // 2 + 10
            player_hitbox_rect = pygame.Rect(0, 0, hitbox_size, hitbox_size)
            player_hitbox_rect.center = (hitbox_center_x, hitbox_center_y)
            pygame.draw.rect(virtual_screen, (255, 255, 0), player_hitbox_rect, 2)
            """
        for exp in explosions[:]:
            progress = (exp['max_timer'] - exp['timer']) / exp['max_timer']
            current_size = int(exp['max_size'] * progress)
            if current_size <= 0: current_size = 1
            alpha = 255 * (1 - progress)
            scaled_exp_original = pygame.transform.scale(explosion_image, (current_size, current_size))
            scaled_exp = scaled_exp_original.copy()
            scaled_exp.set_alpha(alpha)
            virtual_screen.blit(scaled_exp, (exp["x"] - current_size // 2, exp["y"] - current_size // 2))
            
            # 폭발 애니메이션 타이머는 일시정지 아닐 때만 감소
            if not is_paused:
                exp["timer"] -= 1
            if exp["timer"] <= 0:
                explosions.remove(exp)

        # UI 그리기
        score_text = font_ui.render(f"Score: {score}", True, (255, 255, 255))
        virtual_screen.blit(score_text, (10, 10))
        hp_text = font_ui.render(f"HP: {player_hp}", True, (255, 0, 0))
        virtual_screen.blit(hp_text, (10, 50))
        timer_text = font_ui.render(f"Time: {game_timer:.1f}", True, (255, 255, 255))
        timer_rect = timer_text.get_rect(topright=(WIDTH - 10, 10))
        virtual_screen.blit(timer_text, timer_rect)

    # --- 게임오버 화면 ---
    if gameover:
        draw_neon_glow_text(virtual_screen, "GAME OVER", font_gameover_big, 
                          (255, 0, 0), (150, 0, 0), 
                          (WIDTH//2 - 150, HEIGHT//2 - 90), glow_radius=6)
        draw_neon_glow_text(virtual_screen, "Press ENTER to restart", font_gameover_small, 
                          (255, 255, 0), (150, 150, 0), 
                          (WIDTH//2 - 150, HEIGHT//2 + 50), glow_radius=4)
    
    # 일시정지 화면 그리기
    if is_paused:
        draw_neon_glow_text(virtual_screen, "PAUSED", font_pause, 
                          (255, 255, 255), (100, 100, 255), 
                          (WIDTH//2 - 80, HEIGHT//2 - 30), glow_radius=5)

    # -------------------------------------------------------------------------
    # virtual_screen을 실제 screen에 비율 맞춰 그리기
    # -------------------------------------------------------------------------
    screen.fill(BLACK)
    
    display_info = pygame.display.Info()
    display_width = display_info.current_w
    display_height = display_info.current_h
    
    scale_x = display_width / WIDTH
    scale_y = display_height / HEIGHT
    scale = min(scale_x, scale_y)
    
    scaled_width = int(WIDTH * scale)
    scaled_height = int(HEIGHT * scale)
    
    scaled_surface = pygame.transform.scale(virtual_screen, (scaled_width, scaled_height))
    
    blit_x = (screen.get_width() - scaled_width) // 2
    blit_y = (screen.get_height() - scaled_height) // 2
    
    screen.blit(scaled_surface, (blit_x, blit_y))

    # --- 최종 화면 업데이트 ---
    pygame.display.flip()

# =============================================================================
# 7. 게임 종료 (Quit Game)
# =============================================================================
pygame.quit()
