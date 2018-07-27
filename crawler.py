import sqlite3
import sys
import os
import re
database = "lib_stats.db"
	
if os.path.exists(database):
    os.remove(database)
    
conn = sqlite3.connect(database)

class Libset:
	name = ""
	category = ""
	version = ""
	release_date = ""
	old_version = False
	root_package = ""
	fullmatch = False
	comment = ""
	
class Appset:
	filename = ""
	packagename = ""
	version = ""
	vendor = ""
	
i = 0
currentvendor = ""

def analyze(contents):
	
	app = classifyApp(contents)
	
	c = conn.cursor()
	c.execute("insert into apps values (?, ?, ?, ?)", (app.packagename, app.filename, app.version, app.vendor))
	
	istart = contents.find("== Report ==")
	contents = contents[istart:]
	ifull = contents.find("- Full library matches:")
	ipartial = contents.find("- Partial library matches:")
	fullmatch = contents[ifull:ipartial]
	partmatch = contents[ipartial:]
	
	fullmatch = fullmatch.split("name:")
	partmatch = partmatch.split("name:")
	
	add(app.filename, fullmatch, True)
	add(app.filename, partmatch, False)
			

def add(filename, matches, fullmatch):
	global i
	c = conn.cursor()
	for match in matches:
		if "category" in match:
			result = classifyLib("name:" + match)
			result.fullmatch = fullmatch
			c.execute("insert into libs values (?, ?, ?, ?, ?, ?, ?, ?, ?)", (i, result.name, result.category, result.version, result.release_date, result.old_version, result.root_package, result.fullmatch, result.comment))
			c.execute("insert into relations values (?, ?)", (filename, i))
			i += 1

def classifyApp(contents):
	app = Appset()
	
	
	m = re.search("Package name:\s+(.+)", contents)
	app.packagename = m.group(1)
	if "LibraryIdentifier" in app.packagename:
		app.packagename = "error"
	m = re.search("Process app:\s+(.+)", contents)
	app.filename = m.group(1)
	m = re.search("Version code:\s+(.+)", contents)
	app.version = m.group(1)
	app.vendor = currentvendor
	
	return app

def classifyLib(split):
	out = Libset()
	m = re.search("name:\s+(.*)", split)
	out.name = m.group(1)
	m = re.search("category:\s+(.*)", split)
	out.category = m.group(1)
	m = re.search("version:\s+(.*?)\s+(\[OLD VERSION\])?", split)
	out.version = m.group(1)
	if m.group(2):
		out.old_version = True
	m = re.search("release-date:\s+(.*)", split)
	out.release_date = m.group(1)
	m = re.search("lib root package:\s+(.*)", split)
	out.root_package = m.group(1)
	m = re.search("comment:\s+(.*)", split)
	if(m):
		out.comment = m.group(1)
	
	return out
	
	
	
def main():
	
	c = conn.cursor()
	c.execute('''CREATE TABLE apps (package text, filename text, version number, vendor text)''')
	c.execute('''CREATE TABLE relations (filename text, lib_id integer)''')
	c.execute('''CREATE TABLE libs (lib_id integer primary key, name text, category text, version text, release_date text, old_version bool, root_package text, fullmatch bool, comment text)''')
	global currentvendor
	for folder in sys.argv:
		if currentvendor == "":
			currentvendor = "test"
			continue
		else:
			currentvendor = folder
		for fn in os.listdir(folder):
			with open(folder + "/" + fn) as f:
				s = f.read()
				analyze(s)
		conn.commit()
		
if __name__ == "__main__":
	main()
