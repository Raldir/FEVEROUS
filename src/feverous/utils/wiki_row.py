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
    
    def get_col_headers(self, cell_id, table_id):
        table_obj = self.page.get_element_by_id(table_id)
        cell_row = table_obj.all_cells[cell_id].row_num
        cell_col = table_obj.all_cells[cell_id].col_num
        headers_column = [row.row[cell_col] for row in table_obj.rows if cell_row > row.row_num]
        headers_column.reverse()
        context_column = []
        encountered_header = False
        for ele in headers_column:
            if ele.is_header:
                context_column.append(ele)
                encountered_header = True
            elif encountered_header:
                break
        return context_column

    def get_row_headers(self, cell_id, table_id):
        table_obj = self.page.get_element_by_id(table_id)
        cell_row = table_obj.all_cells[cell_id].row_num
        cell_col = table_obj.all_cells[cell_id].col_num
        headers_row = [cell for i, cell in  enumerate(table_obj.rows[cell_row].row) if cell_col > i]
        headers_row.reverse()
        context_row = []
        encountered_header = False
        for ele in headers_row:
            if ele.is_header:
                context_row.append(ele)
                encountered_header = True
            elif encountered_header:
                break
        return context_row

    def get_row_content_and_context(self, row_id):
        table_id = "_".join(row_id.split('_')[:2])
        table_context = None
        cell_content_context = []
        cell_ids = self.row_ids[row_id]
        for cell_id in cell_ids:
            cell_obj = self.page.get_element_by_id(cell_id)
            content = cell_obj.content
            context = " ".join([el.content for el in self.get_col_headers(cell_id, table_id)])
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
        table_id = "_".join(row_id.split('_')[:2])
        Nodes = {} #dict: <unique_cell_id>: <cell_content>
        edges = {} #Adj_List: <unique_cell_id>: <list of adjacent vertices>
        #unique_cell_id = page_title_cell_id
        cell_ids = self.row_ids[row_id]
        for cell_id in cell_ids:
            unique_cell_id = self.page.title.name + "_" + cell_id
            Nodes[unique_cell_id] = self.page.get_element_by_id(cell_id).content
            header_cols = self.get_col_headers(cell_id,table_id) #list of cell_obj of columns headers
            header_cols.insert(0,self.page.get_element_by_id(cell_id))
            for i  in range(1, len(header_cols)):
                header_col = header_cols[i]
                unique_cell_id = self.page.title.name + "_" + header_col.get_id()
                Nodes[unique_cell_id] = header_col.content
                prev_unique_cell_id = self.page.title.name + "_" + header_cols[i-1].get_id()
                edges[unique_cell_id].append(prev_unique_cell_id)
                edges[prev_unique_cell_id].append(unique_cell_id)
        #Make a dummy row_node
        unique_row_id = self.page.title.name + "_" + row_id
        Nodes[unique_row_id] = ''#or some unique characters
        for cell_id in cell_ids:
            unique_cell_id = self.page.title.name + "_" + cell_id
            edges[unique_row_id] = unique_cell_id
            edges[unique_cell_id] = unique_row_id
        #Now we have all cells of same row connected indirectly with each other through dummy node;
        #all cell are connected to it's heirarchical cell headers
        #Now all remain is connecting cells to it's heirarchical row headers
        for cell_id in cell_ids:
            unique_cell_id = self.page.title.name + "_" + cell_id
            header_rows = self.get_row_headers(cell_id,table_id)
            header_rows.insert(0,self.page.get_element_by_id(cell_id))
            for i in range(1,len(header_rows)):
                header_row = header_rows[i]
                unique_cell_id = self.page.title.name + "_" + header_row.get_id()
                prev_unique_cell_id = self.page.title.name + "_" + header_rows[i-1].get_id()
                edges[unique_cell_id].append(prev_unique_cell_id)
                edges[prev_unique_cell_id].append(unique_cell_id)
        return (Nodes, edges)