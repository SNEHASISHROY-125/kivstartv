import subprocess

def get_display_names(): 
	result = subprocess.run(['xrandr', '--query'], stdout=subprocess.PIPE, text=True) 
	lines = result.stdout.splitlines() 
	displays = [line for line in lines: if ' connected ' in line: display = line.split()[0] displays.append(display) ]
	return displays

print(get_display_names())