from player_divercite import PlayerDivercite
from seahorse.game.action import Action
from seahorse.game.game_state import GameState
from game_state_divercite import GameStateDivercite

from seahorse.game.heavy_action import HeavyAction
from seahorse.game.light_action import LightAction
from seahorse.game.game_layout.board import Piece
from game_state_divercite import BoardDivercite


import math, time


# Filter Action
THRESHOLD = 25
LEN_DIVIDE = 2
MAX_ACTIONS = 30

# State Heuristic
OPPONENT_SCORE_MULT = 0.5
DIV_CITY_HEUR = 0.5

# Action Heuristic
SELF_CITY_GAIN_MULT = 1 # mult the gain (after - before) made by an action on a city
OPPONENT_CITY_GAIN_MULT = 1 # mult the gain (after - before) made by an action on an opponent city
RESSOURCE_BALANCE = 2 # base value for the balance of the ressources pieces
CITY_BALANCE = 3 # base value for the balance of the cities pieces

# Evaluate my city
DIVERSITY_SCORE = 6 # score for a diversity
STILL_POSSIBLE_DIVERSITY_MULT = 1.5 # score for a diversity that is still possible
SCORE_FOR_COLOR_MULT = 1.5 # mult the score for a color around a city 

# Evaluate opponent city
CANCEL_DIVERSITY_SCORE = 4 # score for a diversity that is canceled
CANCEL_IN_PROGRESS_DIVERSITY_SCORE = 1 # score for a diversity that is canceled in progress
NOT_COMPLETABLE_DIVERSITY_SCORE = 1
BONUS_CANCEL_WITH_OTHER_COL = 0

# City heuristic
NEAR_OPPONENT_CITY_SCORE = 1
DIFFERENT_COLOR_CITY_BONUS = 1
IN_PROGRESS_DIVERSITY_MULT = 1
CITY_COLOR_SCORE = 1
SAME_COLOR_CITY_BONUS = 0
NEAR_MY_CITY_SCORE = 0.5


