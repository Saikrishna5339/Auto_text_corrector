import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import time
from .corrector import Corrector
from .corpus import CorpusHandler

class AutoCorrectGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto-Correct System")
        self.root.geometry("800x600")
        self.root.minsize(600, 500)
        
        # Initialize corrector in a separate thread to avoid UI freezing
        self.corrector = None
        self.initialization_done = False
        threading.Thread(target=self._initialize_corrector).start()
        
        # Create the main UI frame
        self.main_frame = ttk.Frame(root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a notebook with tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create the main correction tab
        self.create_correction_tab()
        
        # Create the settings tab
        self.create_settings_tab()
        
        # Create the about tab
        self.create_about_tab()
        
        # Status bar at the bottom
        self.status_var = tk.StringVar()
        self.status_var.set("Initializing spell checker...")
        self.status_bar = ttk.Label(
            root, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor="w"
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Periodically check if initialization is done
        self._check_initialization()
    
    def _initialize_corrector(self):
        """Initialize the corrector in a background thread"""
        try:
            self.corrector = Corrector()
            self.initialization_done = True
            self.status_var.set("Ready")
        except Exception as e:
            self.status_var.set(f"Error initializing: {str(e)}")
    
    def _check_initialization(self):
        """Check if corrector initialization is done"""
        if self.initialization_done:
            self.status_var.set("Ready")
            # Enable UI elements that depend on the corrector
            if hasattr(self, 'correct_button'):
                self.correct_button.config(state=tk.NORMAL)
        else:
            # Check again after 100ms
            self.root.after(100, self._check_initialization)
    
    def create_correction_tab(self):
        """Create the main text correction tab"""
        correction_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(correction_tab, text="Text Correction")
        
        # Input frame
        input_frame = ttk.LabelFrame(correction_tab, text="Input Text", padding=5)
        input_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Text input area with scrollbars
        self.input_text = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, height=10)
        self.input_text.pack(fill=tk.BOTH, expand=True)
        
        # Buttons frame
        button_frame = ttk.Frame(correction_tab, padding=5)
        button_frame.pack(fill=tk.X, pady=5)
        
        # Load text from file button
        load_button = ttk.Button(
            button_frame, 
            text="Load from File", 
            command=self.load_text_from_file
        )
        load_button.pack(side=tk.LEFT, padx=5)
        
        # Correction buttons
        self.correct_button = ttk.Button(
            button_frame, 
            text="Correct Text", 
            command=self.correct_text,
            state=tk.DISABLED  # Will be enabled when corrector is initialized
        )
        self.correct_button.pack(side=tk.RIGHT, padx=5)
        
        self.context_correct_button = ttk.Button(
            button_frame, 
            text="Correct with Context", 
            command=self.correct_text_with_context,
            state=tk.DISABLED  # Will be enabled when corrector is initialized
        )
        self.context_correct_button.pack(side=tk.RIGHT, padx=5)
        
        # Clear button
        clear_button = ttk.Button(
            button_frame, 
            text="Clear", 
            command=lambda: self.input_text.delete(1.0, tk.END)
        )
        clear_button.pack(side=tk.LEFT, padx=5)
        
        # Output frame
        output_frame = ttk.LabelFrame(correction_tab, text="Corrected Text", padding=5)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Text output area with scrollbars
        self.output_text = scrolledtext.ScrolledText(
            output_frame, 
            wrap=tk.WORD, 
            height=10,
            state=tk.DISABLED
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Save output button
        save_button = ttk.Button(
            output_frame, 
            text="Save to File", 
            command=self.save_text_to_file
        )
        save_button.pack(side=tk.RIGHT, padx=5, pady=5)
    
    def create_settings_tab(self):
        """Create the settings tab"""
        settings_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(settings_tab, text="Settings")
        
        # Dictionary settings
        dict_frame = ttk.LabelFrame(settings_tab, text="Dictionary Settings", padding=10)
        dict_frame.pack(fill=tk.X, pady=5)
        
        # Custom dictionary option
        ttk.Label(dict_frame, text="Custom Dictionary:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        self.dict_path_var = tk.StringVar()
        dict_entry = ttk.Entry(dict_frame, textvariable=self.dict_path_var, width=50)
        dict_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        dict_button = ttk.Button(
            dict_frame, 
            text="Browse...", 
            command=self.browse_dictionary
        )
        dict_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Load dictionary button
        load_dict_button = ttk.Button(
            dict_frame, 
            text="Load Dictionary", 
            command=self.load_custom_dictionary
        )
        load_dict_button.grid(row=1, column=1, sticky=tk.E, padx=5, pady=5)
        
        # Custom correction settings
        correction_frame = ttk.LabelFrame(settings_tab, text="Custom Corrections", padding=10)
        correction_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Add a custom correction
        ttk.Label(correction_frame, text="Misspelled Word:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        self.misspelled_var = tk.StringVar()
        misspelled_entry = ttk.Entry(correction_frame, textvariable=self.misspelled_var)
        misspelled_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(correction_frame, text="Correction:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        self.correction_var = tk.StringVar()
        correction_entry = ttk.Entry(correction_frame, textvariable=self.correction_var)
        correction_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Add correction button
        add_button = ttk.Button(
            correction_frame, 
            text="Add Correction", 
            command=self.add_custom_correction
        )
        add_button.grid(row=2, column=1, sticky=tk.E, padx=5, pady=5)
        
        # Custom corrections list (placeholder)
        ttk.Label(correction_frame, text="Custom Corrections List:").grid(
            row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5
        )
        
        # List of custom corrections
        self.corrections_list = tk.Listbox(correction_frame, height=10)
        self.corrections_list.grid(
            row=4, column=0, columnspan=2, sticky=tk.NSEW, padx=5, pady=5
        )
        
        # Make the list expandable
        correction_frame.columnconfigure(1, weight=1)
        correction_frame.rowconfigure(4, weight=1)
    
    def create_about_tab(self):
        """Create the about tab"""
        about_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(about_tab, text="About")
        
        # Title
        title_label = ttk.Label(
            about_tab, 
            text="Auto-Correct System", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # Description
        desc_frame = ttk.Frame(about_tab, padding=10)
        desc_frame.pack(fill=tk.BOTH, expand=True)
        
        description = (
            "Auto-Correct System using Natural Language Processing Techniques\n\n"
            "This application detects and corrects spelling mistakes in real-time by "
            "leveraging core NLP techniques and probabilistic models. It utilizes "
            "algorithms such as:\n\n"
            "• Levenshtein Distance to calculate edit distance\n"
            "• N-gram models for contextual relevance\n"
            "• Norvig's algorithm to generate and rank candidate words\n\n"
            "The system employs multiple correction strategies and uses a voting "
            "mechanism to select the best correction for each misspelled word.\n\n"
            "It is adaptable and can be extended with custom dictionaries and "
            "personalized corrections."
        )
        
        desc_text = scrolledtext.ScrolledText(
            desc_frame, 
            wrap=tk.WORD, 
            height=15,
            font=("Arial", 10)
        )
        desc_text.pack(fill=tk.BOTH, expand=True)
        desc_text.insert(tk.END, description)
        desc_text.config(state=tk.DISABLED)
    
    def load_text_from_file(self):
        """Load text from a file into the input text area"""
        file_path = filedialog.askopenfilename(
            title="Select a Text File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                self.input_text.delete(1.0, tk.END)
                self.input_text.insert(tk.END, text)
            self.status_var.set(f"Loaded text from {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")
            self.status_var.set("Error loading file")
    
    def save_text_to_file(self):
        """Save corrected text to a file"""
        file_path = filedialog.asksaveasfilename(
            title="Save Corrected Text",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            output_text = self.output_text.get(1.0, tk.END)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(output_text)
            self.status_var.set(f"Saved corrected text to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")
            self.status_var.set("Error saving file")
    
    def browse_dictionary(self):
        """Browse for a custom dictionary file"""
        file_path = filedialog.askopenfilename(
            title="Select Dictionary File",
            filetypes=[
                ("Text files", "*.txt"), 
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.dict_path_var.set(file_path)
    
    def load_custom_dictionary(self):
        """Load a custom dictionary"""
        dict_path = self.dict_path_var.get().strip()
        
        if not dict_path:
            messagebox.showwarning("Warning", "Please select a dictionary file first.")
            return
            
        if not self.initialization_done:
            messagebox.showwarning("Warning", "Still initializing, please wait.")
            return
            
        # Show loading indicator
        self.status_var.set("Loading custom dictionary...")
        self.root.update_idletasks()
        
        # Run in a separate thread to avoid freezing the UI
        threading.Thread(target=self._load_dictionary_thread, args=(dict_path,)).start()
    
    def _load_dictionary_thread(self, dict_path):
        """Thread function to load dictionary"""
        try:
            # Reinitialize the corrector with the custom dictionary
            self.corrector = Corrector(custom_dict_path=dict_path)
            self.root.after(0, lambda: self.status_var.set(f"Loaded dictionary from {dict_path}"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to load dictionary: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Error loading dictionary"))
    
    def add_custom_correction(self):
        """Add a custom correction to the corrector"""
        if not self.initialization_done:
            messagebox.showwarning("Warning", "Still initializing, please wait.")
            return
            
        misspelled = self.misspelled_var.get().strip()
        correction = self.correction_var.get().strip()
        
        if not misspelled or not correction:
            messagebox.showwarning("Warning", "Please enter both the misspelled word and correction.")
            return
            
        # Add the correction
        self.corrector.add_user_correction(misspelled, correction)
        
        # Update the list
        list_item = f"{misspelled} -> {correction}"
        self.corrections_list.insert(tk.END, list_item)
        
        # Clear the entries
        self.misspelled_var.set("")
        self.correction_var.set("")
        
        self.status_var.set(f"Added correction: '{misspelled}' -> '{correction}'")
    
    def correct_text(self):
        """Correct the input text"""
        if not self.initialization_done:
            messagebox.showwarning("Warning", "Still initializing, please wait.")
            return
            
        input_text = self.input_text.get(1.0, tk.END)
        
        if not input_text.strip():
            messagebox.showwarning("Warning", "Please enter some text to correct.")
            return
            
        # Show loading indicator
        self.status_var.set("Correcting text...")
        self.root.update_idletasks()
        
        # Disable the correction buttons while processing
        self.correct_button.config(state=tk.DISABLED)
        self.context_correct_button.config(state=tk.DISABLED)
        
        # Run correction in a separate thread
        threading.Thread(
            target=self._correct_text_thread, 
            args=(input_text, False)
        ).start()
    
    def correct_text_with_context(self):
        """Correct the input text using contextual information"""
        if not self.initialization_done:
            messagebox.showwarning("Warning", "Still initializing, please wait.")
            return
            
        input_text = self.input_text.get(1.0, tk.END)
        
        if not input_text.strip():
            messagebox.showwarning("Warning", "Please enter some text to correct.")
            return
            
        # Show loading indicator
        self.status_var.set("Correcting text with context...")
        self.root.update_idletasks()
        
        # Disable the correction buttons while processing
        self.correct_button.config(state=tk.DISABLED)
        self.context_correct_button.config(state=tk.DISABLED)
        
        # Run correction in a separate thread
        threading.Thread(
            target=self._correct_text_thread, 
            args=(input_text, True)
        ).start()
    
    def _correct_text_thread(self, input_text, use_context):
        """Thread function to perform text correction"""
        try:
            start_time = time.time()
            
            # Perform correction
            if use_context:
                corrected_text = self.corrector.correct_with_context(input_text)
            else:
                corrected_text = self.corrector.correct_text(input_text)
                
            elapsed_time = time.time() - start_time
            
            # Update UI in the main thread
            self.root.after(0, lambda: self._update_output(corrected_text, elapsed_time, use_context))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Correction failed: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Error during correction"))
            self.root.after(0, lambda: self._enable_buttons())
    
    def _update_output(self, corrected_text, elapsed_time, use_context):
        """Update the output text area with corrected text"""
        # Enable the output text for editing
        self.output_text.config(state=tk.NORMAL)
        
        # Clear previous text and add corrected text
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, corrected_text)
        
        # Disable editing again
        self.output_text.config(state=tk.DISABLED)
        
        # Update status
        correction_type = "context-aware" if use_context else "basic"
        self.status_var.set(f"Text corrected using {correction_type} correction in {elapsed_time:.2f} seconds")
        
        # Re-enable the correction buttons
        self._enable_buttons()
    
    def _enable_buttons(self):
        """Re-enable the correction buttons"""
        self.correct_button.config(state=tk.NORMAL)
        self.context_correct_button.config(state=tk.NORMAL)

def launch_gui():
    """Launch the GUI application"""
    root = tk.Tk()
    app = AutoCorrectGUI(root)
    root.mainloop()

if __name__ == "__main__":
    launch_gui() 