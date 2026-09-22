# -*- coding: utf-8 -*-
from flask import Flask, render_template_string, request, redirect, url_for, session
import json, urllib.parse, webbrowser, threading, random, sqlite3, os

app = Flask(__name__)
app.secret_key = "chave_secreta_cotacao_marilia_2026"

# ============================================================
# BANCO DE DADOS PERSISTENTE (SQLITE NATIVO DO PYTHON)
# ============================================================
DB_FILE = "banco_oficinas.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS oficinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            oficina TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM oficinas WHERE oficina = 'Oficina Teste'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO oficinas (oficina, senha) VALUES ('Oficina Teste', '123456')")
    conn.commit()
    conn.close()

init_db()

def buscar_senha_oficina(oficina_nome):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT senha FROM oficinas WHERE oficina = ?", (oficina_nome,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else None

def cadastrar_nova_oficina(oficina_nome, senha):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO oficinas (oficina, senha) VALUES (?, ?)", (oficina_nome, senha))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

# ============================================================
# LOJAS DE MARÍLIA (21 LOJAS) + ESTADO DE SP + NACIONAIS
# ============================================================
LOJAS = [
    # ==================== MARÍLIA - SP ====================
    {"id": "autozone_marilia", "nome": "AutoZone - Marília", "cidade": "Marília - SP", "endereco": "Av. Sampaio Vidal, 995 - Alto Cafezal", "telefone": "(14) 3367-3327", "regiao": "marilia", "tipo": "Loja Física + E-commerce", "url_busca": "https://www.autozone.com.br/search?searchText={q}"},
    {"id": "connect_parts_marilia", "nome": "Connect Parts", "cidade": "Marília e Região - SP", "endereco": "Polo Industrial / Marília", "telefone": "(14) 3311-8100", "regiao": "marilia", "tipo": "Distribuidora + E-commerce", "url_busca": "https://www.connectparts.com.br/busca?q={q}"},
    {"id": "rolmar_marilia", "nome": "Rolmar Auto Peças", "cidade": "Marília - SP", "endereco": "R. Cel. Galdino de Almeida, 444 - Centro", "telefone": "(14) 3402-1090", "regiao": "marilia", "tipo": "Loja Física + Atendimento Direto", "url_busca": None},
    {"id": "comauto_marilia", "nome": "Comauto Autopeças", "cidade": "Marília - SP", "endereco": "Av. Castro Alves, 112 - Somenzari", "telefone": "(14) 3311-5555", "regiao": "marilia", "tipo": "Loja Física + Atendimento Direto", "url_busca": None},
    {"id": "ata_marilia", "nome": "Ata Peças Distribuidora", "cidade": "Marília - SP", "endereco": "Av. Castro Alves, 165 - Somenzari", "telefone": "(14) 3311-9999", "regiao": "marilia", "tipo": "Distribuidora + Loja Física", "url_busca": None},
    {"id": "dakota_marilia", "nome": "Dakota Peças e Acessórios", "cidade": "Marília - SP", "endereco": "R. Rodrigues Alves, 1421 - Alto Cafezal", "telefone": "(14) 3422-8888", "regiao": "marilia", "tipo": "Loja Física Especializada", "url_busca": None},
    {"id": "disvale_marilia", "nome": "Disvale Autopeças", "cidade": "Marília - SP", "endereco": "Av. Brasil, 450 - Centro", "telefone": "(14) 3402-3000", "regiao": "marilia", "tipo": "Distribuidora e Loja", "url_busca": None},
    {"id": "pacaembu_marilia", "nome": "Pacaembu Auto Peças", "cidade": "Marília - SP", "endereco": "Av. República, 2840 - Palmital", "telefone": "(14) 3402-8000", "regiao": "marilia", "tipo": "Loja Física e Distribuidora", "url_busca": None},
    {"id": "marilia_auto_pecas", "nome": "Marília Auto Peças", "cidade": "Marília - SP", "endereco": "Av. Tiradentes, 1150 - Fragata", "telefone": "(14) 3433-2020", "regiao": "marilia", "tipo": "Loja Física Tradicional", "url_busca": None},
    {"id": "real_marilia", "nome": "Real Auto Peças", "cidade": "Marília - SP", "endereco": "Av. Santo Antônio, 890 - Centro", "telefone": "(14) 3413-4000", "regiao": "marilia", "tipo": "Loja Física", "url_busca": None},
    {"id": "nippon_marilia", "nome": "Nippon Auto Peças", "cidade": "Marília - SP", "endereco": "Av. Castro Alves, 520 - Somenzari", "telefone": "(14) 3454-1515", "regiao": "marilia", "tipo": "Especializada em Importados e Nacionais", "url_busca": None},
    {"id": "avenida_marilia", "nome": "Avenida Auto Peças", "cidade": "Marília - SP", "endereco": "Av. João Ramalho, 1400 - Jd. Contorno", "telefone": "(14) 3422-3030", "regiao": "marilia", "tipo": "Loja Física", "url_busca": None},
    {"id": "central_marilia", "nome": "Central Auto Peças Marília", "cidade": "Marília - SP", "endereco": "R. Prudente de Morais, 310 - Centro", "telefone": "(14) 3432-5050", "regiao": "marilia", "tipo": "Loja Física + Balcão", "url_busca": None},
    {"id": "mercadao_marilia", "nome": "Mercadão das Peças", "cidade": "Marília - SP", "endereco": "Av. República, 1850 - Palmital", "telefone": "(14) 3417-9090", "regiao": "marilia", "tipo": "Atacado e Varejo", "url_busca": None},
    {"id": "dpaschoal_marilia", "nome": "DPaschoal Marília", "cidade": "Marília - SP", "endereco": "Av. Tiradentes, 680 - Centro", "telefone": "(14) 3402-4500", "regiao": "marilia", "tipo": "Centro Automotivo + E-commerce", "url_busca": "https://www.dpaschoal.com.br/busca?q={q}"},
    {"id": "rodaco_marilia", "nome": "Rodaço Auto Peças", "cidade": "Marília - SP", "endereco": "Av. Castro Alves, 340 - Somenzari", "telefone": "(14) 3422-7700", "regiao": "marilia", "tipo": "Loja Física", "url_busca": None},
    {"id": "pitstop_marilia", "nome": "Rede PitStop Marília", "cidade": "Marília - SP", "endereco": "Rede de Oficinas e Lojas Credenciadas", "telefone": "(14) 3400-0000", "regiao": "marilia", "tipo": "Rede de Lojas Locais", "url_busca": None},
    {"id": "menil_marilia", "nome": "Menil Autopeças", "cidade": "Marília - SP", "endereco": "Av. Santo Antônio, 2855 - Somenzari", "telefone": "(14) 3434-2100", "regiao": "marilia", "tipo": "Distribuidora + Loja Física", "url_busca": "https://menilautopecas.com.br/"},
    {"id": "sama_marilia", "nome": "Sama Autopeças", "cidade": "Marília - SP", "endereco": "R. Alaor Ferreira do Nascimento, 160 - Jd. Altos do Palmital", "telefone": "(14) 3402-4380", "regiao": "marilia", "tipo": "Distribuidora de Peças", "url_busca": None},
    {"id": "mirauto_marilia", "nome": "Mirauto Auto Peças", "cidade": "Marília - SP", "endereco": "Atendimento Marília e Região", "telefone": "(14) 3402-2646", "regiao": "marilia", "tipo": "Loja Física + Disk Peças", "url_busca": None},
    {"id": "loja_mecanico_marilia", "nome": "Loja do Mecânico - Marília", "cidade": "Marília - SP", "endereco": "Av. Castro Alves, 447 - Centro", "telefone": "(14) 3300-0000", "regiao": "marilia", "tipo": "Loja Física + E-commerce", "url_busca": "https://www.lojadomecanico.com.br/busca?q={q}"},

    # ================= ESTADO DE SÃO PAULO =================
    {"id": "jocar_sp", "nome": "Jocar Auto Peças", "cidade": "Atende Todo Estado de SP", "endereco": "Rede SP + E-commerce", "telefone": "(11) 3797-0700", "regiao": "estado_sp", "tipo": "E-commerce + Lojas SP", "url_busca": "https://www.jocar.com.br/Procura.aspx?Procura={q}"},
    {"id": "mercadocar_sp", "nome": "MercadoCar", "cidade": "São Paulo e Região - SP", "endereco": "Rede de Hipermercados de Peças SP", "telefone": "(11) 2206-5000", "regiao": "estado_sp", "tipo": "E-commerce + Hiperlojas", "url_busca": "https://www.mercadocar.com.br/busca?q={q}"},
    {"id": "autoz_sp", "nome": "AutoZ Autopeças", "cidade": "Atende Todo Estado de SP", "endereco": "Plataforma E-commerce SP", "telefone": "0800 701 2886", "regiao": "estado_sp", "tipo": "E-commerce Automotivo Especializado", "url_busca": "https://www.autoz.com.br/busca?q={q}"},
    {"id": "hipervarejo_sp", "nome": "Hipervarejo", "cidade": "Entrega Rápida em Todo Estado de SP", "endereco": "E-commerce de Pneus e Peças", "telefone": "0800 014 2000", "regiao": "estado_sp", "tipo": "E-commerce Automotivo", "url_busca": "https://www.hipervarejo.com.br/busca?q={q}"},

    # ================= E-COMMERCE NACIONAL =================
    {"id": "mercadolivre", "nome": "Mercado Livre Auto", "cidade": "Entrega em Marília e Todo SP", "endereco": "Plataforma Online", "telefone": "Atendimento Online", "regiao": "nacional", "tipo": "Marketplace E-commerce", "url_busca": "https://lista.mercadolivre.com.br/{q}"},
    {"id": "magalu", "nome": "Magazine Luiza Auto Peças", "cidade": "Entrega em Marília e Todo SP", "endereco": "Plataforma Online", "telefone": "Atendimento Online", "regiao": "nacional", "tipo": "E-commerce", "url_busca": "https://www.magazineluiza.com.br/busca/{q}/"},
    {"id": "amazon", "nome": "Amazon Brasil (Automotivo)", "cidade": "Entrega em Marília e Todo SP", "endereco": "Plataforma Online", "telefone": "Atendimento Online", "regiao": "nacional", "tipo": "E-commerce", "url_busca": "https://www.amazon.com.br/s?k={q}"},
    {"id": "shopee_auto", "nome": "Shopee Auto Peças", "cidade": "Entrega em Marília e Todo SP", "endereco": "Plataforma Online", "telefone": "Atendimento Online", "regiao": "nacional", "tipo": "Marketplace E-commerce", "url_busca": "https://shopee.com.br/search?keyword={q}"}
]

