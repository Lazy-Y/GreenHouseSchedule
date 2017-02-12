from collections import defaultdict
import csv
from random import choice
from copy import deepcopy

newServerMinHour = 8#4*2
ServerMinHour = 8#5*2
maxHour = 16
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
			if isinstance(duration, list) and duration[1] + 1 - duration[0] >= getMinWorkingTime(name):
				retVal[duration[0]/length_for_day][name].append([duration[0] % length_for_day, duration[1] % length_for_day])
	return retVal



# get empty day sheet template
def getEmptyDaySheet(day):
	# supervisor_sheet = [[0 for i in range(len(time_template[0]))] for j in range(len(time_template))]
	# return supervisors
	return [[] for i in range(len(time_template_const[day]))]


# get all supervisors from employees
def getSupervisors():
	supervisors = []
	for employee in employees:
		if employee.level > 2:
			supervisors.append(employee)
	return supervisors


def getNonSupervisors():
	nonSupervisors = []
	for employee in employees:
		if employee.level <= 2:
			nonSupervisors.append(employee)
	return nonSupervisors
	

def getMinWorkingTime(employee):
	if isinstance(employee, str):
		return ServerMinHour if employees[index_map[employee]].level > 1 else newServerMinHour
	elif isinstance(employee, int):
		return ServerMinHour if employees[employee].level > 1 else newServerMinHour
	else:
		return ServerMinHour if employee.level > 1 else newServerMinHour



(employees, index_map) = parseEmployee()
time_template_const = parseTemplate()
availability = parseAvailability()

def getEmployeeCoverTime(employees, time, availability):
	retVal = []
	for employee in employees:
		for duration in availability[employee.name]:
			if duration[0] <= time and duration[1] >= time:
				leave_time = duration[0] + maxHour
				if leave_time < duration[1] and leave_time - time + 1 >= getMinWorkingTime(employee):
					retVal.append([employee, [duration[0], leave_time]])
				elif duration[1] + 1 - time >= getMinWorkingTime(employee):
					if duration[1] + 1 - duration[0] > maxHour:
						retVal.append([employee, [duration[1] - maxHour - 1, duration[1]]])
					else:
						retVal.append([employee, duration]) 
				elif duration[1] + 1 - duration[0] >= getMinWorkingTime(employee):
					retVal.append([employee, [max(duration[0], duration[1] - maxHour - 1), duration[1]]])
	return retVal


# return all employees who are available at that DAY
def getAvailableEmployee(employees, availability):
	retVal = [employee for employee in employees if len(availability[employee.name]) > 0]
	return retVal



def dfs_supervisors(availability, time_template, employees, start, time_sheet, dptable):
	if str(sorted(time_sheet)) in dptable:
		return []
	dptable.add(str(sorted(time_sheet)))
	result = []
	for i in range(start, len(time_template)):
		if time_template[i] > 0 and len(time_sheet[i]) < minNumSupervisors:
			retVal = getEmployeeCoverTime(employees, i, availability)
			for (employee, duration) in retVal:
				employees_copy = [temp_employee for temp_employee in employees if not employee.name == temp_employee.name]
				time_sheet_copy = deepcopy(time_sheet)
				for j in range(duration[0],duration[1]+1):
					time_sheet_copy[j].append(index_map[employee.name])
				result += dfs_supervisors(availability, time_template, employees_copy, i, time_sheet_copy, dptable)
	result = result if len(result) > 0 else [[time_sheet, employees]]
	return result


def dfs_employees(availability, time_template, employees, start, time_sheet, dptable):
	# print availability, employees, time_sheet
	if str(sorted(time_sheet)) in dptable or len(dptable) > 100:
		return []
	dptable.add(str(sorted(time_sheet)))
	# if len(dptable) % 1000 == 0:
	# 	print 'processing', len(dptable), 'data'
	result = []
	for i in range(start, len(time_template)):
		if time_template[i] > len(time_sheet[i]):
			retVal = getEmployeeCoverTime(employees, i, availability)
			for (employee, duration) in retVal:
				employees_copy = [temp_employee for temp_employee in employees if not employee.name == temp_employee.name]
				time_sheet_copy = deepcopy(time_sheet)
				for j in range(duration[0],duration[1]+1):
					time_sheet_copy[j].append(index_map[employee.name])
				result += dfs_employees(availability, time_template, employees_copy, i, time_sheet_copy, dptable)
	result = result if len(result) > 0 else [[time_sheet, employees]]
	return result




