from .wiki_page import *

class wiki_window:
    def __init__(self, page_obj) -> None:
        """
        Input: (page_obj:   an instance of wiki_page)
        """
        self.page = page_obj
        self.window_size = 5
        #step: used in sliding the windows
        self.step = 1 
        #self.sections: dict <section_id>: <list of sentences_ids>
        self.sections = self.get_sections(self.page.get_page_order())
        #self.windows: dict <window_id>: <list of sentences_ids>
        self.windows =  self.get_windows()
        pass

    def get_sections(self, page_order):
        sections = {}
        curr_section = "intro"
        sentences = []
        for elem in page_order:
            if elem.startswith("section_"):
                sections[curr_section] = sentences
                curr_section = elem
                sentences = []
            elif elem.startswith("sentence_"):
                sentences.append(elem)
        return sections

    def get_windows(self):
        windows = {}
        for section_id in self.sections:
            sentences_ids = self.sections[section_id]
            if len(sentences_ids) == 0:
                continue
            w_id = self.page.title.content + "|window_"+section_id+"_0"
            windows[w_id] = sentences_ids[0:min(self.window_size, len(sentences_ids))]
            for i in range(1,len(sentences_ids)-self.window_size+1, self.step):
                w_id = self.page.title.name + "|window_"+section_id+"_" + str(i)
                windows[w_id] = sentences_ids[i:i+self.window_size]
        return windows
    
    def get_window_content_and_context(self, w_id):
        """
        Input: w_id: window_id
        Given a window id return the content and context of the window
        """
        sentences = self.windows[w_id]
        sentences_content = []
        for sen_id in sentences:
            sentences_content.append(self.page.get_element_by_id(sen_id).__str__())
        #sentences present in same section will have same context 
        #so calculating context once will do the work
        context_elem = self.page.get_context(sentences[0])
        context = []
        for el in context_elem:
            context.append(el.content)
        content_and_context = " ".join(context) + " " + " ".join(sentences_content)
        return content_and_context

    def get_all_windows(self):
        return self.windows
    
    def get_all_content_context(self):
        result = []
        for w_id in self.windows:
            result.append(self.get_window_content_and_context(w_id))
        return result
