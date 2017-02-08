import StringIO
import csv

def parseCSV(filename):
	with open(filename, 'rb') as f:
		reader = csv.reader(f, delimiter="\t")
		return list(reader)

def parseEmployee():
	arr = parseCSV('employee.csv')
	for item in arr[1:]:
		item[1] = int(item[1])
		item[2] = True if item[2].startswith('YES') else False
	return arr[1:]
