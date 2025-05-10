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
    
    # Variables to track tab presses and previous text
    tab_count = [0]
    last_text = [""]
    
    def find_longest_common_prefix(strings):
        """Find the longest common prefix of a list of strings"""
        if not strings:
            return ""
        
        shortest = min(strings, key=len)
        for i, char in enumerate(shortest):
            for other in strings:
                if other[i] != char:
                    return shortest[:i]
        return shortest
    
    def completer(text, state):
        """Autocomplete function for readline"""
        # If text changed, reset tab count
        if text != last_text[0]:
            tab_count[0] = 0
            last_text[0] = text
        
        # Filter commands that match the current text
        matches = [cmd for cmd in all_commands if cmd.startswith(text)]
        
        # Handle matched commands
        if len(matches) == 1:
            # Single match - return with a space
            return matches[0] + " " if state == 0 else None
        elif len(matches) > 1:
            # Find the longest common prefix
            common_prefix = find_longest_common_prefix(matches)
            
            # If we can extend the current text, do it without showing options
            if len(common_prefix) > len(text):
                # Don't add a space so user can keep typing
                return common_prefix if state == 0 else None
                
            # If we can't extend (user already typed the common prefix)
            if state == 0:
                # First tab press - increment count and ring bell
                tab_count[0] += 1
                if tab_count[0] == 1:
                    sys.stdout.write('\a')
                    sys.stdout.flush()
                    return None
                # Second tab press - display all matches
                elif tab_count[0] >= 2:
                    print()
                    print("  ".join(sorted(matches)))
                    print(f"$ {readline.get_line_buffer()}", end='')
                    sys.stdout.flush()
                    return None
            # Return the actual completion on subsequent state values
            state_idx = state
            if state_idx < len(matches):
                return matches[state_idx] + " "
            return None
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
        # Find the full path of the command
        command_path = shutil.which(command)
        if not command_path:
            print(f"{command}: command not found")
            return 127
            
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

        # Check for exit command before pipeline processing
        command_line = command_line.strip()
        if command_line == "exit 0":
            break

        # Skip empty commands
        if not command_line:
            continue
            
        # Split the command line by pipes to handle pipelines
        pipeline = [cmd.strip() for cmd in command_line.split(' | ')]
        
        # Process each command in the pipeline
        processes = []
        prev_pipe = None
        
        # Handle each command in the pipeline
        for i, cmd in enumerate(pipeline):
            is_last = i == len(pipeline) - 1
            
            # Handle redirection for this command
            output_file = None
            error_file = None
            stdout_append = False
            stderr_append = False
            
            # Only process redirections for the last command in the pipeline
            if is_last:
                # Check for stderr append redirection (2>>)
                if ' 2>> ' in cmd:
                    cmd_parts = cmd.split(' 2>> ', 1)
                    cmd = cmd_parts[0]
                    if len(cmd_parts) > 1 and cmd_parts[1].strip():
                        error_file = cmd_parts[1].strip()
                        stderr_append = True
                # Check for stderr redirection (2>)
                elif ' 2> ' in cmd:
                    cmd_parts = cmd.split(' 2> ', 1)
                    cmd = cmd_parts[0]
                    if len(cmd_parts) > 1 and cmd_parts[1].strip():
                        error_file = cmd_parts[1].strip()
                
                # Check for stdout append redirection (>> or 1>>)
                if ' >> ' in cmd or ' 1>> ' in cmd:
                    # Split by redirection operator
                    if ' >> ' in cmd:
                        cmd_parts = cmd.split(' >> ', 1)
                    else:
                        cmd_parts = cmd.split(' 1>> ', 1)
                        
                    cmd = cmd_parts[0]
                    if len(cmd_parts) > 1 and cmd_parts[1].strip():
                        output_file = cmd_parts[1].strip()
                        stdout_append = True
                # Check for stdout redirection (> or 1>)
                elif ' > ' in cmd or ' 1> ' in cmd:
                    # Split by redirection operator
                    if ' > ' in cmd:
                        cmd_parts = cmd.split(' > ', 1)
                    else:
                        cmd_parts = cmd.split(' 1> ', 1)
                        
                    cmd = cmd_parts[0]
                    if len(cmd_parts) > 1 and cmd_parts[1].strip():
                        output_file = cmd_parts[1].strip()

            # Parse with quote awareness
            parts = shlex.split(cmd.strip(), posix=True)
            if not parts:
                continue
                
            command = parts[0]
            args = parts[1:]

            # Handle built-in commands
            if command == "exit" and len(args) == 1 and args[0] == "0":
                # Clean up any processes
                for p in processes:
                    if p.poll() is None:
                        p.terminate()
                break

            # For built-in commands in a pipeline, we need to capture their output
            if command in ["echo", "type", "pwd", "cd"]:
                # Create pipes for stdin and stdout
                if prev_pipe:
                    stdin_source = prev_pipe
                else:
                    stdin_source = subprocess.PIPE
                
                # For the last command, we may need to redirect
                if is_last and not output_file and not error_file:
                    stdout_dest = None  # Terminal
                else:
                    stdout_dest = subprocess.PIPE

                # Create a new pipe for the next command
                if not is_last:
                    next_pipe_read, next_pipe_write = os.pipe()
                    stdout_dest = next_pipe_write
                else:
                    next_pipe_read = None

                # Capture built-in command output
                output = None
                
                # Handle redirected output
                original_stdout = None
                original_stderr = None
                stdout_file = None
                stderr_file = None
                
                try:
                    # Redirect stdout if specified and this is the last command
                    if is_last and output_file:
                        original_stdout = sys.stdout
                        # Use append mode if >> was used, otherwise use write mode
                        mode = 'a' if stdout_append else 'w'
                        stdout_file = open(output_file, mode)
                        sys.stdout = stdout_file
                        
                    # Redirect stderr if specified and this is the last command
                    if is_last and error_file:
                        original_stderr = sys.stderr
                        # Use append mode if 2>> was used, otherwise use write mode
                        mode = 'a' if stderr_append else 'w'
                        stderr_file = open(error_file, mode)
                        sys.stderr = stderr_file

                    # Execute built-in command
                    if command == "echo":
                        execute_echo(args)
                    elif command == "type":
                        execute_type(args)
                    elif command == "pwd":
                        print(os.getcwd())
                    elif command == "cd":
                        execute_cd(args)
                        
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
                        
                prev_pipe = next_pipe_read
            else:
                # Execute external command with pipeline
                
                # Set up stdin - connect to previous pipe if not the first command
                if prev_pipe:
                    stdin_source = prev_pipe
                else:
                    stdin_source = subprocess.PIPE
                
                # Set up stdout - create a pipe if not the last command
                if not is_last:
                    stdout_dest = subprocess.PIPE
                else:
                    # For the last command, set up redirections if needed
                    if output_file:
                        mode = 'a' if stdout_append else 'w'
                        stdout_file = open(output_file, mode)
                        stdout_dest = stdout_file
                    else:
                        stdout_dest = None  # Terminal
                
                # Set up stderr redirection
                if error_file:
                    mode = 'a' if stderr_append else 'w'
                    stderr_file = open(error_file, mode)
                    stderr_dest = stderr_file
                else:
                    stderr_dest = None  # Terminal
                
                # Find the full path of the command
                # command_path = shutil.which(command)
                # if not command_path:
                #     print(f"{command}: command not found")
                #     break
                
                # Create the process
                try:
                    process = subprocess.Popen(
                        [command] + args,
                        stdin=stdin_source,
                        stdout=stdout_dest,
                        stderr=stderr_dest,
                        text=True
                    )
                    processes.append(process)
                    
                    # Store pipe file descriptor for next command
                    prev_pipe = process.stdout
                except Exception as e:
                    print(f"{command}: command not found", file=sys.stderr)
                    break
        
        # Wait for all processes to finish
        for process in processes:
            process.wait()
        
        # Close any open file descriptors
        for process in processes:
            if process.stdout:
                process.stdout.close()
            if process.stderr:
                process.stderr.close()



if __name__ == "__main__":
    main()