import pygame
import sys
import io
import contextlib
import math
import ast
import threading
import array
import random

#========= ΕΝΟΤΗΤΕΣ ==========
# WINDOW            [line 34]
# COLORS            [line 43]
# STATE             [line 76]
# LAYOUT            [line 120]
# SOUNDS            [line 148]
# PARTICLES         [line 201]
# LAYOUT HELPERS    [line 254]
# SANDBOX           [line 354]
# VALIDATION        [line 373]
# LEVELS            [line 550]
# SCORING           [line 640]
# EDITOR            [line 658]
# ANIMATIONS        [line 796]
# EXECUTION         [line 853]
# DRAW - UI         [line 959]
# RUN CODE          [line 1410]
# MAIN LOOP         [line 1461]

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

# =========================
# WINDOW
# =========================


WIDTH, HEIGHT = 900, 680
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Reddy's Quest: Python's Tower")

# =========================
# COLORS
# =========================

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 50, 50)
BLUE = (50, 100, 220)
GREEN = (50, 170, 90)
YELLOW = (255, 220, 0)
GOLD = (255, 200, 50)
PINK = (255, 200, 200)
LIGHT_BLUE = (180, 220, 255)
DARK_GREEN = (30, 100, 30)
GRAY = (240, 240, 240)
DARK_GRAY = (100, 100, 100)
OUTPUT_BG = (30, 30, 40)
OUTPUT_TEXT = (200, 255, 200)
EDITOR_BG = (255, 255, 255)
EXPECTED_BG = (255, 250, 220)
QUEST_GOLD = (255, 235, 150)
MAP_DONE = (100, 200, 120)
MAP_LOCKED = (180, 180, 190)

font = pygame.font.SysFont("arial", 22)
code_font = pygame.font.SysFont("consolas", 18)
small_font = pygame.font.SysFont("arial", 16)
big_font = pygame.font.SysFont("arial", 38, bold=True)
title_font = pygame.font.SysFont("arial", 56, bold=True)
subtitle_font = pygame.font.SysFont("arial", 24)
quest_font = pygame.font.SysFont("arial", 20, bold=True)
clock = pygame.time.Clock()

# =========================
# STATE
# =========================

state = "intro"
phase = "dialogue"
level_index = 0

message = ""
message_time = 0

user_lines = [""]
cursor_line = 0
cursor_col = 0
editor_scroll = 0

output_text = ""
output_feedback = ""
output_scroll = 0

wrong_attempts = 0
hint_unlocked = False
hint_visible = False
hint_used_this_level = False
lamp_pulse = 0
lamp_hover = False

success = False
success_time = 0
success_stars = 0

level_stars = [0] * 8

cursor_visible = True
cursor_blink_time = 0

# Animations
shake_time = 0
shake_x = 0
reddy_bounce = 0.0
flash_color = None
flash_time = 0
particles = []

# =========================
# LAYOUT
# =========================
PANEL_GAP = 20
LABEL_ABOVE = 18
HINT_GAP = 28
HEADER_HEIGHT = 88
BOTTOM_MARGIN = 44

EDITOR_LINE_HEIGHT = 22
EDITOR_VISIBLE_LINES = 5
EDITOR_H = EDITOR_VISIBLE_LINES * EDITOR_LINE_HEIGHT + 22

OUTPUT_LINE_HEIGHT = 20
OUTPUT_PADDING = 12
HINT_LINE_HEIGHT = 18

QUESTION_RECT = pygame.Rect(200, HEADER_HEIGHT + 8, 680, 64)
EXPECTED_RECT = pygame.Rect(200, 0, 520, 42)
EDITOR_Y = 0
EDITOR_RECT = pygame.Rect(200, 0, 520, EDITOR_H)
OUTPUT_RECT = pygame.Rect(200, 0, 520, 52)
RUN_BTN = pygame.Rect(735, EDITOR_Y, 100, 40)
LAMP_RECT = pygame.Rect(90, EDITOR_Y + 12, 60, 60)
MESSAGE_Y = 0
FEEDBACK_Y = 0


# =========================
# SOUNDS (generated)
# =========================

def generate_tone(freq, duration_ms=90, volume=0.25):
#    Δημιουργεί έναν απλό ήχο συγκεκριμένης συχνότητας.
#    Επιστρέφει: pygame.mixer.Sound: Το αντικείμενο ήχου
    sample_rate = 44100
    n_samples = int(sample_rate * duration_ms / 1000)
    buf = array.array("h")
    amp = int(32767 * volume)
    for i in range(n_samples):
        t = i / sample_rate
        env = 1.0 - (i / max(1, n_samples))
        val = int(amp * env * math.sin(2 * math.pi * freq * t))
        buf.append(val)
    return pygame.mixer.Sound(buffer=buf)


def generate_chord(freqs, duration_ms=140):
#   Δημιουργεί συγχορδία από πολλαπλές συχνότητες.
#   Επιστρέφει: pygame.mixer.Sound: Το αντικείμενο ήχου
    sample_rate = 44100
    n_samples = int(sample_rate * duration_ms / 1000)
    buf = array.array("h")
    for i in range(n_samples):
        t = i / sample_rate
        env = 1.0 - (i / max(1, n_samples))
        val = sum(math.sin(2 * math.pi * f * t) for f in freqs)
        val = int(32767 * 0.15 * env * val / len(freqs))
        buf.append(val)
    return pygame.mixer.Sound(buffer=buf)


SOUNDS = {}
try:
    SOUNDS = {
        "run": generate_tone(520, 60, 0.15),
        "error": generate_tone(180, 180, 0.3),
        "success": generate_chord([523, 659, 784]),
        "star": generate_tone(880, 70, 0.2),
    }
except pygame.error:
    SOUNDS = {}


def play_sound(name):
#   Αναπαράγει ήχο από το λεξικό SOUNDS.
    snd = SOUNDS.get(name)
    if snd:
        snd.play()


# =========================
# PARTICLES
# =========================

def spawn_particles(x, y, color, count=18):
#   Δημιουργεί σωματίδια στο σημείο (x, y).
#   Κάθε particle έχει:
#   - Τυχαία αρχική ταχύτητα (vx, vy)
#   - Τυχαία διάρκεια ζωής (life)
#   - Τυχαίο μέγεθος (size)
#    Χρησιμοποιείται για celebration effects κατά την επιτυχία.
    for _ in range(count):
        particles.append({
            "x": x,
            "y": y,
            "vx": random.uniform(-3.5, 3.5),
            "vy": random.uniform(-5.5, -1.0),
            "life": random.randint(25, 55),
            "color": color,
            "size": random.randint(3, 7),
        })


def update_particles():
#   Ενημερώνει θέση και κατάσταση όλων των σωματιδίων.
#   Κάθε frame:
#   - Ενημερώνει τη θέση βάσει ταχύτητας
#   - Εφαρμόζει βαρύτητα
#   - Μειώνει τη διάρκεια ζωής
#   - Διαγράφει τα νεκρά particles
#   Καλείται σε κάθε frame του main loop.
    global particles
    alive = []
    for p in particles:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.18
        p["life"] -= 1
        if p["life"] > 0:
            alive.append(p)
    particles = alive


def draw_particles(surface):
#   Σχεδιάζει όλα τα ενεργά σωματίδια στην οθόνη.
    for p in particles:
        alpha = min(255, p["life"] * 6)
        col = p["color"]
        s = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*col, alpha), (p["size"], p["size"]), p["size"])
        surface.blit(s, (int(p["x"]), int(p["y"])))


# =========================
# LAYOUT HELPERS
# =========================

def measure_wrapped_lines(text, rect_width, fonts):
#   Υπολογίζει πόσες γραμμές χρειάζεται για wrapped text.
#   Χρησιμοποιεί word wrapping - σπάει μόνο ανάμεσα σε λέξεις.
#   Χρησιμοποιείται επίσης για υπολογισμό ύψους panels.
    paragraphs = text.split("\n")
    total = 0
    for paragraph in paragraphs:
        words = paragraph.split(" ")
        current = ""
        for word in words:
            test = (current + " " + word).strip()
            if fonts.size(test)[0] <= rect_width - 16:
                current = test
            else:
                if current:
                    total += 1
                current = word
        if current:
            total += 1
    return max(1, total)


def panel_height_for_lines(line_count, line_height, padding=OUTPUT_PADDING, min_height=52, max_height=140):
#   Υπολογίζει το ύψος ενός panel βάσει του αριθμού γραμμών.
#   Επιστρέφει: [int] Το ύψος του panel.
    needed = line_count * line_height + padding
    return min(max_height, max(min_height, needed))


