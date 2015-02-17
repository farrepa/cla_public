from collections import Mapping, OrderedDict, defaultdict
from pprint import pformat
import sys

from cla_public.libs.money_interval import MoneyInterval
from cla_public.apps.checker.constants import NO, PASSPORTED_BENEFITS, YES
from cla_public.apps.checker.utils import nass, passported


class Payload(dict):
    """
    Base class for JSON data structure the means test API expects.
    """

    def update(self, other={}, **kwargs):
        """
        Recursively merge dicts into self
        """
        other.update(kwargs)
        for key, val in other.iteritems():
            if key == 'notes' and key in self and self[key] != val:
                self[key] = '{0}\n\n{1}'.format(self[key], val)
            elif isinstance(val, MoneyInterval):
                self[key] = self.get(key, MoneyInterval(0)) + val
            elif isinstance(val, Mapping):
                if key not in self:
                    self[key] = Payload()
                self[key].update(val)
            elif isinstance(val, list):
                self[key] = self.get(key, []) + val
            else:
                self[key] = val


class ConverterPayload(Payload):
    """
    Base class for a data structure which implicitly converts form data dicts
    into the means test API JSON data structure.
    """

    def __init__(self, form_data, session=None):
        super(ConverterPayload, self).__init__()
        self.update(self.convert(dict(form_data), session=session))

    def convert(self, form_data, session=None):
        """
        Convert form data dict into API JSON data structure
        """
        raise NotImplementedError


class Zeroable(object):

    def __init__(self, *args, **kwargs):
        zero = kwargs.pop('zero', False)
        init_dict = len(args) > 0 and args[0] or {}
        init_dict.update(kwargs)
        if zero:
            init_dict = self.zero()
        super(Zeroable, self).__init__(init_dict)


class ProblemPayload(ConverterPayload):

    def convert(self, form_data, session=None):
        category = form_data['categories']

        return {
            'category':
                'family' if category == 'violence' else category,

            'notes':
                u'User selected category: {0}'.format(category)
        }


class AboutYouPayload(ConverterPayload):

    def convert(self, form_data, session=None):
        yes = lambda field: form_data[field] == YES
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
                    'self_employed': val('is_self_employed')
                }}
        }

        if yes('have_partner') and not yes('in_dispute') and \
                yes('partner_is_self_employed'):
            payload['partner'] = {
                'income': {
                    'self_employed':
                        val('partner_is_self_employed')}}

        if yes('own_property'):
            if session:
                self.update(
                    PropertiesPayload(
                        session.get('PropertiesForm', {}),
                        session))
        else:
            self.update(
                PropertiesPayload(zero=True))

        return payload


class YourBenefitsPayload(ConverterPayload):

    def convert(self, form_data, session=None):
        is_selected = lambda ben: ben in form_data['benefits']
        benefits = {ben: is_selected(ben) for ben in PASSPORTED_BENEFITS}
        is_passported = passported(form_data['benefits'])

        payload = Payload({
            'specific_benefits':
                benefits,

            'on_passported_benefits':
                is_passported
        })

        if is_passported:
            payload.update(IncomePayload(zero=True))
            payload.update(OutgoingsPayload(zero=True))

        return payload


class PropertyPayload(ConverterPayload):

    def convert(self, form_data, session=None):
        val = lambda field: form_data.get(field)
        yes = lambda field: form_data[field] == YES
        no = lambda field: form_data[field] == NO

        return {
            'value':
                val('property_value'),

            'mortgage_left':
                val('mortgage_remaining'),

            'share':
                100 if no('other_shareholders') else None,

            'disputed':
                val('in_dispute'),

            'rent':
                MoneyInterval(val('rent_amount'))
                if yes('is_rented') else MoneyInterval(0),

            'main':
                val('is_main_home')
        }


class PropertiesPayload(Zeroable, ConverterPayload):

    def zero(self):
        return {'properties': [defaultdict(int)]}

    def convert(self, form_data, session=None):
        val = lambda field: form_data.get(field)
        properties = val('properties')
        total_mortgage = MoneyInterval(
            sum(prop.get('mortgage_payments', 0) for prop in properties))
        properties = map(PropertyPayload, properties)
        total_rent = sum(prop['rent'] for prop in properties)

        return {
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
                }}}


