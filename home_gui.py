import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter.filedialog import asksaveasfilename
import csv
import pandas as pd
import re
import sqlite3


def connect():
    """Connects to the databse"""
    conn = sqlite3.connect("db/cdms.db")
    return conn


def load_data():
    """Load data from database into the table Treeview after program starts"""
    table.delete(*table.get_children())
    conn = connect()
    cur = conn.execute("SELECT * FROM customer_data ORDER BY purchase_amount DESC")
    rows = cur.fetchall()
    for row in rows:
        table.insert("",tk.END,values=row)
    conn.close()
    customerid_entry.insert(tk.END, get_next_id()+1)


def get_next_id():
    """Return next record's id from sqlite_sequence table"""
    conn = connect()
    cur = conn.execute("SELECT seq from sqlite_sequence WHERE name='customer_data'")
    next = cur.fetchall()[0][0]
    conn.close()
    return next


def email_validation(email):
    """validate email based on pattern"""
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"

    if re.match(pattern,email):
        return True
    else:
        messagebox.showerror("Invalid Email", "Please enter a valid email address.")


def phone_number_validation(phone):
    """Validate phone number based on pattern"""
    pattern = r'^\d{10}$'

    if re.match(pattern, phone):
       return True
    else:
        messagebox.showerror("Invalid Phone Number", "Please enter a valid phone number in the format XXXXXXXXXX.")


def get_stats(event,state):
    """Provide stats data for selected state"""
    total_customers_entry.delete(0, tk.END)
    average_purchace_entry.delete(0, tk.END)

    conn = connect()
    cur = conn.execute("SELECT count(*) from customer_data WHERE state=?",(state,))
    total = cur.fetchall()[0][0]
    cur = conn.execute("SELECT avg(purchase_amount) from customer_data WHERE state=?",(state,))
    average = "%0.2f" % (cur.fetchall()[0][0],)
    conn.close()
    total_customers_entry.insert(tk.END,f"{state} is {total}")
    average_purchace_entry.insert(tk.END,f"{average}")


def get_segment_details(event,state):
    """Provide segment details based on purchase of amount of customers for selected state"""
    stats_table.delete(*stats_table.get_children())
    conn = connect()
    cur = conn.execute("""
                WITH customer_segments AS (
            SELECT
                customer_id,
                first_name || ' ' || last_name as full_name,
                state,
                purchase_amount,
                NTILE(4) OVER (PARTITION BY state ORDER BY purchase_amount DESC) AS segment
            FROM
                customer_data
            )
            SELECT
            customer_id,
            full_name,
            state,
            CASE
                WHEN segment = 4 THEN 'High Value'
                WHEN segment = 1 THEN 'Low Value'
                ELSE 'Medium Value'
            END AS segment_category
            FROM
            customer_segments WHERE state = ?;

                """,(state,))
    rows = cur.fetchall()
    for row in rows:
        stats_table.insert("",tk.END,values=row)
    conn.close()


def download_data(table):
    """Downloads the data of provided treeview and stores in a CSV file"""
    file_path = asksaveasfilename(defaultextension=".csv",filetypes=[("CSV Files","*.csv")])
    if file_path:
        with open(file_path,"w",newline='') as file:
            writer = csv.writer(file)

            header = [column for column in table['columns']]
            writer.writerow(header)

            rows = table.get_children()
            for item in rows:
                row  = [table.item(item,"values")[column] for column in range(len(header))]
                writer.writerow(row)
        messagebox.showinfo("Download Complete","The file has been downloaded.")


def clear_form(action="clear"):
        """Clears the values of all the entry widgets"""
        customerid_entry.delete(0, tk.END)
        if action == "clear":
            customerid_entry.insert(tk.END, get_next_id()+1)
        firstname_entry.delete(0, tk.END)
        lastname_entry.delete(0, tk.END)
        email_entry.delete(0, tk.END)
        phonenumber_entry.delete(0, tk.END)
        state_entry.delete(0, tk.END)
        purchaseamt_entry.delete(0, tk.END)
        search_entry.delete(0, tk.END)

        total_customers_entry.delete(0, tk.END)
        average_purchace_entry.delete(0, tk.END)


