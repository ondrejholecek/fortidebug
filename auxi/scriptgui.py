#!/usr/bin/env python2.7

import Tkinter as tk
import tkMessageBox
import tkFileDialog
import os
import re
import xml.etree.ElementTree
import requests
import time

class ScriptFile:
	def __init__(self, url):
		self.url = url

		self.status_ok = False
		self.message   = ""
		self.cycles    = []
		self.profiles  = []

		self.load()

	def load(self):
		g = re.search("^(\S+)://(.*)$", self.url)
		if g == None:
			try:
				e = xml.etree.ElementTree.parse(self.url).getroot()
				self.status_ok = True
				self.message   = "Script file downloaded"
			except:
				self.status_ok = False
				self.message   = "Unable to parse script file (1)"
				return

		elif g.group(1) == 'file':
			try:
				e = xml.etree.ElementTree.parse(g.group(2)).getroot()
				self.status_ok = True
				self.message   = "Script file downloaded"
			except:
				self.status_ok = False
				self.message   = "Unable to parse script file (2)"
				return
		else:
			errcount = 0
			while True:
				try:
					r = requests.get(self.url)
				except Exception, e:
					errcount += 1
					if errcount >= 3:
						self.status_ok = False
						self.message   = "Unable to download script file (%s)" % (str(e),)
						return
					time.sleep(1)
				else:
					break

			if r.status_code != 200: 
				self.status_ok = False
				self.message   = "Unable to download script file (4)"
				return

			else:
				self.real_url = r.url
				try:
					e = xml.etree.ElementTree.fromstring(r.text)
					self.status_ok = True
					self.message   = "Script file downloaded"
				except:
					self.status_ok = False
					self.message   = "Unable to parse script file (5)"
					return
			
		# verify we can work with this file
		if e.tag != "fortimonitor_scriptfile":
			self.status_ok = False
			self.message   = "This is not correct script file"
			return
		
		# find cycles and profiles
		try:
			for c in e.findall("cycles/cycle"):
				self.cycles.append(c.attrib['name'])
		except:
			self.status_ok = False
			self.message   = "Cannot find any cycles in the script file"
			return

		try:
			for c in e.findall("profiles/profile"):
				self.profiles.append(c.attrib['name'])
		except:
			self.status_ok = False
			self.message   = "Cannot find any profiles in the script file"
			return


