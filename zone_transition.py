import pygame

class ZoneTransition:
    def __init__(self, viewport_width, viewport_height, font, subtitle_font):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.font = font
        self.subtitle_font = subtitle_font

        self.alpha = 0
        self.direction = 0  # 1 = fade out, -1 = fade in, 0 = idle
        self.time = 0
        self.duration = 0.5
        self.pending_zone_change = None

        self.zone_title_timer = 0
        self.zone_title_alpha = 0
        self.current_zone_name = ""

        self.boss_intro_data = None
        self.boss_intro_alpha = 0
        self.boss_intro_timer = 0

    def reset_title(self):
        self.zone_title_alpha = 0
        self.zone_title_timer = 0
        self.current_zone_name = ""

    def begin(self, next_zone_id, direction, zone_name):
        self.pending_zone_change = (next_zone_id, direction)
        self.reset_title()
        self.current_zone_name = zone_name
        self.direction = 1
        self.alpha = 0
        self.time = 0
    
    def begin_boss_intro(self, name, subtitle):
        self.boss_intro_data = (name, subtitle)
        self.boss_intro_alpha = 0
        self.boss_intro_timer = 3.0  # how long to show

    def update(self, dt):
        if self.direction == 0:
            if self.zone_title_timer > 0:
                self.zone_title_timer -= dt
                fade_out_progress = max(0.0, self.zone_title_timer / 2.0)
                self.zone_title_alpha = int(255 * fade_out_progress)
            return None  # no transition happening

        self.time += dt
        progress = self.time / self.duration

        if self.direction == 1:  # fade out
            self.alpha = min(255, int(progress * 255))
            if progress >= 1.0:
                self.direction = -1
                self.time = 0
                return self.pending_zone_change  # signal to switch zone

        elif self.direction == -1:  # fade in
            self.alpha = max(0, 255 - int(progress * 255))
            self.zone_title_alpha = int(min(255, progress * 255))
            if progress >= 1.0:
                self.direction = 0
                self.zone_title_timer = 2.5

        if self.boss_intro_timer > 0:
            self.boss_intro_timer -= dt
            progress = 1.0 - abs(self.boss_intro_timer - 1.5) / 1.5  # fade in then out
            self.boss_intro_alpha = int(255 * progress)
        else:
            self.boss_intro_data = None

        return None

    def draw(self, screen):
        # Fade rectangle
        if self.alpha > 0:
            fade_surface = pygame.Surface((self.viewport_width, self.viewport_height), pygame.SRCALPHA)
            fade_surface.fill((0, 0, 0, self.alpha))
            screen.blit(fade_surface, (0, 0))

        # Zone title
        if self.zone_title_alpha > 0 and self.current_zone_name:
            title_surf = self.font.render(self.current_zone_name, True, (255, 255, 255))
            title_surf.set_alpha(self.zone_title_alpha)
            title_rect = title_surf.get_rect(center=(self.viewport_width // 2, self.viewport_height // 4))
            screen.blit(title_surf, title_rect)

        # Boss intro
        if self.boss_intro_data and self.boss_intro_alpha > 0:
            name, subtitle = self.boss_intro_data

            # Name
            name_surf = self.font.render(name, True, (255, 255, 255))
            name_surf.set_alpha(self.boss_intro_alpha)
            name_rect = name_surf.get_rect(center=(self.viewport_width // 2, self.viewport_height // 3))
            screen.blit(name_surf, name_rect)

            # Subtitle
            subtitle_surf = self.subtitle_font.render(subtitle, True, (200, 200, 200))
            subtitle_surf.set_alpha(self.boss_intro_alpha)
            subtitle_rect = subtitle_surf.get_rect(center=(self.viewport_width // 2, self.viewport_height // 3 + self.font.get_height()))
            screen.blit(subtitle_surf, subtitle_rect)

    def is_active(self):
        return self.direction != 0