def on_select(event):
    """Event listner, to fill all the enrty widgets"""
    clear_form(action="on_select")
    selected = table.selection()
    if selected:
        values = table.item(selected)['values']

        customerid_entry.insert(0, values[0])
        firstname_entry.insert(0,values[1])
        lastname_entry.insert(0, values[2])
        email_entry.insert(0, values[3])
        phonenumber_entry.insert(0, values[4])
        state_entry.insert(0, values[5])
        purchaseamt_entry.insert(0, values[6])

    try:
        state = values[5]
        table.bind("<<TreeviewSelect>>",get_stats(event,state))
        stats_table.bind("<<TreeviewSelect>>",get_segment_details(event,state))
    except:
        pass


        
def add_record():
    """Stores data in the database"""
    customer_id = customerid_entry.get()
    first_name = firstname_entry.get()
    last_name = lastname_entry.get()
    email = email_entry.get()
    phone = phonenumber_entry.get()
    state = state_entry.get()
    purchase_amount = purchaseamt_entry.get()
    clear_form()
    if all([customer_id,first_name,last_name,email,phone,state,purchase_amount]):
        if email_validation(email) and phone_number_validation(phone):
            conn = connect()
            cur = conn.cursor()
            cur.execute("INSERT INTO customer_data (first_name, last_name, email, phone, state, purchase_amount) VALUES (?, ?, ?, ?, ?, ?)",(first_name, last_name, email, phone, state, purchase_amount))
            conn.commit()
            conn.close()
            load_data()
            messagebox.showinfo("Record Added","The record has been added successfully.")
    else:
        messagebox.showerror("Error","All fields are required..!")


def update_record():
    """Updates data in the database for selected record"""
    selected = table.selection()
    if selected:
        customer_id = customerid_entry.get()
        first_name = firstname_entry.get()
        last_name = lastname_entry.get()
        email = email_entry.get()
        phone = phonenumber_entry.get()
        state = state_entry.get()
        purchase_amount = purchaseamt_entry.get()
        conn = connect()
        cur = conn.cursor()
        cur.execute("UPDATE customer_data SET first_name=?, last_name=?, email=?, phone=?, state=?, purchase_amount=? WHERE customer_id=?",(first_name, last_name, email, phone, state, purchase_amount,customer_id))
        conn.commit()
        conn.close()
        clear_form(action='add')
        load_data()
        messagebox.showinfo("Record Updated","The record has been updated successfully.")
    else:
        messagebox.showerror("Error", "No record selected.")


def delete_record():
    """Deletes the record from database"""
    selected = table.selection()
    if selected:
        confirmation = messagebox.askyesno("Confirmation", "Are you sure you want to delete the record?")
        if confirmation:
            conn = connect()
            cur = conn.cursor()
            cur.execute("DELETE  FROM customer_data WHERE customer_id=?",(customerid_entry.get(),))
            conn.commit()
            conn.close()
            clear_form()
            load_data()
            messagebox.showinfo("Record Deleted","The record has been deleted successfully.")
    else:
        messagebox.showerror("Error", "No record selected.")


def search_record():
    """Search record based on customer id"""
    customerid = search_entry.get()
    if customerid:
        found = []
        for item in table.get_children():
            values = table.item(item)['values']
            if customerid.lower() in [str(value).lower() for value in values]:
                found.append(item)
        table.selection_set(found)
        if found:
            table.selection_add(found)
            table.focus(found)             
            messagebox.showinfo("Search Results", f"Found {len(found)} record(s) matching the search criteria.")
        else:
            messagebox.showinfo("Search Results", "No records found.")
    else:
        messagebox.showerror("Error", "Please enter search criteria.")


# Main GUI Window
window = tk.Tk()
window.geometry("1350x700")
window.title("Customer Database Management System")
window.iconbitmap("images/icon.ico")

