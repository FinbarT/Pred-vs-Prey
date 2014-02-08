"""
A predater vs prey simulator.

Predator eats or dies. Everyone breeds. Prey get eaten by predators

Only one event per animal per tick
"""

from random import randint
import time
import os


try:
    import curses
    CURSES_AVAILABLE = True

except ImportError:
    print("""
        For an animated output this has to be run in bash/linux
    """)
    CURSES_AVAILABLE = False


class Field(object):
    """
    A field class is an object that represents a field that will contain
    the animals
    """
    def __init__(self, size, population):
        """
        Size will dicatate the length and width of the field and Population,
        the amount of animals. This splits 50:50 predators and prey. self.area
        is a 2D list representing the field.
        """
        self.size = size
        self.area = [[0 for i in range(size)] for j in range(size)]
        self.population = population
        self.populate()
        self.data = self.get_data()
        self.screen = curses.initscr()

    def __str__(self):  
        """
        output:   ....1
                  ..1..
                  ...0.
                  .....
                  .0...
        1: predator
        0: prey
        .: vacant space
        """
        output = ""

        for j in range(self.size - 1, -1, -1):
            for i in range(self.size):
                if not self.area[i][j]:
                    output += "{:^2}".format('.') + " "
                else:
                    output += "{:^2}".format(self.area[i][j].__str__()) + " "
            output += "\n"

        return output

    def place_exists(self, coord):
        """
        Verifies if a given coordinate exists within the field
        """
        if (
            coord[0] < self.size and
            coord[1] < self.size and
            coord[0] >= 0 and 
            coord[1] >= 0
        ):
            return True
        else:
            return False

    def populate(self):
        """
        Adds the animals to the field
        """
        prey_last = True

        for i in range(self.population):
            while True:
                coord = [randint(0, self.size-1), randint(0, self.size-1)]
                if not self.area[coord[0]][coord[1]]:
                    if prey_last:
                        self.area[coord[0]][coord[1]] = Predator(coord)
                        prey_last = False
                    else:
                        self.area[coord[0]][coord[1]] = Prey(coord)
                        prey_last = True
                    break
                else:
                    continue

    def get_data(self):
        """
        Determines how many predators and how many prey are present in the
        field
        """
        get_total = lambda type_, lst: sum(
            len([j for j in i if type(j) == type_]) for i in lst
        )
        preds = get_total(Predator, self.area)
        preys = get_total(Prey, self.area)

        return "PREDATORS: {} PREY: {}".format(preds, preys)

    def to_screen(self):
        """
        Sets the animation on the screen in a bash environment and print to the 
        screen in a window environment
        """
        if CURSES_AVAILABLE:
            time.sleep(1)
            self.screen.erase()
            self.screen.addstr(str(self))
            self.screen.addstr(self.get_data())
            self.screen.refresh()
        else:
            print(self)
            print(self.get_data)

    def simulate(self, ticks):
        """
        Runs the simulation for a given number of ticks
        """
        animals_starved = 0
        animals_checked = 0
        self.to_screen()

        while ticks > 0:
            for i in range(0, self.size):
                for j in range(0, self.size):
                    if self.area[i][j] != 0:
                        if type(self.area[i][j]) == Predator:
                            self.area[i][j].hunger -= 1
                            animals_checked += 1
                            if self.area[i][j].hunger == 0:
                                self.area[i][j] = 0
                                animals_starved += 1
                            else:
                                self.area[i][j].breed_clock -= 1
                                self.area[i][j].decision(self)
                        else:
                            self.area[i][j].breed_clock -= 1
                            self.area[i][j].decision(self)
                    else:
                        continue
            self.to_screen()
            ticks -= 1


