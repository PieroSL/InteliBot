import mysql.connector
import getpass
import re
import random
import datetime
import tkinter as tk
from tkinter import simpledialog, messagebox
from tkinter.scrolledtext import ScrolledText


def get_response(user_input):
    split_message = re.split(r'\s|[,:;.?!-_]\s*', user_input.lower())
    response = check_all_messages(split_message)
    return response

def message_probability(user_message, recognized_words, single_response=False, required_word=[]):
    message_certainty = 0
    has_required_words = True

    for word in user_message:
        if word in recognized_words:
            message_certainty +=1

    percentage = float(message_certainty) / float (len(recognized_words))

    for word in required_word:
        if word not in user_message:
            has_required_words = False  
            break
    if has_required_words or single_response:
        return int(percentage * 100)
    else:
        return 0

def check_all_messages(message):
    highest_prob = {}
    
    connection = mysql.connector.connect(host='localhost',
                                         database='bd_certus',
                                         user='root',
                                         password='4740545Manzana')
    cursor = connection.cursor()
    cursor.execute("SELECT id, respuesta, palabra_clave FROM tb_respuestas")
    all_responses = cursor.fetchall()

    for row in all_responses:
        respuesta_id = row[0]
        respuesta_text = row[1]
        palabra_clave_list = row[2].split(",") if row[2] else []

        highest_prob[respuesta_text] = message_probability(message, palabra_clave_list)

    best_match = max(highest_prob, key=highest_prob.get)

    return unknown() if highest_prob[best_match] < 1 else best_match


def unknown():
    response = ['no entendi tu consulta', 'No estoy seguro de lo quieres', 'Disculpa, puedes intentarlo de nuevo?'][random.randrange(3)]
    return response

###############################################################################################################

def login_window():
    def attempt_login():
        user = user_entry.get()
        password = pass_entry.get()

        try:
            connection = mysql.connector.connect(host='localhost', database='bd_certus', user='root', password='4740545Manzana')
            sql_select_Query = "select * from t_estudiantes where cod_estudiante=%s and con_estudiante=%s"
            cursor = connection.cursor()
            cursor.execute(sql_select_Query, (user, password))
            records = cursor.fetchall()
            rp = cursor.rowcount

            if(rp == 1):
                messagebox.showinfo("Info", "Inicio de sesión exitoso!")
                login.destroy()  # Cerramos la ventana de inicio de sesión
                id_estudiante = user  # Asegúrate de que esta es la forma correcta de obtener el ID del estudiante
                chat_window(id_estudiante)  # Pasamos el ID del estudiante a chat_window

            else:
                messagebox.showwarning("Advertencia", "Error en las credenciales")

        except mysql.connector.Error as e:
            messagebox.showerror("Error", "Error en la consulta")

    # Ventana de inicio de sesión
    login = tk.Tk()
    login.title("Inicio de Sesión")

    # Establecer fondo que cubre toda la pantalla
    main_frame = tk.Frame(login, bg='white')
    main_frame.pack(fill='both', expand=True)

    # Agregar una imagen
    image = tk.PhotoImage(file="img/chatbot1.png    ")  # Asegúrate de que la ruta y el nombre de archivo sean correctos
    image_label = tk.Label(main_frame, image=image, bg='light blue')
    image_label.grid(row=0, column=0, columnspan=2, pady=20)

    # Mejoras en los campos de texto y botones
    tk.Label(main_frame, text="Usuario:", bg='white', font=("Arial", 12)).grid(row=1, column=0, sticky="e", pady=5)
    tk.Label(main_frame, text="Contraseña:", bg='white', font=("Arial", 12)).grid(row=2, column=0, sticky="e", pady=5)

    # Campos de texto con 'bordes' redondeados
    user_frame = tk.Frame(main_frame, bg='white', borderwidth=2, relief="groove")
    user_frame.grid(row=1, column=1, pady=20, padx=50)
    user_entry = tk.Entry(user_frame, font=("Arial", 12))
    user_entry.pack(padx=5, pady=5)

    pass_frame = tk.Frame(main_frame, bg='white', borderwidth=2, relief="groove")
    pass_frame.grid(row=2, column=1, pady=20, padx=50)
    pass_entry = tk.Entry(pass_frame, show="*", font=("Arial", 12))
    pass_entry.pack(padx=5, pady=5)

    login_button = tk.Button(main_frame, text="Iniciar Sesión", command=attempt_login, bg='#4CAF50', fg='white', font=("Arial", 12))
    login_button.grid(row=3, column=0, columnspan=2, pady=20)

    login.mainloop()


