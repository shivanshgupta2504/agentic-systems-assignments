"""
Part 1: Last Three Average
Create a class called StudentMarks which does the following:

Takes a list of marks as input while creating the object.
Create a method called last_three_avg() which:
Finds the average of the last three marks using negative indexing. If the list has less than 3 marks, handle it using exception handling and print:
Not enough marks to calculate average
Example Input:

marks = [50, 60, 70, 80, 90]
Output:

Average of last 3 marks is: 80.0
"""

class StudentMarks:
    def __init__(self, marks):
        self.marks = marks

    def last_three_avg(self):
        try:
            if len(self.marks) < 3:
                raise Exception
            else:
                average = sum(self.marks[-3:]) / 3
                print(f"Average of last 3 marks is: {average}")
        except Exception as e:
            print("Not enough marks to calculate average")

input = input("Enter list of marks(space separated): ")
marks = [int(num) for num in input.split(" ")]
s = StudentMarks(marks)
s.last_three_avg()

