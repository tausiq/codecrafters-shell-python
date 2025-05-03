import sys
import os
import shutil


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
            cmd_to_check = command[5:].strip()
            # Check if the command is a shell builtin
            if cmd_to_check in ['echo', 'exit', 'type']:
                print(f"{cmd_to_check} is a shell builtin")
            else:
                # Look for the command in PATH directories
                cmd_path = shutil.which(cmd_to_check)
                if cmd_path:
                    print(f"{cmd_to_check} is {cmd_path}")
                else:
                    print(f"{cmd_to_check}: not found")
        else: 
            print(f"{command}: command not found")


if __name__ == "__main__":
    main()