def max_visible_lines(rect_height, line_height, padding=OUTPUT_PADDING):
#   Υπολογίζει τον μέγιστο αριθμό ορατών γραμμών σε ένα rectangle.
#   Επιστρέφει: [int] Μέγιστος αριθμός γραμμών που χωράνε
#   Χρησιμοποιείται για scroll calculation σε panels.
    return max(1, (rect_height - padding) // line_height)


def update_layout(level):
#   Προσαρμόζει τη διάταξη UI βάσει του περιεχομένου του level.
#   Υπολογίζει δυναμικά τις θέσεις και τα μεγέθη όλων των panels:
#   - QUESTION_RECT: Βάσει του μήκους της ερώτησης
#   - EXPECTED_RECT: Βάσει του αναμενόμενου output
#   - EDITOR_RECT: Προσαρμόζεται για να χωράει όλα
#   - OUTPUT_RECT: Βάσει του output
#   Χρησιμοποιεί iterative shrinking αν δεν χωράει στην οθόνη.
    global QUESTION_RECT, EXPECTED_RECT, EDITOR_Y, EDITOR_RECT, OUTPUT_RECT
    global RUN_BTN, LAMP_RECT, MESSAGE_Y, FEEDBACK_Y
    global EDITOR_H, EDITOR_VISIBLE_LINES

    question_line_count = measure_wrapped_lines(level["question"], 680, font)
    question_height = min(120, max(64, question_line_count * 22 + 16))

    expected_lines = level["expected"].split("\n")
    expected_line_count = len(expected_lines)
    expected_height = panel_height_for_lines(expected_line_count, OUTPUT_LINE_HEIGHT)

    output_line_count = max(expected_line_count, 1)
    output_height = panel_height_for_lines(output_line_count, OUTPUT_LINE_HEIGHT)

    editor_lines = 6
    while editor_lines >= 4:
        editor_h = editor_lines * EDITOR_LINE_HEIGHT + 22
        q_rect = pygame.Rect(200, HEADER_HEIGHT + 34, 680, question_height)
        e_rect = pygame.Rect(200, q_rect.bottom + PANEL_GAP + 4, 520, expected_height)
        ed_y = e_rect.bottom + PANEL_GAP + 4
        o_rect = pygame.Rect(200, ed_y + editor_h + PANEL_GAP + 4, 520, output_height)
        if o_rect.bottom <= HEIGHT - BOTTOM_MARGIN:
            break
        editor_lines -= 1

    while editor_lines >= 2:
        editor_h = editor_lines * EDITOR_LINE_HEIGHT + 22
        q_rect = pygame.Rect(200, HEADER_HEIGHT + 34, 680, question_height)
        e_rect = pygame.Rect(200, q_rect.bottom + PANEL_GAP + 4, 520, expected_height)
        ed_y = e_rect.bottom + PANEL_GAP + 4
        o_rect = pygame.Rect(200, ed_y + editor_h + PANEL_GAP + 4, 520, output_height)
        if o_rect.bottom <= HEIGHT - BOTTOM_MARGIN:
            break
        if output_height > OUTPUT_LINE_HEIGHT + OUTPUT_PADDING:
            output_height -= OUTPUT_LINE_HEIGHT
        else:
            editor_lines -= 1

    EDITOR_VISIBLE_LINES = editor_lines
    EDITOR_H = editor_lines * EDITOR_LINE_HEIGHT + 22

    QUESTION_RECT = pygame.Rect(200, HEADER_HEIGHT + 34, 680, question_height)
    EXPECTED_RECT = pygame.Rect(200, QUESTION_RECT.bottom + PANEL_GAP + 4, 520, expected_height)
    EDITOR_Y = EXPECTED_RECT.bottom + PANEL_GAP + 4
    EDITOR_RECT = pygame.Rect(200, EDITOR_Y, 520, EDITOR_H)
    OUTPUT_RECT = pygame.Rect(200, EDITOR_RECT.bottom + PANEL_GAP + 4, 520, output_height)
    RUN_BTN = pygame.Rect(735, EDITOR_Y, 100, 40)
    LAMP_RECT = pygame.Rect(90, EDITOR_Y + 12, 60, 60)
    MESSAGE_Y = OUTPUT_RECT.bottom + 16
    FEEDBACK_Y = MESSAGE_Y + 30


# =========================
# SANDBOX
# =========================

SAFE_BUILTINS = {
    "print": print, "range": range, "len": len,
    "int": int, "float": float, "str": str, "bool": bool,
}

BANNED_NAMES = {
    "open", "eval", "exec", "compile", "__import__",
    "globals", "locals", "vars", "input", "exit", "quit",
}

EXECUTION_TIMEOUT = 2.0
_execution_thread = None
_execution_lock = threading.Lock()


# =========================
# VALIDATION
# =========================

def normalize_output(out):
#   Κανονικοποιεί το output του κώδικα σε λίστα γραμμών.
#   Επιστρέφει: [list] Λίστα με τις γραμμές του output (χωρίς trailing spaces/blank lines), Κενή λίστα αν το input είναι κενό
#   Χρησιμοποιείται για σύγκριση του output του χρήστη με τον αναμενόμενο στόχο.
    if not out or not out.strip():
        return []
    return [line.rstrip() for line in out.rstrip("\n").split("\n")]


def uses_print(tree):
#   Ελέγχει αν ο κώδικας περιέχει κλήση της συνάρτησης print.
#   Επιστρέφει: [bool] True αν βρεθεί print() call, False αλλιώς.
#   Χρησιμοποιείται για να διασφαλιστεί ότι ο χρήστης χρησιμοποιεί την έξοδο κονσόλας για την επίλυση του puzzle.
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
            return True
    return False


def assigns_variable(tree, name):
#   Ελέγχει αν ο κώδικας αναθέτει τιμή σε συγκεκριμένη μεταβλητή.
#   Επιστρέφει: [bool] True αν βρεθεί ανάθεση στη μεταβλητή name, False αλλιώς.
#   Χρησιμοποιείται για να διασφαλιστεί ότι ο χρήστης δημιούργησε τη συγκεκριμένη μεταβλητή που απαιτεί το puzzle.
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return True
    return False


def prints_variable(tree, name):
#   Ελέγχει αν ο κώδικας τυπώνει συγκεκριμένη μεταβλητή.
#   Επιστρέφει: [bool] True αν βρεθεί print(name), False αλλιώς.
#   Χρησιμοποιείται για να διασφαλιστεί ότι ο χρήστης τυπώνει τη συγκεκριμένη μεταβλητή που απαιτεί το puzzle.
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
            for arg in node.args:
                if isinstance(arg, ast.Name) and arg.id == name:
                    return True
    return False


def has_arithmetic(tree):
#   Ελέγχει αν ο κώδικας περιέχει αριθμητικές πράξεις.
#   Επιστρέφει: [bool] True αν βρεθεί +, -, *, /, //, ή %, False αλλιώς
#   Χρησιμοποιείται για να διασφαλιστεί ότι ο χρήστης έκανε υπολογισμούς αντί να τυπώσει απλά το αποτέλεσμα.
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod)):
            return True
    return False


def has_if_else(tree):
#   Ελέγχει αν ο κώδικας περιέχει δομή if/else.
#   Επιστρέφει: [bool] True αν βρεθεί if με else block, False αλλιώς.
#   Χρησιμοποιείται για να διασφαλιστεί ότι ο χρήστης χρησιμοποιεί συνθήκες για τη λογική του puzzle.
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and node.orelse:
            return True
    return False


def has_if_elif_else(tree):
#   Ελέγχει αν ο κώδικας περιέχει δομή if/elif/else.
#   Επιστρέφει: [bool] True αν βρεθεί if με elif στο else block, False αλλιώς.
#   Χρησιμοποιείται για να διασφαλιστεί ότι ο χρήστης χρησιμοποιεί πολλαπλές συνθήκες για τη λογική του puzzle.
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and node.orelse:
            if any(isinstance(n, ast.If) for n in node.orelse):
                return True
    return False


def has_while(tree):
#   Ελέγχει αν ο κώδικας περιέχει while loop.
#   Επιστρέφει: [bool] True αν βρεθεί while loop, False αλλιώς
#   Χρησιμοποιείται για να διασφαλιστεί ότι ο χρήστης χρησιμοποιεί επαναλήψεις με while για τη λογική του puzzle.
    return any(isinstance(node, ast.While) for node in ast.walk(tree))


def has_for_with_range(tree):
#   Ελέγχει αν ο κώδικας περιέχει for loop με range.
#   Επιστρέφει: [bool] True αν βρεθεί for ... in range(...), False αλλιώς
#   Χρησιμοποιείται για να διασφαλιστεί ότι ο χρήστης χρησιμοποιεί επαναλήψεις με for/range για τη λογική του puzzle.
    for node in ast.walk(tree):
        if isinstance(node, ast.For) and isinstance(node.iter, ast.Call):
            if isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range":
                return True
    return False


def check_level_1(code, tree, out):
    if not uses_print(tree):
        return False, "Χρησιμοποίησε την εντολή print(...)"
    if normalize_output(out) != ["Hello, Reddy!"]:
        return False, "Το output σου δεν ταιριάζει με τον στόχο"
    return True, ""


def check_level_2(code, tree, out):
    if not assigns_variable(tree, "name"):
        return False, "Δημιούργησε μεταβλητή: name = ..."
    if not prints_variable(tree, "name"):
        return False, "Τύπωσε τη μεταβλητή name με print(name)"
    if normalize_output(out) != ["Python"]:
        return False, "Το output σου δεν ταιριάζει με τον στόχο"
    return True, ""


def check_level_3(code, tree, out):
    if not has_arithmetic(tree):
        return False, "Κάνε αριθμητική πράξη (+, -, *, /) στον κώδικά σου"
    if not uses_print(tree):
        return False, "Χρησιμοποίησε print(...)"
    if normalize_output(out) != ["20"]:
        return False, "Το output σου δεν ταιριάζει με τον στόχο"
    return True, ""


