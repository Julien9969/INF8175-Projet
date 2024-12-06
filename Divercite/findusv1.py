from player_divercite import PlayerDivercite
from seahorse.game.action import Action
from seahorse.game.game_state import GameState
from game_state_divercite import GameStateDivercite
from seahorse.utils.custom_exceptions import MethodNotImplementedError

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

    def compute_action(self, current_state: GameState, remaining_time: int = 1e9, **kwargs) -> Action:
        """
        Use the minimax algorithm to choose the best action based on the heuristic evaluation of game states.

        Args:
            current_state (GameState): The current game state.

        Returns:
            Action: The best action as determined by minimax.
        """
        self.opponent_id = [key for key in current_state.scores if key != self.get_id()][0]

        action = self.alpha_beta_search(current_state, depth=3)
        return action
        

    def alpha_beta_search(self, current_state: GameState, depth: int = 3) -> Action:
        
        alpha = -math.inf
        beta = math.inf

        best_action, _ = self.max_value(current_state, alpha, beta, depth) 

        return best_action

    def max_value(self, state: GameState, alpha: float, beta: float, depth: int) -> tuple[Action, float]:
        if depth == 0 or state.is_done():
            return None, self.move_heuristic(state)

        best_action = None
        value = -math.inf

        for action in state.generate_possible_heavy_actions():
            next_state = action.get_next_game_state()
            _, next_value = self.min_value(next_state, alpha, beta, depth - 1)
            if next_value > value:
                value = next_value
                best_action = action

            alpha = max(alpha, value)

            if beta <= alpha:
                break

        return best_action, value

    def min_value(self, state: GameState, alpha: float, beta: float, depth: int) -> tuple[Action, float]:
        if depth == 0 or state.is_done():
            return None, self.move_heuristic(state)

        best_action = None
        value = math.inf

        for action in state.generate_possible_heavy_actions():
            next_state = action.get_next_game_state()
            _, next_value = self.max_value(next_state, alpha, beta, depth - 1)
            if next_value < value:
                value = next_value
                best_action = action

            beta = min(beta, value)

            if beta <= alpha:
                break

        return best_action, value


    def move_heuristic(self, state: GameState) -> float:
        opponent_id = [key for key in state.scores if key != self.get_id()][0]
        return state.scores[self.get_id()] - state.scores[opponent_id]