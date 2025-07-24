import pygame
import random
import math
import os
import time

# --- Config ---
WIDTH, HEIGHT = 675, 675
BALL_COUNT = 2
BALL_RADIUS = 48  # 30 * 1.6
BALL_MIN_SPEED = 5  # 7 * 0.75
BALL_MAX_SPEED = 14  # 18 * 0.75

# --- Ball Class ---
class Ball:
    def __init__(self, x, y, vx, vy, radius, color, health=20, type=None):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.color = color
        self.health = health
        self.type = type  # e.g. 'blaze', 'zombie', etc.
        self.face_img = None
        self.poisoned = False
        self.poison_time = 0
        self.last_poison_tick = 0
        self.on_fire = False
        self.fire_time = 0
        self.last_fire_tick = 0
        self.last_blazeball_time = 0  # For Blaze only
        self.visible = True  # For Herobrine
        self.visible_until = 0  # For Herobrine

    def move(self):
        self.x += self.vx
        self.y += self.vy

        # Bounce off walls
        if self.x - self.radius < 0:
            self.x = self.radius
            self.vx *= -1
        if self.x + self.radius > WIDTH:
            self.x = WIDTH - self.radius
            self.vx *= -1
        if self.y - self.radius < 0:
            self.y = self.radius
            self.vy *= -1
        if self.y + self.radius > HEIGHT:
            self.y = HEIGHT - self.radius
            self.vy *= -1

        # Herobrine: if not visible, remove all effects
        if self.type == 'herobrine' and not self.visible:
            self.poisoned = False
            self.on_fire = False

    def update_poison(self, current_time):
        if self.poisoned:
            # Poison ticks every 0.5 second
            if current_time - self.last_poison_tick >= 1:
                self.health -= 1
                self.last_poison_tick = current_time
                self.poison_time -= 1
                if self.poison_time <= 0:
                    self.poisoned = False

    def update_fire(self, current_time):
        if self.on_fire:
            if current_time - self.last_fire_tick >= 1:
                self.health -= 1
                self.last_fire_tick = current_time
                self.fire_time -= 1
                if self.fire_time <= 0:
                    self.on_fire = False

    def update_visibility(self, current_time):
        if self.type == 'herobrine' and not self.visible and current_time >= self.visible_until:
            self.visible = False
        if self.type == 'herobrine' and self.visible and current_time >= self.visible_until:
            self.visible = False

    def draw(self, screen, font):
        # Herobrine: 80% transparent when invisible
        if self.type == 'herobrine' and not self.visible:
            # Draw transparent ball and face
            surf = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, self.color + (51,), (self.radius, self.radius), self.radius)
            if self.face_img:
                img = pygame.transform.smoothscale(self.face_img, (self.radius*2, self.radius*2))
                surf.blit(img, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(surf, (int(self.x-self.radius), int(self.y-self.radius)))
            return
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        # Draw fire outline if on fire
        if self.on_fire:
            pygame.draw.circle(screen, (255,140,0), (int(self.x), int(self.y)), self.radius+4, 4)
        # Draw poison outline if poisoned
        if self.poisoned:
            pygame.draw.circle(screen, (0,255,0), (int(self.x), int(self.y)), self.radius+8, 4)
        # Draw health above the ball
        health_surf = font.render(str(self.health), True, (255,255,255))
        rect = health_surf.get_rect(center=(int(self.x), int(self.y - self.radius - 15)))
        screen.blit(health_surf, rect)
        # Draw fire/poison status text
        if self.on_fire:
            fire_surf = font.render("Fire", True, (255,140,0))
            fire_rect = fire_surf.get_rect(center=(int(self.x), int(self.y + self.radius + 15)))
            screen.blit(fire_surf, fire_rect)
        if self.poisoned:
            poison_surf = font.render("Poison", True, (0,255,0))
            poison_rect = poison_surf.get_rect(center=(int(self.x), int(self.y + self.radius + 35)))
            screen.blit(poison_surf, poison_rect)
        # Draw face image if available
        if self.face_img:
            img_rect = self.face_img.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(self.face_img, img_rect)

class Blazeball:
    def __init__(self, x, y, vx, vy, owner_idx):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = int(16 * 1.3)  # 30% bigger
        self.owner_idx = owner_idx  # index of the ball that shot it
        self.active = True
        self.img = pygame.image.load(os.path.join('images', 'blazeball.png')).convert_alpha()
        self.img = pygame.transform.smoothscale(self.img, (self.radius*2, self.radius*2))

    def move(self):
        self.x += self.vx
        self.y += self.vy
        # Deactivate if out of bounds
        if not (0 <= self.x <= WIDTH and 0 <= self.y <= HEIGHT):
            self.active = False

    def draw(self, screen):
        if self.active:
            rect = self.img.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(self.img, rect)

class Explosion:
    def __init__(self, x, y, start_time):
        self.x = x
        self.y = y
        self.start_time = start_time
        self.duration = 0.5  # seconds
        self.max_radius = 120
        self.active = True
    def draw(self, screen, current_time):
        elapsed = current_time - self.start_time
        if elapsed > self.duration:
            self.active = False
            return
        progress = elapsed / self.duration
        radius = int(self.max_radius * progress)
        alpha = int(255 * (1 - progress))
        if radius > 0:
            surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255,255,255,alpha), (radius, radius), radius)
            pygame.draw.circle(surf, (255,255,200,alpha), (radius, radius), int(radius*0.7))
            screen.blit(surf, (self.x-radius, self.y-radius))

