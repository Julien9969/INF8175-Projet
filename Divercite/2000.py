from player_divercite import PlayerDivercite
from seahorse.game.action import Action
from seahorse.game.game_state import GameState
from game_state_divercite import GameStateDivercite
from seahorse.utils.custom_exceptions import MethodNotImplementedError

from seahorse.game.heavy_action import HeavyAction
from seahorse.game.light_action import LightAction
from seahorse.game.game_layout.board import Piece
from game_state_divercite import BoardDivercite


import math, random, time

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
        self.open: list[LightAction] = [LightAction({"piece": "RC", "position": (6, 5)}), LightAction({"piece": "BC", "position": (5, 6)}), LightAction({"piece": "BR", "position": (6, 6)}), LightAction({"piece": "RR", "position": (5, 5)})]
    
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

        if all((value == 2 if key.endswith('C') else value == 3) for key, value in current_state.players_pieces_left[self.get_id()].items()):
            possible_actions = [
                d for d in current_state.generate_possible_heavy_actions()
                if any('C' in key and value < 2 for key, value in d.next_game_state.players_pieces_left[self.get_id()].items())
            ]

            first_action_play_city = random.choice(possible_actions)

            return first_action_play_city
        # if len(self.open) > 0:
        #     fist_action = self.open.pop(0)
        #     while not current_state.check_action(fist_action) and len(self.open) > 0:
        #         fist_action = self.open.pop(0)
            
        #     if current_state.check_action(fist_action):
        #         return fist_action.get_heavy_action(current_state)



        depth = self.depth_depend_on_actions(len(self.filter_actions(current_state)))
        print("Depth: ", depth)
        action = self.alpha_beta_search(current_state, depth)
        return action


    def depth_depend_on_actions(self, length: list) -> int:
        if (self.remaining_time - (time.time() - self.start_time)) < 80: 
            return 3
        if length < 6:
            return 10
        if length < 10:
            return 8
        if length < 12:
            return 7
        if length < 20:
            return 6
        if length < 45:
            return 5
        if length < 80:
            return 4
        return 3
    

    def alpha_beta_search(self, current_state: GameStateDivercite, depth) -> Action:
        
        alpha = -math.inf
        beta = math.inf
        best_action, (tt, hp) = self.max_value(current_state, alpha, beta, depth) 

        print("TT: ", tt, "HP: ", hp)
        return best_action


    def max_value(self, state: GameStateDivercite, alpha: float, beta: float, depth: int, act_heur=0) -> tuple[Action, float]:
        if depth == 0 or state.is_done():
            h = self.state_heuristic(state, act_heur)
            return None, (h, act_heur)

        best_action = None
        value = -math.inf
        
        actions = self.filter_actions(state, act_heur)

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
            return None, (h, act_heur)

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
        return filtered_actions[:min(len(filtered_actions)//3, 25)] if len(filtered_actions) > 20 else filtered_actions
   

    def state_heuristic(self, state: GameStateDivercite, ligth_action_heur: int = 0) -> int:
        player_id = self.get_id()
        # score = state.scores[player_id]
        score = 0
        opponent_score = state.scores[self.opponent_id]
        
        pieces_on_borad = state.rep.env.items()

        for pos, piece in pieces_on_borad:
            if isinstance(piece, Piece):
                if piece.get_type()[1] == 'C':
                    if piece.owner_id == player_id:
                        score += self.evaluate_my_city((piece, pos), state)
                        # opponent_score += self.evaluate_opponent_city((piece, pos), state)/2
                    else:
                        score += self.evaluate_opponent_city((piece, pos), state)
                        # opponent_score += self.evaluate_my_city((piece, pos), state)/2

        return score - opponent_score #* 1.5# * 0.6



    # try to uniformize the usage of pice by color
    def action_heuristic(self, action: LightAction, state: GameStateDivercite, previous_h=0) -> int:
        player_id = self.get_id()
        opponent_id = self.opponent_id
        
        if action.data['piece'].endswith('R'):
            value = 0
            x, y = action.data['position']
            neighbours = state.get_neighbours(x, y)
            
            for key_pos, neighbor_piece in neighbours.items():
                if not isinstance(neighbor_piece[0], Piece):  
                    continue
                if neighbor_piece[0].piece_type[1] == 'C':  
                    if neighbor_piece[0].owner_id == player_id:
                        value += self.evaluate_my_city(neighbor_piece, state, action.data['piece'][0])
                    else:
                        value += self.evaluate_opponent_city(neighbor_piece, state, action.data['piece'][0])
            
            # don't want to expend action of resource if no city around or don't cancel opponent divercite
            if value <= 0:
                return 0
        else:
            value = 1
            x, y = action.data['position']
            neighbours: dict[str|Piece, tuple] = state.get_neighbours(x, y)

            value += self.city_heuristic(neighbours, action.data['piece'][0])
        
        remaining_pieces = state.players_pieces_left[player_id]
        remaining_pieces[action.data['piece']] -= 1

        color_counts_R = {
            'R': remaining_pieces['RR'] ,#+ remaining_pieces['RC'],
            'G': remaining_pieces['GR'] ,#+ remaining_pieces['GC'],
            'B': remaining_pieces['BR'] ,#+ remaining_pieces['BC'],
            'Y': remaining_pieces['YR'] ,#+ remaining_pieces['YC']
        }

        color_counts_C = {
            'R': remaining_pieces['RC'],
            'G': remaining_pieces['GC'],
            'B': remaining_pieces['BC'],
            'Y': remaining_pieces['YC']
        }

        # color_counts = {
        #     'R': 3 + 2,
        #     'G': 2 + 2,
        #     'B': 0 + 1,
        #     'Y': 3 + 0
        # }
        avg_pieces = sum(color_counts_R.values()) / len(color_counts_R)
        imbalance_penalty = sum(abs(count - avg_pieces) for count in color_counts_R.values())


        value += 2 / (imbalance_penalty/2 + 1)

        avg_pieces = sum(color_counts_C.values()) / len(color_counts_C)
        imbalance_penalty = sum(abs(count - avg_pieces) for count in color_counts_C.values())

        value += 2 / (imbalance_penalty/2 + 1)

        remaining_pieces[action.data['piece']] += 1 # restore the state

        return value


    # some logic with opponnet pieces (cant do divercite if dont have color)
    def evaluate_my_city(self, city: tuple[Piece, tuple[int, int]], state: GameStateDivercite, piece_color=None) -> int:
        city_pos = city[1]
        neighbors = state.rep.get_neighbours(city_pos[0], city_pos[1])

        neighbor_piece_colors = [n[0].get_type()[0] for n in neighbors.values() if isinstance(n[0], Piece)]

        if not piece_color is None:
            neighbor_piece_colors.append(piece_color) 
        if len(set(neighbor_piece_colors)) == 4:
            return 6 # reduire
        
        
        if len(set(neighbor_piece_colors)) == len(neighbor_piece_colors) and self.has_needed_pieces(neighbor_piece_colors, state.players_pieces_left[city[0].owner_id]):
            return len(neighbor_piece_colors) + (1 if len(neighbor_piece_colors) == 3 else 0)
        else:
            return len([p for p in neighbor_piece_colors if p == city[0].get_type()[0]])
        

    def evaluate_opponent_city(self, city: tuple[Piece, tuple[int, int]], state: GameStateDivercite, piece_color=None) -> int:
        city_pos = city[1]
        neighbors = state.rep.get_neighbours(city_pos[0], city_pos[1])

        neighbor_piece_colors = [n[0].get_type()[0] for n in neighbors.values() if isinstance(n[0], Piece)]
        if len(neighbor_piece_colors) < 3 or len(neighbor_piece_colors) != len(set(neighbor_piece_colors)) or not self.has_needed_pieces(neighbor_piece_colors, state.players_pieces_left[city[0].owner_id]):
            return 0
        
        if not piece_color is None:
            neighbor_piece_colors.append(piece_color)
            
        if len(neighbor_piece_colors) == 4 and len(set(neighbor_piece_colors)) != 4:
            return 6
        
        if len(neighbor_piece_colors) == 3 and len(set(neighbor_piece_colors)) != 3:
            return 2 + 1 if piece_color != city[0].get_type()[0] else 0
        return 0


    def city_heuristic(self, neighbours: dict[str|Piece, tuple], city_color) -> int:
        neighbor_piece_colors = [n[0].get_type()[0] for n in neighbours.values() if isinstance(n[0], Piece)]

        if len(set(neighbor_piece_colors)) == len(neighbor_piece_colors):
            return len(set(neighbor_piece_colors)) + (1 if len(neighbor_piece_colors) == 3 else 0)
        else:
            return sum(1 for color in neighbor_piece_colors if color == city_color)
        
    def has_needed_pieces(self, current_pieces_colors: list[str], remaining_pieces: dict[str, int]) -> bool:
        needed_color = []
        for color in ['R', 'G', 'B', 'Y']:
            if color not in current_pieces_colors:
                needed_color.append(color)
            
        return all(remaining_pieces[color+'R'] > 0 for color in needed_color)

if __name__ == "__main__":
    player = MyPlayer("W", "Test")

    print(player.has_needed_pieces(['R', 'G'], {'RR': 3, 'RC': 3, 'GR': 3, 'GC': 3, 'BR': 0, 'BC': 0, 'YR': 1, 'YC': 3}))