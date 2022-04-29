import numpy as np
import os 
import pandas as pd 
import sqlite3

class DatabaseBuilder():
    def __init__(self):
        self.ddl_sequence = [
            'dim_competition'
            , 'dim_opponent'
            , 'dim_stadium'
            , 'fact_matches'
            , 'vw_matches_comp'
            , 'vw_mls_regular_season'
        ]

        self.connection = self._reset_connection()
        self._execute_ddl()
        self._load_csv_data()

    def _reset_connection(self):
        db = 'nycfc.db'
        if os.path.exists(db):
            os.remove(db)
        connection = sqlite3.connect(db)
        return connection

    def _execute_ddl(self):
        dirs = ['_sql_table', '_sql_view']
        dir_lookups = [ self._read_dir(d) for d in dirs ]
        ddl_lookup = { k: v for d in dir_lookups for k, v in d.items() }
        paths = [ ddl_lookup[x] for x in self.ddl_sequence ]
        sql = [ open(p).read() for p in paths ]
        run_ddl = lambda x: self.connection.cursor().executescript(x)
        [ run_ddl(x) for x in sql ]
        
    def _read_dir(self, dir):
        sql_files = [ f for f in os.listdir(dir) if f.endswith('.sql') ]
        names = [ f.split('.')[0] for f in sql_files ]
        paths = [ os.path.join(dir, f) for f in sql_files ]
        dir_lookup =  dict(zip(names, paths))
        return dir_lookup

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