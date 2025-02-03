from abc import abstractmethod
import pickle
from editor import Property


class BaseEffect:
    def __init__(self):
        self.label = "Base Effect"
        self.parameters = {}
        self.requirements = []
        self.image = None
        self.new_image = None

    def run_job(self,job_id):
        self.import_job(job_id)
        self.build()
        self.apply()
        self.export_job(job_id)

    def import_job(self,job_id):
        with open("temp/parameters_" + job_id + ".pkl", 'rb') as f:
            self.parameters = pickle.load(f)

        for req in self.requirements:
            if req not in self.parameters.keys():
                raise KeyError(req + " was not provided.")

    def export_job(self,job_id):
        with open("temp/image_" + job_id + ".pkl", 'wb') as f:
            pickle.dump(self.new_image, f)

    @abstractmethod
    def build(self):
        pass

    @abstractmethod
    def apply(self):
        pass

    def update(self):
        pass