# -*- coding: utf-8 -*-
"Means Test class"

from collections import Mapping
from copy import deepcopy
import logging
import sys

from flask import current_app
from slumber.exceptions import SlumberBaseException
from requests.exceptions import ConnectionError, Timeout

from cla_public.apps.checker.api import get_api_connection
from cla_public.apps.checker.constants import YES, NO, PASSPORTED_BENEFITS
from cla_public.apps.checker.utils import nass, passported
from cla_public.libs.money_interval import MoneyInterval, to_amount
from cla_public.libs.utils import classproperty


log = logging.getLogger(__name__)


def mi(field, val):
    amount = '%s-per_interval_value' % field
    period = '%s-interval_period' % field
    return {
        'per_interval_value': val(amount),
        'interval_period': val(period)
    }


def recursive_update(orig, other):
    for key, val in other.iteritems():

        if key not in orig:
            if isinstance(val, Mapping):
                orig[key] = deepcopy(val)
            else:
                orig[key] = val

        elif orig[key] == val:
            continue

        elif key == 'notes' and orig[key] != val:
            orig[key] = '{0}\n\n{1}'.format(orig[key], val)

        elif isinstance(val, Mapping):
            if MoneyInterval.is_money_interval(val):
                orig[key] = MoneyInterval(val)
            elif val != {}:
                if not isinstance(orig[key], Mapping):
                    orig[key] = {}
                orig[key] = recursive_update(orig[key], val)

        elif isinstance(val, list):
            orig[key] = val

        else:
            orig[key] = val

    return orig


class ProblemPayload(dict):

    def __init__(self, form_data={}, session=None):
        super(ProblemPayload, self).__init__()

        category = form_data['categories']

        self.update({
            'category':
                'family' if category == 'violence' else category,

            'notes':
                u'User selected category: {0}'.format(category)
        })


class AboutYouPayload(dict):

    def __init__(self, form_data={}, session=None):
        super(AboutYouPayload, self).__init__()

        yes = lambda field: form_data.get(field) == YES
        val = lambda field: form_data.get(field)

        payload = {
            'dependants_young':
                val('num_children') if yes('have_children') else 0,

            'dependants_old':
                val('num_dependants') if yes('have_dependants') else 0,

            'is_you_or_your_partner_over_60':
                val('aged_60_or_over'),

            'has_partner':
                val('have_partner'),

            'you': {
                'income': {
                    'self_employed': val('is_self_employed')}}}

        if yes('have_partner') and not yes('in_dispute') and \
                yes('partner_is_self_employed'):
            payload['partner'] = {
                'income': {
                    'self_employed':
                        val('partner_is_self_employed')}}

        if yes('own_property'):
            payload = recursive_update(
                payload,
                PropertiesPayload(session=session))
        else:
            payload = recursive_update(payload, PropertiesPayload.default)

        if yes('have_savings') or yes('have_valuables'):
            payload = recursive_update(
                payload,
                SavingsPayload(session=session))
        else:
            payload = recursive_update(payload, SavingsPayload.default)

        payload = recursive_update(payload, IncomePayload(session=session))
        payload = recursive_update(payload, OutgoingsPayload(session=session))

        self.update(payload)


class YourBenefitsPayload(dict):

    def __init__(self, form_data={}, session=None):
        super(YourBenefitsPayload, self).__init__()

        is_selected = lambda ben: ben in form_data['benefits']
        benefits = {ben: is_selected(ben) for ben in PASSPORTED_BENEFITS}
        is_passported = passported(form_data['benefits'])

        payload = {
            'specific_benefits':
                benefits,

            'on_passported_benefits':
                is_passported
        }

        if is_passported:
            payload = recursive_update(payload, IncomePayload.default)
            payload = recursive_update(payload, OutgoingsPayload.default)

        self.update(payload)


class PropertyPayload(dict):

    def __init__(self, form_data={}, session=None):
        super(PropertyPayload, self).__init__()

        val = lambda field: form_data.get(field)
        yes = lambda field: form_data.get(field) == YES
        no = lambda field: form_data.get(field) == NO

        self.update({
            'value':
                to_amount(val('property_value')),

            'mortgage_left':
                to_amount(val('mortgage_remaining')),

            'share':
                100 if no('other_shareholders') else None,

            'disputed':
                val('in_dispute'),

            'rent':
                MoneyInterval(mi('rent_amount', val))
                if yes('is_rented') else MoneyInterval(0),

            'main':
                val('is_main_home')
        })


