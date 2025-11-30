// JavaScript para o sistema de extração de NF-e

// Agente 3 - Consulta RAG (via backend Python)

    document.addEventListener('DOMContentLoaded', function() {
        console.log('[NF-e] JavaScript carregado com sucesso!');
    
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('file');
    const submitBtn = document.getElementById('submitBtn');
    const loading = document.getElementById('loading');
    const result = document.getElementById('result');
    const error = document.getElementById('error');
    const btnCopyJson = document.getElementById('btnCopyJson');
    const tabsContainer = document.getElementById('tabs-container');
    const saveConfirmation = document.getElementById('save-confirmation');
    const successMessage = document.getElementById('success-message');
    
    console.log('[NF-e] Elementos encontrados:', {
        uploadForm: !!uploadForm,
        fileInput: !!fileInput,
        submitBtn: !!submitBtn,
        loading: !!loading,
        error: !!error,
        tabsContainer: !!tabsContainer,
        saveConfirmation: !!saveConfirmation,
        successMessage: !!successMessage
    });
    
        if (!uploadForm) {
            console.error('[NF-e] ERRO: Formulário não encontrado!');
            return;
        }

        const ragBtn = document.getElementById('rag-btn');
        if (ragBtn) {
            ragBtn.addEventListener('click', function() {
                const pergunta = document.getElementById('rag-pergunta').value.trim();
                const tipo = document.getElementById('rag-tipo').value;
                if (!pergunta) {
                    showError('Digite uma pergunta para consultar o RAG');
                    return;
                }
                consultarRag(pergunta, tipo);
            });
        }

    // Manipula o envio do formulário
    uploadForm.addEventListener('submit', function(e) {
        console.log('[NF-e] Submit interceptado pelo JS');
        e.preventDefault();
        
        const file = fileInput.files[0];
        if (!file) {
            showError('Por favor, selecione um arquivo.');
            return;
        }

        // Validação de tamanho (50MB max)
        if (file.size > 50 * 1024 * 1024) {
            showError('O arquivo é muito grande. Tamanho máximo: 50MB');
            return;
        }

        // Validação de tipo
        const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
        if (!allowedTypes.includes(file.type)) {
            showError('Tipo de arquivo não suportado. Use PDF, PNG ou JPEG.');
            return;
        }

        uploadFile(file);
    });

    function uploadFile(file) {
        // Esconde elementos anteriores
        hideAllMessages();
        
        // Mostra loading
        loading.style.display = 'block';
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processando...';

        // Cria FormData
        const formData = new FormData();
        formData.append('file', file);

        // Faz a requisição para a API
        const endpoint = '/upload/';
        console.log('[NF-e] Enviando POST para', endpoint);
        fetch(endpoint, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(async (response) => {
            let payload = null;
            try {
                payload = await response.json();
            } catch (e) {
                // se não houver JSON, tratar como erro genérico
                throw new Error('Falha ao processar resposta do servidor');
            }

            if (!response.ok || (payload && (payload.error || payload.success === false))) {
                const msg = (payload && (payload.error || payload.message)) || 'Falha ao processar arquivo';
                const details = payload && payload.details ? `\nDetalhes: ${payload.details}` : '';
                throw new Error(msg + details);
            }

            return payload;
        })
        .then(data => {
            console.log('[NF-e] Resposta recebida', data);
            hideAllMessages();
            
            // Usar dados diretamente da resposta da API
            const finalData = data;
            showResult(finalData);
        })
        .catch(err => {
            console.error('[NF-e] Erro na requisição', err);
            hideAllMessages();
            showError(err && err.message ? err.message : 'Erro de conexão');
        })
        .finally(() => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-upload"></i> Extrair Dados da NF-e';
        });
    }

    function consultarRag(pergunta, tipo) {
        hideAllMessages();
        loading.style.display = 'block';
        fetch('/consulta-rag/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ pergunta: pergunta, tipo_rag: tipo })
        })
        .then(async (response) => {
            const payload = await response.json();
            if (!response.ok) {
                const msg = payload && (payload.error || payload.message) || 'Falha na consulta RAG';
                throw new Error(msg);
            }
            return payload;
        })
        .then(data => {
            document.getElementById('rag-resultado').style.display = 'block';
            const resp = data.resposta || 'Sem resposta';
            document.getElementById('rag-resposta').textContent = resp;
        })
        .catch(err => {
            showError(err && err.message ? err.message : 'Erro de conexão');
        })
        .finally(() => {
            loading.style.display = 'none';
        });
    }

    function showBancoInfo(resultadoBanco, resumo) {
        const bancoInfo = document.getElementById('banco-info');
        
        if (!resultadoBanco || Object.keys(resultadoBanco).length === 0) {
            bancoInfo.innerHTML = '<div class="alert alert-warning">Nenhum resultado do banco de dados disponível</div>';
            return;
        }

        let bancoHtml = '';

        // Seção de Resumo
        if (resumo && Object.keys(resumo).length > 0) {
            bancoHtml += `
                <div class="row mb-3">
                    <div class="col-12">
                        <h6 class="text-info mb-2">
                            <i class="fas fa-chart-bar"></i>
                            Resumo das Operações
                        </h6>
                        <div class="row">
                            <div class="col-md-3">
                                <div class="text-center p-2 border rounded ${resumo.fornecedor_criado ? 'bg-success text-white' : 'bg-light'}">
                                    <i class="fas fa-building"></i><br>
                                    <small>Fornecedor</small><br>
                                    <strong>${resumo.fornecedor_criado ? 'CRIADO' : 'EXISTENTE'}</strong>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="text-center p-2 border rounded ${resumo.faturado_criado ? 'bg-success text-white' : 'bg-light'}">
                                    <i class="fas fa-user"></i><br>
                                    <small>Cliente</small><br>
                                    <strong>${resumo.faturado_criado ? 'CRIADO' : 'EXISTENTE'}</strong>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="text-center p-2 border rounded ${resumo.movimento_criado ? 'bg-success text-white' : 'bg-light'}">
                                    <i class="fas fa-file-invoice"></i><br>
                                    <small>Movimento</small><br>
                                    <strong>${resumo.movimento_criado ? 'CRIADO' : 'ERRO'}</strong>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="text-center p-2 border rounded ${resumo.parcelas_criadas > 0 ? 'bg-success text-white' : 'bg-light'}">
                                    <i class="fas fa-credit-card"></i><br>
                                    <small>Parcelas</small><br>
                                    <strong>${resumo.parcelas_criadas || 0}</strong>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        // Seção de Consultas
        if (resultadoBanco.consultas) {
            bancoHtml += `
                <div class="row mb-3">
                    <div class="col-12">
                        <h6 class="text-info mb-2">
                            <i class="fas fa-search"></i>
                            Consultas Realizadas
                        </h6>
                        <div class="table-responsive">
                            <table class="table table-sm table-striped">
                                <thead>
                                    <tr>
                                        <th>Tipo</th>
                                        <th>Nome/Descrição</th>
                                        <th>Documento</th>
                                        <th>Status</th>
                                        <th>ID</th>
                                    </tr>
                                </thead>
                                <tbody>
            `;

            const consultas = resultadoBanco.consultas;
            
            if (consultas.fornecedor) {
                bancoHtml += `
                    <tr>
                        <td><i class="fas fa-building text-primary"></i> Fornecedor</td>
                        <td>${consultas.fornecedor.nome || 'N/A'}</td>
                        <td>${consultas.fornecedor.documento || 'N/A'}</td>
                        <td>
                            <span class="badge ${consultas.fornecedor.existe ? 'bg-warning' : 'bg-success'}">
                                ${consultas.fornecedor.existe ? 'Já existe' : 'Novo registro'}
                            </span>
                        </td>
                        <td>${consultas.fornecedor.id || 'N/A'}</td>
                    </tr>
                `;
            }

            if (consultas.faturado) {
                bancoHtml += `
                    <tr>
                        <td><i class="fas fa-user text-info"></i> Cliente</td>
                        <td>${consultas.faturado.nome || 'N/A'}</td>
                        <td>${consultas.faturado.documento || 'N/A'}</td>
                        <td>
                            <span class="badge ${consultas.faturado.existe ? 'bg-warning' : 'bg-success'}">
                                ${consultas.faturado.existe ? 'Já existe' : 'Novo registro'}
                            </span>
                        </td>
                        <td>${consultas.faturado.id || 'N/A'}</td>
                    </tr>
                `;
            }

            if (consultas.despesa) {
                bancoHtml += `
                    <tr>
                        <td><i class="fas fa-tags text-secondary"></i> Classificação</td>
                        <td>${consultas.despesa.descricao || 'N/A'}</td>
                        <td>-</td>
                        <td>
                            <span class="badge ${consultas.despesa.existe ? 'bg-warning' : 'bg-success'}">
                                ${consultas.despesa.existe ? 'Já existe' : 'Novo registro'}
                            </span>
                        </td>
                        <td>${consultas.despesa.id || 'N/A'}</td>
                    </tr>
                `;
            }

            bancoHtml += `
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        }

        // Mensagem de sucesso
        if (resultadoBanco.mensagem_sucesso) {
            bancoHtml += `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle"></i>
                    ${resultadoBanco.mensagem_sucesso}
                </div>
            `;
        }

        bancoInfo.innerHTML = bancoHtml;
    }

    function showResult(data) {
        // Defaults defensivos para dados extraídos
        const dadosExtraidos = data && data.dados_extraidos ? data.dados_extraidos : data;
        const fornecedorData = dadosExtraidos && dadosExtraidos.fornecedor ? dadosExtraidos.fornecedor : {};
        const faturadoData = dadosExtraidos && dadosExtraidos.faturado ? dadosExtraidos.faturado : {};
        const nfData = dadosExtraidos && dadosExtraidos.nota_fiscal ? dadosExtraidos.nota_fiscal : {};
        const produtosData = Array.isArray(nfData.produtos) ? nfData.produtos : [];
        const parcelasData = Array.isArray(nfData.parcelas) ? nfData.parcelas : [];

        // Dados do banco de dados
        const resultadoBanco = data && data.resultado_banco ? data.resultado_banco : {};
        const resumo = data && data.resumo ? data.resumo : {};

        // Preenche informações do banco de dados
        showBancoInfo(resultadoBanco, resumo);

        // Preenche informações do fornecedor
        const fornecedorInfo = document.getElementById('fornecedor-info');
        fornecedorInfo.innerHTML = `
            <div class="info-item">
                <span class="info-label">Razão Social:</span>
                <span class="info-value">${fornecedorData.razao_social || 'Não informado'}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Nome Fantasia:</span>
                <span class="info-value">${fornecedorData.fantasia || 'Não informado'}</span>
            </div>
            <div class="info-item">
                <span class="info-label">CNPJ:</span>
                <span class="info-value">${fornecedorData.cnpj || 'Não informado'}</span>
            </div>
        `;

        // Preenche informações do cliente
        const clienteInfo = document.getElementById('cliente-info');
        clienteInfo.innerHTML = `
            <div class="info-item">
                <span class="info-label">Nome:</span>
                <span class="info-value">${faturadoData.nome || 'Não informado'}</span>
            </div>
            <div class="info-item">
                <span class="info-label">CPF:</span>
                <span class="info-value">${faturadoData.cpf || 'Não informado'}</span>
            </div>
        `;

        // Preenche informações da nota fiscal
        const nfInfo = document.getElementById('nf-info');
        nfInfo.innerHTML = `
            <div class="row">
                <div class="col-md-4">
                    <div class="info-item">
                        <span class="info-label">Número:</span>
                        <span class="info-value">${nfData.numero || 'Não informado'}</span>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="info-item">
                        <span class="info-label">Série:</span>
                        <span class="info-value">${nfData.serie || 'Não informado'}</span>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="info-item">
                        <span class="info-label">Data Emissão:</span>
                        <span class="info-value">${nfData.data_emissao || 'Não informado'}</span>
                    </div>
                </div>
            </div>
            <div class="row mt-2">
                <div class="col-md-6">
                    <div class="info-item">
                        <span class="info-label">Valor Total:</span>
                        <span class="info-value">R$ ${formatCurrency(nfData.valor_total)}</span>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="info-item">
                        <span class="info-label">Classificação:</span>
                        <span class="info-value">${nfData.classificacao_despesa || 'Não informado'}</span>
                    </div>
                </div>
            </div>
        `;

        // Preenche produtos
        const produtosInfo = document.getElementById('produtos-info');
        if (produtosData && produtosData.length > 0) {
            let produtosHtml = `
                <div class="table-responsive">
                    <table class="table table-sm table-striped">
                        <thead>
                            <tr>
                                <th>Descrição</th>
                                <th>Quantidade</th>
                                <th>Valor Unitário</th>
                                <th>Valor Total</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            produtosData.forEach(produto => {
                const valorUnitarioFormatted = formatCurrency(produto.valor_unitario);
                const valorTotalCalculated = calculateTotal(produto.quantidade, produto.valor_unitario);
                
                produtosHtml += `
                    <tr>
                        <td>${produto.descricao || 'Não informado'}</td>
                        <td>${produto.quantidade || 0}</td>
                        <td>R$ ${valorUnitarioFormatted}</td>
                        <td>R$ ${valorTotalCalculated}</td>
                    </tr>
                `;
            });
            
            produtosHtml += `
                        </tbody>
                    </table>
                </div>
            `;
            produtosInfo.innerHTML = produtosHtml;
        } else {
            produtosInfo.innerHTML = '<div class="info-item">Nenhum produto encontrado</div>';
        }

        // Preenche parcelas
        const parcelasInfo = document.getElementById('parcelas-info');
        if (parcelasData && parcelasData.length > 0) {
            let parcelasHtml = `
                <div class="table-responsive">
                    <table class="table table-sm table-striped">
                        <thead>
                            <tr>
                                <th>Parcela</th>
                                <th>Data Vencimento</th>
                                <th>Valor</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            parcelasData.forEach(parcela => {
                parcelasHtml += `
                    <tr>
                        <td>${parcela.numero || 1}</td>
                        <td>${parcela.data_vencimento || 'Não informado'}</td>
                        <td>R$ ${formatCurrency(parcela.valor)}</td>
                    </tr>
                `;
            });
            
            parcelasHtml += `
                        </tbody>
                    </table>
                </div>
            `;
            parcelasInfo.innerHTML = parcelasHtml;
        } else {
            parcelasInfo.innerHTML = '<div class="info-item">Nenhuma parcela encontrada</div>';
        }

        // Mostra JSON no bloco padrão
        const jsonRaw = document.getElementById('json-raw');
        jsonRaw.textContent = JSON.stringify({
            fornecedor: fornecedorData,
            faturado: faturadoData,
            nota_fiscal: {
                ...nfData,
                produtos: produtosData,
                parcelas: parcelasData
            }
        }, null, 2);

        // Habilita copiar JSON
        if (btnCopyJson) {
            btnCopyJson.onclick = async () => {
                try {
                    await navigator.clipboard.writeText(jsonRaw.textContent);
                    btnCopyJson.innerHTML = '<i class="fas fa-check"></i> Copiado';
                    setTimeout(() => btnCopyJson.innerHTML = '<i class="fas fa-copy"></i> Copiar JSON', 1500);
                } catch (e) {
                    console.error('Falha ao copiar JSON', e);
                }
            };
        }

        // Exibe o container de abas
        tabsContainer.style.display = 'block';
        tabsContainer.classList.add('fade-in');
    }

    function showError(message) {
        const errorDiv = document.getElementById('error');
        const errorMessage = document.getElementById('error-message');
        errorMessage.textContent = message;
        errorDiv.style.display = 'block';
    }

    function hideAllMessages() {
        loading.style.display = 'none';
        tabsContainer.style.display = 'none';
        error.style.display = 'none';
        saveConfirmation.style.display = 'none';
        successMessage.style.display = 'none';
    }

    // Função para pegar CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
 
    function formatCurrency(value) {
        if (!value || value === '0' || value === '0.00') return '0,00';
        
        // Remove R$ e espaços
        let numStr = value.toString().replace(/R\$\s*/g, '').trim();
        
        // Se já está no formato brasileiro (com vírgula), converte para número
        if (numStr.includes(',') && !numStr.includes('.')) {
            numStr = numStr.replace(',', '.');
        }
        
        // Converte para número e formata
        const num = parseFloat(numStr);
        if (isNaN(num)) return '0,00';
        
        return num.toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    function calculateTotal(quantidade, valorUnitario) {
        if (!quantidade || !valorUnitario) return '0,00';
        
        const qtd = parseFloat(quantidade.toString().replace(',', '.'));
        const vu = parseFloat(valorUnitario.toString().replace(/R\$\s*/g, '').replace(',', '.'));
        
        if (isNaN(qtd) || isNaN(vu)) return '0,00';
        
        const total = qtd * vu;
        return total.toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    // Funções para Consulta RAG (backend Python)

    // Função para realizar consulta RAG
    window.realizarConsultaRAG = function() {
        const pergunta = document.getElementById('pergunta-rag').value.trim();
        const tipoRag = document.getElementById('tipo-rag') ? document.getElementById('tipo-rag').value : 'simples';
        const resultadoDiv = document.getElementById('resultado-rag');
        const botaoConsultar = document.getElementById('btn-consultar-rag');

        if (!pergunta) {
            resultadoDiv.innerHTML = '<div class="alert alert-warning">Por favor, digite uma pergunta.</div>';
            return;
        }

        // Desabilita botão durante consulta
        botaoConsultar.disabled = true;
        botaoConsultar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Consultando...';
        resultadoDiv.innerHTML = '<div class="alert alert-info"><i class="fas fa-spinner fa-spin"></i> Processando consulta...</div>';

        // Chamada ao backend
        fetch('/consulta-rag/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ pergunta: pergunta, tipo_rag: tipoRag })
        })
        .then(async (response) => {
            let payload;
            try { payload = await response.json(); } catch (e) { throw new Error('Resposta inválida do servidor'); }
            if (!response.ok || payload.error) {
                const msg = payload.error || 'Falha na consulta RAG';
                const details = payload.details ? `\nDetalhes: ${payload.details}` : '';
                throw new Error(msg + details);
            }
            return payload;
        })
        .then(data => {
            if (data && data.resposta) {
                resultadoDiv.innerHTML = `
                    <div class="rag-response">
                        <div class="response-header">
                            <h5><i class="fas fa-brain"></i> Resposta do Agente 03</h5>
                            <small class="text-muted">Modalidade: ${data.tipo_rag || tipoRag} | Confiança: ${data.confianca}% | Fontes: ${data.fontes}</small>
                        </div>
                        <div class="response-content">
                            ${data.resposta}
                        </div>
                        ${data.mensagem ? `<div class="mt-2"><small class="text-muted">${data.mensagem}</small></div>` : ''}
                    </div>
                `;
            } else {
                resultadoDiv.innerHTML = '<div class="alert alert-danger">Erro ao processar consulta: ' + (data && data.error ? data.error : 'Erro desconhecido') + '</div>';
            }
        })
        .catch(error => {
            console.error('Erro na consulta RAG:', error);
            resultadoDiv.innerHTML = '<div class="alert alert-danger">' + (error && error.message ? error.message : 'Erro ao conectar com o servidor') + '</div>';
        })
        .finally(() => {
            botaoConsultar.disabled = false;
            botaoConsultar.innerHTML = '<i class="fas fa-search"></i> Consultar';
        });
    };
});
