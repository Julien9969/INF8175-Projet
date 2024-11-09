import subprocess
import concurrent.futures
from rich.console import Console
from rich.table import Table
from collections import Counter
from rich.text import Text
import sys, time, threading


DIR = "./Divercite"
ENV = "INF8175"
SHELL = "bash"

# agent1_name = "greedy_player_divercite.py" #"2000.py"
# agent2_name = "greedy_player_divercite.py" #findus200v2.py"

agent1_name = "charalv3.py"
agent2_name = "charalv3.py"

class GameResult:
    def __init__(self, i, agent1, score1, time1, agent2, score2, time2, winner):
        self.i = i
        self.agent1 = agent1
        self.score1 = score1
        self.time1 = time1
        self.agent2 = agent2
        self.score2 = score2
        self.time2 = time2
        self.winner = winner

    def __str__(self):
        return f"Game {self.i} - {self.agent1} vs {self.agent2} - Winner: {self.winner}"    


def live_elapsed_time(start_time):
    while True:
        elapsed_time = time.time() - start_time
        sys.stdout.write(f"\rElapsed Time: {elapsed_time:.2f} seconds")
        sys.stdout.flush()
        time.sleep(1)


def play_game(agent1: str, agent2: str, i: int, port):

    if sys.platform == "win32":
        command = f"cmd /c \"cd {DIR} && conda activate {ENV} && python main_divercite.py -t local {agent1} {agent2} -g -p {port}\""
    else:
        command = f"{SHELL} -c \"cd {DIR} && source ~/.{SHELL}rc && source ~/miniconda3/etc/profile.d/conda.sh && conda activate {ENV} && python main_divercite.py -t local {agent1} {agent2} -g -p {port}\""
    
    print(f"Start Game {i} - {agent1} vs {agent2} on port {port}")
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="cp437")
    
    output = result.stdout.splitlines()[::-1]
    
    agent1_score = agent2_score = agent1_time = agent2_time = None
    winner = None

    for j, line in enumerate(output):
        # print(line)
        if "ERROR" in line:
            print(f"#{i}-{line}")
        if 'Winner -' in line:
            winner = line.split()[-1]
        elif f'{agent2.replace(".py", "")}_2:' in line and agent2_score is None:
            agent2_score = (line.split(':')[-1].strip())
        elif f'{agent1.replace(".py", "")}_1:' in line and agent1_score is None:
            agent1_score = (line.split(':')[-1].strip())
        elif f'Player now playing :' in line:
            time_info = (output[j-1].split(':')[-1].strip())
            # print(time_info)
            if f'{agent1.replace(".py", "")}_1' in line and agent1_time is None:
                agent1_time = time_info
            elif f'{agent2.replace(".py", "")}_2' in line and agent2_time is None:
                agent2_time = time_info

        if agent1_score is not None and agent2_score is not None and winner is not None and agent1_time is not None and agent2_time is not None:
            break

    return GameResult(i, agent1, agent1_score, agent1_time, agent2, agent2_score, agent2_time, winner)

def run_simulation() -> list[GameResult]:
    results: list[GameResult] = []
    start_time = time.time()
    n_process = 6

    elapsed_time_thread = threading.Thread(target=live_elapsed_time, args=(start_time,), daemon=True)
    elapsed_time_thread.start()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        
        for i in range(3):
            futures.append(executor.submit(play_game, agent1_name, agent2_name, i, 16565 + i))
        
        for i in range(3, 6):
            futures.append(executor.submit(play_game, agent2_name, agent1_name, i, 16565 + i))
        
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    final_elapsed_time = time.time() - start_time
    sys.stdout.write(f"\rSimulation complete. Total Time: {final_elapsed_time:.2f} seconds\n")
    sys.stdout.flush()
    return results

def display_results(results: list[GameResult]):
    console = Console()
    table = Table(title="Game Results")

    table.add_column("Execution #", justify="center")
    table.add_column("Agent 1", justify="center")
    table.add_column("Time", justify="center")
    table.add_column("Agent 2", justify="center")
    table.add_column("Time", justify="center")

    win_counter = Counter()

    for result in sorted(results, key=lambda x: x.i):
        agent1_style = "green bold" if result.winner == f"{result.agent1[:-3]}_1" else "red"
        agent2_style = "green bold" if result.winner == f"{result.agent2[:-3]}_2" else "red"

        table.add_row(
            str(result.i),
            Text(f"{result.agent1} : {result.score1}", style=agent1_style) if result.score1 is not None else "N/A",
            str(result.time1[:5]) if result.time1 is not None else "N/A",
            Text(f"{result.agent2} : {result.score2}", style=agent2_style) if result.score2 is not None else "N/A",
            str(result.time2[:5]) if result.time2 is not None else "N/A",
        )
        win_counter[result.winner] += 1

    console.print(table)

    best_agent = win_counter.most_common(1)[0][0]
    win_ratio = win_counter[best_agent] / 6
    console.print(f"\nBest Agent: {best_agent}, Win Ratio: {win_ratio:.2f}\n")


def test_subprocess(command):
    try:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="cp437")
        output = result.stdout

        if result.returncode == 0:
            print("Command executed successfully.")
            print("Output:")
            print(output)  
        else:
            print("Command failed.")
            print("Error Output:")
            print(result.stderr)  
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # command_to_test = "cmd /c \"cd ./Divercite && conda activate INF8175 && python main_divercite.py -t local greedy_player_divercite.py greedy_player_divercite.py -g -p 16565\""
    # test_subprocess("dir")
    # test_subprocess("cmd /c \"cd ./Divercite && conda activate INF8175 && python main_divercite.py -t local greedy_player_divercite.py greedy_player_divercite.py -g -p 16565\"")
    results = run_simulation()
    display_results(results)

    # test_subprocess("zsh -c \"cd ./Divercite && source ~/.zshrc && conda activate INF8175 && python main_divercite.py -t local greedy_player_divercite.py greedy_player_divercite.py -g -p 16565\"")
