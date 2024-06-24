import sqlite3


class SimpleORM:
	def __init__(self, db_name):
		self.connection = sqlite3.connect(db_name)
		self.connection.row_factory = sqlite3.Row
		self.cursor = self.connection.cursor()
	
	def drop_table(self, table_name):
		self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
		self.connection.commit()
	
	def create_table(self, table_name, columns):
		columns_def = ', '.join([f"{col} {dtype}" for col, dtype in columns.items()])
		self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_def})")
		self.connection.commit()
	
	def insert(self, table_name, data):
		placeholders = ', '.join(['?' for _ in data])
		columns = ', '.join(data.keys())
		values = tuple(data.values())
		self.cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", values)
		self.connection.commit()
	
	def fetch_all(self, table_name):
		self.cursor.execute(f"SELECT * FROM {table_name}")
		return self.cursor.fetchall()
	
	def fetch_by_id(self, table_name, record_id):
		self.cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (record_id,))
		return self.cursor.fetchone()
	
	def fetch_by_field(self, table_name, field, value):
		self.cursor.execute(f"SELECT * FROM {table_name} WHERE {field} = ?", (value,))
		return self.cursor.fetchone()
	
	def update(self, table_name, record_id, data):
		set_clause = ', '.join([f"{col} = ?" for col in data])
		values = tuple(data.values()) + (record_id,)
		self.cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE id = ?", values)
		self.connection.commit()
	
	def delete(self, table_name, record_id):
		self.cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (record_id,))
		self.connection.commit()
	
	def delete_all(self, table_name):
		self.cursor.execute(f"DELETE FROM {table_name}")
		self.connection.commit()
	
	def close(self):
		self.connection.close()