#####################################################################################################################


def guardar_historial(id_estudiante, mensaje, respuesta):
    connection = mysql.connector.connect(host='localhost', database='bd_certus', user='root', password='4740545Manzana')
    cursor = connection.cursor()        
    sql = "INSERT INTO t_historial (id_estudiante, mensaje, respuesta) VALUES (%s, %s, %s)"
    cursor.execute(sql, (id_estudiante, mensaje, respuesta))
    connection.commit()
    cursor.close()
    connection.close()

def cargar_historial(id_estudiante):
    mensajes = []
    connection = mysql.connector.connect(host='localhost', database='bd_certus', user='root', password='4740545Manzana')
    cursor = connection.cursor()
    sql = "SELECT mensaje, respuesta FROM t_historial WHERE id_estudiante = %s"
    cursor.execute(sql, (id_estudiante,))
    for mensaje, respuesta in cursor.fetchall():
        mensajes.append({"mensaje": mensaje, "respuesta": respuesta})
    cursor.close()
    connection.close()
    return mensajes

def eliminar_historial_bd(id_estudiante):
    connection = mysql.connector.connect(host='localhost', database='bd_certus', user='root', password='4740545Manzana')
    cursor = connection.cursor()
    sql = "DELETE FROM t_historial WHERE id_estudiante = %s"
    cursor.execute(sql, (id_estudiante,))
    connection.commit()
    cursor.close()
    connection.close()


def chat_window(id_estudiante):

    chat_win = tk.Tk()
    chat_win.title("InteliChat")

    # Variable para rastrear si el historial está siendo mostrado
    esta_mostrando_historial = False

    placeholder = "Escribe tu mensaje"

    def on_entry_click(event):
        """Función para borrar el marcador de posición al hacer clic."""
        if user_input.get() == placeholder:
            user_input.delete(0, tk.END)
            user_input.config(fg='black')

    def on_focusout(event):
        """Función para mostrar el marcador de posición cuando el campo está vacío."""
        if not user_input.get():
            user_input.insert(0, placeholder)
            user_input.config(fg='grey')

    # Función para actualizar la interfaz y eliminar el historial visualmente
    def eliminar_historial_interfaz():
        chat_history.config(state=tk.NORMAL)
        chat_history.delete('1.0', tk.END)
        chat_history.config(state=tk.DISABLED)       


    # Función llamada cuando se presiona el botón de eliminar historial
    def eliminar_historial():
        eliminar_historial_bd(id_estudiante)  # Llamar a la función para borrar el historial de la base de datos
        eliminar_historial_interfaz()  # Llamar a la función para borrar el historial de la interfaz 


    def send_message(event=None):
        message = user_input.get()
        # Obtener la respuesta del chatbot
        response = get_response(message)
        # Guardar la interacción en la base de datos    
        guardar_historial(id_estudiante, message, response)
        if message.strip() and message != placeholder:
            timestamp = datetime.datetime.now().strftime("%H:%M")
            chat_history.config(state=tk.NORMAL)
            chat_history.insert(tk.END, f"Tú {timestamp}\n", "you_tag")
            chat_history.insert(tk.END, f"{message}\n", "you_msg")
            response = get_response(message)
            chat_history.insert(tk.END, f"InteliBot {timestamp}\n", "bot_tag")
            chat_history.insert(tk.END, f"{response}\n", "bot_msg")
            chat_history.config(state=tk.DISABLED)
            chat_history.yview(tk.END)
            user_input.delete(0, tk.END)
            on_focusout(None)  # Asegurarse de que el marcador de posición se muestre después de enviar
        event.widget.mark_set(tk.INSERT, "1.0")


