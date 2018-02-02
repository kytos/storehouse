class StoreBase:
    def create(self, box):
        raise Exception("Must Implement")

    def retrieve(self, namespace, box_id):
        raise Exception("Must Implement")

    def delete(self, namespace, box_id):
        raise Exception("Must Implement")

    def list(self, namespace):
        raise Exception("Must Implement")
