#!/usr/bin/env python3
# -*- coding: utf_8 -*-

import os
import sys
import time
import json
import zlib
import copy
import base64
import psutil
import struct
import socket
import hashlib
import platform
import threading
import subprocess
import datetime as DateTimeLibrary
from urllib.request import urlopen
from urllib.error import URLError
from shutil import copyfile

import re


INFO = "info"
WARNING = "warning"
ERROR = "error"
DEBUG = "debug"


class Dict(dict):
	def __init__(self, *args, **kwargs):
		for item in args:
			self._parse_dict(item)
		self._parse_dict(kwargs)
	#end define
	
	def _parse_dict(self, d):
		for key, value in d.items():
			if type(value) == dict:
				value = Dict(value)
			if type(value) == list:
				value = self._parse_list(value)
			self[key] = value
	#end define
	
	def _parse_list(self, l):
		result = list()
		for value in l:
			if type(value) == dict:
				value = Dict(value)
			result.append(value)
		return result
	#end define
	
	def __setattr__(self, key, value):
		self[key] = value
	#end define
	
	def __getattr__(self, key):
		return self.get(key)
	#end define
#end class

class bcolors:
	'''This class is designed to display text in color format'''
	red = "\033[31m"
	green = "\033[32m"
	yellow = "\033[33m"
	blue = "\033[34m"
	magenta = "\033[35m"
	cyan = "\033[36m"
	endc = "\033[0m"
	bold = "\033[1m"
	underline = "\033[4m"
	default = "\033[39m"

	DEBUG = magenta
	INFO = blue
	OKGREEN = green
	WARNING = yellow
	ERROR = red
	ENDC = endc
	BOLD = bold
	UNDERLINE = underline

	def GetArgs(*args):
		text = ""
		for item in args:
			if item is None:
				continue
			text += str(item)
		return text
	#end define

	def Magenta(*args):
		text = bcolors.GetArgs(*args)
		text = bcolors.magenta + text + bcolors.endc
		return text
	#end define

	def Blue(*args):
		text = bcolors.GetArgs(*args)
		text = bcolors.blue + text + bcolors.endc
		return text
	#end define

	def Green(*args):
		text = bcolors.GetArgs(*args)
		text = bcolors.green + text + bcolors.endc
		return text
	#end define

	def Yellow(*args):
		text = bcolors.GetArgs(*args)
		text = bcolors.yellow + text + bcolors.endc
		return text
	#end define

	def Red(*args):
		text = bcolors.GetArgs(*args)
		text = bcolors.red + text + bcolors.endc
		return text
	#end define

	def Bold(*args):
		text = bcolors.GetArgs(*args)
		text = bcolors.bold + text + bcolors.endc
		return text
	#end define

	def Underline(*args):
		text = bcolors.GetArgs(*args)
		text = bcolors.underline + text + bcolors.endc
		return text
	#end define

	colors = {"red": red, "green": green, "yellow": yellow, "blue": blue, "magenta": magenta, "cyan": cyan, "endc": endc, "bold": bold, "underline": underline}
#end class

