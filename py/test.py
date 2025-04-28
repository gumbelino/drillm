

def test():
    return 1,2

x, y = 0, 0

print(x,y)

x,y = test()

print(x,y)

x,y += test()

print(x,y)