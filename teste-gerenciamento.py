import random
import pandas as pd
from tabulate import tabulate

class GerenciamentoConservador:
    def __init__(self, banca_inicial, stopwin_percentual):
        self.banca_inicial = banca_inicial
        self.banca = banca_inicial
        self.entrada_minima = 5
        self.stopwin = banca_inicial * (stopwin_percentual / 100)
        self.prejuizo_acumulado = 0
        self.sequencia_loss = 0
        self.operacoes = []
        self.maior_prejuizo_durante_operacoes = 0
        self.payouts = [0.80, 0.90]  # Alternância de payouts

    def realizar_operacao(self, resultado, payout):
        entrada = self.calcular_entrada(payout)

        if entrada > self.banca:
            entrada = self.banca

        if resultado == "loss":
            self.prejuizo_acumulado += entrada
            self.sequencia_loss += 1
            self.banca -= entrada
        elif resultado == "win":
            lucro = entrada * payout
            self.prejuizo_acumulado = 0
            self.sequencia_loss = 0
            self.banca += lucro

        self.maior_prejuizo_durante_operacoes = min(self.maior_prejuizo_durante_operacoes, -self.prejuizo_acumulado)
        self.operacoes.append((entrada, resultado, payout, self.banca))
        print(f"Operação: {len(self.operacoes)} | Entrada: R${entrada:.2f} | Resultado: {resultado.upper()} | "
              f"Payout: {payout * 100:.0f}% | Banca: R${self.banca:.2f}")

        lucro_total = self.banca - self.banca_inicial

        if self.banca < 5:
            print("STOPLOSS ATINGIDO!!!")
            return "STOPLOSS"

        # Condição de Stopwin
        if lucro_total >= self.stopwin:
            print("STOPWIN ATINGIDO!!!")
            return "STOPWIN"

        return None

    def calculate_dynamic_entry(self, qx, qx_manager, payout):
        """
        Calcula o valor da entrada com base no gerenciamento ativo, conforme a seguinte regra:
        Se houver 3 Loss seguidos:
            Entrada = max( (stopwin + banca_inicial - banca) / payout, entrada_minima )
        Caso contrário:
            Entrada = entrada_minima
        Onde:
        - banca_inicial: saldo inicial (registrado no gerenciamento, ou, se não existir, usa o saldo atual)
        - banca: saldo atual da conta do trader (qx)
        - stopwin: valor definido em qx_manager.stop_gain (meta de ganho)
        - entrada_minima: valor mínimo de entrada definido (qx_manager.entry_minima)
        - payout: valor do payout (porcentagem, ex.: 80 para 80%)
        """
        from decimal import Decimal

        # Obter valores do gerenciamento; se algum atributo não existir, usamos defaults:
        entry_minima = Decimal(getattr(qx_manager, "entry_minima", "5"))
        stopwin = Decimal(getattr(qx_manager, "stop_gain", "8"))
        # Tente obter banca_inicial; se não estiver definido, usa o saldo atual.
        banca_inicial = Decimal(getattr(qx_manager, "banca_inicial", 
                                        qx.real_balance if qx.account_type == "REAL" else qx.demo_balance))
        # Saldo atual ("banca")
        banca = Decimal(qx.real_balance) if qx.account_type == "REAL" else Decimal(qx.demo_balance)
        
        # Converte o payout para Decimal (payout é em porcentagem; por exemplo, 80 significa 80%)
        payout_decimal = Decimal(str(payout))
        
        # Se houver 3 perdas consecutivas, calcular a entrada de recuperação:
        if self.loss_streak >= 3:
            # Valor necessário para atingir o Stopwin: (stopwin + banca_inicial - banca)
            valor_para_stopwin = max(Decimal("0"), (stopwin + banca_inicial) - banca)
            # Entrada necessária, ajustada pelo payout:
            entrada_necessaria = valor_para_stopwin / payout_decimal
            # Retorna o maior entre a entrada necessária e a entrada mínima
            return float(max(entrada_necessaria, entry_minima))
        else:
            return float(entry_minima)


    def simular_operacoes(self, taxa_acerto):
        stop_status = None
        operacao_count = 0
        while stop_status is None:
            payout = self.payouts[operacao_count % len(self.payouts)]  # Alterna entre 80% e 90%
            resultado = "win" if random.random() < (taxa_acerto / 100) else "loss"
            stop_status = self.realizar_operacao(resultado, payout)
            operacao_count += 1
        return stop_status


def executar_simulacao():
    historico_simulacoes = []
    stopwin_count = 0
    stoploss_count = 0

    while True:
        banca_inicial = 100
        stopwin_percentual = 8
        taxa_acerto = float(input("Digite a taxa de acerto desejada (em %): "))

        bot = GerenciamentoConservador(banca_inicial, stopwin_percentual)
        stop_status = bot.simular_operacoes(taxa_acerto)

        if stop_status == "STOPWIN":
            stopwin_count += 1
        else:
            stoploss_count += 1

        lucro_prejuizo = bot.banca - banca_inicial

        historico_simulacoes.append({
            "Simulação": len(historico_simulacoes) + 1,
            "Taxa de Acerto (%)": taxa_acerto,
            "Banca Final": f"R${bot.banca:.2f}",
            "Maior Prejuízo": f"R${bot.maior_prejuizo_durante_operacoes:.2f}",
            "Operações Realizadas": len(bot.operacoes),
            "Payouts (%)": ', '.join(f"{payout * 100:.0f}%" for _, _, payout, _ in bot.operacoes),
            "Stop": "Stop Loss" if stop_status == "STOPLOSS" else "Stop Win",
            "Lucro/Prejuízo": f"R${lucro_prejuizo:.2f}"
        })

        continuar = input("Deseja realizar outra simulação? (s/n): ").strip().lower()
        if continuar != 's':
            break

    df_resultados = pd.DataFrame(historico_simulacoes)

    print("\nResumo das Simulações:")
    print(tabulate(df_resultados, headers="keys", tablefmt="fancy_grid", numalign="center"))
    resultado_final = sum(float(d["Lucro/Prejuízo"].replace("R$", "")) for d in historico_simulacoes)

    print(f"\nNúmero de STOPWINs: {stopwin_count}")
    print(f"Número de STOPLOSSs: {stoploss_count}")
    print(f"Resultado final (Lucro/Prejuízo Total): R${resultado_final:.2f}")


if __name__ == "__main__":
    executar_simulacao()
