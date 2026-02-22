"""
Part 2: Highest of Last Two Scores
Create a class called StudentScores which does the following:

Takes a list of scores as input while creating the object.

Create a method called highest_last_two() which:

Finds the highest score among the last two scores using negative indexing.
If the list has less than 2 scores, handle it using exception handling and print:
Not enough scores to find the highest value
Example Input:

scores = [45, 67, 89, 72]
Output:

Highest score among last two is: 89
"""

class StudentScores:
    def __init__(self, marks):
        self.marks = marks

    def highest_last_two(self):
        try:
            if len(self.marks) < 2:
                raise Exception
            else:
                print(f"Highest score among last two is: {max(self.marks[-1], self.marks[-2])}")
        except Exception as e:
            print("Not enough scores to find the highest value")

input = input("Enter list of marks(space separated): ")
marks = [int(num) for num in input.split(" ")]
s = StudentScores(marks)
s.highest_last_two()
