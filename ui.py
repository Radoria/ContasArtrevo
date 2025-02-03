import sys
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QMessageBox, QDialog, QVBoxLayout, QLineEdit, QComboBox, QPushButton, QDateEdit, QWidget, QHBoxLayout, QFileDialog
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QDoubleValidator, QColor
from database import conectar, adicionar_conta, listar_contas, editar_conta, excluir_conta
import pandas as pd
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton

VERSION = "1.0.0"  # Defina a versão do seu programa

# Janela de cadastro/edição de contas
class CadastroContaDialog(QDialog):
    def __init__(self, parent=None, conta=None):
        super().__init__(parent)
        self.setWindowTitle("Cadastrar/Editar Conta")
        self.setModal(True)
        self.conta = conta

        # Layout
        layout = QVBoxLayout(self)

        # Campos do formulário
        self.txtNome = QLineEdit(self)
        self.txtNome.setPlaceholderText("Nome da Conta")
        layout.addWidget(self.txtNome)

        self.txtValor = QLineEdit(self)
        self.txtValor.setPlaceholderText("Valor (R$)")
        self.txtValor.setValidator(QDoubleValidator(0, 999999, 2, self))  # Aceita apenas números com 2 casas decimais
        layout.addWidget(self.txtValor)

        self.dateVencimento = QDateEdit(self)
        self.dateVencimento.setCalendarPopup(True)
        self.dateVencimento.setDate(QDate.currentDate())
        layout.addWidget(self.dateVencimento)

        self.comboRecorrencia = QComboBox(self)
        self.comboRecorrencia.addItems(["Única", "Mensal", "Anual"])
        layout.addWidget(self.comboRecorrencia)

        # Botão de salvar
        btnSalvar = QPushButton("Salvar", self)
        btnSalvar.clicked.connect(self.salvar_conta)
        layout.addWidget(btnSalvar)

        # Preencher campos se estiver editando
        if self.conta:
            self.txtNome.setText(self.conta["nome"])
            self.txtValor.setText(f"{self.conta['valor']:.2f}")
            self.dateVencimento.setDate(QDate.fromString(self.conta["data_vencimento"], "dd/MM/yyyy"))
            self.comboRecorrencia.setCurrentText(self.conta["recorrencia"])

    def salvar_conta(self):
        nome = self.txtNome.text()
        valor = self.txtValor.text().replace(",", ".")
        data_vencimento = self.dateVencimento.date().toString("dd/MM/yyyy")
        recorrencia = self.comboRecorrencia.currentText()

        if not nome or not valor:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos!")
            return

        try:
            valor = float(valor)
        except ValueError:
            QMessageBox.warning(self, "Erro", "Valor inválido!")
            return

        self.conta = {
            "nome": nome,
            "valor": valor,
            "data_vencimento": data_vencimento,
            "recorrencia": recorrencia
        }
        self.accept()

