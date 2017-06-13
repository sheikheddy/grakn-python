class Duck:

    def __init__(self, name):
        self.name = str(name)

    def squeeze(self):
        response = "Quack! I am " + self.name + "!"
        return response
