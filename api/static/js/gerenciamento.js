// Sistema de Gerenciamento - JavaScript

// Variáveis globais
let paginaAtualPessoas = 1;
let paginaAtualClassificacoes = 1;
let paginaAtualMovimentos = 1;
let paginaAtualParcelas = 1;
const itensPorPagina = 10;
window.filtroMovStatus = '';
window.filtroParcStatus = '';

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
});

// ===== FUNÇÕES UTILITÁRIAS =====

function mostrarMensagem(tipo, titulo, mensagem) {
    const container = document.getElementById('mensagens-container');
    const toastId = 'toast-' + Date.now();
    
    const toastHtml = `
        <div class="toast" id="${toastId}" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="fas fa-${tipo === 'success' ? 'check-circle text-success' : 'exclamation-triangle text-danger'}"></i>
                <strong class="me-auto ms-2">${titulo}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${mensagem}
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', toastHtml);
    const toast = new bootstrap.Toast(document.getElementById(toastId));
    toast.show();
    
    // Remove o toast após 5 segundos
    setTimeout(() => {
        const element = document.getElementById(toastId);
        if (element) element.remove();
    }, 5000);
}

function mostrarLoading() {
    const loadingHtml = `
        <div class="loading-overlay" id="loading-overlay">
            <div class="text-center">
                <i class="fas fa-spinner fa-spin loading-spinner"></i>
                <div class="text-white mt-2">Carregando...</div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', loadingHtml);
}

function esconderLoading() {
    const loading = document.getElementById('loading-overlay');
    if (loading) loading.remove();
}

function formatarData(dataString) {
    if (!dataString) return '-';
    const data = new Date(dataString);
    return data.toLocaleDateString('pt-BR');
}

function formatarMoeda(valor) {
    if (!valor) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(valor);
}

// ===== PESSOAS =====

async function carregarPessoas(pagina = 1) {
    try {
        mostrarLoading();
        
        const filtros = obterFiltrosPessoas();
        const params = new URLSearchParams({
            page: pagina,
            ...filtros
        });
        
        const response = await fetch(`/gerenciar/pessoas/?${params}`);
        const data = await response.json();
        
        if (data.pessoas) {
            renderizarTabelaPessoas(data.pessoas);
            renderizarPaginacaoPessoas({
                current_page: data.page,
                total_pages: data.total_pages,
                total_items: data.total
            });
            paginaAtualPessoas = pagina;
        } else {
            mostrarMensagem('error', 'Erro', 'Erro ao carregar pessoas');
        }
    } catch (error) {
        console.error('Erro:', error);
        mostrarMensagem('error', 'Erro', 'Erro de conexão');
    } finally {
        esconderLoading();
    }
}

function obterFiltrosPessoas() {
    const nome = document.getElementById('filtro-pessoas-nome').value;
    const documento = document.getElementById('filtro-pessoas-documento').value;
    const tipo = document.getElementById('filtro-pessoas-tipo').value;
    const status = document.getElementById('filtro-pessoas-status').value;
    
    // Combinar nome e documento em search
    const searchTerms = [nome, documento].filter(term => term.trim()).join(' ');
    
    return {
        search: searchTerms,
        tipo: tipo,
        status: status
    };
}

function aplicarFiltrosPessoas() {
    carregarPessoas(1);
}
function carregarPessoasTodos() {
    document.getElementById('filtro-pessoas-nome').value = '';
    document.getElementById('filtro-pessoas-documento').value = '';
    document.getElementById('filtro-pessoas-tipo').value = '';
    document.getElementById('filtro-pessoas-status').value = 'true';
    carregarPessoas(1);
}