def checkDriver(time_sheet, time_template):
	for i in range(len(time_sheet)):
		if time_template[i] <= 1:
			continue
		item = time_sheet[i]
		hasDriver = False
		for i in item:
			if employees[i].isDriver:
				hasDriver = True
				break
		if not hasDriver:
			return False
	return True


def hasOtherDriverAndSupervisor(employee, time_sheet, time, time_template):
	hasDriver = time_template[time] <= 1
	hasSupervisor = time_template[time] < 1
	for item in time_sheet[time]:
		if not (employees[item] == employee):
			if employees[item].isDriver:
				hasDriver = True
			if employees[item].level > 2:
				hasSupervisor = True
	return hasDriver and hasSupervisor




dptable = set()
def getSupervisorSheets(current_day):
	dptable = set()
	result = dfs_supervisors(availability[current_day], time_template_const[current_day], getAvailableEmployee(getSupervisors(), availability[current_day]), 0, getEmptyDaySheet(current_day), dptable)
	retVal = []
	for (solution_sheet, employees) in result:
		isOk = True
		for i in range(len(solution_sheet)):
			if len(solution_sheet[i]) == 0 and time_template_const[current_day][i] > 0:
				# print 'not okay',i, solution_sheet
				isOk = False
				break
		if isOk:
			retVal.append([solution_sheet, employees])
	return retVal



def checkValidSolution(solution, time_template):
	for i in range(len(solution)):
		if len(solution[i]) < time_template[i]:
			return False
		elif time_template[i] > 1:
			hasDriver = False
			for j in solution[i]:
				if employees[j].isDriver:
					hasDriver = True
			if not hasDriver:
				return False
	return True


def optimizeEmployee(index, solution, time_template, forward):
	removeable_array = []
	for item in solution[index]:
		if index == 0 or (item not in solution[index-1]):
			removeable_array.append(item)
		elif (index == len(solution) - 1) or (item not in solution[index+1]):
			removeable_array.append(item)

	for item in removeable_array:
		if not hasOtherDriverAndSupervisor(employees[item], solution, index, time_template):
			removeable_array.remove(item)
	max_duration = None
	max_employee = None

	if forward:
		for item in removeable_array:
			i = index
			while i < len(solution) and item in solution[i]:
				i += 1
			if (max_duration == None) or (max_duration < i - index):
				if i - index > getMinWorkingTime(item):
					max_duration = i - index
					max_employee = item
	else:
		for item in removeable_array:
			i = index
			while i >= 0 and item in solution[i]:
				i -= 1
			if (max_duration == None) or (max_duration < index - i):
				if index - i> getMinWorkingTime(item):
					max_duration = index - i
					max_employee = item
	return max_employee


def optimizeSolution(solution, time_template):
	diff = 9999999
	new_diff = diff - 1
	while new_diff < diff and new_diff > 0:
		diff = new_diff
		new_diff = 0
		for i in range(len(solution)):
			while len(solution[i]) > time_template[i]:
				employee_id = optimizeEmployee(i, solution, time_template, True)
				if employee_id == None:
					break
				else:
					solution[i].remove(employee_id)
		for i in range(len(solution) - 1, -1, -1):
			while len(solution[i]) > time_template[i]:
				employee_id = optimizeEmployee(i, solution, time_template, False)
				if employee_id == None:
					break
				else:
					solution[i].remove(employee_id)
		new_diff = countTimeOff(solution, time_template)
	return solution



def countTimeOff(solution, time_template):
	timeOff = 0
	for i in range(len(solution)):
		timeOff += len(solution[i]) - time_template[i]
	return timeOff
	


