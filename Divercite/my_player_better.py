from player_divercite import PlayerDivercite
from seahorse.game.action import Action
from seahorse.game.game_state import GameState
from game_state_divercite import GameStateDivercite
from seahorse.utils.custom_exceptions import MethodNotImplementedError

from seahorse.game.heavy_action import HeavyAction
import math

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
            print('first')
            first_action_play_city = next(
                (d for d in current_state.generate_possible_heavy_actions() if any(key.endswith('C') and value < 2 for key, value in d.next_game_state.players_pieces_left[self.get_id()].items())), 
                None
            )
            return first_action_play_city
        # if all(  in current_state.players_pieces_left):
        
        depth = self.depth_depend_on_gameState(current_state, remaining_time)
        action = self.alpha_beta_search(current_state, depth)
        return action


    def depth_depend_on_gameState(self, current_state: GameStateDivercite, remaining_time: int) -> int:
            
        length = len(current_state.get_possible_light_actions())
        
        print(length)
        
        if length < 10:
            return 11

        if length < 20:
            return 7
        
        if length < 30:
            return 6
        
        if length < 45:
            return 5
        
        if length < 80:
            return 4

        return 3
    

    def alpha_beta_search(self, current_state: GameStateDivercite, depth: int = 3) -> Action:
        
        alpha = -math.inf
        beta = math.inf

        best_action, _ = self.max_value(current_state, alpha, beta, depth) 

        return best_action

    def max_value(self, state: GameStateDivercite, alpha: float, beta: float, depth: int) -> tuple[Action, float]:
        if depth == 0 or state.is_done():
            return None, self.state_heuristic(state)

        best_action = None
        value = -math.inf

        actions = list(state.generate_possible_heavy_actions())
        actions.sort(key=lambda e: self.action_heuristic(e), reverse=True)

        for action in actions:
            next_state = action.get_next_game_state()
            _, next_value = self.min_value(next_state, alpha, beta, depth - 1)
            if next_value > value:
                value = next_value
                best_action = action

            alpha = max(alpha, value)

            if beta <= alpha:
                break

        return best_action, value

    def min_value(self, state: GameStateDivercite, alpha: float, beta: float, depth: int) -> tuple[Action, float]:
        if depth == 0 or state.is_done():
            return None, self.state_heuristic(state)

        best_action = None
        value = math.inf

        actions = list(state.generate_possible_heavy_actions())
        actions.sort(key=lambda a: self.action_heuristic(a), reverse=True)

        for action in actions:
            next_state = action.get_next_game_state()
            _, next_value = self.max_value(next_state, alpha, beta, depth - 1)
            if next_value < value:
                value = next_value
                best_action = action

            beta = min(beta, value)

            if beta <= alpha:
                break

        return best_action, value


    def state_heuristic(self, state: GameState) -> float:
        player_id = self.get_id()
        score = state.scores[player_id]

        opponent_score = state.scores[self.opponent_id]
        # # Evaluate cities controlled by the player and nearby resources
        # for city in state.get_player_cities(player_id):
        #     adjacent_resources = state.get_adjacent_resources(city)
        #     unique_resources = len(set(adjacent_resources))
        #     if unique_resources == 4:
        #         score += 5
        #     else:
        #         score += sum(1 for resource in adjacent_resources if resource == city.get_piece_type()[0])

        # # Evaluate future potential for divercities
        # score += self.evaluate_future_divercite(state, player_id)

        return score - 0.5 * opponent_score


    def evaluate_future_divercite(self, state: GameStateDivercite, player_id: int) -> float:
        """
        Evaluate the potential for future divercities based on the current board state.
        """
        future_potential = 0
        empty_positions = state.get_empty_positions()  # Assuming this method exists
        for position in empty_positions:
            adjacent_resources = state.get_adjacent_resources(position)
            unique_resources = len(set(adjacent_resources))
            if unique_resources == 4:
                future_potential += 3
            elif adjacent_resources.count(None) == 0:
                future_potential -= 1
        return future_potential


    def action_heuristic(self, action: HeavyAction) -> float:
        player_id = self.get_id()

        current_state = action.get_current_game_state()
        next_state = action.get_next_game_state()

        my_current_score = current_state.scores[player_id]
        my_next_score = next_state.scores[player_id]
 
        opponent_current_score = current_state.scores[self.opponent_id]
        opponent_next_score = next_state.scores[self.opponent_id]

        # value -= (opponent_next_score - opponent_current_score)
        return my_next_score - 0.5 * opponent_next_score
