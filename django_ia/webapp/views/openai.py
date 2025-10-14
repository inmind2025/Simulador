import os
import re
import urllib.parse
from io import BytesIO
import json # Para lidar com JSON em AJAX

import google.generativeai as genai

import graphviz
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from webapp.models import Registros, SimulacaoAtendimento, MensagemSimulacao, Sala, Personagem
from django.utils import timezone # Importe para usar timezone.now() na view de reiniciar
from django.contrib.auth.decorators import login_required
from django.urls import reverse 



# --- O resto do seu código (suas views) começa aqui ---

# Substitua pela sua chave de API do Gemini
GEMINI_API_KEY = "AIzaSyAmbKHgr9VbjZnwzT649exJVe_ztcVCvrg"
# GEMINI_API_KEY = "AIzaSyB6em4DeHZYuIydgpSD3kwq4rmWOjH7Psc"

@login_required
def dominante(request):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

    # Verifica se é o início de uma nova simulação (sem histórico na sessão) 
    if 'chat_display' not in request.session: 
        initial_prompt = '''
          PROMPT — Agente Cliente DISC-D (Ramsons) - Perfil Lucas Andrade
Você é um agente que simula Lucas Andrade, um cliente com perfil Dominante (DISC-D) e exigências de alto padrão, em uma loja física Ramsons (eletrodomésticos, eletrônicos, móveis e utilidades). Seu comportamento é direto, objetivo e orientado a métricas, como um Diretor de Operações de uma startup de logística. Seu tempo é extremamente valioso.
________________________________________
REGRAS DE PAPEL
	Seu papel é sempre o de CLIENTE.
	Comece mudo, exibindo apenas: ...
	Responda somente após o vendedor iniciar a conversa.
	Prefixe todas as falas com: Cliente:
	Fale em frases curtas, diretas e naturais. Use de 5 a 15 palavras na maioria das falas, mas permita frases um pouco mais longas para as justificativas rápidas.
	Nunca aja como vendedor nem dê conselhos técnicos.
	Não faça falas exageradas ou teatrais.
________________________________________
PERFIL DO CLIENTE - LUCAS ANDRADE
	Direto e prático: Sua comunicação é direta e voltada para resultados. Impaciente com enrolação, exige agilidade e informações concretas.
	Orientado a métricas: Prefere comparações lado a lado e números concretos, como consumo (kWh/mês), nível de ruído (dB) e prazos de entrega exatos.
	Baixa tolerância à frustração logística: Valoriza eficiência, previsibilidade e um serviço de pós-venda ágil. Quer evitar retrabalho.
	Conhecimento técnico: Possui conhecimento intermediário sobre os produtos, tendo lido reviews técnicos e análises. Sabe a diferença entre compressores inverter e convencionais, por exemplo.
	Motivadores emocionais: Sente urgência, desejo de controle e a necessidade de fazer uma compra 'à prova de problemas' com suporte premium para proteger seu tempo.
________________________________________
PRODUTO DE INTERESSE
	Em cada interação, escolha um produto diferente do anterior.
	O produto deve ser do interesse de Lucas Andrade. Sua necessidade principal é um refrigerador premium French Door com conectividade Wi-Fi, filtro de água e acabamento anti-digitais. Você precisa de um equipamento robusto, eficiente e integrado ao seu ecossistema de casa inteligente (Google Home/Alexa).
	Para interações futuras, alterne categorias. Nunca repita geladeira e micro-ondas em sequência.
	Categorias disponíveis (sem marcas/modelos):
	Cozinha: geladeira, fogão, micro-ondas, cooktop, coifa, forno elétrico, airfryer, cafeteira, sanduicheira, liquidificador, batedeira, panela elétrica, purificador de água, freezer, adega
	Lavanderia: máquina de lavar, lava e seca, ferro de passar
	Climatização: ar-condicionado, ventilador, climatizador
	Limpeza: aspirador, robô aspirador
	Som & Imagem: TV, soundbar, caixa de som, home theater
	Informática: notebook, desktop, monitor, impressora
	Mobile & Foto: celular, tablet, câmera
	Rede & Segurança: roteador, câmera de segurança, videoporteiro, lâmpada inteligente
	Móveis & Colchões: sofá, rack, guarda-roupa, cômoda, mesa/cadeira, colchão
________________________________________
LIMITAÇÕES + O QUE NÃO FAZER
	Não cite marcas/modelos específicos, mas pode usar termos técnicos genéricos para demonstrar conhecimento.
	Não oferecer ajuda ao vendedor.
	Não pedir serviços fora do escopo de loja física.
	Não peça documentos ou detalhes técnicos ao vendedor, como ficha técnica, contrato de seguro ou garantia.
	Não deixar de passar os dados pessoais quando solicitado para cadastro.
	Ao ser oferecido um produto que não atende às suas expectativas, responda de forma direta, sem rodeios, como "Não, obrigado, não é isso que procuro" ou "Não me interessa, tem outro?".
________________________________________
COMPORTAMENTO DAS FALAS
	Varie vocabulário, comprimento e intenção a cada interação.
	Soe como pessoa real: hesitações curtas, comparações simples, sem jargão.
	Exemplos de tom (não repetir literalmente):
	“quero algo que dure bastante”, “tem mais barato?”, “esse tá bonito”,
	“tô na pressa”, “preciso que entreguem logo”, “me mostra outra opção rápido”,
	“gostei, mas tô na dúvida”, “achei meio caro”, “esse parece frágil”.
________________________________________
OBJEÇÕES
	Conceito: objeção é uma barreira/dúvida que impede o avanço na compra.
	Como usar:
	Levante no máximo 1 objeção por vez; varie entre interações.
	Só repita uma objeção se o vendedor não resolver.
	Não invente tecnicidades. Mantenha frases curtas.
	Use os exemplos de objeção de forma alternada e combine-os. Evite repetições literais das frases, buscando variações que mantenham o mesmo sentido.
	Tipos e exemplos (use de forma alternada):
	Preço — “Tá muito caro pra mim.” / “Vi mais barato em outra loja.”
	Falta de dinheiro — “Esse mês não dá.” / “Vou esperar receber.”
	Concorrência — “Na loja X o preço tá melhor.” / “Lá deram brinde.”
	Sem necessidade imediata — “O meu ainda funciona.” / “Não é urgente.”
	Sem urgência — “Vou pensar e volto.” / “Tô pesquisando.”
	Desconfiança da marca — “Não conheço essa marca.” / “E a assistência?”
	Dúvida de qualidade — “Parece frágil.” / “Esse material é bom?”
	Desconfiança na loja/vendedor — “Já comprei aqui e deu ruim.” / “Quero outro vendedor.”
	Medo de arrependimento — “E se eu me arrepender?” / “Tenho receio depois.”
	Resistência a mudanças — “Uso o antigo.” / “Tô acostumado.”
	Falta de tempo — “Tô com pressa.” / “Só uma olhada rápida.”
	Sem autonomia — “Vou falar com minha esposa.” / “Consulto meu marido.”
	Esperar promoção — “Vou esperar a Black Friday.” / “Mês que vem deve baixar.”
	Entrega — “Demora pra chegar?” / “Entregam no meu bairro?”
	Pagamento — “Não quero parcelar.” / “Cartão tá cheio.”
	Experiência ruim anterior — “Já deu defeito.” / “Atendimento foi ruim.”
	Falta de conhecimento — “Não entendo disso.” / “Posso escolher errado.”
	Assistência/garantia — “Como resolve defeito?” / “Tem assistência na cidade?”
	Valor percebido — “Não vejo diferença.” / “Não vale tudo isso.”
	Desinteresse momentâneo — “Só olhando.” / “Acompanhando um amigo.”
________________________________________
FECHAMENTO
	Se decidir comprar, varie a frase de fechamento:
	“Fechou, pode fazer aí.” / “Vou levar esse.” / “Pode concluir pra mim.”
	Não repita literalmente entre atendimentos.
________________________________________
DADOS PESSOAIS (LUCAS ANDRADE) (forneça apenas quando o vendedor pedir)
	Cadastro novo:
	Nome: Lucas Andrade
	Idade: 41
	Profissão/Cargo: Diretor de Operações (COO) em startup de logística
	Localização: Manaus - AM
	Faixa de renda: Classe A (~R$ 32.000 mensais)
	Endividamento: Baixo. Cartões sempre quitados.
	Outros dados: Telefone, e-mail, CPF, RG, data de nascimento, estado civil, forma de pagamento.
	Atualização: confirme ou corrija apenas o que for solicitado.
________________________________________
OBJETIVO
	Simular atendimento real de loja física com cliente exigente e objetivo.
________________________________________
FORMATAÇÃO INICIAL
Ao iniciar, exiba apenas: ... e aguarde o vendedor
        '''
        
        try:
            sala_id = request.session.get('current_sala_id')
            sala = Sala.objects.get(id=sala_id) if sala_id else None

            personagem_id = request.session.get('current_personagem_id')
            if not personagem_id:
                messages.error(request, "Erro: Personagem não selecionado. Inicie o atendimento novamente.")
                return redirect('bem_vindo')
            personagem = get_object_or_404(Personagem, id=personagem_id)

            simulacao = SimulacaoAtendimento.objects.create(
                user=request.user,
                initial_prompt_summary=f"Conversa com {personagem.nome_criativo}",
                sala=sala
            )
            # 2. Armazene o ID da simulação na sessão para associar as futuras mensagens
            request.session['current_simulacao_id'] = simulacao.id

            # O histórico 'interno' do Gemini começa com o prompt de sistema. 
            gemini_internal_history = [{'role': 'user', 'parts': [initial_prompt]}]
            chat = model.start_chat(history=gemini_internal_history)
            
            # Gerar a primeira fala do cliente (Gemini) baseada no prompt. 
            response = chat.send_message("Estou pronto para simular.") 
            
            customer_first_dialogue = response.text.strip()
            
            # 3. Salve a primeira fala do cliente (Gemini/IA) no banco de dados
            MensagemSimulacao.objects.create(
                simulacao=simulacao,
                sender='cliente_ia',
                message_content=customer_first_dialogue
            )
            
            # Atualiza o histórico interno do Gemini com a primeira resposta do modelo. 
            gemini_internal_history.append({'role': 'model', 'parts': [customer_first_dialogue]})
            
            # O histórico para exibição na UI começa apenas com a primeira fala do CLIENTE.
            request.session['chat_display'] = [
                {'role': 'model', 'parts': [customer_first_dialogue]}
            ]
            # Salva o histórico INTERNO do Gemini na sessão.
            request.session['gemini_chat_internal_history'] = gemini_internal_history
            request.session.modified = True # Marca a sessão como modificada

        except Exception as e:
            messages.error(request, f"Ocorreu um erro ao iniciar a simulação: {e}. Certifique-se de que está logado.")
            request.session['chat_display'] = []
            request.session['gemini_chat_internal_history'] = []
            # Limpa o ID da simulação da sessão se deu erro na criação
            if 'current_simulacao_id' in request.session:
                del request.session['current_simulacao_id']

    personagem_id = request.session.get('current_personagem_id')
    personagem = get_object_or_404(Personagem, id=personagem_id) if personagem_id else None

    context = {
        'views': {'id': 'simulacao', 'titulo': f'Simulação de Atendimento - {personagem.nome_criativo if personagem else "Perfil Dominante"}'},
        'chat_display': request.session.get('chat_display', []),
        'personagem': personagem
    }
    return render(request, 'dominante.html', context)

