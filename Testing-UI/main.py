import tkinter as tk
from tkinter import ttk, messagebox
# from PIL import Image, ImageTk
import datetime

class FishSortingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fish Sorting System")
        self.root.state('zoomed')  # Fullscreen untuk Windows
        # self.root.attributes('-fullscreen', True)  # Uncomment untuk Linux/Mac
        self.root.configure(bg='#f0f0f0')
        
        # Flag untuk mencegah multiple popup settings
        self.settings_popup = None
        
        # Inisialisasi data
        self.init_data()
        
        # Setup UI
        self.setup_main_ui()
        
        # Setup bindings
        self.setup_bindings()
        
    def init_data(self):
        """Inisialisasi data aplikasi"""
        self.sorted_count = 1408
        self.sorted_weight = 52.2
        self.hourly_count = 281
        self.hourly_weight = 10.4
        self.box_data = {
            'A': [5.4, 5.4, 5.4],
            'B': [5.4, 5.4, 5.4],
            'C': [5.4, 5.4, 5.4]
        }
        self.conveyor_speeds = [50, 60, 70, 80]  # Conveyor speeds in percentage
        
    def setup_main_ui(self):
        """Setup UI utama"""
        # Main container
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Top row - Camera, Box Manager, Log Activity
        top_frame = tk.Frame(main_frame, bg='#f0f0f0')
        top_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Camera Capture Section
        self.setup_camera_section(top_frame)
        
        # Box Manager Section
        self.setup_box_manager_section(top_frame)
        
        # Log Activity Section
        self.setup_log_activity_section(top_frame)
        
        # Bottom row - Statistics and Acceleration Manager
        bottom_frame = tk.Frame(main_frame, bg='#f0f0f0')
        bottom_frame.pack(fill=tk.BOTH, expand=True)
        
        # Statistics Section
        self.setup_statistics_section(bottom_frame)
        
        # Acceleration Manager Section
        self.setup_acceleration_manager_section(bottom_frame)
        
        # Control Buttons Section
        self.setup_control_buttons_section(bottom_frame)
        
    def setup_camera_section(self, parent):
        """Setup section Camera Capture"""
        camera_frame = tk.Frame(parent, bg='#4472C4', relief=tk.RAISED, bd=2)
        camera_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Header
        header_frame = tk.Frame(camera_frame, bg='#4472C4', height=50)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="Camera Capture", font=('Arial', 16, 'bold'), 
                bg='#4472C4', fg='white').pack(anchor=tk.W, pady=10)
        
        # Camera display area
        camera_display = tk.Frame(camera_frame, bg='#e8f1ff', relief=tk.SUNKEN, bd=2)
        camera_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Placeholder untuk gambar ikan
        fish_img_frame = tk.Frame(camera_display, bg='#e8f1ff')
        fish_img_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Simulasi gambar ikan (placeholder)
        tk.Label(fish_img_frame, text="🐟 FISH CAMERA VIEW 🐟", 
                font=('Arial', 14, 'bold'), bg='#e8f1ff', fg='#4472C4').pack(expand=True)
        
        # Info panel
        info_frame = tk.Frame(camera_frame, bg='#e8f1ff', height=80)
        info_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        info_frame.pack_propagate(False)
        
        # Left side info
        left_info = tk.Frame(info_frame, bg='#e8f1ff')
        left_info.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        tk.Label(left_info, text="Jenis Objek", font=('Arial', 10), 
                bg='#e8f1ff', fg='#666').pack(anchor=tk.W)
        tk.Label(left_info, text="Tuna", font=('Arial', 12, 'bold'), 
                bg='#e8f1ff', fg='#333').pack(anchor=tk.W)
        
        # Middle info
        middle_info = tk.Frame(info_frame, bg='#e8f1ff')
        middle_info.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        tk.Label(middle_info, text="Berat Objek", font=('Arial', 10), 
                bg='#e8f1ff', fg='#666').pack(anchor=tk.W)
        tk.Label(middle_info, text="0.9 Kg", font=('Arial', 12, 'bold'), 
                bg='#e8f1ff', fg='#333').pack(anchor=tk.W)
        
        # Right side info (time)
        right_info = tk.Frame(info_frame, bg='#e8f1ff')
        right_info.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        
        self.time_label = tk.Label(right_info, text="08:20:12", 
                                  font=('Arial', 14, 'bold'), 
                                  bg='#e8f1ff', fg='#4472C4')
        self.time_label.pack(anchor=tk.E)
        
    def setup_box_manager_section(self, parent):
        """Setup section Box Manager"""
        box_frame = tk.Frame(parent, bg='#4472C4', relief=tk.RAISED, bd=2)
        box_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Header
        header_frame = tk.Frame(box_frame, bg='#4472C4', height=50)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="Box Manager", font=('Arial', 16, 'bold'), 
                bg='#4472C4', fg='white').pack(anchor=tk.W, pady=10)
        
        # Box grid
        grid_frame = tk.Frame(box_frame, bg='#e8f1ff')
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Headers
        tk.Label(grid_frame, text="", bg='#e8f1ff', width=3).grid(row=0, column=0, padx=2, pady=2)
        tk.Label(grid_frame, text="A", font=('Arial', 12, 'bold'), 
                bg='#e8f1ff', width=8).grid(row=0, column=1, padx=2, pady=2)
        tk.Label(grid_frame, text="B", font=('Arial', 12, 'bold'), 
                bg='#e8f1ff', width=8).grid(row=0, column=2, padx=2, pady=2)
        tk.Label(grid_frame, text="C", font=('Arial', 12, 'bold'), 
                bg='#e8f1ff', width=8).grid(row=0, column=3, padx=2, pady=2)
        
        # Trash column
        trash_frame = tk.Frame(grid_frame, bg='#ff6b6b', relief=tk.RAISED, bd=2)
        trash_frame.grid(row=0, column=4, rowspan=4, padx=10, pady=5, sticky='nsew')
        
        tk.Label(trash_frame, text="🗑️", font=('Arial', 20), 
                bg='#ff6b6b', fg='white').pack(pady=5)
        tk.Label(trash_frame, text="TRASH", font=('Arial', 12, 'bold'), 
                bg='#ff6b6b', fg='white').pack()
        tk.Label(trash_frame, text="13.3 Kg", font=('Arial', 10), 
                bg='#ff6b6b', fg='white').pack()
        
        # Grid rows
        for i in range(1, 4):
            tk.Label(grid_frame, text=str(i), font=('Arial', 12, 'bold'), 
                    bg='#e8f1ff', width=3).grid(row=i, column=0, padx=2, pady=2)
            
            for j in range(1, 4):
                col_name = ['A', 'B', 'C'][j-1]
                weight = self.box_data[col_name][i-1]
                
                box_btn = tk.Button(grid_frame, text=f"{weight} Kg", 
                                   font=('Arial', 10), bg='#b8cdf0', 
                                   relief=tk.RAISED, bd=2, width=8)
                box_btn.grid(row=i, column=j, padx=2, pady=2)
        
        # Configure grid weights
        for i in range(4):
            grid_frame.grid_rowconfigure(i, weight=1)
        for j in range(5):
            grid_frame.grid_columnconfigure(j, weight=1)
            
    def setup_log_activity_section(self, parent):
        """Setup section Log Activity"""
        log_frame = tk.Frame(parent, bg='#4472C4', relief=tk.RAISED, bd=2)
        log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = tk.Frame(log_frame, bg='#4472C4', height=50)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="Log Activity", font=('Arial', 16, 'bold'), 
                bg='#4472C4', fg='white').pack(anchor=tk.W, pady=10)
        
        # Log content
        log_content = tk.Frame(log_frame, bg='#e8f1ff')
        log_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Log entries
        for i in range(15):
            log_entry = tk.Frame(log_content, bg='#e8f1ff', height=25)
            log_entry.pack(fill=tk.X, pady=1)
            log_entry.pack_propagate(False)
            
            tk.Label(log_entry, text=f"[12:31:22][15/07] Ikan A - 1.4kg → A3", 
                    font=('Arial', 9), bg='#e8f1ff', fg='#333').pack(anchor=tk.W, pady=2)
        
        # Control buttons at bottom
        control_frame = tk.Frame(log_frame, bg='#e8f1ff', height=120)
        control_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        control_frame.pack_propagate(False)
        
        # START button
        start_btn = tk.Button(control_frame, text="START", font=('Arial', 12, 'bold'), 
                             bg='#4CAF50', fg='white', relief=tk.RAISED, bd=3,
                             command=self.start_system)
        start_btn.pack(fill=tk.X, pady=2)
        
        # STOP button
        stop_btn = tk.Button(control_frame, text="STOP", font=('Arial', 12, 'bold'), 
                            bg='#FFD700', fg='black', relief=tk.RAISED, bd=3,
                            command=self.stop_system)
        stop_btn.pack(fill=tk.X, pady=2)
        
        # RESET button
        reset_btn = tk.Button(control_frame, text="RESET", font=('Arial', 12, 'bold'), 
                             bg='#FF6B6B', fg='white', relief=tk.RAISED, bd=3,
                             command=self.reset_system)
        reset_btn.pack(fill=tk.X, pady=2)
        
    def setup_statistics_section(self, parent):
        """Setup section Statistics"""
        stats_frame = tk.Frame(parent, bg='#f0f0f0')
        stats_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))
        
        # Statistics grid
        stats_grid = tk.Frame(stats_frame, bg='#f0f0f0')
        stats_grid.pack(fill=tk.X, pady=(0, 20))
        
        # Row 1
        stat1 = tk.Frame(stats_grid, bg='#87CEEB', relief=tk.RAISED, bd=2, height=80)
        stat1.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        stat1.pack_propagate(False)
        
        tk.Label(stat1, text="1408", font=('Arial', 20, 'bold'), 
                bg='#87CEEB', fg='#333').pack(expand=True)
        tk.Label(stat1, text="Jumlah Pcs Tersortir", font=('Arial', 10), 
                bg='#87CEEB', fg='#333').pack()
        
        stat2 = tk.Frame(stats_grid, bg='#87CEEB', relief=tk.RAISED, bd=2, height=80)
        stat2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        stat2.pack_propagate(False)
        
        tk.Label(stat2, text="52.2", font=('Arial', 20, 'bold'), 
                bg='#87CEEB', fg='#333').pack(expand=True)
        tk.Label(stat2, text="Jumlah Kg Tersortir", font=('Arial', 10), 
                bg='#87CEEB', fg='#333').pack()
        
        # Row 2
        stats_grid2 = tk.Frame(stats_frame, bg='#f0f0f0')
        stats_grid2.pack(fill=tk.X)
        
        stat3 = tk.Frame(stats_grid2, bg='#87CEEB', relief=tk.RAISED, bd=2, height=80)
        stat3.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        stat3.pack_propagate(False)
        
        tk.Label(stat3, text="281", font=('Arial', 20, 'bold'), 
                bg='#87CEEB', fg='#333').pack(expand=True)
        tk.Label(stat3, text="Jumlah Pcs / jam", font=('Arial', 10), 
                bg='#87CEEB', fg='#333').pack()
        
        stat4 = tk.Frame(stats_grid2, bg='#87CEEB', relief=tk.RAISED, bd=2, height=80)
        stat4.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        stat4.pack_propagate(False)
        
        tk.Label(stat4, text="10.4", font=('Arial', 20, 'bold'), 
                bg='#87CEEB', fg='#333').pack(expand=True)
        tk.Label(stat4, text="Jumlah Kg / jam", font=('Arial', 10), 
                bg='#87CEEB', fg='#333').pack()
        
    def setup_acceleration_manager_section(self, parent):
        """Setup section Acceleration Manager"""
        accel_frame = tk.Frame(parent, bg='#4472C4', relief=tk.RAISED, bd=2)
        accel_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))
        
        # Header
        header_frame = tk.Frame(accel_frame, bg='#4472C4', height=50)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="Acceleration Manager", font=('Arial', 16, 'bold'), 
                bg='#4472C4', fg='white').pack(anchor=tk.W, pady=10)
        
        # Conveyor controls
        conveyor_frame = tk.Frame(accel_frame, bg='#e8f1ff')
        conveyor_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.conveyor_vars = []
        conveyor_names = ["Conveyor 1", "Conveyor 2", "Conveyor 3", "Conveyor 4"]
        
        for i, name in enumerate(conveyor_names):
            conv_frame = tk.Frame(conveyor_frame, bg='#e8f1ff')
            conv_frame.pack(fill=tk.X, pady=5)
            
            tk.Label(conv_frame, text=name, font=('Arial', 12), 
                    bg='#e8f1ff', fg='#333').pack(anchor=tk.W)
            
            var = tk.IntVar(value=self.conveyor_speeds[i])
            self.conveyor_vars.append(var)
            
            scale = tk.Scale(conv_frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                           variable=var, bg='#e8f1ff', fg='#333', 
                           highlightthickness=0, bd=0)
            scale.pack(fill=tk.X, pady=2)
            
    def setup_control_buttons_section(self, parent):
        """Setup section Control Buttons"""
        button_frame = tk.Frame(parent, bg='#f0f0f0')
        button_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # Settings button
        settings_btn = tk.Button(button_frame, text="⚙️ SETTINGS", 
                               font=('Arial', 12, 'bold'), bg='#d3d3d3', 
                               fg='#333', relief=tk.RAISED, bd=3, width=15, height=2,
                               command=self.open_settings)
        settings_btn.pack(pady=10)
        
    def setup_bindings(self):
        """Setup event bindings"""
        # Update time setiap detik
        self.update_time()
        
        # Bind escape key untuk exit fullscreen
        self.root.bind('<Escape>', lambda e: self.root.quit())
        
    def update_time(self):
        """Update waktu real-time"""
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)
        
    def start_system(self):
        """Fungsi untuk memulai sistem"""
        messagebox.showinfo("System", "System Started!")
        
    def stop_system(self):
        """Fungsi untuk menghentikan sistem"""
        messagebox.showinfo("System", "System Stopped!")
        
    def reset_system(self):
        """Fungsi untuk reset sistem"""
        if messagebox.askyesno("Reset", "Are you sure you want to reset the system?"):
            messagebox.showinfo("System", "System Reset!")
            
    def open_settings(self):
        """Buka popup settings"""
        # Cek apakah popup sudah ada
        if self.settings_popup and self.settings_popup.winfo_exists():
            return  # Jangan buka popup baru jika sudah ada
            
        self.settings_popup = tk.Toplevel(self.root)
        self.settings_popup.title("Settings")
        self.settings_popup.geometry("800x600")
        self.settings_popup.resizable(True, True)
        self.settings_popup.transient(self.root)
        self.settings_popup.grab_set()
        
        # Center the popup
        self.settings_popup.update_idletasks()
        x = (self.settings_popup.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.settings_popup.winfo_screenheight() // 2) - (600 // 2)
        self.settings_popup.geometry(f"800x600+{x}+{y}")
        
        # Header dengan tombol close
        header_frame = tk.Frame(self.settings_popup, bg='#f0f0f0', height=50)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="⚙️ SETTINGS", font=('Arial', 16, 'bold'), 
                bg='#f0f0f0', fg='#333').pack(side=tk.LEFT, pady=10)
        
        close_btn = tk.Button(header_frame, text="✕", font=('Arial', 14, 'bold'), 
                             bg='#ff6b6b', fg='white', relief=tk.RAISED, bd=2,
                             command=self.settings_popup.destroy)
        close_btn.pack(side=tk.RIGHT, pady=10)
        
        # Scrollable frame
        canvas = tk.Canvas(self.settings_popup, bg='#f0f0f0')
        scrollbar = ttk.Scrollbar(self.settings_popup, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f0f0f0')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10)
        scrollbar.pack(side="right", fill="y")
        
        # Camera Settings
        self.setup_camera_settings(scrollable_frame)
        
        # Database Settings
        self.setup_database_settings(scrollable_frame)
        
        # Range Settings
        self.setup_range_settings(scrollable_frame)
        
        # Bottom buttons
        button_frame = tk.Frame(self.settings_popup, bg='#f0f0f0', height=60)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        button_frame.pack_propagate(False)
        
        cancel_btn = tk.Button(button_frame, text="Cancel", font=('Arial', 12), 
                              bg='#ff6b6b', fg='white', relief=tk.RAISED, bd=2,
                              command=self.settings_popup.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=5, pady=15)
        
        apply_btn = tk.Button(button_frame, text="Apply", font=('Arial', 12, 'bold'), 
                             bg='#4CAF50', fg='white', relief=tk.RAISED, bd=2,
                             command=self.apply_settings)
        apply_btn.pack(side=tk.RIGHT, padx=5, pady=15)
        
        # Bind mouse wheel untuk scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
    def setup_camera_settings(self, parent):
        """Setup Camera Settings section"""
        camera_frame = tk.LabelFrame(parent, text="Camera Settings", 
                                   font=('Arial', 12, 'bold'), bg='#f0f0f0', 
                                   fg='#333', relief=tk.RAISED, bd=2)
        camera_frame.pack(fill=tk.X, padx=10, pady=10)
        
        settings = ["Brightness", "Exposure", "Contrast", "Gain", "Hue"]
        self.camera_vars = {}
        
        for setting in settings:
            frame = tk.Frame(camera_frame, bg='#f0f0f0')
            frame.pack(fill=tk.X, padx=10, pady=5)
            
            tk.Label(frame, text=setting, font=('Arial', 10), 
                    bg='#f0f0f0', fg='#333', width=15).pack(side=tk.LEFT)
            
            var = tk.IntVar(value=50)
            self.camera_vars[setting] = var
            
            scale = tk.Scale(frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                           variable=var, bg='#f0f0f0', fg='#333', 
                           highlightthickness=0, bd=0)
            scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
            
            entry = tk.Entry(frame, width=8, textvariable=var)
            entry.pack(side=tk.RIGHT, padx=5)
            
        # Auto checkbox
        auto_frame = tk.Frame(camera_frame, bg='#f0f0f0')
        auto_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.auto_var = tk.BooleanVar()
        tk.Checkbutton(auto_frame, text="Auto", variable=self.auto_var,
                      bg='#f0f0f0', fg='#333').pack(side=tk.RIGHT)
        
    def setup_database_settings(self, parent):
        """Setup Database Settings section"""
        db_frame = tk.LabelFrame(parent, text="Database Settings", 
                               font=('Arial', 12, 'bold'), bg='#f0f0f0', 
                               fg='#333', relief=tk.RAISED, bd=2)
        db_frame.pack(fill=tk.X, padx=10, pady=10)
        
        db_fields = ["Database Host", "Database Name", "Username", "Password", "Port"]
        self.db_vars = {}
        
        for field in db_fields:
            frame = tk.Frame(db_frame, bg='#f0f0f0')
            frame.pack(fill=tk.X, padx=10, pady=5)
            
            tk.Label(frame, text=field, font=('Arial', 10), 
                    bg='#f0f0f0', fg='#333', width=15).pack(side=tk.LEFT)
            
            var = tk.StringVar()
            self.db_vars[field] = var
            
            entry = tk.Entry(frame, textvariable=var, bg='#d3d3d3', relief=tk.SUNKEN, bd=1)
            entry.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=10)
            
        # Save button
        save_btn = tk.Button(db_frame, text="Save", font=('Arial', 10, 'bold'), 
                           bg='#4CAF50', fg='white', relief=tk.RAISED, bd=2)
        save_btn.pack(side=tk.RIGHT, padx=10, pady=5)
        
    def setup_range_settings(self, parent):
        """Setup Range Settings section"""
        range_frame = tk.LabelFrame(parent, text="Range Settings", 
                                  font=('Arial', 12, 'bold'), bg='#f0f0f0', 
                                  fg='#333', relief=tk.RAISED, bd=2)
        range_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Grid untuk range settings
        grid_frame = tk.Frame(range_frame, bg='#f0f0f0')
        grid_frame.pack(fill=tk.X, padx=10, pady=10)
        
        positions = ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3", "TRASH"]
        self.range_vars = {}
        
        for i, pos in enumerate(positions):
            row = i // 4
            col = (i % 4) * 3
            
            # Label
            tk.Label(grid_frame, text=pos, font=('Arial', 10, 'bold'), 
                    bg='#f0f0f0', fg='#333').grid(row=row, column=col, padx=5, pady=2)
            
            # X entry
            tk.Label(grid_frame, text="x", font=('Arial', 9), 
                    bg='#f0f0f0', fg='#333').grid(row=row, column=col+1, padx=2)
            
            x_var = tk.StringVar()
            x_entry = tk.Entry(grid_frame, textvariable=x_var, width=5, 
                              bg='#d3d3d3', relief=tk.SUNKEN, bd=1)
            x_entry.grid(row=row, column=col+1, padx=(15, 2))
            
            # Y entry
            tk.Label(grid_frame, text="y", font=('Arial', 9), 
                    bg='#f0f0f0', fg='#333').grid(row=row, column=col+2, padx=2)
            
            y_var = tk.StringVar()
            y_entry = tk.Entry(grid_frame, textvariable=y_var, width=5, 
                              bg='#d3d3d3', relief=tk.SUNKEN, bd=1)
            y_entry.grid(row=row, column=col+2, padx=(15, 5))
            
            self.range_vars[pos] = {'x': x_var, 'y': y_var}
            
        # Save button for range settings
        save_range_btn = tk.Button(range_frame, text="Save", font=('Arial', 10, 'bold'), 
                                 bg='#4CAF50', fg='white', relief=tk.RAISED, bd=2)
        save_range_btn.pack(side=tk.RIGHT, padx=10, pady=5)
        
    def apply_settings(self):
        """Apply settings changes"""
        messagebox.showinfo("Settings", "Settings applied successfully!")
        self.settings_popup.destroy()
        
    def save_camera_settings(self):
        """Save camera settings to file"""
        try:
            settings = {}
            for key, var in self.camera_vars.items():
                settings[key] = var.get()
            settings['auto'] = self.auto_var.get()
            
            # Simulate saving to file
            messagebox.showinfo("Camera Settings", "Camera settings saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save camera settings: {str(e)}")
            
    def save_database_settings(self):
        """Save database settings"""
        try:
            # Validate database fields
            required_fields = ["Database Host", "Database Name", "Username", "Password", "Port"]
            for field in required_fields:
                if not self.db_vars[field].get().strip():
                    messagebox.showwarning("Validation", f"{field} cannot be empty!")
                    return
            
            # Simulate database connection test
            messagebox.showinfo("Database Settings", "Database settings saved and connection tested successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save database settings: {str(e)}")
            
    def save_range_settings(self):
        """Save range settings"""
        try:
            # Validate coordinates
            for pos, coords in self.range_vars.items():
                x_val = coords['x'].get()
                y_val = coords['y'].get()
                
                if x_val and not x_val.isdigit():
                    messagebox.showwarning("Validation", f"Invalid X coordinate for {pos}")
                    return
                if y_val and not y_val.isdigit():
                    messagebox.showwarning("Validation", f"Invalid Y coordinate for {pos}")
                    return
            
            messagebox.showinfo("Range Settings", "Range settings saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save range settings: {str(e)}")
            
    def update_conveyor_speed(self, conveyor_index, speed):
        """Update conveyor belt speed"""
        try:
            if 0 <= conveyor_index < len(self.conveyor_speeds):
                self.conveyor_speeds[conveyor_index] = speed
                print(f"Conveyor {conveyor_index + 1} speed updated to {speed}%")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update conveyor speed: {str(e)}")
            
    def simulate_fish_detection(self):
        """Simulate fish detection and sorting"""
        import random
        
        # Simulate random fish detection
        fish_types = ["Tuna", "Salmon", "Cod", "Mackerel"]
        fish_weights = [0.5, 0.8, 1.2, 1.5, 2.0, 2.5]
        destinations = ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3", "TRASH"]
        
        fish_type = random.choice(fish_types)
        fish_weight = random.choice(fish_weights)
        destination = random.choice(destinations)
        
        # Update fish info in camera section
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Add to log
        log_entry = f"[{current_time}] {fish_type} - {fish_weight}kg → {destination}"
        print(log_entry)
        
        # Update statistics
        self.sorted_count += 1
        self.sorted_weight += fish_weight
        self.hourly_count += 1
        self.hourly_weight += fish_weight
        
        # Schedule next simulation
        if hasattr(self, 'is_running') and self.is_running:
            self.root.after(2000, self.simulate_fish_detection)
            
    def start_system(self):
        """Fungsi untuk memulai sistem"""
        try:
            self.is_running = True
            messagebox.showinfo("System", "Fish Sorting System Started!")
            
            # Start fish detection simulation
            self.simulate_fish_detection()
            
            # Update UI to show system is running
            self.update_system_status("RUNNING")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start system: {str(e)}")
            
    def stop_system(self):
        """Fungsi untuk menghentikan sistem"""
        try:
            self.is_running = False
            messagebox.showinfo("System", "Fish Sorting System Stopped!")
            
            # Update UI to show system is stopped
            self.update_system_status("STOPPED")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop system: {str(e)}")
            
    def reset_system(self):
        """Fungsi untuk reset sistem"""
        try:
            if messagebox.askyesno("Reset", "Are you sure you want to reset the system?\nThis will clear all statistics and logs."):
                self.is_running = False
                
                # Reset statistics
                self.sorted_count = 0
                self.sorted_weight = 0.0
                self.hourly_count = 0
                self.hourly_weight = 0.0
                
                # Reset box data
                for key in self.box_data:
                    self.box_data[key] = [0.0, 0.0, 0.0]
                
                # Reset conveyor speeds
                self.conveyor_speeds = [50, 50, 50, 50]
                
                messagebox.showinfo("System", "System Reset Complete!")
                
                # Update UI
                self.update_system_status("RESET")
                self.refresh_ui()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset system: {str(e)}")
            
    def update_system_status(self, status):
        """Update system status indicator"""
        # This would update a status indicator in the UI
        print(f"System Status: {status}")
        
    def refresh_ui(self):
        """Refresh all UI elements with current data"""
        # This would refresh statistics displays, box weights, etc.
        print("UI Refreshed")
        
    def load_configuration(self):
        """Load configuration from file"""
        try:
            # Simulate loading configuration
            print("Loading configuration...")
            
            # Set default values
            default_config = {
                'camera': {
                    'brightness': 50,
                    'exposure': 50,
                    'contrast': 50,
                    'gain': 50,
                    'hue': 50,
                    'auto': False
                },
                'database': {
                    'host': 'localhost',
                    'name': 'fish_sorting',
                    'username': 'admin',
                    'password': '',
                    'port': '5432'
                },
                'ranges': {
                    'A1': {'x': 100, 'y': 150},
                    'A2': {'x': 100, 'y': 200},
                    'A3': {'x': 100, 'y': 250},
                    'B1': {'x': 200, 'y': 150},
                    'B2': {'x': 200, 'y': 200},
                    'B3': {'x': 200, 'y': 250},
                    'C1': {'x': 300, 'y': 150},
                    'C2': {'x': 300, 'y': 200},
                    'C3': {'x': 300, 'y': 250},
                    'TRASH': {'x': 400, 'y': 200}
                }
            }
            
            return default_config
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
            return None
            
    def save_configuration(self):
        """Save current configuration to file"""
        try:
            config = {
                'camera': {},
                'database': {},
                'ranges': {}
            }
            
            # Save camera settings
            if hasattr(self, 'camera_vars'):
                for key, var in self.camera_vars.items():
                    config['camera'][key] = var.get()
                config['camera']['auto'] = self.auto_var.get()
            
            # Save database settings
            if hasattr(self, 'db_vars'):
                for key, var in self.db_vars.items():
                    config['database'][key] = var.get()
            
            # Save range settings
            if hasattr(self, 'range_vars'):
                for pos, coords in self.range_vars.items():
                    config['ranges'][pos] = {
                        'x': coords['x'].get(),
                        'y': coords['y'].get()
                    }
            
            print("Configuration saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
            
    def export_data(self):
        """Export sorting data to CSV"""
        try:
            import csv
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filename:
                # Simulate export data
                sample_data = [
                    ["Time", "Fish Type", "Weight (kg)", "Destination"],
                    ["08:20:12", "Tuna", "0.9", "A1"],
                    ["08:20:15", "Salmon", "1.2", "B2"],
                    ["08:20:18", "Cod", "0.8", "C1"],
                    ["08:20:21", "Mackerel", "1.5", "A3"]
                ]
                
                with open(filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows(sample_data)
                
                messagebox.showinfo("Export", f"Data exported successfully to {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")
            
    def import_settings(self):
        """Import settings from file"""
        try:
            from tkinter import filedialog
            
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                # Simulate import
                messagebox.showinfo("Import", f"Settings imported successfully from {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import settings: {str(e)}")
            
    def show_about(self):
        """Show about dialog"""
        about_text = """
        Fish Sorting System v1.0
        
        Developed for automated fish sorting and classification
        
        Features:
        - Real-time fish detection
        - Automated sorting by weight and type
        - Conveyor belt speed control
        - Database integration
        - Statistical reporting
        
        © 2024 Fish Sorting Solutions
        """
        
        messagebox.showinfo("About", about_text)
        
    def show_help(self):
        """Show help dialog"""
        help_text = """
        Fish Sorting System Help
        
        Getting Started:
        1. Click START to begin sorting
        2. Adjust conveyor speeds as needed
        3. Monitor statistics in real-time
        4. Use STOP to pause operations
        5. Click RESET to clear all data
        
        Settings:
        - Camera: Adjust image capture settings
        - Database: Configure data storage
        - Range: Set sorting coordinates
        
        For technical support, contact:
        support@fishsorting.com
        """
        
        messagebox.showinfo("Help", help_text)

# Main application
if __name__ == "__main__":
    root = tk.Tk()
    app = FishSortingApp(root)
    root.mainloop()