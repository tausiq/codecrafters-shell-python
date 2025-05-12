import sys
import os
import shlex
import shutil
import subprocess
import readline
import io 
import tempfile


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
    if cmd_to_check in ['echo', 'exit', 'type', 'pwd', 'cd']:
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


def execute_external_command(command, args, stdin=None, stdout=None, stderr=None):
    """Execute an external command with arguments"""
    try:
        # Execute the command with specified I/O redirections
        process = subprocess.Popen(
            [command] + args,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            text=True
        )
        return process
    except FileNotFoundError:
        print(f"{command}: command not found", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error executing {command}: {str(e)}", file=sys.stderr)
        return None


def parse_redirections(cmd):
    """Parse a command string and extract redirection operators and file paths"""
    output_file = None
    error_file = None
    stdout_append = False
    stderr_append = False
    
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
    
    return cmd, output_file, error_file, stdout_append, stderr_append


def execute_builtin(command, args, output_file=None, error_file=None, 
                    stdout_append=False, stderr_append=False, is_last=True):
    """Execute a built-in command with redirection handling"""
    # Prepare to capture the output
    output_stream = io.StringIO()
    error_stream = io.StringIO()
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    try:
        # Redirect stdout and stderr to our string buffers
        sys.stdout = output_stream
        sys.stderr = error_stream
        
        # Execute built-in command
        if command == "echo":
            execute_echo(args)
        elif command == "type":
            execute_type(args)
        elif command == "pwd":
            print(os.getcwd())
        elif command == "cd":
            execute_cd(args)
            
        # Get the captured output
        captured_output = output_stream.getvalue()
        captured_error = error_stream.getvalue()
        
        # If this is the last command, handle outputs
        if is_last:
            # Restore original stdout and stderr
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            
            # Handle file redirection for stdout if needed
            if output_file:
                mode = 'a' if stdout_append else 'w'
                with open(output_file, mode) as f:
                    f.write(captured_output)
            else:
                # Print to console
                print(captured_output, end='')
                
            # Handle file redirection for stderr if needed
            if error_file:
                mode = 'a' if stderr_append else 'w'
                with open(error_file, mode) as f:
                    f.write(captured_error)
            elif captured_error:  # Only print if there are errors
                print(captured_error, end='', file=sys.stderr)
            
            return None
        else:
            # This is not the last command, prepare output for pipeline
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            temp_file = tempfile.TemporaryFile(mode='w+t')
            temp_file.write(captured_output)
            temp_file.seek(0)  # Rewind to start of file
            
            return temp_file
    finally:
        # Always restore stdout and stderr
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        output_stream.close()
        error_stream.close()


def execute_pipeline(pipeline):
    """Execute a pipeline of commands"""
    processes = []
    prev_pipe = None
    
    for i, cmd in enumerate(pipeline):
        is_last = i == len(pipeline) - 1
        
        # Parse redirections (only apply to last command)
        if is_last:
            cmd, output_file, error_file, stdout_append, stderr_append = parse_redirections(cmd)
        else:
            cmd = cmd.strip()
            output_file = error_file = None
            stdout_append = stderr_append = False
        
        # Parse the command with quote awareness
        try:
            parts = shlex.split(cmd.strip(), posix=True)
        except ValueError:
            print("Syntax error: unclosed quotes")
            return
            
        if not parts:
            continue
            
        command = parts[0]
        args = parts[1:]
        
        # Handle exit command
        if command == "exit" and len(args) == 1 and args[0] == "0":
            # Clean up any processes
            for p in processes:
                if p.poll() is None:
                    p.terminate()
            return True  # Signal to exit the shell
        
        # Execute the command
        if command in ["echo", "type", "pwd", "cd"]:
            # Built-in command
            next_stdin = execute_builtin(
                command, args, 
                output_file, error_file, 
                stdout_append, stderr_append, 
                is_last
            )
            
            if next_stdin and not is_last:
                prev_pipe = next_stdin
        else:
            # External command
            # Set up stdin
            stdin_source = prev_pipe if prev_pipe else None
            
            # Set up stdout
            if not is_last:
                stdout_dest = subprocess.PIPE
            else:
                # For the last command, set up redirections if needed
                if output_file:
                    mode = 'a' if stdout_append else 'w'
                    stdout_dest = open(output_file, mode)
                else:
                    stdout_dest = None  # Terminal
            
            # Set up stderr
            if error_file:
                mode = 'a' if stderr_append else 'w'
                stderr_dest = open(error_file, mode)
            else:
                stderr_dest = None  # Terminal
            
            # Execute the command
            process = execute_external_command(
                command, args,
                stdin=stdin_source,
                stdout=stdout_dest,
                stderr=stderr_dest
            )
            
            if not process:
                break
                
            processes.append(process)
            
            # Store pipe file descriptor for next command
            if not is_last:
                prev_pipe = process.stdout
    
    # Wait for all processes to finish
    for process in processes:
        process.wait()
    
    # Clean up resources
    for process in processes:
        if process.stdout:
            process.stdout.close()
        if process.stderr:
            process.stderr.close()
    
    return False  # Don't exit the shell


def main():
    """Main shell loop"""

    # Setup autocompletion before entering the loop
    setup_autocomplete()

    while True:
        # Display prompt
        sys.stdout.write("$ ")
        command_line = input()

            
        # Split the command line by pipes to handle pipelines
        pipeline = [cmd.strip() for cmd in command_line.split(' | ')]
        
        # Execute the pipeline
        should_exit = execute_pipeline(pipeline)
        if should_exit:
            break


if __name__ == "__main__":
    main()