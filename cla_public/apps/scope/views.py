# -*- coding: utf-8 -*-
from cla_common.constants import DIAGNOSIS_SCOPE
from django.template.defaultfilters import striptags
from cla_public.apps.checker.views import HelpOrganisations
from cla_public.apps.scope import scope
from cla_public.apps.scope.api import diagnosis_api_client as api
from cla_public.libs.views import RequiresSession
from flask import views, render_template, current_app, url_for, \
    redirect


OUTCOME_URLS = {
    DIAGNOSIS_SCOPE.INSCOPE: '/scope/in-scope',
    DIAGNOSIS_SCOPE.INELIGIBLE: '/scope/ineligible',
    DIAGNOSIS_SCOPE.OUTOFSCOPE: '/result/face-to-face',
    DIAGNOSIS_SCOPE.CONTACT: '/contact',
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
            note = None
            if state == DIAGNOSIS_SCOPE.CONTACT and nodes:
                note = striptags(nodes[-1]['help_text'])
            api.save_category(
                api.get_category(response_json),
                note)

            category = api.get_category(response_json)
            if category == 'violence':
                category = 'domestic-violence'
            if category == 'benefits':
                category = 'welfare-benefits'

            outcome_url = OUTCOME_URLS[state]
            if state == 'INELIGIBLE':
                outcome_url = '/'.join([outcome_url, category])
            return redirect(outcome_url)

        def add_link(choice):
            choices_list = [choice['id']]
            if choices:
                choices_list.insert(0, choices.strip('/'))
            choice['url'] = url_for('.diagnosis',
                                    choices='/'.join(choices_list))
            return choice

        display_choices = map(add_link, response_json.get('choices', []))

        return render_template('scope/diagnosis.html',
                               choices=display_choices,
                               nodes=nodes)


class ScopeInScope(RequiresSession, views.MethodView):
    def get(self, *args, **kwargs):
        return render_template('scope/in-scope.html')


class ScopeIneligible(HelpOrganisations):
    _template = 'scope/ineligible.html'

