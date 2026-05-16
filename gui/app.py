import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import exceptions
from core.logger import get_logger
from automations.operadores import executar_coleta_operadores
from automations.marcos import executar_coleta_marcos
from automations.atualizarPlanilhaPC import executar_atualizacao_planilha

logger = get_logger()

class Application(tk.Tk):
    """
    Classe principal da interface gráfica.
    Gerencia a janela principal, a seleção de automações e o progresso.
    """
    def __init__(self):
        super().__init__()
        self.title("PraContar Automações")
        self.geometry("500x350")
        self.eval('tk::PlaceWindow . center')
        self.configurar_icone()
        
        self.init_ui()

    def configurar_icone(self):
        """Define o ícone da barra de título a partir da pasta public."""
        caminho_icone = os.path.join("public", "icon.png")
        
        if os.path.exists(caminho_icone):
            try:
                # Para arquivos PNG, usamos iconphoto
                self.img_icon = tk.PhotoImage(file=caminho_icone)
                self.iconphoto(False, self.img_icon)
            except Exception as e:
                print(f"Erro ao carregar ícone: {e}")
        else:
            print(f"Aviso: O arquivo {caminho_icone} não foi encontrado.")

    def init_ui(self):
        """Inicializa os componentes visuais da janela principal."""
        ttk.Label(self, text="Selecione a automação desejada", font=("Arial", 14, "bold")).pack(pady=20)

        self.var_opcao = tk.StringVar(value="operadores")
        
        frame_opcoes = ttk.Frame(self)
        frame_opcoes.pack(pady=10)

        ttk.Radiobutton(frame_opcoes, text="Coleta de Operadores", 
                        variable=self.var_opcao, value="operadores").pack(anchor="w", pady=5)
        ttk.Radiobutton(frame_opcoes, text="Coleta de Marcos", 
                        variable=self.var_opcao, value="marcos").pack(anchor="w", pady=5)
        ttk.Radiobutton(frame_opcoes, text="Atualizar Planilha Produtividade", 
                        variable=self.var_opcao, value="atualizar_planilha").pack(anchor="w", pady=5)

        self.btn_executar = ttk.Button(self, text="Executar", command=self.on_executar)
        self.btn_executar.pack(pady=30)

        self.lbl_status = ttk.Label(self, text="", font=("Arial", 9, "italic"))
        self.lbl_status.pack(pady=5)

        # Frame de progresso (oculto inicialmente)
        self.frame_progresso = ttk.Frame(self)
        self.lbl_progresso_texto = ttk.Label(self.frame_progresso, text="", font=("Arial", 9))
        self.lbl_progresso_texto.pack(pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(self.frame_progresso, orient="horizontal", 
                                           mode="determinate", length=300)
        self.progress_bar.pack()

    def on_executar(self):
        """Trata o clique no botão Executar em uma thread secundária."""
        opcao = self.var_opcao.get()
        self.btn_executar.config(state="disabled")
        self.lbl_status.config(text="Rodando automação... (Não feche a janela)")
        self.frame_progresso.pack(pady=10)
        self.progress_bar["value"] = 0
        self.lbl_progresso_texto.config(text="Iniciando...")

        if opcao == "operadores":
            t = threading.Thread(target=self.run_automation, args=(executar_coleta_operadores,))
        elif opcao == "marcos":
            t = threading.Thread(target=self.run_automation, args=(executar_coleta_marcos,))
        elif opcao == "atualizar_planilha":
            t = threading.Thread(target=self.run_automation, args=(executar_atualizacao_planilha,))
        else:
            return
            
        t.daemon = True # Garante que a thread feche se a janela principal fechar
        t.start()

    def run_automation(self, func):
        """Executa a lógica da automação e gerencia feedbacks visuais."""
        try:
            func(self)
            self.after(0, lambda: messagebox.showinfo("Sucesso", "Automação finalizada com sucesso!"))
        except exceptions.BaseAutomationException as e:
            logger.warning(f"Execução interrompida (Tratado): {e}")
            err_msg = str(e)
            self.after(0, lambda err=err_msg: messagebox.showwarning("Interrupção da Automação", err))
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.critical(f"Crash inesperado: {e}", exc_info=True)
            err_msg = str(e)
            self.after(0, lambda err=err_msg: messagebox.showerror("Erro Crítico", f"Erro interno inesperado.\n{err}"))
        finally:
            self.after(0, self.reset_ui)

    def reset_ui(self):
        """Restaura o estado inicial da interface."""
        self.btn_executar.config(state="normal")
        self.lbl_status.config(text="")
        self.frame_progresso.pack_forget()

    def update_progress(self, current, total, message):
        """Atualiza a barra de progresso (thread-safe)."""
        def _update():
            self.lbl_progresso_texto.config(text=message)
            if total > 0:
                self.progress_bar["maximum"] = total
                self.progress_bar["value"] = current
            else:
                self.progress_bar["value"] = 0
        self.after(0, _update)

if __name__ == "__main__":
    app = Application()
    app.mainloop()
