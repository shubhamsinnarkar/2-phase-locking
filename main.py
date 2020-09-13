
def begin(b):
    print(f"Trasaction for {b} started")

def end(e):
    print(f"Trasaction for {e} started")

def read(r):
    print(f"Trasaction for {r} started")

def write(w):
    print(f"Trasaction for {w} started")

with open('input.txt','r') as file:
    print(file.read().strip().split(';'))