def correcao(request):
    params = {
        "views": {
            "id": "correcao",
            "titulo": "Correção de Código com Gemini",
        },
        "linguagens": [
            "C", "C#", "C++", "Clike", "CSV", "CSS", "Django", "Go",
            "Graphql", "HTML", "Java", "JavaScript", "Markup",
            "Markup-templating", "Perl", "PHP", "Python", "Ruby",
            "Rust", "SQL", "XML-Doc", "Yaml",
        ]
    }
    
    # Esta parte é para a exibição inicial do formulário ou para carregar o código da sessão após um redirecionamento
    if "code" in request.session:
        params["code"] = request.session.pop("code")

    if request.method == "POST":
        code_to_fix = request.POST["code"]
        linguagem = request.POST["linguagem"]
        
        request.session["code"] = code_to_fix # Salva na sessão para caso de redirecionamento ou para reexibir o código
        params["code"] = code_to_fix # <-- ADICIONE ESTA LINHA AQUI!
                                     # Isso garante que 'params["code"]' tenha o valor correto para este request.
        
        if linguagem == "Selecione a linguagem de programação":
            messages.error(request, "Por favor, selecione uma linguagem")
            return render(request, "correcao.html", params)
        
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            
            raw_response = response.text.strip()
            
            if raw_response.startswith("```") and raw_response.endswith("```"):
                lines = raw_response.splitlines()
                corrected_code = "\n".join(lines[1:-1])
            else:
                corrected_code = raw_response
            
            params["response"] = corrected_code

            # Parte do Banco de Dados
            # Salva o registro de histórico
            
            registro = Registros(
                pergunta = params["code"], # Agora 'params["code"]' estará definido
                resposta = params["response"],
                linguagem = linguagem, # Pode usar `linguagem` diretamente, já que já foi validado
                user = request.user,
                tipo=params["views"]["id"],
            )
            registro.save()
            messages.success(request, "Código corrigido e salvo com sucesso!") # Adicionar mensagem de sucesso
            
        except Exception as e:
            # A mensagem de erro que você viu. `e` provavelmente era um KeyError('code')
            messages.error(request, f"Ocorreu um erro ao contatar a API do Gemini ou ao processar: {e}")
            
    return render(request, "correcao.html", params)


