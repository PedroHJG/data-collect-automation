import tkinter as tk
from tkinter import ttk, messagebox
import threading

def run_in_main_thread(root, page, func, *args, **kwargs):
    """
    Executa uma função de interface gráfica (dialog) na thread principal e aguarda sua conclusão.
    Utiliza o Playwright para manter o loop de eventos ativo enquanto o dialog está aberto.
    """
    result = {}
    event = threading.Event()
    root.after(0, func, root, result, event, *args, **kwargs)
    
    if page:
        while not event.is_set():
            try:
                page.wait_for_timeout(100)
            except Exception:
                event.wait(0.1)
    else:
        event.wait()
        
    return result

def _dialog_data_operadores(root, result, event):
    """Exibe janela para escolha entre data padrão ou inserção manual de data para coleta de operadores."""
    dialog = tk.Toplevel(root)
    dialog.title("Coleta de Operadores - Data")
    dialog.geometry("380x220")
    dialog.grab_set()

    dialog.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() // 2) - (380 // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (220 // 2)
    dialog.geometry(f"+{x}+{y}")

    ttk.Label(dialog, text="Qual data deseja consultar?", font=("Arial", 10, "bold")).pack(pady=10)

    var_tipo_data = tk.StringVar(value="padrao")
    frame_radios = ttk.Frame(dialog)
    frame_radios.pack(pady=5)
    
    ttk.Radiobutton(frame_radios, text="Parâmetro Padrão (Dia anterior útil)", variable=var_tipo_data, value="padrao").pack(anchor="w", padx=10, pady=2)
    ttk.Radiobutton(frame_radios, text="Data Específica", variable=var_tipo_data, value="especifica").pack(anchor="w", padx=10, pady=2)

    frame_data = ttk.Frame(dialog)
    ttk.Label(frame_data, text="Data (dd/mm/aaaa):").pack(side="left", padx=5)
    entry_data = ttk.Entry(frame_data, width=12)
    entry_data.pack(side="left")

    def on_tipo_change(*args):
        if var_tipo_data.get() == "especifica":
            frame_data.pack(pady=10)
        else:
            frame_data.pack_forget()

    var_tipo_data.trace_add("write", on_tipo_change)

    def on_ok():
        if var_tipo_data.get() == "especifica":
            data_str = entry_data.get().strip()
            # Validação simples
            if len(data_str) != 10 or data_str.count('/') != 2:
                messagebox.showwarning("Aviso", "A data deve estar no formato dd/mm/aaaa", parent=dialog)
                return
            data_alvo = data_str.replace('/', '-')
        else:
            data_alvo = None
            
        result.update({'confirmado': True, 'tipo': var_tipo_data.get(), 'data_alvo': data_alvo})
        dialog.destroy()
        event.set()

    ttk.Button(dialog, text="Confirmar", command=on_ok).pack(pady=15)
    
    def on_close():
        result.update({'confirmado': False})
        dialog.destroy()
        event.set()
        
    dialog.protocol("WM_DELETE_WINDOW", on_close)

def _dialog_mes_ano_padrao(root, result, event):
    """Pergunta ao usuário se deseja utilizar os parâmetros temporais padrões para a coleta de marcos."""
    dialog = tk.Toplevel(root)
    dialog.title("Parâmetros Padrões")
    dialog.geometry("400x150")
    dialog.grab_set()
    
    dialog.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() // 2) - (400 // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (150 // 2)
    dialog.geometry(f"+{x}+{y}")

    ttk.Label(dialog, text="Deseja seguir com os parâmetros padrões\n(Mês de competência e Ano atual)?", justify="center", font=("Arial", 10)).pack(pady=20)

    frame_btns = ttk.Frame(dialog)
    frame_btns.pack()

    def on_yes():
        result.update({'padrao': True, 'cancelado': False})
        dialog.destroy()
        event.set()

    def on_no():
        result.update({'padrao': False, 'cancelado': False})
        dialog.destroy()
        event.set()

    ttk.Button(frame_btns, text="Sim", command=on_yes).pack(side="left", padx=10)
    ttk.Button(frame_btns, text="Não", command=on_no).pack(side="left", padx=10)

    def on_close():
        result.update({'cancelado': True})
        dialog.destroy()
        event.set()

    dialog.protocol("WM_DELETE_WINDOW", on_close)

def _dialog_mes_ano_selecionar(root, result, event, meses_disponiveis, anos_disponiveis):
    """Exibe dropdowns para seleção manual de mês e ano de competência para coleta de marcos."""
    dialog = tk.Toplevel(root)
    dialog.title("Selecionar Mês e Ano")
    dialog.geometry("300x200")
    dialog.grab_set()

    dialog.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() // 2) - (300 // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (200 // 2)
    dialog.geometry(f"+{x}+{y}")

    ttk.Label(dialog, text="Mês:").pack(pady=(15, 0))
    combo_mes = ttk.Combobox(dialog, values=list(meses_disponiveis.keys()), state="readonly")
    if meses_disponiveis: combo_mes.current(0)
    combo_mes.pack(pady=5)

    ttk.Label(dialog, text="Ano:").pack(pady=(5, 0))
    combo_ano = ttk.Combobox(dialog, values=anos_disponiveis, state="readonly")
    if anos_disponiveis: combo_ano.current(0)
    combo_ano.pack(pady=5)

    def on_ok():
        nome_mes = combo_mes.get()
        valor_mes = meses_disponiveis.get(nome_mes)
        valor_ano = combo_ano.get()
        result.update({'cancelado': False, 'mes_val': valor_mes, 'mes_nome': nome_mes, 'ano_val': valor_ano})
        dialog.destroy()
        event.set()

    ttk.Button(dialog, text="Confirmar", command=on_ok).pack(pady=15)

    def on_close():
        result.update({'cancelado': True})
        dialog.destroy()
        event.set()

    dialog.protocol("WM_DELETE_WINDOW", on_close)