class SavingsPayload(ConverterPayload):

    def convert(self, form_data, session=None):
        val = lambda field: form_data.get(field, 0)

        return {
            'you': {
                'savings': {
                    'bank_balance':
                        val('savings'),

                    'investment_balance':
                        val('investments'),

                    'asset_balance':
                        val('valuables')
                }
            }
        }


class TaxCreditsPayload(ConverterPayload):

    def convert(self, form_data, session=None):
        val = lambda field: form_data.get(field)
        yes = lambda field: form_data[field] == YES

        benefits = val('benefits')

        payload = {
            'on_nass_benefits':
                nass(benefits),

            'you': {
                'income': {
                    'child_benefits':
                        MoneyInterval(val('child_benefit')),

                    'tax_credits':
                        MoneyInterval(val('child_tax_credit')),

                    'benefits':
                        MoneyInterval(val('total_other_benefit'))
                        if yes('other_benefits') else MoneyInterval(0)
                }}}

        if benefits:
            payload['notes'] = u'Other benefits:\n - {0}'.format(
                '\n - '.join(benefits))

        return payload


class IncomePayload(Zeroable, ConverterPayload):

    def zero(self):
        return {
            'your_income': defaultdict(int),
            'partner_income': defaultdict(int)
        }

    def convert(self, form_data, session=None):
        your = lambda field: form_data['your_income'].get(field)

        payload = {
            'you': {
                'income': {
                    'earnings':
                        MoneyInterval(your('earnings')),

                    'self_employment_drawings':
                        MoneyInterval(0),

                    'tax_credits':
                        MoneyInterval(your('working_tax_credit')),

                    'maintenance_received':
                        MoneyInterval(your('maintenance')),

                    'pension':
                        MoneyInterval(your('pension')),

                    'other_income':
                        MoneyInterval(your('other_income'))
                },
                'deductions': {
                    'income_tax':
                        MoneyInterval(your('income_tax')),

                    'national_insurance':
                        MoneyInterval(your('national_insurance'))
                }
            }
        }

        if 'partner_income' in form_data:
            partner = lambda field: form_data['partner_income'].get(field)

            payload.update({
                'partner': {
                    'income': {
                        'earnings':
                            MoneyInterval(partner('earnings')),

                        'tax_credits':
                            MoneyInterval(partner('working_tax_credit')),

                        'maintenance_received':
                            MoneyInterval(partner('maintenance')),

                        'pension':
                            MoneyInterval(partner('pension')),

                        'other_income':
                            MoneyInterval(partner('other_income'))
                    },
                    'deductions': {
                        'income_tax':
                            MoneyInterval(partner('income_tax')),

                        'national_insurance':
                            MoneyInterval(partner('national_insurance'))
                    }
                }
            })

        return payload


class OutgoingsPayload(Zeroable, ConverterPayload):

    def zero(self):
        return defaultdict(int)

    def convert(self, form_data, session=None):
        val = lambda field: form_data.get(field)

        return {
            'you': {
                'deductions': {
                    'rent':
                        MoneyInterval(val('rent')),

                    'maintenance':
                        MoneyInterval(val('maintenance')),

                    'criminal_legalaid_contributions':
                        val('income_contribution'),

                    'childcare':
                        MoneyInterval(val('childcare'))
                }
            }
        }


class SessionPayload(ConverterPayload):

    def convert(self, session_data, **kwargs):
        """
        Convert the form data stored in the session into a payload for the
        means test API
        """

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

        def payload_for(form):
            if form in session_data:
                class_name = '{0}Payload'.format(form.replace('Form', ''))
                class_ = getattr(sys.modules[__name__], class_name)
                return class_(session_data[form], session=session_data)
            return {}

        payload = Payload()

        for form in forms:
            payload.update(payload_for(form))

        return payload
