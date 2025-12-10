from aiogram.fsm.state import State, StatesGroup

class OrderState(StatesGroup):
    waiting_for_address = State()
    waiting_for_payment = State()

class AdminState(StatesGroup):
    waiting_for_name = State()
    waiting_for_desc = State()
    waiting_for_price = State()
    waiting_for_photo = State()

class EditProductState(StatesGroup):
    waiting_for_new_value = State()