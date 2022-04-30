import numpy as np
import os 
import pandas as pd 
import sqlite3

class DatabaseBuilder():
    def __init__(self):
        self.ddl_dirs = ['_sql_table', '_sql_view']
        self.ddl_sequence = [
            'dim_competition'
            , 'dim_opponent'
            , 'dim_stadium'
            , 'fact_matches'
            , 'vw_matches_comp'
            , 'vw_mls_regular_season'
        ]
        self.ddl = self._prepare_ddl()
        self.connection = self._reset_connection()

        ddl_in = ' '.join(self.ddl)
        self.connection.cursor().executescript(ddl_in)

        self._load_csv_data()
        self.connection.close()

    def _prepare_ddl(self):
        files = [ self._generate_lookup(d) for d in self.ddl_dirs ]
        lookup = { k: v for d in files for k, v in d.items() }
        lookup_paths = [ lookup[x] for x in self.ddl_sequence ]
        sql = [ self._read_file(lp) for lp in lookup_paths ]
        return sql

    def _generate_lookup(self, dir):
        files = [ f for f in os.listdir(dir) if f.endswith('.sql') ]
        names = [ f.split('.')[0] for f in files ]
        paths = [ os.path.join(dir, f) for f in files ]
        lookup_dict =  dict(zip(names, paths))
        return lookup_dict

    def _read_file(self, file):
        with open(file) as f:
            data = f.read().rstrip()
        assert_false = f'this SQL file does not end with a semi-colon: {file}'
        assert data.endswith(';'), assert_false
        return data

    def _reset_connection(self):
        db = 'nycfc.db'
        if os.path.exists(db):
            os.remove(db)
        connection = sqlite3.connect(db)
        return connection

    def _load_csv_data(self):
        tables = self._transform_csv_data()
        insert_values = lambda key, val: val.to_sql(
            key
            , self.connection
            , if_exists='append'
            , index=False
        )
        [ insert_values(k, v) for k, v in tables.items() ]

    def _transform_csv_data(self):
        with open('match.csv') as f:
            df_data = pd.read_csv(f)
        df_match = df_data.drop(columns=['opponent_nationality', 'location_city', 'location_state', 'location_country', 'is_competitive_match'])

        table_data = {
            'dim_competition': self._transform_dim_table(df_data, ['competition', 'is_competitive_match'])
            , 'dim_opponent': self._transform_dim_table(df_data, ['opponent', 'opponent_nationality'])
            , 'dim_stadium': self._transform_dim_table(df_data, ['stadium', 'location_city', 'location_state', 'location_country'])
            , 'fact_matches': df_match
        }
        return table_data

    def _transform_dim_table(self, df, list_cols):
        df = df[list_cols].drop_duplicates()
        df = df[df[df.columns[0]].notna()]
        return df

def main():
    dbb = DatabaseBuilder()

if __name__ == '__main__':
    main()