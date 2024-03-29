import pygame
import os
import random
import neat


ai_jogando = True
geracao = 0

TELA_LARGURA = 500
TELA_ALTURA = 800

IMAGEM_CANO = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'pipe.png')))
IMAGEM_CHAO = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'base.png')))
IMAGEM_BACKGROUND = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bg.png')))
IMAGENS_PASSARO = [
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird1.png'))),
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird2.png'))),
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird3.png')))
]

pygame.font.init()
FONTE_PONTOS = pygame.font.SysFont('arial', 40)


class Passaro:
    IMGS = IMAGENS_PASSARO
    #animações da rotação
    ANGULO_MAX = 25
    VELOCIDADE_ROTACAO = 20
    TEMPO_ANIMACAO = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angulo = 0
        self.velocidade = 0
        self.altura = self.y
        self.tempo = 0
        self.contagem_imagem = 0
        self.imagem = self.IMGS[0]

    def pular(self): #basicamente esta função reseta a variável deslocamento da função mover
        self.velocidade = -10.5
        self.tempo = 0
        self.altura = self.y #o atributo altura é atualizado somente depois que o passáro pula

    def mover(self):
        #calcular o deslocamento
        self.tempo += 1
        accel = 1.5
        deslocamento = accel * (self.tempo**2) + self.velocidade * self.tempo #fórmula do sovetão

        #restringir o deslocamento
        if deslocamento > 16: #setando o deslocamento máximo para 16 pixels
            deslocamento = 16
        elif deslocamento < 0: #se o passáro estiver se deslocando para cima(pulando) adicione 1.5 no seu deslocamento
            deslocamento -= 1.5

        self.y += deslocamento

        #ângulo do pássaro
        if deslocamento < 0 or self.y < (self.altura + 50): #se estiver pulando ou se a posição em y for acima da sua altura inicial antes do pulo
            if self.angulo < self.ANGULO_MAX:
                self.angulo = self.ANGULO_MAX
        else:
            if self.angulo > -90:
                self.angulo -= self.VELOCIDADE_ROTACAO

    def desenhar(self, tela):
        #definir qual a imagem do pássaro que vamos usar
        self.contagem_imagem += 1

        #início da descida da asa
        if self.contagem_imagem < self.TEMPO_ANIMACAO: #antes dos 5 frames
            self.imagem = self.IMGS[0]
        elif self.contagem_imagem < self.TEMPO_ANIMACAO*2: #antes dos 10 frames
            self.imagem = self.IMGS[1]
        elif self.contagem_imagem < self.TEMPO_ANIMACAO*3: #antes dos 15 frames
            self.imagem = self.IMGS[2]
        #levantando a asa
        elif self.contagem_imagem < self.TEMPO_ANIMACAO*4:
            self.imagem = self.IMGS[1]
        elif self.contagem_imagem >= self.TEMPO_ANIMACAO*4 + 1:
            self.imagem = self.IMGS[0]
            self.contagem_imagem = 0 #reseta a contagem

        #se o pássaro tiver caindo não vai bater a asa
        if self.angulo <= -80:
            self.imagem = self.IMGS[1] #deixar a asa parada no meio
            self.contagem_imagem = self.TEMPO_ANIMACAO*2 #garantindo que a próxima animação é a batida de asa para baixo

        #desenhar a imagem
        imagem_rotacionada = pygame.transform.rotate(self.imagem, self.angulo)
        pos_centro_imagem = self.imagem.get_rect(topleft=(self.x, self.y)).center
        retangulo = imagem_rotacionada.get_rect(center=pos_centro_imagem)
        tela.blit(imagem_rotacionada, retangulo.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.imagem) #definindo a máscara do pássaro para colisão


