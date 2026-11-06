from sys import argv
from mapgen import Parser, Map, Algorithm
from pydantic import ValidationError
from typing import Any


def main() -> None:
    if len(argv) == 2:
        try:
            with open(argv[1]) as file:
                data: dict[str, Any] = Parser.parse([line for line in file.
                                                     read().splitlines()])
                fly_map: Map = Map(**data)
                algorithm: Algorithm = Algorithm(fly_map)
                turn_moves: dict[int, list[str]] = algorithm.run()
                for turn, moves in turn_moves.items():
                    print(f"Turn {turn}: {' '.join(moves)}")
        except ValidationError as e:
            for error in e.errors():
                message: str = ""
                if error["msg"].startswith("Value error, "):
                    message = error["msg"].split('Value error, ')[1]
                else:
                    message = error["msg"]
                print(f"Error: {message}")
        except ValueError as e:
            print(f"Error: {e}")
        except Exception:
            print(f"file '{argv[1]}' not found")
    else:
        print("Usage: python3 main.py map.txt")


if __name__ == "__main__":
    main()