class MyPlayer(PlayerDivercite):
    """
    Player class for Divercite game that makes random moves.

    Attributes:
        piece_type (str): piece type of the player
    """

    def __init__(self, piece_type: str, name: str = "MyPlayer"):
        """
        Initialize the PlayerDivercite instance.

        Args:
            piece_type (str): Type of the player's game piece
            name (str, optional): Name of the player (default is "bob")
            time_limit (float, optional): the time limit in (s)
        """
        super().__init__(piece_type, name)
        self.open: list[LightAction] = [LightAction({"piece": "RC", "position": (6, 5)}), LightAction({"piece": "BC", "position": (5, 6)})]
        self.is_start_player = False


    def compute_action(self, current_state: GameStateDivercite, remaining_time: int = 1e9, **kwargs) -> Action:
        """
        Use the minimax algorithm to choose the best action based on the heuristic evaluation of game states.

        Args:
            current_state (GameState): The current game state.

        Returns:
            Action: The best action as determined by minimax.
        """

        self.start_time = time.time()
        self.remaining_time = remaining_time
        self.opponent_id = [key for key in current_state.scores if key != self.get_id()][0]

        if len(current_state.rep.env.items()) == 0:
            self.is_start_player = True
        
        if self.is_start_player and len(self.open) > 0:
            fist_action = self.open.pop(0)
            while not current_state.check_action(fist_action) and len(self.open) > 0:
                fist_action = self.open.pop(0)
            
            if current_state.check_action(fist_action):
                return fist_action.get_heavy_action(current_state)

        action = self.alpha_beta_search(current_state)        
        return action


    def depth_depend_on_actions(self, length: list) -> int:
        if (self.remaining_time - (time.time() - self.start_time)) < 80: 
            return 3
        if length < 6:
            return 10
        if length < 11:
            return 8
        if length < 15:
            return 7
        if length < 18:
            return 6
        if length < 32:
            return 5
        if length < 70:
            return 4
        return 3

    def alpha_beta_search(self, current_state: GameStateDivercite) -> Action:
        alpha = -math.inf
        beta = math.inf
        best_action, (_, _) = self.max_value(current_state, alpha, beta, -1, action_heur=-1) 

        return best_action


    def max_value(self, state: GameStateDivercite, alpha: float, beta: float, depth: int, action_heur=0) -> tuple[Action, float]:
        if depth == 0 or state.is_done():
            h = self.state_heuristic(state, action_heur)
            return None, (h, state)

        best_action = None
        value = -math.inf
        
        actions = self.filter_actions(state, action_heur)

        if depth == -1:
            depth = self.depth_depend_on_actions(len(actions))
        else:
            depth = min(depth, self.depth_depend_on_actions(len(actions)))

        for action, act_heur in actions:
            heavy_action = action.get_heavy_action(state)
            next_state = heavy_action.get_next_game_state()
            _, (next_value, next_he) = self.min_value(next_state, alpha, beta, depth - 1, act_heur)
            
            if next_value > value:
                value = next_value
                he = next_he
                best_action = heavy_action

            alpha = max(alpha, value)
            if beta <= alpha:
                break

        return best_action, (value, he)



    def min_value(self, state: GameStateDivercite, alpha: float, beta: float, depth: int, act_heur=0) -> tuple[Action, float]:
        if depth == 0 or state.is_done():
            h = self.state_heuristic(state, act_heur)
            return None, (h, state)

        best_action = None
        value = math.inf
        actions = self.filter_actions(state, act_heur)
        depth = min(depth, self.depth_depend_on_actions(len(actions)))

        for action, act_heur in actions:
            heavy_action = action.get_heavy_action(state)
            next_state = heavy_action.get_next_game_state()
           
            _, (next_value, next_he) = self.max_value(next_state, alpha, beta, depth - 1, act_heur)
            if next_value < value:
                value = next_value
                he = next_he
                best_action = heavy_action

            beta = min(beta, value)

            if beta <= alpha:
                break

        return best_action, (value, he)


    def filter_actions(self, state: GameStateDivercite, act_heur=0) -> list[LightAction]:
        actions = list(state.generate_possible_light_actions())
        actions_with_heuristics = [
            (action, heuristic_value)
            for action in actions
            if (heuristic_value := self.action_heuristic(action, state, act_heur)) is not None and heuristic_value >= 0
        ]

        if len(actions_with_heuristics) == 0:
            return [(action, 1) for action in actions]

        filtered_actions = sorted(actions_with_heuristics, key=lambda x: x[1], reverse=True)
        return filtered_actions[:min(len(filtered_actions)//LEN_DIVIDE, MAX_ACTIONS)] if len(filtered_actions) > THRESHOLD else filtered_actions
   

    def state_heuristic(self, state: GameStateDivercite, ligth_action_heur: int = 0) -> int:
        player_id = self.get_id()
        score = 0
        opponent_score = 0
        
        pieces_on_board = state.rep.env.items()

        for pos, piece in pieces_on_board:
            if isinstance(piece, Piece):
                if piece.get_type()[1] == 'C':
                    if piece.owner_id == player_id:
                        score += self.evaluate_my_city((piece, pos), state)
                        score += self.city_heuristic(state, {"piece": piece.get_type(), "position": pos}, player_id)//DIV_CITY_HEUR
                        opponent_score += self.evaluate_opponent_city((piece, pos), state)
                    else:
                        score += self.evaluate_opponent_city((piece, pos), state)
                        opponent_score += self.evaluate_my_city((piece, pos), state)
                        opponent_score += self.city_heuristic(state, {"piece": piece.get_type(), "position": pos}, self.opponent_id)//DIV_CITY_HEUR

        return score - opponent_score * OPPONENT_SCORE_MULT


    def action_heuristic(self, action: LightAction, state: GameStateDivercite, previous_h=0) -> int:
        player_id = self.get_id()
        opponent_id = self.opponent_id
        
        temp = 0
        if action.data['piece'].endswith('R'):
            value = 0
            x, y = action.data['position']
            neighbours = state.get_neighbours(x, y)
            
            for key_pos, neighbor_piece in neighbours.items():
                if not isinstance(neighbor_piece[0], Piece):  
                    continue
                if neighbor_piece[0].piece_type[1] == 'C':  
                    if neighbor_piece[0].owner_id == player_id:
                        temp = self.evaluate_my_city(neighbor_piece, state, action.data['piece'][0]) #- self.evaluate_my_city(neighbor_piece, state)
                        value += temp * SELF_CITY_GAIN_MULT if temp > 0 else 0
                    else:
                        temp = self.evaluate_opponent_city(neighbor_piece, state, action.data['piece'][0]) #- self.evaluate_opponent_city(neighbor_piece, state)
                        value += temp * OPPONENT_CITY_GAIN_MULT if temp > 0 else 0
            
            # don't want to expend action of resource if no city around or don't cancel opponent divercity
            if value <= 0:
                return 0
        else:
            value = 1
            value += self.city_heuristic(state, action.data, player_id) 
        
        remaining_pieces = state.players_pieces_left[player_id]
        remaining_pieces[action.data['piece']] -= 1

        color_counts_R = {
            'R': remaining_pieces['RR'] ,
            'G': remaining_pieces['GR'] ,
            'B': remaining_pieces['BR'] ,
            'Y': remaining_pieces['YR'] ,
        }

        color_counts_C = {
            'R': remaining_pieces['RC'],
            'G': remaining_pieces['GC'],
            'B': remaining_pieces['BC'],
            'Y': remaining_pieces['YC']
        }
        
        avg_pieces = sum(color_counts_R.values()) / len(color_counts_R)
        imbalance_penalty = sum(abs(count - avg_pieces) for count in color_counts_R.values())

        value += RESSOURCE_BALANCE / (imbalance_penalty/2 + 1)
        
        avg_pieces = sum(color_counts_C.values()) / len(color_counts_C)
        imbalance_penalty = sum(abs(count - avg_pieces) for count in color_counts_C.values())

        value += CITY_BALANCE / (imbalance_penalty/2 + 1)
        remaining_pieces[action.data['piece']] += 1 # restore the state

        return value


    def evaluate_my_city(self, city: tuple[Piece, tuple[int, int]], state: GameStateDivercite, piece_color=None) -> int:
        city_pos = city[1]
        neighbors = state.rep.get_neighbours(city_pos[0], city_pos[1])

        neighbor_piece_colors = [n[0].get_type()[0] for n in neighbors.values() if isinstance(n[0], Piece)]

        if not piece_color is None:
            neighbor_piece_colors.append(piece_color) 
        
        # I do a diversity
        if len(set(neighbor_piece_colors)) == 4:
            return DIVERSITY_SCORE 
        
        # Diversity is still possible
        if len(set(neighbor_piece_colors)) == len(neighbor_piece_colors) and self.has_needed_pieces(neighbor_piece_colors, state.players_pieces_left[city[0].owner_id]):
            return STILL_POSSIBLE_DIVERSITY_MULT * len(neighbor_piece_colors) 
        else:
            return len([p for p in neighbor_piece_colors if p == city[0].get_type()[0]]) * SCORE_FOR_COLOR_MULT
        

    def evaluate_opponent_city(self, city: tuple[Piece, tuple[int, int]], state: GameStateDivercite, piece_color=None) -> int:
        city_pos = city[1]
        neighbors = state.rep.get_neighbours(city_pos[0], city_pos[1])

        neighbor_piece_colors = [n[0].get_type()[0] for n in neighbors.values() if isinstance(n[0], Piece)]
        if len(neighbor_piece_colors) == len(set(neighbor_piece_colors)) and not self.has_needed_pieces(neighbor_piece_colors, state.players_pieces_left[city[0].owner_id]):
            return NOT_COMPLETABLE_DIVERSITY_SCORE
        
        if not piece_color is None:
            neighbor_piece_colors.append(piece_color)
        
        # Cancel opponent diversity is good for me
        if len(neighbor_piece_colors) == 4 and len(set(neighbor_piece_colors)) != 4:
            return CANCEL_DIVERSITY_SCORE
        
        # Cancel in progress opponent diversity is good for me
        if len(neighbor_piece_colors) == 3 and len(set(neighbor_piece_colors)) != 3:
            return CANCEL_IN_PROGRESS_DIVERSITY_SCORE + BONUS_CANCEL_WITH_OTHER_COL if piece_color != city[0].get_type()[0] else 0
        
        return 0


    def city_heuristic(self, state: GameStateDivercite, piece: dict[str, tuple|str], player_id: str) -> int:
        city_color = piece['piece'][0]
        x, y = piece['position']
        near_city = 0

        for neighbours_city in self.get_neighbours_city(x, y, state).values():
            if neighbours_city is None:
                continue
            if neighbours_city.piece_type[1] == 'C' and neighbours_city.owner_id != player_id:
                near_city += NEAR_OPPONENT_CITY_SCORE + DIFFERENT_COLOR_CITY_BONUS if neighbours_city.piece_type[0] != city_color else 0
            else:
                near_city += NEAR_MY_CITY_SCORE + SAME_COLOR_CITY_BONUS if neighbours_city.piece_type[0] == city_color else 0

        return near_city
               

    def get_neighbours_city(self, x, y, state: GameStateDivercite) -> dict[str, None|Piece]:
        current_board = state.rep.env
        neighbours = {"top":(x-1, y+1), "left":(x+1,y-1), "bot":(x-1, y+1), "right":(x+1,y+1)}

        for k,v in neighbours.items():
            if v in current_board.keys():
                neighbours[k] = current_board[v]
            else:
                neighbours[k] = None
        
        return neighbours
    

    def has_needed_pieces(self, current_pieces_colors: list[str], remaining_pieces: dict[str, int]) -> bool:
        needed_color = []
        for color in ['R', 'G', 'B', 'Y']:
            if color not in current_pieces_colors:
                needed_color.append(color)
            
        return all(remaining_pieces[color+'R'] > 0 for color in needed_color)


# For testing
if __name__ == "__main__":
    player = MyPlayer("W", "Test")

    print(player.has_needed_pieces(['R', 'G'], {'RR': 3, 'RC': 3, 'GR': 3, 'GC': 3, 'BR': 0, 'BC': 0, 'YR': 1, 'YC': 3}))