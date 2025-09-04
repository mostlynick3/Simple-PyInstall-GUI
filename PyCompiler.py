import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import tempfile
import requests
import shutil
import threading
import sys
import ast
import glob
import socket

class PyInstallerGUI:
   def __init__(self, root):
       self.root = root
       self.root.title("Simple PyInstaller GUI")

       self.py_file_path = tk.StringVar()
       self.excludes = tk.StringVar()
       self.icon_path = tk.StringVar()
       self.use_ubx = tk.BooleanVar()
       self.onefile = tk.BooleanVar(value=True)
       self.windowed = tk.BooleanVar(value=True)
       self.noconsole = tk.BooleanVar()
       self.output_path = tk.StringVar()
       self.binary_name = tk.StringVar()
       self.additional_args = tk.StringVar()
       self.cleanup = tk.BooleanVar(value=True)
       self.hide_console = tk.BooleanVar()

       self.py_file_path.trace('w', self.update_paths)

       self.check_internet_and_set_upx()
       self.create_widgets()

   def create_widgets(self):
       tk.Label(self.root, text="Select Python File:").pack(anchor='w')
       tk.Entry(self.root, textvariable=self.py_file_path, width=50).pack(anchor='w')
       tk.Button(self.root, text="Browse", command=self.browse_py_file).pack(anchor='w')

       tk.Label(self.root, text="Excludes (comma-separated):").pack(anchor='w')
       tk.Entry(self.root, textvariable=self.excludes, width=50).pack(anchor='w')
       tk.Button(self.root, text="Default Excludes", command=self.set_default_excludes).pack(anchor='w')

       tk.Label(self.root, text="Select Icon File (optional):").pack(anchor='w')
       tk.Entry(self.root, textvariable=self.icon_path, width=50).pack(anchor='w')
       tk.Button(self.root, text="Browse", command=self.browse_icon_file).pack(anchor='w')

       tk.Label(self.root, text="Binary Name:").pack(anchor='w')
       tk.Entry(self.root, textvariable=self.binary_name, width=50).pack(anchor='w')

       tk.Label(self.root, text="Additional Arguments:").pack(anchor='w')
       tk.Entry(self.root, textvariable=self.additional_args, width=50).pack(anchor='w')

       tk.Checkbutton(self.root, text="Use UPX Compression (Requires Network Connection)", variable=self.use_ubx).pack(anchor='w')
       tk.Checkbutton(self.root, text="Onefile", variable=self.onefile).pack(anchor='w')
       tk.Checkbutton(self.root, text="Windowed", variable=self.windowed).pack(anchor='w')
       tk.Checkbutton(self.root, text="No Console", variable=self.noconsole).pack(anchor='w')
       tk.Checkbutton(self.root, text="Clean Up After Completion", variable=self.cleanup).pack(anchor='w')
       tk.Checkbutton(self.root, text="Hide Compilation Console Window", variable=self.hide_console).pack(anchor='w')

       tk.Label(self.root, text="Output Path:").pack(anchor='w')
       tk.Entry(self.root, textvariable=self.output_path, width=50).pack(anchor='w')
       tk.Button(self.root, text="Browse", command=self.browse_output_path).pack(anchor='w')

       self.convert_button = tk.Button(self.root, text="Convert to EXE", command=self.start_conversion)
       self.convert_button.pack()

   def check_internet_and_set_upx(self):
       try:
           socket.create_connection(("8.8.8.8", 53), timeout=3)
           self.use_ubx.set(True)
       except OSError:
           self.use_ubx.set(False)

   def browse_py_file(self):
       file_path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
       if file_path:
           self.py_file_path.set(file_path)

   def get_imports_from_file(self, file_path):
       imports = set()
       try:
           with open(file_path, 'r', encoding='utf-8') as f:
               content = f.read()
           
           tree = ast.parse(content)
           for node in ast.walk(tree):
               if isinstance(node, ast.Import):
                   for alias in node.names:
                       imports.add(alias.name.split('.')[0])
               elif isinstance(node, ast.ImportFrom):
                   if node.module:
                       imports.add(node.module.split('.')[0])
       except:
           pass
       return imports

   def find_icon_file(self, py_file_dir, binary_name):
       ico_files = glob.glob(os.path.join(py_file_dir, "*.ico"))
       
       if not ico_files:
           return None
       
       icon_ico = os.path.join(py_file_dir, "icon.ico")
       if icon_ico in ico_files:
           return icon_ico
       
       binary_ico = os.path.join(py_file_dir, f"{binary_name}.ico")
       if binary_ico in ico_files:
           return binary_ico
       
       ico_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
       return ico_files[0]

   def update_paths(self, *args):
       py_file = self.py_file_path.get()
       if py_file:
           filename = os.path.basename(py_file)
           if filename.endswith('.py'):
               binary_name = filename[:-3]
               self.binary_name.set(binary_name)
           
           py_file_dir = os.path.dirname(py_file)
           self.output_path.set(py_file_dir)
           
           icon_file = self.find_icon_file(py_file_dir, binary_name)
           if icon_file:
               self.icon_path.set(icon_file)
           
           self.set_smart_excludes(py_file)

   def set_smart_excludes(self, py_file):
       default_exclude_modules = {'cv2', 'numpy', 'PIL'}
       default_exclude_files = {'libcrypto-3.dll'}
       
       imports = self.get_imports_from_file(py_file)
       
       exclude_list = []
       
       for module in default_exclude_modules:
           if module not in imports:
               exclude_list.append(f"--exclude-module={module}")
       
       for file in default_exclude_files:
           exclude_list.append(f"--exclude={file}")
       
       self.excludes.set(','.join(exclude_list))

   def browse_icon_file(self):
       file_path = filedialog.askopenfilename(filetypes=[("Icon Files", "*.ico")])
       if file_path:
           self.icon_path.set(file_path)

   def browse_output_path(self):
       dir_path = filedialog.askdirectory()
       if dir_path:
           self.output_path.set(dir_path)

   def set_default_excludes(self):
       default_excludes = "--exclude-module=cv2,--exclude-module=numpy,--exclude-module=PIL,--exclude=libcrypto-3.dll"
       self.excludes.set(default_excludes)

   def start_conversion(self):
       self.convert_button.config(text="Compiling EXE...", state=tk.DISABLED)
       threading.Thread(target=self.convert_to_exe).start()

   def convert_to_exe(self):
       py_file = self.py_file_path.get()
       excludes = self.excludes.get().split(',') if self.excludes.get() else []
       icon_file = self.icon_path.get()
       output_dir = self.output_path.get() if self.output_path.get() else os.path.dirname(py_file)
       binary_name = self.binary_name.get()
       additional_args = self.additional_args.get().split() if self.additional_args.get() else []

       command = ["pyinstaller"]

       if self.use_ubx.get():
           ubx_dir = self.download_ubx()
           if ubx_dir:
               command.extend(["--upx-dir", ubx_dir])

       if self.onefile.get():
           command.append("--onefile")

       if self.windowed.get():
           command.append("--windowed")

       if self.noconsole.get():
           command.append("--noconsole")

       if icon_file:
           command.extend(["--icon", icon_file])

       if excludes:
           for exclude in excludes:
               exclude = exclude.strip()
               if exclude.startswith("--exclude-module=") or exclude.startswith("--exclude="):
                   command.append(exclude)

       if binary_name:
           command.extend(["--name", binary_name])

       if additional_args:
           command.extend(additional_args)

       command.extend(["--distpath", output_dir, py_file])

       try:
           if self.hide_console.get() and sys.platform == "win32":
               subprocess.run(command, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
           else:
               subprocess.run(command, check=True)
           messagebox.showinfo("Success", "Conversion to EXE completed successfully!")

           if self.cleanup.get():
               self.cleanup_files(binary_name)
       except subprocess.CalledProcessError as e:
           messagebox.showerror("Error", f"An error occurred: {e}")
       finally:
           self.convert_button.config(text="Convert to EXE", state=tk.NORMAL)

   def cleanup_files(self, binary_name):
       try:
           current_dir = os.getcwd()
           
           build_dir = os.path.join(current_dir, 'build')
           spec_file = os.path.join(current_dir, f"{binary_name}.spec")
           
           if os.path.exists(build_dir):
               shutil.rmtree(build_dir)
           
           if os.path.exists(spec_file):
               os.remove(spec_file)
                   
       except Exception as e:
           print(f"Cleanup warning: {e}")

   def download_ubx(self):
       temp_dir = tempfile.mkdtemp()
       ubx_url = "https://github.com/upx/upx/releases/download/v5.0.0/upx-5.0.0-win64.zip"
       ubx_zip = os.path.join(temp_dir, "upx.zip")
       ubx_dir = os.path.join(temp_dir, "upx")

       response = requests.get(ubx_url)
       with open(ubx_zip, "wb") as file:
           file.write(response.content)

       import zipfile
       with zipfile.ZipFile(ubx_zip, 'r') as zip_ref:
           zip_ref.extractall(ubx_dir)

       return ubx_dir

if __name__ == "__main__":
   root = tk.Tk()
   app = PyInstallerGUI(root)
   root.mainloop()