def criacao(request):
    params = {
        "views": {
            "id": "criacao",
            "titulo": "Criação de Código com Gemini",
        },
        "linguagens": [
            "C", "C#", "C++", "Clike", "CSV", "CSS", "Django", "Go",
            "Graphql", "HTML", "Java", "JavaScript", "Markup",
            "Markup-templating", "Perl", "PHP", "Python", "Ruby",
            "Rust", "SQL", "XML-Doc", "Yaml",
        ]
    }
    
    if "code" in request.session:
        params["code"] = request.session.pop("code")

    if request.method == "POST":
        code_to_fix = request.POST["code"]
        linguagem = request.POST["linguagem"]
        
        request.session["code"] = code_to_fix
        # --- ADICIONE ESTA LINHA AQUI! ---
        params["code"] = code_to_fix 
        # --- FIM DA ADIÇÃO ---
        
        try:
            # Configura a chave de API do Gemini
            genai.configure(api_key=GEMINI_API_KEY)

            # Inicializa o modelo (gemini-1.5-flash é rápido e eficiente)
            model = genai.GenerativeModel('gemini-2.5-flash')

            # Cria o prompt para o Gemini
            prompt = f"Responda apenas com código. {code_to_fix} na linguagem: {linguagem}"

            # Gera o conteúdo
            response = model.generate_content(prompt)
            
            # Pega a resposta de texto crua e remove espaços em branco no início/fim
            raw_response = response.text.strip()
            
            # Verifica se a resposta está formatada como um bloco de código Markdown
            if raw_response.startswith("```") and raw_response.endswith("```"):
                # Remove a primeira linha (ex: ```python) e a última (```)
                lines = raw_response.splitlines()
                # `corrected_code` foi o nome usado na outra view, aqui é o código gerado/criado
                generated_code = "\n".join(lines[1:-1]) 
            else:
                generated_code = raw_response
            
            # Adiciona o código já limpo ao dicionário de parâmetros
            params["response"] = generated_code

            # Parte do Banco de Dados: Salva o registro de histórico
            registro = Registros(
                pergunta = params["code"], # Agora 'params["code"]' estará definido
                resposta = params["response"],
                linguagem = linguagem, # Pode usar `linguagem` diretamente
                user = request.user,
                tipo=params["views"]["id"], # Isso será "criacao" conforme definido em `params["views"]["id"]`
            )
            registro.save()
            messages.success(request, "Código criado e salvo com sucesso!") # Mensagem de sucesso ajustada para "criação"

        except Exception as e:
            messages.error(request, f"Ocorreu um erro ao contatar a API do Gemini: {e}")
            
    return render(request, "criacao.html", params)



def geral(request):
    params = {
        "views": {
            "id": "geral",
            "titulo": "Perguntas Gerais",
        },
    }
    
    if "code" in request.session:
        params["code"] = request.session.pop("code")

    if request.method == "POST":
        code_to_fix = request.POST["code"]
        
        request.session["code"] = code_to_fix
        # --- ADICIONE ESTA LINHA AQUI! ---
        params["code"] = code_to_fix 
        # --- FIM DA ADIÇÃO ---
        
        try:
            # Configura a chave de API do Gemini
            genai.configure(api_key=GEMINI_API_KEY)

            # Inicializa o modelo (gemini-1.5-flash é rápido e eficiente)
            model = genai.GenerativeModel('gemini-2.5-flash')

            # Cria o prompt para o Gemini
            prompt = f"Responda a: {code_to_fix}"

            # Gera o conteúdo
            response = model.generate_content(prompt)
            
            # Pega a resposta de texto crua e remove espaços em branco no início/fim
            raw_response = response.text.strip()
            
            # Verifica se a resposta está formatada como um bloco de código Markdown
            if raw_response.startswith("```") and raw_response.endswith("```"):
                # Remove a primeira linha (ex: ```python) e a última (```)
                lines = raw_response.splitlines()
                generated_response = "\n".join(lines[1:-1]) 
            else:
                generated_response = raw_response
            
            # Adiciona o conteúdo gerado ao dicionário de parâmetros
            params["response"] = generated_response

            # Parte do Banco de Dados: Salva o registro de histórico
            registro = Registros(
                pergunta = params["code"], # Agora 'params["code"]' estará definido
                resposta = params["response"],
                linguagem = "geral", # Fixo como "geral" para esta view, o que está correto
                user = request.user,
                tipo=params["views"]["id"], # Será "geral"
            )
            registro.save()
            # --- ATUALIZE A MENSAGEM DE SUCESSO AQUI! ---
            messages.success(request, "Pergunta respondida e salva com sucesso!") 
            # --- FIM DA ATUALIZAÇÃO ---

        except Exception as e:
            messages.error(request, f"Ocorreu um erro ao contatar a API do Gemini: {e}")
            
    return render(request, "geral.html", params)



# Em seu arquivo views.py

# Em seu arquivo views.py

# Em seu arquivo views.py

def mapa_mental(request):
    # Valores padrão para a primeira vez que a página carrega
    context = {
        "views": {"id": "mapaMental", "titulo": "Gerador de Mapa Mental"},
        "texto_original": "", "mapa_svg": None,
        "layout_choice": "LR", "detalhe_choice": "normal",
    }

    if request.method == "POST":
        # 1. O "chef" anota o pedido completo do cliente
        texto_usuario = request.POST.get("texto_mapa", "") 
        layout_choice = request.POST.get('layout', 'LR')
        detalhe_choice = request.POST.get('detalhe', 'normal')

        # Atualiza o contexto para "lembrar" das escolhas
        context["texto_original"] = texto_usuario
        context["layout_choice"] = layout_choice
        context["detalhe_choice"] = detalhe_choice

        if not texto_usuario.strip():
            messages.error(request, "Por favor, insira um texto.")
            return render(request, "mapa_mental.html", context)

        try:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-2.5-flash')

            # 2. O "chef" prepara as instruções especiais para o Gemini
            
            # Instrução para o Layout
            instrucao_layout = 'O layout do mapa deve ser da esquerda para a direita. Para isso, inclua \'rankdir="LR";\'.'
            engine_to_use = 'dot'
            if layout_choice == 'TB':
                instrucao_layout = 'O layout do mapa deve ser de cima para baixo. Para isso, inclua \'rankdir="TB";\'.'
            elif layout_choice == 'radial':
                engine_to_use = 'twopi'
                instrucao_layout = 'O layout do mapa deve ser radial (formato de teia).'

            # Instrução para o Nível de Detalhe
            instrucao_detalhe = '' # Padrão (Normal)
            if detalhe_choice == 'resumido':
                instrucao_detalhe = 'Seja conciso e foque apenas nos conceitos principais, com poucos níveis.'
            elif detalhe_choice == 'detalhado':
                instrucao_detalhe = 'Seja exaustivo e crie múltiplos níveis de subtópicos. Explore as conexões em profundidade.'

            # 3. O "chef" envia o pedido completo para o Gemini
            prompt = f'''
Sua tarefa é converter o texto em um mapa mental na sintaxe DOT da Graphviz.
{instrucao_layout}
{instrucao_detalhe}
Use nós em formato de caixa. Responda apenas com o código DOT.

TEXTO PARA CONVERTER:
{texto_usuario}
'''
            
            response = model.generate_content(prompt, safety_settings={'HATE': 'BLOCK_NONE', 'HARASSMENT': 'BLOCK_NONE'})
            dot_source = response.text

            # ... (o resto do código para gerar o SVG continua igual) ...
            if dot_source.strip().startswith("```"):
                lines = dot_source.strip().splitlines()
                dot_source = "\n".join(lines[1:-1])

            g = graphviz.Source(dot_source, engine=engine_to_use, format="svg")
            svg_content = g.pipe().decode('utf-8')

            context['mapa_svg'] = svg_content
            request.session['mapa_svg_para_download'] = svg_content

        except Exception as e:
            messages.error(request, f"Ocorreu um erro ao gerar o mapa: {e}")
            
    return render(request, "mapa_mental.html", context)


# ADICIONE ESTA NOVA FUNÇÃO AO SEU views.py
def download_mapa_pdf(request):
    # Pega o SVG que salvamos na sessão
    svg_content = request.session.get('mapa_svg_para_download')

    if not svg_content:
        messages.error(request, "Nenhum mapa mental encontrado para download.")
        return redirect('mapa_mental')

    try:
        # Converte a string SVG em um objeto que o ReportLab entende
        # Usamos BytesIO para tratar a string como um arquivo em memória
        drawing = svg2rlg(BytesIO(svg_content.encode('utf-8')))
        
        # Cria um buffer para guardar o PDF em memória
        pdf_buffer = BytesIO()

        # Renderiza o desenho no buffer de PDF
        renderPDF.drawToFile(drawing, pdf_buffer)
        
        # Pega os dados do PDF a partir do buffer
        pdf_file = pdf_buffer.getvalue()
        pdf_buffer.close()

        # Cria a resposta HTTP para forçar o download do arquivo
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="mapa_mental.pdf"'
        
        return response

    except Exception as e:
        messages.error(request, f"Ocorreu um erro ao converter o mapa para PDF: {e}")
        return redirect('mapa_mental')
    




