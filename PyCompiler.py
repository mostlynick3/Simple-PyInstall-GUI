import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import tempfile
import requests
import shutil
import threading
import sys

class PyInstallerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple PyInstaller GUI")

        self.py_file_path = tk.StringVar()
        self.excludes = tk.StringVar()
        self.icon_path = tk.StringVar()
        self.use_ubx = tk.BooleanVar()
        self.onefile = tk.BooleanVar()
        self.windowed = tk.BooleanVar()
        self.noconsole = tk.BooleanVar()
        self.output_path = tk.StringVar()
        self.binary_name = tk.StringVar()
        self.additional_args = tk.StringVar()
        self.cleanup = tk.BooleanVar()
        self.hide_console = tk.BooleanVar()

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

    def browse_py_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
        if file_path:
            self.py_file_path.set(file_path)

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
        excludes = self.excludes.get().split(',')
        icon_file = self.icon_path.get()
        output_dir = self.output_path.get()
        binary_name = self.binary_name.get()
        additional_args = self.additional_args.get().split()

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
                if exclude.startswith("--exclude-module="):
                    command.append(exclude)
                elif exclude.startswith("--exclude="):
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
                self.cleanup_files(output_dir, binary_name)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            self.convert_button.config(text="Convert to EXE", state=tk.NORMAL)

    def cleanup_files(self, output_dir, binary_name):
        build_dir = os.path.join(os.path.dirname(self.py_file_path.get()), 'build')
        spec_file = os.path.join(os.path.dirname(self.py_file_path.get()), f"{binary_name}.spec")
        dist_dir = os.path.join(os.path.dirname(self.py_file_path.get()), 'dist')
        exe_file = os.path.join(dist_dir, binary_name + '.exe')

        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
        if os.path.exists(spec_file):
            os.remove(spec_file)
        if os.path.exists(exe_file):
            shutil.move(exe_file, os.path.dirname(self.py_file_path.get()))
        if os.path.exists(dist_dir):
            shutil.rmtree(dist_dir)

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