def check_level_4(code, tree, out):
    if not has_if_else(tree):
        return False, "Χρησιμοποίησε if και else"
    if not uses_print(tree):
        return False, "Χρησιμοποίησε print(...)"
    if normalize_output(out) != ["PASS"]:
        return False, "Το output σου δεν ταιριάζει με τον στόχο"
    return True, ""


def check_level_5(code, tree, out):
    if not has_if_elif_else(tree):
        return False, "Χρησιμοποίησε if, elif και else"
    if not uses_print(tree):
        return False, "Χρησιμοποίησε print(...)"
    if normalize_output(out) != ["WARM"]:
        return False, "Το output σου δεν ταιριάζει με τον στόχο"
    return True, ""


def check_level_6(code, tree, out):
    if not has_while(tree):
        return False, "Χρησιμοποίησε while loop"
    if not uses_print(tree):
        return False, "Χρησιμοποίησε print(...)"
    if normalize_output(out) != ["1", "2", "3"]:
        return False, "Το output σου δεν ταιριάζει με τον στόχο"
    return True, ""


def check_level_7(code, tree, out):
    if not has_for_with_range(tree):
        return False, "Χρησιμοποίησε for ... in range(...)"
    if not uses_print(tree):
        return False, "Χρησιμοποίησε print(...)"
    if normalize_output(out) != ["!", "!", "!", "!"]:
        return False, "Το output σου δεν ταιριάζει με τον στόχο"
    return True, ""


def check_level_8(code, tree, out):
    if not has_for_with_range(tree):
        return False, "Χρησιμοποίησε for ... in range(...)"
    if not any(isinstance(n, ast.If) for n in ast.walk(tree)):
        return False, "Χρησιμοποίησε if μέσα στο loop"
    if not uses_print(tree):
        return False, "Χρησιμοποίησε print(...)"
    expected = ["-", "Reddy", "-", "Reddy", "-"]
    if normalize_output(out) != expected:
        return False, "Το output σου δεν ταιριάζει με τον στόχο"
    return True, ""


# =========================
# LEVELS — narrative quests
# =========================

levels = [
    {
        "concept": "print",
        "quest_title": "Quest 1: Η Πύλη",
        "dialogue": "Ο πρώτος φρουρός δεν αναγνωρίζει τον Reddy. Η πύλη θα ανοίξει μόνο αν εμφανιστεί το σωστό μήνυμα.",
        "question": "PUZZLE: Στείλε το μυστικό μήνυμα στην πόρτα.\nΠρέπει να εμφανιστεί ακριβώς:\nHello, Reddy!",
        "expected": "Hello, Reddy!",
        "hint": "print('Hello, Reddy!')",
        "check": check_level_1,
        "visual": "gate",
    },
    {
        "concept": "μεταβλητές",
        "quest_title": "Quest 2: Ο Κρύσταλλος",
        "dialogue": "Μέσα στον πύργο υπάρχει ένας μαγικός κρύσταλλος που αποθηκεύει πληροφορίες. Αποθήκευσε το όνομα της γλώσσας!",
        "question": "PUZZLE: Αποθήκευσε name = \"Python\" και τύπωσε τη μεταβλητή name.",
        "expected": "Python",
        "hint": "name = \"Python\"\nprint(name)",
        "check": check_level_2,
        "visual": "crystal",
    },
    {
        "concept": "πράξεις",
        "quest_title": "Quest 3: Η Κλειδαριά",
        "dialogue": "Η τεράστια μεταλλική κλειδαριά ανοίγει μόνο αν υπολογιστεί σωστά ο μυστικός αριθμός. Υπολόγισε το 12 + 8.",
        "question": "PUZZLE: Υπολόγισε με πράξη (+, -, *, /) και τύπωσε το αποτέλεσμα του 12 + 8.",
        "expected": "20",
        "hint": "print(12 + 8)",
        "check": check_level_3,
        "visual": "lock",
    },
    {
        "concept": "if / else",
        "quest_title": "Quest 4: Η Ξύλινη Πύλη ",
        "dialogue": "Μια μεγάλη ξύλινη πόρτα αποφασίζει ποιος περνάει. Αν score >= 5 → PASS, αλλιώς FAIL. Το score είναι 7!",
        "question": "PUZZLE: Όρισε score = 7.\nΑν score >= 5 τύπωσε PASS, αλλιώς FAIL.",
        "expected": "PASS",
        "hint": "score = 7\nif score >= 5:\n    print('PASS')\nelse:\n    print('FAIL')",
        "check": check_level_4,
        "visual": "door",
    },
    {
        "concept": "if / elif / else",
        "quest_title": "Quest 5: Ο Δράκος",
        "dialogue": "Ένας δράκος φυλάει το πέρασμα. Η διάθεσή του αλλάζει με τη θερμοκρασία (temp = 15). Πες του το σωστό μήνυμα!",
        "question": "PUZZLE: Όρισε temp = 15.\nΑν temp >= 30 → HOT\nelif temp >= 10 → WARM\nelse → COLD",
        "expected": "WARM",
        "hint": "temp = 15\nif temp >= 30:\n    print('HOT')\nelif temp >= 10:\n    print('WARM')\nelse:\n    print('COLD')",
        "check": check_level_5,
        "visual": "dragon",
    },
    {
        "concept": "while",
        "quest_title": "Quest 6: Ο Μηχανισμός",
        "dialogue": "Ένας αρχαίος μηχανισμός χρειάζεται να μετρήσει μέχρι το 3 για να ενεργοποιηθεί. Χρησιμοποίησε while!",
        "question": "PUZZLE: Με while loop, τύπωσε τους αριθμούς 1, 2, 3\n(μία γραμμή η καθεμία).",
        "expected": "1\n2\n3",
        "hint": "i = 1\nwhile i <= 3:\n    print(i)\n    i += 1",
        "check": check_level_6,
        "visual": "gear",
    },
    {
        "concept": "for",
        "quest_title": "Quest 7: Οι Πύργοι",
        "dialogue": "Τέσσερις πύργοι επικοινωνίας πρέπει να ενεργοποιηθούν ένας-ένας. Κάθε '!' ανάβει έναν πύργο!",
        "question": "PUZZLE: Με for και range, τύπωσε \"!\" 4 φορές\n(μία σε κάθε γραμμή).",
        "expected": "!\n!\n!\n!",
        "hint": "for i in range(4):\n    print('!')",
        "check": check_level_7,
        "visual": "towers",
    },
    {
        "concept": "συνδυασμός",
        "quest_title": "Quest 8: Η Γέφυρα",
        "dialogue": "Ο Πύργος της Python είναι απέναντι! Η γέφυρα έχει καταστραφεί. Χτίσε τα πλακίδια: Άρτια = Reddy, μονά = -.",
        "question": "PUZZLE: Για κάθε αριθμό 1 έως 5:\nαν είναι άρτιος → Reddy\nαλλιώς → -\n(Χτίσε τη γέφυρα με print!)",
        "expected": "-\nReddy\n-\nReddy\n-",
        "hint": "for n in range(1, 6):\n    if n % 2 == 0:\n        print('Reddy')\n    else:\n        print('-')",
        "check": check_level_8,
        "visual": "bridge",
    },
]

update_layout(levels[0])


# =========================
# SCORING
# =========================

def calculate_stars():
#   *** = 1η προσπάθεια,  **= χωρίς hint, * = ολοκλήρωση
    if wrong_attempts == 0 and not hint_used_this_level:
        return 3
    if not hint_used_this_level:
        return 2
    return 1


def total_stars():
#   Υπολογίζει το σύνολο των αστέριών.
    return sum(level_stars)


# =========================
# EDITOR
# =========================

def get_code():
#   Επιστρέφει τον κώδικα του χρήστη ως ενιαίο string.
#   Επιστρέφει: [str] Όλες οι γραμμές του editor ενωμένες με newline
#   Μετατρέπει τη λίστα user_lines σε string για εκτέλεση.
    return "\n".join(user_lines)


def reset_editor():
#   Επαναφέρει τον editor στην αρχική κατάσταση.
#   Χρησιμοποιείται στην αρχή κάθε νέου puzzle.
    global user_lines, cursor_line, cursor_col, editor_scroll, output_text, output_feedback, output_scroll
    user_lines = [""]
    cursor_line = 0
    cursor_col = 0
    editor_scroll = 0
    output_text = ""
    output_feedback = ""
    output_scroll = 0


def reset_hint_state():
#   Επαναφέρει την κατάσταση του συστήματος hints.
#   Μηδενίζει τα wrong attempts, κλειδώνει το hint και επαναφέρει το animation του λυχναριού.
#   Χρησιμοποιείται στην αρχή κάθε νέου puzzle.
    global wrong_attempts, hint_unlocked, hint_visible, hint_used_this_level, lamp_pulse
    wrong_attempts = 0
    hint_unlocked = False
    hint_visible = False
    hint_used_this_level = False
    lamp_pulse = 0


def ensure_cursor_visible():
#   Διασφαλίζει ότι ο κέρσορας είναι ορατός στο editor.
#   Προσαρμόζει το scroll ώστε η γραμμή του κέρσορα να είναι πάντα μέσα στα ορατά όρια του editor.
    global editor_scroll
    if cursor_line < editor_scroll:
        editor_scroll = cursor_line
    elif cursor_line >= editor_scroll + EDITOR_VISIBLE_LINES:
        editor_scroll = cursor_line - EDITOR_VISIBLE_LINES + 1


