assignments = []

def cross(A, B):
    "Cross product of elements in A and elements in B."
    return [s+t for s in A for t in B]

rows = 'ABCDEFGHI'
cols = '123456789'
boxes = cross(rows, cols)
row_units = [cross(r, cols) for r in rows]
column_units = [cross(rows, c) for c in cols]
square_units = [cross(rs, cs) for rs in ('ABC','DEF','GHI') for cs in ('123','456','789')]
#adding diagonal units for both diagonal directions
diagonals = [[rows[i] + cols[i] for i in range(len(rows))] ,[rows[i] + cols[8-i] for i in range(len(rows))]]
#add diagonals units to the unitlist so the units and peers in diagonal element has additional constraint propagation
unitlist = row_units + column_units + square_units + diagonals
units = dict((s, [u for u in unitlist if s in u]) for s in boxes)
peers = dict((s, set(sum(units[s],[]))-set([s])) for s in boxes)


def assign_value(values, box, value):
    """
    Please use this function to update your values dictionary!
    Assigns a value to a given box. If it updates the board record it.
    """

    # Don't waste memory appending actions that don't actually change any values
    if values[box] == value:
        return values

    values[box] = value
    if len(value) == 1:
        assignments.append(values.copy())
    return values

#find all the values that length is 2, for values reduced for every loop,first find if the box value to solved length less than 2.
#traverse all 2 length values , find row_units,column_units,square_units if each unit contain the naked_twins
def naked_twins(values):
    """Eliminate values using the naked twins strategy.
    Args:
        values(dict): a dictionary of the form {'box_name': '123456789', ...}

    Returns:
        the values dictionary with the naked twins eliminated from peers.
    """

    # Find all instances of naked twins
    # Eliminate the naked twins as possibilities for their peers

    values_l2 = [box for box in values.keys() if len(values[box]) == 2]
    for box in values_l2:
        if(len(values[box]) < 2):
            continue
        values = naked_twins_reduce(values,box,row_units)
        values = naked_twins_reduce(values,box,column_units)
        values = naked_twins_reduce(values,box,square_units)
    return values

#function for naked_twins to find all kinds of units  and remove  naked twins digit
def naked_twins_reduce(values,box,units):
    flag = 0
    index = -1
    unit = [unit for unit in units if box in unit]
    for peer in unit[0]:
        if(peer == box):
            continue
        if(values[peer] == values[box]):
            flag = 1
            index = peer
            break
    if(flag == 1):
        digit1 = values[box][0]
        digit2 = values[box][1]
        for peer in unit[0]:
            if(peer not in (box,index)):
                    values[peer] = values[peer].replace(digit1,'')
                    values[peer] = values[peer].replace(digit2,'')
    return values

def grid_values(grid):
    """
    Convert grid into a dict of {square: char} with '123456789' for empties.
    Args:
        grid(string) - A grid in string form.
    Returns:
        A grid in dictionary form
            Keys: The boxes, e.g., 'A1'
            Values: The value in each box, e.g., '8'. If the box has no value, then the value will be '123456789'.
    """
    res = {}
    for i in range(len(grid)):
        if(grid[i] == '.'):
            res[boxes[i]] = '123456789'
        else:
            res[boxes[i]] = grid[i]
    return res

def display(values):
    """
    Display the values as a 2-D grid.
    Args:
        values(dict): The sudoku in dictionary form
    """
    print()
    width = 1+max(len(values[s]) for s in boxes)
    line = '+'.join(['-'*(width*3)]*3)
    for r in rows:
         print(''.join(values[r+c].center(width)+('|' if c in '36' else '')
              for c in cols))
         if r in 'CF': print(line)
    return 

# the function will iterate over all the boxes in the puzzle that only have one value assigned to them, and it will remove this value from every one of its peers.
def eliminate(values):
    solved_values = [box for box in values.keys() if len(values[box]) == 1]
    for box in solved_values:
        digit = values[box]
        for peer in peers[box]:
            values[peer] = values[peer].replace(digit,'')
    return values

# if there is only one box in a unit which would allow a certain digit, then that box must be assigned that digit
def only_choice(values):
    for unit in unitlist:
        for digit in '123456789':
            dplaces = [box for box in unit if digit in values[box]]
            if len(dplaces) == 1:
                values[dplaces[0]] = digit
    return values

# combine the functions eliminate,naked_twins,only_choice in a loop and record if values has change, function stop if the puzzle gets solved,if  the function doesn't solve the sudoku return false
def reduce_puzzle(values):
    stalled = False
    while not stalled:
        solved_values_before = len([box for box in values.keys() if len(values[box]) == 1])
        eliminate(values)
        naked_twins(values)
        only_choice(values)
        solved_values_after = len([box for box in values.keys() if len(values[box]) == 1])
        stalled = solved_values_before == solved_values_after
        if len([box for box in values.keys() if len(values[box]) == 0]):
            return False
    return values

# pick a box with a minimal number of possible values. then try to solve each of the puzzles obtained by choosing each of these values
def search(values):
    values = reduce_puzzle(values)
    if(values == False):
        return False
    if(len([box for box in values.keys() if len(values[box]) == 1]) == 81):
        return values
#    if(len([box for box in values.keys() if len(values[box]) == 0]) >0):
#        return false
    minn = 9
    for key in values.keys():
        if(len(values[key]) < minn and len(values[key]) >1):
            minn =len(values[key])
            indexkey = key
    
    for num in values[indexkey]:
        new_values = values.copy()
        new_values[indexkey] = num
        tmp = search(new_values)
        if(tmp):
            return tmp
    return False

# convert the grid into a dict ,then do the search function to find a solution
def solve(grid):
    """
    Find the solution to a Sudoku grid.
    Args:
        grid(string): a string representing a sudoku grid.
            Example: '2.............62....1....7...6..8...3...9...7...6..4...4....8....52.............3'
    Returns:
        The dictionary representation of the final sudoku grid. False if no solution exists.
    """
    values = grid_values(grid)
    return search(values)

if __name__ == '__main__':
    diag_sudoku_grid = '2.............62....1....7...6..8...3...9...7...6..4...4....8....52.............3'
    display(solve(diag_sudoku_grid))

    try:
        from visualize import visualize_assignments
        visualize_assignments(assignments)

    except SystemExit:
        pass
    except:
        print('We could not visualize your board due to a pygame issue. Not a problem! It is not a requirement.')
