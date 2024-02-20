from feverous.utils.wiki_element import WikiElement, process_text


class WikiList(WikiElement):
    def __init__(self, name, list_json, page):
        self.json = list_json
        self.name = name
        self.page = page
        self.list = list_json["list"]
        self.type = list_json["type"]
        self.linearized_list, self.list_by_level = self.compile_list()
        self.linearized_list_str = "\n".join(self.linearized_list)
        self.list_items = {}
        for entry in self.list:
            self.list_items[entry["id"]] = process_text(entry["value"])

    def compile_list(self):
        lin_list = []
        curr_level = 0
        content_by_level = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: [], 9: [], 10: []}
        types = {
            0: self.type,
            1: None,
            2: None,
            3: None,
            4: None,
            5: None,
            6: None,
            7: None,
            8: None,
            9: None,
            10: None,
        }
        level_count = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0}

        for entry in self.list:
            if "type" in entry:
                types[entry["level"] + 1] = entry["type"]
            if curr_level != entry["level"]:
                curr_count = 1
                if curr_level > entry["level"]:
                    level_count[curr_level] = 0
            curr_level = entry["level"]
            if types[curr_level] == "unordered_list" or types[curr_level] == "unordered_list":
                level_count[curr_level] = 0
                if entry["value"] != "":
                    lin_list.append("[SUB] " * entry["level"] + "- " + process_text(entry["value"]))
                    content_by_level[entry["level"]].append(process_text(entry["value"]))
            elif types[curr_level] == "ordered_list" or types[curr_level] == "ordered_list":
                level_count[entry["level"]] += 1
                if entry["value"] != "":
                    lin_list.append(
                        "[SUB] " * entry["level"]
                        + str(level_count[entry["level"]])
                        + ". "
                        + process_text(entry["value"])
                    )
                    content_by_level[entry["level"]].append(
                        str(level_count[entry["level"]]) + ". " + process_text(entry["value"])
                    )
        return lin_list, content_by_level

    def get_item_content(self, item_id):
        return self.list_items[item_id]

    def get_id(self):
        return self.name

    def __str__(self):
        return process_text(self.linearized_list_str)

    def id_repr(self):
        return " | ".join([ele["id"] for ele in self.json])

    def get_ids(self):
        return [ele["id"] for ele in self.json["list"]]

    def get_list_by_level(self, level):
        return self.list_by_level[level]
