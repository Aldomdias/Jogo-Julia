# -*- coding: utf-8 -*-
"""
Jogo da Memória da Júlia
Feito em Python com Tkinter.

Como rodar:
1) Instale Python 3.10 ou superior.
2) Opcional, para fala mais natural:
   pip install pyttsx3
3) Rode:
   python jogo_memoria_julia.py

O jogo tem 3 modos:
- Conhecer: clica no item e escuta o nome.
- Memória: encontra os pares e escuta o nome ao virar a carta.
- Ouça e clique: o jogo fala um item e a criança precisa clicar nele.
"""

import random
import platform
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox


# -----------------------------
# CONFIGURAÇÃO DOS ITENS DO JOGO
# Você pode editar, adicionar ou remover itens aqui.
# -----------------------------
ITENS = [
    {"nome": "Cachorro", "emoji": "🐶", "categoria": "Animais"},
    {"nome": "Gato", "emoji": "🐱", "categoria": "Animais"},
    {"nome": "Vaca", "emoji": "🐮", "categoria": "Animais"},
    {"nome": "Porco", "emoji": "🐷", "categoria": "Animais"},
    {"nome": "Leão", "emoji": "🦁", "categoria": "Animais"},
    {"nome": "Macaco", "emoji": "🐵", "categoria": "Animais"},
    {"nome": "Pato", "emoji": "🦆", "categoria": "Animais"},
    {"nome": "Peixe", "emoji": "🐟", "categoria": "Animais"},
    {"nome": "Borboleta", "emoji": "🦋", "categoria": "Animais"},
    {"nome": "Elefante", "emoji": "🐘", "categoria": "Animais"},

    {"nome": "Carro", "emoji": "🚗", "categoria": "Objetos"},
    {"nome": "Bola", "emoji": "⚽", "categoria": "Objetos"},
    {"nome": "Casa", "emoji": "🏠", "categoria": "Objetos"},
    {"nome": "Avião", "emoji": "✈️", "categoria": "Objetos"},
    {"nome": "Livro", "emoji": "📘", "categoria": "Objetos"},
    {"nome": "Estrela", "emoji": "⭐", "categoria": "Objetos"},
    {"nome": "Coração", "emoji": "❤️", "categoria": "Objetos"},
    {"nome": "Banana", "emoji": "🍌", "categoria": "Objetos"},
    {"nome": "Maçã", "emoji": "🍎", "categoria": "Objetos"},

    {"nome": "Mamãe", "emoji": "👩", "categoria": "Pessoas"},
    {"nome": "Papai", "emoji": "👨", "categoria": "Pessoas"},
    {"nome": "Bebê", "emoji": "👶", "categoria": "Pessoas"},
]


class Voz:
    """
    Classe simples para falar os nomes.
    Tenta usar pyttsx3. Se não tiver, no Windows tenta usar a voz do sistema.
    """

    def __init__(self):
        self.engine = None
        self.lock = threading.Lock()

        try:
            import pyttsx3  # type: ignore

            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", 150)
            self.engine.setProperty("volume", 1.0)

            # Tenta escolher uma voz em português, se existir.
            try:
                voices = self.engine.getProperty("voices")
                for voice in voices:
                    info = (voice.name + " " + voice.id).lower()
                    if "portugu" in info or "brazil" in info or "brasil" in info:
                        self.engine.setProperty("voice", voice.id)
                        break
            except Exception:
                pass

            self.tipo = "pyttsx3"
        except Exception:
            self.tipo = "windows" if platform.system().lower() == "windows" else "sem_voz"

    def falar(self, texto: str):
        texto = texto.strip()
        if not texto:
            return

        thread = threading.Thread(target=self._falar_thread, args=(texto,), daemon=True)
        thread.start()

    def _falar_thread(self, texto: str):
        with self.lock:
            if self.tipo == "pyttsx3" and self.engine is not None:
                try:
                    self.engine.say(texto)
                    self.engine.runAndWait()
                    return
                except Exception:
                    pass

            if self.tipo == "windows":
                try:
                    texto_seguro = texto.replace("'", "''")
                    comando = (
                        "Add-Type -AssemblyName System.Speech; "
                        "$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                        "$speak.Rate = -1; "
                        "$speak.Volume = 100; "
                        f"$speak.Speak('{texto_seguro}');"
                    )
                    subprocess.run(
                        ["powershell", "-NoProfile", "-Command", comando],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )
                    return
                except Exception:
                    pass

            print("FALA:", texto)


