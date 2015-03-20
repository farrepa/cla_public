# -*- coding: utf-8 -*-
"Scope diagnosis views"

from flask import redirect, render_template, session, url_for

from cla_public.apps.scope import scope
from cla_public.apps.scope.nlp import DiagnosisError, guess_category
from cla_public.apps.scope.forms import ScopeForm


@scope.route('/scope', methods=['GET', 'POST'])
def diagnosis():
    form = ScopeForm()

    diagnosis_error = False
    if form.validate_on_submit():
        try:
            session['category'] = guess_category(form.problem.data)
        except DiagnosisError:
            diagnosis_error = True
        else:
            return redirect(url_for('.confirm'))

    return render_template('scope.html', form=form, error=diagnosis_error)


@scope.route('/scope/confirm')
def confirm():
    return render_template('scope_confirm.html')
