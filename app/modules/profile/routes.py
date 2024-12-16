from app.modules.auth.services import AuthenticationService
from app.modules.auth.models import User
from app.modules.dataset.models import DataSet
from flask import flash, render_template, redirect, url_for, request
from flask_login import login_required, current_user

from app import db
from app.modules.profile import profile_bp
from app.modules.profile.forms import UserProfileForm
from app.modules.profile.services import UserProfileService

# Routes for profile module


@profile_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    auth_service = AuthenticationService()
    profile = auth_service.get_authenticated_user_profile
    if not profile:
        return redirect(url_for("public.index"))

    form = UserProfileForm()
    if request.method == "POST":
        service = UserProfileService()
        result, errors = service.update_profile(current_user.profile.id, form)
        return service.handle_service_response(
            result,
            errors,
            "profile.edit_profile",
            "Profile updated successfully",
            "profile/edit.html",
            form,
        )

    return render_template("profile/edit.html", form=form)


@profile_bp.route("/profile/summary")
@login_required
def my_profile():
    page = request.args.get("page", 1, type=int)
    per_page = 5

    user_datasets_pagination = (
        db.session.query(DataSet)
        .filter(DataSet.user_id == current_user.id)
        .order_by(DataSet.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    total_datasets_count = (
        db.session.query(DataSet).filter(DataSet.user_id == current_user.id).count()
    )

    print(user_datasets_pagination.items)

    return render_template(
        "profile/summary.html",
        user_profile=current_user.profile,
        user=current_user,
        datasets=user_datasets_pagination.items,
        pagination=user_datasets_pagination,
        total_datasets=total_datasets_count,
    )


@profile_bp.route("/profile/<int:user_id>")
def view_profile(user_id):
    user = db.session.query(User).filter_by(id=user_id).first_or_404()

    if current_user.is_authenticated:
        if not user.profile.public_data and current_user.id != user_id:
            flash("User data is not public", "error")
            dataset = (
                db.session.query(DataSet).filter(DataSet.user_id == user_id).first()
            )
            if not dataset:
                return redirect(url_for("public.index"))
            else:
                return render_template("dataset/view_dataset.html", dataset=dataset)

    else:
        if not user.profile.public_data:
            flash("User data is not public", "error")
            dataset = (
                db.session.query(DataSet).filter(DataSet.user_id == user_id).first()
            )
            if not dataset:
                return redirect(url_for("public.index"))
            else:
                return render_template("dataset/view_dataset.html", dataset=dataset)

    page = request.args.get("page", 1, type=int)
    per_page = 5

    user_datasets_pagination = (
        db.session.query(DataSet)
        .filter(DataSet.user_id == user_id)
        .order_by(DataSet.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    total_datasets_count = (
        db.session.query(DataSet).filter(DataSet.user_id == user_id).count()
    )

    return render_template(
        "profile/summary.html",
        user_profile=user.profile,
        user=user,
        datasets=user_datasets_pagination.items,
        pagination=user_datasets_pagination,
        total_datasets=total_datasets_count,
    )
