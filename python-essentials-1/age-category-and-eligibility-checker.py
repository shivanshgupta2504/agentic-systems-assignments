"""
Part 3: Age Category and Eligibility Checker
Write a Python program that:

Takes the user's name and age as input.
Converts age to an integer.
Uses conditional statements to determine the category.
Print:

"Hello <name>"

Based on age:

Age Range	Print
Less than 13	"You are a Child"
13 to 17	"You are a Teenager"
18 to 59	"You are an Adult"
60 and above	"You are a Senior Citizen"
Additionally:

If age ≥ 18 → print "You are eligible to vote"
Else → print "You are not eligible to vote"
If:

Invalid input → print "Invalid age input"
Age is negative → print "Age cannot be negative"

"""

name = input("Enter your name: ")
age = input("Enter your age: ")

try:
    age = int(age)
    if age < 0:
        print("Age cannot be negative")
    else:
        print(f"Hello {name}")
        if age < 13:
            print("You are a Child")
            print("You are not eligible to vote")
        elif age <= 17:
            print("You are a Teenager")
            print("You are not eligible to vote")
        elif age <= 59:
            print("You are an Adult")
            print("You are eligible to vote")
        else:
            print("You are a Senior Citizen")
            print("You are eligible to vote")
except ValueError:
    print("Invalid age input")