class HitEffect:
    def __init__(self, x, y, start_time):
        self.x = x
        self.y = y
        self.start_time = start_time
        self.duration = 0.15  # seconds
        self.max_radius = 32
        self.active = True
    def draw(self, screen, current_time):
        elapsed = current_time - self.start_time
        if elapsed > self.duration:
            self.active = False
            return
        progress = elapsed / self.duration
        radius = int(self.max_radius * progress)
        alpha = int(180 * (1 - progress))
        if radius > 0:
            surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255,255,255,alpha), (radius, radius), radius)
            screen.blit(surf, (self.x-radius, self.y-radius))

def random_color():
    return (random.randint(50,255), random.randint(50,255), random.randint(50,255))

def balls_collide(ball1, ball2):
    dx = ball1.x - ball2.x
    dy = ball1.y - ball2.y
    distance = math.hypot(dx, dy)
    return distance < ball1.radius + ball2.radius

def resolve_collision(ball1, ball2):
    # Calculate the normal vector
    dx = ball1.x - ball2.x
    dy = ball1.y - ball2.y
    distance = math.hypot(dx, dy)
    if distance == 0:
        # Prevent division by zero
        distance = 0.1
    nx = dx / distance
    ny = dy / distance

    # Relative velocity
    dvx = ball1.vx - ball2.vx
    dvy = ball1.vy - ball2.vy
    # Velocity along the normal
    vn = dvx * nx + dvy * ny
    if vn > 0:
        return  # Balls are moving away

    # Simple elastic collision (equal mass)
    ball1.vx -= vn * nx
    ball1.vy -= vn * ny
    ball2.vx += vn * nx
    ball2.vy += vn * ny

    # Separate balls so they don't stick
    overlap = (ball1.radius + ball2.radius) - distance
    ball1.x += nx * (overlap / 2)
    ball1.y += ny * (overlap / 2)
    ball2.x -= nx * (overlap / 2)
    ball2.y -= ny * (overlap / 2)

def get_image_files():
    # Only allow common image extensions, and exclude blazeball.png
    allowed_exts = {'.jpg', '.jpeg', '.png'}
    files = []
    for f in os.listdir('images'):
        ext = os.path.splitext(f)[1].lower()
        if ext in allowed_exts and f != 'blazeball.png':
            files.append(f)
    return files