# Janela principal (dashboard)
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('artrevo.ico'))
        self.setWindowTitle(f"Contas a Pagar Artrevo - Versão {VERSION}")
        self.setGeometry(100, 100, 800, 600)

        # Conectar ao banco de dados
        self.conn = conectar()

        # Layout principal
        layout = QVBoxLayout()

        # Filtros de data (alinhados à direita)
        filtro_layout = QHBoxLayout()
        filtro_layout.addStretch()  # Adiciona espaço à esquerda

        self.dateInicial = QDateEdit(self)
        self.dateInicial.setCalendarPopup(True)
        self.dateInicial.setDate(QDate.currentDate())
        self.dateInicial.setFixedWidth(100)  # Reduzir o tamanho
        filtro_layout.addWidget(self.dateInicial)

        self.dateFinal = QDateEdit(self)
        self.dateFinal.setCalendarPopup(True)
        self.dateFinal.setDate(QDate.currentDate())
        self.dateFinal.setFixedWidth(100)  # Reduzir o tamanho
        filtro_layout.addWidget(self.dateFinal)

        btnFiltrar = QPushButton("Filtrar", self)
        btnFiltrar.setFixedWidth(80)  # Reduzir o tamanho
        btnFiltrar.clicked.connect(self.filtrar_contas)
        filtro_layout.addWidget(btnFiltrar)

        layout.addLayout(filtro_layout)

        # Tabela para exibir contas
        self.tableContas = self.criar_tabela()
        layout.addWidget(self.tableContas)

        # Botões de ação (alinhados à direita)
        botoes_layout = QHBoxLayout()
        botoes_layout.addStretch()  # Adiciona espaço à esquerda

        btnCadastrar = QPushButton("Cadastrar Conta", self)
        btnCadastrar.setFixedWidth(120)  # Reduzir o tamanho
        btnCadastrar.clicked.connect(self.abrir_cadastro)
        botoes_layout.addWidget(btnCadastrar)

        btnEditar = QPushButton("Editar Conta", self)
        btnEditar.setFixedWidth(100)  # Reduzir o tamanho
        btnEditar.clicked.connect(self.editar_conta)
        botoes_layout.addWidget(btnEditar)

        btnExcluir = QPushButton("Excluir Conta", self)
        btnExcluir.setFixedWidth(100)  # Reduzir o tamanho
        btnExcluir.clicked.connect(self.excluir_conta)
        botoes_layout.addWidget(btnExcluir)

        btnExportar = QPushButton("Exportar para Excel", self)
        btnExportar.setFixedWidth(120)  # Reduzir o tamanho
        btnExportar.clicked.connect(self.exportar_excel)
        botoes_layout.addWidget(btnExportar)

        layout.addLayout(botoes_layout)

        # Centralizar layout na janela
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Exibir todas as contas inicialmente
        self.exibir_contas(listar_contas(self.conn))

    def criar_tabela(self):
        table = QTableWidget(self)
        table.setColumnCount(5)  # 5 colunas: Nome, Valor, Vencimento, Status, Ações
        table.setHorizontalHeaderLabels(["Nome", "Valor (R$)", "Vencimento", "Status", "Ações"])
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        return table

    def exibir_contas(self, contas):
        self.tableContas.setRowCount(len(contas))
        for i, conta in enumerate(contas):
            self.tableContas.setItem(i, 0, QTableWidgetItem(conta["nome"]))
            self.tableContas.setItem(i, 1, QTableWidgetItem(f"R$ {conta['valor']:.2f}"))
            self.tableContas.setItem(i, 2, QTableWidgetItem(conta["data_vencimento"]))
            self.tableContas.setItem(i, 3, QTableWidgetItem(conta["status"]))

            # Botão para marcar como paga/pendente
            btn_status = QPushButton("Marcar como Paga" if conta["status"] == "Pendente" else "Marcar como Pendente")
            btn_status.clicked.connect(lambda _, row=i: self.alternar_status(row))
            self.tableContas.setCellWidget(i, 4, btn_status)

            # Aplicar cores com base no status e data de vencimento
            self.colorir_linha(i, conta["data_vencimento"], conta["status"])

    def colorir_linha(self, row, data_vencimento, status):
        try:
            data_vencimento_obj = datetime.strptime(data_vencimento, "%Y-%m-%d").date()  # Agora só precisa desse formato
        except ValueError:
            QMessageBox.warning(self, "Erro", f"Data inválida detectada: {data_vencimento}")
            return

        hoje = datetime.now().date()

        if status == "Paga":
            return  # Não altera a cor

        if data_vencimento_obj < hoje:
            self.tableContas.item(row, 2).setBackground(QColor(255, 0, 0))  # Vermelho: vencida e não paga
        elif data_vencimento_obj == hoje:
            self.tableContas.item(row, 2).setBackground(QColor(255, 255, 0))  # Amarelo: vencendo hoje
        else:
            self.tableContas.item(row, 2).setBackground(QColor(0, 255, 0))  # Verde: à vencer

    def alternar_status(self, row):
        conta = listar_contas(self.conn)[row]
        novo_status = "Paga" if conta["status"] == "Pendente" else "Pendente"
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE contas
        SET status = ?
        WHERE id = ?
        ''', (novo_status, conta["id"]))
        self.conn.commit()
        self.exibir_contas(listar_contas(self.conn))

    def filtrar_contas(self):
        data_inicial_sql = self.dateInicial.date().toString("yyyy-MM-dd")
        data_final_sql = self.dateFinal.date().toString("yyyy-MM-dd")

        # Verificar se a data inicial é maior que a data final
        if self.dateInicial.date() > self.dateFinal.date():
            QMessageBox.warning(self, "Erro", "A data inicial não pode ser maior que a data final!")
            return

        # Filtrar contas no período
        contas_filtradas = listar_contas(self.conn, data_inicial_sql, data_final_sql)
        self.exibir_contas(contas_filtradas)

    
    def abrir_cadastro(self, conta=None):
        dialog = CadastroContaDialog(self, conta)
        if dialog.exec() == QDialog.Accepted:
            if conta:
                # Atualizar conta existente
                editar_conta(self.conn, conta["id"], dialog.conta["nome"], dialog.conta["valor"], dialog.conta["data_vencimento"], dialog.conta["recorrencia"])
            else:
                # Adicionar nova conta
                adicionar_conta(self.conn, dialog.conta["nome"], dialog.conta["valor"], dialog.conta["data_vencimento"], dialog.conta["recorrencia"])
            self.exibir_contas(listar_contas(self.conn))

    def editar_conta(self):
        selected_row = self.tableContas.currentRow()
        if selected_row >= 0:
            conta = listar_contas(self.conn)[selected_row]
            self.abrir_cadastro(conta)
        else:
            QMessageBox.warning(self, "Erro", "Selecione uma conta para editar!")

    def excluir_conta(self):
        selected_row = self.tableContas.currentRow()
        if selected_row >= 0:
            conta = listar_contas(self.conn)[selected_row]
            reply = QMessageBox.question(
                self, "Excluir Conta", "Tem certeza que deseja excluir esta conta?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                excluir_conta(self.conn, conta["id"])
                self.exibir_contas(listar_contas(self.conn))
        else:
            QMessageBox.warning(self, "Erro", "Selecione uma conta para excluir!")

    def exportar_excel(self):
        contas = listar_contas(self.conn)
        df = pd.DataFrame(contas)
        df = df[["nome", "valor", "data_vencimento", "status"]]  # Selecionar colunas relevantes

        # Salvar o arquivo
        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar como", "", "Excel Files (*.xlsx)")
        if file_path:
            df.to_excel(file_path, index=False)
            QMessageBox.information(self, "Sucesso", "Dados exportados com sucesso!")

# Executar a aplicação
if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()