class MyPyClass:
	def __init__(self, file):
		self.file = file
		self.db = Dict()
		self.db.config = Dict()

		self.buffer = Dict()
		self.buffer.loglist = list()
		self.buffer.thread_count = None
		self.buffer.memory_using = None
		self.buffer.free_space_memory = None

		# Set default settings
		self.set_default_config()
		self.refresh()
	#end define

	def refresh(self):
		# Get program, log and database file name
		my_name = self.get_my_name()
		my_work_dir = self.get_my_work_dir()
		self.buffer.my_name = my_name
		self.buffer.my_dir = self.get_my_dir()
		self.buffer.my_full_name = self.get_my_full_name()
		self.buffer.my_path = self.get_my_path()
		self.buffer.my_work_dir = my_work_dir
		self.buffer.my_temp_dir = self.get_my_temp_dir()
		self.buffer.log_file_name = my_work_dir + my_name + ".log"
		self.buffer.db_file_name = my_work_dir + my_name + ".db"
		self.buffer.pid_file_path = my_work_dir + my_name + ".pid"

		# Check all directorys
		os.makedirs(self.buffer.my_work_dir, exist_ok=True)
		os.makedirs(self.buffer.my_temp_dir, exist_ok=True)
	#end define

	def run(self):
		# Check args
		if ("-ef" in sys.argv):
			file = open(os.devnull, 'w')
			sys.stdout = file
			sys.stderr = file
		if ("-d" in sys.argv):
			self.fork_daemon()
		if ("-s" in sys.argv):
			x = sys.argv.index("-s")
			filePath = sys.argv[x+1]
			self.get_settings(filePath)
		if ("--add2cron" in sys.argv):
			self.add_to_crone()

		# Start only one process (exit if process exist)
		if self.db.config.is_start_only_one_process:
			self.start_only_one_process()

		# Load local database
		self.load_db()

		# Remove old log file
		if (self.db.config.is_delete_old_log_file and os.path.isfile(self.buffer.log_file_name)):
			os.remove(self.buffer.log_file_name)

		# Start other threads
		threading.Thread(target=self.writing_log_file, name="Logging", daemon=True).start()
		threading.Thread(target=self.self_testing, name="self_testing", daemon=True).start()
		threading.Thread(target=self.db_saving, name="LocdbSaving", daemon=True).start()
		self.buffer.thread_count_old = threading.active_count()

		# Logging the start of the program
		self.add_log("Start program `{self.buffer.my_path}`")
	#end define

	def set_default_config(self):
		if self.db.config.log_level is None:
			self.db.config.log_level = INFO # info || debug
		if self.db.config.is_limit_log_file i None:
			self.db.config.is_limit_log_file = True
		if self.db.config.is_delete_old_log_file is None:
			self.db.config.is_delete_old_log_file = False
		if self.db.config.is_ignor_log_warning is None:
			self.db.config.is_ignor_log_warning = False
		if self.db.config.is_start_only_one_process is None:
			self.db.config.is_start_only_one_process = True
		if self.db.config.memory_using_limit is None:
			self.db.config.memory_using_limit = 50
		if self.db.config.is_db_saving is None:
			self.db.config.is_db_saving = False
		if self.db.config.is_writing_log_file is None:
			self.db.config.is_writing_log_file = True
	#end define

	def start_only_one_process(self):
		pid_file_path = self.buffer.pid_file_path
		if os.path.isfile(pid_file_path):
			file = open(pid_file_path, 'r')
			pid_str = file.read()
			file.close()
			try:
				pid = int(pid_str)
				process = psutil.Process(pid)
				full_process_name = " ".join(process.cmdline())
			except:
				full_process_name = ""
			if (full_process_name.find(self.buffer.my_full_name) > -1):
				print("The process is already running")
				sys.exit(1)
			#end if
		self.write_pid()
	#end define

	def write_pid(self):
		pid = os.getpid()
		pid_str = str(pid)
		pid_file_path = self.buffer.pid_file_path
		with open(pid_file_path, 'w') as file:
			file.write(pid_str)
	#end define

	def self_testing(self):
		self.add_log("Start self_testing thread.", DEBUG)
		while True:
			try:
				time.sleep(1)
				self.self_test()
			except Exception as err:
				self.add_log(f"self_testing: {err}", ERROR)
	#end define

	def self_test(self):
		process = psutil.Process(os.getpid())
		memory_using = b2mb(process.memory_info().rss)
		free_space_memory = b2mb(psutil.virtual_memory().available)
		threadCount = threading.active_count()
		self.buffer.free_space_memory = free_space_memory
		self.buffer.memory_using = memory_using
		self.buffer.thread_count = threadCount
		if memory_using > self.db.config.memory_using_limit:
			self.db.config.memory_using_limit += 50
			self.add_log(f"Memory using: {memory_using}Mb, free: {free_space_memory}Mb", WARNING)
	#end define

	def print_self_testing_result(self):
		thread_count_old = self.buffer.thread_count_old
		thread_count_new = self.buffer.thread_count
		memory_using = self.buffer.memory_using
		free_space_memory = self.buffer.free_space_memory
		self.add_log(color_text("{blue}Self testing informatinon:{endc}")
		self.add_log("Threads: {thread_count_new} -> {thread_count_old}")
		self.add_log("Memory using: {memory_using}Mb, free: {free_space_memory}Mb")
	#end define

	def get_thread_name(self):
		return threading.currentThread().getName()
	#end define

	def get_my_full_name(self):
		'''return "test.py"'''
		my_path = self.get_my_path()
		my_full_name = get_full_name_from_path(my_path)
		if len(my_full_name) == 0:
			my_full_name = "empty"
		return my_full_name
	#end define

	def get_my_name(self):
		'''return "test"'''
		my_full_name = self.get_my_full_name()
		my_name = my_full_name[:my_full_name.rfind('.')]
		return my_name
	#end define

	def get_my_path(self):
		'''return "/some_dir/test.py"'''
		my_path = os.path.abspath(self.file)
		return my_path
	#end define

	def get_my_dir(self):
		'''return "/some_dir/"'''
		my_path = self.get_my_path()
		# myDir = my_path[:my_path.rfind('/')+1]
		myDir = os.path.dirname(my_path)
		myDir = dir(myDir)
		return myDir
	#end define

	def get_my_work_dir(self):
		'''return "/usr/local/bin/test/" or "/home/user/.local/share/test/"'''
		if self.check_root_permission():
			# https://ru.wikipedia.org/wiki/FHS
			program_files_dir = "/usr/local/bin/"
		else:
			# https://habr.com/ru/post/440620/
			user_home_dir = dir(os.getenv("HOME"))
			program_files_dir = dir(os.getenv("XDG_DATA_HOME", user_home_dir + ".local/share/"))
		my_name = self.get_my_name()
		my_work_dir = dir(program_files_dir + my_name)
		return my_work_dir
	#end define

	def get_my_temp_dir(self):
		'''return "/tmp/test/"'''
		temp_files_dir = "/tmp/" # https://ru.wikipedia.org/wiki/FHS
		my_name = self.get_my_name()
		myTempDir = dir(temp_files_dir + my_name)
		return myTempDir
	#end define

	def get_lang(self):
		lang = os.getenv("LANG", "en")
		if "ru" in lang:
			lang = "ru"
		else:
			lang = "en"
		return lang
	#end define

	def check_root_permission(self):
		process = subprocess.run(["touch", "/checkpermission"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		if (process.returncode == 0):
			subprocess.run(["rm", "/checkpermission"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			result = True
		else:
			result = False
		return result
	#end define

	def add_log(self, inputText, mode=INFO):
		inputText = f"{inputText}"
		timeText = DateTimeLibrary.datetime.utcnow().strftime("%d.%m.%Y, %H:%M:%S.%f")[:-3]
		timeText = "{0} (UTC)".format(timeText).ljust(32, ' ')

		# Pass if set log level
		if self.db.config.log_level != DEBUG and mode == DEBUG:
			return
		elif self.db.config.is_ignor_log_warning and mode == WARNING:
			return

		# Set color mode
		if mode == INFO:
			colorStart = bcolors.INFO + bcolors.BOLD
		elif mode == WARNING:
			colorStart = bcolors.WARNING + bcolors.BOLD
		elif mode == ERROR:
			colorStart = bcolors.ERROR + bcolors.BOLD
		elif mode == DEBUG:
			colorStart = bcolors.DEBUG + bcolors.BOLD
		else:
			colorStart = bcolors.UNDERLINE + bcolors.BOLD
		modeText = "{0}{1}{2}".format(colorStart, "[{0}]".format(mode).ljust(10, ' '), bcolors.ENDC)

		# Set color thread
		if mode == ERROR:
			colorStart = bcolors.ERROR + bcolors.BOLD
		else:
			colorStart = bcolors.OKGREEN + bcolors.BOLD
		threadText = "{0}{1}{2}".format(colorStart, "<{0}>".format(self.get_thread_name()).ljust(14, ' '), bcolors.ENDC)
		logText = modeText + timeText + threadText + inputText

		# Queue for recording
		self.buffer.loglist.append(logText)

		# Print log text
		print(logText)
	#end define

	def writing_log_file(self):
		if self.db.config.is_writing_log_file == False:
			return
		self.add_log("Start writing_log_file thread.", DEBUG)
		while True:
			time.sleep(1)
			self.try_write_log_file()
	#end define

	def try_write_log_file(self):
		try:
			self.write_log_file()
		except Exception as err:
			self.add_log(f"try_write_log_file error: {err}", ERROR)
	#end define

	def write_log_file(self):
		logFileName = self.buffer.log_file_name

		with open(logFileName, 'a') as file:
			while len(self.buffer.loglist) > 0:
				logText = self.buffer.loglist.pop(0)
				file.write(logText + '\n')
			#end while
		#end with

		# Control log size
		if self.db.config.is_limit_log_file == False:
			return
		allline = self.count_lines(logFileName)
		if allline > 4096 + 256:
			delline = allline - 4096
			f=open(logFileName).readlines()
			i = 0
			while i < delline:
				f.pop(0)
				i = i + 1
			with open(logFileName,'w') as F:
				F.writelines(f)
	#end define

	def count_lines(self, filename, chunk_size=1<<13):
		if not os.path.isfile(filename):
			return 0
		with open(filename) as file:
			return sum(chunk.count('\n')
				for chunk in iter(lambda: file.read(chunk_size), ''))
	#end define

	def DictToBase64WithCompress(self, item):
		string = json.dumps(item)
		original = string.encode("utf-8")
		compressed = zlib.compress(original)
		b64 = base64.b64encode(compressed)
		data = b64.decode("utf-8")
		return data
	#end define

	def Base64ToDictWithDecompress(self, item):
		data = item.encode("utf-8")
		b64 = base64.b64decode(data)
		decompress = zlib.decompress(b64)
		original = decompress.decode("utf-8")
		data = json.loads(original)
		return data
	#end define

	def exit(self):
		if len(self.buffer.loglist) > 0:
			time.sleep(1.1)
		if os.path.isfile(self.buffer.pid_file_path):
			os.remove(self.buffer.pid_file_path)
		sys.exit(0)
	#end define

	def read_file(self, path):
		with open(path, 'rt') as file:
			text = file.read()
		return text
	#end define

	def write_file(self, path, text=""):
		with open(path, 'wt') as file:
			file.write(text)
	#end define

	def read_db(self):
		err = None
		for i in range(10):
			try:
				return self.read_db_process()
			except Exception as ex:
				err = ex
				time.sleep(0.01)
		raise Exception(f"read_db error: {err}")
	#end define

	def read_db_process(self):
		db_path = self.buffer.db_file_name
		text = self.read_file(db_path)
		return json.loads(text)
	#end define

	def write_db(self, data):
		thr = threading.Thread(target=self.write_db_process, 
			name="write_db_process", 
			args=(data, ), 
			daemon=False)
		thr.start()
		thr.join()
	#end define

	def write_db_process(self, data):
		db_path = self.buffer.db_file_name
		text = json.dumps(data, indent=4)
		self.lock_file(db_path)
		self.write_file(db_path, text)
		self.unlock_file(db_path)
	#end define

	def lock_file(self, path):
		pid_path = path + ".lock"
		for i in range(300):
			if os.path.isfile(pid_path):
				time.sleep(0.01)
			else:
				self.write_file(pid_path)
				return
		raise Exception("lock_file error: time out.")
	#end define

	def unlock_file(self, path):
		pid_path = path + ".lock"
		try:
			os.remove(pid_path)
		except:
			print("Wow. You are faster than me")
	#end define

	def merge_dict(self, local_data, file_data, old_file_data):
		need_write_local_data = False
		if local_data == file_data and file_data == old_file_data:
			return need_write_local_data
		#end if
		
		dict_keys = list()
		dict_keys += [key for key in local_data if key not in dict_keys]
		dict_keys += [key for key in file_data if key not in dict_keys]
		for key in dict_keys:
			local_item = local_data.get(key)
			file_item = file_data.get(key)
			old_file_item = old_file_data.get(key)
			local_item_type = type(local_item)
			file_item_type = type(file_item)
			old_file_item_type = type(file_item)
			if local_item != file_item and local_item_type == dict and file_item_type == dict and old_file_item_type == dict:
				buff = self.merge_dict(local_item, file_item, old_file_item)
				if buff is True:
					need_write_local_data = True
			elif local_item != old_file_item and file_item == old_file_item:
				#print(f"find db change {key}: {old_file_item} -> {local_item}")
				old_file_data[key] = local_item
				need_write_local_data = True
			elif local_item == old_file_item and file_item != old_file_item:
				#print(f"find config file change {key}: {old_file_item} -> {file_item}")
				old_file_data[key] = file_item
				local_data[key] = file_item
			elif local_item != old_file_item and file_item != old_file_item:
				#print(f"find db and config file change {key}: {old_file_item} -> {file_item} <- {local_item}")
				old_file_data[key] = file_item
				local_data[key] = file_item
		return need_write_local_data
	#end define

	def save_db(self):
		data = self.read_db()
		buff = self.merge_dict(self.db, data, self.buffer.old_db)
		if buff is True:
			self.write_db(self.db)
	#end define
	
	def db_saving(self):
		if self.db.config.is_db_saving == False:
			return
		self.add_log("Start db_saving thread.", DEBUG)
		while True:
			time.sleep(3) # 3 sec
			self.save_db()
	#end define

	def load_db(self, db_path=False):
		result = False
		if not db_path:
			db_path = self.buffer.db_file_name
		try:
			data = read_db()
			self.db.update(data)
			self.buffer.old_db.update(data)
			self.set_default_config()
			result = True
		except Exception as err:
			self.add_log(f"load_db error: {err}", ERROR)
		return result
	#end define

	def get_settings(self, filePath):
		try:
			file = open(filePath)
			text = file.read()
			file.close()
			self.db = json.loads(text)
			self.db_save()
			print("get setting successful: " + filePath)
			self.exit()
		except Exception as err:
			self.add_log(f"get_settings error: {err}", WARNING)
	#end define

	def get_python3_path(self):
		python3_path = "/usr/bin/python3"
		if platform.system() == "OpenBSD":
			python3_path = "/usr/local/bin/python3"
		return python3_path
	# end define

	def fork_daemon(self):
		my_path = self.buffer.my_path
		python3_path = self.get_python3_path()
		cmd = " ".join([python3_path, my_path, "-ef", '&'])
		os.system(cmd)
		print("daemon start: " + my_path)
		self.exit()
	#end define

	def add_to_crone(self):
		python3_path = self.get_python3_path()
		cronText = f"@reboot {python3_path} \"{self.buffer.my_path}\" -d\n"
		os.system("crontab -l > mycron")
		with open("mycron", 'a') as file:
			file.write(cronText)
		os.system("crontab mycron && rm mycron")
		print("add to cron successful: " + cronText)
		self.exit()
	#end define

	def try_function(self, func, **kwargs):
		args = kwargs.get("args")
		result = None
		try:
			if args is None:
				result = func()
			else:
				result = func(*args)
		except Exception as err:
			self.add_log(f"{func.__name__} error: {err}", ERROR)
		return result
	#end define

	def start_thread(self, func, **kwargs):
		name = kwargs.get("name", func.__name__)
		args = kwargs.get("args")
		if args is None:
			threading.Thread(target=func, name=name, daemon=True).start()
		else:
			threading.Thread(target=func, name=name, args=args, daemon=True).start()
		self.add_log("Thread {name} started".format(name=name), "debug")
	#end define

	def cycle(self, func, sec, args):
		while True:
			self.try_function(func, args=args)
			time.sleep(sec)
	#end define

	def start_cycle(self, func, **kwargs):
		name = kwargs.get("name", func.__name__)
		args = kwargs.get("args")
		sec = kwargs.get("sec")
		self.start_thread(self.cycle, name=name, args=(func, sec, args))
	#end define

	def init_translator(self, filePath=None):
		if filePath is None:
			filePath = self.db.translate_file_path
		file = open(filePath, encoding="utf-8")
		text = file.read()
		file.close()
		self.buffer.translate = json.loads(text)
	#end define

	def translate(self, text):
		lang = self.get_lang()
		text_list = text.split(' ')
		for item in text_list:
			sitem = self.buffer.translate.get(item)
			if sitem is None:
				continue
			ritem = sitem.get(lang)
			if ritem is not None:
				text = text.replace(item, ritem)
		return text
	#end define
#end class

def get_hash_md5(fileName):
	BLOCKSIZE = 65536
	hasher = hashlib.md5()
	with open(fileName, 'rb') as file:
		buf = file.read(BLOCKSIZE)
		while len(buf) > 0:
			hasher.update(buf)
			buf = file.read(BLOCKSIZE)
	return(hasher.hexdigest())
#end define

def parse(text, search, search2=None):
	if search is None or text is None:
		return None
	if search not in text:
		return None
	text = text[text.find(search) + len(search):]
	if search2 is not None and search2 in text:
		text = text[:text.find(search2)]
	return text
#end define

def ping(hostname):
	process = subprocess.run(["ping", "-c", 1, "-w", 3, hostname], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	if process.returncode == 0:
		result = True
	else:
		result = False
	return result
#end define

def get_request(url):
	link = urlopen(url)
	data = link.read()
	text = data.decode("utf-8")
	return text
#end define

def dir(inputDir):
	if (inputDir[-1:] != '/'):
		inputDir += '/'
	return inputDir
#end define

def b2mb(item):
	return round(int(item)/1000/1000, 2)
#end define

def search_file_in_dir(path, fileName):
	result = None
	for entry in os.scandir(path):
		if entry.name.startswith('.'):
			continue
		if entry.is_dir():
			buff = search_file_in_dir(entry.path, fileName)
			if buff is not None:
				result = buff
				break
		elif entry.is_file():
			if entry.name == fileName:
				result = entry.path
				break
	return result
#end define

def search_dir_in_dir(path, dirName):
	result = None
	for entry in os.scandir(path):
		if entry.name.startswith('.'):
			continue
		if entry.is_dir():
			if entry.name == dirName:
				result = entry.path
				break
			buff = search_dir_in_dir(entry.path, dirName)
			if buff is not None:
				result = buff
				break
	return result
#end define

def get_dir_from_path(path):
	return path[:path.rfind('/')+1]
#end define

def get_full_name_from_path(path):
	return path[path.rfind('/')+1:]
#end define

def print_table(arr):
	buff = dict()
	for i in range(len(arr[0])):
		buff[i] = list()
		for item in arr:
			buff[i].append(len(str(item[i])))
	for item in arr:
		for i in range(len(arr[0])):
			index = max(buff[i]) + 2
			ptext = str(item[i]).ljust(index)
			if item == arr[0]:
				ptext = bcolors.Blue(ptext)
				ptext = bcolors.Bold(ptext)
			print(ptext, end = '')
		print()
#end define

def get_timestamp():
	return int(time.time())
#end define

def color_text(text):
	for cname in bcolors.colors:
		item = '{' + cname + '}'
		if item in text:
			text = text.replace(item, bcolors.colors[cname])
	return text
#end define

def color_print(text):
	text = color_text(text)
	print(text)
#end define

def get_load_avg():
	psys=platform.system()
	if psys in ['FreeBSD','Darwin','OpenBSD']:
		loadavg = subprocess.check_output(["sysctl", "-n", "vm.loadavg"]).decode('utf-8')
		if psys != 'OpenBSD':
			m = re.match(r"{ (\d+\.\d+) (\d+\.\d+) (\d+\.\d+).+", loadavg)
		else:
			m = re.match("(\d+\.\d+) (\d+\.\d+) (\d+\.\d+)", loadavg)
		if m:
			loadavg_arr = [m.group(1), m.group(2), m.group(3)];
		else:
			loadavg_arr = [0.00,0.00,0.00]
	else:
		file = open("/proc/loadavg")
		loadavg = file.read()
		file.close()
		loadavg_arr = loadavg.split(' ')

	output = loadavg_arr[:3]
	for i in range(len(output)):
		output[i] = float(output[i])
	return output
#end define

def get_internet_interface_name():
	if platform.system() == "OpenBSD":
		cmd="ifconfig egress"
		text = subprocess.getoutput(cmd)
		lines = text.split('\n')
		items = lines[0].split(' ')
		interface_name = items[0][:-1]
	else:
		cmd = "ip --json route"
		text = subprocess.getoutput(cmd)
		try:
			arr = json.loads(text)
			interface_name = arr[0]["dev"]
		except:
			lines = text.split('\n')
			items = lines[0].split(' ')
			buff = items.index("dev")
			interface_name = items[buff+1]
	return interface_name
#end define

def thr_sleep():
	while True:
		time.sleep(10)
#end define

def timestamp2datetime(timestamp, format="%d.%m.%Y %H:%M:%S"):
	datetime = time.localtime(timestamp)
	result = time.strftime(format, datetime)
	return result
#end define

def timeago(timestamp=False):
	"""
	Get a datetime object or a int() Epoch timestamp and return a
	pretty string like 'an hour ago', 'Yesterday', '3 months ago',
	'just now', etc
	"""
	now = DateTimeLibrary.datetime.now()
	if type(timestamp) is int:
		diff = now - DateTimeLibrary.datetime.fromtimestamp(timestamp)
	elif isinstance(timestamp, DateTimeLibrary.datetime):
		diff = now - timestamp
	elif not timestamp:
		diff = now - now
	second_diff = diff.seconds
	day_diff = diff.days

	if day_diff < 0:
		return ''

	if day_diff == 0:
		if second_diff < 10:
			return "just now"
		if second_diff < 60:
			return str(second_diff) + " seconds ago"
		if second_diff < 120:
			return "a minute ago"
		if second_diff < 3600:
			return str(second_diff // 60) + " minutes ago"
		if second_diff < 7200:
			return "an hour ago"
		if second_diff < 86400:
			return str(second_diff // 3600) + " hours ago"
	if day_diff < 31:
		return str(day_diff) + " days ago"
	if day_diff < 365:
		return str(day_diff // 30) + " months ago"
	return str(day_diff // 365) + " years ago"
#end define

def time2human(diff):
	dt = DateTimeLibrary.timedelta(seconds=diff)
	if dt.days < 0:
		return ''

	if dt.days == 0:
		if dt.seconds < 60:
			return str(dt.seconds) + " seconds"
		if dt.seconds < 3600:
			return str(dt.seconds // 60) + " minutes"
		if dt.seconds < 86400:
			return str(dt.seconds // 3600) + " hours"
	return str(dt.days) + " days"
#end define

def dec2hex(dec):
	h = hex(dec)[2:]
	if len(h) % 2 > 0:
		h = '0' + h
	return h
#end define

def hex2dec(h):
	return int(h, base=16)
#end define

def run_as_root(args):
	text = platform.version()
	psys = platform.system()
	if "Ubuntu" in text:
		args = ["sudo", "-s"] + args
	elif psys == "OpenBSD":
		args = ["doas"] + args
	else :
		print("Enter root password")
		args = ["su", "-c"] + [" ".join(args)]
	exit_code = subprocess.call(args)
	return exit_code
#end define

def add2systemd(**kwargs):
	name = kwargs.get("name")
	start = kwargs.get("start")
	post = kwargs.get("post", "/bin/echo service down")
	user = kwargs.get("user", "root")
	group = kwargs.get("group", user)
	workdir = kwargs.get("workdir", None)
	pversion = platform.version()
	psys = platform.system()
	path = "/etc/systemd/system/{name}.service".format(name=name)

	if psys == "OpenBSD":
	    path = "/etc/rc.d/{name}".format(name=name)
	if name is None or start is None:
		raise Exception("Bad args. Need 'name' and 'start'.")
		return
	if os.path.isfile(path):
		print("Unit exist.")
		return
	# end if

	text = f"""
[Unit]
Description = {name} service. Created by https://github.com/igroman787/mypylib.
After = network.target

[Service]
Type = simple
Restart = always
RestartSec = 30
ExecStart = {start}
ExecStopPost = {post}
User = {user}
Group = {group} 
{f"WorkingDirectory = {workdir}" if workdir else '# WorkingDirectory not set'}
LimitNOFILE = infinity
LimitNPROC = infinity
LimitMEMLOCK = infinity

[Install]
WantedBy = multi-user.target
"""

	if psys == "OpenBSD" and 'APRENDIENDODEJESUS' in pversion:
		text = f"""
#!/bin/ksh
servicio="{start}"
servicio_user="{user}"
servicio_timeout="3"

. /etc/rc.d/rc.subr

rc_cmd $1
"""

	file = open(path, 'wt')
	file.write(text)
	file.close()

	# Изменить права
	args = ["chmod", "664", path]
	subprocess.run(args)

	# Разрешить запуск
	args = ["chmod", "+x", path]
	subprocess.run(args)

	if psys != "OpenBSD":
		# Перезапустить systemd
		args = ["systemctl", "daemon-reload"]
		subprocess.run(args)
	#end if

	# Включить автозапуск
	if psys == "OpenBSD":
		args = ["rcctl", "enable", name]
	else:
		args = ["systemctl", "enable", name]
	subprocess.run(args)
#end define

def ip2int(addr):
	return struct.unpack("!i", socket.inet_aton(addr))[0]
#end define

def int2ip(dec):
	return socket.inet_ntoa(struct.pack("!i", dec))
#end define

def get_service_status(name):
	status = False
	psys = platform.system()
	if psys == "OpenBSD":
		result = os.system(f"rcctl check {name}")
	else:
		result = os.system(f"systemctl is-active --quiet {name}")
	if result == 0:
		status = True
	return status
#end define

def get_service_uptime(name):
	property = "ExecMainStartTimestampMonotonic"
	args = ["systemctl", "show", name, "--property=" + property]
	process = subprocess.run(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
	output = process.stdout.decode("utf-8")
	err = process.stderr.decode("utf-8")
	if len(err) > 0:
		return
	startTimestampMonotonic = parse(output, f"{property}=", '\n')
	startTimestampMonotonic = int(startTimestampMonotonic) / 10**6
	bootTimestamp = psutil.boot_time()
	timeNow = time.time()
	startTimestamp = bootTimestamp + startTimestampMonotonic
	uptime = int(timeNow - startTimestamp)
	return uptime
#end define

def get_service_pid(name):
	property = "MainPID"
	args = ["systemctl", "show", name, "--property=" + property]
	process = subprocess.run(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
	output = process.stdout.decode("utf-8")
	err = process.stderr.decode("utf-8")
	if len(err) > 0:
		return
	pid = int(parse(output, f"{property}=", '\n'))
	return pid
#end define

def get_git_hash(git_path, short=False):
	args = ["git", "rev-parse", "HEAD"]
	if short is True:
		args.insert(2, '--short')
	process = subprocess.run(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=git_path, timeout=3)
	output = process.stdout.decode("utf-8")
	err = process.stderr.decode("utf-8")
	if len(err) > 0:
		return
	buff = output.split('\n')
	return buff[0]
#end define

def get_git_url(git_path):
	args = ["git", "remote", "-v"]
	try:
		process = subprocess.run(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=git_path, timeout=3)
		output = process.stdout.decode("utf-8")
		err = process.stderr.decode("utf-8")
	except Exception as ex:
		err = str(ex)
	if len(err) > 0:
		return
	lines = output.split('\n')
	url = None
	for line in lines:
		if "origin" in line:
			buff = line.split()
			url = buff[1]
		#end if
	return url
#end define

def get_git_author_and_repo(git_path):
	author = None
	repo = None
	url = get_git_url(git_path)
	if url is not None:
		buff = url.split('/')
		if len(buff) == 5:
			author = buff[3]
			repo = buff[4]
			repo = repo.split('.')
			repo = repo[0]
	return author, repo
#end define

def get_git_last_remote_commit(git_path, branch="master"):
	author, repo = get_git_author_and_repo(git_path)
	if author is None or repo is None:
		return
	url = f"https://api.github.com/repos/{author}/{repo}/branches/{branch}"
	sha = None
	try:
		text = get_request(url)
		data = json.loads(text)
		sha = data["commit"]["sha"]
	except URLError: pass
	return sha
#end define

def get_git_branch(git_path):
	args = ["git", "branch", "-v"]
	process = subprocess.run(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=git_path, timeout=3)
	output = process.stdout.decode("utf-8")
	err = process.stderr.decode("utf-8")
	if len(err) > 0:
		return
	lines = output.split('\n')
	branch = None
	for line in lines:
		if "*" in line:
			buff = line.split()
			branch = buff[1]
		#end if
	return branch
#end define

def check_git_update(git_path):
	branch = get_git_branch(git_path)
	newHash = get_git_last_remote_commit(git_path, branch)
	oldHash = get_git_hash(git_path)
	result = False
	if oldHash != newHash:
		result = True
	if oldHash is None or newHash is None:
		result = None
	return result
#end define