def main():
    def create_balls(selected_imgs):
        balls = []
        types = [os.path.splitext(os.path.basename(f))[0] for f in selected_imgs]
        colors = [(100, 200, 100), (60, 120, 60)]  # Placeholder colors
        face_imgs = []
        for img_file in selected_imgs:
            img = pygame.image.load(os.path.join('images', img_file)).convert_alpha()
            img = pygame.transform.smoothscale(img, (BALL_RADIUS * 2, BALL_RADIUS * 2))
            face_imgs.append(img)
        for i in range(BALL_COUNT):
            while True:
                x = random.randint(BALL_RADIUS, WIDTH - BALL_RADIUS)
                y = random.randint(BALL_RADIUS, HEIGHT - BALL_RADIUS)
                vx = random.choice([-1, 1]) * random.uniform(BALL_MIN_SPEED, BALL_MAX_SPEED)
                vy = random.choice([-1, 1]) * random.uniform(BALL_MIN_SPEED, BALL_MAX_SPEED)
                ball_type = types[i % 2]
                color = colors[i % 2]
                face_img = face_imgs[i % 2]
                new_ball = Ball(x, y, vx, vy, BALL_RADIUS, color, health=20, type=ball_type)
                new_ball.face_img = face_img
                if all(not balls_collide(new_ball, b) for b in balls):
                    balls.append(new_ball)
                    break
        return balls

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Bouncing Balls Game")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 32)
    big_font = pygame.font.SysFont(None, 96)

    # --- Start Screen ---
    image_files = get_image_files()
    selected = []
    thumb_size = 100
    margin = 30
    running = True
    while running and len(selected) < 2:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                for idx, img_file in enumerate(image_files):
                    col = idx % 4
                    row = idx // 4
                    x = margin + col * (thumb_size + margin)
                    y = margin + row * (thumb_size + margin)
                    rect = pygame.Rect(x, y, thumb_size, thumb_size)
                    if rect.collidepoint(mx, my):
                        if img_file not in selected:
                            selected.append(img_file)
        screen.fill((30, 30, 30))
        title = font.render("Pick 2 Fighters", True, (255,255,255))
        screen.blit(title, (margin, 5))
        for idx, img_file in enumerate(image_files):
            col = idx % 4
            row = idx // 4
            x = margin + col * (thumb_size + margin)
            y = margin + row * (thumb_size + margin)
            img = pygame.image.load(os.path.join('images', img_file)).convert_alpha()
            img = pygame.transform.smoothscale(img, (thumb_size, thumb_size))
            rect = pygame.Rect(x, y, thumb_size, thumb_size)
            screen.blit(img, rect)
            if img_file in selected:
                pygame.draw.rect(screen, (0,255,0), rect, 4)
        pygame.display.flip()
        clock.tick(30)
    if len(selected) < 2:
        return

    while True:
        balls = create_balls(selected)
        running = True
        winner = None
        blazeballs = []
        explosions = []
        hit_effects = []
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            # Move balls
            for ball in balls:
                ball.move()

            # Blaze: shoot blazeball every second
            current_time = pygame.time.get_ticks() / 1000.0
            for idx, ball in enumerate(balls):
                if ball.type == 'blaze':
                    if current_time - ball.last_blazeball_time >= 1:
                        # Shoot toward the other ball
                        if len(balls) == 2:
                            enemy_idx = 1 - idx
                            enemy = balls[enemy_idx]
                            dx = enemy.x - ball.x
                            dy = enemy.y - ball.y
                            dist = math.hypot(dx, dy)
                            if dist == 0:
                                dist = 1
                            speed = 12 * 1.5  # 1.5x as fast
                            vx = speed * dx / dist
                            vy = speed * dy / dist
                        else:
                            angle = random.uniform(0, 2*math.pi)
                            speed = 12 * 1.5
                            vx = speed * math.cos(angle)
                            vy = speed * math.sin(angle)
                        blazeballs.append(Blazeball(ball.x, ball.y, vx, vy, idx))
                        ball.last_blazeball_time = current_time

            # Move blazeballs
            for b in blazeballs:
                b.move()
            blazeballs = [b for b in blazeballs if b.active]

            # Handle blazeball collisions
            for b in blazeballs:
                for idx, ball in enumerate(balls):
                    if idx != b.owner_idx and b.active:
                        dx = ball.x - b.x
                        dy = ball.y - b.y
                        dist = math.hypot(dx, dy)
                        if dist < ball.radius + b.radius:
                            ball.health -= 1
                            # Set on fire for 5s, reset timer if already on fire
                            ball.on_fire = True
                            ball.fire_time = 5
                            ball.last_fire_tick = current_time
                            b.active = False

            # Handle collisions and effects
            collided_pairs = set()
            for i in range(len(balls)):
                for j in range(i + 1, len(balls)):
                    if balls_collide(balls[i], balls[j]):
                        pair = tuple(sorted((i, j)))
                        if pair not in collided_pairs:
                            resolve_collision(balls[i], balls[j])
                            # Add a small hit effect at the collision point
                            hx, hy = (balls[i].x + balls[j].x) / 2, (balls[i].y + balls[j].y) / 2
                            hit_effects.append(HitEffect(hx, hy, current_time))
                            # Herobrine special logic
                            herobrine_handled = False
                            for idx, (a, b) in enumerate([(i, j), (j, i)]):
                                if balls[a].type == 'herobrine':
                                    # Become visible for 1 second
                                    balls[a].visible = True
                                    balls[a].visible_until = current_time + 1
                                    # Determine hit direction
                                    dy = balls[b].y - balls[a].y
                                    dx = balls[b].x - balls[a].x
                                    if abs(dy) > abs(dx):
                                        # Top or bottom hit
                                        balls[b].health -= 4
                                        herobrine_handled = True
                                    # If side hit, do 0 damage and do not set herobrine_handled
                            if not herobrine_handled:
                                # Creeper explosion effect
                                if balls[i].type == 'creeper' or balls[j].type == 'creeper':
                                    # Find which is creeper and which is enemy
                                    if balls[i].type == 'creeper':
                                        balls[j].health -= 4
                                        balls[i].health -= 2
                                        ex, ey = (balls[i].x + balls[j].x) / 2, (balls[i].y + balls[j].y) / 2
                                        # Accelerate both away from explosion
                                        for b in [balls[i], balls[j]]:
                                            dx = b.x - ex
                                            dy = b.y - ey
                                            dist = math.hypot(dx, dy)
                                            if dist == 0:
                                                dx, dy = random.uniform(-1,1), random.uniform(-1,1)
                                                dist = math.hypot(dx, dy)
                                            push = 4  # reduced explosion force
                                            b.vx += push * dx / dist
                                            b.vy += push * dy / dist
                                    else:
                                        balls[i].health -= 4
                                        balls[j].health -= 2
                                        ex, ey = (balls[i].x + balls[j].x) / 2, (balls[i].y + balls[j].y) / 2
                                        # Accelerate both away from explosion
                                        for b in [balls[i], balls[j]]:
                                            dx = b.x - ex
                                            dy = b.y - ey
                                            dist = math.hypot(dx, dy)
                                            if dist == 0:
                                                dx, dy = random.uniform(-1,1), random.uniform(-1,1)
                                                dist = math.hypot(dx, dy)
                                            push = 4  # reduced explosion force
                                            b.vx += push * dx / dist
                                            b.vy += push * dy / dist
                                    explosions.append(Explosion(ex, ey, current_time))
                                else:
                                    balls[i].health -= 1
                                    balls[j].health -= 1
                            collided_pairs.add(pair)
            # Update poison/fire effects
            for ball in balls:
                ball.update_poison(current_time)
                ball.update_fire(current_time)
                ball.update_visibility(current_time)
            # Remove dead balls
            balls = [ball for ball in balls if ball.health > 0]
            # Remove finished explosions
            explosions = [e for e in explosions if e.active]
            hit_effects = [e for e in hit_effects if e.active]

            # Check for winner
            if len(balls) == 1:
                winner_ball = balls[0]
                # Animate winner growing to fill the screen
                grow_radius = winner_ball.radius
                grow_center = (winner_ball.x, winner_ball.y)
                grow_img = winner_ball.face_img
                grow_color = winner_ball.color
                grow_type = winner_ball.type
                grow_health = winner_ball.health
                for frame in range(60):
                    screen.fill((30, 30, 30))
                    # Grow the ball
                    r = int(grow_radius + (max(WIDTH, HEIGHT) // 2 - grow_radius) * (frame / 59))
                    pygame.draw.circle(screen, grow_color, (int(WIDTH//2), int(HEIGHT//2)), r)
                    if grow_img:
                        img = pygame.transform.smoothscale(grow_img, (r*2, r*2))
                        img_rect = img.get_rect(center=(WIDTH//2, HEIGHT//2))
                        screen.blit(img, img_rect)
                    # Draw health
                    health_surf = font.render(str(grow_health), True, (255,255,255))
                    rect = health_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - r - 15))
                    screen.blit(health_surf, rect)
                    # Draw winner text
                    winner_text = f"{grow_type.capitalize()} Wins!"
                    text_surf = big_font.render(winner_text, True, (255,255,0))
                    text_rect = text_surf.get_rect(center=(WIDTH//2, HEIGHT//2))
                    screen.blit(text_surf, text_rect)
                    pygame.display.flip()
                    clock.tick(60)
                # Hold the winner face for about 3 seconds
                hold_frames = 3 * 60
                for _ in range(hold_frames):
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            return
                    screen.fill((30, 30, 30))
                    r = max(WIDTH, HEIGHT) // 2
                    pygame.draw.circle(screen, grow_color, (int(WIDTH//2), int(HEIGHT//2)), r)
                    if grow_img:
                        img = pygame.transform.smoothscale(grow_img, (r*2, r*2))
                        img_rect = img.get_rect(center=(WIDTH//2, HEIGHT//2))
                        screen.blit(img, img_rect)
                    health_surf = font.render(str(grow_health), True, (255,255,255))
                    rect = health_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - r - 15))
                    screen.blit(health_surf, rect)
                    winner_text = f"{grow_type.capitalize()} Wins!"
                    text_surf = big_font.render(winner_text, True, (255,255,0))
                    text_rect = text_surf.get_rect(center=(WIDTH//2, HEIGHT//2))
                    screen.blit(text_surf, text_rect)
                    pygame.display.flip()
                    clock.tick(60)
                # Immediately return to start screen after animation
                main()
                return
            elif len(balls) == 0:
                # No draw screen, just return to start
                break

            # Draw
            screen.fill((30, 30, 30))
            for ball in balls:
                ball.draw(screen, font)
            for b in blazeballs:
                b.draw(screen)
            for e in explosions:
                e.draw(screen, current_time)
            for h in hit_effects:
                h.draw(screen, current_time)
            pygame.display.flip()
            clock.tick(60)

        # Winner screen with restart button
        if winner:
            winner_text = f"{winner.capitalize()} Wins!"
        else:
            winner_text = "Draw!"
        button_font = pygame.font.SysFont(None, 48)
        button_text = button_font.render("Restart", True, (0,0,0))
        button_w, button_h = 220, 80
        button_x = WIDTH//2 - button_w//2
        button_y = HEIGHT//2 + 100
        button_rect = pygame.Rect(button_x, button_y, button_w, button_h)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if button_rect.collidepoint(event.pos):
                        # Restart the fight (go back to start screen)
                        return main()
            else:
                screen.fill((30, 30, 30))
                text_surf = big_font.render(winner_text, True, (255,255,0))
                text_rect = text_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
                screen.blit(text_surf, text_rect)
                # Draw button
                pygame.draw.rect(screen, (200,200,200), button_rect)
                pygame.draw.rect(screen, (0,0,0), button_rect, 4)
                btn_text_rect = button_text.get_rect(center=button_rect.center)
                screen.blit(button_text, btn_text_rect)
                pygame.display.flip()
                clock.tick(30)
                continue
            break

if __name__ == "__main__":
    main() 