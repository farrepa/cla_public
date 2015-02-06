from cla_common.money_interval.models import MoneyInterval as MIBase


class MoneyInterval(dict):

    def __init__(self, *args, **kwargs):
        init_val = {
            'per_interval_value': None,
            'interval_period': 'per_month'
        }

        if len(args) > 0:
            if isinstance(args[0], MoneyInterval):
                init_val = args[0]
            elif isinstance(args[0], dict):
                init_val.update(
                    per_interval_value=args[0].get('per_interval_value'),
                    interval_period=args[0].get('interval_period', 'per_month'))
            elif isinstance(args[0], int):
                init_val['per_interval_value'] = args[0]
            elif isinstance(args[0], float):
                init_val['per_interval_value'] = int(args[0])
            else:
                raise ValueError(args[0])

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
        if not isinstance(other, MoneyInterval):
            raise ValueError(other)

        first = self.per_month()
        second = other.per_month()

        return MoneyInterval(first.amount + second.amount)

    def __radd__(self, other):
        if other == 0:
            return self.__add__(MoneyInterval(0))
        return self.__add__(other)

    def per_month(self):
        if self.amount is None or self.interval == '':
            return MoneyInterval(0)

        if self.interval == 'per_month':
            return self

        multiplier = MIBase._intervals_dict[self.interval]['multiply_factor']

        return MoneyInterval(self.amount * multiplier)