function renderizarTabelaPessoas(pessoas) {
    const tbody = document.getElementById('pessoas-tbody');
    
    if (!pessoas || pessoas.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted py-4">
                    <i class="fas fa-users fa-2x mb-2"></i><br>
                    Nenhuma pessoa encontrada
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = pessoas.map(pessoa => `
        <tr class="${!pessoa.ativo ? 'registro-inativo' : ''}">
            <td>${pessoa.id}</td>
            <td class="fw-semibold">${pessoa.nome}</td>
            <td>${pessoa.documento || '-'}</td>
            <td>
                <span class="badge ${pessoa.tipo === 'FORNECEDOR' ? 'bg-primary' : 'bg-info'}">
                    ${pessoa.tipo}
                </span>
            </td>
            <td>
                <span class="badge ${pessoa.ativo ? 'bg-success' : 'bg-danger'}">
                    ${pessoa.ativo ? 'Ativo' : 'Inativo'}
                </span>
            </td>
            <td>${formatarData(pessoa.created_at)}</td>
            <td>
                <div class="btn-group-sm">
                    ${pessoa.ativo ? `
                        <button class="btn btn-outline-primary btn-sm" onclick="editarPessoa(${pessoa.id})">
                            <i class="fas fa-edit"></i> Editar
                        </button>
                        <button class="btn btn-outline-warning btn-sm" onclick="alterarStatusPessoa(${pessoa.id}, false)">
                            <i class="fas fa-ban"></i> Inativar
                        </button>
                    ` : `
                        <button class="btn btn-outline-success btn-sm" onclick="alterarStatusPessoa(${pessoa.id}, true)">
                            <i class="fas fa-check"></i> Reativar
                        </button>
                    `}
                </div>
            </td>
        </tr>
    `).join('');
    habilitarOrdenacao('pessoas-tbody');
}

function renderizarPaginacaoPessoas(pagination) {
    const container = document.getElementById('pessoas-paginacao');
    
    if (pagination.total_pages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let paginasHtml = '';
    
    // Botão anterior
    if (pagination.current_page > 1) {
        paginasHtml += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="carregarPessoas(${pagination.current_page - 1})">
                    <i class="fas fa-chevron-left"></i>
                </a>
            </li>
        `;
    }
    
    // Páginas
    for (let i = 1; i <= pagination.total_pages; i++) {
        if (i === pagination.current_page) {
            paginasHtml += `
                <li class="page-item active">
                    <span class="page-link">${i}</span>
                </li>
            `;
        } else {
            paginasHtml += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="carregarPessoas(${i})">${i}</a>
                </li>
            `;
        }
    }
    
    // Botão próximo
    if (pagination.current_page < pagination.total_pages) {
        paginasHtml += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="carregarPessoas(${pagination.current_page + 1})">
                    <i class="fas fa-chevron-right"></i>
                </a>
            </li>
        `;
    }
    
    container.innerHTML = `
        <ul class="pagination justify-content-center">
            ${paginasHtml}
        </ul>
        <div class="text-center text-muted mt-2">
            Página ${pagination.current_page} de ${pagination.total_pages} 
            (${pagination.total_items} registros)
        </div>
    `;
}

async function alterarStatusPessoa(id, novoStatus) {
    const acao = novoStatus ? 'reativar' : 'inativar';
    
    if (!confirm(`Tem certeza que deseja ${acao} esta pessoa?`)) {
        return;
    }
    
    try {
        mostrarLoading();
        
        const response = await fetch(`/gerenciar/pessoas/${id}/status/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ ativo: novoStatus })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const acao = novoStatus ? 'reativado' : 'inativado';
            mostrarMensagem('success', 'Sucesso', `Registro ${acao} com sucesso.`);
            carregarPessoas(paginaAtualPessoas);
        } else {
            mostrarMensagem('error', 'Erro', data.error || 'Erro ao alterar status');
        }
    } catch (error) {
        console.error('Erro:', error);
        mostrarMensagem('error', 'Erro', 'Erro de conexão');
    } finally {
        esconderLoading();
    }
}

// ===== CLASSIFICAÇÕES =====

