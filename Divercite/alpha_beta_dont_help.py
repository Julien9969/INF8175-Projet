from player_divercite import PlayerDivercite
from seahorse.game.action import Action
from seahorse.game.game_state import GameState
from game_state_divercite import GameStateDivercite
from seahorse.utils.custom_exceptions import MethodNotImplementedError

from seahorse.game.heavy_action import HeavyAction
from seahorse.game.light_action import LightAction
from seahorse.game.game_layout.board import Piece
from game_state_divercite import BoardDivercite


import math, random

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

    def compute_action(self, current_state: GameStateDivercite, remaining_time: int = 1e9, **kwargs) -> Action:
        """
        Use the minimax algorithm to choose the best action based on the heuristic evaluation of game states.

        Args:
            current_state (GameState): The current game state.

        Returns:
            Action: The best action as determined by minimax.
        """

        self.opponent_id = [key for key in current_state.scores if key != self.get_id()][0]
        if all((value == 2 if key.endswith('C') else value == 3) for key, value in current_state.players_pieces_left[self.get_id()].items()):
            possible_actions = [
                d for d in current_state.generate_possible_heavy_actions()
                if any('C' in key and value < 2 for key, value in d.next_game_state.players_pieces_left[self.get_id()].items())
            ]

            first_action_play_city = random.choice(possible_actions)

            return first_action_play_city
        
        depth = self.depth_depend_on_actions(len(self.filter_actions(current_state)), remaining_time)
        action = self.alpha_beta_search(current_state, depth)
        return action


    def depth_depend_on_actions(self, length: list, remaining_time: int) -> int:
          
        print(length)
        
        # if remaining_time < 1000: 
        #     return 3

        if length < 15:
            return 6
        if length < 20:
            return 5
        if length < 30:
            return 4
        if length < 45:
            return 3
        if length < 80:
            return 5

        return 4
    

    def alpha_beta_search(self, current_state: GameStateDivercite, depth) -> Action:
        
        alpha = -math.inf
        beta = math.inf
        best_action, _ = self.max_value(current_state, alpha, beta, depth) 

        print(_)
        return best_action


    def max_value(self, state: GameStateDivercite, alpha: float, beta: float, depth: int, act_heur=0) -> tuple[Action, float]:
        if depth == 0 or state.is_done():
            return None, self.state_heuristic(state, act_heur)

        best_action = None
        value = -math.inf
        
        actions = self.filter_actions(state)

        for action, act_heur in actions:
            heavy_action = action.get_heavy_action(state)
            next_state = heavy_action.get_next_game_state()
            _, next_value = self.min_value(next_state, alpha, beta, depth - 1, act_heur)
            if next_value > value:
                value = next_value
                best_action = heavy_action

            alpha = max(alpha, value)

            if beta <= alpha:
                break

        return best_action, value


    def min_value(self, state: GameStateDivercite, alpha: float, beta: float, depth: int, act_heur=0) -> tuple[Action, float]:
        if depth == 0 or state.is_done():
            h = self.state_heuristic(state, act_heur)
            return None, h

        best_action = None
        value = math.inf

        actions = self.filter_actions(state)

        for action, act_heur in actions:
            heavy_action = action.get_heavy_action(state)
            next_state = heavy_action.get_next_game_state()
            _, next_value = self.max_value(next_state, alpha, beta, depth - 1, act_heur)
            if next_value < value:
                value = next_value
                best_action = heavy_action

            beta = min(beta, value)

            if beta <= alpha:
                break

        return best_action, value


    def filter_actions(self, state: GameStateDivercite) -> list[LightAction]:
        actions_with_heuristics = [
            (action, heuristic_value)
            for action in state.generate_possible_light_actions()
            if (heuristic_value := self.action_heuristic(action, state)) is not None and heuristic_value > 0
        ]

        filtered_actions = sorted(actions_with_heuristics, key=lambda x: x[1], reverse=True)
        return filtered_actions[:len(filtered_actions)//2] if len(filtered_actions) > 18 else filtered_actions
   
   
    def state_heuristic(self, state: GameState, ligth_action_heur: int = 0) -> float:
        player_id = self.get_id()
        score = state.scores[player_id]
        opponent_score = state.scores[self.opponent_id]
        
        score_diff = score - opponent_score
        if score_diff > 5:
            opponent_weight = 0.8 
        elif score_diff < -5:
            opponent_weight = 0.3  
        else:
            opponent_weight = 0.5 

        return score - opponent_weight * opponent_score + ligth_action_heur//2


    # try to uniformize the usage of pice by color
    def action_heuristic(self, action: LightAction, state: GameStateDivercite) -> float:
        player_id = self.get_id()
        
        value = 0

        if action.data['piece'].endswith('R'):
            x, y = action.data['position']
            neighbours = state.get_neighbours(x, y)
            
            for key_pos, neighbor_piece in neighbours.items():
                if not isinstance(neighbor_piece[0], Piece):  
                    continue
                if neighbor_piece[0].piece_type[1] == 'C':  
                    if neighbor_piece[0].owner_id == player_id:
                        # Reward more for creating a 'divercité' for the player
                        value += self.continue_divercite(neighbor_piece, state.rep, action.data['piece'][0])
                    else:
                        # Penalize opponent by canceling their divercité
                        value += self.cancel_divercite(neighbor_piece, state.rep, action.data['piece'][0])
            
            # don't want to expend action of resource if no city around or don't cancel opponent divercite
            if value == 0:
                return 0
        else:
            x, y = action.data['position']
            neighbours: dict[str|Piece, tuple] = state.get_neighbours(x, y)

            value += self.city_heuristic(neighbours, action.data['piece'][0])
            
        return value


    # some logic with opponnet pieces (cant do divercite if dont have color)
    def continue_divercite(self, city: tuple[Piece, tuple[int, int]], board: BoardDivercite, piece_color = None) -> int:
        city_pos = city[1]
        neighbors = board.get_neighbours(city_pos[0], city_pos[1])

        neighbor_piece_colors = [n[0].get_type()[0] for n in neighbors.values() if isinstance(n[0], Piece)]

        if len(set(neighbor_piece_colors).union(set([piece_color]) if piece_color else {})) == 4:
            return 8
        
        neighbor_piece_colors.append(piece_color) if piece_color else None
        if len(set(neighbor_piece_colors)) == len(neighbor_piece_colors):
            return len(neighbor_piece_colors) + 1
        else:
            return len([p for p in neighbor_piece_colors if p == city[0].get_type()[0]])
        
    def cancel_divercite(self, city: tuple[Piece, tuple[int, int]], board: BoardDivercite, piece_color=None) -> int:
        city_pos = city[1]
        neighbors = board.get_neighbours(city_pos[0], city_pos[1])

        neighbor_piece_colors = [n[0].get_type()[0] for n in neighbors.values() if isinstance(n[0], Piece)]
        neighbor_piece_colors.append(piece_color) if piece_color else None

        if len(neighbor_piece_colors) == 4 and len(set(neighbor_piece_colors)) != 4:
            return 8
        return -1


    def city_heuristic(self, neighbours: dict[str|Piece, tuple], city_color) -> int:
        value = 0
        
        neighbor_piece_colors = [n[0].get_type()[0] for n in neighbours.values() if isinstance(n[0], Piece)]

        if len(set(neighbor_piece_colors)) == len(neighbor_piece_colors):
            value += len(set(neighbor_piece_colors))

        value += sum(1 for color in neighbor_piece_colors if color == city_color)
            
        return value