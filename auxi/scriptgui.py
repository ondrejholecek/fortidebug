#!/usr/bin/env python2.7

import Tkinter as tk
import tkMessageBox
import tkFileDialog
import os
import re
import xml.etree.ElementTree
import requests

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
			try:
				r = requests.get(self.url)
			except Exception, e:
				self.status_ok = False
				self.message   = "Unable to download script file (%s)" % (str(e),)
				return

			if r.status_code != 200: 
				self.status_ok = False
				self.message   = "Unable to download script file (4)"
				return

			else:
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

	def create_input(self, parent, row, label, name, width=None, show=None, default=None, isselect=False):
		self.inputs[name] = {}

		self.inputs[name]['label'] = tk.Label(parent, text=label, width=10, anchor="e")
		self.inputs[name]['label'].grid(row=row, column=0, sticky="W")

		self.inputs[name]['value'] = tk.StringVar()
		if not isselect:
			if default != None: self.inputs[name]['value'].set(default)
			self.inputs[name]['input'] = tk.Entry(parent, width=width, textvar=self.inputs[name]['value'], show=show)
		else:
			self.inputs[name]['value'].set(default)
			self.inputs[name]['input'] = tk.OptionMenu(parent, self.inputs[name]['value'], default)

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
		self.create_input(group_script, 0, "Script URL:", "url", 50)

		self.btn_load = tk.Button(group_script, text="Load", command=self.script_entered)
		self.btn_load.grid(row=1, column=1, sticky="we")

		self.create_input(group_script, 2, "Cycle name:", "cycle", isselect=True)
		self.create_input(group_script, 3, "Profile:", "profile", isselect=True, default="<default>")
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

		self.inputs['cycle']['value'].set('')
		self.inputs['cycle']['input']['menu'].delete(0, 'end')
		for choice in sf.cycles:
			self.inputs['cycle']['input']['menu'].add_command(label=choice, command=tk._setit(self.inputs['cycle']['value'], choice))
		self.inputs['cycle']['input'].config(state="normal")

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
		cmdline = "..\\utilities\\script.py "

		optionals = ('password',)
		for k in ('host', 'port', 'username', 'password', 'url', 'cycle', 'profile', 'output'):
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

		if error:
			tkMessageBox.showerror("Error", "Please fill all the mandatory inputs.")
			return

		cmdline += " --ignore-ssh-key"

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