async function carregarClassificacoes(pagina = 1) {
    try {
        mostrarLoading();
        
        const filtros = obterFiltrosClassificacoes();
        const params = new URLSearchParams({
            page: pagina,
            ...filtros
        });
        
        const response = await fetch(`/gerenciar/classificacoes/?${params}`);
        const data = await response.json();
        
        if (data.classificacoes) {
            renderizarTabelaClassificacoes(data.classificacoes);
            renderizarPaginacaoClassificacoes({
                current_page: data.page,
                total_pages: data.total_pages,
                total_items: data.total
            });
            paginaAtualClassificacoes = pagina;
        } else {
            mostrarMensagem('error', 'Erro', 'Erro ao carregar classificações');
        }
    } catch (error) {
        console.error('Erro:', error);
        mostrarMensagem('error', 'Erro', 'Erro de conexão');
    } finally {
        esconderLoading();
    }
}

function obterFiltrosClassificacoes() {
    return {
        search: document.getElementById('filtro-classificacoes-descricao').value,
        tipo: document.getElementById('filtro-classificacoes-tipo').value,
        status: document.getElementById('filtro-classificacoes-status').value
    };
}

function aplicarFiltrosClassificacoes() {
    carregarClassificacoes(1);
}
function carregarClassificacoesTodos() {
    document.getElementById('filtro-classificacoes-descricao').value = '';
    document.getElementById('filtro-classificacoes-tipo').value = '';
    document.getElementById('filtro-classificacoes-status').value = 'true';
    carregarClassificacoes(1);
}

function renderizarTabelaClassificacoes(classificacoes) {
    const tbody = document.getElementById('classificacoes-tbody');
    
    if (!classificacoes || classificacoes.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted py-4">
                    <i class="fas fa-tags fa-2x mb-2"></i><br>
                    Nenhuma classificação encontrada
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = classificacoes.map(classificacao => `
        <tr class="${!classificacao.ativo ? 'registro-inativo' : ''}">
            <td>${classificacao.id}</td>
            <td class="fw-semibold">${classificacao.descricao}</td>
            <td>
                <span class="badge ${classificacao.tipo === 'DESPESA' ? 'bg-danger' : 'bg-success'}">
                    ${classificacao.tipo}
                </span>
            </td>
            <td>
                <span class="badge ${classificacao.ativo ? 'bg-success' : 'bg-danger'}">
                    ${classificacao.ativo ? 'Ativo' : 'Inativo'}
                </span>
            </td>
            <td>${formatarData(classificacao.created_at)}</td>
            <td>
                <div class="btn-group-sm">
                    ${classificacao.ativo ? `
                        <button class="btn btn-outline-primary btn-sm" onclick="editarClassificacao(${classificacao.id})">
                            <i class="fas fa-edit"></i> Editar
                        </button>
                        <button class="btn btn-outline-warning btn-sm" onclick="alterarStatusClassificacao(${classificacao.id}, false)">
                            <i class="fas fa-ban"></i> Inativar
                        </button>
                    ` : `
                        <button class="btn btn-outline-success btn-sm" onclick="alterarStatusClassificacao(${classificacao.id}, true)">
                            <i class="fas fa-check"></i> Reativar
                        </button>
                    `}
                </div>
            </td>
        </tr>
    `).join('');
    habilitarOrdenacao('classificacoes-tbody');
}

function renderizarPaginacaoClassificacoes(pagination) {
    const container = document.getElementById('classificacoes-paginacao');
    
    if (pagination.total_pages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let paginasHtml = '';
    
    if (pagination.current_page > 1) {
        paginasHtml += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="carregarClassificacoes(${pagination.current_page - 1})">
                    <i class="fas fa-chevron-left"></i>
                </a>
            </li>
        `;
    }
    
    for (let i = 1; i <= pagination.total_pages; i++) {
        if (i === pagination.current_page) {
            paginasHtml += `
                <li class="page-item active">
                    <span class="page-link">${i}</span>
                </li>
            `;
        } else {
            paginasHtml += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="carregarClassificacoes(${i})">${i}</a>
                </li>
            `;
        }
    }
    
    if (pagination.current_page < pagination.total_pages) {
        paginasHtml += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="carregarClassificacoes(${pagination.current_page + 1})">
                    <i class="fas fa-chevron-right"></i>
                </a>
            </li>
        `;
    }
    
    container.innerHTML = `
        <ul class="pagination justify-content-center">
            ${paginasHtml}
        </ul>
        <div class="text-center text-muted mt-2">
            Página ${pagination.current_page} de ${pagination.total_pages} 
            (${pagination.total_items} registros)
        </div>
    `;
}

async function alterarStatusClassificacao(id, novoStatus) {
    const acao = novoStatus ? 'reativar' : 'inativar';
    
    if (!confirm(`Tem certeza que deseja ${acao} esta classificação?`)) {
        return;
    }
    
    try {
        mostrarLoading();
        
        const response = await fetch(`/gerenciar/classificacoes/${id}/status/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ ativo: novoStatus })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const acao = novoStatus ? 'reativado' : 'inativado';
            mostrarMensagem('success', 'Sucesso', `Registro ${acao} com sucesso.`);
            carregarClassificacoes(paginaAtualClassificacoes);
        } else {
            mostrarMensagem('error', 'Erro', data.error || 'Erro ao alterar status');
        }
    } catch (error) {
        console.error('Erro:', error);
        mostrarMensagem('error', 'Erro', 'Erro de conexão');
    } finally {
        esconderLoading();
    }
}