class Cano:
    DISTANCIA = 200 #distância entre cano inferior e superior em pixels
    VELOCIDADE = 5
    VEL_VERTICAL = 3

    def __init__(self, x):
        self.x = x
        self.altura = 0
        self.pos_topo = 0
        self.pos_base = 0
        self.IMG_CANO_TOPO = pygame.transform.flip(IMAGEM_CANO, False, True)
        self.IMG_CANO_BASE = IMAGEM_CANO
        self.passou = False
        self.definir_altura() #roda a função na criação do objeto cano
        self.sentido = random.randint(0,1)


    def definir_altura(self):
        self.altura = random.randrange(50, 450)
        self.pos_topo = self.altura - self.IMG_CANO_TOPO.get_height()
        self.pos_base = self.altura + self.DISTANCIA

    def mover(self):
        self.x -= self.VELOCIDADE

    def mover_vertical(self):
        if (self.pos_topo + self.IMG_CANO_TOPO.get_height()) <= 450 and self.sentido == 1:
            self.pos_topo += self.VEL_VERTICAL
            self.pos_base += self.VEL_VERTICAL
        elif (self.pos_topo + self.IMG_CANO_TOPO.get_height()) >= 70 and self.sentido == 0:
            self.pos_topo -= self.VEL_VERTICAL
            self.pos_base -= self.VEL_VERTICAL

    def alterar_mov_vertical(self):
        posicao_cano = self.pos_topo + self.IMG_CANO_TOPO.get_height()
        if 425 < posicao_cano <= 460:
            self.sentido = 0
        if 50 <= posicao_cano < 95:
            self.sentido = 1

    def desenhar(self, tela):
        tela.blit(self.IMG_CANO_TOPO, (self.x, self.pos_topo))
        tela.blit(self.IMG_CANO_BASE, (self.x, self.pos_base))

    def colidir(self, passaro):
        passaro_mask = passaro.get_mask()
        topo_mask = pygame.mask.from_surface(self.IMG_CANO_TOPO)
        base_mask = pygame.mask.from_surface(self.IMG_CANO_BASE)

        distancia_topo = (self.x - passaro.x, self.pos_topo - round(passaro.y))
        distancia_base = (self.x - passaro.x, self.pos_base - round(passaro.y))

        #as duas variáveis abaixo são True (se existe um ponto de colisão) ou False (se não existir colisão)
        topo_colisao = passaro_mask.overlap(topo_mask, distancia_topo)
        base_colisao = passaro_mask.overlap(base_mask, distancia_base)

        if base_colisao or topo_colisao:
            return True
        else:
            return False


class Chao:
    VELOCIDADE = 5 #precisa ser o mesmo do cano
    LARGURA = IMAGEM_CHAO.get_width()
    IMAGEM = IMAGEM_CHAO

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.LARGURA

    def mover(self):
        self.x1 -= self.VELOCIDADE
        self.x2 -= self.VELOCIDADE

        #se chão 1 saiu da tela
        if self.x1 + self.LARGURA < 0: #lembrando que x1 é a posição do canto superior esquerdo do objeto chão 1
            self.x1 = self.x2 + self.LARGURA #reposiciona o chão 1 no final da tela

        # se chão 2 saiu da tela
        if self.x2 + self.LARGURA < 0:
            self.x2 = self.x1 + self.LARGURA

    def desenhar(self, tela):
        tela.blit(self.IMAGEM, (self.x1, self.y))
        tela.blit(self.IMAGEM, (self.x2, self.y))


def desenhar_tela(tela, passaros, canos, chao, pontos):
    tela.blit(IMAGEM_BACKGROUND, (0, 0))
    for passaro in passaros:
        passaro.desenhar(tela)
    for cano in canos:
        cano.desenhar(tela)

    texto = FONTE_PONTOS.render(f"Pontuação: {pontos}", 1, (255, 255, 255))
    tela.blit(texto, (TELA_LARGURA - 10 - texto.get_width(), 10))

    if ai_jogando:
        texto = FONTE_PONTOS.render(f"Geração: {geracao}", 1, (255, 255, 255))
        tela.blit(texto, (10, 10))

    chao.desenhar(tela)
    pygame.display.update()


