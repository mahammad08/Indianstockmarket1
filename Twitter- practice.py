# # # age = 5
# # # if True:
# # #     age = 6
# # # print(age)
# #
# #
# # # a = 10
# # # b = 20
# # #
# # # temp = a
# # # a = b
# # # b = temp
# # #
# # # print("After swapping: a =",a, "b=",b)
# #
# #
# # a = 10
# # b = 5
# # a,b = b,a
# #
# # print("after swapping:a =",a,"b =",b)
#
#
# # def calc(*args):
# #     count = len(args)
# #     elem = args[count-1]
# #     return count * elem
# # print(calc(2,2,1,3))
# # a = set()
# # for n in range(21,30):
# #     if n % 2 == 0:
# #         a.add(n)
# # print(a)
#
# my_info = {'name':'Noor',
#            'age': 28,
#            'city':['Hyderabad','Pune','Bangalore']}
#
# keys = my_info.keys()
# print(keys)
#
# values = my_info.values()
# print(values)
#
# my_info["age"] = 27
# print(my_info["age"])
#
# my_info["country"] = "India"
#
# del my_info["country"]
#
# print(my_info)
#
# if "city" in my_info:
#     print("Yes!")
# else:
#     print("No!")
#
# items = my_info.items()
# print(items)
#
#
# for key in my_info:
#     value = my_info.values()
#     print(key,":", value)


# value = 7 and 8
# result = "Even" if value % 2 == 0 else "odd"
# print(result)

# score = 87
# if score <= 87:
#     print("1")
# if score == 87:
#     print("2")
#
# print('a')
# for i in range(1,5):
#     if (i == 6):
#         break
# else:
#     print('b')


# number = 0
# while number < 7:
#     number = number + 3
#     if number == 6:
#         continue
#     print(number)


# n = 9
# first = 0
# second = 1
#
# series = [first,second]
#
# if n == 0:
#     print("the required fibonacci series is",first)
# else:
#
# for i in range(0,n-2):
# num = series[i] + series[i+1]
# series.append(num)
# print(series)

n = 9
first = 0  # first value of series
second = 1  # second value of series
series = [first, second]

if n == 1:
    print("The required fibonacci series is", first)
else:
    for i in range(0, n - 2):
        num = series[i] + series[i + 1]
        series.append(num)

    print("The required fibonacci series is", series)
