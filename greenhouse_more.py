from collections import defaultdict
import csv
from random import choice
from copy import deepcopy

newServerMinHour = 8#4*2
ServerMinHour = 10#5*2
maxHour = 16
minNumSupervisors = 1
debugMode = False
allowFewerEmployee = False
printDetail = False
maxTableSize = 1000
maxIteration = 1000

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

	def __gt__(self, other):
	    return self.level > other.level


def parseCSV(filename):
	with open(filename, 'rb') as f:
		reader = csv.reader(f, delimiter="\t")
		return list([[item.strip() for item in row] for row in reader])


def parseRequirement():
	arr = parseCSV('requirement.csv')
	minMap, maxMap = {}, {}
	for line in arr:
		if line[1] == 'min':
			minMap[line[0]] = int(line[2])
		elif line[1] == 'max':
			maxMap[line[0]] = int(line[2])
	return minMap, maxMap

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
		for j in range(3, len(arr[i])):
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
	

minMap, maxMap = parseRequirement()


def getMinWorkingTime(employee):
	person = None
	if isinstance(employee, str):
		person = employees[index_map[employee]]
	elif isinstance(employee, int):
		person = employees[employee]
	else:
		person = employee
	if person.name in minMap:
		return minMap[person.name]
	else:
		return ServerMinHour if person.level > 1 else newServerMinHour


(employees, index_map) = parseEmployee()
time_template_const = parseTemplate()
availability = parseAvailability()


def getEmployeeCoverTime(employees, time, availability, time_template):
	open_time, close_time = getStartAndEnd(time_template)
	retVal = []
	for employee in employees:
		for duration in availability[employee.name]:
			if duration[0] <= time and duration[1] >= time:
				end_time = min(duration[1], time + maxHour - 1, close_time)
				start_time = max(end_time - maxHour + 1, duration[0], open_time)
				retVal.append([employee, [start_time, end_time]])
	return retVal


# return all employees who are available at that DAY
def getAvailableEmployee(employees, availability):
	retVal = [employee for employee in employees if len(availability[employee.name]) > 0]
	return sorted(retVal, reverse = True)






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
def checkValidSolution(solution, day):
	for i in range(len(solution)):
		if time_template_const[day][i] > 0:
			hasSupervisor = False
			for j in solution[i]:
				if employees[j].level > 2:
					hasSupervisor = True
			if not hasSupervisor:
				if debugMode:
					print 'no supervisor', [[employees[index].name for index in array] for array in solution], '\n', solution, '\n', [len(item) for item in solution], '\n', time_template_const[day]
				return False
		if time_template_const[day][i] > 1:
			hasDriver = False
			for j in solution[i]:
				if employees[j].isDriver:
					hasDriver = True
			if not hasDriver:
				if debugMode:
					print 'no driver'
				return False
		if not allowFewerEmployee:
			if len(solution[i]) < time_template_const[day][i]:
				if debugMode:
					print 'few employee in day', day
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
	# for i in range(len(time_template)):
	# 	if time_template[i] == 0 and solution[i] > 0:
	# 		return None
	return solution



def countTimeOff(solution, time_template):
	timeOff = 0
	for i in range(len(solution)):
		timeOff += abs(len(solution[i]) - time_template[i])
	return timeOff
	


def getDaySolutions(i):
	dptable = set()
	availableEmployees = getAvailableEmployee(employees, availability[i])
	allSolutions = dfs_employees (availability[i], time_template_const[i], availableEmployees, 0, [[] for item in time_template_const[i]], dptable)

	retVal = []
	for item in allSolutions:
		if checkValidSolution(item[0], i):
			solution = optimizeSolution(item[0], time_template_const[i])
			if not solution == None:
				retVal.append(solution)
	print 'Get day', i
	return retVal


def getStartAndEnd(time_template):
	start, end = 0, 0
	for i in range(len(time_template)):
		if time_template[i] > 0:
			start = i
			break
	for i in range(len(time_template)-1, -1, -1):
		if time_template[i] > 0:
			end = i
			break
	return start, end


def intToTime(i, day):
	(start, end) = getStartAndEnd(time_template_const[day])
	if i == 0:
		return 'Open'
	elif i > end:
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
# def getAllSolutions():
# 	retVal = []
# 	for i in range(7):
# 		result = getDaySolutions(i)
# 		result = moreSenior(fewestPeople(closestToTime(result, time_template_const[i])))
# 		if len(result) > 0:
# 			sol = choice(result)
# 			print dayArr[i], 'num_solutions', len(result), 'time_off', countTimeOff(sol, time_template_const[i])
# 			if printDetail:
# 				print sol, '\n', [len(item) for item in sol], '\n', time_template_const[i]
# 			retVal.append(convertSolution(sol, i))
# 			print '\n'
# 		else:
# 			print 'Day', i, 'no solution\n'
# 			retVal.append([])
# 	return retVal
def getAllSolutions():
	retVal = [moreSenior(fewestPeople(closestToTime(getDaySolutions(i), time_template_const[i]))) for i in range(7)]
	bestSolution = None
	maxNumPeople = 0
	for iteration in range(maxIteration):
		currSolution = []
		for solutions in retVal:
			currSolution.append(choice(solutions) if len(solutions) > 0 else None)
		s = set()
		for daySolution in currSolution:
			if daySolution:
				for section in daySolution:
					for people in section:
						s.add(people)
		if len(s) > maxNumPeople:
			maxNumPeople = len(s)
			bestSolution = currSolution
			if len(s) == len(employees):
				break

	for i in range(7):
		sol = bestSolution[i]
		if sol:
			print dayArr[i], 'num_solutions', len(retVal[i]), 'time_off', countTimeOff(sol, time_template_const[i])
			if printDetail:
				print sol, '\n', [len(item) for item in sol], '\n', time_template_const[i]
			retVal[i] = convertSolution(sol, i)
			print '\n'
		else:
			print 'Day', i, 'no solution\n'
			retVal[i] = []

	if maxNumPeople < len(employees):
		print 'Unable to find solutions in', maxIteration, 'that everyone can work'
	return retVal


result = getAllSolutions()




def export(result):
	array = defaultdict(lambda: [])
	final_str = ''
	for i in range(7):
		if len(result[i]) == 0:
			print 'Day', i, 'no solution\n'
			for employee in employees:
				array[employee.name].append("")
		else:
			for employee in employees:
				array[employee.name].append(result[i][employee.name])
	final_str += 'Supervisors\t' + '\t'.join(dayArr) + '\n'
	for name, intervals in array.iteritems():
		s = name
		if employees[index_map[name]].level >= 3:
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
	f = open('output.csv', 'w')
	f.write(final_str)
			



export(result)