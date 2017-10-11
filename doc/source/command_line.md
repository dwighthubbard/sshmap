## SSHMap Command Line

### Usage

    usage: sshmap [-h] [--jobs JOBS] [--timeout TIMEOUT] [--sort] [--shuffle]
                  [--output_terse_headers] [--output_json] [--output_base64]
                  [--summarize_failed] [--aggregate_output] [--only_output]
                  [--print_rc] [--match MATCH] [--no_status]
                  [--runscript RUNSCRIPT] [--callback_script CALLBACK_SCRIPT]
                  [--sudo] [--username] [--password]
                  hostrange [command [command ...]]

    positional arguments:
      hostrange             Hostlists hostrange of hosts to operate on
      command               Command to run on the remote system

    optional arguments:
      -h, --help            show this help message and exit

    Job Settings:
      --jobs JOBS, -j JOBS  Number of parallel commands to execute
      --timeout TIMEOUT     Timeout, or 0 for no timeout
      --sort                Print output sorted in the order listed
      --shuffle             Shuffle (randomize) the order of hosts

    Output Formats:
      --output_terse_headers
                            Use more compact headers
      --output_json         Output in JSON format
      --output_base64       Output in base64 format

    Output Options:
      --summarize_failed    Print a list of hosts that failed at the end
      --aggregate_output, --collapse
                            Aggregate identical list
      --only_output         Only print lines for hosts that return output
      --print_rc            Print the return code value
      --match MATCH         Only show host output if the string is found in the
                            output
      --no_status           Don't show a status count as the command progresses

    Execution Options:
      --runscript RUNSCRIPT, --run_script RUNSCRIPT
                            Run a script on all hosts. The command value is the
                            shell to pass the script to on the remote host.
      --callback_script CALLBACK_SCRIPT
                            Script to process the output of each host. The
                            hostname will be passed as the first argument and the
                            stdin/stderr from the host will be passed as
                            stdin/stderr of the script
      --sudo                Use sudo to run the command as root
      --username            Prompt for a password
      --password            Prompt for a password