#####################################################################################################################

    # Definición de la función para alternar el historial
    def toggle_historial():
        nonlocal esta_mostrando_historial
        if esta_mostrando_historial:
            # Si el historial está mostrándose, lo ocultamos
            chat_history.config(state=tk.NORMAL)
            chat_history.delete('1.0', tk.END)          
            chat_history.config(state=tk.DISABLED)
            historial_button.config(text="Mostrar Historial")
        else:
            # Si el historial no está mostrándose, lo cargamos y mostramos
            chat_history.config(state=tk.NORMAL)
            chat_history.delete('1.0', tk.END)
            historial = cargar_historial(id_estudiante)
            for interaccion in historial:
                chat_history.insert(tk.END, f"Tú: {interaccion['mensaje']}\n", "you_msg")
                chat_history.insert(tk.END, f"InteliBot: {interaccion['respuesta']}\n", "bot_msg")
            chat_history.config(state=tk.DISABLED)
            chat_history.yview(tk.END)
            historial_button.config(text="Ocultar Historial")
        
        # Invertir el estado del flag
        esta_mostrando_historial = not esta_mostrando_historial


    def logout():
        chat_win.destroy()
        login_window()


    # Botón para alternar el historial
    historial_button = tk.Button(chat_win, text="Mostrar Historial", command=toggle_historial)
    historial_button.pack(side=tk.TOP, fill=tk.X)

    # Botón para eliminar el historial
    eliminar_button = tk.Button(chat_win, text="Eliminar Historial", command=eliminar_historial)
    eliminar_button.pack(side=tk.TOP, fill=tk.X)

    # Colores y estilos
    bg_color = "#FFFFFF"
    input_bg_color = "#E0E0E0"  # Color gris para el fondo del campo de entrada
    user_color = "#E1F5FE"
    bot_color = "#FFCCBC"
    chat_win.configure(bg=bg_color)

    # Aumentar las dimensiones del área de texto ScrolledText
    chat_history = ScrolledText(chat_win, font=("Arial", 12), height=20, width=50, bd=1, relief=tk.FLAT, bg=bg_color)
    chat_history.pack(padx=10, pady=10)
    chat_history.config(state=tk.DISABLED, spacing3=5)


    # Configurar las etiquetas para los mensajes del usuario y el bot
    chat_history.tag_configure("you_tag", foreground="#333333", font=("Arial", 10, "bold"), justify='right')
    chat_history.tag_configure("you_msg", background=user_color, font=("Arial", 12), justify='left', wrap=tk.WORD, lmargin2=20, rmargin=10)
    chat_history.tag_configure("bot_tag", foreground="#333333", font=("Arial", 10, "bold"), justify='left')
    chat_history.tag_configure("bot_msg", background=bot_color, font=("Arial", 12), justify='left', wrap=tk.WORD, lmargin2=20, rmargin=10)

    user_input_frame = tk.Frame(chat_win, bg=input_bg_color)
    user_input_frame.pack(fill=tk.BOTH, side=tk.BOTTOM, padx=10, pady=10)
    user_input = tk.Entry(user_input_frame, font=("Arial", 12), bd=0, relief=tk.FLAT, fg='grey', background="#C3C3C3")
    user_input.insert(0, placeholder)
    user_input.bind("<FocusIn>", on_entry_click)
    user_input.bind("<FocusOut>", on_focusout)
    user_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 10))  # add padx to create space
    user_input.bind("<Return>", send_message)

    send_button = tk.Button(user_input_frame, text="Enviar", font=("Arial", 12), command=send_message, bg="#30B5FF", fg="white", bd=0)
    send_button.pack(side=tk.RIGHT, padx=(0, 10))  # add padx to create space on the right

    logout_btn = tk.Button(chat_win, text="Cerrar Sesión", font=("Arial", 12) ,command=logout, bg='red', fg='white', width=15, bd=0)
    logout_btn.pack(side=tk.TOP, padx=(0))

    chat_win.mainloop()    


# Comienza con la ventana de inicio de sesión
login_window()