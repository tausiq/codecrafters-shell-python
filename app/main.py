import sys


def main():
    while True: 
        # Uncomment this block to pass the first stage
        sys.stdout.write("$ ")

        # Wait for user input
        command = input()

        # Check if the command is "exit"
        if command == "exit 0":
            break 

        print(f"{command}: command not found")


if __name__ == "__main__":
    main()