// ===== MOVIMENTOS =====

async function carregarMovimentos(pagina = 1) {
    try {
        mostrarLoading();
        
        const filtros = obterFiltrosMovimentos();
        const params = new URLSearchParams({
            page: pagina,
            ...filtros
        });
        
        const response = await fetch(`/gerenciar/movimentos/?${params}`);
        const data = await response.json();
        
        if (data.movimentos) {
            renderizarTabelaMovimentos(data.movimentos);
            renderizarPaginacaoMovimentos({
                current_page: data.page,
                total_pages: data.total_pages,
                total_items: data.total
            });
            paginaAtualMovimentos = pagina;
        } else {
            mostrarMensagem('error', 'Erro', 'Erro ao carregar movimentos');
        }
    } catch (error) {
        console.error('Erro:', error);
        mostrarMensagem('error', 'Erro', 'Erro de conexão');
    } finally {
        esconderLoading();
    }
}

function obterFiltrosMovimentos() {
    return {
        search: document.getElementById('filtro-movimentos-search').value,
        status: window.filtroMovStatus
    };
}

function aplicarFiltrosMovimentos() {
    carregarMovimentos(1);
}
function carregarMovimentosTodos() {
    document.getElementById('filtro-movimentos-search').value = '';
    window.filtroMovStatus = 'true';
    carregarMovimentos(1);
}