def getDaySolutions(i):
	supervisor_solutions = getSupervisorSheets(i)
	allSolutions = []
	for solution in supervisor_solutions:
		dptable = set()
		allSolutions += dfs_employees(availability[i], time_template_const[i], solution[1] + getAvailableEmployee(getNonSupervisors(), availability[i]), 0, solution[0], dptable)
	len(set([str(item) for item in allSolutions]))
	retVal = []
	for item in allSolutions:
		if checkValidSolution(item[0], time_template_const[i]):
			solution = optimizeSolution(item[0], time_template_const[i])
			if not solution == None:
				retVal.append(solution)
	return retVal


def intToTime(i, day):
	end = len(time_template_const[day])-1
	for time in range(len(time_template_const[day])-1, -1, -1):
		if time_template_const[day][time] == 0:
			end = time
		else:
			break
	if i == 0:
		return 'Open'
	elif i >= end:
		return 'Close'
	else:
		return str(i/2+11) + ':' + ('30' if i%2 else '00')


def convertSolution(solution, day):
	m = {}
	for i in range(len(solution)):
		for j in range(len(solution[i])):
			name = employees[solution[i][j]].name
			if name in m:
				m[name][1] = i
			else:
				m[name] = [i,i]
	retVal = defaultdict(lambda: "")
	for name, duration in m.iteritems():
		interval = intToTime(duration[0], day) + ' ~ ' + intToTime(duration[1]+1, day)
		print name + ',', interval
		retVal[name] = interval
	return retVal

def closestToTime(solution_set, time_template):
	retVal = []
	timeOff = 9999999
	for solution in solution_set:
		currTimeOff = countTimeOff(solution, time_template)
		if currTimeOff < timeOff:
			timeOff = currTimeOff
			retVal = [solution]
		elif currTimeOff == timeOff:
			retVal.append(solution)
	return retVal

def fewestPeople(solution_set):
	numPeople = 9999999
	retVal = []
	for solution in solution_set:
		pplSet = set()
		for arr in solution:
			pplSet = pplSet.union(set(arr))
		if len(pplSet) < numPeople:
			numPeople = len(pplSet)
			retVal = [solution]
		elif len(pplSet) == numPeople:
			retVal.append(solution)
	return retVal


def moreSenior(solution_set):
	retVal = []
	max_points = 0
	for solution in solution_set:
		points = 0
		for arr in solution:
			for i in arr:
				points += employees[i].level
		if points > max_points:
			retVal = [solution]
			max_points = points
		elif points == max_points:
			retVal.append(solution)
	return retVal


dayArr = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
def getAllSolutions():
	retVal = []
	for i in range(7):
		result = getDaySolutions(i)
		result = moreSenior(fewestPeople(closestToTime(result, time_template_const[i])))
		if len(result) > 0:
			sol = choice(result)
			print dayArr[i], 'num_solutions', len(result), 'time_off', countTimeOff(sol, time_template_const[i])
			retVal.append(convertSolution(sol, i))
			print '\n'
		else:
			print 'Day', i, 'no solution\n'
	return retVal


result = getAllSolutions()




def export(result):
	array = defaultdict(lambda: [])
	final_str = ''
	for i in range(7):
		for employee in employees:
			array[employee.name].append(result[i][employee.name])
	final_str += 'Supervisors\t' + '\t'.join(dayArr) + '\n'
	for name, intervals in array.iteritems():
		s = name
		if employees[index_map[name]].level == 3:
			for interval in intervals:
				s += '\t' + interval
			final_str += s + '\n'

	final_str += '\n\n'
	final_str += 'Servers\t\n'
	for name, intervals in array.iteritems():
		s = name
		if employees[index_map[name]].level == 2:
			for interval in intervals:
				s += '\t' + interval
			final_str += s + '\n'

	final_str += '\n\n'
	final_str += 'New Servers\t\n'
	for name, intervals in array.iteritems():
		s = name
		if employees[index_map[name]].level < 2:
			for interval in intervals:
				s += '\t' + interval
			final_str += s + '\n'
	f = open('output.txt', 'w')
	f.write(final_str)
			



export(result)



	

