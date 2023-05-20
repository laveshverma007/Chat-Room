import subprocess

# command 1
cmd1 = "python3 main.py"

# command 2
cmd2 = "cd uploads && python3 server.py"

# run both commands concurrently
p1 = subprocess.Popen(cmd1, shell=True)
p2 = subprocess.Popen(cmd2, shell=True)

# wait for both commands to finish
p1.wait()
p2.wait()
