import customtkinter as ctk
import requests
import json
import os
import subprocess
import uuid
from tkinter import simpledialog, messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

APP_FILE = "saved_key.json"
SERVER_URL = "https://ds4-server.onrender.com/verify"
DS4_PATH = r"C:\Users\arthu\OneDrive\Desktop\DS4 IA\dswindows.bat"

current_key = None
license_valid = False

app = ctk.CTk()
app.title("DS4 IA")
app.geometry("520x760")
app.resizable(False, False)


def get_hwid():
    return str(uuid.getnode())


def save_key(key):
    with open(APP_FILE, "w", encoding="utf-8") as f:
        json.dump({"key": key}, f)


def load_key():
    if not os.path.exists(APP_FILE):
        return None
    try:
        with open(APP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("key")
    except Exception:
        return None


def clear_key():
    global current_key, license_valid
    current_key = None
    license_valid = False

    if os.path.exists(APP_FILE):
        os.remove(APP_FILE)

    key_label.configure(text="Clé : Non définie")
    sub_label.configure(text="Abonnement : Aucun")
    time_value_label.configure(text="Aucun")
    exp_value_label.configure(text="Non définie")
    abo_value_label.configure(text="Aucun")
    login_value_label.configure(text="Jamais")
    user_value_label.configure(text="Non défini")
    launch_btn.configure(state="disabled")


def verify_key(key):
    try:
        r = requests.post(
            SERVER_URL,
            json={
                "key": key,
                "hwid": get_hwid()
            },
            timeout=15
        )
        return r.json()
    except Exception:
        return {"valid": False, "reason": "server_error"}


def apply_license_data(key, data):
    global current_key, license_valid
    current_key = key
    license_valid = True

    key_label.configure(text=f"Clé : {key}")
    sub_label.configure(text=f"Abonnement : {data.get('subscription', 'Aucun')}")
    time_value_label.configure(text=data.get("time_left", "Aucun"))
    exp_value_label.configure(text=data.get("expires_at", "Non définie"))
    abo_value_label.configure(text=data.get("subscription", "Aucun"))
    login_value_label.configure(text=data.get("last_login", "Jamais"))
    user_value_label.configure(text=data.get("username", "Non défini"))
    launch_btn.configure(state="normal")


def ask_new_key():
    key = simpledialog.askstring("Clé de licence", "Entre ta clé :")
    if not key:
        return

    result = verify_key(key)

    if result.get("valid"):
        save_key(key)
        apply_license_data(key, result)
        messagebox.showinfo("Succès", "Clé valide.")
    else:
        clear_key()
        reason = result.get("reason", "invalid_key")

        if reason == "already_used_on_other_pc":
            messagebox.showerror("Erreur", "Cette clé est déjà utilisée sur un autre PC.")
        elif reason == "expired":
            messagebox.showerror("Erreur", "Cette clé a expiré.")
        elif reason == "disabled":
            messagebox.showerror("Erreur", "Cette clé a été désactivée.")
        elif reason == "missing_data":
            messagebox.showerror("Erreur", "Données manquantes.")
        elif reason == "server_error":
            messagebox.showerror("Erreur", "Serveur inaccessible.")
        else:
            messagebox.showerror("Erreur", "Clé invalide.")


def launch_ds4():
    if not license_valid:
        messagebox.showerror("Erreur", "Aucune licence valide.")
        return

    if not os.path.exists(DS4_PATH):
        messagebox.showerror("Erreur", f"Fichier introuvable : {DS4_PATH}")
        return

    try:
        ds4_folder = os.path.dirname(DS4_PATH)
        subprocess.Popen(DS4_PATH, cwd=ds4_folder, shell=True)
        app.destroy()
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de lancer le fichier :\n{e}")


main = ctk.CTkFrame(app, fg_color="#0b0b12", corner_radius=15)
main.pack(fill="both", expand=True, padx=20, pady=20)

title = ctk.CTkLabel(main, text="DS4 IA", font=("Arial", 24, "bold"))
title.pack(pady=(20, 10))

key_label = ctk.CTkLabel(main, text="Clé : Non définie", font=("Arial", 16, "bold"))
key_label.pack(pady=(10, 5))

sub_label = ctk.CTkLabel(main, text="Abonnement : Aucun")
sub_label.pack(pady=(0, 20))

time_frame = ctk.CTkFrame(main)
time_frame.pack(fill="x", padx=20, pady=10)

ctk.CTkLabel(time_frame, text="TEMPS RESTANT").pack(anchor="w", padx=15, pady=(15, 5))

time_value_label = ctk.CTkLabel(time_frame, text="Aucun", font=("Arial", 28, "bold"))
time_value_label.pack(anchor="w", padx=15, pady=(0, 15))

grid = ctk.CTkFrame(main)
grid.pack(fill="x", padx=20, pady=10)

box1 = ctk.CTkFrame(grid)
box1.grid(row=0, column=0, padx=5, pady=5)

box2 = ctk.CTkFrame(grid)
box2.grid(row=0, column=1, padx=5, pady=5)

box3 = ctk.CTkFrame(grid)
box3.grid(row=1, column=0, padx=5, pady=5)

box4 = ctk.CTkFrame(grid)
box4.grid(row=1, column=1, padx=5, pady=5)

exp_value_label = ctk.CTkLabel(box1, text="Non définie")
exp_value_label.pack(padx=20, pady=20)

abo_value_label = ctk.CTkLabel(box2, text="Aucun")
abo_value_label.pack(padx=20, pady=20)

login_value_label = ctk.CTkLabel(box3, text="Jamais")
login_value_label.pack(padx=20, pady=20)

user_value_label = ctk.CTkLabel(box4, text="Non défini")
user_value_label.pack(padx=20, pady=20)

launch_btn = ctk.CTkButton(
    main,
    text="▶ Lancer DS4 IA",
    command=launch_ds4,
    state="disabled"
)
launch_btn.pack(fill="x", padx=20, pady=20)

change_key_btn = ctk.CTkButton(
    main,
    text="🔑 Changer de clé",
    command=ask_new_key
)
change_key_btn.pack(fill="x", padx=20, pady=10)

remove_key_btn = ctk.CTkButton(
    main,
    text="🗑 Supprimer la clé",
    command=clear_key
)
remove_key_btn.pack(fill="x", padx=20, pady=10)

saved = load_key()
if saved:
    result = verify_key(saved)
    if result.get("valid"):
        apply_license_data(saved, result)
    else:
        clear_key()
        app.after(500, ask_new_key)
else:
    app.after(500, ask_new_key)

app.mainloop()import customtkinter as ctk
import requests
import json
import os
import subprocess
import uuid
from tkinter import simpledialog, messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

APP_FILE = "saved_key.json"
SERVER_URL = "https://ds4-server.onrender.com/verify"
DS4_PATH = r"C:\Users\arthu\OneDrive\Desktop\DS4 IA\dswindows.bat"

current_key = None
license_valid = False

app = ctk.CTk()
app.title("DS4 IA")
app.geometry("520x760")
app.resizable(False, False)


def get_hwid():
    return str(uuid.getnode())


def save_key(key):
    with open(APP_FILE, "w", encoding="utf-8") as f:
        json.dump({"key": key}, f)


def load_key():
    if not os.path.exists(APP_FILE):
        return None
    try:
        with open(APP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("key")
    except Exception:
        return None


def clear_key():
    global current_key, license_valid
    current_key = None
    license_valid = False

    if os.path.exists(APP_FILE):
        os.remove(APP_FILE)

    key_label.configure(text="Clé : Non définie")
    sub_label.configure(text="Abonnement : Aucun")
    time_value_label.configure(text="Aucun")
    exp_value_label.configure(text="Non définie")
    abo_value_label.configure(text="Aucun")
    login_value_label.configure(text="Jamais")
    user_value_label.configure(text="Non défini")
    launch_btn.configure(state="disabled")


def verify_key(key):
    try:
        r = requests.post(
            SERVER_URL,
            json={
                "key": key,
                "hwid": get_hwid()
            },
            timeout=15
        )
        return r.json()
    except Exception:
        return {"valid": False, "reason": "server_error"}


def apply_license_data(key, data):
    global current_key, license_valid
    current_key = key
    license_valid = True

    key_label.configure(text=f"Clé : {key}")
    sub_label.configure(text=f"Abonnement : {data.get('subscription', 'Aucun')}")
    time_value_label.configure(text=data.get("time_left", "Aucun"))
    exp_value_label.configure(text=data.get("expires_at", "Non définie"))
    abo_value_label.configure(text=data.get("subscription", "Aucun"))
    login_value_label.configure(text=data.get("last_login", "Jamais"))
    user_value_label.configure(text=data.get("username", "Non défini"))
    launch_btn.configure(state="normal")


def ask_new_key():
    key = simpledialog.askstring("Clé de licence", "Entre ta clé :")
    if not key:
        return

    result = verify_key(key)

    if result.get("valid"):
        save_key(key)
        apply_license_data(key, result)
        messagebox.showinfo("Succès", "Clé valide.")
    else:
        clear_key()
        reason = result.get("reason", "invalid_key")

        if reason == "already_used_on_other_pc":
            messagebox.showerror("Erreur", "Cette clé est déjà utilisée sur un autre PC.")
        elif reason == "expired":
            messagebox.showerror("Erreur", "Cette clé a expiré.")
        elif reason == "disabled":
            messagebox.showerror("Erreur", "Cette clé a été désactivée.")
        elif reason == "missing_data":
            messagebox.showerror("Erreur", "Données manquantes.")
        elif reason == "server_error":
            messagebox.showerror("Erreur", "Serveur inaccessible.")
        else:
            messagebox.showerror("Erreur", "Clé invalide.")


def launch_ds4():
    if not license_valid:
        messagebox.showerror("Erreur", "Aucune licence valide.")
        return

    if not os.path.exists(DS4_PATH):
        messagebox.showerror("Erreur", f"Fichier introuvable : {DS4_PATH}")
        return

    try:
        ds4_folder = os.path.dirname(DS4_PATH)
        subprocess.Popen(DS4_PATH, cwd=ds4_folder, shell=True)
        app.destroy()
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de lancer le fichier :\n{e}")


main = ctk.CTkFrame(app, fg_color="#0b0b12", corner_radius=15)
main.pack(fill="both", expand=True, padx=20, pady=20)

title = ctk.CTkLabel(main, text="DS4 IA", font=("Arial", 24, "bold"))
title.pack(pady=(20, 10))

key_label = ctk.CTkLabel(main, text="Clé : Non définie", font=("Arial", 16, "bold"))
key_label.pack(pady=(10, 5))

sub_label = ctk.CTkLabel(main, text="Abonnement : Aucun")
sub_label.pack(pady=(0, 20))

time_frame = ctk.CTkFrame(main)
time_frame.pack(fill="x", padx=20, pady=10)

ctk.CTkLabel(time_frame, text="TEMPS RESTANT").pack(anchor="w", padx=15, pady=(15, 5))

time_value_label = ctk.CTkLabel(time_frame, text="Aucun", font=("Arial", 28, "bold"))
time_value_label.pack(anchor="w", padx=15, pady=(0, 15))

grid = ctk.CTkFrame(main)
grid.pack(fill="x", padx=20, pady=10)

box1 = ctk.CTkFrame(grid)
box1.grid(row=0, column=0, padx=5, pady=5)

box2 = ctk.CTkFrame(grid)
box2.grid(row=0, column=1, padx=5, pady=5)

box3 = ctk.CTkFrame(grid)
box3.grid(row=1, column=0, padx=5, pady=5)

box4 = ctk.CTkFrame(grid)
box4.grid(row=1, column=1, padx=5, pady=5)

exp_value_label = ctk.CTkLabel(box1, text="Non définie")
exp_value_label.pack(padx=20, pady=20)

abo_value_label = ctk.CTkLabel(box2, text="Aucun")
abo_value_label.pack(padx=20, pady=20)

login_value_label = ctk.CTkLabel(box3, text="Jamais")
login_value_label.pack(padx=20, pady=20)

user_value_label = ctk.CTkLabel(box4, text="Non défini")
user_value_label.pack(padx=20, pady=20)

launch_btn = ctk.CTkButton(
    main,
    text="▶ Lancer DS4 IA",
    command=launch_ds4,
    state="disabled"
)
launch_btn.pack(fill="x", padx=20, pady=20)

change_key_btn = ctk.CTkButton(
    main,
    text="🔑 Changer de clé",
    command=ask_new_key
)
change_key_btn.pack(fill="x", padx=20, pady=10)

remove_key_btn = ctk.CTkButton(
    main,
    text="🗑 Supprimer la clé",
    command=clear_key
)
remove_key_btn.pack(fill="x", padx=20, pady=10)

saved = load_key()
if saved:
    result = verify_key(saved)
    if result.get("valid"):
        apply_license_data(saved, result)
    else:
        clear_key()
        app.after(500, ask_new_key)
else:
    app.after(500, ask_new_key)

app.mainloop()