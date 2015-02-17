import json
import os
import unittest

from cla_public.libs.api import *


class TestApiPayloads(unittest.TestCase):

    session = None

    def setUp(self):
        if not self.session:
            self.load_session()

    def load_session(self):
        filename = os.path.join(os.path.dirname(__file__), 'test_session.json')
        with open(filename) as data:
            self.session = json.load(data)

    def test_problem_form(self):
        converted = ProblemPayload(self.session['ProblemForm'])
        self.assertEqual(converted['category'], 'debt')
        self.assertEqual(converted['notes'], 'User selected category: debt')

    def test_about_you_form(self):
        converted = AboutYouPayload(self.session['AboutYouForm'])
        self.assertEqual(1, converted['dependants_young'])
        self.assertEqual(0, converted['dependants_old'])
        self.assertEqual(NO, converted['is_you_or_your_partner_over_60'])
        self.assertEqual(YES, converted['has_partner'])
        self.assertEqual(YES, converted['you']['income']['self_employed'])
        self.assertEqual(YES, converted['partner']['income']['self_employed'])

    def test_your_benefits_form(self):
        converted = YourBenefitsPayload(self.session['YourBenefitsForm'])
        self.assertFalse(converted['specific_benefits']['pension_credit'])
        self.assertFalse(converted['specific_benefits']['job_seekers_allowance'])
        self.assertFalse(converted['specific_benefits']['employment_support'])
        self.assertFalse(converted['specific_benefits']['universal_credit'])
        self.assertFalse(converted['specific_benefits']['income_support'])
        self.assertEqual(False, converted['on_passported_benefits'])

    def test_properties_form(self):
        converted = PropertiesPayload(self.session['PropertiesForm'])
        other_income = converted['you']['income']['other_income']
        self.assertEqual(0, other_income.amount)
        self.assertEqual('per_month', other_income.interval)
        mortgage = converted['you']['deductions']['mortgage']
        self.assertEqual(80000, mortgage.amount)
        property_one = converted['property_set'][0]
        self.assertEqual(10000000, property_one['value'])
        self.assertEqual(8000000, property_one['mortgage_left'])
        self.assertEqual(100, property_one['share'])
        self.assertEqual(NO, property_one['disputed'])
        self.assertEqual(0, property_one['rent'].amount)
        self.assertEqual(YES, property_one['main'])

    def test_savings_form(self):
        converted = SavingsPayload(self.session['SavingsForm'])
        self.assertEqual(500000, converted['you']['savings']['bank_balance'])
        self.assertEqual(0, converted['you']['savings']['investment_balance'])
        self.assertEqual(70000, converted['you']['savings']['asset_balance'])

    def test_tax_credits_form(self):
        converted = TaxCreditsPayload(self.session['TaxCreditsForm'])
        self.assertEqual(False, converted['on_nass_benefits'])
        self.assertEqual(0, converted['you']['income']['child_benefits'].amount)
        self.assertEqual(0, converted['you']['income']['tax_credits'].amount)
        self.assertEqual(0, converted['you']['income']['benefits'].amount)
        self.assertEqual(u'Other benefits:\n - housing', converted['notes'])

    def test_income_form(self):
        converted = IncomePayload(self.session['IncomeForm'])
        your = converted['you']['income']
        self.assertEqual(150000, your['earnings'].amount)
        self.assertEqual(0, your['tax_credits'].amount)
        self.assertEqual(0, your['maintenance_received'].amount)
        self.assertEqual(0, your['pension'].amount)
        self.assertEqual(0, your['other_income'].amount)
        your = converted['you']['deductions']
        self.assertEqual(30000, your['income_tax'].amount)
        self.assertEqual(2000, your['national_insurance'].amount)
        partner = converted['partner']['income']
        self.assertEqual(86666, partner['earnings'].amount)
        self.assertEqual('per_month', partner['earnings'].interval)
        self.assertEqual(0, partner['tax_credits'].amount)
        self.assertEqual(0, partner['maintenance_received'].amount)
        self.assertEqual(0, partner['pension'].amount)
        self.assertEqual(0, partner['other_income'].amount)
        partner = converted['partner']['deductions']
        self.assertEqual(4333, partner['income_tax'].amount)
        self.assertEqual('per_month', partner['income_tax'].interval)
        self.assertEqual(866, partner['national_insurance'].amount)
        self.assertEqual('per_month', partner['national_insurance'].interval)

    def test_outgoing_form(self):
        converted = OutgoingsPayload(self.session['OutgoingsForm'])
        your = converted['you']['deductions']
        self.assertEqual(0, your['rent'].amount)
        self.assertEqual(0, your['maintenance'].amount)
        self.assertEqual(0, your['criminal_legalaid_contributions'])
        self.assertEqual(0, your['childcare'].amount)

    def test_session_converter(self):
        converted = SessionPayload(self.session)
        import pprint
        print pprint.pformat(converted)
        self.assertEqual('debt', converted['category'])
        self.assertEqual(1, converted['dependants_young'])
        self.assertEqual(0, converted['dependants_old'])
        self.assertEqual(NO, converted['is_you_or_your_partner_over_60'])
        self.assertEqual(YES, converted['has_partner'])
        self.assertEqual(YES, converted['you']['income']['self_employed'])
        self.assertEqual(YES, converted['partner']['income']['self_employed'])
        self.assertFalse(converted['specific_benefits']['pension_credit'])
        self.assertFalse(converted['specific_benefits']['job_seekers_allowance'])
        self.assertFalse(converted['specific_benefits']['employment_support'])
        self.assertFalse(converted['specific_benefits']['universal_credit'])
        self.assertFalse(converted['specific_benefits']['income_support'])
        self.assertEqual(False, converted['on_passported_benefits'])
        other_income = converted['you']['income']['other_income']
        self.assertEqual(0, other_income.amount)
        self.assertEqual('per_month', other_income.interval)
        mortgage = converted['you']['deductions']['mortgage']
        self.assertEqual(80000, mortgage.amount)
        property_one = converted['property_set'][0]
        self.assertEqual(10000000, property_one['value'])
        self.assertEqual(8000000, property_one['mortgage_left'])
        self.assertEqual(100, property_one['share'])
        self.assertEqual(NO, property_one['disputed'])
        self.assertEqual(0, property_one['rent'].amount)
        self.assertEqual(YES, property_one['main'])
        self.assertEqual(500000, converted['you']['savings']['bank_balance'])
        self.assertEqual(0, converted['you']['savings']['investment_balance'])
        self.assertEqual(70000, converted['you']['savings']['asset_balance'])
        self.assertEqual(False, converted['on_nass_benefits'])
        self.assertEqual(0, converted['you']['income']['child_benefits'].amount)
        self.assertEqual(0, converted['you']['income']['tax_credits'].amount)
        self.assertEqual(0, converted['you']['income']['benefits'].amount)

        your = converted['you']['income']
        self.assertEqual(150000, your['earnings'].amount)
        self.assertEqual(0, your['tax_credits'].amount)
        self.assertEqual(0, your['maintenance_received'].amount)
        self.assertEqual(0, your['pension'].amount)
        self.assertEqual(0, your['other_income'].amount)
        your = converted['you']['deductions']
        self.assertEqual(30000, your['income_tax'].amount)
        self.assertEqual(2000, your['national_insurance'].amount)
        partner = converted['partner']['income']
        self.assertEqual(86666, partner['earnings'].amount)
        self.assertEqual('per_month', partner['earnings'].interval)
        self.assertEqual(0, partner['tax_credits'].amount)
        self.assertEqual(0, partner['maintenance_received'].amount)
        self.assertEqual(0, partner['pension'].amount)
        self.assertEqual(0, partner['other_income'].amount)
        partner = converted['partner']['deductions']
        self.assertEqual(4333, partner['income_tax'].amount)
        self.assertEqual('per_month', partner['income_tax'].interval)
        self.assertEqual(866, partner['national_insurance'].amount)
        self.assertEqual('per_month', partner['national_insurance'].interval)
        your = converted['you']['deductions']
        self.assertEqual(0, your['rent'].amount)
        self.assertEqual(0, your['maintenance'].amount)
        self.assertEqual(0, your['criminal_legalaid_contributions'])
        self.assertEqual(0, your['childcare'].amount)

        # combined notes
        self.assertEqual((
            u'User selected category: debt\n\n'
            u'Other benefits:\n'
            u' - housing'), converted['notes'])

    def assertZeroedIncomeFields(self, payload):
        income = payload['you']['income']
        self.assertEqual(income['earnings'].amount, 0)
        self.assertEqual(income['self_employment_drawings'].amount, 0)
        self.assertEqual(income['tax_credits'].amount, 0)
        self.assertEqual(income['maintenance_received'].amount, 0)
        self.assertEqual(income['pension'].amount, 0)
        self.assertEqual(income['other_income'].amount, 0)
        deductions = payload['you']['deductions']
        self.assertEqual(deductions['income_tax'].amount, 0)
        self.assertEqual(deductions['national_insurance'].amount, 0)

    def test_your_benefits_form_passported(self):
        payload = YourBenefitsPayload({'benefits': ['income_support']})
        self.assertTrue(payload['specific_benefits']['income_support'])
        self.assertTrue(payload['on_passported_benefits'])
        self.assertZeroedIncomeFields(payload)
