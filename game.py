from models.calcular import Calcular

def main() -> None:
    pontos: int = 0
    jogar(pontos)
    
def jogar(pontos: int) -> None:
    dificuldade: int = int(input('Escolha a dificuldade (1, 2 ou 3): '))

    calc: Calcular = Calcular(dificuldade)
    
    print('Informe o resultado para a seguinte operação:')
    calc.mostrar_operacao()
    
    resposta: float = float(input('Informe o resultado: '))
    
    if calc.checar_resultado(resposta):
        pontos += 1
        print(f'Você tem {pontos} pontos.')
    
    continuar: str = input('Deseja continuar jogando? (s/n): ')
    if continuar.lower() == 's':
        jogar(pontos)
    elif continuar.lower() == 'n':
        print(f'Jogo encerrado. Pontos finais: {pontos}')
    else:
        print('Opção inválida. Encerrando o jogo.')
        print(f'Pontos finais: {pontos}')
    
if __name__ == '__main__':
    main()