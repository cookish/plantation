import os
import subprocess
import json
from player import Player

class PHPPlayerWrapper(Player):

    def __init__(self, name: str):
        super().__init__(name)
        self.php_script_path = os.path.join(os.path.dirname(__file__), "genetic.php")
        self.process = subprocess.Popen(["php", self.php_script_path],
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        text=True)
        self.send_call( {
            "function": "init",
            "name": name
        } )

    def send_call(self, data):
        json_data = json.dumps(data) + "\n"  # Add newline to signal end of input
        #print(json_data)
        self.process.stdin.write(json_data)
        self.process.stdin.flush()
        response = self.process.stdout.readline()
        #print(response)
        return json.loads(response)

    def start_game(self, board_size, sign):
        super().start_game(board_size, sign)
        data = {
            "function": "start_game",
            "sign": sign
        }
        return self.send_call(data)

    def get_move(self, board, turn, moves_remaining, time_remaining):
        # Prepare the data to send
        data = {
            "function": "get_move",
            "board": board.tolist(),  # Convert numpy array to list
            "turn": turn,
            "moves_remaining": moves_remaining,
            "time_remaining": time_remaining
        }
        return self.send_call(data)

    def handle_move_result(self, move, turn, pos, result):
        # Prepare the data to send
        data = {
            "function": "handle_move_result",
            "move": move,
            "turn": turn,
            "pos": pos, # Convert numpy array to list
            "result": result
        }
        return self.send_call(data)

    def end_game(self, your_score: int, opponent_score: int):
        data = {
            "function": "end_game",
            "your_score": int(your_score),
            "opponent_score": int(opponent_score)
        }
        return self.send_call(data)

    def close(self):
        self.process.terminate()

    def __del__(self):
        self.close()
