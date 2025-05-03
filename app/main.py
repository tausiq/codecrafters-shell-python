import sys
import os
import shutil
import subprocess


def execute_echo(args):
    """Handle the echo command"""
    message = ' '.join(args)
    print(message)


def execute_type(args):
    """Handle the type command"""
    if not args:
        return
        
    cmd_to_check = args[0]
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


def execute_cd(args):
    """Handle the cd command"""
    if not args:
        return
        
    dir_to_change = args[0]
    # Change the current working directory
    try:
        if dir_to_change == '~':
            dir_to_change = os.path.expanduser('~')
        os.chdir(dir_to_change)
    except FileNotFoundError:
        print(f"cd: {dir_to_change}: No such file or directory")


def execute_external_command(command, args):
    """Execute an external command with arguments"""
    try:
        # Execute the command and capture output
        result = subprocess.run([command] + args, capture_output=True, text=True)
        
        # Print stdout
        if result.stdout:
            print(result.stdout.rstrip())
            
        # Print stderr if any
        if result.stderr:
            print(result.stderr.rstrip(), file=sys.stderr)
            
        return result.returncode
    except FileNotFoundError:
        print(f"{command}: command not found")
        return 127
    except Exception as e:
        print(f"Error executing {command}: {str(e)}", file=sys.stderr)
        return 1


def main():
    """Main shell loop"""
    while True:
        # Display prompt
        sys.stdout.write("$ ")
        sys.stdout.flush()

        # Get command input
        try:
            command_line = input()
        except EOFError:
            # Handle Ctrl+D gracefully
            print()
            break

        # Skip empty commands
        if not command_line.strip():
            continue

        # Parse command and arguments
        parts = command_line.strip().split()
        if not parts:
            continue
            
        command = parts[0]
        args = parts[1:]

        # Handle built-in commands
        if command == "exit" and len(args) == 1 and args[0] == "0":
            break
        elif command == "echo":
            execute_echo(args)
        elif command == "type":
            execute_type(args)
        elif command == "pwd":
            print(os.getcwd())
        elif command == "cd":
            execute_cd(args)
        else:
            # Try to execute as external command
            execute_external_command(command, args)


if __name__ == "__main__":
    main()