function renderizarTabelaMovimentos(movimentos) {
    const tbody = document.getElementById('movimentos-tbody');
    
    if (!movimentos || movimentos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" class="text-center text-muted py-4">
                    <i class="fas fa-file-invoice-dollar fa-2x mb-2"></i><br>
                    Nenhum movimento encontrado
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = movimentos.map(movimento => `
        <tr>
            <td>${movimento.id}</td>
            <td class="fw-semibold">${movimento.numero_nf}</td>
            <td>${movimento.serie_nf || '-'}</td>
            <td>${formatarData(movimento.data_emissao)}</td>
            <td>${movimento.fornecedor || '-'}</td>
            <td>${movimento.faturado || '-'}</td>
            <td class="fw-semibold">${formatarMoeda(movimento.valor_total)}</td>
            <td>
                <span class="badge bg-info">${movimento.quantidade_parcelas || 0}</span>
            </td>
            <td>
                <span class="badge ${movimento.ativo ? 'bg-success' : 'bg-danger'}">
                    ${movimento.ativo ? 'Ativo' : 'Inativo'}
                </span>
            </td>
            <td>
                <div class="btn-group-sm">
                    <button class="btn btn-outline-primary btn-sm" onclick="editarMovimento(${movimento.id})">
                        <i class="fas fa-edit"></i> Editar
                    </button>
                    ${movimento.ativo ? `
                    <button class="btn btn-outline-warning btn-sm" onclick="alterarStatusMovimento(${movimento.id}, false)">
                        <i class="fas fa-ban"></i> Inativar
                    </button>` : `
                    <button class="btn btn-outline-success btn-sm" onclick="alterarStatusMovimento(${movimento.id}, true)">
                        <i class="fas fa-check"></i> Reativar
                    </button>`}
                </div>
            </td>
        </tr>
    `).join('');
    habilitarOrdenacao('movimentos-tbody');
}

function renderizarPaginacaoMovimentos(pagination) {
    const container = document.getElementById('movimentos-paginacao');
    
    if (pagination.total_pages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let paginasHtml = '';
    
    if (pagination.current_page > 1) {
        paginasHtml += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="carregarMovimentos(${pagination.current_page - 1})">
                    <i class="fas fa-chevron-left"></i>
                </a>
            </li>
        `;
    }
    
    for (let i = 1; i <= pagination.total_pages; i++) {
        if (i === pagination.current_page) {
            paginasHtml += `
                <li class="page-item active">
                    <span class="page-link">${i}</span>
                </li>
            `;
        } else {
            paginasHtml += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="carregarMovimentos(${i})">${i}</a>
                </li>
            `;
        }
    }
    
    if (pagination.current_page < pagination.total_pages) {
        paginasHtml += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="carregarMovimentos(${pagination.current_page + 1})">
                    <i class="fas fa-chevron-right"></i>
                </a>
            </li>
        `;
    }
    
    container.innerHTML = `
        <ul class="pagination justify-content-center">
            ${paginasHtml}
        </ul>
        <div class="text-center text-muted mt-2">
            Página ${pagination.current_page} de ${pagination.total_pages} 
            (${pagination.total_items} registros)
        </div>
    `;
}

// ===== PARCELAS =====

async function carregarParcelas(pagina = 1) {
    try {
        mostrarLoading();
        
        const filtros = obterFiltrosParcelas();
        const params = new URLSearchParams({
            page: pagina,
            ...filtros
        });
        
        const response = await fetch(`/gerenciar/parcelas/?${params}`);
        const data = await response.json();
        
        if (data.parcelas) {
            renderizarTabelaParcelas(data.parcelas);
            renderizarPaginacaoParcelas({
                current_page: data.page,
                total_pages: data.total_pages,
                total_items: data.total
            });
            paginaAtualParcelas = pagina;
        } else {
            mostrarMensagem('error', 'Erro', 'Erro ao carregar parcelas');
        }
    } catch (error) {
        console.error('Erro:', error);
        mostrarMensagem('error', 'Erro', 'Erro de conexão');
    } finally {
        esconderLoading();
    }
}

function obterFiltrosParcelas() {
    return {
        search: document.getElementById('filtro-parcelas-search').value,
        status: window.filtroParcStatus
    };
}

function aplicarFiltrosParcelas() {
    carregarParcelas(1);
}
function carregarParcelasTodos() {
    document.getElementById('filtro-parcelas-search').value = '';
    window.filtroParcStatus = 'true';
    carregarParcelas(1);
}

function renderizarTabelaParcelas(parcelas) {
    const tbody = document.getElementById('parcelas-tbody');
    
    if (!parcelas || parcelas.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted py-4">
                    <i class="fas fa-credit-card fa-2x mb-2"></i><br>
                    Nenhuma parcela encontrada
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = parcelas.map(parcela => `
        <tr>
            <td>${parcela.id}</td>
            <td class="fw-semibold">${parcela.numero_nf}</td>
            <td>
                <span class="badge bg-secondary">${parcela.numero_parcela}</span>
            </td>
            <td>${formatarData(parcela.data_vencimento)}</td>
            <td class="fw-semibold">${formatarMoeda(parcela.valor_parcela)}</td>
            <td>
                <span class="badge ${parcela.ativo ? 'bg-success' : 'bg-danger'}">
                    ${parcela.ativo ? 'Ativa' : 'Inativa'}
                </span>
            </td>
            <td>
                <div class="btn-group-sm">
                    <button class="btn btn-outline-primary btn-sm" onclick="editarParcela(${parcela.id})">
                        <i class="fas fa-edit"></i> Editar
                    </button>
                    ${parcela.ativo ? `
                    <button class="btn btn-outline-warning btn-sm" onclick="alterarStatusParcela(${parcela.id}, false)">
                        <i class="fas fa-ban"></i> Inativar
                    </button>` : `
                    <button class="btn btn-outline-success btn-sm" onclick="alterarStatusParcela(${parcela.id}, true)">
                        <i class="fas fa-check"></i> Reativar
                    </button>`}
                </div>
            </td>
        </tr>
    `).join('');
    habilitarOrdenacao('parcelas-tbody');
}

function renderizarPaginacaoParcelas(pagination) {
    const container = document.getElementById('parcelas-paginacao');
    
    if (pagination.total_pages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let paginasHtml = '';
    
    if (pagination.current_page > 1) {
        paginasHtml += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="carregarParcelas(${pagination.current_page - 1})">
                    <i class="fas fa-chevron-left"></i>
                </a>
            </li>
        `;
    }
    
    for (let i = 1; i <= pagination.total_pages; i++) {
        if (i === pagination.current_page) {
            paginasHtml += `
                <li class="page-item active">
                    <span class="page-link">${i}</span>
                </li>
            `;
        } else {
            paginasHtml += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="carregarParcelas(${i})">${i}</a>
                </li>
            `;
        }
    }
    
    if (pagination.current_page < pagination.total_pages) {
        paginasHtml += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="carregarParcelas(${pagination.current_page + 1})">
                    <i class="fas fa-chevron-right"></i>
                </a>
            </li>
        `;
    }
    
    container.innerHTML = `
        <ul class="pagination justify-content-center">
            ${paginasHtml}
        </ul>
        <div class="text-center text-muted mt-2">
            Página ${pagination.current_page} de ${pagination.total_pages} 
            (${pagination.total_items} registros)
        </div>
    `;
}

// ===== FUNÇÕES DE EDIÇÃO (PLACEHOLDERS) =====

function editarPessoa(id) {
    const container = document.getElementById('modals-container');
    const mid = 'modal-editar-pessoa';
    container.innerHTML = `
    <div class="modal" tabindex="-1" id="${mid}">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header"><h5 class="modal-title">Editar Pessoa</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
          <div class="modal-body">
            <div class="mb-2"><label class="form-label">Nome</label><input class="form-control" id="editar-pessoa-nome"></div>
            <div class="mb-2"><label class="form-label">Documento</label><input class="form-control" id="editar-pessoa-documento"></div>
            <div class="mb-2"><label class="form-label">Tipo</label><select class="form-select" id="editar-pessoa-tipo"><option value="FORNECEDOR">Fornecedor</option><option value="FATURADO">Cliente</option></select></div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
            <button class="btn btn-primary" onclick="salvarPessoa(${id})">Salvar</button>
          </div>
        </div>
      </div>
    </div>`;
    new bootstrap.Modal(document.getElementById(mid)).show();
}

async function salvarPessoa(id) {
    try {
        const nome = document.getElementById('editar-pessoa-nome').value.trim();
        const documento = document.getElementById('editar-pessoa-documento').value.trim();
        const tipo = document.getElementById('editar-pessoa-tipo').value;
        const resp = await fetch(`/gerenciar/pessoas/${id}/`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
            body: JSON.stringify({ nome, documento, tipo })
        });
        const data = await resp.json();
        if (data.success) {
            mostrarMensagem('success', 'Sucesso', 'Pessoa atualizada');
            carregarPessoas(paginaAtualPessoas);
            document.querySelector('#modal-editar-pessoa .btn-close').click();
        } else {
            mostrarMensagem('error', 'Erro', data.error || 'Erro ao salvar');
        }
    } catch (e) {
        mostrarMensagem('error', 'Erro', 'Erro de conexão');
    }
}

function editarClassificacao(id) {
    const container = document.getElementById('modals-container');
    const mid = 'modal-editar-classificacao';
    container.innerHTML = `
    <div class="modal" tabindex="-1" id="${mid}">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header"><h5 class="modal-title">Editar Classificação</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
          <div class="modal-body">
            <div class="mb-2"><label class="form-label">Descrição</label><input class="form-control" id="editar-class-descricao"></div>
            <div class="mb-2"><label class="form-label">Tipo</label><select class="form-select" id="editar-class-tipo"><option value="DESPESA">Despesa</option><option value="RECEITA">Receita</option></select></div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
            <button class="btn btn-primary" onclick="salvarClassificacao(${id})">Salvar</button>
          </div>
        </div>
      </div>
    </div>`;
    new bootstrap.Modal(document.getElementById(mid)).show();
}

async function salvarClassificacao(id) {
    try {
        const descricao = document.getElementById('editar-class-descricao').value.trim();
        const tipo = document.getElementById('editar-class-tipo').value;
        const resp = await fetch(`/gerenciar/classificacoes/${id}/`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
            body: JSON.stringify({ descricao, tipo })
        });
        const data = await resp.json();
        if (data.success) {
            mostrarMensagem('success', 'Sucesso', 'Classificação atualizada');
            carregarClassificacoes(paginaAtualClassificacoes);
            document.querySelector('#modal-editar-classificacao .btn-close').click();
        } else {
            mostrarMensagem('error', 'Erro', data.error || 'Erro ao salvar');
        }
    } catch (e) {
        mostrarMensagem('error', 'Erro', 'Erro de conexão');
    }
}

