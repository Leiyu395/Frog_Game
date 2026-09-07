import turtle
from turtle import bgpic


# ------------------ Constants / Config ------------------
# Screen dimensions in pixels
GAME_WIDTH, GAME_HEIGHT = 900, 600
FPS = 60  # Frames per second - how many times the game updates each second

# Physics constants - these control how the player moves
GRAVITY = -0.7  # Negative because it pulls downward (vertical physics still uses original per-frame values)
MOVE_SPEED = 300.0  # Horizontal movement speed in pixels per second (will be scaled by dt in update())
JUMP_SPEED = 12.5  # Initial upward velocity when jumping
MAX_FALL_SPEED = -18.0  # Terminal velocity - prevents falling too fast

# Player dimensions (a square)
PLAYER_W, PLAYER_H = 20, 20
START_TIME = 60  # Starting time in seconds for each level

#Backround image
turtle.register_shape("The_Frog_Backround.gif")
bgpic("The_Frog_Backround.gif")

#Player images
turtle.register_shape("Idle.gif")
turtle.register_shape("Idle-right.gif")
turtle.register_shape("Jump.gif")
turtle.register_shape("Jump-right.gif")
turtle.register_shape("Fall.gif")
turtle.register_shape("Fall-right.gif")

#Platform images
turtle.register_shape("tile_0000.gif")

# Color scheme for the game - change these to customize the look!
THEME = {
    "title": "Platformer Game",
    "goal_color": "#2ECC71",  # Green goal
    "hazard_color": "#E74C3C",  # Red hazards
    "ui_color": "black",  # Text color
}

# ------------------ Screen / Turtles ------------------
# Set up the game window
screen = turtle.Screen()
screen.setup(GAME_WIDTH, GAME_HEIGHT)
screen.title(THEME["title"])
screen.tracer(0)  # Turn off automatic animation - we'll update manually for smooth movement

# Create a turtle for drawing the world (platforms, hazards, goal)
pen = turtle.Turtle(visible=False)  # world drawer
pen.hideturtle()
pen.penup()
pen.speed(0)

# Create a turtle for drawing UI elements (score, timer, messages)
ui = turtle.Turtle(visible=False)   # UI text
ui.hideturtle()
ui.penup()
ui.color(THEME["ui_color"])

# TODO: Task 3 - Load a player image
# Create the player turtle - this is what you control
player = turtle.Turtle()            # player
player.shape("Idle.gif")
player.shapesize(stretch_wid=PLAYER_H / 20, stretch_len=PLAYER_W / 20)  # Default turtle is 20x20, so we scale it
player.penup()
player.speed(0)

# ------------------ Shared State dict ------------------
# This dictionary holds ALL the game's current information
STATE = {
    # References to our turtle objects
    "screen": screen,
    "pen": pen,
    "ui": ui,
    "player": player,

    # Track which keys are currently pressed
    "keys": {"left": False, "right": False, "jump": False},

    # Level data and tracking
    "levels": [],  # Will be filled by load_levels()
    "current_level": 0,  # Which level we're currently playing

    # Player physics - velocity in x and y directions
    "vx": 0.0, "vy": 0.0,
    "grounded": True,  # Is the player standing on a platform?

    # Game progression
    "score": 0,
    "time_left": START_TIME,
    "frames": 0,  # Total frames rendered (used for timing)
    "game_over": False,  # Has the game ended?
    "win": False,  # Did the player win?
}

# ------------------ Utility Functions ------------------
def bound_value(val, lo, hi):
    """Keep a value within a range (prevents player from leaving screen)"""
    return max(lo, min(hi, val))

def calculate_overlap(object_a, object_b):
    """
    Check if two rectangles overlap (collision detection).
    Each object is a dict with x, y (center position), w (width), h (height).
    Returns True if they're touching, False otherwise.
    """
    return (abs(object_a["x"] - object_b["x"]) * 2 < (object_a["w"] + object_b["w"])) and \
           (abs(object_a["y"] - object_b["y"]) * 2 < (object_a["h"] + object_b["h"]))

def player_box():
    """
    Create a rectangle dictionary for the player's current position.
    Used for collision detection.
    """
    p = STATE["player"]
    return {"x": p.xcor(), "y": p.ycor(), "w": PLAYER_W, "h": PLAYER_H}

