"""Tarefas de inicialização que não devem bloquear a disponibilidade HTTP."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable


DatabaseInitializer = Callable[[], Awaitable[bool]]


def start_database_initialization(
    initializer: DatabaseInitializer,
    logger: logging.Logger,
) -> asyncio.Task[bool]:
    """Inicia a verificação/criação de tabelas sem atrasar o servidor HTTP.

    O portal estático e suas rotas podem ser atendidos durante a inicialização.
    O resultado continua registrado no log para que uma indisponibilidade do banco
    seja visível, sem transformar o cold start em erro de publicação.
    """

    task = asyncio.create_task(initializer(), name="marketmind-database-init")

    def report_result(completed_task: asyncio.Task[bool]) -> None:
        try:
            database_ready = completed_task.result()
        except asyncio.CancelledError:
            return
        except Exception:
            logger.exception("Falha inesperada ao inicializar o banco em segundo plano")
            return

        if database_ready:
            logger.info("Banco inicializado em segundo plano")
        else:
            logger.warning("Banco indisponível ou não configurado após o startup")

    task.add_done_callback(report_result)
    return task