#GUI heading title 
heading_title = tk.Label(window,text="Customer Database Management System",font=("arial",30,"bold"),bg="gray90",relief=tk.GROOVE)
heading_title.pack(fill=tk.X)

# Customer data Treeview
table = ttk.Treeview(window)
scrollbar_v = tk.Scrollbar(table, orient='vertical',command=table.yview)
scrollbar_v.pack(side=tk.RIGHT, fill='y')
table.configure(yscrollcommand=scrollbar_v.set)

table["columns"] = ('customer_id', 'first_name', 'last_name', 'email','phone_number','state','purchase_amount')
table.column('#0',width=0,stretch=tk.NO)
table.column("customer_id", width=100 ,anchor=tk.CENTER)
table.column("first_name", width=100,anchor=tk.CENTER)
table.column("last_name", width=100,anchor=tk.CENTER)
table.column("email", width=100,anchor=tk.CENTER)
table.column("phone_number", width=100,anchor=tk.CENTER)
table.column("state", width=100,anchor=tk.CENTER)
table.column("purchase_amount", width=100,anchor=tk.CENTER)

table.heading("customer_id", text="Customer ID",anchor=tk.CENTER)
table.heading("first_name", text="First Name",anchor=tk.CENTER)
table.heading("last_name", text="Last Name",anchor=tk.CENTER)
table.heading("email", text="Email",anchor=tk.CENTER)
table.heading("phone_number", text="Phone",anchor=tk.CENTER)
table.heading("state", text="State",anchor=tk.CENTER)
table.heading("purchase_amount",text="Purchase Amount",anchor=tk.CENTER)

table.pack(fill="both", expand=True)

# Customer Details Frame
customer_details_frame = tk.LabelFrame(window,text="Customer Details",font=("arial",20,"bold"))
customer_details_frame.pack(pady=20)

customerid_label = tk.Label(customer_details_frame,text="Customer ID",font=("arial",10,"bold"))
customerid_label.grid(row=0,column=0,padx=10,pady=2)
customerid_entry = tk.Entry(customer_details_frame,font=("arial",25))
customerid_entry.grid(row=0,column=1,padx=8,pady=8)

firstname_label = tk.Label(customer_details_frame,text="First Name",font=("arial",10,"bold"))
firstname_label.grid(row=0,column=2,padx=20,pady=2)
firstname_entry = tk.Entry(customer_details_frame,font=("arial",25))
firstname_entry.grid(row=0,column=3,padx=8,pady=8)

lastname_label = tk.Label(customer_details_frame,text="Last Name",font=("arial",10,"bold"))
lastname_label.grid(row=0,column=4,padx=20,pady=2)
lastname_entry = tk.Entry(customer_details_frame,font=("arial",25))
lastname_entry.grid(row=0,column=5,padx=8,pady=8)

email_label = tk.Label(customer_details_frame,text="Email",font=("arial",10,"bold"))
email_label.grid(row=1,column=0,padx=20,pady=2)
email_entry = tk.Entry(customer_details_frame,font=("arial",25))
email_entry.grid(row=1,column=1,padx=8,pady=8)

phonenumber_label = tk.Label(customer_details_frame,text="Phone Number",font=("arial",10,"bold"))
phonenumber_label.grid(row=1,column=2,padx=20,pady=2)
phonenumber_entry = tk.Entry(customer_details_frame,font=("arial",25))
phonenumber_entry.grid(row=1,column=3,padx=8,pady=8)

state_label = tk.Label(customer_details_frame,text="State",font=("arial",10,"bold"))
state_label.grid(row=1,column=4,padx=20,pady=2)
state_entry = tk.Entry(customer_details_frame,font=("arial",25))
state_entry.grid(row=1,column=5,padx=8,pady=8)

purchaseamt_label = tk.Label(customer_details_frame,text="Purchase Amount",font=("arial",10,"bold"))
purchaseamt_label.grid(row=2,column=0,padx=20,pady=2)
purchaseamt_entry = tk.Entry(customer_details_frame,font=("arial",25))
purchaseamt_entry.grid(row=2,column=1,padx=8,pady=8)

