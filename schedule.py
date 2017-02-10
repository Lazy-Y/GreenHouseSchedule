from collections import defaultdict
import csv
from random import choice
from copy import deepcopy


newServerMinHour = 8
ServerMinHour = 8
maxHour = 16
minNumSupervisors = 1

maxSolCount = 1000

class Employee:
	"""docstring for Employee"""
	def __init__(self, name, level, isDriver):
		self.name = name
		self.level = level
		self.isDriver = isDriver

	def __str__(self):
		return 'name: ' + self.name + ', level: ' + str(self.level) + ', isDriver: ' + str(self.isDriver)

	def __repr__(self):
	    return self.__str__()


class AvailHandler(object):
	"""docstring for AvailHandler"""
	def __init__(self):
		self.availability = parseAvailability()
		self.maxTime = 0
		self.solCount = 0
		self.dptable = defaultdict(lambda: {})

	def isAvailable(name, day, time):
		duration = self.availability[day][name]
		return duration[0] <= time and duration[1] >= time


def parseCSV(filename):
	with open(filename, 'rb') as f:
		reader = csv.reader(f, delimiter="\t")
		return list(reader)


# return the array of Employee
# return a name to id map
def parseEmployee():
	arr = parseCSV('employee.csv')
	for item in arr[1:]:
		item[1] = int(item[1])
		item[2] = True if item[2].startswith('YES') else False
	# result = [item for item in arr[1:] if item[1] > 0]
	result = []
	for item in arr[1:]:
		if item[1] > 0:
			result.append(Employee(item[0],item[1],item[2]))
	m = {}
	for i in range(len(result)):
		m[result[i].name] = i
	return result, m


# return an array, each item is an array of available time for each day
def parseTemplate():
	arr = parseCSV('time_template.csv')
	result = [[] for i in range(7)]
	for item in arr[1:]:
		for i in range(1, len(item)):
			result[i-1].append(int(item[i]))
	return result


# return available time pieces for each employee
def parseAvailability():
	arr = parseCSV('availability.csv')
	length_for_day = len(arr)/7
	result = defaultdict(lambda: [])
	for i in range(1, len(arr)):
		for j in range(1, len(arr[i])):
			name = arr[0][j]
			if arr[i][j].startswith('YES'):
				if len(result[name]) == 0:
					result[name].append([i-1, i-1])
				else:
					lastItem = result[name][-1]
					if (i-1) % length_for_day == 0:
						result[name].append([i-1, i-1])
					elif i-1 - lastItem[1] == 1:
						result[name][-1][1] = i-1
					else:
						result[name].append([i-1, i-1])
	retVal = [defaultdict(lambda: []) for i in range(7)]
	for name, arr in result.iteritems():
		for duration in arr:
			if isinstance(duration, list) and duration[1] - duration[0] >= getMinWorkingTime(name):
				retVal[duration[0]/length_for_day][name].append([duration[0] % length_for_day, duration[1] % length_for_day])
	return retVal

(employees, index_map) = parseEmployee()

def getMinWorkingTime(employee):
	if isinstance(employee, str):
		return ServerMinHour if employees[index_map[employee]].level > 1 else newServerMinHour
	elif isinstance(employee, int):
		return ServerMinHour if employees[employee].level > 1 else newServerMinHour
	else:
		return ServerMinHour if employee.level > 1 else newServerMinHour

availHandler = AvailHandler()
time_template_const = parseTemplate()

def getAllEmployees():
	arr = []
	for employee in employees:
		arr.append(index_map[employee.name])
	return arr


def complianceChecking(numNeeded, currNode):
	hasSupervisor = numNeeded <= 0
	hasDriver = numNeeded <= 1
	for index in currNode:
		if employees[index].isDriver:
			hasDriver = True
		if employees[index].level > 2:
			hasSupervisor = True
	return hasSupervisor and hasDriver