def main(genomas, config): #fitness function ligado ao NEAT
    global geracao #importando a variável global, pois vamos modificar ela (por isso não a passamos como parâmetro)
    geracao += 1

    # criar vários pássaros
    redes = []
    lista_genomas = []  # genoma é responsável por ditar como as redes neurais irão se modificar
    passaros = []

    if ai_jogando:
        for _, genoma in genomas: # o "_" indica que após realizar o unpacking da tupla, eu não quero usar o primeiro item desta tupla para nada
            rede = neat.nn.FeedForwardNetwork.create(genoma, config)
            redes.append(rede)
            genoma.fitness = 0 #pontuação interna do genoma setado para 0
            lista_genomas.append(genoma)
            passaros.append(Passaro(230, 350))
    else:
        passaros = [Passaro(230, 350)]
    chao = Chao(730)
    canos = [Cano(700)]
    tela = pygame.display.set_mode((TELA_LARGURA, TELA_ALTURA))
    pontos = 0
    relogio = pygame.time.Clock()

    rodando = True
    while rodando: #loop do jogo
        relogio.tick(30) #define a taxa de atualização de quadros (fps)

        #interação com usuário
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: #se apertar no X da janela
                rodando = False
                pygame.quit() #encerra o jogo
                quit() #encerra o python em si
            if not ai_jogando:
                if evento.type == pygame.KEYDOWN: #se pressionar tecla
                    if evento.key == pygame.K_SPACE:
                        for passaro in passaros:
                            passaro.pular()

        indice_cano = 0
        if len(passaros) > 0:
            #se a posição x do primeiro pássaro for maior que a posição da img do cano mais a largura do cano
            if len(canos) > 1 and passaros[0].x > (canos[0].x + canos[0].IMG_CANO_TOPO.get_width()):
                indice_cano = 1 #altero o cano que deve ser olhado pela IA
        else:
            rodando = False
            break #termina o loop while do jogo

        #mover objetos
        #aqui a IA vai decidir se o pássaro deve pular ou não
        for i, passaro in enumerate(passaros):
            passaro.mover()
            if ai_jogando:
                #dar feedback positivo na fitness da IA (incentivo positivo) -> quanto mais a direita mais pontos
                lista_genomas[i].fitness += 0.1
                output = redes[i].activate((passaro.y,
                                            abs(passaro.y - canos[indice_cano].altura),
                                            abs(passaro.y - canos[indice_cano].pos_base),
                                            abs(canos[indice_cano].sentido)))
                #output retorna entre -1 e 1 -> se for maior que 0.5 -> pássaro pula
                if output[0] > 0.5:
                    passaro.pular()

        chao.mover()

        adicionar_cano = False
        remover_canos = []
        for cano in canos:
            for i, passaro in enumerate(passaros):
                if cano.colidir(passaro):
                    passaros.pop(i) #pássaro morreu
                    if ai_jogando:
                        lista_genomas[i].fitness -= 2 #penalização -> feedback negativo
                        #removendo aquela instância de rede
                        lista_genomas.pop(i)
                        redes.pop(i)
                # se cano.passou diz False, mas a posição do pássaro em x já ultrapassou o cano, então altero a variável cano.passou e adiciono um cano
                if not cano.passou and passaro.x > cano.x:
                    cano.passou = True
                    adicionar_cano = True
            cano.mover()
            cano.mover_vertical()
            cano.alterar_mov_vertical()
            if cano.x + cano.IMG_CANO_TOPO.get_width() < 0:
                remover_canos.append(cano) #usando uma lista auxiliar para remover cano sem que a remoção ocorra enquanto estou percorrendo a lista de canos

        if adicionar_cano:
            pontos += 1
            canos.append(Cano(600))

            # incentivo -> feedback positivo
            for genoma in lista_genomas:
                genoma.fitness += 5

        for cano in remover_canos:
            canos.remove(cano)

        for i, passaro in enumerate(passaros):
            # se a posição da caixa do pássaro + a altura dele mesmo for maior que a posição do chao -> morreu
            # ou se a posição y do pássaro for menor do que zero, ou seja, acima da tela -> morreu
            if (passaro.y + passaro.imagem.get_height()) > chao.y or passaro.y <0:
                passaros.pop(i)
                if ai_jogando:
                    lista_genomas.pop(i)
                    redes.pop(i)

        desenhar_tela(tela, passaros, canos, chao, pontos)


def rodar(caminho_config):
    config = neat.config.Config(neat.DefaultGenome,
                                neat.DefaultReproduction,
                                neat.DefaultSpeciesSet,
                                neat.DefaultStagnation,
                                caminho_config)
    populacao = neat.Population(config)

    #adicionando infos sobre a simulação
    populacao.add_reporter(neat.StdOutReporter(True))
    populacao.add_reporter(neat.StatisticsReporter())

    if ai_jogando:
        populacao.run(main, 50) #limitando a simulação até 50 gerações
    else:
        main(None, None) #caso seja o usuário jogando


#garante que a função main não irá imediatamente rodar se este código for importado por outro código
if __name__ == '__main__':
    caminho = os.path.dirname(__file__) #pegando o caminho da pasta FlappyBird que contém este arquivo .py
    caminho_config = os.path.join(caminho, 'config.txt')
    rodar(caminho_config)