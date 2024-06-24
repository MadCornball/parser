import tkinter as tk
from datetime import datetime, timedelta
from config import SimpleORM


class Employee:
	def __init__(self, name, position):
		self.name = name
		self.position = position


class Client:
	def __init__(self, surname, name, patronymic, passport_details, comment=''):
		self.surname = surname
		self.name = name
		self.patronymic = patronymic
		self.passport_details = passport_details
		self.comment = comment
		self.discounts = []
	
	def add_discount(self, discount):
		self.discounts.append(discount)
	
	def get_total_discount(self):
		return sum(self.discounts)


class Room:
	def __init__(self, room_number, capacity, comfort, price):
		self.room_number = room_number
		self.capacity = capacity
		self.comfort = comfort
		self.price = price
		self.is_available = True


class Booking:
	def __init__(self, client, room, check_in_date, check_out_date=None, note=''):
		self.client = client
		self.room = room
		self.check_in_date = check_in_date
		self.check_out_date = check_out_date
		self.note = note


class StaffManagement:
	def __init__(self):
		self.employees = []
	
	def add_employee(self, employee):
		self.employees.append(employee)
	
	def list_employees(self):
		employee_list = ""
		for employee in self.employees:
			employee_list += f"Ім'я: {employee.name}, Посада: {employee.position}\n"
		return employee_list


class ReportGenerator:
	def generate_report(self, start_date, end_date):
		report = f"Звіт за період з {start_date} по {end_date} згенеровано."
		return report


class Hotel:
	def __init__(self):
		self.orm = SimpleORM('hotel.db')
		
		# Удаление таблицы rooms, если она существует
		self.orm.drop_table('rooms')
		
		# Создание таблицы rooms с правильной структурой
		self.orm.create_table('rooms',
		                      {'id': 'INTEGER PRIMARY KEY AUTOINCREMENT', 'number': 'INTEGER', 'capacity': 'INTEGER',
		                       'comfort': 'TEXT', 'price': 'INTEGER', 'is_available': 'INTEGER'})
		self.orm.create_table('guests', {'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
		                                 'surname': 'TEXT',
		                                 'name': 'TEXT',
		                                 'patronymic': 'TEXT',
		                                 'passport_details': 'TEXT',
		                                 'comment': 'TEXT'})
		
		self.orm.create_table('bookings', {'id': 'INTEGER PRIMARY KEY AUTOINCREMENT', 'client_id': 'INTEGER',
		                                   'room_number': 'INTEGER', 'check_in_date': 'TEXT', 'check_out_date': 'TEXT',
		                                   'note': 'TEXT'})
	
	def add_rooms(self):
		self.delete_all_rooms()
		
		blocks = [
			{"start": 101, "end": 110, "capacity": 2, "comfort": "люкс", "price": 2000},
			{"start": 201, "end": 210, "capacity": 1, "comfort": "звичайний", "price": 1000},
			{"start": 301, "end": 310, "capacity": 3, "comfort": "напівлюкс", "price": 1500},
		]
		for block in blocks:
			for room_number in range(block["start"], block["end"] + 1):
				room_data = {
					'number': room_number,
					'capacity': block["capacity"],
					'comfort': block["comfort"],
					'price': block["price"],
					'is_available': True
				}
				self.orm.insert('rooms', room_data)
	
	def delete_all_rooms(self):
		self.orm.delete_all('rooms')
	
	def find_available_rooms(self, capacity, comfort, start_date, end_date):
		all_rooms_data = self.orm.fetch_all('rooms')
		available_rooms = []
		for room_data in all_rooms_data:
			if room_data['is_available'] and room_data['capacity'] == capacity and room_data['comfort'] == comfort:
				room = Room(room_number=room_data['number'], capacity=room_data['capacity'],
				            comfort=room_data['comfort'], price=room_data['price'])
				available_rooms.append(room)
		return available_rooms
	
	def book_room(self, client, room_number, days_to_stay, note=''):
		current_date = datetime.now().date()
		end_date = current_date + timedelta(days=days_to_stay)
		
		room_data = self.orm.fetch_by_field('rooms', 'number', room_number)
		if room_data and room_data['is_available']:
			room = Room(room_data['number'], room_data['capacity'], room_data['comfort'], room_data['price'])
			booking = Booking(client, room, check_in_date=current_date, check_out_date=end_date, note=note)
			self.orm.insert('bookings',
			                {'client_id': client.id, 'room_number': room_number, 'check_in_date': str(current_date),
			                 'check_out_date': str(end_date), 'note': note})
			self.orm.update('rooms', room_data['id'], {'is_available': False})
			return booking
		else:
			return None


# GUI Section

hotel = Hotel()
hotel.add_rooms()

staff_management = StaffManagement()
staff_management.add_employee(Employee(name="Іван", position="Адміністратор"))
staff_management.add_employee(Employee(name="Марія", position="Прибиральниця"))
staff_management.add_employee(Employee(name="Петро", position="Офіціант"))

report_generator = ReportGenerator()

root = tk.Tk()
root.title("Готель")
root.geometry("800x600")


def show_employees():
	employees_text = staff_management.list_employees()
	employees_label.config(text=employees_text)


