import concurrent.futures
import subprocess, json
import os, logging
import random, sys, time
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
INITIAL_SET_SIZE = 394  

# 4j = 4 * 24 * 60 = 5760 min
# 30 min par match
# 2 défaites par config
# 4 match en mm temps => 4 défaites par batch
# x = 4 * 5760 / (30 * 2) = 384 config + 10 car on en garde 10 a la fin

LIVES = 2  
SAVE_FILE = "testing_configurations.json"  
DIR = "./Divercite"
ENV = "INF8175"
SHELL = "bash"

AGENT_FILES = ["charalv3.py", "charalv3_2.py"] # SAME AGENT but will retrieve different parameters

# AGENT_FILES = ["greedy_player_divercite.py", "greedy_player_divercite.py"]

# Parameter ranges with (start, stop, step)
PARAM_RANGES = {
    "OPPONENT_SCORE_MULT": (0.5, 2, 0.5), # 4 values
    "THRESHOLD": (30, 60, 10), # 3 values 
    "LEN_DIVIDE": (2, 4, 1), # 3 values
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
    "CITY_COLOR_SCORE": (0.5, 2, 0.5), # 4 values
    "DIV_CITY_HEUR": (0.5, 2, 0.5), # 4 values
    "NEAR_MY_CITY_SCORE": (0.5, 2, 0.5), # 4 values
    "SAME_COLOR_CITY_BONUS": (0, 2, 1), # 3 values
}

def generate_param_values():
    param_values = {}
    for param, (start, stop, step) in PARAM_RANGES.items():
        param_values[param] = np.arange(start, stop, step).tolist()
    return param_values


def initialize_testing_set(size) -> list[dict]:
    param_values = generate_param_values()
    testing_set = []
    i = 0

    while i < (size):
        params = {param: random.choice(values) for param, values in param_values.items()}

        if params in [config["params"] for config in testing_set]:
            print("Duplicate config", params)
            continue

        testing_set.append({"id":i, "params": params, "lives": LIVES, "matches": 0})
        i += 1

    save_testing_set(testing_set)
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


def evaluate_agent(config1, config2, p=1) -> list[tuple[int, int]]:
    agent1_params = json.dumps(config1["params"]).replace('"', '\\"')
    agent2_params = json.dumps(config2["params"]).replace('"', '\\"')

    port = 20000 + p

    if sys.platform == "win32":
        command = (
            f"cmd /c \"cd {DIR} && conda activate {ENV} && "
            f"python main_divercite_custom.py -t local {AGENT_FILES[0]} {AGENT_FILES[1]} -g -p {port} "
            f"\"{agent1_params}\" \"{agent2_params}\"\""
        )
    else:
        command = (
            f"{SHELL} -c \"cd {DIR} && source ~/.{SHELL}rc && source ~/miniconda3/etc/profile.d/conda.sh && conda activate {ENV} && "
            f"python main_divercite_custom.py -t local {AGENT_FILES[0]} {AGENT_FILES[1]} -g -p {port} "
            f"'{agent1_params}' '{agent2_params}'\""
        )

    # logger.info(f"Running command: {command}")

    process_file = f"./matches_logs/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{config1['id']}_vs_{config2['id']}.txt"
    with open(process_file, "w", encoding="cp437") as file:
        result = subprocess.run(
            command,
            shell=True,
            stdout=file,
            stderr=file,
            text=True,
            encoding="cp437"
        )

    # time.sleep(1)

    with open(process_file, "r", encoding="cp437") as file:
        output = file.readlines()
        output.reverse()
        if not output:
            logger.error(f"Error in match between {config1['id']} and {config2['id']}: no output")
            return -1

        err = winner = agent1_score = agent2_score = agent1_time = agent2_time = None

        for j, line in enumerate(output):
            if "ERROR" in line:
                err = line
            if 'Winner -' in line:
                winner = line.split()[-1]
            elif f'{AGENT_FILES[0].replace(".py", "")}_1:' in line and agent1_score is None:
                agent1_score = (line.split(':')[-1].strip())
            elif f'{AGENT_FILES[1].replace(".py", "")}_2:' in line and agent2_score is None:
                agent2_score = (line.split(':')[-1].strip())
            elif f'Player now playing :' in line:
                time_info = (output[j-1].split(':')[-1].strip())
                if f'{AGENT_FILES[0].replace(".py", "")}_1' in line and agent1_time is None:
                    agent1_time = time_info
                elif f'{AGENT_FILES[1].replace(".py", "")}_2' in line and agent2_time is None:
                    agent2_time = time_info

            if agent1_score and agent2_score and agent1_time and agent2_time and winner:
                break

    if err:
        logger.error(f"Error in match between {config1['id']} and {config2['id']}: {err}")
        return -1

    # if "-" in agent1_score or "-" in agent2_score: # negative score
    #     logger.error(f"Error in match between {config1['id']} and {config2['id']}: timeout")
    #     return -1

    winner_id = config1["id"] if winner == AGENT_FILES[0] else config2["id"]
    logger.info(f"Match between {config1['id']}:{agent1_score} and {config2['id']}:{agent2_score}, Time: {agent1_time}-{agent2_time}")

    return winner_id


def run_tournament(testing_set):
    min_matches_done = min([config["matches"] for config in testing_set])

    while len(testing_set) > 10:

        filtered_testing_set = [config for config in testing_set if config["matches"] == min_matches_done]
        batch = random.sample(filtered_testing_set, min(8, len(filtered_testing_set)))
        if len(batch) < 8:
            batch += random.sample(testing_set, 8 - len(batch))
        
        with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(evaluate_agent, batch[i], batch[i+1], i): (batch[i], batch[i+1]) for i in range(0, len(batch), 2)}

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
                    logger.error(f'future exception: {exc}')

        testing_set = [config for config in testing_set if config["lives"] > 0]

        min_matches_done = min([config["matches"] for config in testing_set])

        logger.info(f"Batch done, Testing set size: {len(testing_set)}")    
        save_testing_set(testing_set)


def test_run():
    b = initialize_testing_set(2)
    # logger.info(b)

    evaluate_agent(b[0], b[1])




if __name__ == "__main__":

    if not os.path.exists(DIR):
        logger.error(f"Directory {DIR} does not exist")
        sys.exit(1)
    
    if not os.path.exists(f"matches_logs"):
        os.makedirs(f"matches_logs")

    # test_run()

    testing_set = load_testing_set()
    run_tournament(testing_set)