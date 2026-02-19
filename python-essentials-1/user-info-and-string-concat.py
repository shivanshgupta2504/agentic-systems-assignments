"""
Part 2: User Information and String Concatenation
Write a Python program that:

Takes the user's first name and last name as input.
Takes the user's age as input.
Converts the age into an integer.
Print:

Full name using string concatenation Example: Full Name: John Doe

Age next year Example: You will be 21 next year

If:

Age is not numeric → print "Invalid age input"
Age is less than 0 → print "Age cannot be negative"
"""

first_name = input("Enter your first name: ")
last_name = input("Enter your last name: ")
age = input("Enter your age: ")

try:
    full_name = first_name + " " + last_name
    age = int(age)
    if age < 0:
        print("Age cannot be negative")
    else:
        print(f"Full Name: {full_name}")
        print(f"You will be {age + 1} next year")
except ValueError:
    print("Invalid age input")
