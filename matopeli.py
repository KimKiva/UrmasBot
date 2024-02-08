from tkinter import *
import random 

GAME_WIDTH = 700
GAME_HEIGHT = 500
SPEED = 100
SPACE_SIZE = 50
BODY_PARTS = 3
SNAKE_COLOR = "#00FF00"
FOOD_COLOR = "#FF0000"
BACKGROUND_COLOR = "#000000"
HIGH_SCORE = 0

class Snake:
   def __init__(self):
      self.body_size = BODY_PARTS
      self.coordinates = []
      self.squares = []

      for i in range(0, BODY_PARTS):
        self.coordinates.append([0, 0])

      for x, y in self.coordinates:
        square = canvas.create_rectangle(x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill=SNAKE_COLOR)
        self.squares.append(square)

class Food:

    def __init__(self):
      
        x = random.randint(0, (GAME_WIDTH / SPACE_SIZE-1)) * SPACE_SIZE
        y = random.randint(0, (GAME_HEIGHT / SPACE_SIZE-1)) * SPACE_SIZE

        self.coordinates = [x, y]

        canvas.create_oval(x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill=FOOD_COLOR, tag="food")

def next_turn(snake, food):

  x, y = snake.coordinates[0]

  if direction == "up":
    y -= SPACE_SIZE
     
  elif direction == "down":
    y += SPACE_SIZE
     
  elif direction == "left":
    x -= SPACE_SIZE
     
  elif direction == "right":
    x += SPACE_SIZE

  snake.coordinates.insert(0, (x,y))

  square = canvas.create_rectangle(x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill=SNAKE_COLOR)

  snake.squares.insert(0, square)

  if x == food.coordinates[0] and y == food.coordinates[1]:
      global score, high_score
      score += 1
      if score > high_score:
        high_score = score
      label.config(text="Pisteet:{}   |   Ennätys:{}".format(score, high_score))
      canvas.delete("food")
      food = Food()
  else:
        del snake.coordinates[-1]
        canvas.delete(snake.squares[-1])
        del snake.squares[-1]

  if check_collision(snake):
        game_over()
  else:
        window.after(SPEED, next_turn, snake, food)

def change_direection(new_direction):
  
  global direction

  if new_direction == 'left':
      if direction != 'right':
        direction = new_direction
  elif new_direction == 'right':
      if direction != 'left':
          direction = new_direction
  elif new_direction == 'up':
      if direction != 'down':
          direction = new_direction
  elif new_direction == 'down':
      if direction != 'up':
          direction = new_direction

def check_collision(snake):
  
  x, y = snake.coordinates[0]

  if x < 0 or x >= GAME_WIDTH:
     return True
  elif y < 0 or y>= GAME_HEIGHT:
     return True
  
  for body_part in snake.coordinates[1:]:
     if x == body_part[0] and y == body_part[1]:
      print("PELI PÄÄTTYI")
      return True
      
  return False

def game_over():
  
  canvas.delete(ALL)
  canvas.create_text(canvas.winfo_width()/2, canvas.winfo_height()/2, font=('arial', 70), text="PELI PÄÄTTYI", fill="red", tag="game_over")

window = Tk()
window.title("Matopeli")
window.resizable(False, False)

score = 0
high_score = 0
direction = 'down'

label = Label(window, text="Pisteet:{}   |   Ennätys:{}".format(score, high_score), font=('arial', 40))
label.pack()

canvas = Canvas(window, bg=BACKGROUND_COLOR, height=GAME_HEIGHT, width=GAME_WIDTH)
canvas.pack()

def restart_game():
    global score, high_score, direction, snake, food
  
    score = 0
    direction = 'down'
    snake = Snake()
    food = Food()
    if score > high_score:
        high_score = score
    label.config(text="Pisteet:{}   |  Ennätys:{}".format(score, high_score))
    canvas.delete('game_over')
    difficultylevel()
    next_turn(snake, food)
    window.config(menu=game_menu)

def difficultylevel(): 
    global SPEED

    if difficulty_var.get() == "Helppo":
        SPEED = 100
    elif difficulty_var.get() == "Keskitaso":
        SPEED = 70
    elif difficulty_var.get() == "Vaikea":
        SPEED = 50

def exit_game():
   exit()
   
try:
    # Päivitä ikkuna ja määritä sen geometria
    window.update()
    window_width = window.winfo_width()
    window_height = window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = int(screen_width/2) - (window_width/2)
    y = int(screen_height/2) - (window_height/2)
    window.geometry(f"{window_width}x{window_height}+{x}+{y}")

except Exception as e:
    print(e)

window.bind('<Left>', lambda event: change_direection('left'))
window.bind('<Right>', lambda event: change_direection('right'))
window.bind('<Up>', lambda event: change_direection('up'))
window.bind('<Down>', lambda event: change_direection('down'))

snake = Snake()
food = Food()

next_turn(snake, food)

game_menu = Menu(window)
game_menu.add_command(label="Uusi peli", command=restart_game)
difficulty_menu = Menu(game_menu, tearoff=0)
game_menu.add_cascade(label="Vaikeustaso", menu=difficulty_menu)
difficulty_var = StringVar(window)
difficulty_var.set("Helppo")
difficulty_options = ["Helppo", "Keskitaso", "Vaikea"]
difficulty_menu.add_radiobutton(label="Helppo", variable=difficulty_var, value="Helppo")
difficulty_menu.add_radiobutton(label="Keskitaso", variable=difficulty_var, value="Keskitaso")
difficulty_menu.add_radiobutton(label="Vaikea", variable=difficulty_var, value="Vaikea")
game_menu.add_command(label="Lopeta", command=exit_game)
window.config(menu=game_menu)

window.mainloop()