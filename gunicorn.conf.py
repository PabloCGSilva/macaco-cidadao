bind = "0.0.0.0:5000"
workers = 2                 # 2 × CPU + 1 para containers pequenos
worker_class = "sync"
timeout = 120               # tolerante para envio de e-mail SMTP
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
preload_app = True          # carrega app no master; workers forked ganham
                            # memória compartilhada (copy-on-write)
accesslog = "-"             # stdout para docker logs
errorlog = "-"
loglevel = "info"
forwarded_allow_ips = "*"   # necessário atrás de proxy reverso


def post_fork(server, worker):
    """
    Descarta o pool de conexões herdado do master após o fork.

    Com preload_app=True, o master cria o engine SQLAlchemy (e pode abrir
    conexões ao DB). Se os workers reutilizarem essas conexões herdadas,
    dois processos compartilham o mesmo file descriptor TCP → erros
    aleatórios ("SSL connection closed", "server closed the connection").

    db.engine.dispose() fecha os descritores no worker sem afetar o master.
    O worker abrirá conexões próprias na primeira requisição.

    Nota sobre o scheduler: BackgroundScheduler usa threads.  fork() copia
    apenas a thread principal → o scheduler continua rodando no master
    (processo árbitro do Gunicorn), que permanece vivo enquanto houver
    workers. Esse é o comportamento correto e intencional.
    """
    from panel.app import app
    with app.app_context():
        from db.models import db
        db.engine.dispose()
