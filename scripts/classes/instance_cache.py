import json


class instance_cache:
    class position:
        def __init__(self, location: list = [0, 0, 0], rotate: list = [0, 0, 0], scale: list = [1, 1, 1]):
            self.location = location
            self.rotate = rotate
            self.scale = scale

        def __str__(self):
            return json.dumps(self, default=lambda o: o.__dict__)
            # return vars(self)
            # return (json.dumps(vars(self), indent=4))
            # return f'location: {self.location},\nrotation: {self.rotate},\nscale: {self.scale}'

    class model:
        def __init__(self, positions=[]):
            self.positions: list = positions

        def __str__(self):
            return json.dumps(self, default=lambda o: o.__dict__)

    def __init__(self):
        # models = {}
        self.models: dict[str, self.model] = {}

    def toJSON(self):
        return json.loads(json.dumps(self, default=lambda o: o.__dict__))