function editarMovimento(id) {
    mostrarMensagem('info', 'Em desenvolvimento', 'Funcionalidade de edição será implementada em breve');
}

function editarParcela(id) {
    mostrarMensagem('info', 'Em desenvolvimento', 'Funcionalidade de edição será implementada em breve');
}

function abrirModalNovaPessoa() {
    const container = document.getElementById('modals-container');
    const id = 'modal-nova-pessoa';
    container.innerHTML = `
    <div class="modal" tabindex="-1" id="${id}">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header"><h5 class="modal-title">Nova Pessoa</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
          <div class="modal-body">
            <div class="mb-2"><label class="form-label">Nome</label><input class="form-control" id="nova-pessoa-nome"></div>
            <div class="mb-2"><label class="form-label">Documento</label><input class="form-control" id="nova-pessoa-documento"></div>
            <div class="mb-2"><label class="form-label">Tipo</label><select class="form-select" id="nova-pessoa-tipo"><option value="FORNECEDOR">Fornecedor</option><option value="FATURADO">Cliente</option></select></div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
            <button class="btn btn-primary" onclick="criarPessoa()">Salvar</button>
          </div>
        </div>
      </div>
    </div>`;
    const m = new bootstrap.Modal(document.getElementById(id));
    m.show();
}

async function criarPessoa() {
    try {
        const nome = document.getElementById('nova-pessoa-nome').value.trim();
        const documento = document.getElementById('nova-pessoa-documento').value.trim();
        const tipo = document.getElementById('nova-pessoa-tipo').value;
        const response = await fetch('/gerenciar/pessoas/criar/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
            body: JSON.stringify({ nome, documento, tipo })
        });
        const data = await response.json();
        if (data.success) {
            mostrarMensagem('success', 'Sucesso', 'Pessoa criada com sucesso');
            document.querySelector('#modal-nova-pessoa .btn-close').click();
        } else {
            mostrarMensagem('error', 'Erro', data.error || 'Erro ao criar');
        }
    } catch (e) {
        mostrarMensagem('error', 'Erro', 'Erro de conexão');
    }
}

