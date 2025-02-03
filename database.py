import sqlite3
from datetime import datetime, timedelta

def conectar():
    """Cria a conexão com o banco de dados e a tabela, se não existir."""
    conn = sqlite3.connect('contas.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        valor REAL NOT NULL,
        data_vencimento TEXT NOT NULL,
        recorrencia TEXT,
        status TEXT DEFAULT 'Pendente'
    )
    ''')
    conn.commit()
    return conn

def adicionar_conta(conn, nome, valor, data_vencimento, recorrencia):
    """Adiciona uma nova conta ao banco, garantindo que a data seja salva em YYYY-MM-DD."""
    cursor = conn.cursor()
    
    # Converter a data para o formato YYYY-MM-DD antes de salvar no banco
    data_vencimento_sql = datetime.strptime(data_vencimento, "%d/%m/%Y").strftime("%Y-%m-%d")

    if recorrencia == "Mensal":
        for i in range(12):  # Criar 12 contas mensais
            nova_data = (datetime.strptime(data_vencimento, "%d/%m/%Y") + timedelta(days=30 * i)).strftime("%Y-%m-%d")
            cursor.execute('''
            INSERT INTO contas (nome, valor, data_vencimento, recorrencia, status)
            VALUES (?, ?, ?, ?, ?)
            ''', (nome, valor, nova_data, recorrencia, "Pendente"))
    elif recorrencia == "Anual":
        for i in range(5):  # Criar 5 contas anuais
            nova_data = (datetime.strptime(data_vencimento, "%d/%m/%Y").replace(year=datetime.strptime(data_vencimento, "%d/%m/%Y").year + i)).strftime("%Y-%m-%d")
            cursor.execute('''
            INSERT INTO contas (nome, valor, data_vencimento, recorrencia, status)
            VALUES (?, ?, ?, ?, ?)
            ''', (nome, valor, nova_data, recorrencia, "Pendente"))
    else:  # Conta única
        cursor.execute('''
        INSERT INTO contas (nome, valor, data_vencimento, recorrencia, status)
        VALUES (?, ?, ?, ?, ?)
        ''', (nome, valor, data_vencimento_sql, recorrencia, "Pendente"))

    conn.commit()

def listar_contas(conn, data_inicial=None, data_final=None):
    """Lista todas as contas cadastradas no banco, filtrando por data se necessário."""
    cursor = conn.cursor()
    
    if data_inicial and data_final:
        cursor.execute('''
        SELECT * FROM contas
        WHERE date(data_vencimento) BETWEEN date(?) AND date(?)
        ''', (data_inicial, data_final))
    else:
        cursor.execute('SELECT * FROM contas')

    # Converter tuplas em dicionários
    colunas = [desc[0] for desc in cursor.description]
    return [dict(zip(colunas, row)) for row in cursor.fetchall()]

def editar_conta(conn, id, nome, valor, data_vencimento, recorrencia):
    """Edita uma conta existente no banco."""
    cursor = conn.cursor()
    
    # Converter para o formato correto
    data_vencimento_sql = datetime.strptime(data_vencimento, "%d/%m/%Y").strftime("%Y-%m-%d")
    
    cursor.execute('''
    UPDATE contas
    SET nome = ?, valor = ?, data_vencimento = ?, recorrencia = ?
    WHERE id = ?
    ''', (nome, valor, data_vencimento_sql, recorrencia, id))
    conn.commit()

def excluir_conta(conn, id):
    """Exclui uma conta do banco."""
    cursor = conn.cursor()
    cursor.execute('DELETE FROM contas WHERE id = ?', (id,))
    conn.commit()