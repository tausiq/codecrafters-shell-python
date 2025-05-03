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
        elif command.startswith('echo'):
            # Extract the message to echo
            message = command[5:]
            # Print the message
            print(message)
        elif command.startswith('type'):
            command = command[5:]
            # Check if the command is "exit"
            if command == 'echo' or command == 'exit' or command == 'type':
                print(f"{command} is a shell builtin")
            else: 
                print(f"{command}: not found")
        else: 
            print(f"{command}: command not found")


if __name__ == "__main__":
    main()
