import itertools

from feverous.utils.wiki_element import WikiElement, process_text


class WikiTable(WikiElement):
    def __init__(self, name, table_json, page):
        self.name = name
        self.page = page
        self.table = table_json["table"]
        self.table = self.normalize_table()
        self.caption = table_json["caption"] if "caption" in table_json else ""
        self.caption_id = "table_caption_" + self.name.split("_")[-1]
        self.type = table_json["type"]
        self.rows = [Row(row, i, self.page) for i, row in enumerate(self.table)]
        self.header_rows = [row for row in self.rows if row.is_header_row() == True]
        self.cell_ids = [row.cell_ids for row in self.rows]
        self.cell_ids = list(itertools.chain(*self.cell_ids))
        self.linearized_table = "\n".join([str(row) for row in self.rows])
        self.linearized_table_id = "\n".join([row.id_repr() for row in self.rows])
        self.all_cells = {}
        for row in self.rows:
            for cell in row.row:
                self.all_cells[cell.name] = cell

    def consecutive_non_nulls(self, row):
        count = 0
        while count < len(row) and row[count] != 0:
            count += 1
        return count

    def normalize_table(self):
        col_size = sum(int(cell["column_span"]) for cell in self.table[0])
        row_size = len(self.table)
        normalized_table = [[0 for j in range(col_size)] for i in range(row_size)]
        for i, row in enumerate(self.table):
            for j, col in enumerate(row):
                cell = self.table[i][j]
                lowest_col = self.consecutive_non_nulls(normalized_table[i])
                for k in range(min(int(cell["column_span"]), col_size - lowest_col)):
                    normalized_table[i][lowest_col + k] = self.table[i][j]
                for k in range(min(int(cell["row_span"]), row_size - i)):
                    normalized_table[i + k][lowest_col] = self.table[i][j]
        return normalized_table

    def __str__(self):
        return self.linearized_table

    def get_cell_content(self, cell_id):
        return str(self.all_cells[cell_id])

    def get_header_rows(self):
        return self.header_rows

    def get_rows(self):
        return self.rows

    def get_table_caption(self):
        return self.caption

    def get_table_caption_id(self):
        return self.caption_id

    def get_cell(self, cell_id):
        return self.all_cells[cell_id]

    def get_cells(self):
        return self.all_cells

    def get_ids(self):
        return list(itertools.chain.from_iterable([row.get_ids() for row in self.rows])) + [self.caption_id]

    def get_id(self):
        return self.name

    def id_repr(self):
        return "\n".join([row.id_repr() for row in self.rows])

    def joint_repr(self):
        return "\n".join([row.joint_repr() for row in self.rows])

    def get_cell_row(cell_id):
        for i, row in enumerate(self.rows):
            if cell_id in row.id_content_map:
                return row


class Cell:
    def __init__(self, cell, row_num, col_num, page):
        self.row_num = row_num
        self.col_num = col_num
        self.page = page
        self.is_header = cell["is_header"]
        self.content = process_text(cell["value"])
        self.name = cell["id"]

    def __str__(self):
        str = self.content if not self.is_header else "[H] " + self.content
        return str

    def joint_repr(self):
        return self.name + ";;;" + self.content

    def id_repr(self):
        return self.name

    def get_id(self):
        return self.name

    def get_ids(self):
        return [self.name]


class Row:
    def __init__(self, row_json, row_num, page):
        self.json = row_json
        self.row_num = row_num
        self.page = page
        self.row = [Cell(cell, row_num, i, self.page) for i, cell in enumerate(row_json)]
        self.cell_ids = [cell.name for cell in self.row]
        self.id = " | ".join(self.cell_ids)
        self.cell_content = [cell.content for cell in self.row]
        self._is_header_row = len([ele for ele in self.row if ele.is_header == False]) == 0

    def __str__(self):
        return " | ".join([str(ele) for ele in self.row])

    def is_header_row(self):
        return self._is_header_row

    def get_row_cells(self):
        return self.row

    def get_id(self):
        return "row_" + "_".join(self.cell_ids[0].get_id().split("_")[1:])

    def get_ids(self):
        return self.cell_ids

    def joint_repr(self):
        return " | ".join([cell.joint_repr() for cell in self.row])

    def id_repr(self):
        return " | ".join(self.cell_ids)