def draw_rect(x, y, w, h, color):
    """
    Draw a filled rectangle at position (x, y) with given width, height, and color.
    Used for drawing platforms, hazards, and goals.
    """
    pen = STATE["pen"]
    pen.color(color)
    pen.fillcolor(color)
    pen.penup()
    pen.goto(x - w / 2, y - h / 2) # Move to bottom-left corner
    pen.setheading(0) # Face right
    pen.pendown()
    pen.begin_fill()
    # Draw a rectangle by moving forward and turning left
    for _ in range(2):
        pen.forward(w)
        pen.left(90)
        pen.forward(h)
        pen.left(90)
    pen.end_fill()
    pen.penup()

def initialize_platform_blocks():
    """Create a pool of platform blocks that we can reuse"""
    if "platform_blocks_pool" not in STATE:
        STATE["platform_blocks_pool"] = []
        STATE["platform_blocks_in_use"] = []
        # Pre-create a pool of blocks - adjust number based on maximum needed
        for _ in range(100):  # Adjust this number based on your maximum platform width
            block = turtle.Turtle()
            block.penup()
            block.shape("tile_0000.gif")
            block.hideturtle()
            STATE["platform_blocks_pool"].append(block)

def draw_image(x, y, w, image_path = "tile_0000.gif", tile_size=18):
    if "platform_blocks_pool" not in STATE:
        initialize_platform_blocks()
    
    tiles = int(w // tile_size)
    start_x = x - (w / 2) + (tile_size / 2)
    
    # Reuse blocks from the pool
    for i in range(tiles):
        if STATE["platform_blocks_pool"]:
            block = STATE["platform_blocks_pool"].pop()
            block.goto(start_x + i * tile_size, y)
            block.showturtle()
            STATE["platform_blocks_in_use"].append(block)


# ------------------ Level Data ------------------
def load_levels():
    """
    Create the level layouts. Each level has platforms, hazards, and a goal.
    Add more levels here to extend the game!
    """
    # Level 1
    STATE["levels"].append({
        "platforms": [
            {"x": 0, "y": -250, "w": GAME_WIDTH + 20, "h": 20},   # ground - extra wide so player can't fall off
            {"x": -220, "y": -160, "w": 140, "h": 20},  # First floating platform
            {"x":  20, "y":   -80, "w": 120, "h": 20},  # Second floating platform
        ],
        "hazards": [
            {"x": -80, "y": -140, "w": 60, "h": 20},  # Red hazard - don't touch!
        ],
        "goal": {}  # Will be set below
    })

    # Place the goal at the end of the last platform
    last = STATE["levels"][len(STATE["levels"]) - 1]["platforms"][-1]
    STATE["levels"][len(STATE["levels"]) - 1]["goal"] = {"x": last["x"] + last["w"] / 2 - 20, "y": last["y"] + 40, "w": 40, "h": 40}

    # TODO: Task 4 - Add more levels
    # Level 2
    STATE["levels"].append({
        "platforms": [
            {"x": 0, "y": -250, "w": GAME_WIDTH + 20, "h": 20},   # ground - extra wide so player can't fall off
            {"x": -300, "y": -160, "w": 100, "h": 20},  # First platform
            {"x": -100, "y": -80, "w": 100, "h": 20},   # Second platform
            {"x": 100, "y": 0, "w": 100, "h": 20},      # Third platform
            {"x": 300, "y": 80, "w": 100, "h": 20},     # Fourth platform
        ],
        "hazards": [
            {"x": -200, "y": -140, "w": 60, "h": 20},  # First hazard
            {"x": 0, "y": -60, "w": 60, "h": 20},      # Second hazard
            {"x": 200, "y": 20, "w": 60, "h": 20},     # Third hazard
        ],
        "goal": {}  # Will be set below
    })

    # Place the goal at the end of the last platform
    last = STATE["levels"][len(STATE["levels"]) - 1]["platforms"][-1]
    STATE["levels"][len(STATE["levels"]) - 1]["goal"] = {"x": last["x"] + last["w"] / 2 - 20, "y": last["y"] + 40, "w": 40, "h": 40}

# ------------------ Lifecycle ------------------
def reset_positions():
    """
    Move the player back to the starting position.
    Called at the beginning and when hitting hazards.
    """
    # Spawn standing on the ground so jump works immediately
    player = STATE["player"]
    player.goto(-380, -230)  # ground top (-240) + half player (10)
    STATE["vx"], STATE["vy"] = 0.0, 0.0  # Stop all movement
    STATE["grounded"] = True  # Player is on the ground
    STATE["can_double_jump"] = False

def reset():
    """
    Reset the entire game to the beginning.
    Called when pressing 'R' to restart.
    """
    # TODO: Task 2 - Reset the score, time left, frame, game_over and win in STATE,
    #  and reset the player position (hint: there is a function for this)
    STATE["keys"]["r"] = True
    STATE["score"] = 0
    STATE["time_left"] = START_TIME
    STATE["frames"] = 0
    STATE["game_over"] = False
    STATE["win"] = False
    reset_positions()
    pass

# ------------------ Input Handlers ------------------
def on_left_down():
    """Called when left arrow key is pressed"""
    # TODO: Task 1 - Replace "pass" with your left movement functionality
    STATE["keys"]["left"] = True

def on_left_up():
    """Called when left arrow key is released"""
    # TODO: Task 1 - Replace "pass" with your left movement functionality
    STATE["keys"]["left"] = False

def on_right_down():
    """Called when right arrow key is pressed"""
    STATE["keys"]["right"] = True

def on_right_up():
    """Called when right arrow key is released"""
    STATE["keys"]["right"] = False

def on_jump():
    """Called when space or up arrow is pressed"""
    if STATE["grounded"]:
        STATE["keys"]["jump"] = True

def on_restart():
    """Called when 'R' key is pressed"""
    reset()
    update()  # resume loop if it had stopped

def on_continue():
    """Called when 'C' key is pressed to go to next level"""
    if STATE["goal"] and not STATE["win"]:
        reset_positions()
        STATE["time_left"] = START_TIME
        STATE["current_level"] += 1
        STATE["goal"] = False
        STATE["frames"] = 0
        STATE["game_over"] = False
        update()

# ------------------ Main Update Loop ------------------
def update():
    """
    This is the heart of the game! Called 60 times per second.
    Handles input, physics, collision, drawing, and game logic.
    """
    screen = STATE["screen"]
    player = STATE["player"]
    current_level = STATE["current_level"]

    # --- INPUT PHASE ---
    # Convert key presses into horizontal velocity (frame-rate independent)
    dt = 1.0 / FPS
    STATE["vx"] = 0.0
    if STATE["keys"]["left"]:
        STATE["vx"] -= MOVE_SPEED * dt
    if STATE["keys"]["right"]:
        STATE["vx"] += MOVE_SPEED * dt

    #Check direction
    if STATE["vx"] < 0:
        if STATE["grounded"] == True:
            player.shape("Idle.gif")
        else:
            if STATE["vy"] > 0:
                player.shape("Jump.gif")
            elif STATE["vy"] < 0:
                player.shape("Fall.gif")
    else:
        if STATE ["grounded"] == True:
           player.shape("Idle-right.gif")
        else:
            if STATE["vy"] > 0:
                player.shape("Jump-right.gif")
            elif STATE["vy"] < 0:
                player.shape("Fall-right.gif")

    # Handle jumping (only works when grounded)
    if STATE["keys"]["jump"] and STATE["grounded"]:
        STATE["vy"] = JUMP_SPEED
        STATE["keys"]["jump"] = False
        STATE["grounded"] = False

    # --- PHYSICS PHASE ---
    # Apply gravity every frame
    STATE["vy"] = max(STATE["vy"] + GRAVITY, MAX_FALL_SPEED)

    # Calculate new position based on velocity
    nx = player.xcor() + STATE["vx"]
    ny = player.ycor() + STATE["vy"]

    # --- COLLISION DETECTION & RESOLUTION ---
    # Horizontal sweep & resolve (move left/right and check for wall collisions)
    player.setx(nx)
    player_icon = player_box()
    for platform in STATE["levels"][current_level]["platforms"]:
        if calculate_overlap(player_icon, platform):
            # We hit a platform from the side - push player out
            dx = platform["x"] - player_icon["x"]
            overlap_x = (platform["w"] + player_icon["w"]) / 2 - abs(dx)
            if dx > 0:
                player.setx(player.xcor() - overlap_x)  # Platform is to the right
            else:
                player.setx(player.xcor() + overlap_x)  # Platform is to the left
            player_icon = player_box()

    # Vertical sweep & resolve (move up/down and check for platform collisions)
    player.sety(ny)
    player_icon = player_box()

    # Check if we're on the ground platform (special check for grounded state)
    if calculate_overlap(player_icon, STATE["levels"][current_level]["platforms"][0]):
        STATE["grounded"] = True

    # Check all platforms for vertical collisions
    for platform in STATE["levels"][current_level]["platforms"]:
        if calculate_overlap(player_icon, platform):
            dy = platform["y"] - player_icon["y"]
            overlap_y = (platform["h"] + player_icon["h"]) / 2 - abs(dy)
            if dy > 0:
                # Hit underside of platform
                player.sety(player.ycor() - overlap_y)
                STATE["vy"] = 0
            else:
                # Land on top of platform
                player.sety(player.ycor() + overlap_y)
                STATE["vy"] = 0
                STATE["grounded"] = True
            player_icon = player_box()

    # Keep player within screen boundaries
    player.setx(bound_value(player.xcor(),
                            -GAME_WIDTH / 2 + PLAYER_W / 2, GAME_WIDTH / 2 - PLAYER_W / 2))
    player.sety(bound_value(player.ycor(),
                            -GAME_HEIGHT / 2 + PLAYER_H / 2, GAME_HEIGHT / 2 - PLAYER_H / 2))

    # --- GAME LOGIC ---
    # Check if player touched a hazard (red rectangles)
    player_icon = player_box()
    for h in STATE["levels"][current_level]["hazards"]:
        if calculate_overlap(player_icon, h):
            reset_positions()  # Respawn at start
            break

    # Check if player reached the goal
    if calculate_overlap(player_icon, STATE["levels"][current_level]["goal"]):
        STATE["goal"] = True
        STATE["game_over"] = True

    # --- DRAWING PHASE ---
    # Clear previous drawings (but not the screen itself)
    STATE["pen"].clear()
    STATE["ui"].clear()

    # Return used blocks to the pool
    if "platform_blocks_in_use" in STATE:
        for block in STATE["platform_blocks_in_use"]:
            block.hideturtle()
            STATE["platform_blocks_pool"].append(block)
        STATE["platform_blocks_in_use"] = []

    # Draw all platforms
    for platform in STATE["levels"][current_level]["platforms"]:
        draw_image(platform["x"], platform["y"], platform["w"], image_path = "tile_0000.gif")

    # Draw all hazards
    for h in STATE["levels"][current_level]["hazards"]:
        draw_rect(h["x"], h["y"], h["w"], h["h"], THEME["hazard_color"])

    # Draw the goal
    g = STATE["levels"][current_level]["goal"]
    draw_rect(g["x"], g["y"], g["w"], g["h"], THEME["goal_color"])

    # --- UI PHASE ---
    # Update timer (once per second)
    if (STATE["frames"] % FPS == 0) and (not STATE["game_over"]):
        STATE["time_left"] -= 1
        if STATE["time_left"] <= 0:
            STATE["game_over"] = True
    STATE["frames"] += 1

    # Draw timer in top-left
    STATE["ui"].goto(-GAME_WIDTH / 2 + 10, GAME_HEIGHT / 2 - 30)
    STATE["ui"].write(f"Time: {STATE['time_left']:>2}s", font=("Arial", 14, "normal"))

    # Show controls for the first 7 seconds
    if STATE["frames"] < 7 * FPS and not STATE["game_over"]:
        STATE["ui"].goto(0, GAME_HEIGHT / 2 - 30)
        STATE["ui"].write("← → move   Space/↑ jump   R restart",
                          align="center", font=("Arial", 12, "normal"))

    # Show game over / win messages
    if STATE["game_over"]:
        STATE["ui"].goto(0, 20)
        if STATE["goal"]:
            if current_level >= len(STATE["levels"]) - 1:
                STATE["win"] = True
                msg = "You Finished the game! 🎉🎉🎉🎉 Press R to restart"
            else:
                msg = "You Reached the Goal! 🎉 Press c to continue"
        else:
            msg = "Time's Up! ⏰ Press R to restart"
        STATE["ui"].write(msg, align="center", font=("Arial", 22, "bold"))
        STATE["ui"].goto(0, -20)

    # Update the screen with all our drawings
    screen.update()

    # Schedule next frame (only if game is still running)
    if not STATE["game_over"]:
        screen.ontimer(update, int(1000 / FPS))  # Call update again in 1/60th of a second

# ------------------ Bind Inputs ------------------
# Tell the screen to listen for keyboard input
screen.listen()
screen.onkeypress(on_jump, "space")
screen.onkeypress(on_jump, "Up")

# TODO: Task 1 - Implement Left
screen.onkeypress(on_right_down, "Right")
screen.onkeyrelease(on_right_up, "Right")

screen.onkeypress(on_left_down, "Left")
screen.onkeyrelease(on_left_up, "Left")

screen.onkeyrelease(on_restart, "r")
screen.onkeyrelease(on_continue, "c")


# ------------------ Start ------------------
# Initialize the game and start the main loop
load_levels()  # Create level data
reset_positions()  # Put player at starting position
update()  # Start the game loop
screen.mainloop()  # Keep window open and responsive