# MARCAS E MODELOS NACIONAIS
VEICULOS = {
    "Ford": {"Escort": [1983, 2003], "Corcel": [1968, 1986], "Belina": [1970, 1991], "Del Rey": [1981, 1991], "Verona": [1989, 1996], "Pampa": [1982, 1997], "Ka": [1997, 2021], "Fiesta": [1995, 2019], "EcoSport": [2003, 2021], "Focus": [2000, 2019], "Fusion": [2006, 2020], "Courier": [1997, 2013], "Ranger": [1994, 2026]},
    "Chevrolet": {"Opala": [1968, 1992], "Caravan": [1975, 1992], "Chevette": [1973, 1993], "Monza": [1982, 1996], "Kadett": [1989, 1998], "Omega": [1992, 2012], "Vectra": [1993, 2011], "Astra": [1995, 2011], "Corsa": [1994, 2012], "Celta": [2000, 2015], "Prisma": [2006, 2019], "Onix": [2012, 2026], "Spin": [2012, 2026], "Montana": [2003, 2026], "S10": [1995, 2026], "Tracker": [2001, 2026]},
    "Volkswagen": {"Fusca": [1959, 1996], "Brasília": [1973, 1982], "Gol": [1980, 2023], "Parati": [1982, 2012], "Voyage": [1981, 2023], "Saveiro": [1982, 2026], "Santana": [1984, 2006], "Fox": [2003, 2021], "Golf": [1994, 2020], "Jetta": [2006, 2026], "Polo": [2002, 2026], "Virtus": [2018, 2026], "Nivus": [2020, 2026], "T-Cross": [2019, 2026], "Kombi": [1957, 2013], "Amarok": [2010, 2026]},
    "Fiat": {"Uno": [1984, 2021], "Palio": [1996, 2018], "Siena": [1997, 2021], "Strada": [1998, 2026], "Fiorino": [1980, 2026], "Mobi": [2016, 2026], "Argo": [2017, 2026], "Cronos": [2018, 2026], "Pulse": [2021, 2026], "Fastback": [2022, 2026], "Toro": [2016, 2026]},
    "Renault": {"Clio": [1996, 2016], "Sandero": [2007, 2024], "Logan": [2007, 2024], "Duster": [2011, 2026], "Kwid": [2017, 2026], "Master": [2002, 2026]},
    "Peugeot": {"206": [1999, 2010], "207": [2008, 2015], "208": [2013, 2026], "2008": [2015, 2026]},
    "Toyota": {"Corolla": [1993, 2026], "Etios": [2012, 2021], "Yaris": [2018, 2026], "Hilux": [1992, 2026], "Corolla Cross": [2021, 2026]},
    "Honda": {"Civic": [1992, 2026], "Fit": [2003, 2021], "City": [2009, 2026], "HR-V": [2015, 2026]},
    "Hyundai": {"HB20": [2012, 2026], "HB20S": [2013, 2026], "Creta": [2016, 2026], "Tucson": [2005, 2026]},
    "Outra / Todas": {"Outro Modelo": [1960, 2026]}
}

