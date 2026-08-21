# len(s) : returns the length of object/string
x = "Noor Mahammad"
print(len(x))

# str() converts the specified value into a string
a=12345678
b= str(a)
print(b.find("45"))
print(len('a'))

print(type(b))
# count() returns the number of times a specified item is found in the string/object
# count(sub[,start[,end]])
x= "Noor Mahammad"
print(x.count('m',2,12))

x = "Noor Mahammad Ghouse"
print(type(x))
print(x.split())
y= (x.upper())
print(y.isupper())
print(x.replace("Ghouse","Shaik"))
