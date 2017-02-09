from collections import defaultdict
import csv
from random import choice
from copy import deepcopy

newServerMinHour = 4*2
ServerMinHour = 5*2
maxHour = 8*2
minNumSupervisors = 1

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
	result = defaultdict(lambda: [])
	for i in range(1, len(arr)):
		for j in range(1, len(arr[i])):
			name = arr[0][j]
			if arr[i][j].startswith('YES'):
				if len(result[name]) == 0:
					result[name].append(i-1)
				else:
					lastItem = result[name][-1]
					if isinstance(lastItem, int):
						if i-1 - lastItem == 1:
							result[name][-1] = [lastItem, i-1]
						else:
							result[name][-1] = [lastItem, lastItem]
							result[name].append(i-1)
					else:
						if i-1 - lastItem[1] == 1:
							result[name][-1][1] = i-1
						else:
							result[name].append(i-1)
	# construct time lines
	retVal = defaultdict(lambda: [])
	for name, arr in result.iteritems():
		for duration in arr:
			if isinstance(duration, list) and duration[1] - duration[0] >= getMinWorkingTime(name):
				retVal[name].append(duration)
	return retVal








# get empty day sheet template
def getEmptyDaySheet():
	# supervisor_sheet = [[0 for i in range(len(time_template[0]))] for j in range(len(time_template))]
	# return supervisors
	return [[] for i in range(len(time_template[0]))]


# get all supervisors from employees
def getSupervisors():
	supervisors = []
	for employee in employees:
		if employee.level > 2:
			supervisors.append(employee)
	return supervisors


def getMinWorkingTime(employee):
	if isinstance(employee, str):
		return ServerMinHour if employees[index_map[employee]].level > 1 else newServerMinHour
	else:
		return ServerMinHour if employee.level > 1 else newServerMinHour





# randomly choose an employee that haven't been choosen yet, who can cover the $time
# randomly choose a maximum time from the employee's available time that can cover the $time
def getEmployeeCoverTime(employees, time, availability, choosen):
	available_employees = list(set(employees) - choosen)
	while len(available_employees) > 0:
		employee = choice(available_employees)
		available_employees.remove(employee)
		for duration in availability[employee.name]:
			if duration[0] <= time and duration[1] > time:
				choosen.add(employee)
				leave_time = duration[0] + maxHour
				if leave_time < duration[1] and leave_time - time >= getMinWorkingTime(employee):
					return (employee, [duration[0], leave_time])
				elif duration[1] - time >= getMinWorkingTime(employee):
					return (employee, duration) 
	return False


# return all employees who are available at that DAY
def getAvailableEmployee(employees, availability):
	return [employee for employee in employees if len(availability[employee.name]) > 0]


# get the employee who leaves at time and with the longest duration
# return Employ
def getLongestTimelineEndAt(time_map, time):
	result_employee = None
	for employee, duration in time_map.iteritems():
		if duration[1] - 1 == time and duration[1] - duration[0] > getMinWorkingTime(employee):
			if result_employee == None or time_map[result_employee][1] - time_map[result_employee][0] < duration[1] - duration[0]:
				result_employee = employee
	return result_employee


def getLongestTimelineStartAt(time_map, time):
	result_employee = None
	for employee, duration in time_map.iteritems():
		if duration[0] == time and duration[1] - duration[0] > getMinWorkingTime(employee):
			if result_employee == None or time_map[result_employee][1] - time_map[result_employee][0] < duration[1] - duration[0]:
				result_employee = employee
	return result_employee


def optimization(empty_sheet, time_template, time_map):
	start = 0
	end = len(empty_sheet) - 1
	diff = end - start
	while diff >= 0:
		while not (len(empty_sheet[end]) > time_template[end]):# or len(empty_sheet[end]) > minNumSupervisors):
			end-=1
			if start > end:
				break
		while len(empty_sheet[end]) > time_template[end]:# or len(empty_sheet[end]) > minNumSupervisors:
			employee = getLongestTimelineEndAt(time_map, end)
			if employee == None:
				break
			time_map[employee][1] -= 1
			empty_sheet[end].remove(index_map[employee.name])
			end-=1
		while not (len(empty_sheet[start]) > time_template[start]):# or len(empty_sheet[start]) > minNumSupervisors):
			start+=1
			if start > end:
				break
		while len(empty_sheet[start]) > time_template[start]:# or len(empty_sheet[start]) > minNumSupervisors:
			employee = getLongestTimelineStartAt(time_map, start)
			if employee == None:
				break
			time_map[employee][0] += 1
			empty_sheet[start].remove(index_map[employee.name])
			start+=1
		if diff == end - start:
			return False
		else:
			diff = end - start
	return empty_sheet


# get a solution for supervisor arrangement for a DAY
def getSupervisorSheet(availability, time_template, choosen=set()):
	supervisors = getAvailableEmployee(getSupervisors(), availability)
	empty_sheet = getEmptyDaySheet()
	time_map = {}
	for i in range(len(empty_sheet)):
		while time_template[i] > 0 and len(empty_sheet[i]) < minNumSupervisors:
			retVal = getEmployeeCoverTime(supervisors, i, availability, choosen)
			if not retVal:
				return False
			(employee, duration) = retVal
			time_map[employee] = duration
			for j in range(duration[0],duration[1]):
				empty_sheet[j].append(index_map[employee.name])
	time_sheet = optimization(empty_sheet, time_template, time_map)
	if time_sheet == None:
		return False
	else:
		return time_sheet
	


# get a solution for a DAY
def getDaySolution(availability, time_template):
	supervisor_sheet = getSupervisorSheet(availability, time_template)
	print supervisor_sheet


# get a solution for a WEEK
def getSolutions():
	solution_arr = []
	for i in range(1):
		solution_arr.append(getDaySolution(availability, time_template[i]))
	return solution_arr
		







(employees, index_map) = parseEmployee()
time_template = parseTemplate()
availability = parseAvailability()

getSolutions()