button_add = tk.Button(customer_details_frame,text="Add Record",width=15, height=2, bg='#0052cc', fg='#ffffff', activebackground='#0052cc', activeforeground='#aaffaa',command=add_record)
button_add.grid(row=2,column=2,padx=10,pady=10)

button_update = tk.Button(customer_details_frame,text="Update Record",width=15, height=2, bg='#0052cc', fg='#ffffff', activebackground='#0052cc', activeforeground='#aaffaa',command=update_record)
button_update.grid(row=2,column=3,padx=10,pady=10)

button_delete = tk.Button(customer_details_frame,text="Delete Record",width=15, height=2, bg='#0052cc', fg='#ffffff', activebackground='#0052cc', activeforeground='#aaffaa',command=delete_record)
button_delete.grid(row=2,column=4,padx=10,pady=10)

search_label = tk.Label(customer_details_frame,text="Search Customer",font=("arial",10,"bold"))
search_label.grid(row=4,column=0,padx=20,pady=2)
search_entry = tk.Entry(customer_details_frame,font=("arial",25))

search_entry.grid(row=4,column=1,padx=8,pady=8)
button_search = tk.Button(customer_details_frame,text="Search",width=15, height=2,command=search_record)
button_search.grid(row=4,column=2,padx=10,pady=10)

button_download = tk.Button(customer_details_frame,text="Download All Data",width=15, height=2,command=lambda:download_data(table))
button_download.grid(row=4,column=3,padx=10,pady=10)

button_clear_form = tk.Button(customer_details_frame,text="Clear Form",width=15, height=2, bg='#0052cc', fg='#ffffff', activebackground='#0052cc', activeforeground='#aaffaa',command=clear_form)
button_clear_form.grid(row=4,column=4,padx=10,pady=10)

# Stats details frame
stat_details_frame = tk.LabelFrame(window,text="Stats",font=("arial",20,"bold"))
stat_details_frame.pack(pady=20)

total_customers_label = tk.Label(stat_details_frame,text="Total Customers in",font=("arial",10,"bold"))
total_customers_label.grid(row=0,column=0,padx=10,pady=2)
total_customers_entry = tk.Entry(stat_details_frame,font=("arial",25))
total_customers_entry.config(state="normal")
total_customers_entry.grid(row=0,column=1,padx=8,pady=8)

average_purchace_label = tk.Label(stat_details_frame,text="Average Purchace:",font=("arial",10,"bold"))
average_purchace_label.grid(row=0,column=2,padx=10,pady=2)
average_purchace_entry = tk.Entry(stat_details_frame,font=("arial",25))
average_purchace_entry.grid(row=0,column=3,padx=8,pady=8)

button_download = tk.Button(stat_details_frame,text="Download Segment Data",width=25, height=2,command=lambda:download_data(stats_table))
button_download.grid(row=1,column=1,padx=20,pady=20)

# Customer segment Treeview
stats_table = ttk.Treeview(window)
scrollbar_v = tk.Scrollbar(stats_table, orient='vertical',command=stats_table.yview)
scrollbar_v.pack(side=tk.RIGHT, fill='y')
stats_table.configure(yscrollcommand=scrollbar_v.set)

stats_table["columns"] = ("customer_id", "full_name","state","segment_category")
stats_table.column('#0',width=0,stretch=tk.NO)
stats_table.column("customer_id", width=100 ,anchor=tk.CENTER)
stats_table.column("full_name", width=100,anchor=tk.CENTER)
stats_table.column("state", width=100,anchor=tk.CENTER)
stats_table.column("segment_category", width=100,anchor=tk.CENTER)

stats_table.heading("customer_id", text="Customer ID",anchor=tk.CENTER)
stats_table.heading("full_name", text="Full Name",anchor=tk.CENTER)
stats_table.heading("state", text="State",anchor=tk.CENTER)
stats_table.heading("segment_category", text="Segment",anchor=tk.CENTER)

stats_table.pack(fill="both", expand=True)

load_data()
table.bind("<<TreeviewSelect>>",on_select)

window.mainloop()