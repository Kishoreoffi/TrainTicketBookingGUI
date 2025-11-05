import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import mysql.connector
import hashlib
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import datetime
import cv2
from PIL import Image, ImageTk
import os
from fpdf import FPDF
import time

# Database connection
def create_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="train_booking_db2"
        )
        return connection
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error: {err}")
        return None

# Create necessary tables if they don't exist
def initialize_database():
    connection = create_db_connection()
    if connection:
        cursor = connection.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                verified BOOLEAN DEFAULT FALSE,
                otp VARCHAR(6),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Trains table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trains (
                id INT AUTO_INCREMENT PRIMARY KEY,
                train_name VARCHAR(255) NOT NULL,
                source VARCHAR(255) NOT NULL,
                destination VARCHAR(255) NOT NULL,
                departure_time TIME NOT NULL,
                arrival_time TIME NOT NULL,
                seats_available INT NOT NULL
            )
        """)
        
        # Bookings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                train_id INT NOT NULL,
                journey_date DATE NOT NULL,
                passengers INT NOT NULL,
                total_fare DECIMAL(10, 2) NOT NULL,
                booking_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'Confirmed',
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (train_id) REFERENCES trains(id)
            )
        """)
        
        # Tickets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INT AUTO_INCREMENT PRIMARY KEY,
                booking_id INT NOT NULL,
                pdf_path VARCHAR(500),
                FOREIGN KEY (booking_id) REFERENCES bookings(id)
            )
        """)
        
        # Insert sample train data if not exists
        cursor.execute("SELECT COUNT(*) FROM trains")
        if cursor.fetchone()[0] == 0:
            sample_trains = [
                ("Pandian Express", "Madurai", "Chennai", "06:00:00", "13:00:00", 100),
                ("Vaigai Express", "Madurai", "Chennai", "15:00:00", "22:00:00", 120),
                ("Nellai Express", "Tirunelveli", "Chennai", "17:30:00", "06:00:00", 80),
                ("Kanyakumari Express", "Kanyakumari", "Chennai", "16:00:00", "07:00:00", 90),
                ("Rockfort Express", "Coimbatore", "Chennai", "21:00:00", "05:00:00", 110)
            ]
            
            for train in sample_trains:
                cursor.execute(
                    "INSERT INTO trains (train_name, source, destination, departure_time, arrival_time, seats_available) VALUES (%s, %s, %s, %s, %s, %s)",
                    train
                )
        
        connection.commit()
        cursor.close()
        connection.close()

# Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# OTP generation
def generate_otp():
    return str(random.randint(100000, 999999))

# Email sending function
def send_email(receiver_email, subject, body, attachment_path=None):
    try:
        # Replace with your email credentials
        sender_email = "labs65432@gmail.com"
        sender_password = "nkdddraihhptfioe"  # Use app password for Gmail
        
        # Create message
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        
        # Add body to email
        message.attach(MIMEText(body, "plain"))
        
        # Add attachment if provided
        if attachment_path:
            with open(attachment_path, "rb") as attachment:
                part = MIMEApplication(attachment.read(), Name=os.path.basename(attachment_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                message.attach(part)
        
        # Create SMTP session
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# PDF generation
def generate_pdf(booking_details, user_details, image_path=None):
    pdf = FPDF()
    pdf.add_page()
    
    # Add title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Train Ticket", 0, 1, "C")
    pdf.ln(10)
    
    # Add user details
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Passenger Details", 0, 1)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Name: {user_details['name']}", 0, 1)
    pdf.cell(0, 10, f"Email: {user_details['email']}", 0, 1)
    pdf.ln(5)
    
    # Add booking details
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Journey Details", 0, 1)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Train: {booking_details['train_name']}", 0, 1)
    pdf.cell(0, 10, f"From: {booking_details['source']} To: {booking_details['destination']}", 0, 1)
    pdf.cell(0, 10, f"Departure: {booking_details['departure_time']} on {booking_details['journey_date']}", 0, 1)
    pdf.cell(0, 10, f"Arrival: {booking_details['arrival_time']}", 0, 1)
    pdf.cell(0, 10, f"Passengers: {booking_details['passengers']}", 0, 1)
    pdf.cell(0, 10, f"Total Fare: INR {booking_details['total_fare']}", 0, 1)
    pdf.cell(0, 10, f"Status: {booking_details['status']}", 0, 1)
    pdf.ln(5)
    
    # Add captured image if available
    if image_path and os.path.exists(image_path):
        pdf.cell(0, 10, "Passenger Photo:", 0, 1)
        pdf.image(image_path, x=10, y=pdf.get_y(), w=40)
        pdf.ln(45)
    
    # Add footer
    pdf.set_y(-15)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 0, 'C')
    
    # Save PDF
    pdf_path = f"ticket_{booking_details['train_name'].replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(pdf_path)
    
    return pdf_path

# Registration module
class Registration:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app
        self.frame = tk.Frame(self.root)
        
        # Registration form
        tk.Label(self.frame, text="Name:").grid(row=0, column=0, padx=10, pady=5, sticky='e')
        self.name_entry = tk.Entry(self.frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(self.frame, text="Email:").grid(row=1, column=0, padx=10, pady=5, sticky='e')
        self.email_entry = tk.Entry(self.frame, width=30)
        self.email_entry.grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(self.frame, text="Password:").grid(row=2, column=0, padx=10, pady=5, sticky='e')
        self.password_entry = tk.Entry(self.frame, width=30, show="*")
        self.password_entry.grid(row=2, column=1, padx=10, pady=5)
        
        tk.Label(self.frame, text="Confirm Password:").grid(row=3, column=0, padx=10, pady=5, sticky='e')
        self.confirm_password_entry = tk.Entry(self.frame, width=30, show="*")
        self.confirm_password_entry.grid(row=3, column=1, padx=10, pady=5)
        
        self.register_btn = tk.Button(self.frame, text="Register", command=self.register)
        self.register_btn.grid(row=4, column=1, padx=10, pady=10, sticky='e')
        
        self.back_btn = tk.Button(self.frame, text="Back to Main Menu", command=self.go_to_main)
        self.back_btn.grid(row=4, column=0, padx=10, pady=10, sticky='w')
        
        self.frame.pack(padx=20, pady=20)
    
    def register(self):
        name = self.name_entry.get()
        email = self.email_entry.get()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        
        if not name or not email or not password or not confirm_password:
            messagebox.showerror("Error", "All fields are required!")
            return
        
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match!")
            return
        
        # Check if email already exists
        connection = create_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                messagebox.showerror("Error", "Email already registered!")
                connection.close()
                return
            
            # Hash password and generate OTP
            hashed_password = hash_password(password)
            otp = generate_otp()
            
            # Insert user into database
            cursor.execute(
                "INSERT INTO users (name, email, password, otp) VALUES (%s, %s, %s, %s)",
                (name, email, hashed_password, otp)
            )
            connection.commit()
            
            # Send OTP email
            email_body = f"Your OTP for registration is: {otp}\nPlease enter this code to verify your account."
            if send_email(email, "Train Booking - OTP Verification", email_body):
                messagebox.showinfo("Success", "Registration successful! OTP sent to your email.")
                self.verify_otp_screen(email)
            else:
                messagebox.showerror("Error", "Failed to send OTP email. Please try again.")
            
            connection.close()
    
    def verify_otp_screen(self, email):
        # Clear the registration form
        for widget in self.frame.winfo_children():
            widget.destroy()
        
        tk.Label(self.frame, text="OTP Verification").pack(pady=10)
        tk.Label(self.frame, text=f"Enter OTP sent to {email}").pack(pady=5)
        
        self.otp_entry = tk.Entry(self.frame, width=30)
        self.otp_entry.pack(pady=5)
        
        verify_btn = tk.Button(self.frame, text="Verify OTP", command=lambda: self.verify_otp(email))
        verify_btn.pack(pady=10)
        
        back_btn = tk.Button(self.frame, text="Back to Main Menu", command=self.go_to_main)
        back_btn.pack(pady=5)
    
    def verify_otp(self, email):
        entered_otp = self.otp_entry.get()
        
        connection = create_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT otp FROM users WHERE email = %s", (email,))
            result = cursor.fetchone()
            
            if result and result[0] == entered_otp:
                # Update user as verified
                cursor.execute("UPDATE users SET verified = TRUE, otp = NULL WHERE email = %s", (email,))
                connection.commit()
                connection.close()
                
                messagebox.showinfo("Success", "OTP verified successfully! You can now login.")
                self.go_to_main()
            else:
                messagebox.showerror("Error", "Invalid OTP! Please try again.")
                connection.close()
    
    def go_to_main(self):
        self.frame.destroy()
        self.main_app.show_main_menu()

# Login module
class Login:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app
        self.frame = tk.Frame(self.root)
        
        # Login form
        tk.Label(self.frame, text="Email:").grid(row=0, column=0, padx=10, pady=5, sticky='e')
        self.email_entry = tk.Entry(self.frame, width=30)
        self.email_entry.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(self.frame, text="Password:").grid(row=1, column=0, padx=10, pady=5, sticky='e')
        self.password_entry = tk.Entry(self.frame, width=30, show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=5)
        
        self.login_btn = tk.Button(self.frame, text="Login", command=self.login)
        self.login_btn.grid(row=2, column=1, padx=10, pady=10, sticky='e')
        
        self.back_btn = tk.Button(self.frame, text="Back to Main Menu", command=self.go_to_main)
        self.back_btn.grid(row=2, column=0, padx=10, pady=10, sticky='w')
        
        self.frame.pack(padx=20, pady=20)
    
    def login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        
        if not email or not password:
            messagebox.showerror("Error", "All fields are required!")
            return
        
        connection = create_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id, name, password, verified FROM users WHERE email = %s", (email,))
            result = cursor.fetchone()
            
            if result:
                user_id, name, hashed_password, verified = result
                if not verified:
                    messagebox.showerror("Error", "Email not verified! Please complete verification.")
                    connection.close()
                    return
                
                if hashed_password == hash_password(password):
                    messagebox.showinfo("Success", f"Welcome {name}!")
                    connection.close()
                    self.main_app.user_id = user_id
                    self.main_app.user_name = name
                    self.main_app.user_email = email
                    self.go_to_dashboard()
                else:
                    messagebox.showerror("Error", "Invalid password!")
            else:
                messagebox.showerror("Error", "Email not found!")
            
            connection.close()
    
    def go_to_dashboard(self):
        self.frame.destroy()
        self.main_app.show_dashboard()
    
    def go_to_main(self):
        self.frame.destroy()
        self.main_app.show_main_menu()

# Dashboard module
class Dashboard:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app
        self.frame = tk.Frame(self.root)
        
        tk.Label(self.frame, text=f"Welcome {main_app.user_name}", font=("Arial", 16)).pack(pady=20)
        
        tk.Button(self.frame, text="1. Book Tickets", command=self.book_tickets, width=20, height=2).pack(pady=10)
        tk.Button(self.frame, text="2. Download Tickets", command=self.download_tickets, width=20, height=2).pack(pady=10)
        tk.Button(self.frame, text="3. Exit", command=self.exit_app, width=20, height=2).pack(pady=10)
        
        self.frame.pack(padx=20, pady=20)
    
    def book_tickets(self):
        self.frame.destroy()
        self.main_app.show_booking()
    
    def download_tickets(self):
        # Show user's tickets for download
        connection = create_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT b.id, t.train_name, b.journey_date, b.passengers, b.total_fare, tk.pdf_path
                FROM bookings b
                JOIN trains t ON b.train_id = t.id
                LEFT JOIN tickets tk ON b.id = tk.booking_id
                WHERE b.user_id = %s
            """, (self.main_app.user_id,))
            
            bookings = cursor.fetchall()
            connection.close()
            
            if not bookings:
                messagebox.showinfo("Info", "You have no bookings yet.")
                return
            
            # Create download window
            self.download_window = tk.Toplevel(self.root)
            self.download_window.title("Your Tickets")
            self.download_window.geometry("600x400")
            
            tk.Label(self.download_window, text="Your Bookings", font=("Arial", 14)).pack(pady=10)
            
            # Create a frame for the listbox and scrollbar
            frame = tk.Frame(self.download_window)
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Create a listbox to display bookings
            scrollbar = tk.Scrollbar(frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            self.bookings_listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, width=80, height=15)
            self.bookings_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=self.bookings_listbox.yview)
            
            # Add bookings to the listbox
            for booking in bookings:
                booking_id, train_name, journey_date, passengers, total_fare, pdf_path = booking
                display_text = f"ID: {booking_id} | Train: {train_name} | Date: {journey_date} | Passengers: {passengers} | Fare: INR {total_fare}"
                if pdf_path:
                    display_text += " | PDF Available"
                self.bookings_listbox.insert(tk.END, display_text)
            
            # Download button
            tk.Button(self.download_window, text="Download Selected Ticket", command=self.download_selected_ticket).pack(pady=10)
            
            # Close button
            tk.Button(self.download_window, text="Close", command=self.download_window.destroy).pack(pady=5)
    
    def download_selected_ticket(self):
        selected_index = self.bookings_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Warning", "Please select a ticket to download.")
            return
        
        selected_text = self.bookings_listbox.get(selected_index)
        booking_id = int(selected_text.split("|")[0].split(":")[1].strip())
        
        connection = create_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT pdf_path FROM tickets WHERE booking_id = %s", (booking_id,))
            result = cursor.fetchone()
            connection.close()
            
            if result and result[0]:
                pdf_path = result[0]
                # Ask user where to save the file
                save_path = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("PDF files", "*.pdf")],
                    title="Save Ticket PDF"
                )
                
                if save_path:
                    try:
                        # Copy the PDF file to the selected location
                        with open(pdf_path, 'rb') as source_file:
                            with open(save_path, 'wb') as target_file:
                                target_file.write(source_file.read())
                        messagebox.showinfo("Success", f"Ticket saved to {save_path}")
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to save ticket: {e}")
            else:
                messagebox.showwarning("Warning", "No PDF available for this booking.")
    
    def exit_app(self):
        self.root.quit()

