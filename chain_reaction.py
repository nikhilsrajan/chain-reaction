import typing

class Cell:
    def __init__(self, value:int=0, belongs_to:int=0, explode_at:int=4):
        self.value:int = value
        self.belongs_to:int = belongs_to
        self.explode_at:int = explode_at
    
    def __repr__(self):
        return f"{self.value}/{self.explode_at} [{self.belongs_to}]"

    def should_explode(self)->bool:
        return self.value >= self.explode_at
    
    def increment(self, who:int)->typing.Tuple[int, bool]:
        self.value += 1
        self.belongs_to = who
        return self.value, self.should_explode()

class Grid:
    def __init__(self, nrows:int, ncols:int, _margin:int=1):
        self.nrows = nrows
        self.ncols = ncols

        self.grid:typing.List[typing.List[Cell]] \
            = self._generate_grid()
        
        self._ownership_list_dict = {
            0: set([(r, c) for r, row in enumerate(self.grid) for c, _ in enumerate(row)])
        }
        
        if _margin < 0:
            print('Warning: _margin < 0, _margin set to 0.')
            _margin = 0
        self._margin = _margin
    
    def _generate_grid(self)->typing.List[typing.List[Cell]]:
        grid = []
        for r in range(self.nrows):
            row = []
            for c in range(self.ncols):
                row.append(self.generate_cell(row=r, col=c))
            grid.append(row)
        return grid

    def _is_row_col_valid(self, row:int, col:int):
        if row < 0 or row >= self.nrows:
            raise ValueError(f"Invalid row={row}. row must be between [0, {self.nrows}].")
        if col < 0 or col >= self.ncols:
            raise ValueError(f"Invalid col={col}. col must be between [0, {self.ncols}].")

    def generate_cell(self, row:int, col:int)->Cell:
        self._is_row_col_valid(row=row, col=col)
        explode_at = 4
        if row in [0, self.nrows-1]:
            explode_at -= 1
        if col in [0, self.ncols-1]:
            explode_at -= 1
        return Cell(explode_at=explode_at)
    
    def __repr__(self):
        max_cell_repr_len = max([len(str(cell)) for row in self.grid for cell in row]) + self._margin*2
        repr_str = ''
        cell_line = ''.join(['-' for _ in range(max_cell_repr_len)])
        v_edge_str = ''
        cell_margin_str = ''.join([' ' for _ in range(self._margin)])
        for _ in range(self.ncols):
            v_edge_str += '+' + cell_line
        v_edge_str += '+\n'
        for r in range(self.nrows):
            repr_str += v_edge_str
            for c in range(self.ncols):
                cell_str = str(self.grid[r][c])
                repr_str += '|' + cell_margin_str + cell_str
                for _ in range(max_cell_repr_len - (len(cell_str) + self._margin)):
                    repr_str += ' '
            repr_str += '|\n'
        repr_str += v_edge_str
        return repr_str
    
    def _declare_cell_ownership_change(self, row:int, col:int, previous_owner:int, new_owner:int):
        if new_owner not in self._ownership_list_dict.keys():
            self._ownership_list_dict[new_owner] = set()
        self._ownership_list_dict[previous_owner].remove((row, col))
        self._ownership_list_dict[new_owner].add((row, col))
        if len(self._ownership_list_dict[previous_owner]) == 0:
            self._ownership_list_dict.pop(previous_owner)

    def increment(self, row:int, col:int, who:int, force:bool=False)->typing.Tuple[bool,int,bool]:
        if who == 0:
            raise ValueError("who=0 is reserved for 'noone'. Please select anyother id.")

        previous_owner = self.grid[row][col].belongs_to

        is_valid_increment = previous_owner in [0, who]
        new_value = 0
        should_explode = False

        if is_valid_increment or force:
            new_value, should_explode = self.grid[row][col].increment(who=who)

            if who != previous_owner:
                self._declare_cell_ownership_change(row=row, col=col, previous_owner=previous_owner, new_owner=who)

        return is_valid_increment, new_value, should_explode
    
    def get_neighbours(self, row:int, col:int):
        self._is_row_col_valid(row=row, col=col)
        neighbours = set()
        if row != 0:
            neighbours.add((row-1, col))
            if col != 0:  
                neighbours.add((row, col-1))
            if col != self.ncols-1:
                neighbours.add((row, col+1))
        if row != self.nrows-1:
            neighbours.add((row+1, col))
            if col != 0:
                neighbours.add((row, col-1))
            if col != self.ncols-1:
                neighbours.add((row, col+1))
        return list(neighbours)
    
    def get_ownership_list_dict(self)->typing.Dict[int,typing.Set[typing.Tuple[int,int]]]:
        return self._ownership_list_dict
    
    def get_winner(self)->int:
        ownership_list_dict = self.get_ownership_list_dict()
        winner = 0
        present_owners = set(ownership_list_dict.keys())
        if 0 in present_owners:
            present_owners.remove(0)
        there_is_a_winner = len(present_owners) == 1
        if there_is_a_winner:
            winner = list(present_owners)[0]
        return there_is_a_winner, winner
    
    def update_state(self, row:int, col:int)->typing.Tuple[bool, int]:
        who = self.grid[row][col].belongs_to
        queue = [(row, col)]
        continue_playing = True
        winner = 0

        while len(queue) > 0:
            row, col = queue.pop(0)
            
            if self.grid[row][col].should_explode():
                who = self.grid[row][col].belongs_to
                neighbours = self.get_neighbours(row=row, col=col)
                self.grid[row][col].value -= self.grid[row][col].explode_at
                
                if self.grid[row][col].value == 0:
                    previous_owner = self.grid[row][col].belongs_to
                    self.grid[row][col].belongs_to = 0
                    self._declare_cell_ownership_change(row=row, col=col, previous_owner=previous_owner, new_owner=0)
            
                for n_row, n_col in neighbours:
                    _, _, should_explode = self.increment(
                        row=n_row, col=n_col, who=who, force=True
                    )
            
                    if should_explode:
                        queue.append((n_row, n_col))
            
                if self.grid[row][col].should_explode():
                    queue.append((row, col))
                there_is_a_winner, winner = self.get_winner()
            
                if there_is_a_winner:
                    continue_playing = False
                    break
        
        return continue_playing, winner
