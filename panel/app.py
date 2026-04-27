import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from db.models import db, Denuncia, FollowUp
from notifier.email_sender import enviar_email_formal
from notifier.telegram_notifier import notificar_usuario
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.pbh_obras import resumo_regional
import config

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = config.FLASK_SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = config.DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    from ai.vereador_mapper import seed_vereadores_exemplo
    seed_vereadores_exemplo(app)

from notifier.scheduler import iniciar_scheduler
_scheduler = iniciar_scheduler(app)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logado"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if (
            request.form.get("usuario") == config.PANEL_USERNAME
            and request.form.get("senha") == config.PANEL_PASSWORD
        ):
            session["logado"] = True
            return redirect(url_for("painel"))
        flash("Usuário ou senha incorretos.", "erro")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def painel():
    status_filter = request.args.get("status", "aguardando_triagem")
    denuncias = (
        Denuncia.query
        .filter_by(status=status_filter)
        .order_by(Denuncia.criado_em.desc())
        .all()
    )
    contagens = {
        "aguardando_triagem": Denuncia.query.filter_by(status="aguardando_triagem").count(),
        "aprovada": Denuncia.query.filter_by(status="aprovada").count(),
        "publicada": Denuncia.query.filter_by(status="publicada").count(),
        "rejeitada": Denuncia.query.filter_by(status="rejeitada").count(),
    }
    return render_template("painel.html", denuncias=denuncias, status=status_filter, contagens=contagens)


@app.route("/denuncia/<int:denuncia_id>")
@login_required
def detalhe(denuncia_id):
    denuncia = Denuncia.query.get_or_404(denuncia_id)
    obras = {}
    if denuncia.regional:
        try:
            obras = resumo_regional(denuncia.regional, denuncia.categoria)
        except Exception:
            obras = {"total": 0, "obras": [], "fonte": "", "atualizado_em": "—"}
    return render_template("detalhe.html", denuncia=denuncia, obras=obras)


@app.route("/denuncia/<int:denuncia_id>/aprovar", methods=["POST"])
@login_required
def aprovar(denuncia_id):
    denuncia = Denuncia.query.get_or_404(denuncia_id)
    denuncia.status = "aprovada"
    denuncia.aprovada_em = datetime.utcnow()
    denuncia.moderador_notas = request.form.get("notas", "")
    # Update post text if moderator edited it
    if request.form.get("texto_post"):
        denuncia.texto_post_sugerido = request.form.get("texto_post")
    if request.form.get("minuta_email"):
        denuncia.minuta_email = request.form.get("minuta_email")
    db.session.commit()
    flash(f"Denúncia {denuncia.protocolo} aprovada.", "sucesso")
    return redirect(url_for("detalhe", denuncia_id=denuncia_id))


@app.route("/denuncia/<int:denuncia_id>/publicar", methods=["POST"])
@login_required
def publicar(denuncia_id):
    denuncia = Denuncia.query.get_or_404(denuncia_id)
    if denuncia.status != "aprovada":
        flash("Denúncia precisa estar aprovada antes de publicar.", "erro")
        return redirect(url_for("detalhe", denuncia_id=denuncia_id))

    link_post = request.form.get("link_post", "").strip()
    if not link_post:
        flash("Informe o link do post publicado.", "erro")
        return redirect(url_for("detalhe", denuncia_id=denuncia_id))

    denuncia.link_post = link_post
    denuncia.publicada_em = datetime.utcnow()
    denuncia.status = "publicada"

    ok_email = enviar_email_formal(denuncia)
    if ok_email:
        denuncia.email_enviado = True
        denuncia.email_enviado_em = datetime.utcnow()

    ok_tg = notificar_usuario(denuncia.telegram_user_id, denuncia.protocolo, link_post)
    if ok_tg:
        denuncia.telegram_notificado = True

    db.session.commit()

    if ok_email and ok_tg:
        flash(f"Publicada, e-mail enviado e usuário notificado — {denuncia.protocolo}", "sucesso")
    elif ok_email:
        flash(f"Publicada e e-mail enviado. Falha ao notificar usuário no Telegram.", "aviso")
    else:
        flash(f"Publicada. Erro no e-mail formal — verifique os logs.", "aviso")
    return redirect(url_for("detalhe", denuncia_id=denuncia_id))


@app.route("/denuncia/<int:denuncia_id>/rejeitar", methods=["POST"])
@login_required
def rejeitar(denuncia_id):
    denuncia = Denuncia.query.get_or_404(denuncia_id)
    denuncia.status = "rejeitada"
    denuncia.moderador_notas = request.form.get("motivo", "")
    db.session.commit()
    flash(f"Denúncia {denuncia.protocolo} rejeitada.", "info")
    return redirect(url_for("painel"))


@app.route("/denuncia/<int:denuncia_id>/registrar-resposta", methods=["POST"])
@login_required
def registrar_resposta(denuncia_id):
    denuncia = Denuncia.query.get_or_404(denuncia_id)
    denuncia.resposta_vereador = request.form.get("resposta")
    denuncia.resposta_em = datetime.utcnow()
    denuncia.classificacao_scorecard = request.form.get("classificacao_scorecard")
    if request.form.get("resolvida"):
        denuncia.resolvida_em = datetime.utcnow()
    db.session.commit()
    flash("Resposta registrada.", "sucesso")
    return redirect(url_for("detalhe", denuncia_id=denuncia_id))


@app.route("/scorecard")
@login_required
def scorecard():
    from sqlalchemy import func
    publicadas = Denuncia.query.filter_by(status="publicada").all()

    vereadores_stats = {}
    for d in publicadas:
        nome = d.vereador_nome or "Não identificado"
        if nome not in vereadores_stats:
            vereadores_stats[nome] = {
                "total": 0,
                "cobrou": 0,
                "respondeu_sem_acao": 0,
                "ignorou": 0,
                "pendente": 0,
            }
        vereadores_stats[nome]["total"] += 1
        sc = d.classificacao_scorecard
        if sc == "cobrou_prefeitura":
            vereadores_stats[nome]["cobrou"] += 1
        elif sc == "respondeu_sem_acao":
            vereadores_stats[nome]["respondeu_sem_acao"] += 1
        elif sc == "ignorou":
            vereadores_stats[nome]["ignorou"] += 1
        else:
            vereadores_stats[nome]["pendente"] += 1

    return render_template("scorecard.html", stats=vereadores_stats)


@app.route("/followups")
@login_required
def followups():
    pendentes = (
        FollowUp.query
        .filter_by(publicado=False)
        .order_by(FollowUp.criado_em.desc())
        .all()
    )
    return render_template("followups.html", followups=pendentes)


@app.route("/followup/<int:fu_id>/marcar-publicado", methods=["POST"])
@login_required
def marcar_followup_publicado(fu_id):
    fu = FollowUp.query.get_or_404(fu_id)
    fu.publicado = True
    db.session.commit()
    flash("Follow-up marcado como publicado.", "sucesso")
    return redirect(url_for("followups"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
