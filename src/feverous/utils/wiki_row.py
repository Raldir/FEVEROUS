from utils.wiki_page import *

class wiki_row:
    def __init__(self, page_obj) -> None:
        self.page = page_obj
        self.table_ids = self.page.get_table_ids() #List of table_ids in the page
        #self.row_ids: dict: <row_id>: <List of cell_ids>
        self.row_ids = self.get_row_ids(self.table_ids)

        pass

    def get_row_ids(self,table_ids):
        row_ids = {}
        for table_id in table_ids:
            table_obj = self.page.get_element_by_id(table_id)
            rows = table_obj.get_rows()
            for row_obj in rows:
                row_id = table_obj.get_id() + "_ " + row_obj.row_num
                row_ids[row_id] = row_obj.get_ids()
        return row_ids
    
    def get_col_context(self, cell_id, table_id):
        table_obj = self.page.get_element_by_id(table_id)
        cell_row = table_obj.all_cells[cell_id].row_num
        cell_col = table_obj.all_cells[cell_id].col_num
        headers_column = [row.row[cell_col] for row in table_obj.rows if cell_row > row.row_num]
        headers_column.reverse()
        context_column = []
        encountered_header = False
        for ele in headers_column:
            if ele.is_header:
                context_column.append(ele.content)
                encountered_header = True
            elif encountered_header:
                break
        return context_column

    def get_row_content_and_context(self, row_id):
        table_id = "_".join(row_id.split('_')[:2])
        table_context = None
        col_context = []
        cell_content_context = []
        cell_ids = self.row_ids[row_id]
        for cell_id in cell_ids:
            cell_obj = self.page.get_element_by_id(cell_id)
            content = cell_obj.content
            context = " ".join(self.get_col_context(cell_id, table_id))
            cell_content_context.append(context + " " + content)
        table_obj = self.page.get_element_by_id(table_id)
        table_caption_id = table_obj.caption_id
        table_caption = table_obj.caption
        table_caption_context_obj = self.page.get_context(table_caption_id)
        table_caption_context = []
        for el in table_caption_context_obj:
            table_caption_context.append(el.content)
        table_context = table_caption_context + " " + table_caption
        content_context = table_context + cell_content_context
        return content_context

    def get_row_graph(self, row_id):
        pass