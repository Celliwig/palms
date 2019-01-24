# Asortted screen utilities
#############################################################################

class screen_utils(object):
    def convert_2_pages(item_list, page_length):
        return [item_list[i:i + page_length] for i in range(0, len(item_list), page_length)]

