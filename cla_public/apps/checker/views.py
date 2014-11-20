# -*- coding: utf-8 -*-
"Checker views"

from collections import namedtuple
import logging

from flask import abort, current_app, render_template, redirect, request, \
    session, url_for

from cla_public.apps.checker import checker
from cla_public.apps.checker.api import post_to_case_api, \
    post_to_eligibility_check_api, get_organisation_list
from cla_public.apps.checker.constants import RESULT_OPTIONS, CATEGORIES, ORGANISATION_CATEGORY_MAPPING
from cla_public.apps.checker.decorators import form_view, override_session_vars
from cla_public.apps.checker.forms import AboutYouForm, YourBenefitsForm, \
    ProblemForm, PropertiesForm, SavingsForm, TaxCreditsForm, income_form, \
    OutgoingsForm, ApplicationForm


log = logging.getLogger(__name__)


def proceed(next_step, **kwargs):
    return redirect(url_for('.{0}'.format(next_step), **kwargs))


def outcome(outcome):
    return proceed('result', outcome=outcome)


@checker.route('/problem', methods=['GET', 'POST'])
@form_view(ProblemForm, 'problem.html')
def problem(user):

    if user.needs_face_to_face:
        return outcome('face-to-face')

    return proceed('about')


@checker.route('/about', methods=['GET', 'POST'])
@form_view(AboutYouForm, 'about.html')
def about(user):

    next_step = 'income'

    if user.has_savings:
        next_step = 'savings'

    if user.owns_property:
        next_step = 'property'

    if user.is_on_benefits:
        next_step = 'benefits'

    return proceed(next_step)


@checker.route('/benefits', methods=['GET', 'POST'])
@form_view(YourBenefitsForm, 'benefits.html')
def benefits(user):

    if user.is_on_passported_benefits:
        return outcome('eligible')

    next_step = 'income'

    if user.has_tax_credits:
        next_step = 'benefits_tax_credits'

    if user.has_savings:
        next_step = 'savings'

    if user.owns_property:
        next_step = 'property'

    return proceed(next_step)


@checker.route('/property', methods=['GET', 'POST'])
def property():
    if current_app.config.get('DEBUG'):
        override_session_vars()

    form = PropertiesForm(request.form, session)
    if form.is_submitted():
        # Add new property button clicked
        # submit the form but don't validate
        if 'add-property' in request.form:
            if len(form.properties.entries) < form.properties.max_entries:
                form.properties.append_entry()
        # Remove property button clicked
        # Remove the item from the properties list
        # index passed as button value
        elif 'remove-property' in request.form:
            index = int(request.form['remove-property'])
            form.properties.remove(index)
        # Do normal validation on submit
        elif form.validate():
            next_step = 'income'

            if session.has_tax_credits:
                next_step = 'benefits_tax_credits'

            if session.has_savings:
                next_step = 'savings'

            return proceed(next_step)

    return render_template('property.html', form=form)


@checker.route('/savings', methods=['GET', 'POST'])
@form_view(SavingsForm, 'savings.html')
def savings(user):
    next_step = 'income'

    if user.has_tax_credits:
        next_step = 'benefits_tax_credits'

    return proceed(next_step)


@checker.route('/benefits-tax-credits', methods=['GET', 'POST'])
@form_view(TaxCreditsForm, 'benefits-tax-credits.html')
def benefits_tax_credits(user):
    return proceed('income')


@checker.route('/income', methods=['GET', 'POST'])
@form_view(income_form, 'income.html')
def income(user):
    return proceed('outgoings')


@checker.route('/outgoings', methods=['GET', 'POST'])
@form_view(OutgoingsForm, 'outgoings.html')
def outgoings(user):
    return outcome('eligible')


@checker.route('/result/<outcome>', methods=['GET', 'POST'])
def result(outcome):
    "Display the outcome of the means test"

    valid_outcomes = (result for (result, _) in RESULT_OPTIONS)
    if outcome not in valid_outcomes:
        abort(404)

    form = ApplicationForm()
    if form.validate_on_submit():
        notes = session.get('notes', {})
        notes['User problem'] = form.extra_notes.data

        class Notes(object):
            def api_payload(self):
                return {'notes': '\n\n'.join(
                    '{0}:\n {1}'.format(k, v) for k, v in notes.items())}
        post_to_eligibility_check_api(Notes())
        post_to_case_api(form)
        return redirect(url_for('.result', outcome='confirmation'))

    organisations = []
    if outcome == 'ineligible':
        category_name = (name for field, name, description in CATEGORIES if field == session.category).next()
        category_name = ORGANISATION_CATEGORY_MAPPING.get(category_name, category_name)
        organisations = get_organisation_list(article_category__name=category_name)

    return render_template(
        'result/%s.html' % outcome, form=form, organisations=organisations)
