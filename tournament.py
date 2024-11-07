import concurrent.futures
import subprocess, json
import os, logging
import random, sys
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('tournament.log')
console_handler = logging.StreamHandler()

file_handler.setLevel(logging.INFO)
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s | %(message)s | %(levelname)s - %(name)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Constants
INITIAL_SET_SIZE = 500  
LIVES = 3  
SAVE_FILE = "testing_configurations.json"  
DIR = "./Divercite"
ENV = "INF8175"
SHELL = "zsh"

AGENT_FILES = ["charalv3.py", "charalv3_2.py"] # SAME AGENT but will retrieve different parameters

# Parameter ranges with (start, stop, step)
PARAM_RANGES = {
    "OPPONENT_SCORE_MULT": (0.5, 2, 0.5), # 4 values
    "THRESHOLD": (30, 60, 10), # 3 values 
    "LEN_DIVIDE": (1, 4, 1), # 3 values
    "MAX_ACTIONS": (20, 50, 10), # 3 values 
    "SELF_CITY_GAIN_MULT": (0.5, 2, 0.5), # 4 values
    "OPPONENT_CITY_GAIN_MULT": (0.5, 2, 0.5), # 4 values 
    "RESSOURCE_BALANCE": (1, 4, 1), # 3 values
    "CITY_BALANCE": (1, 4, 1), # 3 values
    "DIVERSITY_SCORE": (4, 10, 1), # 6 values
    "STILL_POSSIBLE_DIVERSITY_MULT": (0.5, 2, 0.5), # 4 values
    "SCORE_FOR_COLOR_MULT": (0.5, 2, 0.5), # 4 values
    "CANCEL_DIVERSITY_SCORE": (1, 6, 1), # 5 values
    "CANCEL_IN_PROGRESS_DIVERSITY_SCORE": (0, 3, 1), # 3 values
    "NOT_COMPLETABLE_DIVERSITY_SCORE": (0, 3, 1), # 3 values
    "BONUS_CANCEL_WITH_OTHER_COL": (0, 3, 1), # 3 values
    "NEAR_OPPONENT_CITY_SCORE": (0.5, 2, 0.5), # 4 values
    "DIFFERENT_COLOR_CITY_BONUS": (0.5, 2, 0.5), # 4 values
    "IN_PROGRESS_DIVERSITY_MULT": (0.5, 2, 0.5), # 4 values
    "CITY_COLOR_SCORE": (0.5, 2, 0.5) # 4 values
}

def generate_param_values():
    param_values = {}
    for param, (start, stop, step) in PARAM_RANGES.items():
        param_values[param] = np.arange(start, stop, step).tolist()
    return param_values


def initialize_testing_set(size):
    param_values = generate_param_values()
    testing_set = []

    for i in range(size):
        params = {param: random.choice(values) for param, values in param_values.items()}
        testing_set.append({"id":i, "params": params, "lives": LIVES, "matches": 0})
    
    return testing_set


def save_testing_set(testing_set):
    with open(SAVE_FILE, "w") as f:
        json.dump(testing_set, f, indent=4)


def load_testing_set():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    else:
        return initialize_testing_set(INITIAL_SET_SIZE)


def evaluate_agent(config1, config2) -> list[tuple[int, int]]:
    agent1_params = config1["params"]
    agent2_params = config2["params"]
    port = 20000 + config1["id"] 

    if sys.platform == "win32":
        command = (
            f"cmd /c \"cd {DIR} && conda activate {ENV} && "
            f"python main_divercite.py -t local {AGENT_FILES[0]} {AGENT_FILES[1]} -g -p {port} '{agent1_params}' '{agent2_params}'\""
        )
    else:
        command = (
            f"{SHELL} -c \"cd {DIR} && source ~/.{SHELL}rc && conda activate {ENV} && "
            f"python main_divercite.py -t local {AGENT_FILES[0]} {AGENT_FILES[1]} -g -p {port} '{agent1_params}' '{agent2_params}'\""
        )

    process_file = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{config1['id']}_vs_{config2['id']}.txt"
    with open(process_file, "w") as file:
        result = subprocess.run(
            command,
            shell=True,
            stdout=file,
            stderr=file,
            text=True,
            encoding="cp437"
        )

    with open(process_file, "r") as file:
        output = file.readlines().reverse()


    logger.info(f"Match between {config1['id']} and {config2['id']} done. Winner: {winner_id}")

    # Parse the output to get the winner and the score
    return winner_id


def run_tournament(testing_set):
    min_matches_done = min([config["matches"] for config in testing_set])

    while len(testing_set) > 10:

        filtered_testing_set = [config for config in testing_set if config["matches"] == min_matches_done]
        batch = random.sample(filtered_testing_set, min(16, len(filtered_testing_set)))
        if len(batch) < 16:
            batch += random.sample(testing_set, 16 - len(batch))
        
        with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(evaluate_agent, batch[i], batch[i+1]): (batch[i], batch[i+1]) for i in range(0, len(batch), 2)}

            for future in concurrent.futures.as_completed(futures):
                config1, config2 = futures[future]
                try:
                    winner_id = future.result()

                    if winner_id != config1["id"]:
                        config1["lives"] -= 1
                    else:
                        config2["lives"] -= 1

                    config1["matches"] += 1
                    config2["matches"] += 1

                except Exception as exc:
                    print(f'Generated an exception: {exc}')

        testing_set = [config for config in testing_set if config["lives"] > 0]

        min_matches_done = min([config["matches"] for config in testing_set])
        save_testing_set(testing_set)


if __name__ == "__main__":

    testing_set = load_testing_set()
    run_tournament(testing_set)