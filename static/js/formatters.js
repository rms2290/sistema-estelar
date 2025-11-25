// Formatação automática de campos CNPJ, telefone, CPF e CEP
document.addEventListener('DOMContentLoaded', function() {
    
    // Função para formatar CNPJ
    function formatarCNPJ(valor) {
        // Remove tudo que não é número
        let numeros = valor.replace(/\D/g, '');
        
        // Limita a 14 dígitos
        numeros = numeros.substring(0, 14);
        
        // Aplica a máscara: 00.000.000/0000-00
        if (numeros.length <= 2) {
            return numeros;
        } else if (numeros.length <= 5) {
            return numeros.substring(0, 2) + '.' + numeros.substring(2);
        } else if (numeros.length <= 8) {
            return numeros.substring(0, 2) + '.' + numeros.substring(2, 5) + '.' + numeros.substring(5);
        } else if (numeros.length <= 12) {
            return numeros.substring(0, 2) + '.' + numeros.substring(2, 5) + '.' + numeros.substring(5, 8) + '/' + numeros.substring(8);
        } else {
            return numeros.substring(0, 2) + '.' + numeros.substring(2, 5) + '.' + numeros.substring(5, 8) + '/' + numeros.substring(8, 12) + '-' + numeros.substring(12);
        }
    }
    
    // Função para formatar telefone
    function formatarTelefone(valor) {
        // Remove tudo que não é número
        let numeros = valor.replace(/\D/g, '');
        
        // Limita a 11 dígitos
        numeros = numeros.substring(0, 11);
        
        // Aplica a máscara baseada no número de dígitos
        if (numeros.length <= 2) {
            return '(' + numeros;
        } else if (numeros.length <= 6) {
            return '(' + numeros.substring(0, 2) + ') ' + numeros.substring(2);
        } else if (numeros.length <= 10) {
            // Telefone fixo: (00) 0000-0000
            return '(' + numeros.substring(0, 2) + ') ' + numeros.substring(2, 6) + '-' + numeros.substring(6);
        } else {
            // Celular: (00) 00000-0000
            return '(' + numeros.substring(0, 2) + ') ' + numeros.substring(2, 7) + '-' + numeros.substring(7);
        }
    }
    
    // Função para formatar CPF
    function formatarCPF(valor) {
        let numeros = valor.replace(/\D/g, '');
        numeros = numeros.substring(0, 11);
        
        if (numeros.length <= 3) {
            return numeros;
        } else if (numeros.length <= 6) {
            return numeros.substring(0, 3) + '.' + numeros.substring(3);
        } else if (numeros.length <= 9) {
            return numeros.substring(0, 3) + '.' + numeros.substring(3, 6) + '.' + numeros.substring(6);
        } else {
            return numeros.substring(0, 3) + '.' + numeros.substring(3, 6) + '.' + numeros.substring(6, 9) + '-' + numeros.substring(9);
        }
    }
    
    // Função para formatar CEP
    function formatarCEP(valor) {
        let numeros = valor.replace(/\D/g, '');
        numeros = numeros.substring(0, 8);
        
        if (numeros.length <= 5) {
            return numeros;
        } else {
            return numeros.substring(0, 5) + '-' + numeros.substring(5);
        }
    }
    
    // Função para calcular a nova posição do cursor após formatação
    function calcularNovaPosicaoCursor(valorAntigo, valorNovo, posicaoAntiga) {
        // Conta quantos caracteres não numéricos foram adicionados antes da posição do cursor
        let caracteresAdicionados = 0;
        let posicaoNumerica = 0;
        
        for (let i = 0; i < posicaoAntiga && i < valorAntigo.length; i++) {
            if (/\d/.test(valorAntigo[i])) {
                posicaoNumerica++;
            }
        }
        
        // Encontra a posição correspondente no novo valor
        let novaPosicao = 0;
        let numerosContados = 0;
        
        for (let i = 0; i < valorNovo.length; i++) {
            if (/\d/.test(valorNovo[i])) {
                numerosContados++;
                if (numerosContados > posicaoNumerica) {
                    break;
                }
            }
            novaPosicao = i + 1;
        }
        
        return novaPosicao;
    }
    
    // Função para aplicar formatação em um campo
    function aplicarFormatacao(campo, tipo) {
        const valor = campo.value;
        let valorFormatado = '';
        
        if (tipo === 'cnpj') {
            valorFormatado = formatarCNPJ(valor);
        } else if (tipo === 'telefone') {
            valorFormatado = formatarTelefone(valor);
        } else if (tipo === 'cpf') {
            valorFormatado = formatarCPF(valor);
        } else if (tipo === 'cep') {
            valorFormatado = formatarCEP(valor);
        }
        
        // Só atualiza se o valor mudou para evitar problemas com o cursor
        if (valor !== valorFormatado) {
            const posicaoCursor = campo.selectionStart;
            const posicaoFinal = campo.selectionEnd;
            
            campo.value = valorFormatado;
            
            // Ajusta a posição do cursor
            if (posicaoCursor === posicaoFinal) {
                // Cursor simples
                const novaPosicao = calcularNovaPosicaoCursor(valor, valorFormatado, posicaoCursor);
                campo.setSelectionRange(novaPosicao, novaPosicao);
            } else {
                // Seleção de texto - manter a seleção no final
                const novaPosicao = calcularNovaPosicaoCursor(valor, valorFormatado, posicaoFinal);
                campo.setSelectionRange(novaPosicao, novaPosicao);
            }
        }
    }
    
    // Função para detectar o tipo de campo baseado no nome, id, placeholder ou data-format
    function detectarTipoCampo(campo) {
        // Verificar primeiro o atributo data-format (prioridade)
        if (campo.hasAttribute && campo.hasAttribute('data-format')) {
            const dataFormat = campo.getAttribute('data-format');
            if (dataFormat === 'cpf' || dataFormat === 'cnpj' || dataFormat === 'telefone' || dataFormat === 'cep' || dataFormat === 'cpf_cnpj') {
                return dataFormat;
            }
        }
        
        const nome = campo.name ? campo.name.toLowerCase() : '';
        const id = campo.id ? campo.id.toLowerCase() : '';
        const placeholder = campo.placeholder ? campo.placeholder.toLowerCase() : '';
        
        // Verificar CNPJ
        if (nome.includes('cnpj') || id.includes('cnpj') || placeholder.includes('cnpj')) {
            return 'cnpj';
        }
        
        // Verificar telefone
        if (nome.includes('telefone') || id.includes('telefone') || placeholder.includes('telefone')) {
            return 'telefone';
        }
        
        // Verificar CPF (verificar antes de cpf_cnpj para evitar conflito)
        if ((nome.includes('cpf') && !nome.includes('cnpj')) || (id.includes('cpf') && !id.includes('cnpj')) || (placeholder.includes('cpf') && !placeholder.includes('cnpj'))) {
            return 'cpf';
        }
        
        // Verificar CEP
        if (nome.includes('cep') || id.includes('cep') || placeholder.includes('cep')) {
            return 'cep';
        }
        
        // Verificar campos que podem ter CPF ou CNPJ (como proprietario_cpf_cnpj)
        if (nome.includes('cpf_cnpj') || id.includes('cpf_cnpj') || (placeholder.includes('cpf') && placeholder.includes('cnpj'))) {
            return 'cpf_cnpj'; // Tipo especial para campos que podem ter ambos
        }
        
        return null;
    }
    
    // Função para aplicar formatação a um campo específico
    function aplicarFormatacaoCampo(campo) {
        const tipo = detectarTipoCampo(campo);
        if (tipo) {
            // Aplicar formatação inicial se já tem valor
            if (campo.value) {
                if (tipo === 'cpf_cnpj') {
                    const valor = campo.value.replace(/\D/g, '');
                    const tipoFormatacao = valor.length <= 11 ? 'cpf' : 'cnpj';
                    aplicarFormatacao(campo, tipoFormatacao);
                } else {
                    aplicarFormatacao(campo, tipo);
                }
            }
            
            // Aplicar formatação durante a digitação
            campo.addEventListener('input', function(e) {
                // Evitar formatação durante operações de colar/desfazer
                if (e.inputType === 'insertFromPaste' || e.inputType === 'historyUndo' || e.inputType === 'historyRedo') {
                    return;
                }
                
                // Para campos CPF/CNPJ, redetectar o tipo baseado no valor atual
                let tipoFormatacao = tipo;
                if (tipo === 'cpf_cnpj') {
                    const valor = this.value.replace(/\D/g, '');
                    tipoFormatacao = valor.length <= 11 ? 'cpf' : 'cnpj';
                }
                
                aplicarFormatacao(this, tipoFormatacao);
            });
            
            // Aplicar formatação ao perder o foco
            campo.addEventListener('blur', function() {
                // Para campos CPF/CNPJ, redetectar o tipo baseado no valor atual
                let tipoFormatacao = tipo;
                if (tipo === 'cpf_cnpj') {
                    const valor = this.value.replace(/\D/g, '');
                    tipoFormatacao = valor.length <= 11 ? 'cpf' : 'cnpj';
                }
                
                aplicarFormatacao(this, tipoFormatacao);
            });
            
            // Permitir colar texto
            campo.addEventListener('paste', function(e) {
                setTimeout(() => {
                    // Para campos CPF/CNPJ, redetectar o tipo baseado no valor atual
                    let tipoFormatacao = tipo;
                    if (tipo === 'cpf_cnpj') {
                        const valor = this.value.replace(/\D/g, '');
                        tipoFormatacao = valor.length <= 11 ? 'cpf' : 'cnpj';
                    }
                    
                    aplicarFormatacao(this, tipoFormatacao);
                }, 10);
            });
        }
    }
    
    // Aplicar formatação a todos os campos de entrada
    function aplicarFormatacaoTodosCampos() {
        const todosCampos = document.querySelectorAll('input[type="text"], input[type="tel"]');
        todosCampos.forEach(function(campo) {
            aplicarFormatacaoCampo(campo);
        });
    }
    
    // Aplicar formatação inicial
    aplicarFormatacaoTodosCampos();
    
    // Observar mudanças no DOM para aplicar formatação a novos campos
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1) { // Element node
                    // Verificar se o próprio nó é um campo de entrada
                    if (node.tagName === 'INPUT' && (node.type === 'text' || node.type === 'tel')) {
                        aplicarFormatacaoCampo(node);
                    }
                    
                    // Verificar campos dentro do nó adicionado
                    const campos = node.querySelectorAll ? node.querySelectorAll('input[type="text"], input[type="tel"]') : [];
                    campos.forEach(function(campo) {
                        aplicarFormatacaoCampo(campo);
                    });
                }
            });
        });
    });
    
    // Iniciar observação de mudanças no DOM
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Aplicar formatação quando a página é carregada dinamicamente (AJAX)
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(aplicarFormatacaoTodosCampos, 100);
    });
    
    // Aplicar formatação após carregamento de conteúdo via AJAX
    window.addEventListener('load', function() {
        setTimeout(aplicarFormatacaoTodosCampos, 200);
    });
}); 