class JogoDaMemoriaJulia(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Jogo da Memória da Júlia")
        self.geometry("980x680")
        self.minsize(760, 560)
        self.configure(bg="#F8F4FF")

        self.voz = Voz()

        self.modo_atual = "conhecer"
        self.botoes_cartas = []
        self.cartas = []
        self.viradas = []
        self.bloqueado = False
        self.pontos = 0
        self.alvo_atual = None
        self.itens_na_tela = []

        self._montar_layout()
        self.modo_conhecer()

    # -----------------------------
    # LAYOUT PRINCIPAL
    # -----------------------------
    def _montar_layout(self):
        topo = tk.Frame(self, bg="#F8F4FF")
        topo.pack(fill="x", padx=18, pady=14)

        titulo = tk.Label(
            topo,
            text="🎮 Jogo da Júlia",
            font=("Arial", 26, "bold"),
            bg="#F8F4FF",
            fg="#4E008F",
        )
        titulo.pack(side="left")

        botoes = tk.Frame(topo, bg="#F8F4FF")
        botoes.pack(side="right")

        self._botao_menu(botoes, "👆 Conhecer", self.modo_conhecer).pack(side="left", padx=5)
        self._botao_menu(botoes, "🧠 Memória", self.modo_memoria).pack(side="left", padx=5)
        self._botao_menu(botoes, "👂 Ouça e clique", self.modo_ouca_e_clique).pack(side="left", padx=5)

        self.mensagem = tk.StringVar(value="")
        msg = tk.Label(
            self,
            textvariable=self.mensagem,
            font=("Arial", 18, "bold"),
            bg="#F8F4FF",
            fg="#430D95",
            wraplength=900,
            justify="center",
        )
        msg.pack(fill="x", padx=18, pady=(0, 10))

        self.area = tk.Frame(self, bg="#F8F4FF")
        self.area.pack(fill="both", expand=True, padx=18, pady=10)

        rodape = tk.Frame(self, bg="#F8F4FF")
        rodape.pack(fill="x", padx=18, pady=(0, 14))

        self.info = tk.Label(
            rodape,
            text="Dica: para trocar os itens, edite a lista ITENS no início do arquivo.",
            font=("Arial", 11),
            bg="#F8F4FF",
            fg="#666666",
        )
        self.info.pack(side="left")

        self.botao_reiniciar = tk.Button(
            rodape,
            text="🔄 Reiniciar modo",
            font=("Arial", 13, "bold"),
            bg="#04C7A4",
            fg="white",
            activebackground="#04C7A4",
            activeforeground="white",
            relief="flat",
            padx=18,
            pady=8,
            cursor="hand2",
            command=self.reiniciar_modo_atual,
        )
        self.botao_reiniciar.pack(side="right")

    def _botao_menu(self, parent, texto, comando):
        return tk.Button(
            parent,
            text=texto,
            font=("Arial", 12, "bold"),
            bg="#9153F0",
            fg="white",
            activebackground="#6514DE",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=8,
            cursor="hand2",
            command=comando,
        )

    def limpar_area(self):
        for widget in self.area.winfo_children():
            widget.destroy()

        self.botoes_cartas = []
        self.cartas = []
        self.viradas = []
        self.bloqueado = False
        self.pontos = 0
        self.alvo_atual = None
        self.itens_na_tela = []

    def reiniciar_modo_atual(self):
        if self.modo_atual == "conhecer":
            self.modo_conhecer()
        elif self.modo_atual == "memoria":
            self.modo_memoria()
        elif self.modo_atual == "ouca":
            self.modo_ouca_e_clique()

    # -----------------------------
    # MODO 1: CONHECER
    # -----------------------------
    def modo_conhecer(self):
        self.modo_atual = "conhecer"
        self.limpar_area()
        self.mensagem.set("Clique em uma figura para ouvir o nome ❤️")

        itens = random.sample(ITENS, min(12, len(ITENS)))
        self.itens_na_tela = itens

        self._criar_grade_itens(
            itens=itens,
            comando=lambda item: self.falar_item(item),
            mostrar_nome=True,
            colunas=4,
        )

    def falar_item(self, item):
        self.mensagem.set(f"{item['emoji']} {item['nome']}")
        self.voz.falar(item["nome"])

    # -----------------------------
    # MODO 2: JOGO DA MEMÓRIA
    # -----------------------------
    def modo_memoria(self):
        self.modo_atual = "memoria"
        self.limpar_area()
        self.mensagem.set("Encontre os pares! Clique nas cartas para virar 🧠")

        pares = random.sample(ITENS, 6)
        cartas = []

        for item in pares:
            cartas.append({**item, "id_par": item["nome"]})
            cartas.append({**item, "id_par": item["nome"]})

        random.shuffle(cartas)
        self.cartas = cartas

        for idx, item in enumerate(cartas):
            botao = tk.Button(
                self.area,
                text="❔",
                font=("Arial", 30, "bold"),
                bg="#DEB5FF",
                fg="#4E008F",
                activebackground="#BD98F5",
                activeforeground="#4E008F",
                relief="flat",
                width=8,
                height=3,
                cursor="hand2",
                command=lambda i=idx: self.clicar_carta_memoria(i),
            )
            botao.grid(row=idx // 4, column=idx % 4, padx=10, pady=10, sticky="nsew")
            self.botoes_cartas.append(botao)

        for col in range(4):
            self.area.grid_columnconfigure(col, weight=1)
        for row in range(3):
            self.area.grid_rowconfigure(row, weight=1)

    def clicar_carta_memoria(self, indice):
        if self.bloqueado:
            return

        item = self.cartas[indice]
        botao = self.botoes_cartas[indice]

        if item.get("combinada") or item.get("virada"):
            return

        item["virada"] = True
        botao.config(
            text=f"{item['emoji']}\n{item['nome']}",
            bg="#E9DCFC",
            fg="#4E008F",
            font=("Arial", 18, "bold"),
        )
        self.voz.falar(item["nome"])
        self.viradas.append(indice)

        if len(self.viradas) == 2:
            self.bloqueado = True
            self.after(850, self.verificar_par)

    def verificar_par(self):
        i1, i2 = self.viradas
        c1 = self.cartas[i1]
        c2 = self.cartas[i2]

        if c1["id_par"] == c2["id_par"]:
            c1["combinada"] = True
            c2["combinada"] = True

            self.botoes_cartas[i1].config(bg="#04C7A4", fg="white", state="disabled")
            self.botoes_cartas[i2].config(bg="#04C7A4", fg="white", state="disabled")

            self.pontos += 1
            self.mensagem.set(f"Muito bem! Você encontrou: {c1['nome']} ⭐")
            self.voz.falar("Muito bem!")

            if self.pontos == 6:
                self.mensagem.set("Parabéns! Você encontrou todos os pares! 🎉")
                self.voz.falar("Parabéns! Você encontrou todos os pares!")
                messagebox.showinfo("Parabéns!", "Você encontrou todos os pares! 🎉")
        else:
            for i in self.viradas:
                self.cartas[i]["virada"] = False
                self.botoes_cartas[i].config(
                    text="❔",
                    bg="#DEB5FF",
                    fg="#4E008F",
                    font=("Arial", 30, "bold"),
                )

            self.mensagem.set("Quase! Tente de novo 😊")
            self.voz.falar("Tente de novo")

        self.viradas = []
        self.bloqueado = False

    # -----------------------------
    # MODO 3: OUÇA E CLIQUE
    # -----------------------------
    def modo_ouca_e_clique(self):
        self.modo_atual = "ouca"
        self.limpar_area()

        cabecalho = tk.Frame(self.area, bg="#F8F4FF")
        cabecalho.pack(fill="x", pady=(0, 10))

        tk.Button(
            cabecalho,
            text="🔊 Ouvir novamente",
            font=("Arial", 14, "bold"),
            bg="#04C7A4",
            fg="white",
            activebackground="#04C7A4",
            activeforeground="white",
            relief="flat",
            padx=18,
            pady=8,
            cursor="hand2",
            command=self.falar_alvo,
        ).pack()

        grade = tk.Frame(self.area, bg="#F8F4FF")
        grade.pack(fill="both", expand=True)

        self.grade_ouca = grade

        itens = random.sample(ITENS, min(9, len(ITENS)))
        self.itens_na_tela = itens

        for idx, item in enumerate(itens):
            botao = tk.Button(
                grade,
                text=f"{item['emoji']}\n{item['nome']}",
                font=("Arial", 20, "bold"),
                bg="#E9DCFC",
                fg="#4E008F",
                activebackground="#BD98F5",
                activeforeground="#4E008F",
                relief="flat",
                width=9,
                height=3,
                cursor="hand2",
                command=lambda it=item: self.clicar_ouca(it),
            )
            botao.grid(row=idx // 3, column=idx % 3, padx=10, pady=10, sticky="nsew")

        for col in range(3):
            grade.grid_columnconfigure(col, weight=1)
        for row in range(3):
            grade.grid_rowconfigure(row, weight=1)

        self.novo_alvo()

    def novo_alvo(self):
        self.alvo_atual = random.choice(self.itens_na_tela)
        self.mensagem.set("Escute e clique na figura certa 👂")
        self.after(400, self.falar_alvo)

    def falar_alvo(self):
        if self.alvo_atual:
            frase = f"Encontre {self.alvo_atual['nome']}"
            self.mensagem.set(f"🔊 {frase}")
            self.voz.falar(frase)

    def clicar_ouca(self, item):
        if not self.alvo_atual:
            return

        if item["nome"] == self.alvo_atual["nome"]:
            self.mensagem.set(f"Acertou! Era {item['emoji']} {item['nome']} 🎉")
            self.voz.falar("Muito bem!")
            self.after(1200, self.novo_alvo)
        else:
            self.mensagem.set(f"Esse é {item['nome']}. Tente encontrar {self.alvo_atual['nome']} 😊")
            self.voz.falar(f"Esse é {item['nome']}. Tente de novo.")

    # -----------------------------
    # GRADE DE BOTÕES GENÉRICA
    # -----------------------------
    def _criar_grade_itens(self, itens, comando, mostrar_nome=True, colunas=4):
        for idx, item in enumerate(itens):
            texto = f"{item['emoji']}\n{item['nome']}" if mostrar_nome else item["emoji"]

            botao = tk.Button(
                self.area,
                text=texto,
                font=("Arial", 20, "bold"),
                bg="#E9DCFC",
                fg="#4E008F",
                activebackground="#BD98F5",
                activeforeground="#4E008F",
                relief="flat",
                width=10,
                height=4,
                cursor="hand2",
                command=lambda it=item: comando(it),
            )
            botao.grid(row=idx // colunas, column=idx % colunas, padx=10, pady=10, sticky="nsew")

        linhas = (len(itens) + colunas - 1) // colunas

        for col in range(colunas):
            self.area.grid_columnconfigure(col, weight=1)
        for row in range(linhas):
            self.area.grid_rowconfigure(row, weight=1)


if __name__ == "__main__":
    app = JogoDaMemoriaJulia()
    app.mainloop()
