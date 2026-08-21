# # Even or odd in without function
#
# # number = int(input("Enter a number: "))
# # if number % 2 == 0:
# #     print("Given input is a even number")
# # else:
# #     print("Given input is a odd number")
# #
# # Area of Rectangle
# import math
# # def area_rectangle(l,b):
# #     area = l * b
# #     return area
# #
# # length = int(input("Enter length of Rectangle: "))
# # breadth = int(input("Enter breadth of Rectangle: "))
# # result = area_rectangle(length, breadth)
# # print("Area of the rectangle is :",result)
#
# #reverse a string
# string = "Hello World!"
# # reversed_string = string[::-1]
# # print(reversed_string)
# #checking if a string contains substring
# sub_string = "World"
# if sub_string in string:
#     print("substring found")
# else:
#     print("substring not found")
# #finding the maximum value in a list
# # list=[1,2,3,4,5,6,7,]
# # max_value = max(list)
# # print(max_value)
# # #findig the index  of the maximum value in a list
# # index_value = list.index(max_value)
# # print(index_value)
# # # reversing a list
# # list =['Hello','Python']
# # reversed_list = list[::-1]
# # print(reversed_list)
# # # #removing duplicates from a list
# # list1 = ["Hello",'Python',"python",'Hello']
# # my_list = list(set(list1))
# # print(my_list)

# num1 = input("Enter a number: ")
# num2 = input("Enter a number: ")
#
# sum = float(num1) + float(num2)
# print("sum of two numbers is :".format(num1,num2,sum))

# number1 = input("First number: ")
# number2 = input("\nSecond number: ")
#
# # Adding two numbers
# # User might also enter float numbers
# sum = float(number1) + float(number2)
#
# # Display the sum
# # will print value in float
# print("The sum of {0} and {1} is {2}".format(number1,
#                                              number2, sum))

# def show_employee(name, salary=9000):
#     print("Name:", name, "salary:", salary)
#
# show_employee("Ben", 12000)
# show_employee("Jessa")

# def show_employee(name, salary = 90000):
#     print("Name:",name,"salary:",salary)
# show_employee("Noor")
# show_employee("Shaik",120000)

# Write a program to create a function show_employee() using the following conditions.
#
# It should accept the employee’s name and salary and display both.
# If the salary is missing in the function call then assign default value 9000 to salary
#def employee(name, salary = 90000):
 #   print("Name:",name,"salary:",salary)
#employee("Noor")
#employee("Shaik",120000)


#def student(name, age):
 #   print(name,age)
#student("Noor",27)

#def func1(*args):
 #   for i in args:
  #      print(i)
# func1(20,30)
# func1(20,30,40)
#
# def calculation(a,b):
#     addition = a + b
#     subtraction = a - b
#     return addition, subtraction
# x = calculation(10,20)
# print(x)

# def calculation(a,b):
#     return  a + b, a - b
# add,sub = calculation(10,20)
# print(add,sub)
#
# def addition(num):
#     if num:
#         # call same function by reducing number by 1
#         return num + addition(num - 1)
#     else:
#         return 0
#
# res = addition(10)
# print(res)
#
# def display_student(name, age):
#     print(name, age)
#
# # call using original name
# display_student("Emma", 26)
#
# # assign new name
# showStudent = display_student
# # call using new name
# showStudent("Emma", 26)
#
# def employee(name, id):
#     print((name,id))
# employee("Noor",325186)
# GL_employee = employee
# GL_employee("Shaik",325187)

# print(list(range(4,30,2)))
#
# x = [4, 6, 8, 24, 12, 2]
# y = max(x)
# print(y)
#
#
# # num1 = int(input("Enter a number: "))
# # num2 = int(input("Enter a number: "))
# # res = num1 * num2
# # print("multiplication is ",res)
#
# #print('Name', 'Is', 'James') will display Name**Is**James
# print("Name"+"*"+"*"+"Is"+"*"+"James")


i = 1
while i < 10:
    print(i)
    i += 1