def _dialog_esteiras(root, result, event, opcoes):
    """
    Exibe árvore de seleção múltipla para escolha das esteiras e estações a serem processadas.
    """
    dialog = tk.Toplevel(root)
    dialog.title("Selecionar Esteiras e Estações")
    dialog.geometry("500x400")
    dialog.grab_set()
    
    dialog.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() // 2) - (500 // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (400 // 2)
    dialog.geometry(f"+{x}+{y}")

    tree_frame = ttk.Frame(dialog)
    tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

    tree = ttk.Treeview(tree_frame, selectmode="none")
    tree.pack(side="left", fill="both", expand=True)
    
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    scrollbar.pack(side="right", fill="y")
    tree.configure(yscrollcommand=scrollbar.set)

    # Dicionário para rastrear os checkbuttons (nó -> booleano selecionado)
    # Como Treeview não tem checkboxes nativos, usaremos caracteres (✅/❌ ou [X] / [ ])
    # ou podemos colocar botões, ou apenas clicar para selecionar
    # Mais fácil usar seleção múltipla do treeview
    tree.configure(selectmode="extended")
    
    # Agrupar por esteira
    esteiras = {}
    for op in opcoes:
        c_esteira = op['esteira']
        n_esteira = op['nome_esteira']
        c_estacao = op['estacao']
        n_estacao = op['nome_estacao']
        
        if c_esteira not in esteiras:
            esteiras[c_esteira] = {'nome': n_esteira, 'estacoes': []}
        esteiras[c_esteira]['estacoes'].append({'cod': c_estacao, 'nome': n_estacao})

    nodos_estacoes = {}
    for c_est, info in esteiras.items():
        node_id = tree.insert("", "end", text=info['nome'], open=True)
        for estacao in info['estacoes']:
            child_id = tree.insert(node_id, "end", text=estacao['nome'])
            nodos_estacoes[child_id] = (c_est, estacao['cod'])

    lbl_info = ttk.Label(dialog, text="Segure Ctrl/Shift para selecionar várias ou clique em Selecionar Tudo")
    lbl_info.pack(pady=5)

    def on_select_all():
        for child_id in nodos_estacoes.keys():
            tree.selection_add(child_id)
            
    frame_btns_sel = ttk.Frame(dialog)
    frame_btns_sel.pack(pady=5)
    ttk.Button(frame_btns_sel, text="Selecionar Tudo", command=on_select_all).pack(side="left", padx=5)

    def on_ok():
        selecionados = tree.selection()
        if not selecionados:
            messagebox.showwarning("Aviso", "Selecione pelo menos uma estação.", parent=dialog)
            return
            
        selecao_final = {}
        for sel in selecionados:
            if sel in nodos_estacoes:
                c_est, c_estacao = nodos_estacoes[sel]
                if c_est not in selecao_final:
                    selecao_final[c_est] = []
                selecao_final[c_est].append(c_estacao)
                
        # Se usuário selecionou a raiz (esteira), vamos adicionar todos os filhos?
        # A árvore no modo extended também retorna o pai se clicado
        for sel in selecionados:
            if sel not in nodos_estacoes: # é uma esteira (pai)
                for child in tree.get_children(sel):
                    c_est, c_estacao = nodos_estacoes[child]
                    if c_est not in selecao_final:
                        selecao_final[c_est] = []
                    if c_estacao not in selecao_final[c_est]:
                        selecao_final[c_est].append(c_estacao)
        
        result.update({'cancelado': False, 'selecao': selecao_final})
        dialog.destroy()
        event.set()

    ttk.Button(dialog, text="Confirmar Coleta", command=on_ok).pack(pady=10)

    def on_close():
        result.update({'cancelado': True})
        dialog.destroy()
        event.set()

    dialog.protocol("WM_DELETE_WINDOW", on_close)

# Interfaces públicas
def pedir_data_operadores(root, page=None):
    """Interface pública para solicitar data de coleta de operadores."""
    return run_in_main_thread(root, page, _dialog_data_operadores)

def pedir_mes_ano_padrao(root, page=None):
    """Interface pública para confirmar parâmetros padrões de marcos."""
    return run_in_main_thread(root, page, _dialog_mes_ano_padrao)

def selecionar_mes_ano(root, page, meses_disponiveis, anos_disponiveis):
    """Interface pública para seleção manual de mês/ano de marcos."""
    return run_in_main_thread(root, page, _dialog_mes_ano_selecionar, meses_disponiveis, anos_disponiveis)

def selecionar_esteiras(root, page, opcoes):
    """Interface pública para seleção de esteiras e estações."""
    return run_in_main_thread(root, page, _dialog_esteiras, opcoes)
