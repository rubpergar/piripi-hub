from flask import render_template, redirect, url_for, request, flash, current_app
from flask_login import current_user, login_user, logout_user
from app import mail

from app.modules.auth import auth_bp
from app.modules.auth.forms import SignupForm, LoginForm, PasswordRecoveryForm
from app.modules.auth.services import AuthenticationService
from app.modules.profile.services import UserProfileService
from flask_mail import Message
from app.modules.auth.models import User
from werkzeug.security import generate_password_hash

from itsdangerous import URLSafeTimedSerializer as Serializer
from app import db

authentication_service = AuthenticationService()
user_profile_service = UserProfileService()


@auth_bp.route("/signup/", methods=["GET", "POST"])
def show_signup_form():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data
        if not authentication_service.is_email_available(email):
            return render_template(
                "auth/signup_form.html", form=form, error=f"Email {email} in use"
            )

        try:
            user = authentication_service.create_with_profile(**form.data)
        except Exception as exc:
            return render_template(
                "auth/signup_form.html", form=form, error=f"Error creating user: {exc}"
            )

        # Log user
        login_user(user, remember=True)
        return redirect(url_for("public.index"))

    return render_template("auth/signup_form.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        if authentication_service.login(form.email.data, form.password.data):
            return redirect(url_for("public.index"))

        return render_template(
            "auth/login_form.html", form=form, error="Invalid credentials"
        )

    return render_template("auth/login_form.html", form=form)


@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("public.index"))


def generate_reset_token(email):
    s = Serializer(current_app.config["SECRET_KEY"])
    return s.dumps({"email": email})


def verify_reset_token(token):
    s = Serializer(current_app.config["SECRET_KEY"])
    try:
        data = s.loads(token, max_age=600)
    except Exception:
        return None
    return data.get("email")


def send_reset_email(user_email):
    token = generate_reset_token(user_email)
    reset_url = url_for("auth.reset_password", token=token, _external=True)

    msg = Message("Password Reset Request", recipients=[user_email])
    msg.body = f"Click in the link to reset your password: {reset_url}"

    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error al enviar el correo: {e}")


authentication_service = AuthenticationService()
user_profile_service = UserProfileService()


@auth_bp.route("/recover_password", methods=["GET", "POST"])
def recover_password():
    form = PasswordRecoveryForm()

    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("No existe una cuenta asociada con ese correo", "error")
            return render_template("auth/recover_password_form.html", form=form)

        try:
            token = generate_reset_token(email)
            reset_url = url_for("auth.reset_password", token=token, _external=True)

            msg = Message(
                "Recupera tu contraseña",
                recipients=[email],
                body=f"Haz clic en el siguiente enlace para restablecer tu contraseña: {reset_url}",
            )
            mail.send(msg)
            flash(
                "Mira tu correo para restablecer la contraseña y sigue las instrucciones.",
                "success",
            )
            return redirect(url_for("auth.password_recovery_success"))

        except Exception as e:
            flash(f"Error al enviar el correo: {e}", "error")
            return render_template("auth/recover_password_form.html", form=form)

    return render_template("auth/recover_password_form.html", form=form)


@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        flash("El token es inválido o ha expirado", "error")
        return redirect(url_for("auth.recover_password"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Usuario no encontrado", "error")
        return redirect(url_for("auth.recover_password"))

    if request.method == "POST":
        new_password = request.form["password"]
        if not new_password:
            flash("La contraseña no puede estar vacía.", "error")
            return render_template("auth/reset_password.html", token=token)

        user.password = generate_password_hash(new_password)
        db.session.commit()
        flash("Tu contraseña ha sido actualizada con éxito.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)
