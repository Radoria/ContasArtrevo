import sys
from PySide6.QtWidgets import QApplication
from ui import MainWindow  # Importa a janela principal da interface gráfica

# Função principal
def main():
    # Cria a aplicação
    app = QApplication(sys.argv)

    # Cria e exibe a janela principal
    window = MainWindow()
    window.show()

    # Executa a aplicação
    sys.exit(app.exec())

# Ponto de entrada do programa
if __name__ == "__main__":
    main()