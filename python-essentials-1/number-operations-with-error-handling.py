"""
Part 1: Number Operations with Error Handling
Write a Python program that:

Takes two numbers as input from the user.
Converts both inputs to integers.
Print:

Their sum
Their division result
If:

The user enters non-numeric input → print "Invalid input"
The second number is zero → print "Cannot divide by zero"
"""

a = input("Enter a number: ")
b = input("Enter another number: ")

try:
    a = int(a)
    b = int(b)
    if b == 0:
        print("Cannot divide by zero")
    else:
        print(f"Sum is: {int(a) + int(b)}")
        print(f"Division is: {int(a) / int(b)}")
except ValueError:
    print("Invalid input")