# A view `enviar_resposta_vendedor` será ajustada na próxima etapa, caso você precise.
# A view `reiniciar_simulacao` também pode ser ajustada para finalizar a simulação no banco.

@require_POST
def enviar_resposta_vendedor(request):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

    # Recupera o histórico para exibição na UI e o histórico INTERNO do Gemini
    chat_display = request.session.get('chat_display', [])
    gemini_chat_internal_history = request.session.get('gemini_chat_internal_history', [])
    
    # 1. Recupera o ID da simulação atual da sessão
    current_simulacao_id = request.session.get('current_simulacao_id')

    # Validações iniciais
    if not current_simulacao_id:
        # Se não há ID de simulação, algo deu errado ou a sessão expirou/foi reiniciada incorretamente
        return JsonResponse({'error': 'Simulação não encontrada. Por favor, reinicie a simulação.'}, status=400)
    
    try:
        # 2. Carrega a instância de SimulacaoAtendimento do banco de dados
        simulacao_atual = SimulacaoAtendimento.objects.get(id=current_simulacao_id)
    except SimulacaoAtendimento.DoesNotExist:
        # Se o ID existe na sessão mas a simulação não existe no DB, é um erro grave
        return JsonResponse({'error': 'Simulação inválida. Por favor, reinicie a simulação.'}, status=400)

    # Valida a entrada do vendedor (mensagem do usuário)
    data = json.loads(request.body)
    vendedor_message = data.get('message', '').strip()

    if not vendedor_message:
        return JsonResponse({'error': 'Mensagem do vendedor não pode estar vazia.'}, status=400)

    try:
        # 3. Salva a mensagem do vendedor (Usuário) no banco de dados
        MensagemSimulacao.objects.create(
            simulacao=simulacao_atual,
            sender='vendedor_usuario',
            message_content=vendedor_message
        )

        # Adiciona a mensagem do vendedor ao histórico INTERNO do Gemini
        gemini_chat_internal_history.append({'role': 'user', 'parts': [vendedor_message]})
        
        # Reinicia o objeto de chat do Gemini com o histórico interno completo
        chat = model.start_chat(history=gemini_chat_internal_history)
        
        # Envia a mensagem do vendedor e obtém a resposta do cliente (Gemini)
        response = chat.send_message(vendedor_message)
        customer_response_text = response.text.strip()
        
        # 4. Salva a resposta do Cliente (IA) no banco de dados
        MensagemSimulacao.objects.create(
            simulacao=simulacao_atual,
            sender='cliente_ia',
            message_content=customer_response_text
        )
        
        # Adiciona a mensagem do vendedor ao histórico para EXIBIÇÃO na UI
        chat_display.append({'role': 'user', 'parts': [vendedor_message]})
        
        # Adiciona a resposta do cliente (Gemini) ao histórico INTERNO do Gemini
        gemini_chat_internal_history.append({'role': 'model', 'parts': [customer_response_text]})
        
        # Adiciona a resposta do cliente (Gemini) ao histórico para EXIBIÇÃO na UI
        chat_display.append({'role': 'model', 'parts': [customer_response_text]})
        
        # Salva AMBOS os históricos atualizados na sessão
        request.session['chat_display'] = chat_display
        request.session['gemini_chat_internal_history'] = gemini_chat_internal_history
        request.session.modified = True 

        # Retorna a resposta do cliente em JSON e o histórico completo para a UI atualizar
        return JsonResponse({
            'customer_response': customer_response_text,
            'chat_history': chat_display 
        })

    except Exception as e:
        # Se houver um erro, ainda tenta retornar uma resposta JSON adequada
        return JsonResponse({'error': f"Ocorreu um erro na interação com o Gemini: {e}"}, status=500)

# -----------------------------------------------------------------------------------
# Opcional: Ajuste na view reiniciar_simulacao para marcar o fim da simulação no DB
# -----------------------------------------------------------------------------------


def reiniciar_simulacao(request):
    # Antes de limpar a sessão, tentamos marcar a hora de término da simulação no DB
    if 'current_simulacao_id' in request.session:
        try:
            simulacao = SimulacaoAtendimento.objects.get(id=request.session['current_simulacao_id'])
            if not simulacao.end_time: # Só atualiza se ainda não tiver sido definida
                simulacao.end_time = timezone.now() 
                simulacao.save()
        except SimulacaoAtendimento.DoesNotExist:
            pass # A simulação pode já ter sido excluída ou nunca existiu
        # Sempre remove o ID da sessão, mesmo que não consiga atualizar o DB
        del request.session['current_simulacao_id'] 

    # Limpa os históricos da sessão para iniciar uma nova simulação
    if 'chat_display' in request.session:
        del request.session['chat_display']
    if 'gemini_chat_internal_history' in request.session:
        del request.session['gemini_chat_internal_history']
    
    # Se 'gemini_chat_id' não é mais usado, pode ser removido
    if 'gemini_chat_id' in request.session:
        del request.session['gemini_chat_id']
    
    messages.info(request, "Simulação finalizada com sucesso!") # Mensagem para o usuário

    return redirect('bem_vindo')

def historico(request):
    # Verifica se o usuário tem um perfil e qual é a sua função
    if hasattr(request.user, 'profile') and request.user.profile.role == 'administrador':
        # O administrador vê todas as simulações
        simulacoes = SimulacaoAtendimento.objects.all().prefetch_related('mensagens').order_by('-start_time')
    else:
        # O cliente vê apenas as suas próprias simulações
        simulacoes = SimulacaoAtendimento.objects.filter(user=request.user).prefetch_related('mensagens').order_by('-start_time')
    
    context = {
        'simulacoes': simulacoes,
        'views': {'id': 'historico_simulacoes', 'titulo': 'Histórico de Simulações de Atendimento'}
    }
    return render(request, 'historico_simulacoes.html', context)


def historico_simulacoes(request):
    # Verifica se o usuário tem um perfil e qual é a sua função
    if hasattr(request.user, 'profile') and request.user.profile.role == 'administrador':
        # O administrador vê todas as simulações
        simulacoes = SimulacaoAtendimento.objects.all().prefetch_related('mensagens').order_by('-start_time')
    else:
        # O cliente vê apenas as suas próprias simulações
        simulacoes = SimulacaoAtendimento.objects.filter(user=request.user).prefetch_related('mensagens').order_by('-start_time')
    
    context = {
        'simulacoes': simulacoes,
        'views': {'id': 'historico_simulacoes', 'titulo': 'Histórico de Simulações de Atendimento'}
    }
    return render(request, 'historico_simulacoes.html', context)

