# from tkinter import *
from  customtkinter import *
from CTkListbox import *
# from tkinter import ttk
# import snoop

def accept_license(select_option):
    global var_acc
    for i in login_all:
        if i[0] == select_option:
            var_acc = i[1]
            break
    root.destroy()


def intetface(acc_s: list):
    global root, var_acc, login_all

    var_acc = -1
    root = CTk()
    root.title("Выбор аккаунта")
    root.geometry("170x600")

    login_all = []
    s = 0
    for i in acc_s:
        login_all.append((i[1], s))
        s += 1


    acc_listbox = CTkListbox(root, command=accept_license)

    acc_listbox.pack(fill="both", expand=True, padx=10, pady=10)

    for i in login_all:
        acc_listbox.insert(END, i[0])

    root.mainloop()

def get_num_acc(acc_s: list):
    global root, var_acc
    intetface(acc_s)
    return var_acc