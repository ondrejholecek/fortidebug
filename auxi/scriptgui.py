#!/usr/bin/env python2.7

import Tkinter as tk
import tkMessageBox
import tkFileDialog
import os

class App(tk.Frame):
	def __init__(self, master=None):
		tk.Frame.__init__(self, master)

		self.master = master
		self.inputs = {}

		self.pack()
		self.createWidgets()

		self.winfo_toplevel().title("FortiMonitor ScriptGUI")

	def create_input(self, parent, row, label, name, width=None, show=None, default=None):
		self.inputs[name] = {}

		self.inputs[name]['label'] = tk.Label(parent, text=label)
		self.inputs[name]['label'].grid(row=row, column=0, sticky="W")

		self.inputs[name]['value'] = tk.StringVar()
		if default != None: self.inputs[name]['value'].set(default)
		self.inputs[name]['input'] = tk.Entry(parent, width=width, textvar=self.inputs[name]['value'], show=show)
		self.inputs[name]['input'].grid(row=row, column=1)

	def createWidgets(self):

		# Widget group - FortiGate connection settings
		group_fgt = tk.LabelFrame(self, text="FortiGate", padx=5, pady=5)
		self.create_input(group_fgt, 0, "Host:", "host", 50)
		self.create_input(group_fgt, 1, "Usernane:", "username", 50)
		self.create_input(group_fgt, 2, "Password:", "password", 50, show="*")
		group_fgt.grid(row=0, column=0, padx=10, pady=10)

		# Widget group - Script parameters
		group_script = tk.LabelFrame(self, text="Script options", padx=5, pady=5)
		self.create_input(group_script, 0, "Script URL:", "url", 50)
		self.create_input(group_script, 1, "Cycle name:", "cycle", 50)
		self.create_input(group_script, 2, "Profile:", "profile", 50, default="default")
		self.create_input(group_script, 3, "Save output:", "output", 50)
		group_script.grid(row=1, column=0, padx=10, pady=10)

		self.inputs['output']['input'].bind("<Button-1>", self.save_dialog)


		self.btn_start = tk.Button(self)
		self.btn_start["text"] = "Start"
		self.btn_start["command"] =  self.start
		self.btn_start.grid(row=2, columnspan=2, sticky="nswe")

	def save_dialog(self, event):
		tmp = tkFileDialog.asksaveasfilename(title="Save outputs", filetypes = (("JSONline","*.jsonl"),("All files","*.*")), defaultextension=".jsonl")
		if len(tmp) > 0:
			self.inputs['output']['value'].set(tmp)

	def start(self):
		error = False
		cmdline = "c:\\python27\\python.exe c:\\fortimonitor\\utilities\\script.py "

		optionals = ('password',)
		for k in ('host', 'username', 'password', 'url', 'cycle', 'profile', 'output'):
			v = self.inputs[k]['value'].get()
			if len(v) == 0 and k not in optionals:
				error = True
				self.inputs[k]['input'].config(background="#ffd8dd")
			else:
				self.inputs[k]['input'].config(background="white")

			if k == 'host': cmdline += " --host " + v 
			elif k == 'username': cmdline += " --user " + v
			elif k == 'password' and len(v) > 0: cmdline += " --password " + v
			elif k == 'url': cmdline += " --script " + v
			elif k == 'cycle': cmdline += " --cycle " + v 
			elif k == 'profile' and v != "default": cmdline += " --profile " + v 
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