def conversation_detail(request, simulacao_id):
    simulacao = get_object_or_404(SimulacaoAtendimento.objects.prefetch_related('mensagens'), id=simulacao_id)
    
    # Security check: ensure non-admins can only see their own history
    if not request.user.profile.role == 'administrador' and not simulacao.user == request.user:
        messages.error(request, "Você não tem permissão para ver esta conversa.")
        return redirect('historico_simulacoes')

    # Pega a URL da página anterior ou define uma padrão
    back_url = request.META.get('HTTP_REFERER', reverse('historico_simulacoes'))

    context = {
        'simulacao': simulacao,
        'views': {'id': 'conversation_detail', 'titulo': 'Detalhes da Simulação'},
        'back_url': back_url
    }
    return render(request, 'conversation_detail.html', context)


@login_required
def bem_vindo(request):
    context = {
        'views': {'id': 'bem_vindo', 'titulo': 'Seja Bem-Vindo(a) à Plataforma de Treinamento'}
    }
    return render(request, 'bem_vindo.html', context)

@login_required
def influente(request):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

    if 'chat_display' not in request.session: 
        initial_prompt = '''
     PROMPT — Agente Cliente DISC-I (Ramsons) - Perfil Mariana Lobo
Você é um agente que simula Mariana Lobo, uma cliente com perfil Influente (DISC-I), em uma loja física Ramsons (eletrodomésticos, eletrônicos, móveis e utilidades).
________________________________________
REGRAS DE PAPEL
	Seu papel é SEMPRE o de CLIENTE.
	Comece mudo, exibindo apenas: ...
	Responda somente após o vendedor iniciar a conversa.
	Prefixe todas as falas com: Cliente:
	Fale em frases curtas, leves e naturais (5 a 15 palavras).
	Nunca aja como vendedor nem dê conselhos técnicos.
	Não faça falas exageradas ou teatrais.
________________________________________
PERFIL DO CLIENTE - MARIANA LOBO
	Geral: Comunicativa, simpática e extrovertida. Sua comunicação é leve, envolvente e descontraída, mas SEM exageros caricatos.
	Foco de compra: Valoriza design, estilo, novidade e a experiência de compra. A compra deve atender à sua necessidade de transformar o estúdio para aulas híbridas, lives e eventos, com uma imagem impactante e áudio imersivo.
	Comportamento: Dá importância à simpatia do vendedor e ao clima da conversa. Pode se distrair em comentários rápidos sobre a estética ou a vida social, mas retorna ao foco quando direcionada.
	Decisão de compra: Rejeita pressão agressiva. Prefere sentir autonomia e co-criação na escolha. A decisão é emocional, baseada em validação social (opinião de amigos/seguidores) e prova social (reviews 5 estrelas e cases de sucesso).
________________________________________
O QUE NÃO FAZER
	Não conduzir a conversa ou oferecer produtos.
	Não mencionar marcas, modelos ou termos técnicos (exceto para demonstrar conhecimento, se aplicável, de forma natural).
	Não usar emojis.
	Não falar de forma artificial ou exagerada. A simulação deve ser de vida real, com entusiasmo natural e plausível.
	Não pedir ficha técnica do produto.
	Não pedir contrato de seguro ou garantia.
	Não pedir qualquer documento ao vendedor.
	Não deixar de passar os dados pessoais para cadastro.
________________________________________
PRODUTO DE INTERESSE
	Sua necessidade principal é uma Smart TV 75" 4K com pico de brilho alto para ambientes claros, sistema fluido e soundbar com subwoofer. O objetivo é ter um equipamento que combine com a decoração minimalista do estúdio de pilates e que facilite a produção de conteúdo.
	Em cada interação, escolha um produto DIFERENTE do anterior.
	Quando houver vários clientes logados simultaneamente, cada um deve estar interessado em um produto diferente.
	Alterne categorias (cozinha, lavanderia, climatização, limpeza, som & imagem, informática, mobile & foto, rede & segurança, móveis & colchões).
	Nunca repita geladeira e micro-ondas em sequência.
	Categorias disponíveis (sem citar marcas/modelos):
	Cozinha: geladeira, fogão, micro-ondas, cooktop, coifa, forno elétrico, airfryer, cafeteira, sanduicheira, liquidificador, batedeira, panela elétrica, purificador de água, freezer, adega
	Lavanderia: máquina de lavar, lava e seca, ferro de passar
	Climatização: ar-condicionado, ventilador, climatizador
	Limpeza: aspirador, robô aspirador
	Som & Imagem: TV, soundbar, caixa de som, home theater
	Informática: notebook, desktop, monitor, impressora
	Mobile & Foto: celular, tablet, câmera
	Rede & Segurança: roteador, câmera de segurança, videoporteiro, lâmpada inteligente
	Móveis & Colchões: sofá, rack, guarda-roupa, cômoda, mesa/cadeira, colchão
________________________________________
COMPORTAMENTO DAS FALAS
	Demonstre interesse e simpatia de forma realista. Use frases variadas, nunca repetidas literalmente.
	Exemplos de estilo (use como referência, não copie literalmente):
	FALAS DE INTERESSE: "Gostei do visual desse aqui." / "Será que combina com a minha sala?" / "Achei bonita a cor." / "Vi algo parecido na casa de um amigo."
	FALAS DE DÚVIDA / CURIOSIDADE: "Tem em outras cores?" / "Esse é novidade?" / "É fácil de usar?" / "Será que dá pra levar hoje?"
	FALAS DE COTIDIANO / CONTEXTO: "Quero algo que deixe a sala mais aconchegante." / "Tô precisando de um celular novo." / "Quero uma cafeteira prática pro dia a dia."
________________________________________
OBJEÇÕES
	Conceito: objeção é uma barreira/dúvida que impede o avanço na compra.
	Como usar:
	Levante no máximo 1 objeção por vez; varie entre interações.
	Só repita uma objeção se o vendedor não resolver.
	Mantenha frases curtas.
	Tipos e exemplos (use de forma alternada):
	Preço — “Tá muito caro pra mim.” / “Vi esse mesmo modelo mais barato em outra loja.”
	Falta de dinheiro — “Esse mês não dá, tô cheio de contas.” / “Vou esperar receber pra ver se consigo comprar.”
	Comparação com concorrência — “Na loja X o preço tá melhor.” / “O concorrente entrega mais rápido.”
	Falta de necessidade imediata — “Meu produto antigo ainda funciona, posso esperar.”
	Falta de urgência — “Vou pensar e volto outro dia.” / “Tô só pesquisando por enquanto.”
	Desconfiança na marca — “Nunca ouvi falar nessa marca.” / “Será que essa marca tem boa assistência?”
	Dúvida sobre qualidade — “Parece meio frágil, será que aguenta o uso?”
	Falta de confiança no vendedor ou na loja — “Já comprei aqui e não deu certo.”
	Medo de arrependimento — “E se eu comprar e me arrepender depois?”
	Resistência a mudanças — “Sempre usei o modelo antigo, não quero trocar.”
	Falta de tempo — “Tô com pressa agora, depois eu volto.”
	Falta de autonomia para decidir — “Preciso falar com meu marido/minha esposa antes.”
	Expectativa de promoção futura — “Vou esperar a Black Friday.”
	Questões de entrega — “Demora muito pra chegar?” / “Vocês entregam no meu bairro?”	Condições de pagamento — “Não quero parcelar, só compro à vista.”
	Experiência ruim anterior — “Comprei esse produto antes e deu defeito.” / “Na última compra aqui, o atendimento não foi bom.”
	Falta de conhecimento técnico — “Não entendo muito sobre isso.”
	Dúvida sobre assistência e garantia — “E se der problema, como faço pra resolver?”
	Dificuldade em perceber valor — “Não vejo diferença pra um modelo mais barato.”
	Desinteresse momentâneo — “Tô só olhando, não vou comprar hoje.”
________________________________________
FECHAMENTO
	Se decidir comprar, varie a frase de fechamento:
	"Gostei, vou levar esse." / "Fechou, pode fazer pra mim." / "Pode anotar meus dados e concluir."
	Se não fechar, use frases de saída variadas:
	"Vou pensar mais um pouco." / "Quero mostrar pra minha família e volto depois." / "Hoje não vou levar, mas gostei de conhecer."
________________________________________
DADOS PESSOAIS (MARIANA LOBO) (forneça apenas quando o vendedor pedir)
	Cadastro novo:
	Nome: Mariana Lobo
	Idade: 29
	Profissão: Empreendedora (Studio de Pilates) e Criadora de Conteúdo
	Localização: Manaus - AM
	Renda: Classe A (~R$ 22.000 mensais)
	Endividamento: Moderado e saudável.
	Outros dados: Telefone, e-mail, CPF, RG, data de nascimento, estado civil, forma de pagamento.
	Atualização: confirme ou corrija apenas o que o vendedor solicitar.
________________________________________
OBJETIVO
	Simular atendimento real de loja física com cliente influente: empático, comunicativo, positivo e leve.
	Treinar vendedores para lidar com clientes que valorizam conexão e experiência, sem excesso de tecnicismo.
________________________________________
FORMATAÇÃO INICIAL
	Ao iniciar, exiba apenas: ... e aguarde o vendedor.


        '''
        
        try:
            sala_id = request.session.get('current_sala_id')
            sala = Sala.objects.get(id=sala_id) if sala_id else None

            personagem_id = request.session.get('current_personagem_id')
            if not personagem_id:
                messages.error(request, "Erro: Personagem não selecionado. Inicie o atendimento novamente.")
                return redirect('bem_vindo')
            personagem = get_object_or_404(Personagem, id=personagem_id)

            simulacao = SimulacaoAtendimento.objects.create(
                user=request.user,
                initial_prompt_summary=f"Conversa com {personagem.nome_criativo}",
                sala=sala
            )
            request.session['current_simulacao_id'] = simulacao.id

            gemini_internal_history = [{'role': 'user', 'parts': [initial_prompt]}]
            chat = model.start_chat(history=gemini_internal_history)
            
            response = chat.send_message("Estou pronto para simular.") 
            
            customer_first_dialogue = response.text.strip()
            
            MensagemSimulacao.objects.create(
                simulacao=simulacao,
                sender='cliente_ia',
                message_content=customer_first_dialogue
            )
            
            gemini_internal_history.append({'role': 'model', 'parts': [customer_first_dialogue]})
            
            request.session['chat_display'] = [
                {'role': 'model', 'parts': [customer_first_dialogue]}
            ]
            request.session['gemini_chat_internal_history'] = gemini_internal_history
            request.session.modified = True

        except Exception as e:
            messages.error(request, f"Ocorreu um erro ao iniciar a simulação: {e}.")
            request.session['chat_display'] = []
            request.session['gemini_chat_internal_history'] = []
            if 'current_simulacao_id' in request.session:
                del request.session['current_simulacao_id']

    personagem_id = request.session.get('current_personagem_id')
    personagem = get_object_or_404(Personagem, id=personagem_id) if personagem_id else None

    context = {
        'views': {'id': 'simulacao', 'titulo': f'Simulação de Atendimento - {personagem.nome_criativo if personagem else "Perfil Influente"}'},
        'chat_display': request.session.get('chat_display', []),
        'personagem': personagem
    }
    return render(request, 'influente.html', context)

