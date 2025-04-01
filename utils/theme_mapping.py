import pandas as pd

class ThemeMapping:
    def __init__(self, excel_path):
        df = pd.read_excel(excel_path)
        self.main_themes = list(df['Main Theme'].unique())
        self.sub_themes = list(df['Sub Theme'].unique())
        self.main_id_to_name = {i: name for i, name in enumerate(self.main_themes)}
        self.sub_id_to_name = {i: name for i, name in enumerate(self.sub_themes)}
        self.num_main = len(self.main_themes)
        self.num_sub = len(self.sub_themes)

    def get_main_name(self, id):
        return self.main_id_to_name.get(id, 'Unknown')

    def get_sub_name(self, id):
        return self.sub_id_to_name.get(id, 'Unknown')