class App(tk.Frame):
	def __init__(self, master=None):
		tk.Frame.__init__(self, master)

		self.master = master
		self.inputs = {}

		self.pack()
		self.createWidgets()

		self.winfo_toplevel().title("FortiMonitor ScriptGUI")

	def create_input(self, parent, row, label, name, width=None, show=None, default=None, isselect=False, islist=False):
		self.inputs[name] = {}

		self.inputs[name]['label'] = tk.Label(parent, text=label, width=10, anchor="e")
		self.inputs[name]['label'].grid(row=row, column=0, sticky="W")

		self.inputs[name]['value'] = tk.StringVar()
		if isselect:
			self.inputs[name]['value'].set(default)
			self.inputs[name]['input'] = tk.OptionMenu(parent, self.inputs[name]['value'], default)
			self.inputs[name]['input'].grid(row=row, column=1, sticky="WE")
		elif islist:
			f = tk.Frame(parent)
			scrollbar = tk.Scrollbar(f, orient=tk.VERTICAL)
			self.inputs[name]['input'] = tk.Listbox(f, selectmode=tk.MULTIPLE, exportselection=0, height=10, yscrollcommand=scrollbar.set, width=49)
			self.inputs[name]['input'].grid(row=0, column=0, sticky="WE")
			scrollbar.config(command=self.inputs[name]['input'].yview)
			scrollbar.grid(row=0, column=1, sticky="NS")
			f.grid(row=row, column=1, sticky="WE")
		else:
			if default != None: self.inputs[name]['value'].set(default)
			self.inputs[name]['input'] = tk.Entry(parent, width=width, textvar=self.inputs[name]['value'], show=show)
			self.inputs[name]['input'].grid(row=row, column=1, sticky="WE")

	def createWidgets(self):

		# Widget group - FortiGate connection settings
		group_fgt = tk.LabelFrame(self, text="FortiGate", padx=5, pady=5)
		self.create_input(group_fgt, 0, "Host:", "host", 50)
		self.create_input(group_fgt, 1, "Port:", "port", 50, default="22")
		self.create_input(group_fgt, 2, "Usernane:", "username")
		self.create_input(group_fgt, 3, "Password:", "password", show="*")
		group_fgt.grid(row=0, column=0, padx=10, pady=10, sticky="WE")

		# Widget group - Script parameters
		group_script = tk.LabelFrame(self, text="Script options", padx=5, pady=5)
		self.create_input(group_script, 0, "Script URL:", "url", 50, default="https://scripts.fortimonitor.com/global/latest.xml")

		self.btn_load = tk.Button(group_script, text="Load", command=self.script_entered)
		self.btn_load.grid(row=1, column=1, sticky="we")

		self.create_input(group_script, 2, "Cycle name:", "cycle", islist=True)
		self.create_input(group_script, 3, "Profile:", "profile", isselect=True, default="<default>")
		self.create_input(group_script, 4, "Cycle time:", "time", default="30")
		group_script.grid(row=1, column=0, padx=10, pady=10, sticky="WE")

		self.inputs['cycle']['input'].config(state="disabled")
		self.inputs['profile']['input'].config(state="disabled")

		group_output = tk.LabelFrame(self, text="Save output", padx=5, pady=5)
		self.create_input(group_output, 3, "Filename:", "output", default="<click to select>", width=50)
		group_output.grid(row=2, column=0, padx=10, pady=10, sticky="WE")

		self.inputs['output']['input'].config(state="disabled")
		self.inputs['output']['input'].bind("<Button-1>", self.save_dialog)


		self.btn_start = tk.Button(self)
		self.btn_start["text"] = "Start"
		self.btn_start["command"] =  self.start
		self.btn_start.grid(row=3, columnspan=2, sticky="nswe")

	def script_entered(self):
		sf = ScriptFile(self.inputs['url']['value'].get())
		if not sf.status_ok:
			tkMessageBox.showerror("Error", sf.message)
			return

		self.inputs['url']['value'].set(sf.real_url)
		self.inputs['url']['input'].config(state="disabled")
		self.btn_load.config(state="disabled")

		self.inputs['cycle']['input'].config(state="normal")
		for choice in sf.cycles:
			self.inputs['cycle']['input'].insert(tk.END, choice)

		self.inputs['profile']['value'].set('<default>')
		for choice in sf.profiles:
			self.inputs['profile']['input']['menu'].add_command(label=choice, command=tk._setit(self.inputs['profile']['value'], choice))
		self.inputs['profile']['input'].config(state="normal")


	def save_dialog(self, event):
		tmp = tkFileDialog.asksaveasfilename(title="Save outputs", filetypes = (("JSONline","*.jsonl"),("All files","*.*")), defaultextension=".jsonl")
		if len(tmp) > 0:
			self.inputs['output']['value'].set(tmp)

		if self.inputs['output']['value'].get() == "<click to select>":
			self.inputs['output']['value'].set("")

		self.inputs['output']['input'].config(state="normal")

	def start(self):
		error = False
		cmdline = os.path.join("..", "utilities", "script.py") + " "

		optionals = ('password',)
		for k in ('host', 'port', 'username', 'password', 'url', 'profile', 'output', 'time'):
			v = self.inputs[k]['value'].get()
			if (len(v) == 0 or v == "<click to select>") and k not in optionals:
				error = True
				self.inputs[k]['input'].config(background="#ffd8dd")
			else:
				self.inputs[k]['input'].config(background="white")

			if k == 'host': cmdline += " --host " + v 
			elif k == 'port': cmdline += " --port " + v
			elif k == 'username': cmdline += " --user " + v
			elif k == 'password' and len(v) > 0: cmdline += " --password \"" + v + "\""
			elif k == 'url': cmdline += " --script " + v
			elif k == 'cycle': cmdline += " --cycle " + v 
			elif k == 'profile' and v != "<default>": cmdline += " --profile " + v 
			elif k == 'output': cmdline += " --output \"" + v + "\""
			elif k == 'time': cmdline += " --cycle-time " + v

		# cycles
		cycles = self.inputs['cycle']['input'].curselection()
		if len(cycles) == 0:
			error = True
			self.inputs['cycle']['input'].config(background="#ffd8dd")
		else:
			self.inputs['cycle']['input'].config(background="white")

		for cycle in cycles:
			cmdline += " --cycle " + self.inputs['cycle']['input'].get(cycle)

		#
		if error:
			tkMessageBox.showerror("Error", "Please fill all the mandatory inputs.")
			return

		cmdline += " --ignore-ssh-key"
		#print cmdline

		self.btn_start.config(text='Running')
		self.btn_start.config(state='disabled')
		self.master.withdraw()
		os.system(cmdline)
		self.btn_start.config(text='Start')
		self.btn_start.config(state='active')


root = tk.Tk()
root.lift()
root.attributes("-topmost", True)
root.focus_force()

app = App(master=root)
app.mainloop()
#root.destroy()
