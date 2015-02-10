from decimal import Decimal

from cla_common.money_interval.models import MoneyInterval as MIBase


class MoneyInterval(dict):

    def __init__(self, *args, **kwargs):
        init_val = {
            'per_interval_value': None,
            'interval_period': 'per_month'
        }

        if len(args) > 0:
            value = args[0]
            if isinstance(value, MoneyInterval):
                init_val = value
            elif isinstance(value, dict):
                init_val.update(
                    per_interval_value=value.get('per_interval_value'),
                    interval_period=value.get('interval_period', 'per_month'))
            else:
                if isinstance(value, float) or isinstance(value, Decimal):
                    value = value * 100
                try:
                    init_val['per_interval_value'] = int(value)
                except ValueError:
                    raise ValueError(
                        'Invalid value for amount {0} ({1})'.format(
                            value, type(value)))

            if len(args) > 1:
                if args[1] in MIBase._intervals_dict:
                    init_val['interval_period'] = args[1]
                else:
                    raise ValueError(args[1])

        else:
            init_val.update(
                per_interval_value=kwargs.get('per_interval_value'),
                interval_period=kwargs.get('interval_period', 'per_month'))

        super(MoneyInterval, self).__init__(init_val)

    @property
    def amount(self):
        return self.get('per_interval_value')

    @amount.setter
    def amount(self, value):
        self['per_interval_value'] = value

    @property
    def interval(self):
        return self.get('interval_period')

    @interval.setter
    def interval(self, value):
        self['interval_period'] = value

    def __add__(self, other):
        if other == 0:
            other = MoneyInterval(0)

        if not isinstance(other, MoneyInterval):
            raise ValueError(other)

        first = self.per_month()
        second = other.per_month()

        return MoneyInterval(first.amount + second.amount)

    def __radd__(self, other):
        return self.__add__(other)

    def per_month(self):
        if self.amount is None or self.interval == '':
            return MoneyInterval(0)

        if self.interval == 'per_month':
            return self

        multiplier = MIBase._intervals_dict[self.interval]['multiply_factor']

        return MoneyInterval(int(self.amount * multiplier))
