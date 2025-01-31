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

    def calcular_entrada(self, payout):
        if self.sequencia_loss >= 3:
            # Calcula a entrada exata para atingir o stopwin considerando o payout
            valor_para_stopwin = max(0, (self.stopwin + self.banca_inicial) - self.banca)
            entrada_necessaria = valor_para_stopwin / payout
            return max(entrada_necessaria, self.entrada_minima)  # Mantém a entrada mínima
        return self.entrada_minima

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