def solveTime(day, time_template, availableEmployees, time, currNode, currLength, parentLength, start = 0):
	if (str(parentLength) + str(availableEmployees)) in availHandler.dptable:
		return availHandler.dptable[time][str(parentLength) + str(availableEmployees)]
	if len(currNode) == time_template[time]:
		if complianceChecking(time_template[time], currNode):
			return [(currNode, currLength, availableEmployees)]
		else:
			return None
	if start >= len(availableEmployees):
		# print 'no more employees'
		return None
	retVal = []
	# print 'avail', len(availableEmployees)
	for i in range(start, len(availableEmployees)):
		currNodeCopy = deepcopy(currNode)
		currLengthCopy = deepcopy(currLength)
		availableEmployeesCopy = deepcopy(availableEmployees)
		del availableEmployeesCopy[i]
		index = availableEmployees[i]
		currNodeCopy.append(index)
		currLengthCopy[index] = parentLength[index] + 1 if index in parentLength else 1
		timeSolution = solveTime(day, time_template, availableEmployeesCopy, time, currNodeCopy, currLengthCopy, parentLength, i + 1)
		if not timeSolution == None:
			retVal += [solution for solution in timeSolution if not solution == None]
	result = None if len(retVal) == 0 else retVal
	availHandler.dptable[time][str(parentLength) + str(availableEmployees)] = result
	return result


def solveDay(day, time_template, availableEmployees, time = 0, parentNode = [], parentLength = {}):
	if time >= len(time_template):
		availHandler.solCount += 1
		return [[[]]]
	if (str(parentLength) + str(availableEmployees)) in availHandler.dptable:
		return availHandler.dptable[time][str(parentLength) + str(availableEmployees)]
	if availHandler.solCount > maxSolCount:
		return None
	currNode = []
	currLength = {}
	for node in parentNode:
		if parentLength[node] >= maxHour:
			pass
		elif parentLength[node] < getMinWorkingTime(node):
			currNode.append(node)
			currLength[node] = parentLength[node] + 1
		elif node not in availableEmployees:
			availableEmployees.append(node)
	if len(currNode) > time_template[time]:
		# print 'Excess'
		return None
	timeSolution = solveTime(day, time_template, availableEmployees, time, currNode, currLength, parentLength)
	# if time == 0:
	# 	print 'time 0', timeSolution
	if timeSolution == None:
		# print 'No time'
		return None
	currSolution = [item for item in timeSolution if not item == None]
	daySolution = []
	for (currNodeReturn, currLengthReturn, currEmployees) in currSolution:
		nextDaySolution = solveDay(day, time_template, currEmployees, time + 1, currNodeReturn, currLengthReturn)
		if not nextDaySolution == None:
			for item in nextDaySolution:
				# print 'prev item', item
				# print 'item', [parentNode] + item
				newItem = [currNodeReturn] + item
				daySolution.append(newItem)
		# else:
		# 	print 'No next day'
	availHandler.dptable[time][str(parentLength) + str(availableEmployees)] = daySolution
	if len(daySolution) > 0:
		return daySolution  
	else:
		# print 'No day', time
		return None


def intToTime(i):
	return str(i/2+11) + ':' + ('30' if i%2 else '00')


def convertSolution(solution):
	m = {}
	for i in range(len(solution)):
		for j in range(len(solution[i])):
			name = employees[solution[i][j]].name
			if name in m:
				m[name][1] = i
			else:
				m[name] = [i,i]
	retVal = []
	for name, duration in m.iteritems():
		retVal.append(name + ', from ' + intToTime(duration[0]) + ' to ' + intToTime(duration[1] + 1))
	return retVal

def solveWeek():
	solutions = []
	for i in range(7):
		availHandler.dptable = defaultdict(lambda: {})
		availHandler.solCount = 0
		solutions.append(solveDay(i, time_template_const[i], getAllEmployees()))
		s = solutions[-1]
		minRetVal = None
		if not s == None:
			print 'Day', i, 'num sol', len(s), availHandler.solCount
			retVal = convertSolution(s[0])
			if minRetVal == None or len(minRetVal) > retVal:
				minRetVal = retVal
			print minRetVal
		else:
			print 'Day', i, 'None'
		print '\n'
	return solutions

solutions = solveWeek()
# for s in solutions:
# 	if s == None:
# 		print s
# 	else:
# 		print len(s)



