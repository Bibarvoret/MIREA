#   Objective:   Запрограммируйте формулы Хартли. Количество состояний вводится с клавиатуры.
#                При вычислении по формуле Хартли может получено нецелое значение N. В этом случае значение необходимо округлить вверх до целого значения.
import math
k = int(input())
n = math.log(k,2)
print(math.ceil(n))