"""Relational database routines

"""

import petl as etl
import json
import pandas as pd
import sqlite3

import strax
from .common import Store, Saver, NotCached, CacheKey

export, __all__ = strax.exporter()


@export
class SQLLiteStore(Store):

    def __init__(self, *args, **kwargs):
        """SQL-based storage backend for strax.

        data is stored either in SQLite files or in Amazon RDS

        {provides_doc}

        """
        super().__init__(*args, **kwargs)

        self.filename = 'strax.db'

        self.connection = sqlite3.connect(self.filename)

        if 'metadata' not in self._get_tables():
            self.log.debug('Creating metadata table')
            # Unique key index -> JSON metadata
            command = 'CREATE TABLE metadata (name text, metadata text)'
            self.connection.execute(command)
            self.log.debug('Created metadata table')

    def _get_tables(self):
        """Get a list of available tables in SQLite
        """
        cursor = self.connection.cursor()
        cmd = "SELECT name FROM sqlite_master WHERE type='table'"
        cursor.execute(cmd)
        names = [row[0] for row in cursor.fetchall()]
        return names

    def _find(self, key):
        if str(key) in self._get_tables():
            self.log.debug(f"{key} is in cache.")

            # Run this just to make sure metadata exists
            self._read_meta(str(key))

            return str(key)

        self.log.debug(f"{key} is NOT in cache.")
        raise NotCached

    def _read_chunk(self, table, chunk_info, dtype, compressor):
        command = f"SELECT * FROM {table} WHERE chunk_i == {chunk_info['chunk_i']}"
        return etl.fromdb(self.connection,
                          command).torecarray()

    def _read_meta(self, table):
        cmd = f"SELECT * FROM metadata WHERE name='{table}'"
        cursor = self.connection.cursor()
        cursor.execute(cmd)

        results = cursor.fetchall()
        if len(results) > 1:
            raise RuntimeError("Repeated metadata error")
        elif len(results) == 0:
            raise RuntimeError("Metadata missing")
        elif len(results[0]) != 2:
            raise RuntimeError("Misformatted metadata")
        return json.loads(results[0][1])

    def saver(self, key, metadata):
        super().saver(key, metadata)
        return SQLLiteSaver(key, metadata, self.filename)


@export
class SQLLiteSaver(Saver):
    #prefer_rechunk = False

    def __init__(self, key, metadata, filename):
        super().__init__(key, metadata)
        self.filename = filename
        self.connection = sqlite3.connect(self.filename)
        self.md['chunks'] = {}

    def _save_chunk(self, data, chunk_info):
        print(data)
        table = pd.DataFrame.from_records(data)
        print('chunk_i', chunk_info['chunk_i'])
        table['chunk_i'] = [chunk_info['chunk_i'], ] * len(data)
        print(table.head())
        print(table.columns)
        etl.todb(data,
                 self.connection,
                 str(self.key),
                 create=True)
        return dict()

    def _save_chunk_metadata(self, chunk_info):
        self.md['chunks'].append(chunk_info)

    def close(self):
        super().close()
        json_dump = json.dumps(self.md)
        command = f"INSERT INTO metadata VALUES ('{self.key}', '{json_dump}')"

        self.connection.execute(command)
