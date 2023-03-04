class WikiElement(object):
    def get_ids(self) -> list:
        """Returns list of all ids in that element"""
        pass

    def get_id(self) -> str:
        """Return the specific id of that element"""

    def id_repr(self) -> str:
        """Returns a string representation of all ids in that element"""
        pass

    def __str__(self) -> str:
        """Returns a string representation of the element's content"""
        pass


def process_text(text: str):
    return text.strip()