class PropertiesPayload(dict):

    @classproperty
    def default(cls):
        return {
            'property_set': [],
            'you': {
                'deductions': {
                    'mortgage': MoneyInterval(0)
                },
                'income': {
                    'other_income': MoneyInterval(0)
                }
            }
        }

    def __init__(self, form_data={}, session=None):
        super(PropertiesPayload, self).__init__()

        def prop(index):
            if 'properties-%d-is_main_home' % index not in form_data:
                return None
            prop_data = dict([
                (key[13:], val) for key, val in form_data.items()
                if key.startswith('properties-%d-' % index)])
            return PropertyPayload(prop_data)

        properties = filter(None, map(prop, range(3)))
        if not properties and session.owns_property:
            properties.append(PropertyPayload())

        def mortgage(index):
            return MoneyInterval(
                form_data.get('properties-%d-mortgage_payments' % index, 0))

        total_mortgage = sum(map(mortgage, range(len(properties))))

        total_rent = sum(p['rent'] for p in properties)

        self.update({
            'property_set':
                properties,

            'you': {
                'income': {
                    'other_income':
                        total_rent
                },
                'deductions': {
                    'mortgage':
                        total_mortgage
                }}})


class SavingsPayload(dict):

    @classproperty
    def default(cls):
        return {
            'you': {
                'savings': {
                    'bank_balance': 0,
                    'investment_balance': 0,
                    'asset_balance': 0
                }
            }
        }

    def __init__(self, form_data={}, session=None):
        super(SavingsPayload, self).__init__()

        savings = None if session.has_savings else 0
        valuables = None if session.has_valuables else 0

        val = lambda field, default=0: form_data.get(field, default)

        self.update({
            'you': {
                'savings': {
                    'bank_balance':
                        to_amount(val('savings', savings)),

                    'investment_balance':
                        to_amount(val('investments', savings)),

                    'asset_balance':
                        to_amount(val('valuables', valuables))
                }
            }
        })


class TaxCreditsPayload(dict):

    def __init__(self, form_data={}, session=None):
        super(TaxCreditsPayload, self).__init__()

        val = lambda field: form_data.get(field)
        yes = lambda field: form_data[field] == YES

        benefits = val('benefits')

        payload = {
            'on_nass_benefits':
                nass(benefits),

            'you': {
                'income': {
                    'child_benefits':
                        MoneyInterval(mi('child_benefit', val)),

                    'tax_credits':
                        MoneyInterval(mi('child_tax_credit', val)),

                    'benefits':
                        MoneyInterval(mi('total_other_benefit' ,val))
                        if yes('other_benefits') else MoneyInterval(0)
                }}}

        if benefits:
            payload['notes'] = u'Other benefits:\n - {0}'.format(
                '\n - '.join(benefits))

        self.update(payload)


class IncomePayload(dict):

    @classproperty
    def default(cls):
        income = lambda: {
            'income': {
                'earnings': MoneyInterval(0),
                'tax_credits': MoneyInterval(0),
                'other_income': MoneyInterval(0),
                'self_employment_drawings': MoneyInterval(0),
                'maintenance_received': MoneyInterval(0),
                'pension': MoneyInterval(0)
            },
            'deductions': {
                'income_tax': MoneyInterval(0),
                'national_insurance': MoneyInterval(0)
            }
        }

        return {
            'you': income(),
            'partner': income()
        }

    def __init__(self, form_data={}, session=None):
        super(IncomePayload, self).__init__()

        def income(person, prefix_, self_employed=False):
            prefix = lambda field: '{0}-{1}'.format(prefix_, field)
            val = lambda field: form_data.get(prefix(field))
            payload = {
                person: {
                    'income': {
                        'earnings':
                            MoneyInterval(mi('earnings', val)),

                        'self_employment_drawings':
                            MoneyInterval(0),

                        'tax_credits':
                            MoneyInterval(mi('working_tax_credit', val)),

                        'maintenance_received':
                            MoneyInterval(mi('maintenance', val)),

                        'pension':
                            MoneyInterval(mi('pension', val)),

                        'other_income':
                            MoneyInterval(mi('other_income', val)),

                    },
                    'deductions': {
                        'income_tax':
                            MoneyInterval(mi('income_tax', val)),

                        'national_insurance':
                            MoneyInterval(mi('national_insurance', val))
                    }
                }
            }

            if self_employed:
                payload[person]['income']['earnings'] = MoneyInterval(0)
                payload[person]['income']['self_employment_drawings'] = \
                    MoneyInterval(mi('earnings', val))

            return payload

        payload = income(
            'you',
            'your_income',
            session.is_self_employed and not session.is_employed)

        child_tax_credit = session.get('TaxCreditsForm', {}).get(
            'child_tax_credit', MoneyInterval(0))
        payload['you']['income']['tax_credits'] += child_tax_credit

        if session.owns_property:
            rents = [MoneyInterval(p['rent_amount']) for p in session.get(
                'PropertiesForm', {}).get('properties', [])]
            total_rent = sum(rents)
            payload['you']['income']['other_income'] += total_rent

        if session.has_partner:
            partner_payload = income(
                'partner',
                'partner_income',
                session.partner_is_self_employed and not
                session.partner_is_employed)
            payload = recursive_update(payload, partner_payload)

        self.update(payload)


