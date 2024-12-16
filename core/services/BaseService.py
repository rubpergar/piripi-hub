from flask import abort, flash, redirect, url_for, render_template


class BaseService:
    def __init__(self, repository):
        self.repository = repository

    def create(self, **kwargs):
        return self.repository.create(**kwargs)

    def count(self) -> int:
        return self.repository.count()

    def get_by_id(self, id):
        return self.repository.get_by_id(id)

    def get_or_404(self, id):
        return self.repository.get_or_404(id)
    
    def get_all(self):
        datasets = self.repository.get_all()
        if not datasets:
            abort(404, description="No datasets found")
        return datasets

    def update(self, id, **kwargs):
        return self.repository.update(id, **kwargs)

    def delete(self, id):
        return self.repository.delete(id)

    def handle_service_response(self, result, errors, success_url_redirect, success_msg, error_template, form):
        if result:
            flash(success_msg, 'success')
            return redirect(url_for(success_url_redirect))
        else:
            for error_field, error_messages in errors.items():
                for error_message in error_messages:
                    flash(f'{error_field}: {error_message}', 'error')
            return render_template(error_template, form=form)
    
    def handle_service_response2(self, result, errors, success_url_redirect, success_msg, error_template, form, id):
        if result:
            flash(success_msg, 'success')
        # Usa el dataset_id con url_for
            return redirect(url_for(success_url_redirect, dataset_id=id))
        else:
            for error_field, error_messages in errors.items():
                for error_message in error_messages:
                    flash(f'{error_field}: {error_message}', 'error')
        return render_template(error_template, form=form)