@login_required
def analitico(request):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

    if 'chat_display' not in request.session: 
        initial_prompt = '''
       PROMPT — Agente Cliente DISC-C (Ramsons) - Perfil Eliane Souza
Você é um agente que simula Eliane Souza, uma cliente com perfil Cautelosa e Analítica (DISC-C), em uma loja física Ramsons (eletrodomésticos, eletrônicos, móveis e utilidades).
________________________________________
REGRAS DE PAPEL
	Seu papel é SEMPRE o de CLIENTE.
	Comece mudo, exibindo apenas: ...
	Responda somente após o vendedor iniciar a conversa.
	Prefixe todas as falas com: Cliente:
	Fale em frases curtas, leves e naturais (5 a 15 palavras).
	Nunca aja como vendedor, atendente, consultor ou técnico.
	Não faça falas exageradas ou teatrais.
________________________________________
PERFIL DO CLIENTE - ELIANE SOUZA
	Geral: Lógica, detalhista e cautelosa. Sua comunicação é objetiva e respeitosa, evitando jargões. Ela é uma mãe solo com orçamento limitado e valoriza a transparência e o respeito.
	Foco de compra: A compra é uma necessidade prática e de longo prazo. Ela busca um produto confiável, durável e que caiba no orçamento, com foco em custo-benefício e condições claras de pagamento.
	Comportamento: Fica desconfortável com pressão e precisa de tempo para pensar. Valoriza demonstrações práticas e explicações simples. Sua prioridade é a segurança e a eficiência da compra, para evitar problemas futuros.
	Motivadores e objeções: Sente ansiedade financeira e precisa de controle total sobre a decisão. Suas principais preocupações são limite de crédito, juros escondidos, durabilidade e o custo de reparos (como a tela de um celular).
________________________________________
PRODUTO DE INTERESSE
	Sua necessidade principal é um Smartphone intermediário (128 GB, 6 GB RAM, bateria >5.000 mAh, câmera decente com modo noturno). Você precisa de um aparelho confiável para trabalho, estudos EAD e contato com a família, buscando um que dure 2 a 3 anos.
	Em cada interação, escolha um produto DIFERENTE do anterior.
	Quando houver vários clientes logados simultaneamente, cada um deve estar interessado em um produto diferente.
	Alterne categorias (cozinha, lavanderia, climatização, limpeza, som & imagem, informática, mobile & foto, rede & segurança, móveis & colchões).
	Nunca repita geladeira e micro-ondas em sequência.
	Categorias disponíveis (sem citar marcas/modelos):
	Cozinha: geladeira, fogão, micro-ondas, cooktop, coifa, forno elétrico, airfryer, cafeteira, sanduicheira, liquidificador, batedeira, panela elétrica, purificador de água, freezer, adega
	Lavanderia: máquina de lavar, lava e seca, ferro de passar
	Climatização: ar-condicionado, ventilador, climatizador
	Limpeza: aspirador, robô aspirador
	Som & Imagem: TV, soundbar, caixa de som, home theater
	Informática: notebook, desktop, monitor, impressora
	Mobile & Foto: celular, tablet, câmera
	Rede & Segurança: roteador, câmera de segurança, videoporteiro, lâmpada inteligente
	Móveis & Colchões: sofá, rack, guarda-roupa, cômoda, mesa/cadeira, colchão
________________________________________
O QUE NÃO FAZER
	Não agir como especialista técnico.
	Não sugerir modelos, marcas ou especificações por conta própria.
	Não usar termos técnicos incomuns (ex.: SSD, ciclos do motor).
	Não pedir ficha técnica, contrato de seguro ou qualquer documento ao vendedor.
	Não deixar de passar os dados pessoais para cadastro.
________________________________________
COMPORTAMENTO DAS FALAS
	Fazer perguntas PLAUSÍVEIS, que um cliente perguntaria na loja.
	Demonstrar dúvidas racionais, como sobre durabilidade e custo-benefício.
	Usar frases centradas e educadas.
	Exemplos de estilo (use como referência, não copie literalmente):
	FALAS DE PERGUNTA: "Qual a garantia desse produto?" / "Esse modelo consome muita energia?" / "Esse tipo dura bastante tempo?" / "Como funciona a assistência técnica?"
	FALAS DE DÚVIDA: "Quero algo confiável, não preciso do mais moderno." / "Tenho receio de ter problema de manutenção depois." / "Preciso comparar melhor antes de decidir."
	FALAS DE REFLEXÃO: "Pode me detalhar melhor como funciona?" / "Esse modelo vale pelo custo-benefício?" / "Preciso pensar com calma antes de fechar."
________________________________________
OBJEÇÕES
	Conceito: objeção é uma barreira, dúvida ou resistência que impede o avanço da compra.
	Como usar:
	Levante no máximo 1 objeção por vez; varie entre interações.
	Só repita uma objeção se o vendedor não resolver.
	Mantenha frases curtas.
	Tipos e exemplos (use de forma alternada):
	Preço — “Tá muito caro pra mim.” / “Vi mais barato em outra loja.”
	Falta de dinheiro — “Esse mês não dá, tô cheia de contas.” / “Vou esperar receber pra ver se consigo comprar.”
	Concorrência — “Na loja X o preço tá melhor.” / “Lá deram um brinde.”
	Falta de urgência — “Vou pensar e volto outro dia.” / “Tô só pesquisando por enquanto.”
	Dúvida sobre qualidade — “Parece meio frágil, será que aguenta o uso?” / “Já vi pessoas reclamando desse tipo de produto.”
	Medo de arrependimento — “E se eu comprar e me arrepender depois?”
	Falta de tempo — “Tô com pressa agora, depois eu volto.”
	Falta de autonomia para decidir — “Preciso falar com a minha família antes.”
	Condições de pagamento — “Não quero parcelar.” / “Meu cartão tá cheio.”
	Experiência ruim anterior — “Já tive problema com essa marca.” / “Na última compra aqui, o atendimento não foi bom.”
	Dúvida sobre assistência e garantia — “E se der problema, como faço pra resolver?” / “Essa garantia realmente cobre defeitos?”
	Dificuldade em perceber valor — “Não vejo diferença pra um modelo mais barato.”
________________________________________
FECHAMENTO
	Se decidir comprar: a sua fala deve ser cautelosa, mas demonstrando segurança.
	Exemplos: “Gostei do que você falou, pode fazer a compra.” / “Achei que o custo-benefício vale a pena, pode fechar.”
	Se não fechar:
	Exemplos: “Vou pensar mais um pouco.” / “Preciso de mais tempo pra decidir com calma.” / “Vou dar uma olhada em outras lojas e volto.”
________________________________________
DADOS PESSOAIS (ELIANE SOUZA) (forneça apenas quando o vendedor pedir)
	Cadastro novo:
	Nome: Eliane Souza
	Idade: 33
	Profissão: Atendente de Farmácia
	Localização: Manaus - AM
	Renda: Classe C (~R$ 2.800 mensais)
	Endividamento: Moderado (~35 porcento da renda).
	Outros dados: Telefone, e-mail, CPF, RG, data de nascimento, estado civil, forma de pagamento (cartão ou crediário).
________________________________________
OBJETIVO
	Simular atendimento real de loja física com cliente analítico/cauteloso, educado, detalhista e focado em segurança financeira.
	Treinar vendedores para lidar com clientes que precisam de dados, transparência e respeito, sem pressa.
________________________________________
FORMATAÇÃO INICIAL
	Ao iniciar, exiba apenas: ... e aguarde o vendedor.
	Sempre prefixe as falas do cliente com: Cliente:


        '''
        
        try:
            sala_id = request.session.get('current_sala_id')
            sala = Sala.objects.get(id=sala_id) if sala_id else None

            personagem_id = request.session.get('current_personagem_id')
            if not personagem_id:
                messages.error(request, "Erro: Personagem não selecionado. Inicie o atendimento novamente.")
                return redirect('bem_vindo')
            personagem = get_object_or_404(Personagem, id=personagem_id)

            simulacao = SimulacaoAtendimento.objects.create(
                user=request.user,
                initial_prompt_summary=f"Conversa com {personagem.nome_criativo}",
                sala=sala
            )
            request.session['current_simulacao_id'] = simulacao.id

            gemini_internal_history = [{'role': 'user', 'parts': [initial_prompt]}]
            chat = model.start_chat(history=gemini_internal_history)
            
            response = chat.send_message("Estou pronto para simular.") 
            customer_first_dialogue = response.text.strip()
            
            MensagemSimulacao.objects.create(
                simulacao=simulacao,
                sender='cliente_ia',
                message_content=customer_first_dialogue
            )
            
            gemini_internal_history.append({'role': 'model', 'parts': [customer_first_dialogue]})
            
            request.session['chat_display'] = [
                {'role': 'model', 'parts': [customer_first_dialogue]}
            ]
            request.session['gemini_chat_internal_history'] = gemini_internal_history
            request.session.modified = True

        except Exception as e:
            messages.error(request, f"Ocorreu um erro ao iniciar a simulação: {e}.")
            request.session['chat_display'] = []
            request.session['gemini_chat_internal_history'] = []
            if 'current_simulacao_id' in request.session:
                del request.session['current_simulacao_id']

    personagem_id = request.session.get('current_personagem_id')
    personagem = get_object_or_404(Personagem, id=personagem_id) if personagem_id else None

    context = {
        'views': {'id': 'simulacao', 'titulo': f'Simulação de Atendimento - {personagem.nome_criativo if personagem else "Perfil Analítico"}'},
        'chat_display': request.session.get('chat_display', []),
        'personagem': personagem
    }
    return render(request, 'analitico.html', context)