class OutgoingsPayload(dict):

    @classproperty
    def default(cls):
        return {
            'you': {
                'deductions': {
                    'rent': MoneyInterval(0),
                    'maintenance': MoneyInterval(0),
                    'childcare': MoneyInterval(0),
                    'criminal_legalaid_contributions': 0
                }
            }
        }

    def __init__(self, form_data={}, session=None):
        super(OutgoingsPayload, self).__init__()

        val = lambda field: form_data.get(field)
        self.update({
            'you': {
                'deductions': {
                    'rent':
                        MoneyInterval(mi('rent', val)),

                    'maintenance':
                        MoneyInterval(mi('maintenance', val)),

                    'criminal_legalaid_contributions':
                        to_amount(val('income_contribution')),

                    'childcare':
                        MoneyInterval(mi('childcare', val))
                }
            }
        })


class MeansTestError(Exception):
    pass


class MeansTest(dict):
    """
    Encapsulates the means test data and saving to and querying the API
    """

    def __init__(self, *args, **kwargs):
        super(MeansTest, self).__init__(*args, **kwargs)

        self.reference = None

        def zero_finances():
            return {
                'income': {
                    'earnings': MoneyInterval(0),
                    'benefits': MoneyInterval(0),
                    'tax_credits': MoneyInterval(0),
                    'child_benefits': MoneyInterval(0),
                    'other_income': MoneyInterval(0),
                    'self_employment_drawings': MoneyInterval(0),
                    'maintenance_received': MoneyInterval(0),
                    'pension': MoneyInterval(0),
                    'total': 0,
                    'self_employed': NO
                },
                'savings': {
                    'credit_balance': 0,
                    'investment_balance': 0,
                    'asset_balance': 0,
                    'bank_balance': 0,
                    'total': 0
                },
                'deductions': {
                    'income_tax': MoneyInterval(0),
                    'mortgage': MoneyInterval(0),
                    'childcare': MoneyInterval(0),
                    'rent': MoneyInterval(0),
                    'maintenance': MoneyInterval(0),
                    'national_insurance': MoneyInterval(0),
                    'criminal_legalaid_contributions': 0
                }
            }

        self.update({
            'you': zero_finances(),
            'partner': zero_finances(),
            'dependants_young': 0,
            'dependants_old': 0,
            'on_passported_benefits': NO,
            'on_nass_benefits': NO,
            'specific_benefits': {}
        })

    def update(self, other={}, **kwargs):
        """
        Recursively merge dicts into self
        """
        other.update(kwargs)
        recursive_update(self, other)

    def update_from_form(self, form, form_data, session=None):
        payload_class = '{0}Payload'.format(form.replace('Form', ''))
        payload = getattr(sys.modules[__name__], payload_class)
        self.update(payload(form_data, session=session))

    def update_from_session(self, session):

        forms = [
            'ProblemForm',
            'AboutYouForm',
            'YourBenefitsForm',
            'PropertiesForm',
            'SavingsForm',
            'TaxCreditsForm',
            'IncomeForm',
            'OutgoingsForm'
        ]

        for form in forms:
            if form in session:
                self.update_from_form(form, session[form], session)

    def save(self):
        sentry = getattr(current_app, 'sentry', None)
        try:
            backend = get_api_connection()

            if self.reference:
                backend.eligibility_check(self.reference).patch(self)
            else:
                response = backend.eligibility_check.post(self)
                self.reference = response['reference']
        except (ConnectionError, Timeout, SlumberBaseException) as e:
            if sentry:
                sentry.captureException()
            else:
                log.exception('Failed saving eligibility check')
            raise MeansTestError()

    def is_eligible(self):
        sentry = getattr(current_app, 'sentry', None)
        try:
            backend = get_api_connection()

            if self.reference:
                api = backend.eligibility_check(self.reference).is_eligible()
                response = api.post({})
                return response.get('is_eligible')
        except (ConnectionError, Timeout, SlumberBaseException) as e:
            if sentry:
                sentry.captureException()
            else:
                log.exception('Failed testing eligibility')
            raise MeansTestError()