def book_room():
	days_to_stay = int(days_to_stay_entry.get())
	current_date = datetime.now().date()
	end_date = current_date + timedelta(days=days_to_stay)
	
	guest_name = guest_name_entry.get()
	guest_surname = guest_surname_entry.get()
	guest_patronymic = guest_patronymic_entry.get()
	guest_passport_details = guest_passport_details_entry.get()
	guest_comment = guest_comment_entry.get()
	
	if guest_name.strip() == "" or guest_surname.strip() == "":
		result_label.config(text="Будь ласка, вкажіть ім'я та прізвище гостя.")
		return
	
	client = Client(surname=guest_surname, name=guest_name, patronymic=guest_patronymic,
	                passport_details=guest_passport_details, comment=guest_comment)
	hotel.orm.insert('guests', {'surname': guest_surname, 'name': guest_name, 'patronymic': guest_patronymic,
	                            'passport_details': guest_passport_details, 'comment': guest_comment})
	client_id = hotel.orm.cursor.lastrowid
	client.id = client_id
	
	capacity = int(room_capacity_entry.get())
	comfort = room_comfort_entry.get()
	available_rooms = hotel.find_available_rooms(capacity, comfort, start_date=current_date, end_date=end_date)
	
	if available_rooms:
		room_number_to_book = room_number_entry.get()
		
		if room_number_to_book.isdigit():
			room_number_to_book = int(room_number_to_book)
			if any(room.room_number == room_number_to_book for room in available_rooms):
				booking = hotel.book_room(client, room_number_to_book, days_to_stay, note="")
				if booking:
					result_label.config(text="Номер успішно заброньовано.")
					report_text = report_generator.generate_report(start_date=current_date, end_date=end_date)
					report_text += f"\n\nГість: {guest_name} {guest_surname}\nНомер кімнати: {room_number_to_book}\nДата проживання: з {current_date} по {end_date}"
					report_label.config(text=report_text)
				else:
					result_label.config(text="Цей номер недоступний для бронювання.")
			else:
				result_label.config(text="Такого номера немає в списку доступних номерів.")
		else:
			result_label.config(text="Будь ласка, введіть число.")
	else:
		result_label.config(text="Вибачте, вільних номерів немає.")


def show_available_rooms_count():
	capacity = int(room_capacity_entry.get())
	comfort = room_comfort_entry.get()
	days_to_stay_text = days_to_stay_entry.get()
	if not days_to_stay_text:
		result_label.config(text="Будь ласка, введіть кількість днів на проживання.")
		return
	current_date = datetime.now().date()
	end_date = current_date + timedelta(days=int(days_to_stay_text))
	available_rooms_count = len(hotel.find_available_rooms(capacity, comfort, current_date, end_date))
	available_rooms_count_label.config(text=f"Кількість вільних номерів: {available_rooms_count}")


def show_rooms():
	rooms = hotel.orm.fetch_all('rooms')
	rooms_text = "Список номерів:\n"
	for room in rooms:
		rooms_text += f"Номер: {room['number']}, Місткість: {room['capacity']}, Комфорт: {room['comfort']}, Ціна: {room['price']}, Доступність: {'Так' if room['is_available'] else 'Ні'}\n"
	rooms_label.config(text=rooms_text)


def capture_screenshot():
	x = root.winfo_rootx()
	y = root.winfo_rooty()
	width = root.winfo_width()
	height = root.winfo_height()


employees_button = tk.Button(root, text="Список працівників", command=show_employees)
employees_button.pack()

employees_label = tk.Label(root, text="")
employees_label.pack()

guest_name_label = tk.Label(root, text="Ім'я гостя:")
guest_name_label.pack()

guest_name_entry = tk.Entry(root)
guest_name_entry.pack()

guest_surname_label = tk.Label(root, text="Прізвище гостя:")
guest_surname_label.pack()

guest_surname_entry = tk.Entry(root)
guest_surname_entry.pack()

guest_patronymic_label = tk.Label(root, text="По батькові гостя:")
guest_patronymic_label.pack()

guest_patronymic_entry = tk.Entry(root)
guest_patronymic_entry.pack()

guest_passport_details_label = tk.Label(root, text="Паспортні дані гостя:")
guest_passport_details_label.pack()

guest_passport_details_entry = tk.Entry(root)
guest_passport_details_entry.pack()

guest_comment_label = tk.Label(root, text="Коментар:")
guest_comment_label.pack()

guest_comment_entry = tk.Entry(root)
guest_comment_entry.pack()

room_capacity_label = tk.Label(root, text="Місткість кімнати:")
room_capacity_label.pack()

room_capacity_entry = tk.Entry(root)
room_capacity_entry.pack()

room_comfort_label = tk.Label(root, text="Комфорт:")
room_comfort_label.pack()

room_comfort_entry = tk.Entry(root)
room_comfort_entry.pack()

room_number_label = tk.Label(root, text="Номер кімнати:")
room_number_label.pack()

room_number_entry = tk.Entry(root)
room_number_entry.pack()

days_to_stay_label = tk.Label(root, text="Кількість днів на проживання:")
days_to_stay_label.pack()

days_to_stay_entry = tk.Entry(root)
days_to_stay_entry.pack()

book_button = tk.Button(root, text="Забронювати", command=book_room)
book_button.pack()

result_label = tk.Label(root, text="")
result_label.pack()

report_label = tk.Label(root, text="")
report_label.pack()

show_available_rooms_count_button = tk.Button(root, text="Показати кількість вільних номерів",
                                              command=show_available_rooms_count)
show_available_rooms_count_button.pack()

available_rooms_count_label = tk.Label(root, text="")
available_rooms_count_label.pack()

# Нові кнопки та віджети для сторінки матеріалів
show_rooms_button = tk.Button(root, text="Показати список номерів", command=show_rooms)
show_rooms_button.pack()

rooms_label = tk.Label(root, text="")
rooms_label.pack()


root.mainloop()