class Animal(object):
    """
    Defines a class animal 
    """
    animal_population = 0

    def __init__(
        self,
        name,
        map_id,
        position=[0, 0],
        breed_clock=3,
    ):
        self.name = name                      #pred / prey,
        self.map_id = map_id                  #1 / 0
        self.position = position              #starting postion
        self.breed_clock = breed_clock        #starts on 3 breeds and resets on 0
        self.__class__.animal_population += 1

    def __str__(self):
        return self.map_id

    def check_perimeter(self, field):
        """
        Allows the animal survey the surrounding cells for preds, prey &
        vacant space. Returns a listed break down.
        """
        get_direction = lambda a, b: (a[0] + b[0], a[1] + b[1])

        choices = {'preys': [], 'preds': [], 'vacant': []}

        north = get_direction(self.position, [-1, 0])
        north_east = get_direction(self.position, [-1, 1])
        east = get_direction(self.position, [1, 1])
        south_east = get_direction(self.position, [1, 1])
        south = get_direction(self.position, [1, 0])
        south_west = get_direction(self.position, [1, -1])
        west = get_direction(self.position, [0, -1])
        north_west = get_direction(self.position, [-1, -1])

        directions = [
            north,
            north_east,
            east,
            south_east,
            south,
            south_west,
            west,
            north_west
        ]
        for coord in directions:
            if field.place_exists(coord):
                if type(field.area[coord[0]][coord[1]]) == Prey:
                    choices['preys'].append(coord)
                elif type(field.area[coord[0]][coord[1]]) == Predator:
                    choices['preds'].append(coord)
                else:
                    choices['vacant'].append(coord)
            else:
                continue 

        return choices

    def move(self, coords, field):
        """
        moves the animal from it's present coordinates to the provided ones
        """
        x = self.position[0]
        y = self.position[1]
        self.position = coords
        field.area[coords[0]][coords[1]] = self
        field.area[x][y] = 0

        return field

    def breed(self, coord, field):
        """
        Spawns a new animal
        """
        self.breed_clock = 3
        field.area[coord[0]][coord[1]] = self.__class__(coord)

        return field

    def decision(self, field, options=0):
        """
        Allows the animal to decide what course of action to take based on 
        it's circumstances and surroundings 
        """
        if options == 0:
            options = self.check_perimeter(field)
        else:
            pass
        #Breed
        if self.breed_clock == 0:
            #if can't breed
            if (len(options['preds']) == 0 and len(options['vacant']) > 0):
                field = self.breed(
                    options['vacant'][randint(0, len(options['vacant'])-1)],
                    field
                )
            #move
            elif len(options['vacant']) > 0:
                new_pos = options['vacant'][randint(
                        0,
                        len(options['vacant'])-1
                )]
                if self.position == new_pos:
                    field = self.move(
                        options['vacant'][randint(
                            0,
                            len(options['vacant'])-1
                        )],
                        field
                    )
                else:                
                    field = self.move(new_pos, field)
            #or don't
            else:
                pass
        #Or Move
        elif len(options['vacant']) > 0:
            new_pos = options['vacant'][randint(0, len(options['vacant'])-1)]
            if self.position == new_pos:
                field = self.move(
                    options['vacant'][randint(0, len(options['vacant'])-1)],
                    field
                )
            else:                
                field = self.move(new_pos, field)
        #or do nothing
        else:
            pass            

class Predator(Animal):
    """
    Defines a predator. A subclass of Animal. Survives by eating 
    other animals or staring to death
    """
    predator_population = 0

    def __init__(
        self,
        position,
        name="predator",
        map_id="1",
    ):
        Animal.__init__(
            self,
            name,
            map_id,
            position
        )
        self.hunger = 5
        self.__class__.predator_population += 1

    def eat(self, coord, field):
        """
        Function for eating other animals and resttignn the hunger clock
        """
        self.move(coord, field)
        self.hunger = 5

        return field

    def decision(self, field):
        """
        overloading the inital animal.decision() to allow for eating
        """
        options = self.check_perimeter(field)
        if len(options['preys']) > 0:
            field = self.eat(options['preys'][0], field)
        else:
            Animal.decision(self, field, options)


class Prey(Animal):
    """
    Defines a prey, a subclass of animal
    """
    prey_population = 0

    def __init__(
        self,
        position,
        name="prey",
        map_id="0"
    ):
        Animal.__init__(
            self,
            name,
            map_id,
            position
        )
        self.__class__.prey_population += 1


def get_input(
    prompt_input,
    max_value,
    min_value=0,
    bad_input="That's not right!"
):
    '''
    handles user input read in from the console. Ensures appropriate input
    recieved
    '''
    while True:

        try:
            input_value = int(input(prompt_input))
            if input_value < min_value:
                print("Number too small")
            elif input_value <= max_value:
                break
            else:
                print(bad_input)
        except ValueError:
            print("Oops! That was not a valid number. Please try again...")

    return input_value

def main():
    #calling code
    print("Please enter the following")
    size = get_input(
        "Size (Must be 20 or less): ",
        20,
    )
    population = get_input(
        "Enter number of animals (Must be {} or less): ".format(
            int((size*size) / 2)
        ),
        int((size*size) / 2)
    )
    ticks = get_input(
        "Enter number of cycles (Must not be more than 2000: ",
        2000
    )
    island = Field(size, population)
    island.simulate(ticks)
    os._exit(0)

if __name__ == "__main__":
    main()