function abrirModalNovaClassificacao() {
    const container = document.getElementById('modals-container');
    const id = 'modal-nova-classificacao';
    container.innerHTML = `
    <div class="modal" tabindex="-1" id="${id}">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header"><h5 class="modal-title">Nova Classificação</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
          <div class="modal-body">
            <div class="mb-2"><label class="form-label">Descrição</label><input class="form-control" id="nova-class-descricao"></div>
            <div class="mb-2"><label class="form-label">Tipo</label><select class="form-select" id="nova-class-tipo"><option value="DESPESA">Despesa</option><option value="RECEITA">Receita</option></select></div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
            <button class="btn btn-primary" onclick="criarClassificacao()">Salvar</button>
          </div>
        </div>
      </div>
    </div>`;
    const m = new bootstrap.Modal(document.getElementById(id));
    m.show();
}

async function criarClassificacao() {
    try {
        const descricao = document.getElementById('nova-class-descricao').value.trim();
        const tipo = document.getElementById('nova-class-tipo').value;
        const response = await fetch('/gerenciar/classificacoes/criar/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
            body: JSON.stringify({ descricao, tipo })
        });
        const data = await response.json();
        if (data.success) {
            mostrarMensagem('success', 'Sucesso', 'Classificação criada com sucesso');
            document.querySelector('#modal-nova-classificacao .btn-close').click();
        } else {
            mostrarMensagem('error', 'Erro', data.error || 'Erro ao criar');
        }
    } catch (e) {
        mostrarMensagem('error', 'Erro', 'Erro de conexão');
    }
}

