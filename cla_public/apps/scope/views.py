# -*- coding: utf-8 -*-
import re
from cla_common.constants import DIAGNOSIS_SCOPE
from cla_public.apps.checker.views import HelpOrganisations
from cla_public.apps.scope import scope
from cla_public.apps.scope.api import diagnosis_api_client as api
from cla_public.libs.views import RequiresSession
from flask import views, render_template, current_app, url_for, \
    redirect, session


OUTCOME_URLS = {
    DIAGNOSIS_SCOPE.INSCOPE:    '/about',
    DIAGNOSIS_SCOPE.INELIGIBLE: '/scope/refer',
    DIAGNOSIS_SCOPE.OUTOFSCOPE: '/scope/refer/legal-adviser',
    DIAGNOSIS_SCOPE.MEDIATION:  '/scope/refer/mediation',
    DIAGNOSIS_SCOPE.CONTACT:    '/contact',
}


@scope.after_request
def add_header(response):
    """
    Add no-cache headers
    """
    response.headers['Cache-Control'] = \
        'no-cache, must-revalidate, no-store, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response


class ScopeDiagnosis(RequiresSession, views.MethodView):
    def get(self, choices='', *args, **kwargs):
        api.create_diagnosis()

        response = api.move([c for c in choices.strip('/').split('/') if c])

        try:
            response_json = response.json()
        except ValueError:
            if current_app.config['DEBUG']:
                return response.text
            raise

        state = response_json.get('state')
        nodes = response_json.get('nodes', [])

        if state and state != DIAGNOSIS_SCOPE.UNKNOWN:
            api.save(response_json)

            outcome_url = OUTCOME_URLS[state]
            if state == DIAGNOSIS_SCOPE.INELIGIBLE:
                outcome_url = '%s/%s' % (
                    outcome_url,
                    session.checker.category_slug)
            elif state == DIAGNOSIS_SCOPE.OUTOFSCOPE:
                outcome_url = '%s?category=%s' % (
                    outcome_url,
                    session.checker.category)
            return redirect(outcome_url)

        def add_link(choice):
            choices_list = [choice['id']]
            if choices:
                choices_list.insert(0, choices.strip('/'))
            choice['url'] = url_for('.diagnosis',
                                    choices='/'.join(choices_list))
            return choice

        display_choices = map(add_link, response_json.get('choices', []))

        # Start HACK for user testing.
        # TODO properly if users confirm the need

        IN_SCOPE = ['Debt', 'Domestic abuse', 'Discrimination', 'Education',
            'Employment', 'Family', 'Housing', 'Immigration', 'Welfare benefits']

        def in_scope(category):
            return re.sub('<[^<]+?>', '', category['label']) in IN_SCOPE
        def out_of_scope(category):
            return re.sub('<[^<]+?>', '', category['label']) not in IN_SCOPE

        in_scope_choices = filter(in_scope, display_choices)
        out_of_scope_choices = filter(out_of_scope, display_choices)

        # End HACK

        return render_template('scope/diagnosis.html',
                               in_scope_choices=in_scope_choices,
                               out_of_scope_choices=out_of_scope_choices,
                               choices=display_choices,
                               nodes=nodes)


class ScopeIneligible(HelpOrganisations):
    _template = 'scope/ineligible.html'


class ScopeMediation(RequiresSession, views.MethodView):
    def get(self):
        return render_template('scope/mediation.html')