def insert_text(text):
#   Εισάγει κείμενο στη θέση του κέρσορα.
    global cursor_col
    line = user_lines[cursor_line]
    user_lines[cursor_line] = line[:cursor_col] + text + line[cursor_col:]
    cursor_col += len(text)


def delete_before_cursor():
#   Διαγράφει τον χαρακτήρα πριν τον κέρσορα (Backspace).
    global cursor_line, cursor_col
    if cursor_col > 0:
        line = user_lines[cursor_line]
        user_lines[cursor_line] = line[:cursor_col - 1] + line[cursor_col:]
        cursor_col -= 1
    elif cursor_line > 0:
        prev_len = len(user_lines[cursor_line - 1])
        user_lines[cursor_line - 1] += user_lines[cursor_line]
        del user_lines[cursor_line]
        cursor_line -= 1
        cursor_col = prev_len


def delete_after_cursor():
#   Διαγράφει τον χαρακτήρα μετά τον κέρσορα (Delete).
    line = user_lines[cursor_line]
    if cursor_col < len(line):
        user_lines[cursor_line] = line[:cursor_col] + line[cursor_col + 1:]
    elif cursor_line < len(user_lines) - 1:
        user_lines[cursor_line] += user_lines[cursor_line + 1]
        del user_lines[cursor_line + 1]


def newline_at_cursor():
#   Δημιουργεί νέα γραμμή στη θέση του κέρσορα (Enter).
    global cursor_line, cursor_col
    line = user_lines[cursor_line]
    before = line[:cursor_col]
    after = line[cursor_col:]
    user_lines[cursor_line] = before
    user_lines.insert(cursor_line + 1, after)
    cursor_line += 1
    cursor_col = 0
    ensure_cursor_visible()


def move_cursor(dx, dy):
#   Κινεί τον κέρσορα οριζόντια και κάθετα.

    global cursor_line, cursor_col
    if dy != 0:
        cursor_line = max(0, min(len(user_lines) - 1, cursor_line + dy))
        cursor_col = min(cursor_col, len(user_lines[cursor_line]))
    if dx != 0:
        cursor_col = max(0, min(len(user_lines[cursor_line]), cursor_col + dx))
    ensure_cursor_visible()


def scroll_editor(dy):
#   Κυλάει τον editor κατά dy γραμμές.
#   Χρησιμοποιείται με Ctrl+Up/Down για πλοήγηση.
    global editor_scroll
    max_scroll = max(0, len(user_lines) - EDITOR_VISIBLE_LINES)
    editor_scroll = max(0, min(max_scroll, editor_scroll + dy))


def scroll_output(dy):
#   Κυλάει το output panel κατά dy γραμμές.
#   Χρησιμοποιείται με Ctrl+Shift+Up/Down για πλοήγηση.
    global output_scroll
    if not output_text.strip():
        output_scroll = 0
        return
    lines = output_text.rstrip("\n").split("\n")
    visible = max_visible_lines(OUTPUT_RECT.height, OUTPUT_LINE_HEIGHT)
    max_scroll = max(0, len(lines) - visible)
    output_scroll = max(0, min(max_scroll, output_scroll + dy))


def clamp_output_scroll():
#   Περιορίζει το scroll του output μέσα στα έγκυρα όρια.
#   Χρησιμοποιείται μετά από αλλαγές στο output.
    global output_scroll
    if not output_text.strip():
        output_scroll = 0
        return
    lines = output_text.rstrip("\n").split("\n")
    visible = max_visible_lines(OUTPUT_RECT.height, OUTPUT_LINE_HEIGHT)
    max_scroll = max(0, len(lines) - visible)
    output_scroll = max(0, min(max_scroll, output_scroll))


# =========================
# ANIMATIONS
# =========================

def trigger_error_fx():
#   Ενεργοποιεί τα εφέ λάθους.
#   - Shake: Κουνάει την οθόνη για οπτική ανατροφοδότηση
#   - Flash: Κόκκινο flash overlay για έμφαση στο λάθος
#   - Ήχος: Error tone για ακουστική ανατροφοδότηση
#   Χρησιμοποιείται όταν ο κώδικας του χρήστη είναι λάθος.
    global shake_time, flash_color, flash_time
    shake_time = 350
    flash_color = (255, 80, 80)
    flash_time = 200
    play_sound("error")


