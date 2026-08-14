# Notas operacionais — modo gratuito

Em 14 de agosto de 2026, a verificação pública de `https://marketmind-l3kg.onrender.com/health` retornou `200` com banco conectado. As rotas públicas de alertas também responderam: `/alerts/status`, `/alerts/recent` e, após a correção publicada, `/alerts/preferences`.

O painel do Render exibiu que a criação de um Background Worker separado exige uma instância paga, com plano inicial de US$ 7 por mês. A operação gratuita não deve substituir o comando de inicialização do Web Service existente pelo comando `python -m services.alerts.alert_worker`; o processo contínuo precisa permanecer separado do serviço HTTP.

Para respeitar a decisão de não contratar serviço adicional, os alertas serão preparados para execução agendada e pontual. Essa modalidade não oferece monitoramento contínuo nem a mesma latência de um processo residente.

Como alternativa de agendamento, a documentação oficial do GitHub informa que execuções padrão em repositórios públicos são gratuitas. Para repositórios privados no plano GitHub Free, há 2.000 minutos mensais incluídos; sem método de pagamento, novas execuções são bloqueadas quando a franquia se esgota. Fonte: https://docs.github.com/billing/managing-billing-for-github-actions/about-billing-for-github-actions
