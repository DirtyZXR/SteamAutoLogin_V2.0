from customtkinter import CTk, CTkButton
from CTkListbox import CTkListbox


def select_account(accounts: list[tuple]) -> int:
    result = -1

    def on_select(option):
        nonlocal result
        for i, acc in enumerate(accounts):
            if i == option:
                result = option
                break
        root.destroy()

    root = CTk()
    root.title("Выбор аккаунта")
    root.geometry("250x500")

    listbox = CTkListbox(root, command=on_select)
    listbox.pack(fill="both", expand=True, padx=10, pady=10)

    for acc in accounts:
        listbox.insert("END", acc[1])

    root.mainloop()
    return result