// ===== UTILITÁRIOS =====

function getCsrfToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}

function habilitarOrdenacao(tbodyId) {
    const tbody = document.getElementById(tbodyId);
    const thead = tbody && tbody.parentElement && tbody.parentElement.querySelector('thead');
    if (!thead) return;
    const headers = thead.querySelectorAll('th[data-sort]');
    headers.forEach((h, idx) => {
        h.style.cursor = 'pointer';
        h.addEventListener('click', () => {
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const asc = h.getAttribute('data-asc') !== 'true';
            rows.sort((a, b) => {
                const ta = a.children[idx].textContent.trim();
                const tb = b.children[idx].textContent.trim();
                const na = parseFloat(ta.replace(/[R$.,\s]/g, '').replace(',', '.'));
                const nb = parseFloat(tb.replace(/[R$.,\s]/g, '').replace(',', '.'));
                const va = isNaN(na) ? ta.toLowerCase() : na;
                const vb = isNaN(nb) ? tb.toLowerCase() : nb;
                if (va < vb) return asc ? -1 : 1;
                if (va > vb) return asc ? 1 : -1;
                return 0;
            });
            tbody.innerHTML = '';
            rows.forEach(r => tbody.appendChild(r));
            headers.forEach(x => x.removeAttribute('data-asc'));
            h.setAttribute('data-asc', asc ? 'true' : 'false');
        });
    });
}

async function alterarStatusMovimento(id, novoStatus) {
    try {
        mostrarLoading();
        const response = await fetch(`/gerenciar/movimentos/${id}/status/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ ativo: novoStatus })
        });
        const data = await response.json();
        if (data.success) {
            carregarMovimentos(paginaAtualMovimentos);
        } else {
            mostrarMensagem('error', 'Erro', data.error || 'Erro ao alterar status');
        }
    } catch (error) {
        mostrarMensagem('error', 'Erro', 'Erro de conexão');
    } finally {
        esconderLoading();
    }
}

async function alterarStatusParcela(id, novoStatus) {
    try {
        mostrarLoading();
        const response = await fetch(`/gerenciar/parcelas/${id}/status/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ ativo: novoStatus })
        });
        const data = await response.json();
        if (data.success) {
            carregarParcelas(paginaAtualParcelas);
        } else {
            mostrarMensagem('error', 'Erro', data.error || 'Erro ao alterar status');
        }
    } catch (error) {
        mostrarMensagem('error', 'Erro', 'Erro de conexão');
    } finally {
        esconderLoading();
    }
}
