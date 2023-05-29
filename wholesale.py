import csv

def LP():
    p = []
    with open('Wholesale.CSV', newline='') as csvfile:
        properties = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in properties:
            p.append(row)
    return p

