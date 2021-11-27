# Author: Jingyi Wang
# Stu_ID: 1929591
# Email: Jingyi.Wang1903@student.xjtlu.edu.cn
import re


class Number:
    def __init__(self, value, start, strlen):
        self.value = value
        self.location = [start, strlen]

    def __str__(self):
        return "{}, {}".format(self.value, self.location)

    def __lt__(self, other):
        return self.value < other.value


number_class_list = []
number_list = []
location_list = []

if __name__ == '__main__':
    input_str = input()
    numbers = re.findall(r'\d+\.?\d*', input_str)

    for number in numbers:
        index = input_str.find(number)
        length = len(number)
        number_class_list.append(Number(float(number), index, length))

    number_class_list.sort()

    for number_class in number_class_list:
        number_list.append(number_class.value)
        location_list.append(number_class.location)

    print("number_list: ", number_list)
    print("location_list: ", location_list)