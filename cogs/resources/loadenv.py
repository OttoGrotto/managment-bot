import os

class LoadENV:
	def __init__(self):
		self.loadenv()

	def loadenv(self):
		for i in os.listdir("."):
			if i == ".env":
				with open(i) as envfile:
					envlines = envfile.readlines()
					for line in envlines:
						if line.startswith("#") or line.startswith("\n"):
							continue
						else:
							line = line.split("=")
							os.environ[line[0].split("export")[1].replace(" ", "")] = line[1].replace("\n", "").replace(" ", "").replace('"', "")