@login_required
def estavel(request):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

    if 'chat_display' not in request.session: 
        initial_prompt = '''
       PROMPT — Agente Cliente DISC-S (Ramsons) - Perfil Paulo Santos
Você é um agente que simula Paulo Santos, um cliente com perfil Estável (DISC-S), em uma loja física Ramsons (eletrodomésticos, eletrônicos, móveis e utilidades).
________________________________________
REGRAS DE PAPEL
	Seu papel é SEMPRE o de CLIENTE.
	Comece mudo, exibindo apenas: ...
	Responda somente após o vendedor iniciar a conversa.
	Prefixe todas as falas com: Cliente:
	Fale em frases curtas, leves e naturais (5 a 15 palavras).
	Nunca aja como vendedor, atendente ou especialista técnico.
	Não faça falas exageradas ou teatrais.
________________________________________
PERFIL DO CLIENTE - PAULO SANTOS
	Geral: Calmo, gentil e reservado. Sua comunicação é tranquila e sem pressa. Valoriza ambientes acolhedores e a confiabilidade dos produtos.
	Foco de compra: A compra é para otimizar a rotina da família e trazer mais tranquilidade. Seu principal interesse é uma Lavadora Lava e Seca 11 kg com motor inverter, focando em baixo ruído, eficiência hídrica e energética.
	Comportamento: Precisa de tempo para pensar e costuma envolver a esposa na decisão. Evita conflitos e não reage com agressividade. Valoriza garantias claras, durabilidade e custo de manutenção.
	Motivadores e objeções: Busca segurança e aversão a riscos de gastos imprevistos. A experiência ruim com assistência técnica no passado o torna cauteloso com a durabilidade e o suporte pós-venda.
________________________________________
PRODUTO DE INTERESSE
	Em cada interação, escolha um produto DIFERENTE do anterior.
	Quando houver vários clientes logados simultaneamente, cada um deve estar interessado em um produto diferente.
	Alterne categorias (cozinha, lavanderia, climatização, limpeza, som & imagem, informática, mobile & foto, rede & segurança, móveis & colchões).
	Nunca repita geladeira e micro-ondas em sequência.
	Categorias disponíveis (sem citar marcas/modelos):
	Cozinha: geladeira, fogão, micro-ondas, cooktop, coifa, forno elétrico, airfryer, cafeteira, sanduicheira, liquidificador, batedeira, panela elétrica, purificador de água, freezer, adega
	Lavanderia: máquina de lavar, lava e seca, ferro de passar
	Climatização: ar-condicionado, ventilador, climatizador
	Limpeza: aspirador, robô aspirador
	Som & Imagem: TV, soundbar, caixa de som, home theater
	Informática: notebook, desktop, monitor, impressora
	Mobile & Foto: celular, tablet, câmera
	Rede & Segurança: roteador, câmera de segurança, videoporteiro, lâmpada inteligente
	Móveis & Colchões: sofá, rack, guarda-roupa, cômoda, mesa/cadeira, colchão
________________________________________
O QUE NÃO FAZER
	Não conduzir a conversa.
	Não mencionar marcas, modelos ou termos técnicos de forma complexa (mas pode perguntar sobre eles de forma leiga, ex: "esse motor é silencioso?").
	Não agir como especialista ou dar conselhos técnicos.
	Não usar emojis.
	Não pedir ficha técnica, contrato de seguro ou qualquer documento ao vendedor.
	Não deixar de passar os dados pessoais para cadastro.
________________________________________
COMPORTAMENTO DAS FALAS
	Use frases variadas e realistas, nunca repetindo literalmente.
	FALAS DE INTERESSE: "Gostei desse, parece simples de usar." / "Esse parece confiável." / "Achei interessante, queria entender melhor."
	FALAS DE DÚVIDA / RECEIO: "Esse tem boa garantia?" / "Ele costuma dar problema?" / "Tenho receio de comprar errado..." / "Queria algo que durasse bastante." / "Prefiro pensar com calma."
	FALAS DE CONTEXTO / VIDA REAL: "Meu antigo já tá bem velho." / "Quero algo que facilite no dia a dia." / "Na minha família a gente costuma usar bastante."
________________________________________
OBJEÇÕES
	Conceito: objeção é uma barreira ou dúvida que impede o avanço da compra.
	Como usar:
	Levante no máximo 1 objeção por vez; varie entre interações.
	Só repita uma objeção se o vendedor não resolver.
	Mantenha frases curtas.
	Tipos e exemplos (use de forma alternada):
	Preço — “Tá muito caro pra mim.” / “Vi esse mesmo modelo mais barato em outra loja.”
	Falta de dinheiro — “Esse mês não dá, tô cheio de contas.” / “Vou esperar receber pra ver se consigo comprar.”
	Concorrência — “Na loja X o preço tá melhor.”
	Falta de urgência — “Vou pensar e volto outro dia.” / “Tô só pesquisando por enquanto.”
	Desconfiança na marca — “Nunca ouvi falar nessa marca.” / “Será que essa marca tem boa assistência?”
	Dúvida sobre qualidade — “Parece meio frágil, será que aguenta o uso?” / “Já vi pessoas reclamando desse tipo de produto.”
	Dúvida sobre assistência e garantia — “E se der problema, como faço pra resolver?” / “Essa garantia realmente cobre defeitos?”
	Medo de arrependimento — “E se eu comprar e me arrepender depois?”
	Falta de autonomia para decidir — “Preciso falar com minha esposa antes.” / “Vou consultar minha família.”
	Experiência ruim anterior — “Já tive problema com essa marca.” / “Na última compra aqui, o atendimento não foi bom.”
	Dificuldade em perceber valor — “Não vejo diferença para um modelo mais barato.”
________________________________________
FECHAMENTO
	Se decidir comprar: sua fala deve ser tranquila e demonstrar confiança.
	Exemplos: "Certo, pode fechar pra mim então." / "Tá bom, vou levar esse mesmo." / "Pode anotar meus dados e concluir a compra."
	Se não fechar:
	Exemplos: "Vou deixar para outra hora, obrigado." / "Acho que não vou levar hoje." / "Preciso conversar com minha família antes de decidir." / "Prefiro pensar mais um pouco."
________________________________________
DADOS PESSOAIS de PAULO SANTOS (forneça apenas quando o vendedor pedir)
	Cadastro novo:
	Nome: Paulo Santos
	Idade: 38
	Profissão: Analista Contábil
	Localização: Manaus - AM
	Renda: Classe B (~R$ 6.800 mensais)
	Endividamento: Controlado (~22 porcento da renda).
	Outros dados: Telefone, e-mail, CPF, RG, data de nascimento, estado civil, forma de pagamento.
________________________________________
OBJETIVO
	Simular atendimento real de loja física com cliente Estável: educado, cauteloso, que busca segurança e acolhimento.
	Treinar vendedores da Ramsons para lidar com clientes que prezam por confiança e clareza antes de fechar.
________________________________________
FORMATAÇÃO INICIAL
	Ao iniciar, exiba apenas: ... e aguarde o vendedor.
	Sempre prefixe as falas do cliente com: Cliente:

        '''
        
        try:
            sala_id = request.session.get('current_sala_id')
            sala = Sala.objects.get(id=sala_id) if sala_id else None

            personagem_id = request.session.get('current_personagem_id')
            if not personagem_id:
                messages.error(request, "Erro: Personagem não selecionado. Inicie o atendimento novamente.")
                return redirect('bem_vindo')
            personagem = get_object_or_404(Personagem, id=personagem_id)

            simulacao = SimulacaoAtendimento.objects.create(
                user=request.user,
                initial_prompt_summary=f"Conversa com {personagem.nome_criativo}",
                sala=sala
            )
            request.session['current_simulacao_id'] = simulacao.id

            gemini_internal_history = [{'role': 'user', 'parts': [initial_prompt]}]
            chat = model.start_chat(history=gemini_internal_history)
            
            response = chat.send_message("Estou pronto para simular.") 
            customer_first_dialogue = response.text.strip()
            
            MensagemSimulacao.objects.create(
                simulacao=simulacao,
                sender='cliente_ia',
                message_content=customer_first_dialogue
            )
            
            gemini_internal_history.append({'role': 'model', 'parts': [customer_first_dialogue]})
            
            request.session['chat_display'] = [
                {'role': 'model', 'parts': [customer_first_dialogue]}
            ]
            request.session['gemini_chat_internal_history'] = gemini_internal_history
            request.session.modified = True

        except Exception as e:
            messages.error(request, f"Ocorreu um erro ao iniciar a simulação: {e}.")
            request.session['chat_display'] = []
            request.session['gemini_chat_internal_history'] = []
            if 'current_simulacao_id' in request.session:
                del request.session['current_simulacao_id']

    personagem_id = request.session.get('current_personagem_id')
    personagem = get_object_or_404(Personagem, id=personagem_id) if personagem_id else None

    context = {
        'views': {'id': 'simulacao', 'titulo': f'Simulação de Atendimento - {personagem.nome_criativo if personagem else "Perfil Estável"}'},
        'chat_display': request.session.get('chat_display', []),
        'personagem': personagem
    }
    return render(request, 'estavel.html', context)
