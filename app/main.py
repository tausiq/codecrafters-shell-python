import sys
import os
import shlex
import shutil
import subprocess
import readline  # Add this import


def setup_autocomplete():
    """Set up command autocompletion for the shell"""
    # List of built-in commands
    builtin_commands = ['echo', 'exit', 'type', 'pwd', 'cd']
    
    # Get commands from PATH
    path_commands = []
    for path_dir in os.environ.get('PATH', '').split(':'):
        if os.path.isdir(path_dir):
            try:
                for file in os.listdir(path_dir):
                    file_path = os.path.join(path_dir, file)
                    if os.access(file_path, os.X_OK) and os.path.isfile(file_path):
                        path_commands.append(file)
            except (PermissionError, FileNotFoundError):
                # Skip directories we can't access
                pass
    
    # Combine built-in and PATH commands (remove duplicates)
    all_commands = list(set(builtin_commands + path_commands))
    
    def completer(text, state):
        """Autocomplete function for readline"""
        # Filter commands that match the current text
        options = [cmd + ' ' for cmd in all_commands if cmd.startswith(text)]

        if state < len(options):
            return options[state]
        else:
            return None
    
    # Register the completer function
    readline.parse_and_bind("tab: complete")
    readline.set_completer(completer)

def execute_echo(args):
    """Handle the echo command"""
    print(" ".join(args))


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
    # Set up autocompletion
    setup_autocomplete()

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
            
        # Handle redirection before parsing with shlex
        output_file = None
        error_file = None
        stdout_append = False
        stderr_append = False
        
        # Check for stderr append redirection (2>>)
        if ' 2>> ' in command_line:
            cmd_parts = command_line.split(' 2>> ', 1)
            command_line = cmd_parts[0]
            if len(cmd_parts) > 1 and cmd_parts[1].strip():
                error_file = cmd_parts[1].strip()
                stderr_append = True
        # Check for stderr redirection (2>)
        elif ' 2> ' in command_line:
            cmd_parts = command_line.split(' 2> ', 1)
            command_line = cmd_parts[0]
            if len(cmd_parts) > 1 and cmd_parts[1].strip():
                error_file = cmd_parts[1].strip()
        
        # Check for stdout append redirection (>> or 1>>)
        if ' >> ' in command_line or ' 1>> ' in command_line:
            # Split by redirection operator
            if ' >> ' in command_line:
                cmd_parts = command_line.split(' >> ', 1)
            else:
                cmd_parts = command_line.split(' 1>> ', 1)
                
            command_line = cmd_parts[0]
            if len(cmd_parts) > 1 and cmd_parts[1].strip():
                output_file = cmd_parts[1].strip()
                stdout_append = True
        # Check for stdout redirection (> or 1>)
        elif ' > ' in command_line or ' 1> ' in command_line:
            # Split by redirection operator
            if ' > ' in command_line:
                cmd_parts = command_line.split(' > ', 1)
            else:
                cmd_parts = command_line.split(' 1> ', 1)
                
            command_line = cmd_parts[0]
            if len(cmd_parts) > 1 and cmd_parts[1].strip():
                output_file = cmd_parts[1].strip()

        # Parse with quote awareness
        parts = shlex.split(command_line.strip(), posix=True)
        if not parts:
            continue
            
        command = parts[0]
        args = parts[1:]

        # Handle redirected output
        original_stdout = None
        original_stderr = None
        stdout_file = None
        stderr_file = None
        
        try:
            # Redirect stdout if specified
            if output_file:
                original_stdout = sys.stdout
                # Use append mode if >> was used, otherwise use write mode
                mode = 'a' if stdout_append else 'w'
                stdout_file = open(output_file, mode)
                sys.stdout = stdout_file
                
            # Redirect stderr if specified
            if error_file:
                original_stderr = sys.stderr
                # Use append mode if 2>> was used, otherwise use write mode
                mode = 'a' if stderr_append else 'w'
                stderr_file = open(error_file, mode)
                sys.stderr = stderr_file

            # Execute the command with redirected output if applicable
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
        finally:
            # Restore stdout if it was redirected
            if stdout_file:
                stdout_file.close()
            if original_stdout:
                sys.stdout = original_stdout
                
            # Restore stderr if it was redirected
            if stderr_file:
                stderr_file.close()
            if original_stderr:
                sys.stderr = original_stderr



if __name__ == "__main__":
    main()