def trigger_success_fx():
#   Ενεργοποιεί τα εφέ επιτυχίας.
#   - Bounce: Ο χαρακτήρας Reddy χοροπηδάει
#   - Flash: Πράσινο flash overlay για έμφαση στην επιτυχία
#   - Σωματίδια: Gold και green particles για γιορταστικό εφέ
#   - Ήχος: Success chord για ακουστική ανατροφοδότηση
#   Χρησιμοποιείται όταν ο κώδικας του χρήστη είναι σωστός.
    global reddy_bounce, flash_color, flash_time
    reddy_bounce = 1.0
    flash_color = (80, 255, 120)
    flash_time = 250
    play_sound("success")
    spawn_particles(75, EDITOR_Y + 95, GOLD, 24)
    spawn_particles(WIDTH // 2, HEIGHT // 2, GREEN, 16)


def update_animations(dt):
#   Ενημερώνει όλες τις animations του παιχνιδιού.
#   Ενημερώνει:
#   - shake_time/shake_x: Screen shake effect
#   - reddy_bounce: Bounce animation του χαρακτήρα
#   - flash_time/flash_color: Flash overlay effect
#   Καλείται σε κάθε frame του main loop.
    global shake_time, shake_x, reddy_bounce, flash_time, flash_color

    if shake_time > 0:
        shake_time -= dt
        shake_x = random.randint(-5, 5) if shake_time > 0 else 0
    else:
        shake_x = 0

    if reddy_bounce > 0:
        reddy_bounce = max(0, reddy_bounce - dt / 1200)

    if flash_time > 0:
        flash_time -= dt
        if flash_time <= 0:
            flash_color = None


# =========================
# EXECUTION
# =========================

def validate_ast(tree):
#   Ελέγχει αν το Abstract Syntax Tree (AST) περιέχει απαγορευμένες εντολές.
#   Επιστρέφει: tuple: (bool, str) - (True, '') αν ο κώδικας είναι ασφαλής, (False, error_msg) αν βρεθεί απαγορευμένη εντολή
#   Ελέγχει για:
#   - Import statements (import, from ... import)
#   - Απαγορευμένα ονόματα (eval, exec, open, κλπ)
#   - Πρόσβαση σε attributes (security risk)
#   - while True loops (infinite loop prevention)
#   - break/continue statements
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return False, " Δεν επιτρέπεται η χρήση import."
        if isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            return False, f" Η εντολή '{node.id}' δεν επιτρέπεται."
        if isinstance(node, ast.Attribute):
            return False, " Δεν επιτρέπεται πρόσβαση σε εσωτερικά αντικείμενα."
        if isinstance(node, ast.While):
            if isinstance(node.test, ast.Constant) and node.test.value is True:
                return False, " Δεν επιτρέπεται while True."
        if isinstance(node, (ast.Break, ast.Continue)):
            return False, " Δεν επιτρέπεται break/continue."
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BANNED_NAMES:
                return False, f" Η εντολή '{node.func.id}' δεν επιτρέπεται."
    return True, ""


def _execute_in_thread(code, result_container):
#   Εκτελεί κώδικα Python σε ξεχωριστό thread για υποστήριξη timeout.
#   Χρησιμοποιείται σε συνδυασμό με threading.Thread.join(timeout)για την αποφυγή infinite loops στον κώδικα του χρήστη.
#   Ο κώδικας εκτελείται με περιορισμένα builtins (SAFE_BUILTINS)για λόγους ασφαλείας.
    try:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exec(code, {"__builtins__": SAFE_BUILTINS})
        result_container["output"] = output.getvalue()
        result_container["error"] = None
    except Exception as e:
        result_container["output"] = ""
        result_container["error"] = e


def run_user_code(code, check_func):
#   Εκτελεί τον κώδικα του χρήστη σε ασφαλές sandbox και επιστρέφει το αποτέλεσμα.
#   Επιστρέφει:
#       tuple: (success: bool, output: str, error: str ή None)
#              success: True αν ο κώδικας πέρασε τον έλεγχο
#              output: Το stdout από την εκτέλεση
#              error: Μήνυμα σφάλματος (αν υπάρχει)
#   Διαδικασία:
#   1. Έλεγχος κενού κώδικα και μέγεθους
#   2. Parsing σε AST και έλεγχος syntax
#   3. Validation AST για απαγορευμένες εντολές
#   4. Εκτέλεση σε thread με timeout (EXECUTION_TIMEOUT)
#   5. Χειρισμός exceptions και επιστροφή κατάλληλου μηνύματος
#   6. Έλεγχος αποτελέσματος μέσω check_func
    global _execution_thread
    if not code.strip():
        return False, "", "Γράψε κώδικα πριν πατήσεις RUN"
    if len(code) > 1500:
        return False, "", " Ο κώδικας είναι πολύ μεγάλος."
    if len(code.splitlines()) > 80:
        return False, "", " Πάρα πολλές γραμμές κώδικα."
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, "", f"SyntaxError: {e.msg} (γραμμή {e.lineno})"
    ok_ast, ast_msg = validate_ast(tree)
    if not ok_ast:
        return False, "", ast_msg
    with _execution_lock:
        if _execution_thread is not None and _execution_thread.is_alive():
            return False, "", " Περίμενε... ο προηγούμενος κώδικας ακόμα τρέχει."
        result_container = {"output": "", "error": None}
        _execution_thread = threading.Thread(
            target=_execute_in_thread, args=(code, result_container), daemon=True,
        )
        _execution_thread.start()
    _execution_thread.join(timeout=EXECUTION_TIMEOUT)
    if _execution_thread.is_alive():
        return False, "", (
            f" Υπερβήκατε το όριο χρόνου ({EXECUTION_TIMEOUT:.0f} δευτ.). "
            "Πιθανός ατέρμονος βρόχος — έλεγξε τη συνθήκη του while/for."
        )
    if result_container["error"] is not None:
        e = result_container["error"]
        if isinstance(e, NameError):
            return False, "", f" Μεταβλητή που δεν υπάρχει.\n{e}"
        if isinstance(e, TypeError):
            return False, "", f" Λάθος τύπος δεδομένων.\n{e}"
        if isinstance(e, ZeroDivisionError):
            return False, "", " Δεν μπορείς να διαιρέσεις με το μηδέν."
        if isinstance(e, IndentationError):
            return False, "", " Λάθος indentation."
        return False, "", f" Σφάλμα: {e}"
    result = result_container["output"]
    ok, feedback = check_func(code, tree, result)
    if ok:
        return True, result, None
    return False, result, feedback


# =========================
# DRAW — UI
# =========================

def draw_multiline_in_rect(surface, lines, rect, fonts, color, line_height, max_lines=None):
#   Σχεδιάζει πολλαπλές γραμμές κειμένου σε rectangle.
#   Χρησιμοποιείται για output panels με scroll.
    if max_lines is None:
        max_lines = max_visible_lines(rect.height, line_height)
    y = rect.y + 6
    max_y = rect.bottom - 6
    for line in lines[:max_lines]:
        if y + line_height > max_y:
            break
        surface.blit(fonts.render(line, True, color), (rect.x + 8, y))
        y += line_height


def draw_wrapped_multiline(surface, text, rect, fonts, color, line_height):
#   Σχεδιάζει κείμενο με automatic word wrapping.
#   Σπάει λέξεις που δεν χωράνε στην τρέχουσα γραμμή.
#   Χρησιμοποιείται για long text όπως hints.
    paragraphs = text.split("\n")
    y = rect.y + 8
    max_y = rect.bottom - 8
    for paragraph in paragraphs:
        words = paragraph.split(" ")
        current = ""
        for word in words:
            test = (current + " " + word).strip()
            if fonts.size(test)[0] <= rect.width - 16:
                current = test
            else:
                if current:
                    surface.blit(fonts.render(current, True, color), (rect.x + 8, y))
                    y += line_height
                    if y > max_y:
                        return
                current = word
        if current:
            surface.blit(fonts.render(current, True, color), (rect.x + 8, y))
            y += line_height
            if y > max_y:
                return


def draw_text(surface, text, color, rect, fonts):
#   Σχεδιάζει κείμενο με wrapping σε rectangle.
#   Απλοποιημένη έκδοση του draw_wrapped_multiline.
    words = text.split(" ")
    lines = []
    current = ""
    for w in words:
        test = current + w + " "
        if fonts.size(test)[0] <= rect.width - 10:
            current = test
        else:
            lines.append(current)
            current = w + " "
    lines.append(current)
    y = rect.y + 10
    for line in lines:
        surface.blit(fonts.render(line, True, color), (rect.x + 10, y))
        y += fonts.get_height()


def draw_stars(surface, x, y, count, size=22, spacing=28):
#   Σχεδιάζει αστέρια βαθμολόγησης (1-3).
#   Τα κενά αστέρια είναι γκρίζα, τα γεμάτα είναι χρυσά.
#   Χρησιμοποιείται για level completion rating.
    for i in range(3):
        cx = x + i * spacing
        filled = i < count
        color = GOLD if filled else (200, 200, 200)
        points = []
        for j in range(10):
            angle = math.pi / 2 + j * math.pi / 5
            r = size // 2 if j % 2 == 0 else size // 5
            points.append((cx + r * math.cos(angle), y + r * math.sin(angle)))
        pygame.draw.polygon(surface, color, points)


def draw_progress_bar(surface):
#   Σχεδιάζει την μπάρα προόδου των quests.
#   Δείχνει πόσα levels έχουν ολοκληρωθεί.
#   Πράσινο fill για το progress, γκρίζο background.
    bar = pygame.Rect(200, 52, 680, 12)
    pygame.draw.rect(surface, GRAY, bar, border_radius=6)
    progress = (level_index + (1 if success else 0)) / len(levels)
    fill_w = max(0, int(bar.width * progress))
    if fill_w > 0:
        pygame.draw.rect(surface, GREEN, pygame.Rect(bar.x, bar.y, fill_w, bar.height), border_radius=6)
    label = small_font.render(f"Quest Progress: {level_index + 1}/{len(levels)}", True, DARK_GREEN)
    surface.blit(label, (bar.x, bar.y - 18))


def draw_quest_map(surface):
#   Mini-map 8 quests.
    start_x, y = 620, 12
    spacing = 32
    for i in range(len(levels)):
        x = start_x + i * spacing
        if i < level_index:
            col = MAP_DONE
        elif i == level_index:
            col = RED
        else:
            col = MAP_LOCKED
        pygame.draw.circle(surface, col, (x, y), 10)
        pygame.draw.circle(surface, DARK_GREEN, (x, y), 10, 2)
        if level_stars[i] > 0:
            draw_stars(surface, x - 26, y + 14, level_stars[i], size=10, spacing=12)


def draw_reddy(surface, cx, cy, bounce=0.0, happy=False):
#   Σχεδιάζει τον χαρακτήρα Reddy (κόκκινο μπαλάκι).
#   Ο χαρακτήρας έχει μάτια, στόμα και μαγουλάκια.
#   Το bounce εφαρμόζεται κάθετα.
    bounce_y = int(abs(math.sin(pygame.time.get_ticks() / 120)) * 18 * bounce) if bounce > 0 else 0
    cy -= bounce_y

    # σώμα
    body = (255, 90, 90) if happy else (220, 50, 50)
    pygame.draw.circle(surface, body, (cx, cy), 45)

    # μαγουλάκια όταν είναι χαρούμενος
    if happy:
        pygame.draw.circle(surface, (255, 170, 170), (cx - 24, cy + 6), 7)
        pygame.draw.circle(surface, (255, 170, 170), (cx + 24, cy + 6), 7)

    # μάτια
    if happy:
        # χαρούμενα "κλειστά" μάτια
        pygame.draw.arc(surface, BLACK, pygame.Rect(cx - 24, cy - 20, 16, 12), math.pi, 2 * math.pi, 3)
        pygame.draw.arc(surface, BLACK, pygame.Rect(cx + 8, cy - 20, 16, 12), math.pi, 2 * math.pi, 3)
    else:
        # κανονικά μάτια
        pygame.draw.circle(surface, WHITE, (cx - 16, cy - 11), 11)
        pygame.draw.circle(surface, WHITE, (cx + 16, cy - 11), 11)
        pygame.draw.circle(surface, BLACK, (cx - 16, cy - 11), 4)
        pygame.draw.circle(surface, BLACK, (cx + 16, cy - 11), 4)

    # στόμα
    if happy:
        pygame.draw.arc(surface,BLACK,pygame.Rect(cx - 22, cy + 2, 44, 30),math.pi,2 * math.pi,4)
    else:
        pygame.draw.arc(surface,BLACK,pygame.Rect(cx - 16, cy + 14, 32, 10),math.pi,2 * math.pi,2)

def draw_puzzle_visual(surface, level):
#   Σχεδιάζει τα γραφικά του puzzle δίπλα στον Reddy.
#   Διαφορετικά visuals ανάλογα με τον τύπο puzzle:
#   - 'apples': Κόκκινα και πράσινα μήλα
#   - 'bridge': Tiles για γέφυρα
#   - 'stars': Αστέρια για συλλογή
    vx, vy = 10, EDITOR_RECT.bottom + 10
    vtype = level.get("visual")
    if not vtype:
        return

    box = pygame.Rect(vx, vy, 170, 70)
    pygame.draw.rect(surface, QUEST_GOLD, box, border_radius=8)
    pygame.draw.rect(surface, DARK_GREEN, box, 2, border_radius=8)
    surface.blit(small_font.render("PUZZLE", True, DARK_GREEN), (vx + 8, vy + 4))

    if vtype == "gate":
        pygame.draw.rect(surface, DARK_GRAY, (vx + 50, vy + 20, 70, 45), border_radius=4)
        pygame.draw.rect(surface, RED, (vx + 55, vy + 35, 60, 15))
        surface.blit(small_font.render("DENIED", True, WHITE), (vx + 58, vy + 33))

    elif vtype == "crystal":
        points = [(vx + 85, vy + 18), (vx + 105, vy + 40), (vx + 85, vy + 62), (vx + 65, vy + 40)]
        pygame.draw.polygon(surface, LIGHT_BLUE, points)
        pygame.draw.polygon(surface, BLUE, points, 2)
        pygame.draw.circle(surface, WHITE, (vx + 80, vy + 30), 3)

    elif vtype == "lock":
        pygame.draw.rect(surface, DARK_GRAY, (vx + 60, vy + 28, 50, 32), border_radius=4)
        pygame.draw.arc(surface, DARK_GRAY, pygame.Rect(vx + 68, vy + 14, 34, 30), 0, math.pi, 4)
        surface.blit(code_font.render("12+8=?", True, BLACK), (vx + 20, vy + 38))

    elif vtype == "door":
        pygame.draw.rect(surface, (139, 90, 43), (vx + 55, vy + 20, 60, 45), border_radius=3)
        pygame.draw.circle(surface, GOLD, (vx + 100, vy + 45), 5)
        surface.blit(small_font.render("score≥5", True, BLACK), (vx + 18, vy + 48))


    elif vtype == "dragon":
        # Κεντρικό σημείο αναφοράς για το κεφάλι του δράκου
        hx, hy = vx + 60, vy + 35
        # 1. ΦΩΤΙΑ (Σχεδιάζεται πρώτη για να φαίνεται ότι βγαίνει ΜΕΣΑ από το στόμα)
        # Εξωτερική μεγάλη κόκκινη φλόγα
        pygame.draw.polygon(surface, RED,
                            [(hx + 25, hy + 5), (vx + 155, vy + 15), (vx + 165, vy + 35), (vx + 150, vy + 55)])
        # Μεσαία πορτοκαλί φλόγα
        pygame.draw.polygon(surface, (255, 120, 0),
                            [(hx + 30, hy + 5), (vx + 135, vy + 22), (vx + 140, vy + 35), (vx + 130, vy + 48)])
        # Εσωτερική κίτρινη φλόγα (πυρήνας)
        pygame.draw.polygon(surface, YELLOW,
                            [(hx + 35, hy + 5), (vx + 115, vy + 28), (vx + 120, vy + 35), (vx + 112, vy + 42)])
        # 2. ΣΩΜΑ & ΛΑΙΜΟΣ (Σκούρο πράσινο)
        pygame.draw.polygon(surface, DARK_GREEN,
                            [(vx + 20, vy + 65), (vx + 45, vy + 65), (hx, hy + 15), (hx - 15, hy + 10)])
        # Αγκάθια στην πλάτη/λαιμό (ακόμα πιο σκούρο πράσινο για αντίθεση)
        pygame.draw.polygon(surface, (15, 60, 15), [(vx + 35, vy + 45), (vx + 23, vy + 40), (vx + 38, vy + 38)])
        pygame.draw.polygon(surface, (15, 60, 15), [(vx + 26, vy + 58), (vx + 14, vy + 52), (vx + 29, vy + 50)])
        # 3. ΚΕΦΑΛΙ & ΣΑΓΟΝΙΑ
        # Κρανίο (Κύκλος)
        pygame.draw.circle(surface, DARK_GREEN, (hx, hy), 14)
        # Πάνω Σαγόνι (Ρύγχος)
        pygame.draw.polygon(surface, DARK_GREEN, [(hx, hy - 12), (hx + 35, hy - 2), (hx + 35, hy + 6), (hx, hy + 10)])
        # Κάτω Σαγόνι (Ανοιχτό για τη φωτιά)
        pygame.draw.polygon(surface, DARK_GREEN,
                            [(hx, hy + 6), (hx + 28, hy + 14), (hx + 22, hy + 22), (hx - 5, hy + 14)])
        # 4. ΛΕΠΤΟΜΕΡΕΙΕΣ (Κέρατα και Μάτι)
        # Πίσω κέρατο (γκρι/κοκάλινο)
        pygame.draw.polygon(surface, (140, 140, 140), [(hx - 8, hy - 8), (hx - 28, hy - 22), (hx - 2, hy - 12)])
        # Μπροστινό κέρατο
        pygame.draw.polygon(surface, (180, 180, 180), [(hx - 4, hy - 10), (hx - 22, hy - 26), (hx + 2, hy - 12)])
        # Λαμπερό κίτρινο μάτι
        pygame.draw.circle(surface, YELLOW, (hx + 10, hy - 3), 3)

    elif vtype == "gear":
        pygame.draw.circle(surface, GRAY, (vx + 85, vy + 45), 18)
        pygame.draw.circle(surface, DARK_GRAY, (vx + 85, vy + 45), 18, 4)
        pygame.draw.circle(surface, DARK_GRAY, (vx + 85, vy + 45), 6)
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            cx = vx + 85 + 20 * math.cos(rad)
            cy = vy + 45 + 20 * math.sin(rad)
            pygame.draw.circle(surface, DARK_GRAY, (int(cx), int(cy)), 4)

    elif vtype == "towers":
        for i in range(4):
            tx = vx + 20 + i * 32
            pygame.draw.rect(surface, DARK_GRAY, (tx, vy + 30, 18, 30))
            surface.blit(code_font.render("!", True, YELLOW), (tx + 5, vy + 34))

    elif vtype == "bridge":
        tiles = level["expected"].split("\n")
        for i, t in enumerate(tiles):
            tx = vx + 12 + i * 30
            col = RED if t.strip() == "Reddy" else (160, 160, 160)
            pygame.draw.rect(surface, col, (tx, vy + 38, 26, 22), border_radius=4)
            label = "R" if t.strip() == "Reddy" else "-"
            surface.blit(small_font.render(label, True, WHITE), (tx + 7, vy + 40))

def draw_bridge_from_output(surface):
#   Σχεδιάζει τη γέφυρα από το output του χρήστη (Level 8).
#   Κάθε γραμμή output γίνεται tile στη γέφυρα.
    if level_index != 7 or not output_text.strip():
        return
    lines = normalize_output(output_text)
    bx, by = 200, OUTPUT_RECT.bottom + 4
    if by + 30 > HEIGHT:
        return
    for i, t in enumerate(lines[:5]):
        tx = bx + i * 100
        is_reddy = t.strip() == "Reddy"
        col = RED if is_reddy else (140, 140, 140)
        pygame.draw.rect(surface, col, (tx, by, 90, 26), border_radius=6)
        label = "Reddy" if is_reddy else t.strip()[:8]
        surface.blit(small_font.render(label, True, WHITE), (tx + 8, by + 5))


def draw_expected_panel(surface, expected):
#   Σχεδιάζει το panel με τον στόχο του puzzle.
#   Δείχνει τι πρέπει να βγάλει ο κώδικας του χρήστη.
#   Χρησιμοποιεί multiline rendering για πολλαπλές γραμμές.
    pygame.draw.rect(surface, EXPECTED_BG, EXPECTED_RECT, border_radius=8)
    pygame.draw.rect(surface, DARK_GREEN, EXPECTED_RECT, 2, border_radius=8)
    surface.blit(
        small_font.render("ΣΤΟΧΟΣ PUZZLE", True, DARK_GREEN),
        (EXPECTED_RECT.x, EXPECTED_RECT.y - LABEL_ABOVE),
    )
    draw_multiline_in_rect(surface, expected.split("\n"), EXPECTED_RECT, code_font, DARK_GREEN, OUTPUT_LINE_HEIGHT)


def draw_editor(surface):
#   Σχεδιάζει τον κώδικα editor με line numbers και cursor.
#   - Δείχνει line numbers στα αριστερά
#   - Δείχνει τον κώδικα του χρήστη
#   - Δείχνει τον cursor (μπλε γραμμή)
#   - Υποστηρίζει scroll
    rect = EDITOR_RECT.move(shake_x, 0)
    pygame.draw.rect(surface, EDITOR_BG, rect, border_radius=8)
    pygame.draw.rect(surface, BLACK, rect, 2, border_radius=8)
    surface.blit(small_font.render("ΚΩΔΙΚΑΣ", True, DARK_GREEN), (EDITOR_RECT.x, EDITOR_RECT.y - LABEL_ABOVE))
    surface.blit(
        small_font.render("Ctrl+Enter = Run  |  Scroll: ↑↓", True, DARK_GRAY),
        (EDITOR_RECT.right - 210, EDITOR_RECT.y - LABEL_ABOVE),
    )
    y = rect.y + 6
    visible = user_lines[editor_scroll:editor_scroll + EDITOR_VISIBLE_LINES]
    for i, line in enumerate(visible):
        line_num = editor_scroll + i + 1
        surface.blit(code_font.render(f"{line_num:2}", True, DARK_GRAY), (rect.x + 6, y))
        surface.blit(code_font.render(line, True, BLACK), (rect.x + 36, y))
        y += EDITOR_LINE_HEIGHT
    if len(user_lines) > EDITOR_VISIBLE_LINES:
        scroll_text = f"{editor_scroll + 1}-{min(editor_scroll + EDITOR_VISIBLE_LINES, len(user_lines))} / {len(user_lines)}"
        surface.blit(small_font.render(scroll_text, True, DARK_GRAY), (rect.right - 70, rect.bottom - 16))
    if cursor_visible and phase == "question" and state == "game":
        if editor_scroll <= cursor_line < editor_scroll + EDITOR_VISIBLE_LINES:
            rel_line = cursor_line - editor_scroll
            cx = rect.x + 36 + code_font.size(user_lines[cursor_line][:cursor_col])[0]
            cy = rect.y + 6 + rel_line * EDITOR_LINE_HEIGHT
            pygame.draw.line(surface, BLUE, (cx, cy), (cx, cy + EDITOR_LINE_HEIGHT - 4), 2)


def draw_output_panel(surface):
#   Σχεδιάζει το panel με το output του κώδικα.
#   Δείχνει το stdout από την εκτέλεση του κώδικα.
#   Υποστηρίζει scroll για μεγάλο output.
    rect = OUTPUT_RECT.move(shake_x, 0)
    pygame.draw.rect(surface, OUTPUT_BG, rect, border_radius=8)
    pygame.draw.rect(surface, DARK_GRAY, rect, 2, border_radius=8)
    surface.blit(small_font.render("ΤΟ OUTPUT ΣΟΥ", True, WHITE), (OUTPUT_RECT.x, OUTPUT_RECT.y - LABEL_ABOVE))
    if output_text.strip():
        lines = output_text.rstrip("\n").split("\n")
        visible_count = max_visible_lines(OUTPUT_RECT.height, OUTPUT_LINE_HEIGHT)
        visible_lines = lines[output_scroll:output_scroll + visible_count]
        draw_multiline_in_rect(surface, visible_lines, rect, code_font, OUTPUT_TEXT, OUTPUT_LINE_HEIGHT, visible_count)
        if len(lines) > visible_count:
            scroll_text = f"{output_scroll + 1}-{min(output_scroll + visible_count, len(lines))} / {len(lines)}"
            surface.blit(small_font.render(scroll_text, True, DARK_GRAY), (rect.right - 70, rect.bottom - 16))
    else:
        surface.blit(
            code_font.render("(τρέξε κώδικα για να δεις output)", True, DARK_GRAY),
            (rect.x + 8, rect.y + 8),
        )


def get_hint_rect(level):
#   Επιστρέφει το rectangle και τις γραμμές του hint.
#   Υπολογίζει το ύψος βάσει του αριθμού γραμμών hint.
    hint_lines = level["hint"].split("\n")
    height = len(hint_lines) * HINT_LINE_HEIGHT + 20
    y = OUTPUT_RECT.bottom + HINT_GAP
    return pygame.Rect(200, y, 635, height), hint_lines


def draw_hint_panel(surface, level):
#   Σχεδιάζει το panel με τη βοήθεια (hint).
#   - Δείχνει το hint text με scroll αν είναι μεγάλο
#   - Χρησιμοποιεί fixed height για να χωράει στην οθόνη
#   - Δείχνει scroll indicator αν χρειάζεται
    hint_rect, hint_lines = get_hint_rect(level)

    # FIXED HEIGHT για να χωράει πάντα στην οθόνη
    visible_lines = 4
    line_h = HINT_LINE_HEIGHT
    padding = 20

    fixed_height = visible_lines * line_h + padding

    hint_rect.height = fixed_height
    hint_rect.y = min(hint_rect.y, HEIGHT - fixed_height - 10)

    pygame.draw.rect(surface, (230, 255, 230), hint_rect, border_radius=12)
    pygame.draw.rect(surface, GREEN, hint_rect, 2, border_radius=12)

    surface.blit(small_font.render("ΒΟΗΘΕΙΑ", True, DARK_GREEN),
                 (hint_rect.x, hint_rect.y - LABEL_ABOVE))

    # SCROLL state
    if not hasattr(draw_hint_panel, "scroll"):
        draw_hint_panel.scroll = 0

    max_scroll = max(0, len(hint_lines) - visible_lines)

    keys = pygame.key.get_pressed()

    start = draw_hint_panel.scroll
    end = start + visible_lines

    visible = hint_lines[start:end]

    y = hint_rect.y + 10
    for line in visible:
        surface.blit(code_font.render(line, True, DARK_GREEN),
                     (hint_rect.x + 10, y))
        y += line_h

    # scroll indicator
    if len(hint_lines) > visible_lines:
        txt = f"{start + 1}-{min(end, len(hint_lines))}/{len(hint_lines)}"
        surface.blit(small_font.render(txt, True, DARK_GRAY),
                     (hint_rect.right - 90, hint_rect.bottom - 18))


def draw_lamp(surface, level):
#   Σχεδιάζει το λυχνάρι των hints.
#   - Κλειδωμένο (γκρίζο): Το hint δεν είναι ακόμα διαθέσιμο
#   - Παλμωμένο (κίτρινο): Το hint είναι διαθέσιμο
#   - Σταθερό (χρυσό): Το hint είναι ανοιχτό
#   Χρησιμοποιείται για hint unlock μετά από 2 λάθη.
    global lamp_pulse, lamp_hover, hint_used_this_level
    if not hint_unlocked:
        return
    mouse_pos = pygame.mouse.get_pos()
    lamp_hover = LAMP_RECT.collidepoint(mouse_pos)
    if hint_visible:
        draw_hint_panel(surface, level)
        pulse = 0
        color = (255, 240, 80) if lamp_hover else (220, 220, 0)
    else:
        lamp_pulse += 0.05
        blink = (math.sin(lamp_pulse) + 1) / 2
        pulse = 4 + int(4 * blink)
        color = (255, 240, 80) if lamp_hover else (int(220 + 35 * blink), int(220 + 35 * blink), int(120 * blink))
    pygame.draw.circle(surface, (255, 255, 180), LAMP_RECT.center, 24 + pulse)
    pygame.draw.circle(surface, color, LAMP_RECT.center, 16 + pulse // 2)
    pygame.draw.circle(surface, WHITE, (LAMP_RECT.centerx - 6, LAMP_RECT.centery - 6), 4)


def draw_flash_overlay(surface):
#   Σχεδιάζει το flash overlay για animations.
#   Χρησιμοποιείται για error (κόκκινο) και success (πράσινο) effects.
#   Το alpha μειώνεται με τον χρόνο για fade-out.
    if flash_color and flash_time > 0:
        alpha = min(100, flash_time // 2)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((*flash_color, alpha))
        surface.blit(overlay, (0, 0))


def draw_success_overlay(surface, current_time):
#   Σχεδιάζει το overlay επιτυχίας με αστέρια.
#   - Λευκό overlay για έμφαση
#   - Μήνυμα "PUZZLE ΛΥΘΗΚΕ!"
#   - Αστέρια που εμφανίζονται διαδοχικά
#   - Ηχητικά effects για κάθε αστέρι
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((255, 255, 255, 140))
    surface.blit(overlay, (0, 0))
    elapsed = current_time - success_time
    surface.blit(big_font.render("PUZZLE ΛΥΘΗΚΕ!", True, GREEN), (270, HEIGHT // 2 - 80))
    surface.blit(font.render("ΣΩΣΤΑ! ΜΠΡΑΒΟ!", True, DARK_GREEN), (330, HEIGHT // 2 - 35))
    stars_to_show = min(success_stars, int(elapsed / 400) + 1)
    draw_stars(surface, WIDTH // 2 - 40, HEIGHT // 2 + 10, stars_to_show, size=30, spacing=40)
    if stars_to_show > 0 and elapsed < 500:
        play_sound("star")
    hints = [
        "*** = 1η προσπάθεια & χωρίς hint",
        "** = χωρίς hint",
        "* = ολοκλήρωση",
    ]
    for i, h in enumerate(hints):
        surface.blit(small_font.render(h, True, DARK_GRAY), (310, HEIGHT // 2 + 60 + i * 20))


# =========================
# RUN CODE
# =========================

def try_run_code():
#   Τρέχει τον κώδικα του χρήστη και χειρίζεται το αποτέλεσμα.
#   Διαδικασία:
#   1. Παίρνει τον κώδικα από τον editor
#   2. Τρέχει run_user_code για εκτέλεση και έλεγχο
#   3. Αν επιτυχία:
#      - Υπολογίζει αστέρια βάσει προσπαθειών
#      - Ενεργοποιεί success effects
#      - Αποθηκεύει το score
#   4. Αν αποτυχία:
#      - Αυξάνει wrong attempts
#      - Ξεκλειδώνει hint μετά από 2 λάθη
#      - Ενεργοποιεί error effects
    global success, success_time, wrong_attempts, hint_unlocked, hint_visible
    global message, message_time, output_text, output_feedback, output_scroll
    global success_stars, level_stars

    level = levels[level_index]
    code = get_code()
    play_sound("run")

    ok, out, err = run_user_code(code, level["check"])
    output_text = out
    output_feedback = err or ""
    output_scroll = 0
    clamp_output_scroll()

    if ok:
        stars = calculate_stars()
        success_stars = stars
        level_stars[level_index] = max(level_stars[level_index], stars)
        success = True
        success_time = pygame.time.get_ticks()
        hint_unlocked = False
        hint_visible = False
        message = "ΣΩΣΤΑ!"
        message_time = pygame.time.get_ticks()
        trigger_success_fx()
    else:
        wrong_attempts += 1
        message = "ΛΑΘΟΣ! ΞΑΝΑΠΡΟΣΠΑΘΗΣΕ"
        message_time = pygame.time.get_ticks()
        if wrong_attempts >= 2:
            hint_unlocked = True
        trigger_error_fx()


# =========================
# MAIN LOOP
# =========================

running = True
prev_time = pygame.time.get_ticks()

while running:
    current_time = pygame.time.get_ticks()
    dt = current_time - prev_time
    prev_time = current_time

    update_animations(dt)
    update_particles()

    screen.fill(LIGHT_BLUE)
    if level_index >= len(levels):
        state = "win"
        level_index = len(levels) - 1

    level = levels[level_index]

    if state != "intro" and state != "win":
        draw_progress_bar(screen)
        draw_quest_map(screen)
        screen.blit(big_font.render(f"LEVEL {level_index + 1}", True, BLACK), (20, 8))
        screen.blit(small_font.render(level["quest_title"], True, DARK_GREEN), (20, 44))
        screen.blit(small_font.render(f"Έννοια: {level['concept']}", True, DARK_GRAY), (20, 62))

        char_x = 75 + shake_x
        char_y = EDITOR_Y + 95
        draw_reddy(screen, 95, 150, reddy_bounce, happy=success)

    if state == "intro":
        shadow_color = (80, 80, 80)
        screen.blit(title_font.render("Reddy's Quest:", True, shadow_color), (332, 52))
        screen.blit(title_font.render("Against Python", True, shadow_color), (372, 112))
        screen.blit(title_font.render("Reddy's Quest:", True, DARK_GREEN), (330, 50))
        screen.blit(title_font.render("Against Python", True, RED), (370, 110))

        intro_story = (
            "Ο Reddy είναι ένας μικρός προγραμματιστής που θέλει να φτάσει στον "
            "Πύργο της Python, όπου βρίσκεται ο Κρύσταλλος της Γνώσης. Για να "
            "ανοίξει ο δρόμος, πρέπει να λύσει 8 προγραμματιστικά puzzles. "
            "Κάθε puzzle του διδάσκει μια νέα έννοια της Python και τον "
            "φέρνει πιο κοντά στον τελικό του στόχο!"
        )
        story_rect = pygame.Rect(300, 200, 550, 150)
        draw_wrapped_multiline(screen, intro_story, story_rect, font, BLACK, 26)

        start_font = pygame.font.SysFont("arial", 28, bold=True)
        screen.blit(start_font.render("Πάτα SPACE για να ξεκινήσεις", True, BLUE), (410, 400))
        draw_reddy(screen, 160, 280, bounce=0.3)

    elif state == "game":
        if success:
            draw_success_overlay(screen, current_time)
            if current_time - success_time > 2200:
                success = False
                reset_hint_state()
                phase = "dialogue"
                level_index += 1
                reset_editor()
                particles.clear()
                if level_index >= len(levels):
                    state = "win"

        elif phase == "dialogue":
            banner = pygame.Rect(200, 100, 680, 36)
            pygame.draw.rect(screen, QUEST_GOLD, banner, border_radius=8)
            screen.blit(quest_font.render(level["quest_title"], True, DARK_GREEN), (210, 106))
            bubble = pygame.Rect(200, 145, 680, 100)
            pygame.draw.rect(screen, PINK, bubble, border_radius=15)
            pygame.draw.rect(screen, DARK_GREEN, bubble, 3, border_radius=15)
            draw_text(screen, level["dialogue"], BLACK, bubble, font)
            screen.blit(font.render("SPACE για να ξεκινήσει το puzzle", True, BLACK), (220, 260))

        elif phase == "question":
            quest_banner = pygame.Rect(200, HEADER_HEIGHT - 6, 680, 28)
            pygame.draw.rect(screen, QUEST_GOLD, quest_banner, border_radius=6)
            screen.blit(quest_font.render(level["quest_title"], True, DARK_GREEN), (210, HEADER_HEIGHT - 2))

            pygame.draw.rect(screen, PINK, QUESTION_RECT, border_radius=15)
            pygame.draw.rect(screen, DARK_GREEN, QUESTION_RECT, 3, border_radius=15)
            screen.blit(
                small_font.render("PUZZLE", True, DARK_GREEN),
                (QUESTION_RECT.x, QUESTION_RECT.y - LABEL_ABOVE),
            )
            draw_wrapped_multiline(screen, level["question"], QUESTION_RECT, font, BLACK, 22)

            draw_puzzle_visual(screen, level)
            draw_expected_panel(screen, level["expected"])
            draw_editor(screen)
            draw_output_panel(screen)
            draw_bridge_from_output(screen)

            pygame.draw.rect(screen, BLUE, RUN_BTN, border_radius=6)
            screen.blit(font.render("RUN", True, WHITE), (RUN_BTN.x + 22, RUN_BTN.y + 6))

            draw_lamp(screen, level)

            if message and current_time - message_time < 2500:
                msg_color = GREEN if "ΣΩΣΤΑ" in message else RED
                screen.blit(font.render(message, True, msg_color), (200, MESSAGE_Y))

            if output_feedback and current_time - message_time < 2500:
                draw_wrapped_multiline(
                    screen, output_feedback.strip(),
                    pygame.Rect(200, FEEDBACK_Y, 635, 50), small_font, RED, 18,
                )


    elif state == "win":
        screen.blit(big_font.render("Ο ΠΥΡΓΟΣ ΤΗΣ PYTHON!", True, BLUE), (260, 40))
        win_story = (
            "Συγχαρητήρια! Ο Reddy κατάφερε να φτάσει στον Πύργο της Python, "
            "και να συλλέξει τον περίφημο Κρύσταλλος της Γνώσης. "
            "Λύνοντας όλα τα puzzles έμαθε τις βασικές έννοιες της Python: μεταβλητές, "
            "αριθμητικές πράξεις, συνθήκες και επαναλήψεις. Το ταξίδι ολοκληρώθηκε, "
            "αλλά η εκμάθηση του προγραμματισμού μόλις ξεκίνησε!"

        )

        win_rect = pygame.Rect(200, 100, 650, 150)
        draw_wrapped_multiline(screen, win_story, win_rect, font, BLACK, 26)

        # Draw Big Crystal
        crystal_pts = [(150, 200), (190, 260), (150, 320), (110, 260)]
        pygame.draw.polygon(screen, LIGHT_BLUE, crystal_pts)
        pygame.draw.polygon(screen, BLUE, crystal_pts, 3)
        draw_reddy(screen, WIDTH // 2, 300, bounce=0.5, happy=True)

        total = total_stars()
        max_stars = len(levels) * 3
        screen.blit(big_font.render(f"{total} / {max_stars}", True, GOLD), (380, 360))
        screen.blit(font.render("Συνολικά Αστέρια", True, DARK_GREEN), (350, 410))
        for i, stars in enumerate(level_stars):
            x = 220 + (i % 4) * 160
            y = 450 + (i // 4) * 40
            screen.blit(small_font.render(f"Quest {i + 1}:", True, BLACK), (x, y))
            draw_stars(screen, x + 70, y + 8, stars, size=14, spacing=18)

    draw_particles(screen)
    draw_flash_overlay(screen)

    if current_time - cursor_blink_time > 500:
        cursor_visible = not cursor_visible
        cursor_blink_time = current_time

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            ctrl = pygame.key.get_mods() & pygame.KMOD_CTRL
            shift = pygame.key.get_mods() & pygame.KMOD_SHIFT

            if state == "intro" and event.key == pygame.K_SPACE:
                state = "game"

            elif state == "game" and not success:
                if phase == "dialogue" and event.key == pygame.K_SPACE:
                    phase = "question"
                    reset_editor()
                    reset_hint_state()
                    update_layout(levels[level_index])

                elif phase == "question":
                    if event.key == pygame.K_RETURN and ctrl:
                        try_run_code()
                    elif event.key == pygame.K_RETURN:
                        newline_at_cursor()
                        cursor_visible = True
                        cursor_blink_time = current_time
                    elif event.key == pygame.K_BACKSPACE:
                        delete_before_cursor()
                        cursor_visible = True
                        cursor_blink_time = current_time
                    elif event.key == pygame.K_DELETE:
                        delete_after_cursor()
                    elif event.key == pygame.K_TAB:
                        insert_text("    ")
                        cursor_visible = True
                        cursor_blink_time = current_time
                    elif event.key == pygame.K_UP and ctrl and shift:
                        scroll_output(-1)
                    elif event.key == pygame.K_DOWN and ctrl and shift:
                        scroll_output(1)
                    elif event.key == pygame.K_UP and ctrl:
                        scroll_editor(-1)
                    elif event.key == pygame.K_DOWN and ctrl:
                        scroll_editor(1)
                    elif event.key == pygame.K_UP:
                        move_cursor(0, -1)
                    elif event.key == pygame.K_DOWN:
                        move_cursor(0, 1)
                    elif event.key == pygame.K_LEFT:
                        move_cursor(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        move_cursor(1, 0)
                    elif event.key == pygame.K_HOME:
                        cursor_col = 0
                    elif event.key == pygame.K_END:
                        cursor_col = len(user_lines[cursor_line])
                    elif event.unicode and event.unicode.isprintable():
                        insert_text(event.unicode)
                        cursor_visible = True
                        cursor_blink_time = current_time

        if event.type == pygame.MOUSEBUTTONDOWN:
            if state == "game" and phase == "question" and not success:
                if hint_unlocked and LAMP_RECT.collidepoint(event.pos):
                    hint_visible = not hint_visible
                    if hint_visible:
                        hint_used_this_level = True
                if RUN_BTN.collidepoint(event.pos):
                    try_run_code()

        if event.type == pygame.MOUSEWHEEL and state == "game" and phase == "question":
            mouse_pos = pygame.mouse.get_pos()
            if OUTPUT_RECT.collidepoint(mouse_pos):
                scroll_output(-event.y)
            else:
                scroll_editor(-event.y)
            if hint_visible and hint_unlocked:
                mx, my = pygame.mouse.get_pos()
                hint_rect, _ = get_hint_rect(level)
                if hint_rect.collidepoint((mx, my)):
                    draw_hint_panel.scroll -= event.y
                    draw_hint_panel.scroll = max(0, draw_hint_panel.scroll)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()