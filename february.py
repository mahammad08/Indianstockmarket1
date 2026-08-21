# n = 15
# first = 0
# second = 1
#
# series = [first, second]
#
# if n == 1:
#     print("The required fibonacci series",first)
# else:
#     for i in range(0, n - 2):
#         num = series[i] + series[i+1]
#
#         print("The required fibonacci series", series)
#
#         series.append(num)
#     print(series)


sequence = "NoorMahammad"
reverse = sequence[::-1]

if sequence == reverse:
    print("sequence is a palindrome")
else:
    print("sequence is not a palindrome")