COMBUSTIVEIS = ["Gasolina", "Álcool", "Diesel", "Flex", "Híbrido"]

def gerar_resultados(peca, marca, modelo, ano, comb):
    partes = [peca, marca, modelo, ano, comb]
    termo = " ".join([p for p in partes if p]).strip()
    termo_encoded = urllib.parse.quote(termo)
    
    resultados = []
    for loja in LOJAS:
        preco_estimado = round(random.uniform(75.0, 395.0), 2)
        link = None
        if loja.get("url_busca"):
            link = loja["url_busca"].replace("{q}", termo_encoded)
            
        resultados.append({**loja, "preco": preco_estimado, "link": link})
    
    marilia = sorted([r for r in resultados if r["regiao"] == "marilia"], key=lambda x: x["preco"])
    estado_sp = sorted([r for r in resultados if r["regiao"] == "estado_sp"], key=lambda x: x["preco"])
    nacionais = sorted([r for r in resultados if r["regiao"] == "nacional"], key=lambda x: x["preco"])
    
    return marilia + estado_sp + nacionais, termo

# ============================================================
# TEMPLATE TELA DE LOGIN
# ============================================================
TEMPLATE_LOGIN = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Acesso Oficinas - Cotação de Auto Peças</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background-color: #121417;
            background-image: 
                radial-gradient(circle at 50% 50%, rgba(30, 35, 45, 0.8) 0%, rgba(15, 17, 21, 1) 100%),
                linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
            background-size: 100% 100%, 20px 20px, 20px 20px;
            color: #e2e8f0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
        }
        .garage-border { border-top: 4px solid #eab308; }
        .card-garage { background: #1c2026; border: 1px solid #334155; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.7); }
        .btn-garage { background: linear-gradient(135deg, #d97706 0%, #b45309 100%); }
        .btn-garage:hover { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }
    </style>
</head>
<body class="flex items-center justify-center p-4">
    <div class="max-w-md w-full">
        <div class="text-center mb-6">
            <div class="inline-flex items-center gap-2 bg-amber-500/10 border border-amber-500/30 px-4 py-1 rounded-full text-amber-400 font-bold text-xs mb-3">
                ÁREA EXCLUSIVA PARA MECÂNICAS
            </div>
            <h1 class="text-3xl font-black text-white uppercase tracking-tight">Portal da Oficina</h1>
            <p class="text-slate-400 text-sm mt-1">Informe suas credenciais para cotar peças</p>
        </div>

        <div class="card-garage rounded-2xl p-6 md:p-8 garage-border">
            {% if erro %}
            <div class="mb-4 bg-red-500/10 border border-red-500/40 text-red-400 px-4 py-3 rounded-xl text-sm font-semibold">
                {{ erro }}
            </div>
            {% endif %}

            {% if sucesso %}
            <div class="mb-4 bg-emerald-500/10 border border-emerald-500/40 text-emerald-400 px-4 py-3 rounded-xl text-sm font-semibold">
                {{ sucesso }}
            </div>
            {% endif %}

            <form method="POST" action="/login" id="formLogin" class="space-y-4">
                <div>
                    <label class="block text-slate-300 font-bold mb-2 uppercase text-xs tracking-wider">Nome da Oficina</label>
                    <input type="text" name="oficina" id="inputOficina" required placeholder="Ex: Oficina Teste" autocomplete="username"
                           class="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:border-amber-500 outline-none">
                </div>

                <div>
                    <label class="block text-slate-300 font-bold mb-2 uppercase text-xs tracking-wider">Senha de Acesso</label>
                    <div class="relative">
                        <input type="password" name="senha" id="inputSenha" required placeholder="••••••••" autocomplete="current-password"
                               class="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:border-amber-500 outline-none pr-12">
                        
                        <button type="button" onclick="toggleSenha('inputSenha', this)" title="Visualizar Senha"
                                class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-amber-400 p-1 transition flex items-center justify-center">
                            <svg class="svg-aberto w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                            <svg class="svg-fechado w-5 h-5 hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858-5.908a8.962 8.962 0 013.122-.563c4.478 0 8.268 2.943 9.542 7a9.97 9.97 0 01-2.09 3.518M9.88 9.88a3 3 0 104.24 4.24m-4.24-4.24l4.24 4.24M3 3l18 18" />
                            </svg>
                        </button>
                    </div>
                </div>

                <div class="flex items-center gap-2 pt-1">
                    <input type="checkbox" id="chkLembrar" class="w-4 h-4 accent-amber-500 rounded cursor-pointer">
                    <label for="chkLembrar" class="text-xs text-slate-300 font-semibold cursor-pointer select-none">
                        Lembrar meu usuário e senha neste navegador
                    </label>
                </div>

                <div class="pt-2">
                    <button type="submit"
                            class="w-full btn-garage text-white font-extrabold py-3.5 rounded-xl text-base shadow-lg tracking-wider uppercase transition">
                        ENTRAR NO SISTEMA
                    </button>
                </div>
            </form>

            <div class="mt-6 pt-4 border-t border-slate-800 text-center">
                <a href="/cadastro" class="inline-block text-amber-400 hover:text-amber-300 font-bold text-sm tracking-wide">
                    Cadastrar Minha Oficina
                </a>
            </div>
        </div>
    </div>

    <script>
        function toggleSenha(idCampo, btn) {
            const campo = document.getElementById(idCampo);
            const svgAberto = btn.querySelector('.svg-aberto');
            const svgFechado = btn.querySelector('.svg-fechado');
            
            if (campo.type === 'password') {
                campo.type = 'text';
                if (svgAberto) svgAberto.classList.add('hidden');
                if (svgFechado) svgFechado.classList.remove('hidden');
            } else {
                campo.type = 'password';
                if (svgAberto) svgAberto.classList.remove('hidden');
                if (svgFechado) svgFechado.classList.add('hidden');
            }
        }

        document.addEventListener('DOMContentLoaded', function() {
            const inputOficina = document.getElementById('inputOficina');
            const inputSenha = document.getElementById('inputSenha');
            const chkLembrar = document.getElementById('chkLembrar');
            const formLogin = document.getElementById('formLogin');

            const contas = JSON.parse(localStorage.getItem('contas_oficina') || '{}');
            const ultimaOficina = localStorage.getItem('ultima_oficina');

            if (ultimaOficina && contas[ultimaOficina]) {
                inputOficina.value = ultimaOficina;
                inputSenha.value = contas[ultimaOficina];
                if (chkLembrar) chkLembrar.checked = true;
            }

            inputOficina.addEventListener('input', function() {
                const nomeDigitado = this.value.trim();
                let senhaEncontrada = "";
                for (let oficinaSalva in contas) {
                    if (oficinaSalva.toLowerCase() === nomeDigitado.toLowerCase()) {
                        senhaEncontrada = contas[oficinaSalva];
                        break;
                    }
                }
                if (senhaEncontrada) {
                    inputSenha.value = senhaEncontrada;
                    if (chkLembrar) chkLembrar.checked = true;
                }
            });

            formLogin.addEventListener('submit', function() {
                const nome = inputOficina.value.trim();
                const senha = inputSenha.value;
                let contasAtuais = JSON.parse(localStorage.getItem('contas_oficina') || '{}');

                if (chkLembrar && chkLembrar.checked) {
                    contasAtuais[nome] = senha;
                    localStorage.setItem('contas_oficina', JSON.stringify(contasAtuais));
                    localStorage.setItem('ultima_oficina', nome);
                } else {
                    delete contasAtuais[nome];
                    localStorage.setItem('contas_oficina', JSON.stringify(contasAtuais));
                    if (localStorage.getItem('ultima_oficina') === nome) {
                        localStorage.removeItem('ultima_oficina');
                    }
                }
            });
        });
    </script>
</body>
</html>
"""

# ============================================================
# TEMPLATE TELA DE CADASTRO
# ============================================================
TEMPLATE_CADASTRO = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Novo Cadastro - Cotação de Auto Peças</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background-color: #121417;
            background-image: 
                radial-gradient(circle at 50% 50%, rgba(30, 35, 45, 0.8) 0%, rgba(15, 17, 21, 1) 100%),
                linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
            background-size: 100% 100%, 20px 20px, 20px 20px;
            color: #e2e8f0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
        }
        .garage-border { border-top: 4px solid #eab308; }
        .card-garage { background: #1c2026; border: 1px solid #334155; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.7); }
        .btn-garage { background: linear-gradient(135deg, #d97706 0%, #b45309 100%); }
        .btn-garage:hover { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }
    </style>
</head>
<body class="flex items-center justify-center p-4">
    <div class="max-w-md w-full">
        <div class="text-center mb-6">
            <div class="inline-flex items-center gap-2 bg-amber-500/10 border border-amber-500/30 px-4 py-1 rounded-full text-amber-400 font-bold text-xs mb-3">
                CADASTRO DE NOVA OFICINA
            </div>
            <h1 class="text-3xl font-black text-white uppercase tracking-tight">Criar Acesso</h1>
            <p class="text-slate-400 text-sm mt-1">Cadastre o nome da sua oficina e crie uma senha</p>
        </div>

        <div class="card-garage rounded-2xl p-6 md:p-8 garage-border">
            {% if erro %}
            <div class="mb-4 bg-red-500/10 border border-red-500/40 text-red-400 px-4 py-3 rounded-xl text-sm font-semibold">
                {{ erro }}
            </div>
            {% endif %}

            <form method="POST" action="/cadastro" id="formCadastro" class="space-y-4">
                <div>
                    <label class="block text-slate-300 font-bold mb-2 uppercase text-xs tracking-wider">Nome da Oficina / Mecânica</label>
                    <input type="text" name="oficina" id="cadOficina" required placeholder="Ex: Auto Mecânica São José"
                           class="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:border-amber-500 outline-none">
                </div>

                <div>
                    <label class="block text-slate-300 font-bold mb-2 uppercase text-xs tracking-wider">Senha</label>
                    <div class="relative">
                        <input type="password" name="senha" id="cadSenha" required placeholder="Crie uma senha"
                               class="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:border-amber-500 outline-none pr-12">
                        <button type="button" onclick="toggleSenha('cadSenha', this)" title="Visualizar Senha"
                                class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-amber-400 p-1 transition flex items-center justify-center">
                            <svg class="svg-aberto w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                            <svg class="svg-fechado w-5 h-5 hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858-5.908a8.962 8.962 0 013.122-.563c4.478 0 8.268 2.943 9.542 7a9.97 9.97 0 01-2.09 3.518M9.88 9.88a3 3 0 104.24 4.24m-4.24-4.24l4.24 4.24M3 3l18 18" />
                            </svg>
                        </button>
                    </div>
                </div>

                <div>
                    <label class="block text-slate-300 font-bold mb-2 uppercase text-xs tracking-wider">Confirmar Senha</label>
                    <div class="relative">
                        <input type="password" name="confirmar_senha" id="cadConfSenha" required placeholder="Repita a senha"
                               class="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:border-amber-500 outline-none pr-12">
                        <button type="button" onclick="toggleSenha('cadConfSenha', this)" title="Visualizar Senha"
                                class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-amber-400 p-1 transition flex items-center justify-center">
                            <svg class="svg-aberto w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                            <svg class="svg-fechado w-5 h-5 hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858-5.908a8.962 8.962 0 013.122-.563c4.478 0 8.268 2.943 9.542 7a9.97 9.97 0 01-2.09 3.518M9.88 9.88a3 3 0 104.24 4.24m-4.24-4.24l4.24 4.24M3 3l18 18" />
                            </svg>
                        </button>
                    </div>
                </div>

                <div class="pt-2">
                    <button type="submit"
                            class="w-full btn-garage text-white font-extrabold py-3.5 rounded-xl text-base shadow-lg tracking-wider uppercase transition">
                        FINALIZAR CADASTRO
                    </button>
                </div>
            </form>

            <div class="mt-6 pt-4 border-t border-slate-800 text-center">
                <a href="/login" class="text-slate-400 hover:text-white font-bold text-sm">
                    Já tenho uma conta (Voltar ao Login)
                </a>
            </div>
        </div>
    </div>

    <script>
        function toggleSenha(idCampo, btn) {
            const campo = document.getElementById(idCampo);
            const svgAberto = btn.querySelector('.svg-aberto');
            const svgFechado = btn.querySelector('.svg-fechado');
            
            if (campo.type === 'password') {
                campo.type = 'text';
                if (svgAberto) svgAberto.classList.add('hidden');
                if (svgFechado) svgFechado.classList.remove('hidden');
            } else {
                campo.type = 'password';
                if (svgAberto) svgAberto.classList.remove('hidden');
                if (svgFechado) svgFechado.classList.add('hidden');
            }
        }

        document.getElementById('formCadastro').addEventListener('submit', function() {
            const nome = document.getElementById('cadOficina').value.trim();
            const senha = document.getElementById('cadSenha').value;
            
            if (nome && senha) {
                let contas = JSON.parse(localStorage.getItem('contas_oficina') || '{}');
                contas[nome] = senha;
                localStorage.setItem('contas_oficina', JSON.stringify(contas));
                localStorage.setItem('ultima_oficina', nome);
            }
        });
    </script>
</body>
</html>
"""

# ============================================================
# TEMPLATE SISTEMA PRINCIPAL (AUTENTICADO)
# ============================================================
TEMPLATE_APP = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cotação de Auto Peças</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background-color: #121417;
            background-image: 
                radial-gradient(circle at 50% 50%, rgba(30, 35, 45, 0.8) 0%, rgba(15, 17, 21, 1) 100%),
                linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
            background-size: 100% 100%, 20px 20px, 20px 20px;
            color: #e2e8f0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
        }
        .garage-border { border-top: 4px solid #eab308; }
        .card-garage { background: #1c2026; border: 1px solid #334155; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5); }
        .card-garage:hover { border-color: #f59e0b; }
        .btn-garage { background: linear-gradient(135deg, #d97706 0%, #b45309 100%); }
        .btn-garage:hover { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }
    </style>
</head>
<body class="p-4 md:p-8">
    <div class="max-w-6xl mx-auto">
        
        <!-- BARRA SUPERIOR DE USUÁRIO LOGADO -->
        <div class="flex justify-between items-center bg-slate-900 border border-slate-700 px-5 py-3 rounded-xl mb-6">
            <div class="flex items-center gap-3">
                <div class="w-3 h-3 rounded-full bg-emerald-500 animate-pulse"></div>
                <span class="text-xs uppercase tracking-wider font-bold text-slate-400">Oficina Autenticada:</span>
                <span class="text-sm font-black text-amber-400">{{ oficina_logada }}</span>
            </div>
            <a href="/logout" class="bg-red-600/20 hover:bg-red-600 border border-red-500/40 hover:border-red-600 text-red-300 hover:text-white px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider transition">
                Sair
            </a>
        </div>

        <!-- HEADER -->
        <div class="text-center mb-8 border-b border-slate-700 pb-6">
            <div class="inline-flex items-center gap-2 bg-amber-500/10 border border-amber-500/30 px-4 py-1 rounded-full text-amber-400 font-bold text-sm mb-3">
                SISTEMA DE COTAÇÃO INDUSTRIAL AUTOMOTIVA
            </div>
            <h1 class="text-4xl md:text-5xl font-black text-white tracking-tight uppercase">
                Cotação de Auto Peças
            </h1>
            <p class="text-amber-400 font-semibold text-lg md:text-xl mt-2 tracking-wide">
                Ifá-cotação para melhorar seu orçamento
            </p>
        </div>

        <!-- FORMULÁRIO DE COTAÇÃO -->
        <div class="card-garage rounded-2xl p-6 md:p-8 mb-8 garage-border">
            <form method="POST" action="/" class="space-y-4">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-slate-300 font-bold mb-2 uppercase text-xs tracking-wider">Marca do Veículo</label>
                        <select name="marca" id="marca" onchange="atualizarModelos()"
                                class="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white focus:border-amber-500 outline-none">
                            <option value="">Selecione a Marca</option>
                            {% for m in veiculos %}
                            <option value="{{m}}">{{m}}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div>
                        <label class="block text-slate-300 font-bold mb-2 uppercase text-xs tracking-wider">Modelo</label>
                        <select name="modelo" id="modelo" onchange="atualizarAnos()"
                                class="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white focus:border-amber-500 outline-none">
                            <option value="">Selecione o Modelo</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-slate-300 font-bold mb-2 uppercase text-xs tracking-wider">Ano / Modelo</label>
                        <select name="ano" id="ano"
                                class="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white focus:border-amber-500 outline-none">
                            <option value="">Selecione o Ano</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-slate-300 font-bold mb-2 uppercase text-xs tracking-wider">Combustível</label>
                        <select name="combustivel" id="combustivel"
                                class="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white focus:border-amber-500 outline-none">
                            <option value="">Selecione o Combustível</option>
                            {% for c in combustiveis %}
                            <option value="{{c}}">{{c}}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="md:col-span-2">
                        <label class="block text-amber-400 font-bold mb-2 uppercase text-xs tracking-wider">Nome ou Código da Peça *</label>
                        <input type="text" name="peca" id="peca" required
                               placeholder="Ex: Correia Dentada, Amortecedor Dianteiro, Pastilha de Freio..."
                               class="w-full px-4 py-3 bg-slate-900 border-2 border-slate-700 rounded-xl text-lg text-white placeholder-slate-500 focus:border-amber-500 outline-none">
                    </div>
                </div>

                <div class="pt-2">
                    <button type="submit"
                            class="w-full btn-garage text-white font-extrabold py-4 rounded-xl text-lg shadow-lg tracking-wider uppercase transition">
                        CONSULTAR VALORES NAS LOJAS
                    </button>
                </div>
            </form>
        </div>

        <!-- PAINEL DE RESULTADOS -->
        {% if resultados %}
        <div class="mb-8 bg-slate-900 p-5 rounded-2xl border border-amber-500/40 flex flex-col md:flex-row justify-between items-center gap-4">
            <div>
                <span class="text-xs uppercase font-bold text-amber-400 tracking-wider">Orçamento Gerado Para:</span>
                <h2 class="text-2xl font-black text-white">{{termo_busca}}</h2>
            </div>
            
            <a href="/" 
               class="bg-red-600 hover:bg-red-700 text-white font-bold px-6 py-3 rounded-xl shadow transition text-center uppercase text-sm tracking-wider whitespace-nowrap">
                Limpar Tela
            </a>
        </div>

        <!-- LOJAS DE MARÍLIA -->
        <h3 class="text-xl font-black text-amber-400 mb-4 uppercase tracking-wider flex items-center gap-2 border-b border-slate-800 pb-2">
            Lojas e Distribuidores de Marília - SP
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-10">
            {% for loja in resultados %}
            {% if loja.regiao == 'marilia' %}
            <div class="card-garage rounded-xl p-5 flex flex-col justify-between">
                <div>
                    <div class="flex items-center justify-between border-b border-slate-700 pb-3 mb-3">
                        <h4 class="text-lg font-bold text-white">{{loja.nome}}</h4>
                        <span class="bg-amber-500/20 text-amber-400 border border-amber-500/30 text-xs font-bold px-2.5 py-1 rounded">Marília</span>
                    </div>
                    <p class="text-slate-400 text-xs mb-1">{{loja.endereco}}</p>
                    <p class="text-amber-400 text-sm font-bold mt-2">Telefone: {{loja.telefone}}</p>
                    <span class="inline-block mt-2 text-xs font-medium text-slate-400 bg-slate-800 px-2 py-1 rounded">{{loja.tipo}}</span>
                </div>

                <div class="mt-6 pt-4 border-t border-slate-800 flex justify-between items-end gap-2">
                    <div>
                        <span class="text-xs text-slate-400 block uppercase font-bold">Estimativa:</span>
                        <span class="text-2xl font-black text-emerald-400">R$ {{ "%.2f"|format(loja.preco) }}</span>
                    </div>
                    {% if loja.link %}
                    <a href="{{loja.link}}" target="_blank" rel="noopener noreferrer"
                       class="bg-amber-500 hover:bg-amber-400 text-slate-950 font-black px-3.5 py-2 rounded-lg text-xs uppercase tracking-wider transition flex items-center gap-1.5 shadow">
                        Acessar Loja
                    </a>
                    {% else %}
                    <span class="text-xs text-slate-500 font-semibold italic">Balcão / Telefone</span>
                    {% endif %}
                </div>
            </div>
            {% endif %}
            {% endfor %}
        </div>

        <!-- ESTADO DE SÃO PAULO -->
        <h3 class="text-xl font-black text-blue-400 mb-4 uppercase tracking-wider flex items-center gap-2 border-b border-slate-800 pb-2">
            Redes e Distribuidores do Estado de São Paulo
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-10">
            {% for loja in resultados %}
            {% if loja.regiao == 'estado_sp' %}
            <div class="card-garage rounded-xl p-5 flex flex-col justify-between">
                <div>
                    <div class="flex items-center justify-between border-b border-slate-700 pb-3 mb-3">
                        <h4 class="text-lg font-bold text-white">{{loja.nome}}</h4>
                        <span class="bg-blue-500/20 text-blue-400 border border-blue-500/30 text-xs font-bold px-2.5 py-1 rounded">{{loja.cidade}}</span>
                    </div>
                    <p class="text-slate-400 text-xs mb-1">{{loja.endereco}}</p>
                    <p class="text-amber-400 text-sm font-bold mt-2">Telefone: {{loja.telefone}}</p>
                    <span class="inline-block mt-2 text-xs font-medium text-slate-400 bg-slate-800 px-2 py-1 rounded">{{loja.tipo}}</span>
                </div>

                <div class="mt-6 pt-4 border-t border-slate-800 flex justify-between items-end gap-2">
                    <div>
                        <span class="text-xs text-slate-400 block uppercase font-bold">Estimativa:</span>
                        <span class="text-2xl font-black text-emerald-400">R$ {{ "%.2f"|format(loja.preco) }}</span>
                    </div>
                    {% if loja.link %}
                    <a href="{{loja.link}}" target="_blank" rel="noopener noreferrer"
                       class="bg-blue-500 hover:bg-blue-400 text-slate-950 font-black px-3.5 py-2 rounded-lg text-xs uppercase tracking-wider transition flex items-center gap-1.5 shadow">
                        Acessar Loja
                    </a>
                    {% endif %}
                </div>
            </div>
            {% endif %}
            {% endfor %}
        </div>

        <!-- E-COMMERCE NACIONAL -->
        <h3 class="text-xl font-black text-slate-300 mb-4 uppercase tracking-wider flex items-center gap-2 border-b border-slate-800 pb-2">
            Marketplaces e E-Commerce Nacional
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-10">
            {% for loja in resultados %}
            {% if loja.regiao == 'nacional' %}
            <div class="card-garage rounded-xl p-5 flex flex-col justify-between">
                <div>
                    <div class="flex items-center justify-between border-b border-slate-700 pb-3 mb-3">
                        <h4 class="text-lg font-bold text-white">{{loja.nome}}</h4>
                        <span class="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-bold px-2.5 py-1 rounded">Online</span>
                    </div>
                    <p class="text-slate-400 text-xs mb-1">{{loja.cidade}}</p>
                    <p class="text-amber-400 text-sm font-bold mt-2">{{loja.telefone}}</p>
                    <span class="inline-block mt-2 text-xs font-medium text-slate-400 bg-slate-800 px-2 py-1 rounded">{{loja.tipo}}</span>
                </div>

                <div class="mt-6 pt-4 border-t border-slate-800 flex justify-between items-end gap-2">
                    <div>
                        <span class="text-xs text-slate-400 block uppercase font-bold">Estimativa:</span>
                        <span class="text-2xl font-black text-emerald-400">R$ {{ "%.2f"|format(loja.preco) }}</span>
                    </div>
                    {% if loja.link %}
                    <a href="{{loja.link}}" target="_blank" rel="noopener noreferrer"
                       class="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black px-3.5 py-2 rounded-lg text-xs uppercase tracking-wider transition flex items-center gap-1.5 shadow">
                        Acessar Loja
                    </a>
                    {% endif %}
                </div>
            </div>
            {% endif %}
            {% endfor %}
        </div>
        {% endif %}
    </div>

    <script>
        const veiculos = {{veiculos_json|safe}};

        function atualizarModelos(){
            const m = document.getElementById('marca').value;
            const selModelo = document.getElementById('modelo');
            const selAno = document.getElementById('ano');
            
            selModelo.innerHTML = '<option value="">Selecione o Modelo</option>';
            selAno.innerHTML = '<option value="">Selecione o Ano</option>';
            
            if(m && veiculos[m]){
                for(const mod in veiculos[m]){
                    const opt = document.createElement('option');
                    opt.value = mod; 
                    opt.textContent = mod;
                    selModelo.appendChild(opt);
                }
            }
        }

        function atualizarAnos(){
            const m = document.getElementById('marca').value;
            const mod = document.getElementById('modelo').value;
            const selAno = document.getElementById('ano');
            
            selAno.innerHTML = '<option value="">Selecione o Ano</option>';
            
            if(m && mod && veiculos[m] && veiculos[m][mod]){
                const [ini, fim] = veiculos[m][mod];
                for(let a = fim; a >= ini; a--){
                    const opt = document.createElement('option');
                    opt.value = a; 
                    opt.textContent = a;
                    selAno.appendChild(opt);
                }
            }
        }
    </script>
</body>
</html>
"""

# ============================================================
# ROTAS DE AUTENTICAÇÃO E CADASTRO
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    if request.method == "POST":
        oficina = request.form.get("oficina", "").strip()
        senha = request.form.get("senha", "").strip()

        senha_salva = buscar_senha_oficina(oficina)
        if senha_salva and senha_salva == senha:
            session["oficina_logada"] = oficina
            return redirect(url_for("index"))
        else:
            erro = "Nome da oficina ou senha incorretos."

    return render_template_string(TEMPLATE_LOGIN, erro=erro)

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    erro = None
    if request.method == "POST":
        oficina = request.form.get("oficina", "").strip()
        senha = request.form.get("senha", "").strip()
        confirmar_senha = request.form.get("confirmar_senha", "").strip()

        if not oficina or not senha:
            erro = "Por favor, preencha todos os campos."
        elif senha != confirmar_senha:
            erro = "As senhas informadas não coincidem."
        else:
            sucesso_cadastro = cadastrar_nova_oficina(oficina, senha)
            if sucesso_cadastro:
                return render_template_string(
                    TEMPLATE_LOGIN, 
                    sucesso=f"Oficina '{oficina}' cadastrada com sucesso! Faça login para começar."
                )
            else:
                erro = "Esta oficina já está cadastrada. Faça login ou escolha outro nome."

    return render_template_string(TEMPLATE_CADASTRO, erro=erro)

@app.route("/logout")
def logout():
    session.pop("oficina_logada", None)
    return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
def index():
    if "oficina_logada" not in session:
        return redirect(url_for("login"))

    resultados = []
    termo_busca = ""
    if request.method == "POST":
        peca = request.form.get("peca", "").strip()
        marca = request.form.get("marca", "").strip()
        modelo = request.form.get("modelo", "").strip()
        ano = request.form.get("ano", "").strip()
        comb = request.form.get("combustivel", "").strip()
        
        if peca:
            resultados, termo_busca = gerar_resultados(peca, marca, modelo, ano, comb)

    return render_template_string(
        TEMPLATE_APP,
        oficina_logada=session["oficina_logada"],
        veiculos=VEICULOS,
        veiculos_json=json.dumps(VEICULOS, ensure_ascii=False),
        combustiveis=COMBUSTIVEIS,
        resultados=resultados,
        termo_busca=termo_busca
    )

if __name__ == "__main__":
    print("Iniciando Sistema de Cotação: http://localhost:5000")
    threading.Timer(1.2, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run(debug=False, port=5000)
