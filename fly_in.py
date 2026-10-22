from sys import argv, exit
from mapgen import Parser, Map, Algorithm
from pydantic import ValidationError
from typing import Any


def main() -> None:
    if len(argv) == 2:
        try:
            with open(argv[1]) as file:
                data: dict[str, Any] = Parser.parse([line for line in file.
                                                     read().splitlines()
                                                     if line and not
                                                     line.startswith("#")])
                fly_map = Map(**data)
                algorithm = Algorithm(fly_map)
                algorithm.run()
        except ValidationError as e:
            for error in e.errors():
                message: str = ""
                if error["msg"].startswith("Value error, "):
                    message = error["msg"].split('Value error, ')[1]
                else:
                    message = error["msg"]
                print(f"Error: {message}")
            exit(1)
        except ValueError as e:
            print(f"Error: {e}")
            exit(1)
    else:
        print("Usage: python3 main.py map.txt")


if __name__ == "__main__":
    main()
