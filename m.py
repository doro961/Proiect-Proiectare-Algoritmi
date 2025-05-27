import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import smtplib
from email.mime.text import MIMEText
import webbrowser
import sqlite3
import os
import cv2
import time
class ContactManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Contact Manager")

        self.contacts = []
        self.selected_contact_index = None
        self.selected_image_path = None

        self.conn = sqlite3.connect("contacts.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY,
                name TEXT,
                phone TEXT,
                address TEXT,
                email TEXT,
                image TEXT
            )
        """)
        self.conn.commit()

        top_frame = tk.Frame(root)
        top_frame.grid(row=0, column=0, sticky="ew")

        self.image_label = tk.Label(top_frame)
        self.image_label.grid(row=0, column=0, rowspan=5, padx=10, pady=10)

        self.upload_button = ttk.Button(top_frame, text="Select Image", command=self.select_image)
        self.upload_button.grid(row=5, column=0, padx=10, pady=2)

        self.capture_button = ttk.Button(top_frame, text="Capture Image", command=self.capture_image)
        self.capture_button.grid(row=6, column=0, padx=10, pady=2)

        self.name_entry = ttk.Entry(top_frame)
        self.phone_entry = ttk.Entry(top_frame)
        self.address_entry = ttk.Entry(top_frame)
        self.email_entry = ttk.Entry(top_frame)

        ttk.Label(top_frame, text="Name:").grid(row=0, column=1, sticky="w")
        self.name_entry.grid(row=0, column=2, sticky="ew", padx=5)

        ttk.Label(top_frame, text="Phone:").grid(row=1, column=1, sticky="w")
        self.phone_entry.grid(row=1, column=2, sticky="ew", padx=5)

        ttk.Label(top_frame, text="Address:").grid(row=2, column=1, sticky="w")
        self.address_entry.grid(row=2, column=2, sticky="ew", padx=5)

        ttk.Label(top_frame, text="Email:").grid(row=3, column=1, sticky="w")
        self.email_entry.grid(row=3, column=2, sticky="ew", padx=5)

        ttk.Label(top_frame, text="Search:").grid(row=4, column=1, sticky="w")
        self.search_entry = ttk.Entry(top_frame)
        self.search_entry.grid(row=4, column=2, sticky="ew", padx=5)
        self.search_entry.bind("<KeyRelease>", self.search_contacts)

        top_frame.columnconfigure(2, weight=1)

        btn_frame = tk.Frame(root)
        btn_frame.grid(row=1, column=0, sticky="ew", pady=5)

        ttk.Button(btn_frame, text="Add", command=self.add_contact).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Edit", command=self.edit_contact).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete", command=self.delete_contact).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Email", command=self.send_email).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="WhatsApp", command=self.send_whatsapp).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Telegram", command=self.send_telegram).pack(side="left", padx=5)

        self.contact_listbox = tk.Listbox(root)
        self.contact_listbox.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.contact_listbox.bind("<<ListboxSelect>>", self.on_contact_select)

        root.rowconfigure(2, weight=1)
        root.columnconfigure(0, weight=1)

        self.load_contacts()

    def select_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png *.jpeg *.gif")])
        if path:
            self.selected_image_path = path
            self.show_image(path)

    def capture_image(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error", "Camera nu a putut fi deschisă.")
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            cv2.imshow("Capture Image - Apasă 'c' pentru captură, 'q' pentru ieșire", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('c'):
                timestamp = int(time.time())
                name = self.name_entry.get().strip().replace(" ", "_") or "contact"
                os.makedirs("images", exist_ok=True)
                filename = f"images/{name}_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                self.selected_image_path = filename
                self.show_image(filename)
                break
            elif key == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    def show_image(self, path):
        try:
            image = Image.open(path)
            image = image.resize((100, 100))
            photo = ImageTk.PhotoImage(image)
            self.image_label.configure(image=photo)
            self.image_label.image = photo
        except Exception as e:
            print(f"Eroare imagine: {e}")

    def add_contact(self):
        name = self.name_entry.get()
        phone = self.phone_entry.get()
        address = self.address_entry.get()
        email = self.email_entry.get()
        image = self.selected_image_path

        if name:
            self.cursor.execute("INSERT INTO contacts (name, phone, address, email, image) VALUES (?, ?, ?, ?, ?)",
                                (name, phone, address, email, image))
            self.conn.commit()
            self.load_contacts()
            self.clear_fields()
        else:
            messagebox.showerror("Error", "Name is required.")

    def edit_contact(self):
        if self.selected_contact_index is not None:
            contact = self.contacts[self.selected_contact_index]
            new_data = (self.name_entry.get(), self.phone_entry.get(), self.address_entry.get(),
                        self.email_entry.get(), self.selected_image_path, contact['id'])
            self.cursor.execute("""
                UPDATE contacts SET name=?, phone=?, address=?, email=?, image=? WHERE id=?
            """, new_data)
            self.conn.commit()
            self.load_contacts()
            self.clear_fields()
        else:
            messagebox.showerror("Error", "No contact selected.")

    def delete_contact(self):
        if self.selected_contact_index is not None:
            contact = self.contacts[self.selected_contact_index]
            self.cursor.execute("DELETE FROM contacts WHERE id=?", (contact['id'],))
            self.conn.commit()
            self.load_contacts()
            self.clear_fields()
        else:
            messagebox.showerror("Error", "No contact selected.")

    def send_email(self):
        if self.selected_contact_index is not None:
            contact = self.contacts[self.selected_contact_index]
            recipient_email = contact['email']
            subject = f"Contact Details: {contact['name']}"
            body = f"Name: {contact['name']}\nPhone: {contact['phone']}\nAddress: {contact['address']}\nEmail: {contact['email']}"

            msg = MIMEText(body)
            msg['Subject'] = subject
            sender_email = "dalexandrustefan961@gmail.com"
            sender_password = "ibrs cuwp inlr szzb"

            try:
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, recipient_email, msg.as_string())
                messagebox.showinfo("Success", f"Email sent to {recipient_email}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def send_whatsapp(self):
        if self.selected_contact_index is not None:
            contact = self.contacts[self.selected_contact_index]
            phone = contact['phone'].replace("+", "").replace(" ", "")
            message = f"Name: {contact['name']}\nPhone: {contact['phone']}\nAddress: {contact['address']}\nEmail: {contact['email']}"
            url = f"https://wa.me/{phone}?text={message}"
            webbrowser.open(url)

    def send_telegram(self):
        if self.selected_contact_index is not None:
            contact = self.contacts[self.selected_contact_index]
            message = f"Nume: {contact['name']}\nTelefon: {contact['phone']}\nAdresă: {contact['address']}\nEmail: {contact['email']}"
            bot_token = "7411224762:AAH6xuxGusgl2bEav_1wnoTBJoUusLAX3iw"
            chat_id = "5330195126"
            telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}"
            webbrowser.open(telegram_url)
            messagebox.showinfo("Telegram", f"Mesaj trimis către chat-ul {chat_id}.")
        else:
            messagebox.showerror("Error", "Niciun contact selectat pentru Telegram.")

    def search_contacts(self, event):
        search_term = self.search_entry.get().lower()
        self.contacts.clear()
        self.contact_listbox.delete(0, tk.END)
        self.cursor.execute("SELECT * FROM contacts")
        for row in self.cursor.fetchall():
            contact = {
                "id": row[0],
                "name": row[1],
                "phone": row[2],
                "address": row[3],
                "email": row[4],
                "image": row[5]
            }
            if search_term in contact['name'].lower() or search_term in contact['phone']:
                self.contacts.append(contact)
                self.contact_listbox.insert(tk.END, contact['name'])

    def load_contacts(self):
        self.contacts.clear()
        self.contact_listbox.delete(0, tk.END)
        self.cursor.execute("SELECT * FROM contacts")
        for row in self.cursor.fetchall():
            contact = {
                "id": row[0],
                "name": row[1],
                "phone": row[2],
                "address": row[3],
                "email": row[4],
                "image": row[5]
            }
            self.contacts.append(contact)
            self.contact_listbox.insert(tk.END, contact['name'])

    def on_contact_select(self, event):
        try:
            index = self.contact_listbox.curselection()[0]
            self.selected_contact_index = index
            contact = self.contacts[index]

            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, contact['name'])

            self.phone_entry.delete(0, tk.END)
            self.phone_entry.insert(0, contact['phone'])

            self.address_entry.delete(0, tk.END)
            self.address_entry.insert(0, contact['address'])

            self.email_entry.delete(0, tk.END)
            self.email_entry.insert(0, contact['email'])

            self.selected_image_path = contact['image']
            if contact['image']:
                self.show_image(contact['image'])
            else:
                self.image_label.config(image='')

        except IndexError:
            pass

    def clear_fields(self):
        self.name_entry.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        self.address_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)
        self.selected_image_path = None
        self.image_label.config(image='')
        self.image_label.image = None
        self.selected_contact_index = None

if __name__ == "__main__":
    root = tk.Tk()
    app = ContactManager(root)
    root.mainloop()