import itertools
import logging

from feverous.utils.wiki_element import WikiElement
from feverous.utils.wiki_list import WikiList
from feverous.utils.wiki_section import WikiSection
from feverous.utils.wiki_sentence import WikiSentence
from feverous.utils.wiki_table import WikiTable


class WikiTitle(WikiElement):
    def __init__(self, name, content):
        self.name = name.strip()
        self.content = content.strip()

    def get_ids(self):
        return [self.name]

    def get_id(self):
        return self.name

    def id_repr(self):
        return self.name

    def __str__(self):
        return self.content


class WikiPage:
    def __init__(self, title, dict, filter=None, mode=None):
        self.error_dict = {
            "tables_empty": 0,
            "tables_formatting_errors": 0,
            "list_empty": 0,
            "sentence_empty": 0,
            "list_formatting_errors": 0,
            "sentences_empty": 0,
        }
        self.page_items = {}
        self.title = WikiTitle("_title", title)
        elements_to_consider = None
        if mode == "intro":
            elements_to_consider = (
                dict["order"][: dict["order"].index("section_0")] if "section_0" in dict["order"] else dict["order"]
            )
        for entry in dict:
            if entry in ["title", "order"] or (filter != None and filter not in entry):
                continue
            if elements_to_consider and entry not in elements_to_consider:
                continue
            # entry_s = process_id(entry, is_annotation=False)
            if entry.startswith("table_"):
                if len(dict[entry]["table"]) == 0:
                    self.error_dict["tables_empty"] += 1
                    continue
                try:
                    tab = WikiTable(entry, dict[entry], self.title.content)
                    self.page_items[entry] = tab
                except Exception:
                    self.error_dict["tables_formatting_errors"] += 1
                    # traceback.print_exc()
                    # logging.warning("Table formatting error in {}, {}".format(title, entry))
            if entry.startswith("list_"):
                if (
                    len(dict[entry]["list"]) == 0
                    or len([en["value"] for en in dict[entry]["list"] if en["value"] != ""]) == 0
                ):
                    self.error_dict["list_empty"] += 1
                    continue
                try:
                    tab = WikiList(entry, dict[entry], self.title.content)
                    self.page_items[entry] = tab
                except Exception:
                    self.error_dict["list_formatting_errors"] += 1
                    # logging.warning("List formatting error in {}, {}".format(title, entry))
                    # traceback.print_exc()
                    # print(title, entry)
            elif entry.startswith("sentence_"):
                text = WikiSentence(entry, dict[entry], self.title.content)
                self.page_items[entry] = text
            elif entry.startswith("section_"):
                section = WikiSection(entry, dict[entry], self.title.content)
                # print(str(section))
                self.page_items[entry] = section

        self.page_order = [el for el in dict["order"] if el in self.page_items]

    def get_element_by_id(self, id):
        return self.page_items[id] if id in self.page_items else None

    def get_previous_k_elements(self, element_id, k=1):
        element_position = self.page_order.index(element_id)
        return [
            self.get_element_by_id(ele) for ele in reversed(self.page_order[element_position - k : element_position])
        ]
        # return self.get_element_by_id(self.page_order[element_position-1]) if element_position-1 >=0 else None

    def get_next_k_elements(self, element_id, k=1):
        element_position = self.page_order.index(element_id)
        return [
            self.get_element_by_id(ele) for ele in self.page_order[element_position + 1 : element_position + (k + 1)]
        ]
        # return self.get_element_by_id(self.page_order[element_position-1]) if element_position-1 >=0 else None

    def get_next_element(self, element_id):
        element_position = self.page_order.index(element_id)
        return self.get_element_by_id(self.page_order[element_position - 1]) if element_position - 1 >= 0 else None

    def get_title_content(self):
        return str(self.title)

    def get_page_items(self):
        return self.page_items

    def get_cell_content(self, cell_id):
        for tab in self.get_tables():
            if cell_id in tab.all_cells:
                return tab.get_cell_content(cell_id)

    def get_cell(self, cell_id):
        for tab in self.get_tables():
            if cell_id in tab.all_cells:
                return tab.get_cell(cell_id)

    def get_table_from_cell_id(self, cell_id):
        for tab in self.get_tables():
            if cell_id in tab.all_cells:
                return tab

    def get_item_content(self, item_id):
        for list in self.get_lists():
            if item_id in list.list_items:
                return list.list_items[item_id]

    def get_caption_content(self, caption_id):
        for tab in self.get_tables():
            if caption_id == tab.caption_id:
                return tab.caption

    def get_error_dict():
        return self.error_dict

    def get_ids(self):
        return list(itertools.chain.from_iterable([value.get_ids() for ele, value in self.page_items.items()]))

    def get_page(self):
        return [self.page_items[el] for el in self.page_order]

    def get_tables(self):
        return [ele for key, ele in self.page_items.items() if key.startswith("table_")]

    def get_lists(self):
        return [ele for key, ele in self.page_items.items() if key.startswith("list_")]

    def get_sections(self):
        return [ele for key, ele in self.page_items.items() if key.startswith("section_")]

    def get_sentences(self):
        return [ele for key, ele in self.page_items.items() if key.startswith("sentence_")]

    def get_cells(self):
        return [ele for key, ele in self.page_items.items() if key.startswith("cell_")]

    def get_list_items(self):
        return [ele for key, ele in self.page_items.items() if key.startswith("item_")]

    def get_context(self, id):
        if id.startswith("sentence_"):
            return self._get_sentence_context(id)
        elif id.startswith("item_"):
            return self._get_list_context(id)
        elif id.startswith("header_cell_"):
            return self._get_cell_header_context(id)
        elif id.startswith("cell_"):
            return self._get_cell_context(id)
        elif id.startswith("table_caption_"):
            return self._get_caption_context(id)
        return []

    def __str__(self):
        return "\n".join([str(el) for el in self.get_page()])

    def convert_ids_to_objects(self, id_list):
        return [self.page_items[el] for el in id_list]

    def _get_caption_context(self, caption):
        table = None
        for ele in self.get_tables():
            if caption in ele.get_ids():
                # if ele.name.split('_')[-1] == cell.split('_')[1]:
                table = ele
                break
        if table == None:
            logging.warning("Table not found in context, {}".format(caption))
        section_context = self._get_section_context(table.name)
        return [self.title] + section_context

    def _get_sentence_context(self, sentence):
        section_context = self._get_section_context(sentence)
        return [self.title] + section_context

    def _get_list_context(self, item):
        list_id = None
        for ele in self.get_lists():
            if ele.name.split("_")[-1] == item.split("_")[1]:
                list_id = ele
                break
        if list_id == None:
            logging.warning("List not found in context, {}".format(item))
        section_context = self._get_section_context(list_id.name)
        return [self.title] + section_context

    def _get_cell_header_context(self, cell):
        table = None
        for ele in self.get_tables():
            if ele.name.split("_")[-1] == cell.split("_")[2]:
                table = ele
                break
        if table == None:
            logging.warning("Table not found in context, {}".format(cell))
        section_context = self._get_section_context(table.name)
        return [self.title] + section_context

    def get_table_from_cell(self, cell):
        table = None
        for ele in self.get_tables():
            if ele.name.split("_")[-1] == cell.split("_")[1]:
                table = ele
                break
        return table

    def _get_cell_context(self, cell):
        table = None
        for ele in self.get_tables():
            if ele.name.split("_")[-1] == cell.split("_")[1]:
                table = ele
                break
        if table == None:
            logging.warning("Table not found in context, {}".format(cell))
        cell_row = table.all_cells[cell].row_num
        cell_col = table.all_cells[cell].col_num
        headers_row = [cell for i, cell in enumerate(table.rows[cell_row].row) if cell_col > i]
        headers_row.reverse()
        context_row = set([])
        encountered_header = False
        for ele in headers_row:
            if ele.is_header:
                context_row.add(ele)
                encountered_header = True
            elif encountered_header:
                break
        headers_column = [row.row[cell_col] for row in table.rows if cell_row > row.row_num]
        headers_column.reverse()
        context_column = set([])
        encountered_header = False
        for ele in headers_column:
            if ele.is_header:
                context_column.add(ele)
                encountered_header = True
            elif encountered_header:
                break

        return self._get_section_context(table.name) + list(context_row) + list(context_column)

    def _get_section_context(self, element_id):
        section_context = []
        if element_id not in self.page_order:
            print("NOT IN")
            print(self.page_order)
            print(element_id)
            print(self.title.content)
            print(self.page_items.keys())
        page_position = self.page_order.index(element_id)

        before_elements = self.page_order[:page_position]
        before_elements = self.convert_ids_to_objects(before_elements)
        before_elements.reverse()
        for ele in before_elements:
            if ele.name.startswith("section_"):
                if not section_context:
                    section_context.append(ele)
                elif section_context[-1].level > ele.level:
                    section_context.append(ele)
                elif section_context[-1].level < ele.level:
                    break
        return section_context

    def __del__(self):
        for ele, item in self.page_items.items():
            del item
        del self.title
        del self.page_order
