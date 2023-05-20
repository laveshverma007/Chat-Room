import subprocess

cmd1 = "python3 main.py"
cmd2 = "cd uploads && python3 server.py"

p1 = subprocess.Popen(cmd1,shell=True)
p2 = subprocess.Popen(cmd2,shell=True)
p1.wait()
p2.wait()
