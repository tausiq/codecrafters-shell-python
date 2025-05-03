import sys
import os
import shutil
import subprocess


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
            if cmd_to_check in ['echo', 'exit', 'type', 'pwd']:
                print(f"{cmd_to_check} is a shell builtin")
            else:
                # Look for the command in PATH directories
                cmd_path = shutil.which(cmd_to_check)
                if cmd_path:
                    print(f"{cmd_to_check} is {cmd_path}")
                else:
                    print(f"{cmd_to_check}: not found")
        elif command == "pwd":
            print(os.getcwd())
        elif command.startswith('cd'):
            # Extract the directory to change to
            dir_to_change = command[3:].strip()
            # Change the current working directory
            try:
                if dir_to_change == '~': 
                    dir_to_change = os.path.expanduser('~')
                os.chdir(dir_to_change)
            except FileNotFoundError:
                print(f"cd: {dir_to_change}: No such file or directory")
        else: 
            # Parse command and arguments
            command_parts = command.strip().split()

            # Try to execute the command as an external program
            program = command_parts[0]
            args = command_parts[1:]

            try:
                # Execute the command and capture output
                result = subprocess.run([program] + args, capture_output=True, text=True)
                
                # Print stdout
                if result.stdout:
                    print(result.stdout.rstrip())
            except Exception as e:
                print(f"{command}: command not found")


if __name__ == "__main__":
    main()