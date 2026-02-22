"""
Part 3: Difference Between First and Last Score
Create a class called StudentPerformance which does the following:

Takes a list of scores as input while creating the object.

Create a method called score_difference() which:

Finds the difference between the last score and the first score using indexing.
If the list is empty, handle it using exception handling and print:
No scores available to calculate difference
Example Input:

scores = [55, 65, 75, 85]
Output:

Difference between last and first score is: 30
"""

class StudentPerformance:
    def __init__(self, marks):
        self.marks = marks

    def score_difference(self):
        try:
            if not len(self.marks):
                raise Exception
            else:
                print(f"Difference between last and first score is: {self.marks[-1] - self.marks[0]}")
        except Exception as e:
            print("No scores available to calculate difference")

input = input("Enter list of marks(space separated): ")
marks = [int(num) for num in input.split(" ")]
s = StudentPerformance(marks)
s.score_difference()
