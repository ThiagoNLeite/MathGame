from models.database import buscar_ranking
from models.calcular import Calcular
q = Calcular.gerar_questao(3)
print(q)
print(Calcular.formatar_enunciado(q))
print(Calcular.calcular_pontos(q, True, 5.0))