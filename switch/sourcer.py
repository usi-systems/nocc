# Source: http://stackoverflow.com/questions/3503719/emulating-bash-source-in-python
import subprocess

def sourceFile(filename):
    command = ['bash', '-c', 'source %s && set' % filename]
    proc = subprocess.Popen(command, stdout = subprocess.PIPE)
    env_vars = {}
    for line in proc.stdout:
      (key, _, value) = line.partition("=")
      env_vars[key] = value.strip('\n')
    proc.communicate()
    return env_vars
