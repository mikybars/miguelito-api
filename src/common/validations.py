class Validations:
    def __setattr__(self, prop, value):
        if (validator := getattr(self, f'validate_{prop}', None)):
            object.__setattr__(self, prop, validator(value) or value)
        else:
            super().__setattr__(prop, value)
