print(int("101010",2)) #1 42
print(int("563",8)) #2 371
print(int("a1286",12)) #3 209478

x=bin(127)
print(x.count("1")) #4 7

x=367
list=[]
while x>0:
    k=(x%7)
    x=x//7
    list.append(k)
print(list[::-1]) #5 1033

x=1143
list=[]
while x>0:
    k=(x%12)
    x=x//12
    list.append(k)
print(list[::-1]) #6 7b33

x=127
list=[]
while x>0:
    k=(x%9)
    x=x//9
    list.append(k)
print(list[::-1]) #7 151

x=10114
list=[]
while x>0:
    k=(x%6)
    x=x//6
    list.append(k)
print(list[::-1]) #8 114454

# bin(2) 1010011101 -> hex(16)
# 0010.1001.1101 -> 2 9 d
#9 29d

# oct(8) 1147453 -> bin(2)
# 1 1 100 111 100 101 11
# 001 001 100 111 100 101 011
#10 001001100111100101011

# oct(8) 127 -> hex(16)
# 127 -> 1 10 111
# 0001 0010 0111 -> 1 2 7
#11 127

# hex(16) c3e1 -> bin(2)
# 1100 0011 1110 0001
#12 8

# 32 -> 16 -> 8 -> 2
# af38 -> 53c68
# 




-------------------------------------------------

n = int(input("основание: "))
a = str(int(input("число: ")))
print(int(a,n))
----------------------------------------------
x = str(int(input()))
if len(str(x)) == 2:
    if '3' in str(x): print('yes')
    else: print('no')
else: print('число не двузначное')
------------------------------------------------
x = str(int(input()))
if len(str(x)) == 2:
    if x[0] > x[1]: print(x[0], '>', x[1])
    elif x[0] < x[1]: print(x[1], '>', x[0])
    else: print('цифры равны')
else: print('число не двузначное')
    ---------------------------------------------
from math import sqrt
a = int(input())
b = int(input())
c = int(input())
d = b*b - 4*a*c
if d < 0: print('нет корней')
if d == 0:
    x = -b / (2*a)
    print(x)
if d > 0:
    x1= (-b + sqrt(d)) / (2*a)
    x2= (-b - sqrt(d)) / (2*a)
    print(x1,x2)
====================================================
x = int(input())
if x<2: print('no')
else:
    for i in range(2, x+1):
        if x%i == 0:
            print(i)
            break
----------------------------------------------------