# Booking module
class Booking:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app
        self.frame = tk.Frame(self.root)
        
        # Tamil Nadu cities
        self.cities = [
            "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem",
            "Tirunelveli", "Tiruppur", "Erode", "Vellore", "Thoothukudi",
            "Dindigul", "Thanjavur", "Ranipet", "Sivakasi", "Karur"
        ]
        
        tk.Label(self.frame, text="Book Tickets", font=("Arial", 16)).pack(pady=10)
        
        # Source selection
        tk.Label(self.frame, text="From:").pack(pady=5)
        self.source_var = tk.StringVar()
        self.source_combo = ttk.Combobox(self.frame, textvariable=self.source_var, values=self.cities, state="readonly")
        self.source_combo.pack(pady=5)
        
        # Destination selection
        tk.Label(self.frame, text="To:").pack(pady=5)
        self.dest_var = tk.StringVar()
        self.dest_combo = ttk.Combobox(self.frame, textvariable=self.dest_var, values=self.cities, state="readonly")
        self.dest_combo.pack(pady=5)
        
        # Journey date
        tk.Label(self.frame, text="Journey Date:").pack(pady=5)
        self.date_entry = tk.Entry(self.frame)
        self.date_entry.insert(0, (datetime.datetime.now() + datetime.timedelta(days=2)).strftime("%Y-%m-%d"))
        self.date_entry.pack(pady=5)
        
        # Number of passengers
        tk.Label(self.frame, text="Number of Passengers:").pack(pady=5)
        self.passengers_var = tk.IntVar(value=1)
        tk.Spinbox(self.frame, from_=1, to=10, textvariable=self.passengers_var, width=10).pack(pady=5)
        
        # Search button
        tk.Button(self.frame, text="Search Trains", command=self.search_trains).pack(pady=10)
        
        # Back button
        tk.Button(self.frame, text="Back to Dashboard", command=self.go_to_dashboard).pack(pady=5)
        
        self.frame.pack(padx=20, pady=20)
    
    def search_trains(self):
        source = self.source_var.get()
        destination = self.dest_var.get()
        journey_date = self.date_entry.get()
        passengers = self.passengers_var.get()
        
        if not source or not destination:
            messagebox.showerror("Error", "Please select both source and destination.")
            return
        
        if source == destination:
            messagebox.showerror("Error", "Source and destination cannot be the same.")
            return
        
        # Validate date
        try:
            journey_date_obj = datetime.datetime.strptime(journey_date, "%Y-%m-%d")
            if journey_date_obj < datetime.datetime.now():
                messagebox.showerror("Error", "Journey date cannot be in the past.")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD.")
            return
        
        # Search for available trains
        connection = create_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Calculate time range (current time to 2 days later + 11am)
            current_time = datetime.datetime.now().time()
            time_condition = f"departure_time >= '{current_time}'" if journey_date_obj.date() == datetime.datetime.now().date() else "1=1"
            
            cursor.execute(f"""
                SELECT * FROM trains 
                WHERE source = %s AND destination = %s 
                AND seats_available >= %s
                AND {time_condition}
                ORDER BY departure_time
            """, (source, destination, passengers))
            
            trains = cursor.fetchall()
            connection.close()
            
            if not trains:
                messagebox.showinfo("No Trains", "No trains available for the selected route and date.")
                return
            
            # Show available trains
            self.show_available_trains(trains, journey_date, passengers)
    
    def show_available_trains(self, trains, journey_date, passengers):
        # Clear the current frame
        for widget in self.frame.winfo_children():
            widget.destroy()
        
        tk.Label(self.frame, text="Available Trains", font=("Arial", 16)).pack(pady=10)
        
        # Create a frame for the listbox and scrollbar
        list_frame = tk.Frame(self.frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a listbox to display trains
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.trains_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, width=80, height=10)
        self.trains_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.trains_listbox.yview)
        
        # Add trains to the listbox
        for train in trains:
            train_id, train_name, source, destination, dep_time, arr_time, seats = train
            display_text = f"{train_name} | {source} to {destination} | Dep: {dep_time} | Arr: {arr_time} | Seats: {seats}"
            self.trains_listbox.insert(tk.END, display_text)
        
        # Select train button
        tk.Button(self.frame, text="Select Train", command=lambda: self.select_train(trains, journey_date, passengers)).pack(pady=10)
        
        # Back button
        tk.Button(self.frame, text="Back", command=self.go_back).pack(pady=5)
    
    def select_train(self, trains, journey_date, passengers):
        selected_index = self.trains_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Warning", "Please select a train.")
            return
        
        selected_train = trains[selected_index[0]]
        train_id, train_name, source, destination, dep_time, arr_time, seats = selected_train
        
        # Calculate fare (simple calculation: ₹100 per passenger)
        fare = passengers * 100
        
        # Ask for confirmation
        confirm = messagebox.askyesno(
            "Confirm Booking",
            f"Train: {train_name}\nFrom: {source} To: {destination}\nDate: {journey_date}\nDeparture: {dep_time}\nPassengers: {passengers}\nTotal Fare: INR{fare}\n\nDo you want to proceed?"
        )
        
        if confirm:
            # Send OTP for verification
            otp = generate_otp()
            
            connection = create_db_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute("UPDATE users SET otp = %s WHERE id = %s", (otp, self.main_app.user_id))
                connection.commit()
                connection.close()
            
            email_body = f"Your OTP for ticket booking is: {otp}\nPlease enter this code to confirm your booking."
            if send_email(self.main_app.user_email, "Train Booking - OTP Verification", email_body):
                self.otp_verification_screen(train_id, journey_date, passengers, fare)
            else:
                messagebox.showerror("Error", "Failed to send OTP email. Please try again.")
    
    def otp_verification_screen(self, train_id, journey_date, passengers, fare):
        # Clear the current frame
        for widget in self.frame.winfo_children():
            widget.destroy()
        
        tk.Label(self.frame, text="OTP Verification", font=("Arial", 16)).pack(pady=10)
        tk.Label(self.frame, text=f"Enter OTP sent to {self.main_app.user_email}").pack(pady=5)
        
        self.otp_entry = tk.Entry(self.frame, width=30)
        self.otp_entry.pack(pady=5)
        
        verify_btn = tk.Button(self.frame, text="Verify OTP", command=lambda: self.verify_otp(train_id, journey_date, passengers, fare))
        verify_btn.pack(pady=10)
        
        back_btn = tk.Button(self.frame, text="Back", command=self.go_back)
        back_btn.pack(pady=5)
    
    def verify_otp(self, train_id, journey_date, passengers, fare):
        entered_otp = self.otp_entry.get()
        
        connection = create_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT otp FROM users WHERE id = %s", (self.main_app.user_id,))
            result = cursor.fetchone()
            
            if result and result[0] == entered_otp:
                # OTP verified, proceed to capture image
                cursor.execute("UPDATE users SET otp = NULL WHERE id = %s", (self.main_app.user_id,))
                connection.commit()
                connection.close()
                
                self.capture_image_screen(train_id, journey_date, passengers, fare)
            else:
                messagebox.showerror("Error", "Invalid OTP! Please try again.")
                connection.close()
    
    def capture_image_screen(self, train_id, journey_date, passengers, fare):
        # Clear the current frame
        for widget in self.frame.winfo_children():
            widget.destroy()
        
        tk.Label(self.frame, text="Capture Live Image", font=("Arial", 16)).pack(pady=10)
        tk.Label(self.frame, text="Please look at the camera and click 'Capture Image'").pack(pady=5)
        
        # Create a label for the camera feed
        self.camera_label = tk.Label(self.frame)
        self.camera_label.pack(pady=5)
        
        # Start camera
        self.cap = cv2.VideoCapture(0)
        self.update_camera()
        
        # Capture button
        capture_btn = tk.Button(self.frame, text="Capture Image", command=lambda: self.capture_image(train_id, journey_date, passengers, fare))
        capture_btn.pack(pady=10)
        
        # Skip button
        skip_btn = tk.Button(self.frame, text="Skip Image Capture", command=lambda: self.process_payment(train_id, journey_date, passengers, fare, None))
        skip_btn.pack(pady=5)
        
        # Back button
        back_btn = tk.Button(self.frame, text="Back", command=self.go_back)
        back_btn.pack(pady=5)
    
    def update_camera(self):
        ret, frame = self.cap.read()
        if ret:
            # Convert frame to RGB and resize
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (320, 240))
            
            # Convert to ImageTk format
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            
            # Update label
            self.camera_label.imgtk = imgtk
            self.camera_label.configure(image=imgtk)
            
            # Schedule next update
            self.root.after(10, self.update_camera)
    
    def capture_image(self, train_id, journey_date, passengers, fare):
        ret, frame = self.cap.read()
        if ret:
            # Save the captured image
            image_path = f"user_{self.main_app.user_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(image_path, frame)
            
            # Release camera
            self.cap.release()
            
            # Process payment
            self.process_payment(train_id, journey_date, passengers, fare, image_path)
        else:
            messagebox.showerror("Error", "Failed to capture image. Please try again.")
    
    def process_payment(self, train_id, journey_date, passengers, fare, image_path):
        # Clear the current frame
        for widget in self.frame.winfo_children():
            widget.destroy()
        
        tk.Label(self.frame, text="Payment Process", font=("Arial", 16)).pack(pady=10)
        tk.Label(self.frame, text=f"Total Amount to Pay: INR {fare}").pack(pady=5)
        
        # Simple payment - just enter the correct amount
        tk.Label(self.frame, text="Enter the amount to pay:").pack(pady=5)
        self.payment_entry = tk.Entry(self.frame, width=30)
        self.payment_entry.pack(pady=5)
        
        # Process payment button
        pay_btn = tk.Button(self.frame, text="Pay Now", 
                           command=lambda: self.complete_payment(train_id, journey_date, passengers, fare, image_path))
        pay_btn.pack(pady=10)
        
        # Back button
        back_btn = tk.Button(self.frame, text="Back", command=self.go_back)
        back_btn.pack(pady=5)
    
    def complete_payment(self, train_id, journey_date, passengers, fare, image_path):
        try:
            entered_amount = float(self.payment_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount!")
            return
        
        # Check if the entered amount matches the fare
        if entered_amount != fare:
            messagebox.showerror("Error", f"Amount must be exactly INR{fare}. Please enter the correct amount.")
            return
        
        # Process booking
        connection = create_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Create booking
            cursor.execute(
                "INSERT INTO bookings (user_id, train_id, journey_date, passengers, total_fare) VALUES (%s, %s, %s, %s, %s)",
                (self.main_app.user_id, train_id, journey_date, passengers, fare)
            )
            booking_id = cursor.lastrowid
            
            # Update available seats
            cursor.execute("UPDATE trains SET seats_available = seats_available - %s WHERE id = %s", (passengers, train_id))
            
            # Get train details for PDF
            cursor.execute("SELECT train_name, source, destination, departure_time, arrival_time FROM trains WHERE id = %s", (train_id,))
            train_details = cursor.fetchone()
            
            connection.commit()
            connection.close()
            
            # Generate PDF ticket
            booking_details = {
                'train_name': train_details[0],
                'source': train_details[1],
                'destination': train_details[2],
                'departure_time': str(train_details[3]),
                'arrival_time': str(train_details[4]),
                'journey_date': journey_date,
                'passengers': passengers,
                'total_fare': fare,
                'status': 'Confirmed'
            }
            
            user_details = {
                'name': self.main_app.user_name,
                'email': self.main_app.user_email
            }
            
            pdf_path = generate_pdf(booking_details, user_details, image_path)
            
            # Store PDF path in database
            connection = create_db_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO tickets (booking_id, pdf_path) VALUES (%s, %s)",
                    (booking_id, pdf_path)
                )
                connection.commit()
                connection.close()
            
            # Send email with ticket
            email_body = f"Dear {self.main_app.user_name},\\n\\nYour train ticket booking is confirmed.\\n\\nTrain: {train_details[0]}\\nFrom: {train_details[1]} To: {train_details[2]}\\nDate: {journey_date}\\nDeparture: {train_details[3]}\\nPassengers: {passengers}\\nTotal Fare: INR {fare}\\n\\nThank you for using our service!"

            if send_email(self.main_app.user_email, "Train Ticket Booking Confirmation", email_body, pdf_path):
                messagebox.showinfo("Success", "Booking confirmed! Ticket has been sent to your email.")
            else:
                messagebox.showinfo("Success", "Booking confirmed! But failed to send email.")
            
            # Ask user what to do next
            self.ask_next_action()
    
    def ask_next_action(self):
        # Clear the current frame
        for widget in self.frame.winfo_children():
            widget.destroy()
        
        tk.Label(self.frame, text="Booking Completed Successfully!", font=("Arial", 16)).pack(pady=20)
        
        tk.Button(self.frame, text="Book Another Ticket", command=self.book_another, width=20, height=2).pack(pady=10)
        tk.Button(self.frame, text="Go to Dashboard", command=self.go_to_dashboard, width=20, height=2).pack(pady=10)
        tk.Button(self.frame, text="Exit", command=self.exit_app, width=20, height=2).pack(pady=10)
        
        self.frame.pack(padx=20, pady=20)
    
    def book_another(self):
        self.frame.destroy()
        self.__init__(self.root, self.main_app)
    
    def go_to_dashboard(self):
        self.frame.destroy()
        self.main_app.show_dashboard()
    
    def exit_app(self):
        self.root.quit()
    
    def go_back(self):
        self.frame.destroy()
        self.__init__(self.root, self.main_app)

# Main application
class TrainBookingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Train Ticket Booking System")
        self.root.geometry("800x600")
        
        # Initialize database
        initialize_database()
        
        # User info
        self.user_id = None
        self.user_name = None
        self.user_email = None
        
        self.show_main_menu()
    
    def show_main_menu(self):
        # Clear the window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Main menu
        tk.Label(self.root, text="Train Ticket Booking System", font=("Arial", 20)).pack(pady=30)
        
        tk.Button(self.root, text="Register", command=self.show_registration, width=20, height=2).pack(pady=10)
        tk.Button(self.root, text="Login", command=self.show_login, width=20, height=2).pack(pady=10)
        tk.Button(self.root, text="Exit", command=self.root.quit, width=20, height=2).pack(pady=10)
    
    def show_registration(self):
        # Clear the window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Show registration form
        Registration(self.root, self)
    
    def show_login(self):
        # Clear the window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Show login form
        Login(self.root, self)
    
    def show_dashboard(self):
        # Clear the window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Show dashboard
        Dashboard(self.root, self)
    
    def show_booking(self):
        # Clear the window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Show booking form
        Booking(self.root, self)

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = TrainBookingApp(root)
    root.mainloop()