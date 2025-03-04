from abc import ABC, abstractmethod


class DataGenerator(ABC):

    @abstractmethod
    def __init__(self, model):
        super().__init__()
        self.model = model

    @abstractmethod
    def generate_data(self):
        pass
