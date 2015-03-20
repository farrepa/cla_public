# -*- coding: utf-8 -*-
"Scope diagnosis forms"

from flask_wtf import Form
import wtforms

from cla_public.libs.honeypot import Honeypot


class ScopeForm(Honeypot, Form):

    problem = wtforms.TextAreaField(
        'What is your problem?',
        description='Please describe your problem')
